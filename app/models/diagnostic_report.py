from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class DiagnosticReport(Base):
    """
    FHIR DiagnosticReport equivalent.
    Used for Delayed Results (e.g., Lab tests, X-Rays) mapped by sticker_id.
    """
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    encounter_uuid = Column(String, index=True)

    # E.g., 'lab_results', 'xray_image'
    category = Column(String, index=True)

    # JSON string containing the delayed results payload
    result_payload = Column(String)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
