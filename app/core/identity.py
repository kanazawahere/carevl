import uuid
from app.core.config import settings

CAREVL_NAMESPACE = uuid.UUID(settings.CAREVL_NAMESPACE_UUID)

def generate_encounter_uuid(site_id: str, cccd: str, timestamp_iso: str) -> str:
    """
    Generates a UUIDv5 for an Encounter based on SiteID, CCCD, and ISO 8601 Timestamp.
    Formula: UUIDv5(Namespace, SiteID + CCCD + Timestamp)
    """
    name_string = f"{site_id}{cccd}{timestamp_iso}"
    return str(uuid.uuid5(CAREVL_NAMESPACE, name_string))
