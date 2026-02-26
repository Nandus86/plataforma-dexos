"""
Hikvision Bridge – FastAPI Application

Two-pronged architecture:
  1. Events FROM device → HTTP Webhook (device POSTs XML to /hikvision/events)
     Works cloud ↔ device (device sends to public URL)
  
  2. Users TO device → ISAPI REST calls via SDK (NET_DVR_Login + STDXMLConfig)
     When device is connected via ISUP: SDK receives connection, logs in, manages users
     When on same LAN: direct ISAPI connection to device IP

  3. Forward TO Exousia → REST API calls to /attendance
"""
import ctypes
import logging
import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.isup_server import HikvisionEventReceiver
from app.exousia_client import ExousiaClient

logger = logging.getLogger(__name__)


# ──────── Clients ────────
exousia = ExousiaClient(
    api_url=settings.EXOUSIA_API_URL,
    api_token=settings.EXOUSIA_API_TOKEN,
)

event_receiver = HikvisionEventReceiver(
    on_attendance_event=exousia.send_attendance,
)


# ──────── SDK Globals ────────
sdk = None
sdk_available = False
listen_handle = -1
device_user_id = -1
connected_devices = {}  # device_id -> user_id


# ──────── SDK Callback Structures ────────
if os.name != 'nt':
    CALLBACK_FUNC = ctypes.CFUNCTYPE(
        ctypes.c_bool, ctypes.c_long, 
        ctypes.c_void_p, ctypes.c_char_p,
        ctypes.c_ulong, ctypes.c_void_p
    )
else:
    CALLBACK_FUNC = ctypes.CFUNCTYPE(
        ctypes.c_bool, ctypes.c_long,
        ctypes.c_void_p, ctypes.c_char_p,
        ctypes.c_ulong, ctypes.c_void_p
    )

callback_ref = None  # prevent GC


def sdk_alarm_callback(command, alarmer, alarm_info, buf_len, user):
    """SDK callback when a device sends data via ISUP."""
    global connected_devices
    try:
        logger.info(f"📡 SDK Callback: command=0x{command:04X}, buf_len={buf_len}")
        
        if alarm_info and buf_len > 0:
            raw = ctypes.string_at(alarm_info, buf_len)
            logger.debug(f"   Raw data (first 200 bytes): {raw[:200].hex()}")
            
            # Try to extract device info from the callback
            if command == 0x5002:  # COMM_ALARM_ACS
                logger.info("🔒 Access Control event received via SDK!")
    except Exception as e:
        logger.error(f"SDK callback error: {e}")
    return True


def init_sdk():
    """Initialize HCNetSDK and start listening for ISUP connections."""
    global sdk, sdk_available, listen_handle, callback_ref
    
    lib_path = settings.SDK_LIB_PATH
    if not os.path.exists(lib_path):
        logger.warning(f"⚠️  SDK not found at {lib_path}. Running without SDK.")
        return False
    
    try:
        sdk = ctypes.CDLL(lib_path)
        logger.info(f"✅ Loaded HCNetSDK from {lib_path}")
        
        # Init
        if not sdk.NET_DVR_Init():
            logger.error("NET_DVR_Init failed")
            return False
        logger.info("✅ NET_DVR_Init success")
        
        # Set timeouts
        sdk.NET_DVR_SetConnectTime(5000, 3)
        sdk.NET_DVR_SetReconnect(10000, 1)
        
        # Register alarm callback
        callback_ref = CALLBACK_FUNC(sdk_alarm_callback)
        sdk.NET_DVR_SetDVRMessageCallBack_V50(0, callback_ref, None)
        logger.info("✅ Alarm callback registered")
        
        # Start listening for ISUP device connections
        listen_ip = settings.ISUP_LISTEN_IP.encode("utf-8")
        listen_port = settings.ISUP_LISTEN_PORT
        
        listen_handle = sdk.NET_DVR_StartListen_V30(
            listen_ip, listen_port, callback_ref, None
        )
        
        if listen_handle < 0:
            err = sdk.NET_DVR_GetLastError()
            logger.warning(f"⚠️  StartListen_V30 failed (error: {err}). ISUP listening disabled.")
        else:
            logger.info(f"✅ ISUP Listener on {settings.ISUP_LISTEN_IP}:{listen_port}")
        
        sdk_available = True
        return True
        
    except Exception as e:
        logger.error(f"SDK init failed: {e}")
        return False


def login_to_device(host: str, port: int = 8000, 
                    user: str = "admin", password: str = "") -> int:
    """Login to a device via ISAPI for user management."""
    global sdk
    if not sdk_available or not sdk:
        return -1
    
    from ctypes import c_byte, c_char, c_ushort, Structure, byref, sizeof
    
    class NET_DVR_DEVICEINFO_V30(Structure):
        _fields_ = [
            ("sSerialNumber", c_byte * 48),
            ("byAlarmInPortNum", c_byte),
            ("byAlarmOutPortNum", c_byte),
            ("byDiskNum", c_byte),
            ("byDVRType", c_byte),
            ("byChanNum", c_byte),
            ("byStartChan", c_byte),
            ("byAudioChanNum", c_byte),
            ("byIPChanNum", c_byte),
            ("byZeroChanNum", c_byte),
            ("byMainProto", c_byte),
            ("bySubProto", c_byte),
            ("bySupport", c_byte),
            ("bySupport1", c_byte),
            ("bySupport2", c_byte),
            ("wDevType", c_ushort),
            ("bySupport3", c_byte),
            ("byMultiStreamProto", c_byte),
            ("byStartDChan", c_byte),
            ("byStartDTalkChan", c_byte),
            ("byHighDChanNum", c_byte),
            ("bySupport4", c_byte),
            ("byLanguageType", c_byte),
            ("byVoiceInChanNum", c_byte),
            ("byStartVoiceInChanNo", c_byte),
            ("bySupport5", c_byte),
            ("bySupport6", c_byte),
            ("byMirrorChanNum", c_byte),
            ("wStartMirrorChanNo", c_ushort),
            ("bySupport7", c_byte),
            ("byRes2", c_byte),
        ]
    
    device_info = NET_DVR_DEVICEINFO_V30()
    
    user_id = sdk.NET_DVR_Login_V30(
        host.encode("utf-8"),
        port,
        user.encode("utf-8"),
        password.encode("utf-8"),
        byref(device_info)
    )
    
    if user_id < 0:
        err = sdk.NET_DVR_GetLastError()
        logger.error(f"❌ Login to {host}:{port} failed, error: {err}")
        return -1
    
    serial = bytes(device_info.sSerialNumber).decode("utf-8", errors="ignore").strip("\x00")
    logger.info(f"✅ Logged into device {host}:{port} (serial: {serial}, userId: {user_id})")
    return user_id


def sdk_send_isapi(user_id: int, url: str, body: str = "") -> Optional[str]:
    """Send an ISAPI command to a logged-in device via SDK tunnel.
    
    Args:
        user_id: SDK login handle
        url: ISAPI URL path, e.g. "PUT /ISAPI/AccessControl/UserInfo/Record?format=xml"
             Must start with HTTP method (GET/POST/PUT/DELETE)
        body: XML body for POST/PUT requests
    """
    global sdk
    if not sdk_available or not sdk or user_id < 0:
        return None
    
    from ctypes import c_ulong, byref, create_string_buffer
    
    class NET_DVR_XML_CONFIG_INPUT(ctypes.Structure):
        _fields_ = [
            ("dwSize", c_ulong),
            ("lpRequestUrl", ctypes.c_void_p),
            ("dwRequestUrlLen", c_ulong),
            ("lpInBuffer", ctypes.c_void_p),
            ("dwInBufferSize", c_ulong),
        ]
    
    class NET_DVR_XML_CONFIG_OUTPUT(ctypes.Structure):
        _fields_ = [
            ("dwSize", c_ulong),
            ("lpOutBuffer", ctypes.c_void_p),
            ("dwOutBufferSize", c_ulong),
            ("dwReturnedXMLSize", c_ulong),
            ("lpStatusBuffer", ctypes.c_void_p),
            ("dwStatusSize", c_ulong),
        ]
    
    url_bytes = url.encode("utf-8") + b"\0"
    body_bytes = (body.encode("utf-8") + b"\0") if body else b""
    
    url_buf = create_string_buffer(url_bytes, len(url_bytes))
    in_buf = create_string_buffer(body_bytes, len(body_bytes)) if body_bytes else None
    out_buf = create_string_buffer(64 * 1024)
    status_buf = create_string_buffer(4096)
    
    input_param = NET_DVR_XML_CONFIG_INPUT()
    input_param.dwSize = ctypes.sizeof(NET_DVR_XML_CONFIG_INPUT)
    input_param.lpRequestUrl = ctypes.cast(url_buf, ctypes.c_void_p)
    input_param.dwRequestUrlLen = len(url_bytes) - 1  # exclude null
    input_param.lpInBuffer = ctypes.cast(in_buf, ctypes.c_void_p) if in_buf else None
    input_param.dwInBufferSize = (len(body_bytes) - 1) if body_bytes else 0
    
    output_param = NET_DVR_XML_CONFIG_OUTPUT()
    output_param.dwSize = ctypes.sizeof(NET_DVR_XML_CONFIG_OUTPUT)
    output_param.lpOutBuffer = ctypes.cast(out_buf, ctypes.c_void_p)
    output_param.dwOutBufferSize = 64 * 1024
    output_param.lpStatusBuffer = ctypes.cast(status_buf, ctypes.c_void_p)
    output_param.dwStatusSize = 4096
    
    logger.debug(f"ISAPI call: url='{url}', body_len={len(body_bytes)}")
    
    result = sdk.NET_DVR_STDXMLConfig(
        user_id, byref(input_param), byref(output_param)
    )
    
    if result:
        response = out_buf.value.decode("utf-8", errors="ignore")
        logger.info(f"✅ ISAPI {url}: {len(response)} bytes response")
        return response
    else:
        err = sdk.NET_DVR_GetLastError()
        status = status_buf.value.decode("utf-8", errors="ignore")
        logger.error(f"❌ ISAPI {url} failed, error: {err}, status: {status}")
        return None


def cleanup_sdk():
    """Cleanup SDK resources."""
    global sdk, listen_handle, device_user_id
    if sdk:
        if listen_handle >= 0:
            sdk.NET_DVR_StopListen_V30(listen_handle)
        if device_user_id >= 0:
            sdk.NET_DVR_Logout(device_user_id)
        sdk.NET_DVR_Cleanup()
        logger.info("SDK cleaned up")


# ──────── Logging Setup ────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ──────── Lifespan ────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🚀 Hikvision Biometric Bridge v2.0 starting")
    logger.info(f"   Exousia API: {settings.EXOUSIA_API_URL}")
    logger.info(f"   Bridge port: {settings.BRIDGE_PORT}")
    
    # Try to initialize SDK
    if init_sdk():
        logger.info(f"   SDK: ✅ loaded (ISUP port {settings.ISUP_LISTEN_PORT})")
        
        # Try auto-login to configured device
        if settings.HIKVISION_PASSWORD:
            global device_user_id
            device_user_id = login_to_device(
                settings.HIKVISION_HOST,
                settings.HIKVISION_PORT,
                settings.HIKVISION_USER,
                settings.HIKVISION_PASSWORD,
            )
            if device_user_id >= 0:
                logger.info(f"   Device: ✅ connected ({settings.HIKVISION_HOST})")
            else:
                logger.info(f"   Device: ⚠️  not reachable (user management via ISAPI disabled)")
    else:
        logger.info("   SDK: ⚠️  not available")
    
    logger.info(f"   HTTP Webhook: ✅ /hikvision/events (always active)")
    logger.info("=" * 60)
    
    yield
    cleanup_sdk()


# ──────── FastAPI App ────────
app = FastAPI(
    title="Hikvision Biometric Bridge",
    version="2.0.0",
    lifespan=lifespan,
)


# ──────── Webhook endpoint ────────

@app.post("/hikvision/events")
async def receive_hikvision_event(request: Request):
    """Receives XML events from the Hikvision terminal HTTP Listening feature."""
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    logger.info(f"📥 Event from {request.client.host} ({len(body)} bytes)")
    result = await event_receiver.handle_event(body, content_type)
    return JSONResponse(content=result)


@app.post("/")
async def receive_event_root(request: Request):
    return await receive_hikvision_event(request)


# ──────── Simulation ────────

class SimulatedEvent(BaseModel):
    registration_number: str
    timestamp: str = ""

@app.post("/simulate/event")
async def simulate_event(event: SimulatedEvent):
    ts = datetime.now()
    if event.timestamp:
        try: ts = datetime.fromisoformat(event.timestamp)
        except ValueError: pass
    
    result = await exousia.send_attendance(event.registration_number, ts)
    if result:
        return {"status": "ok", "forwarded": True}
    raise HTTPException(status_code=502, detail="Failed to forward to Exousia API")


# ──────── Device User Management (ISAPI HTTP) ────────

class UserCreateRequest(BaseModel):
    employee_no: str
    name: str

@app.post("/device/users")
async def create_device_user(user: UserCreateRequest, host: str = "", port: int = 80, protocol: str = "http"):
    """Push a user to the device via ISAPI HTTP."""
    from app.user_sync import HikvisionUserManager
    
    mgr = HikvisionUserManager(
        host=host or settings.HIKVISION_HOST,
        port=port,
        protocol=protocol,
        username=settings.HIKVISION_USER,
        password=settings.HIKVISION_PASSWORD,
    )
    result = await mgr.add_user(
        employee_no=user.employee_no,
        name=user.name,
    )
    
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)


@app.get("/device/users")
async def list_device_users(host: str = "", port: int = 80, protocol: str = "http"):
    """List users on the device via ISAPI HTTP."""
    from app.user_sync import HikvisionUserManager
    
    mgr = HikvisionUserManager(
        host=host or settings.HIKVISION_HOST,
        port=port,
        protocol=protocol,
        username=settings.HIKVISION_USER,
        password=settings.HIKVISION_PASSWORD,
    )
    result = await mgr.search_users()
    
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)


@app.delete("/device/users/{employee_no}")
async def delete_device_user(employee_no: str, host: str = "", port: int = 80, protocol: str = "http"):
    """Delete a user from the device."""
    from app.user_sync import HikvisionUserManager
    
    mgr = HikvisionUserManager(
        host=host or settings.HIKVISION_HOST,
        port=port,
        protocol=protocol,
        username=settings.HIKVISION_USER,
        password=settings.HIKVISION_PASSWORD,
    )
    result = await mgr.delete_user(employee_no)
    
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)


@app.post("/device/users/{employee_no}/fingerprint")
async def start_fingerprint_capture(employee_no: str, finger_no: int = 1, host: str = "", port: int = 80, protocol: str = "http"):
    """Trigger fingerprint capture on the device for a user."""
    from app.user_sync import HikvisionUserManager
    
    mgr = HikvisionUserManager(
        host=host or settings.HIKVISION_HOST,
        port=port,
        protocol=protocol,
        username=settings.HIKVISION_USER,
        password=settings.HIKVISION_PASSWORD,
    )
    result = await mgr.capture_fingerprint(employee_no, finger_no)
    
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)


@app.get("/device/capabilities")
async def get_device_capabilities(host: str = "", port: int = 80, protocol: str = "http"):
    """Get device access control capabilities."""
    from app.user_sync import HikvisionUserManager
    
    mgr = HikvisionUserManager(
        host=host or settings.HIKVISION_HOST,
        port=port,
        protocol=protocol,
        username=settings.HIKVISION_USER,
        password=settings.HIKVISION_PASSWORD,
    )
    return await mgr.get_capabilities()


@app.post("/device/login")
async def device_login(host: str = "", port: int = 7667,
                       user: str = "admin", password: str = ""):
    """Manually login to a device via SDK."""
    global device_user_id
    
    host = host or settings.HIKVISION_HOST
    password = password or settings.HIKVISION_PASSWORD
    
    if not password:
        raise HTTPException(status_code=400, detail="Password required")
    
    device_user_id = login_to_device(host, port, user, password)
    if device_user_id >= 0:
        return {"status": "ok", "user_id": device_user_id, "host": host}
    raise HTTPException(status_code=503, detail="Login failed")


# ──────── Health check ────────

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "sdk_loaded": sdk_available,
        "isup_listening": listen_handle >= 0,
        "device_connected": device_user_id >= 0,
        "device_host": settings.HIKVISION_HOST,
        "webhook_endpoint": "/hikvision/events",
        "exousia_api": settings.EXOUSIA_API_URL,
    }
