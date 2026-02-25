"""
Hikvision ISUP Bridge - ISUP Server
Wraps the HCNetSDK C library via ctypes to act as an ISUP (EHome) server.
Receives device connections and access control events.
"""
import ctypes
import logging
import asyncio
import os
import platform
from ctypes import (
    c_int, c_uint, c_char_p, c_void_p, c_bool, c_long, c_ulong,
    POINTER, Structure, CFUNCTYPE, byref, sizeof
)
from datetime import datetime
from typing import Optional, Callable

from app.config import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# HCNetSDK C Structure Definitions
# ──────────────────────────────────────────────

class NET_DVR_ALARMER(Structure):
    """Device info attached to alarm callbacks."""
    _fields_ = [
        ("byUserIDValid", ctypes.c_byte),
        ("bySerialValid", ctypes.c_byte),
        ("byVersionValid", ctypes.c_byte),
        ("byDeviceNameValid", ctypes.c_byte),
        ("byMacAddrValid", ctypes.c_byte),
        ("byLinkPortValid", ctypes.c_byte),
        ("byDeviceIPValid", ctypes.c_byte),
        ("bySocketIPValid", ctypes.c_byte),
        ("lUserID", c_long),
        ("sSerialNumber", ctypes.c_char * 48),
        ("dwDeviceVersion", c_ulong),
        ("sDeviceName", ctypes.c_char * 32),
        ("byMacAddr", ctypes.c_byte * 6),
        ("wLinkPort", ctypes.c_ushort),
        ("sDeviceIP", ctypes.c_char * 128),
        ("sSocketIP", ctypes.c_char * 128),
    ]


class NET_DVR_ACS_ALARM_INFO(Structure):
    """Access Control System alarm information."""
    _fields_ = [
        ("dwSize", c_ulong),
        ("dwMajor", c_ulong),
        ("dwMinor", c_ulong),
        ("struTime", ctypes.c_byte * 32),  # NET_DVR_TIME
        ("sNetUser", ctypes.c_char * 16),
        ("struRemoteHostAddr", ctypes.c_byte * 16),  # NET_DVR_IPADDR
        ("struAcsEventInfo", ctypes.c_byte * 480),  # NET_DVR_ACS_EVENT_INFO (contains employeeNo)
        # Extended fields may vary by SDK version
    ]


# Callback type for ISUP message reception
# bool (__stdcall *MSGCallBack)(LONG lCommand, NET_DVR_ALARMER *pAlarmer, char *pAlarmInfo, DWORD dwBufLen, void* pUser)
if platform.system() == "Windows":
    MSGCALLBACK = CFUNCTYPE(c_bool, c_long, POINTER(NET_DVR_ALARMER), c_char_p, c_ulong, c_void_p)
else:
    MSGCALLBACK = CFUNCTYPE(c_bool, c_long, POINTER(NET_DVR_ALARMER), c_char_p, c_ulong, c_void_p)

# HCNetSDK constants
COMM_ALARM_ACS = 0x5002  # Access control alarm


class HikvisionISUPServer:
    """
    Manages the Hikvision HCNetSDK lifecycle:
    - Initializes the SDK
    - Starts the ISUP listener on a given port
    - Registers an event callback for access control alarms
    """

    def __init__(self, on_attendance_event: Optional[Callable] = None):
        self._sdk = None
        self._listen_handle = -1
        self._callback_ref = None  # prevent GC of the ctypes callback
        self.on_attendance_event = on_attendance_event  # async callable(registration_number, timestamp)

    def _load_sdk(self) -> ctypes.CDLL:
        """Load the HCNetSDK shared library."""
        lib_path = settings.SDK_LIB_PATH

        if not os.path.exists(lib_path):
            logger.error(f"SDK library not found at {lib_path}")
            raise FileNotFoundError(f"HCNetSDK library not found: {lib_path}")

        if platform.system() == "Windows":
            sdk = ctypes.WinDLL(lib_path)
        else:
            sdk = ctypes.CDLL(lib_path)

        logger.info(f"Loaded HCNetSDK from {lib_path}")
        return sdk

    def init(self) -> bool:
        """Initialize the SDK and start listening for ISUP connections."""
        try:
            self._sdk = self._load_sdk()
        except FileNotFoundError:
            logger.warning(
                "⚠️  HCNetSDK not found. Running in SIMULATION mode. "
                "Place the SDK files in the /app/sdk/ directory for production."
            )
            return False

        # NET_DVR_Init
        result = self._sdk.NET_DVR_Init()
        if not result:
            logger.error("NET_DVR_Init failed")
            return False
        logger.info("✅ NET_DVR_Init success")

        # Register the alarm callback
        self._callback_ref = MSGCALLBACK(self._alarm_callback)
        self._sdk.NET_DVR_SetDVRMessageCallBack_V50(0, self._callback_ref, None)
        logger.info("✅ Alarm callback registered")

        # Start listening for ISUP device connections
        listen_ip = settings.ISUP_LISTEN_IP.encode("utf-8")
        listen_port = settings.ISUP_LISTEN_PORT

        self._listen_handle = self._sdk.NET_DVR_StartListen_V30(
            listen_ip, listen_port, MSGCALLBACK(self._alarm_callback), None
        )

        if self._listen_handle < 0:
            err = self._sdk.NET_DVR_GetLastError()
            logger.error(f"NET_DVR_StartListen_V30 failed, error code: {err}")
            return False

        logger.info(f"✅ ISUP Server listening on {settings.ISUP_LISTEN_IP}:{listen_port}")
        return True

    def _alarm_callback(self, command, alarmer, alarm_info, buf_len, user) -> bool:
        """
        C callback invoked by the SDK when a device sends an alarm.
        We care about COMM_ALARM_ACS (access control events).
        """
        try:
            if command == COMM_ALARM_ACS:
                self._handle_acs_event(alarmer, alarm_info, buf_len)
            else:
                logger.debug(f"Received non-ACS alarm command: 0x{command:04X}")
        except Exception as e:
            logger.error(f"Error in alarm callback: {e}", exc_info=True)

        return True

    def _handle_acs_event(self, alarmer, alarm_info, buf_len):
        """
        Parse an access control event to extract employeeNo and timestamp.
        The exact offsets depend on the SDK version; this is a best-effort parse.
        """
        try:
            # Parse raw alarm info bytes
            raw = ctypes.string_at(alarm_info, buf_len)

            # Try to find employeeNo in the raw data
            # In many SDK versions, employeeNo is at a known offset within NET_DVR_ACS_EVENT_INFO
            # For robustness, we also try string scanning
            employee_no = self._extract_employee_no(raw)
            event_time = datetime.now()  # Fallback; ideally parse from event data

            if employee_no:
                device_serial = ""
                if alarmer:
                    device_serial = alarmer.contents.sSerialNumber.decode("utf-8", errors="ignore").strip("\x00")

                logger.info(
                    f"🔒 Access event: employeeNo={employee_no}, "
                    f"device={device_serial}, time={event_time}"
                )

                # Fire the async callback
                if self.on_attendance_event:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(
                            self.on_attendance_event(employee_no, event_time)
                        )
                    else:
                        loop.run_until_complete(
                            self.on_attendance_event(employee_no, event_time)
                        )
            else:
                logger.warning(f"ACS event received but could not extract employeeNo (buf_len={buf_len})")
                logger.debug(f"Raw ACS data (hex): {raw.hex()}")

        except Exception as e:
            logger.error(f"Failed to handle ACS event: {e}", exc_info=True)

    def _extract_employee_no(self, raw: bytes) -> Optional[str]:
        """
        Attempt to extract the employeeNo from raw ACS event data.
        Strategy:
            1. Try known SDK struct offset (dwEmployeeNo at byte offset ~184)
            2. Fallback: scan for ASCII digit sequences that look like registration numbers
        """
        # Strategy 1: struct offset (varies by SDK version)
        # NET_DVR_ACS_EVENT_INFO.dwEmployeeNo is typically a 4-byte uint at a known offset
        # Common offset: 184 bytes from start of NET_DVR_ACS_ALARM_INFO
        try:
            if len(raw) >= 200:
                # Try reading a uint32 at offset 184
                employee_no_int = int.from_bytes(raw[184:188], byteorder="little")
                if 0 < employee_no_int < 999999999:
                    return str(employee_no_int)
        except Exception:
            pass

        # Strategy 2: look for byEmployeeNo string field (later SDK versions)
        # Some versions use a null-terminated string field
        try:
            # Scan for the employeeNo string field (typically 32 bytes at offset ~422)
            if len(raw) >= 460:
                emp_bytes = raw[422:454]
                emp_str = emp_bytes.decode("utf-8", errors="ignore").strip("\x00").strip()
                if emp_str and emp_str.isalnum():
                    return emp_str
        except Exception:
            pass

        return None

    def cleanup(self):
        """Cleanup SDK resources."""
        if self._sdk:
            if self._listen_handle >= 0:
                self._sdk.NET_DVR_StopListen_V30(self._listen_handle)
                logger.info("ISUP listener stopped")
            self._sdk.NET_DVR_Cleanup()
            logger.info("HCNetSDK cleaned up")


# ──────────────────────────────────────────────
# Simulation mode (when SDK is not available)
# ──────────────────────────────────────────────

class SimulatedISUPServer:
    """
    Fallback server that simulates ISUP events via a REST endpoint.
    Useful for development/testing without the physical device.
    """

    def __init__(self, on_attendance_event: Optional[Callable] = None):
        self.on_attendance_event = on_attendance_event

    def init(self) -> bool:
        logger.info("🧪 Running in SIMULATION mode (no HCNetSDK)")
        logger.info("   Use POST /simulate/event to send test attendance events")
        return True

    def cleanup(self):
        pass
