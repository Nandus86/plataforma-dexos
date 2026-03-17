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

@app.post("/device/users")
async def create_device_user(user: UserCreateRequest):
    mgr = HikvisionUserManager()
    result = await mgr.add_user(
        employee_no=user.employee_no,
        name=user.name,
    )
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

@app.get("/device/users")
async def list_device_users():
    mgr = HikvisionUserManager()
    result = await mgr.search_users()
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

@app.delete("/device/users/{employee_no}")
async def delete_device_user(employee_no: str):
    mgr = HikvisionUserManager()
    result = await mgr.delete_user(employee_no)
    if result.get("status") == "ok":
        return result
    raise HTTPException(status_code=500, detail=result)

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
