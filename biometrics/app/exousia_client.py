"""
Hikvision Bridge - Exousia API Client
Forwards attendance events to the main Exousia platform.
"""
import httpx
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class ExousiaClient:
    """Client for sending attendance events to Exousia API."""

    def __init__(self, api_url: str = "", api_token: str = ""):
        self.api_url = api_url or settings.EXOUSIA_API_URL
        self.api_token = api_token or settings.EXOUSIA_API_TOKEN

    async def send_attendance(self, registration_number: str, timestamp: datetime) -> bool:
        """
        Send a biometric check-in event to the Exousia API.

        Args:
            registration_number: Student's registration number (employeeNo)
            timestamp: When the biometric event occurred

        Returns:
            True if accepted, False otherwise
        """
        url = f"{self.api_url}/attendance/biometric"
        payload = {
            "registration_number": registration_number,
            "checkin_method": "biometric",
            "timestamp": timestamp.isoformat(),
        }

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code in (200, 201):
                logger.info(
                    f"✅ Attendance sent: {registration_number} at {timestamp}"
                )
                return True
            else:
                logger.error(
                    f"❌ Exousia rejected: {response.status_code} - {response.text}"
                )
                return False

        except httpx.RequestError as e:
            logger.error(f"❌ Failed to reach Exousia API: {e}")
            return False
