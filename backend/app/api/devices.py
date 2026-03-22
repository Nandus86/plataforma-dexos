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
from app.models.biometric_data import BiometricData
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.schemas.biometric_data import BiometricDataResponse

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
    receiver_index: str
    types: List[str]  # ["fingerprint", "face", "password"]


@router.post("/migrate-biometrics")
async def migrate_biometrics(req: MigrateBiometricsRequest, db: AsyncSession = Depends(get_db)):
    """Injeta biometrias (salvas no banco) de um RA para o terminal destino selecionado."""
    # 1. Busca os dados biométricos salvos para este RA
    bios_query = select(BiometricData).filter(BiometricData.registration_number == req.employee_no)
    bios_res = await db.execute(bios_query)
    bios = bios_res.scalars().all()
    
    if not bios:
        return {"status": "error", "message": f"Nenhuma biometria salva encontrada no banco para RA: {req.employee_no}"}

    results = {"fingerprint": None, "face": None}
    
    # 2. Envia para o aparelho destino
    async with httpx.AsyncClient(timeout=30.0) as client:
        if "fingerprint" in req.types:
            fingers = [b for b in bios if b.biometric_type == "fingerprint"]
            if not fingers:
                results["fingerprint"] = {"status": "error", "message": "Nenhuma digital salva"}
            else:
                success_count = 0
                errors = []
                for finger in fingers:
                    try:
                        res = await client.post(
                            f"{settings.BIOMETRICS_SERVICE_URL}/device/fingerprint",
                            json={
                                "employee_no": req.employee_no,
                                "dev_index": req.receiver_index,
                                "finger_id": finger.finger_id,
                                "finger_data": finger.data
                            }
                        )
                        if res.status_code == 200:
                            success_count += 1
                        else:
                            errors.append(res.text)
                    except Exception as e:
                        errors.append(str(e))
                
                if success_count > 0:
                    results["fingerprint"] = {"status": "ok", "message": f"{success_count} digitais enviadas com sucesso."}
                else:
                    results["fingerprint"] = {"status": "error", "message": f"Falha ao enviar digitais: {errors}"}

        # Para face/password, a mesma lógica poderia ser adicionada futuramente
        if "face" in req.types:
            results["face"] = {"status": "error", "message": "Face não suportada ainda (não implementado DB)."}

    return {"status": "completed", "results": results}


class CaptureFingerprintRequest(BaseModel):
    user_id: UUID
    dev_index: str
    finger_no: int = 1

@router.post("/capture-fingerprint")
async def capture_fingerprint(req: CaptureFingerprintRequest, db: AsyncSession = Depends(get_db)):
    """Ações: 1. Chama Gateway para capturar; 2. Salva no BD; 3. Envia para todos os outros Devices"""
    # 1. Obter usuário e garantir que existe
    user = await db.get(User, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    ra = str(user.registration_number) if user.registration_number else str(user.id)[:8]

    # 2. Chamar Biometrics Bridge para capturar no dev_index informado
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            capture_res = await client.post(
                f"{settings.BIOMETRICS_SERVICE_URL}/gateway/capture-fingerprint",
                json={"dev_index": req.dev_index, "finger_no": req.finger_no}
            )
            capture_data = capture_res.json()
        except Exception as e:
            logger.error(f"Failed to connect to biometrics bridge: {e}")
            raise HTTPException(status_code=500, detail="Falha ao contatar serviço de biometria")

    if capture_data.get("status") != "ok" or not capture_data.get("fingerData"):
        raise HTTPException(status_code=400, detail=f"Falha na captura: {capture_data.get('message', capture_data)}")

    finger_data_b64 = capture_data["fingerData"]

    # 3. Salvar digital no Banco de Dados
    # Primeiro checamos se já existe esse finger_id para esse usuáriol
    existing_query = select(BiometricData).filter(
        BiometricData.user_id == user.id,
        BiometricData.biometric_type == "fingerprint",
        BiometricData.finger_id == req.finger_no
    )
    existing_res = await db.execute(existing_query)
    existing_bio = existing_res.scalars().first()

    if existing_bio:
        existing_bio.data = finger_data_b64
        existing_bio.registration_number = ra
    else:
        new_bio = BiometricData(
            user_id=user.id,
            tenant_id=user.tenant_id,
            registration_number=ra,
            biometric_type="fingerprint",
            finger_id=req.finger_no,
            data=finger_data_b64
        )
        db.add(new_bio)
    
    await db.commit()

    # 4. Distribuir a digital nova para TODOS os devices ativos (incluindo o que originou para garantir sync, ou pular se quiser)
    devices_res = await db.execute(select(Device).filter(Device.is_active == True))
    devices = devices_res.scalars().all()
    
    sync_results = []
    bio_url = f"{settings.BIOMETRICS_SERVICE_URL}/device/users"
    
    # Enviamos a digital capturada para todo mundo 
    # (Em um sistema robusto pode-se chamar um endpoint de sincronizacao especifica)
    async with httpx.AsyncClient(timeout=10.0) as client:
        for d in devices:
            if d.dev_index == req.dev_index:
                # Opcional: pular o device onde foi capturado pois teoricamente ja tem, mas mandar via API garante que ele salvou o usuario localmente
                pass
            
            try:
                # Usa O MESMO ENDPOINT de criar usuario, mas agora teremos que alterar a API de biometria para receber FingerData tb ?
                # Como precisamos enviar uma digital especifica e o endpoint antigo era apenas info do usuario, vamos usar um endpoint de force push
                push_res = await client.post(
                    f"{settings.BIOMETRICS_SERVICE_URL}/device/fingerprint",
                    json={
                        "employee_no": ra,
                        "dev_index": d.dev_index,
                        "finger_id": req.finger_no,
                        "finger_data": finger_data_b64
                    }
                )
                sync_results.append({"device": d.name, "status": "ok", "detail": push_res.json()})
            except Exception as e:
                sync_results.append({"device": d.name, "status": "error", "message": str(e)})

    return {
        "status": "completed",
        "fingerprint": "saved",
        "sync_results": sync_results
    }


@router.get("/biometrics/{user_id}", response_model=List[BiometricDataResponse])
async def get_user_biometrics(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retorna digitais salvas para um usuário"""
    query = select(BiometricData).filter(BiometricData.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/distribute-biometrics/{user_id}")
async def distribute_biometrics(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Reenvia todas as digitais de um aluno para todos terminais ativos (sync forçado)"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    ra = str(user.registration_number) if user.registration_number else str(user.id)[:8]

    bios_res = await db.execute(select(BiometricData).filter(BiometricData.user_id == user_id))
    bios = bios_res.scalars().all()
    
    devices_res = await db.execute(select(Device).filter(Device.is_active == True))
    devices = devices_res.scalars().all()

    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for bio in bios:
            if bio.biometric_type == "fingerprint":
                for d in devices:
                    try:
                        res = await client.post(
                            f"{settings.BIOMETRICS_SERVICE_URL}/device/fingerprint",
                            json={
                                "employee_no": ra,
                                "dev_index": d.dev_index,
                                "finger_id": bio.finger_id,
                                "finger_data": bio.data
                            }
                        )
                        results.append({"device": d.name, "finger_id": bio.finger_id, "status": "ok"})
                    except Exception as e:
                        results.append({"device": d.name, "finger_id": bio.finger_id, "status": "error", "message": str(e)})

    return {"status": "completed", "results": results}

