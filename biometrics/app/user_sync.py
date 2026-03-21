"""
Hikvision Bridge - User Sync via ISAPI HTTP

Manages users on the Hikvision DS-K1T342MFWX access control terminal
using ISAPI REST endpoints (HTTP Digest auth).

Reference ISAPI endpoints for access control:
  - POST /ISAPI/AccessControl/UserInfo/Record?format=json  → Add user
  - PUT  /ISAPI/AccessControl/UserInfo/Modify?format=json   → Modify user
  - POST /ISAPI/AccessControl/UserInfo/Search?format=json   → Search users
  - PUT  /ISAPI/AccessControl/UserInfo/Delete?format=json   → Delete user
  - POST /ISAPI/AccessControl/FingerPrint/SetUp?format=json → Set fingerprints
  - POST /ISAPI/AccessControl/FingerPrint/Capture           → Capture fingerprint
"""
import httpx
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class HikvisionUserManager:
    """
    Manages users on the device.
    Prioritizes Hik Device Gateway (Build 2025) for stable cloud communication.
    Fallbacks: SDK Tunnel (ISUP) -> Direct HTTP.
    """

    def __init__(self, host: str = None, port: int = None,
                 username: str = None, password: str = None, 
                 protocol: str = "http", dev_index: str = None):
        
        # Prefer settings but allow override
        self.host = host or settings.HIKVISION_HOST
        self.port = port or settings.HIKVISION_PORT
        self.username = username or settings.HIKVISION_USER
        self.password = password or settings.HIKVISION_PASSWORD
        self.dev_index = dev_index or settings.HIKVISION_DEV_INDEX
        self.gateway_url = settings.GATEWAY_URL
        
        self.auth = httpx.DigestAuth(self.username, self.password)
        
        logger.info(f"UserManager initialized. Gateway: {self.gateway_url} | Device: {self.host}")

    async def _request(self, method: str, path: str, 
                       json_data: dict = None, xml_data: str = None) -> dict:
        """Prioritizes Gateway -> SDK Tunnel -> Direct HTTP."""
        
        # 1. TENTATIVA VIA HIK DEVICE GATEWAY (Recomendado para Produção/Cloud)
        if self.gateway_url:
            try:
                # O Gateway serve como um proxy ISAPI. 
                # Adicionamos devIndex para identificar qual dispositivo comandar.
                connector = "&" if "?" in path else "?"
                gateway_path = f"{path}{connector}devIndex={self.dev_index}"
                url = f"{self.gateway_url}{gateway_path}"
                
                logger.info(f"🚀 Usando Hik Gateway: {method} {url}")
                
                async with httpx.AsyncClient(auth=self.auth, timeout=20.0, verify=False) as client:
                    response = await client.request(
                        method, url, json=json_data, 
                        content=xml_data.encode("utf-8") if xml_data else None
                    )
                
                if response.status_code in (200, 201):
                    return {"status": "ok", "data": response.json() if "json" in response.headers.get("Content-Type", "") else response.text}
                else:
                    logger.warning(f"⚠️ Gateway retornou {response.status_code}. Tentando fallback...")
            except Exception as e:
                logger.error(f"❌ Erro ao usar Gateway: {e}")

        # 2. TENTATIVA VIA TÚNEL SDK (ISUP/EHome Classic)
        try:
            from app.main import device_user_id, sdk_available, sdk_send_isapi
            import json
            
            if sdk_available and device_user_id >= 0:
                logger.info(f"🔄 Fallback: Usando Túnel SDK para ISAPI: {method} {path}")
                
                body_str = xml_data or (json.dumps(json_data) if json_data else "")
                url = f"{method} {path}"
                
                result_str = sdk_send_isapi(device_user_id, url, body_str)
                
                if result_str is not None:
                    try:
                        parsed = json.loads(result_str)
                        return {"status": "ok", "data": parsed}
                    except Exception:
                        return {"status": "ok", "data": result_str}
        except Exception as e:
            logger.debug(f"Erro no túnel SDK (esperado se não conectado): {e}")

        # 3. ÚLTIMO RECURSO: CONEXÃO DIRETA (Só funciona se estiver na mesma rede local)
        port_str = f":{self.port}" if self.port not in (80, 443) else ""
        direct_url = f"http://{self.host}{port_str}{path}"
        logger.info(f"🌐 Fallback final: Requisição HTTP direta: {method} {direct_url}")
        
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=10.0, verify=False) as client:
                response = await client.request(method, direct_url, json=json_data, content=xml_data)
            
            if response.status_code in (200, 201):
                return {"status": "ok", "data": response.json()}
            return {"status": "error", "code": response.status_code, "message": response.text}
        except Exception as e:
            return {"status": "error", "message": f"All connection attempts failed: {str(e)}"}

    async def search_users(self, start: int = 0, count: int = 30) -> dict:
        """Search/list users on the device."""
        body = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "maxResults": count,
                "searchResultPosition": start
            }
        }
        return await self._request(
            "POST", "/ISAPI/AccessControl/UserInfo/Search?format=json",
            json_data=body
        )

    async def add_user(self, employee_no: str, name: str,
                       user_type: str = "normal") -> dict:
        """Add a user to the device (Gateway format: UserInfo as array)."""
        body = {
            "UserInfo": [{
                "employeeNo": employee_no,
                "name": name,
                "userType": user_type,
                "Valid": {
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2037-12-31T23:59:59"
                }
            }]
        }
        return await self._request(
            "POST", "/ISAPI/AccessControl/UserInfo/Record?format=json",
            json_data=body
        )

    async def delete_user(self, employee_no: str) -> dict:
        """Delete a user from the device."""
        body = {
            "UserInfoDelCond": {
                "EmployeeNoList": [
                    {"employeeNo": employee_no}
                ]
            }
        }
        return await self._request(
            "PUT", "/ISAPI/AccessControl/UserInfo/Delete?format=json",
            json_data=body
        )

    async def get_capabilities(self) -> dict:
        """Get device access control capabilities."""
        return await self._request(
            "GET", "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
        )

    async def capture_fingerprint(self, employee_no: str, 
                                   finger_no: int = 1) -> dict:
        """Start fingerprint capture on the device for a specific user."""
        body = {
            "FingerPrintCond": {
                "employeeNo": employee_no,
                "enableCardReader": [1],
                "fingerPrintID": finger_no
            }
        }
        return await self._request(
            "POST", "/ISAPI/AccessControl/FingerPrint/Capture",
            json_data=body
        )

    async def set_face(self, employee_no: str, face_data_url: str = "") -> dict:
        """Set face data for a user (face recognition enrollment)."""
        body = {
            "FaceInfo": {
                "employeeNo": employee_no,
            }
        }
        return await self._request(
            "POST", "/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json",
            json_data=body
        )

    # === NOVOS MÉTODOS PARA GESTÃO DE DISPOSITIVOS E MIGRAÇÃO ===

    async def get_gateway_devices(self) -> dict:
        """Fetch connected devices from the Hik Device Gateway using POST deviceList."""
        body = {
            "SearchDescription": {
                "position": 0,
                "maxResult": 100,
                "Filter": {
                    "key": "",
                    "devType": "",
                    "protocolType": ["ehomeV5"],
                    "devStatus": ["online", "offline"]
                }
            }
        }
        return await self._request(
            "POST", "/ISAPI/ContentMgmt/DeviceMgmt/deviceList?format=json",
            json_data=body
        )

    async def set_fingerprint(self, employee_no: str, finger_data: str, finger_id: int = 1) -> dict:
        """Add fingerprint to the device via FingerPrintDownload (Gateway endpoint)."""
        body = {
            "FingerPrintCfg": {
                "employeeNo": employee_no,
                "fingerPrintID": finger_id,
                "fingerData": finger_data
            }
        }
        return await self._request(
            "POST", "/ISAPI/AccessControl/FingerPrintDownload?format=json",
            json_data=body
        )

    async def capture_fingerprint_on_device(self, finger_no: int = 1) -> dict:
        """Trigger fingerprint capture on the physical device reader."""
        body = {
            "CaptureFingerPrintCond": {
                "fingerNo": finger_no
            }
        }
        return await self._request(
            "POST", "/ISAPI/AccessControl/CaptureFingerPrint?format=json",
            json_data=body
        )

    async def set_face_data(self, employee_no: str, data: dict) -> dict:
        """Add face data to the device via FaceDataRecord (Gateway endpoint)."""
        return await self._request(
            "POST", "/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json",
            json_data=data
        )
