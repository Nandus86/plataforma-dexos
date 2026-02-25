"""
Hikvision ISUP Bridge - Exousia API Client
Forwards attendance events to the main Exousia platform.
"""
import httpx
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


async def send_attendance(registration_number: str, timestamp: datetime) -> bool:
    """
    Send a biometric check-in event to the Exousia API.

    Args:
        registration_number: Student's registration number (employeeNo from Hikvision)
        timestamp: When the biometric event occurred

    Returns:
        True if accepted, False otherwise
    """
    url = f"{settings.EXOUSIA_API_URL}/attendance"
    payload = {
        "registration_number": registration_number,
        "checkin_method": "biometric",
        "timestamp": timestamp.isoformat(),
    }

    headers = {"Content-Type": "application/json"}
    if settings.EXOUSIA_API_TOKEN:
        headers["Authorization"] = f"Bearer {settings.EXOUSIA_API_TOKEN}"

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
                f"❌ Exousia rejected attendance: {response.status_code} - {response.text}"
            )
            return False

    except httpx.RequestError as e:
        logger.error(f"❌ Failed to reach Exousia API: {e}")
        return False
