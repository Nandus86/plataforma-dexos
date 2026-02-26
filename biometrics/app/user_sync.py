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

logger = logging.getLogger(__name__)


class HikvisionUserManager:
    """
    Manages users on the device via ISAPI REST (HTTP Digest Auth).
    Works when Bridge can reach the device over the network or via Tunnel.
    """

    def __init__(self, host: str, port: int = 80,
                 username: str = "admin", password: str = "", protocol: str = "http"):
        
        # If port is 80/443, we typically don't append it for cleaner URLs
        port_str = f":{port}" if port not in (80, 443) else ""
        self.base_url = f"{protocol}://{host}{port_str}"
        self.auth = httpx.DigestAuth(username, password)
        self.host = host
        logger.info(f"UserManager initialized for {self.base_url}")

    async def _request(self, method: str, path: str, 
                       json_data: dict = None, xml_data: str = None) -> dict:
        """Make an ISAPI request with digest auth."""
        url = f"{self.base_url}{path}"
        
        headers = {}
        content = None
        
        if json_data:
            headers["Content-Type"] = "application/json"
        elif xml_data:
            headers["Content-Type"] = "application/xml"
            content = xml_data.encode("utf-8")
        
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=15.0, verify=False) as client:
                response = await client.request(
                    method, url, headers=headers, 
                    json=json_data, content=content
                )
            
            logger.debug(f"ISAPI {method} {path}: {response.status_code}")
            
            if response.status_code in (200, 201):
                try:
                    return {"status": "ok", "data": response.json()}
                except Exception:
                    return {"status": "ok", "data": response.text}
            else:
                logger.error(f"ISAPI error: {response.status_code} - {response.text}")
                return {"status": "error", "code": response.status_code, 
                        "message": response.text}
                        
        except httpx.ConnectError as e:
            logger.error(f"Cannot reach device at {self.host}: {e}")
            return {"status": "error", "message": f"Device unreachable: {self.host}"}
        except Exception as e:
            logger.error(f"ISAPI request failed: {e}")
            return {"status": "error", "message": str(e)}

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
        """Add a user to the device."""
        body = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": name,
                "userType": user_type,
                "Valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2037-12-31T23:59:59",
                    "timeType": "local"
                },
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ]
            }
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
