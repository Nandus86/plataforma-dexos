"""
Hikvision Bridge – FastAPI Application (Gateway Edition)

Architecture:
  1. Events FROM device/gateway → HTTP Webhook (/hikvision/events)
  2. Commands TO device → Routed via Hik Device Gateway API
  3. Forward TO Exousia → REST API calls to /attendance

Strictly following 'No Database Changes' rule.
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.isup_server import HikvisionEventReceiver
from app.exousia_client import ExousiaClient
from app.user_sync import HikvisionUserManager

logger = logging.getLogger(__name__)

# Clients
exousia = ExousiaClient(
    api_url=settings.EXOUSIA_API_URL,
    api_token=settings.EXOUSIA_API_TOKEN,
)

event_receiver = HikvisionEventReceiver(
    on_attendance_event=exousia.send_attendance,
)

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Hikvision Biometric Bridge v2.1 (Gateway Mode) starting")
    logger.info(f"   Exousia API: {settings.EXOUSIA_API_URL}")
    logger.info(f"   Hik Gateway: {settings.GATEWAY_URL}")
    logger.info(f"   Device Index: {settings.HIKVISION_DEV_INDEX}")
    logger.info("=" * 60)
    yield

# FastAPI App
app = FastAPI(
    title="Hikvision Biometric Bridge",
    version="2.1.0",
    lifespan=lifespan,
)

# Webhook endpoint
@app.post("/hikvision/events")
async def receive_hikvision_event(request: Request):
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    logger.info(f"Event received ({len(body)} bytes)")
    result = await event_receiver.handle_event(body, content_type)
    return JSONResponse(content=result)

@app.post("/")
async def receive_event_root(request: Request):
    return await receive_hikvision_event(request)

# Device User Management
class UserCreateRequest(BaseModel):
    employee_no: str
    name: str
    dev_index: str | None = None

@app.post("/device/users")
async def create_device_user(user: UserCreateRequest):
    mgr = HikvisionUserManager(dev_index=user.dev_index)
    result = await mgr.add_user(
        employee_no=user.employee_no,
        name=user.name,
    )
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

@app.get("/device/users")
async def list_device_users(dev_index: str | None = None):
    mgr = HikvisionUserManager(dev_index=dev_index)
    result = await mgr.search_users()
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

@app.delete("/device/users/{employee_no}")
async def delete_device_user(employee_no: str, dev_index: str | None = None):
    mgr = HikvisionUserManager(dev_index=dev_index)
    result = await mgr.delete_user(employee_no)
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

# === Novos Endpoints de Gestão de Dispositivos e Transferência ===

@app.get("/gateway/devices")
async def get_gateway_devices():
    mgr = HikvisionUserManager()
    result = await mgr.get_gateway_devices()
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

class BiometricTransferRequest(BaseModel):
    employee_no: str
    transmitter_index: str
    receiver_index: str
    types: list[str]  # ["face", "fingerprint", "password"]

@app.post("/gateway/transfer/biometrics")
async def transfer_biometrics(req: BiometricTransferRequest):
    tx_mgr = HikvisionUserManager(dev_index=req.transmitter_index)
    rx_mgr = HikvisionUserManager(dev_index=req.receiver_index)
    
    results = {"fingerprint": None, "face": None, "password": None}
    
    # 1. Transferir Digital
    if "fingerprint" in req.types:
        tx_res = await tx_mgr.search_fingerprint(req.employee_no)
        if tx_res.get("status") == "ok":
            # Extrair dados e enviar para o receptor
            rx_res = await rx_mgr.set_fingerprint(req.employee_no, tx_res["data"])
            results["fingerprint"] = rx_res
        else:
            results["fingerprint"] = tx_res

    # 2. Transferir Face
    if "face" in req.types:
        tx_res = await tx_mgr.search_face(req.employee_no)
        if tx_res.get("status") == "ok":
             # Extrair dados e enviar para o receptor
            rx_res = await rx_mgr.set_face_data(req.employee_no, tx_res["data"])
            results["face"] = rx_res
        else:
            results["face"] = tx_res

    return {"status": "completed", "results": results}

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "mode": "gateway",
        "gateway_url": settings.GATEWAY_URL,
        "device_host": settings.HIKVISION_HOST,
        "exousia_api": settings.EXOUSIA_API_URL,
    }
