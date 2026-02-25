"""
Hikvision ISUP Bridge - Main Application
FastAPI server that:
  1. Starts the ISUP listener (HCNetSDK) to receive biometric events from
     Hikvision terminals.
  2. Forwards attendance events to the Exousia School API.
  3. Provides REST endpoints for user management (sync students to device).
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.exousia_client import send_attendance
from app.isup_server import HikvisionISUPServer, SimulatedISUPServer


# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# ISUP Server instance
# ──────────────────────────────────────────────
isup_server = None


async def on_attendance_event(registration_number: str, timestamp):
    """Callback invoked when the ISUP server receives a biometric event."""
    logger.info(f"📡 Biometric event received: {registration_number} at {timestamp}")
    await send_attendance(registration_number, timestamp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global isup_server

    # Try to start with real SDK, fall back to simulation
    isup_server = HikvisionISUPServer(on_attendance_event=on_attendance_event)
    if not isup_server.init():
        logger.warning("Falling back to simulation mode")
        isup_server = SimulatedISUPServer(on_attendance_event=on_attendance_event)
        isup_server.init()

    yield

    # Cleanup
    if isup_server:
        isup_server.cleanup()


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="Hikvision ISUP Bridge",
    description="Ponte entre terminais biométricos Hikvision e a plataforma Exousia School",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/health")
async def health():
    mode = "sdk" if isinstance(isup_server, HikvisionISUPServer) else "simulation"
    return {
        "status": "ok",
        "mode": mode,
        "isup_port": settings.ISUP_LISTEN_PORT,
        "exousia_api": settings.EXOUSIA_API_URL,
    }


# ──────────────────────────────────────────────
# Simulation endpoints (for testing without device)
# ──────────────────────────────────────────────
class SimulateEventRequest(BaseModel):
    registration_number: str
    timestamp: str = ""  # ISO format; auto-fills if empty


@app.post("/simulate/event")
async def simulate_event(req: SimulateEventRequest):
    """
    Simulates a biometric event for testing.
    Sends a fake attendance record to the Exousia API.
    """
    from datetime import datetime

    ts = datetime.fromisoformat(req.timestamp) if req.timestamp else datetime.now()

    success = await send_attendance(req.registration_number, ts)
    if success:
        return {"status": "sent", "registration_number": req.registration_number}
    else:
        raise HTTPException(status_code=502, detail="Failed to forward to Exousia API")


# ──────────────────────────────────────────────
# User management endpoints
# ──────────────────────────────────────────────
class AddUserRequest(BaseModel):
    employee_no: str  # registration_number / matrícula
    name: str
    device_ip: str = ""  # Falls back to env HIKVISION_HOST
    device_user: str = "admin"
    device_password: str = ""


@app.post("/users/sync")
async def sync_user_to_device(req: AddUserRequest):
    """
    Register a student on the Hikvision terminal.
    After this, the student can enroll their fingerprint directly at the device.
    """
    from app.user_sync import HikvisionUserManager

    device_ip = req.device_ip or settings.__dict__.get("HIKVISION_HOST", "192.168.15.10")
    manager = HikvisionUserManager(device_ip, req.device_user, req.device_password)

    success = await manager.add_user(req.employee_no, req.name)
    if success:
        return {"status": "ok", "employee_no": req.employee_no, "message": "User added to device"}
    else:
        raise HTTPException(status_code=502, detail="Failed to add user to Hikvision device")


@app.post("/users/capture-fingerprint")
async def capture_fingerprint(employee_no: str, finger_id: int = 1,
                               device_ip: str = "", device_user: str = "admin",
                               device_password: str = ""):
    """
    Start fingerprint capture mode on the device for a student.
    The student must physically touch the reader after this call.
    """
    from app.user_sync import HikvisionUserManager

    device_ip = device_ip or settings.__dict__.get("HIKVISION_HOST", "192.168.15.10")
    manager = HikvisionUserManager(device_ip, device_user, device_password)

    success = await manager.start_fingerprint_capture(employee_no, finger_id)
    if success:
        return {"status": "ok", "message": f"Waiting for fingerprint on device for {employee_no}"}
    else:
        raise HTTPException(status_code=502, detail="Failed to start fingerprint capture")


@app.delete("/users/{employee_no}")
async def remove_user_from_device(employee_no: str,
                                   device_ip: str = "", device_user: str = "admin",
                                   device_password: str = ""):
    """Remove a student from the Hikvision terminal."""
    from app.user_sync import HikvisionUserManager

    device_ip = device_ip or settings.__dict__.get("HIKVISION_HOST", "192.168.15.10")
    manager = HikvisionUserManager(device_ip, device_user, device_password)

    success = await manager.delete_user(employee_no)
    if success:
        return {"status": "ok", "message": f"User {employee_no} removed from device"}
    else:
        raise HTTPException(status_code=502, detail="Failed to remove user from device")
