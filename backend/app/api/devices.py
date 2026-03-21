from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx



from app.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.config import settings

router = APIRouter()

@router.post("/", response_model=DeviceResponse)
async def create_device(device_in: DeviceCreate, db: AsyncSession = Depends(get_db)):
    # Check if dev_index already exists
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
    """Trigger a bulk synchronization of all students to multiple devices."""
    # Logic to iterate students and call biometrics bridge for each device
    # For now, just a placeholder for the UI
    return {"status": "started", "device_count": len(device_ids)}

@router.post("/migrate-biometrics")
async def migrate_biometrics(
    employee_no: str, 
    transmitter_index: str, 
    receiver_index: str, 
    types: List[str]
):
    """Proxy to migrate biometric data between terminals."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "employee_no": employee_no,
                "transmitter_index": transmitter_index,
                "receiver_index": receiver_index,
                "types": types
            }
            response = await client.post(
                f"{settings.BIOMETRICS_SERVICE_URL}/gateway/transfer/biometrics",
                json=payload
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
