"""
Hikvision Bridge - HTTP Webhook Event Receiver

Receives HTTP POST events from the Hikvision DS-K1T342MFWX
access control terminal via its "HTTP Listening" feature.

The device sends XML payloads on each biometric event (fingerprint match).
This module parses the XML and extracts the student's employeeNo and timestamp.

Production Flow:
  Device (school LAN) → HTTPS POST → Bridge (Easypanel cloud) → Exousia API
"""
import logging
from datetime import datetime
from typing import Optional, Callable
import xmltodict

logger = logging.getLogger(__name__)


class HikvisionEventReceiver:
    """
    Parses HTTP events from Hikvision access control terminals.
    The device is configured in: Network > Advanced > HTTP Listening
    to POST events to our Bridge endpoint.
    """

    def __init__(self, on_attendance_event: Optional[Callable] = None):
        self.on_attendance_event = on_attendance_event

    async def handle_event(self, body: bytes, content_type: str = "") -> dict:
        """
        Parse a raw HTTP event payload from the device.
        Returns dict with parsed event info.
        """
        try:
            # Hikvision sends XML or multipart (with image + XML)
            if b"<EventNotificationAlert" in body or b"<AccessControllerEvent" in body:
                return await self._parse_xml_event(body)
            elif b"--boundary" in body.lower() or "multipart" in content_type.lower():
                return await self._parse_multipart_event(body, content_type)
            else:
                # Try XML anyway
                return await self._parse_xml_event(body)

        except Exception as e:
            logger.error(f"Failed to parse event: {e}", exc_info=True)
            logger.debug(f"Raw body ({len(body)} bytes): {body[:500]}")
            return {"status": "error", "message": str(e)}

    async def _parse_xml_event(self, body: bytes) -> dict:
        """Parse a pure XML event."""
        text = body.decode("utf-8", errors="ignore")
        logger.debug(f"Raw XML event:\n{text[:1000]}")

        parsed = xmltodict.parse(text)

        # Try EventNotificationAlert wrapper
        alert = parsed.get("EventNotificationAlert", parsed)

        # Extract event type
        event_type = alert.get("eventType", "unknown")
        event_state = alert.get("eventState", "")
        event_description = alert.get("eventDescription", "")

        logger.info(f"📡 Event received: type={event_type}, state={event_state}")

        # For AccessControllerEvent
        acs_info = alert.get("AccessControllerEvent", {})
        if not acs_info and "AccessControllerEvent" in parsed:
            acs_info = parsed["AccessControllerEvent"]

        employee_no = acs_info.get("employeeNoString", "")
        if not employee_no:
            employee_no = acs_info.get("employeeNo", "")

        card_no = acs_info.get("cardNo", "")
        name = acs_info.get("name", "")
        door_no = acs_info.get("doorNo", "")
        event_time_str = alert.get("dateTime", "")
        verify_mode = acs_info.get("currentVerifyMode", "")

        # Parse timestamp
        event_time = datetime.now()
        if event_time_str:
            try:
                # Hikvision format: 2024-01-15T14:30:00+08:00
                clean = event_time_str.replace("T", " ").split("+")[0].split(".")[0]
                event_time = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            except (ValueError, IndexError):
                logger.warning(f"Could not parse dateTime: {event_time_str}")

        result = {
            "status": "ok",
            "event_type": event_type,
            "employee_no": employee_no,
            "card_no": card_no,
            "name": name,
            "door_no": door_no,
            "verify_mode": verify_mode,
            "timestamp": event_time.isoformat(),
        }

        logger.info(
            f"🎯 Parsed event: employee={employee_no}, name={name}, "
            f"verify={verify_mode}, time={event_time}"
        )

        # Forward to Exousia if we have an employeeNo
        if employee_no and self.on_attendance_event:
            await self.on_attendance_event(employee_no, event_time)

        return result

    async def _parse_multipart_event(self, body: bytes, content_type: str) -> dict:
        """
        Parse multipart event (XML/JSON + image).
        The device may include a face snapshot in multipart format.
        Hikvision uses custom boundaries like '--MIME_boundary' or similar.
        """
        # Log the raw body for debugging
        logger.info(f"📦 Raw multipart body ({len(body)} bytes, content-type: {content_type})")
        logger.debug(f"   First 1500 bytes:\n{body[:1500]}")

        # Strategy 1: Try to find XML anywhere in the body
        xml_tags = [b"<?xml", b"<EventNotificationAlert", b"<AccessControllerEvent"]
        xml_start = -1
        for tag in xml_tags:
            pos = body.find(tag)
            if pos >= 0:
                xml_start = pos
                break

        if xml_start >= 0:
            # Find end of XML
            end_tags = [
                (b"</EventNotificationAlert>", len(b"</EventNotificationAlert>")),
                (b"</AccessControllerEvent>", len(b"</AccessControllerEvent>")),
            ]
            for end_tag, end_len in end_tags:
                xml_end = body.find(end_tag, xml_start)
                if xml_end >= 0:
                    xml_part = body[xml_start:xml_end + end_len]
                    logger.info(f"✅ Found XML part ({len(xml_part)} bytes)")
                    return await self._parse_xml_event(xml_part)

        # Strategy 2: Split by multipart boundary and check each part
        boundary = None
        if "boundary=" in content_type:
            boundary = content_type.split("boundary=")[-1].strip().strip('"')
        
        if not boundary:
            # Try to detect boundary from body itself
            first_line = body.split(b"\r\n")[0].split(b"\n")[0]
            if first_line.startswith(b"--"):
                boundary = first_line[2:].decode("utf-8", errors="ignore").strip()

        if boundary:
            logger.debug(f"   Boundary: {boundary}")
            parts = body.split(f"--{boundary}".encode())
            for i, part in enumerate(parts):
                part_lower = part.lower()
                # Check for JSON content
                if b"application/json" in part_lower or b'"event' in part_lower:
                    # Extract JSON portion
                    json_start = part.find(b"{")
                    if json_start >= 0:
                        json_end = part.rfind(b"}") + 1
                        if json_end > json_start:
                            try:
                                import json
                                json_data = json.loads(part[json_start:json_end])
                                logger.info(f"✅ Found JSON event in part {i}")
                                return await self._parse_json_event(json_data)
                            except json.JSONDecodeError:
                                pass

                # Check for XML content in this part
                for tag in xml_tags:
                    if tag in part:
                        tag_pos = part.find(tag)
                        for end_tag, end_len in end_tags:
                            end_pos = part.find(end_tag, tag_pos)
                            if end_pos >= 0:
                                xml_part = part[tag_pos:end_pos + end_len]
                                logger.info(f"✅ Found XML in multipart part {i} ({len(xml_part)} bytes)")
                                return await self._parse_xml_event(xml_part)

        # Strategy 3: Try JSON parse on the entire body
        try:
            import json
            json_start = body.find(b"{")
            if json_start >= 0:
                json_end = body.rfind(b"}") + 1
                json_data = json.loads(body[json_start:json_end])
                logger.info("✅ Parsed entire body as JSON")
                return await self._parse_json_event(json_data)
        except (json.JSONDecodeError, ValueError):
            pass

        logger.warning(f"⚠️ Could not parse multipart event. Raw body:\n{body[:2000]}")
        return {"status": "error", "message": "No XML/JSON found in multipart body"}

    async def _parse_json_event(self, data: dict) -> dict:
        """Parse a JSON event from the Hikvision device."""
        logger.info(f"📋 Full JSON event data: {data}")

        # Hikvision JSON event structure
        event_type = data.get("eventType", data.get("EventNotificationAlert", {}).get("eventType", "unknown"))
        
        acs_info = data.get("AccessControllerEvent", {})
        if not acs_info:
            alert = data.get("EventNotificationAlert", {})
            acs_info = alert.get("AccessControllerEvent", {})

        employee_no = acs_info.get("employeeNoString", "") or acs_info.get("employeeNo", "")
        name = acs_info.get("name", "")
        event_time_str = data.get("dateTime", "") or data.get("EventNotificationAlert", {}).get("dateTime", "")

        event_time = datetime.now()
        if event_time_str:
            try:
                # Python 3.11+ handles ISO 8601 with timezone offsets like "-03:00"
                event_time = datetime.fromisoformat(event_time_str)
                logger.info(f"⏱️ Parsed timestamp: {event_time} (from '{event_time_str}')")
            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️ Failed to parse timestamp '{event_time_str}': {e}, using now()")
                pass

        result = {
            "status": "ok",
            "event_type": event_type,
            "employee_no": str(employee_no),
            "name": name,
            "timestamp": event_time.isoformat(),
        }

        logger.info(f"🎯 JSON event: employee={employee_no}, name={name}, time={event_time}")

        if employee_no and self.on_attendance_event:
            await self.on_attendance_event(str(employee_no), event_time)

        return result
