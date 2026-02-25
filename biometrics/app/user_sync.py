"""
Hikvision ISUP Bridge - User Sync
Pushes student profiles (name + registration_number) to the Hikvision device
so fingerprints can be enrolled locally at the terminal.
"""
import httpx
import logging
from typing import Optional
from xml.etree import ElementTree as ET

from app.config import settings

logger = logging.getLogger(__name__)


class HikvisionUserManager:
    """
    Manages user profiles on the Hikvision terminal via ISAPI over HTTP.
    Note: Even when using ISUP for events, user management is often done
    via ISAPI HTTP calls to the device's local IP when on the same network,
    OR via the ISUP tunnel if the SDK supports remote configuration.
    """

    def __init__(self, device_ip: str, username: str, password: str):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.base_url = f"http://{device_ip}"

    async def add_user(
        self,
        employee_no: str,
        name: str,
        valid_begin: str = "2024-01-01T00:00:00",
        valid_end: str = "2030-12-31T23:59:59",
    ) -> bool:
        """
        Register a user on the Hikvision terminal.
        The user can then enroll their fingerprint directly on the device.

        Args:
            employee_no: Registration number (matrícula)
            name: Student's full name
            valid_begin: Validity start (ISO format)
            valid_end: Validity end (ISO format)
        """
        url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Record?format=json"
        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": name,
                "userType": "normal",
                "Valid": {
                    "enable": True,
                    "beginTime": valid_begin,
                    "endTime": valid_end,
                },
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ],
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    auth=httpx.DigestAuth(self.username, self.password),
                )

            if response.status_code == 200:
                logger.info(f"✅ User {employee_no} ({name}) added to device")
                return True
            else:
                logger.error(
                    f"❌ Failed to add user {employee_no}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except httpx.RequestError as e:
            logger.error(f"❌ Cannot reach device at {self.device_ip}: {e}")
            return False

    async def delete_user(self, employee_no: str) -> bool:
        """Remove a user from the Hikvision terminal."""
        url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [
                    {"employeeNo": employee_no}
                ]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    url,
                    json=payload,
                    auth=httpx.DigestAuth(self.username, self.password),
                )

            if response.status_code == 200:
                logger.info(f"✅ User {employee_no} deleted from device")
                return True
            else:
                logger.error(
                    f"❌ Failed to delete user {employee_no}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except httpx.RequestError as e:
            logger.error(f"❌ Cannot reach device at {self.device_ip}: {e}")
            return False

    async def list_users(self) -> Optional[dict]:
        """List all users registered on the device."""
        url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"
        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "maxResults": 100,
                "searchResultPosition": 0,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    auth=httpx.DigestAuth(self.username, self.password),
                )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to list users: {response.status_code}")
                return None

        except httpx.RequestError as e:
            logger.error(f"❌ Cannot reach device: {e}")
            return None

    async def start_fingerprint_capture(self, employee_no: str, finger_id: int = 1) -> bool:
        """
        Initiate fingerprint capture mode on the device for a specific user.
        The student must physically place their finger on the reader.

        Args:
            employee_no: The student's registration number
            finger_id: Which finger (1-10)
        """
        url = f"{self.base_url}/ISAPI/AccessControl/FingerPrint/SetUp?format=json"
        payload = {
            "FingerPrintCfg": {
                "employeeNo": employee_no,
                "enableCardReader": [1],
                "fingerPrintID": finger_id,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    auth=httpx.DigestAuth(self.username, self.password),
                )

            if response.status_code == 200:
                logger.info(
                    f"✅ Fingerprint capture started for {employee_no} "
                    f"(finger #{finger_id}). Student must touch the reader now."
                )
                return True
            else:
                logger.error(
                    f"❌ Failed to start capture for {employee_no}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except httpx.RequestError as e:
            logger.error(f"❌ Cannot reach device: {e}")
            return False
