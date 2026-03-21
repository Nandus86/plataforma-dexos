import logging
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import httpx

from app.database import get_db
from app.models.device import Device
from app.models.user import User, UserRole
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DeviceResponse)
async def create_device(device_in: DeviceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).filter(Device.dev_index == device_in.dev_index))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Device already registered")
    
    device = Device(**device_in.dict())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    tenant_id: Optional[UUID] = None, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Device)
    if tenant_id:
        query = query.filter(Device.tenant_id == tenant_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: UUID, device_in: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    return device

@router.delete("/{device_id}")
async def delete_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await db.delete(device)
    await db.commit()
    return {"status": "ok"}

# --- Proxy Endpoints to Biometrics Bridge ---

@router.get("/gateway/connected-devices")
async def get_connected_gateway_devices():
    """Proxy to get real-time connected devices from the Hik Gateway via Biometrics Bridge."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.BIOMETRICS_SERVICE_URL}/gateway/devices")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all")
async def sync_all_students_to_devices(
    device_ids: List[UUID] = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    """Bulk sync: query all students and POST each one to biometrics bridge for each selected device."""
    # 1. Fetch selected devices to get their dev_index
    devices_result = await db.execute(
        select(Device).filter(Device.id.in_(device_ids), Device.is_active == True)
    )
    devices = devices_result.scalars().all()
    if not devices:
        raise HTTPException(status_code=404, detail="No active devices found for given IDs")

    # 2. Fetch all students (role == ALUNO)
    students_result = await db.execute(
        select(User).filter(User.role == UserRole.ESTUDANTE, User.is_active == True)
    )
    students = students_result.scalars().all()

    if not students:
        return {"status": "completed", "synced": 0, "errors": 0, "message": "Nenhum aluno ativo encontrado"}

    # 3. For each device, send each student to the biometrics bridge
    synced = 0
    errors = 0
    bio_url = f"{settings.BIOMETRICS_SERVICE_URL}/device/users"

    async with httpx.AsyncClient(timeout=15.0) as client:
        for device in devices:
            for student in students:
                try:
                    ra = str(student.registration_number) if student.registration_number else str(student.id)[:8]
                    await client.post(bio_url, json={
                        "employee_no": ra,
                        "name": student.name,
                        "dev_index": device.dev_index
                    })
                    synced += 1
                except Exception as e:
                    logger.error(f"Sync error: student={student.name} device={device.name}: {e}")
                    errors += 1

    return {
        "status": "completed",
        "synced": synced,
        "errors": errors,
        "devices": len(devices),
        "students": len(students)
    }


class MigrateBiometricsRequest(BaseModel):
    employee_no: str
    transmitter_index: str
    receiver_index: str
    types: List[str]  # ["fingerprint", "face", "password"]


@router.post("/migrate-biometrics")
async def migrate_biometrics(req: MigrateBiometricsRequest):
    """Proxy to migrate biometric data between terminals."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {
                "employee_no": req.employee_no,
                "transmitter_index": req.transmitter_index,
                "receiver_index": req.receiver_index,
                "types": req.types
            }
            response = await client.post(
                f"{settings.BIOMETRICS_SERVICE_URL}/gateway/transfer/biometrics",
                json=payload
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
