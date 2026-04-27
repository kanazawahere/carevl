from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class MeasureReport(Base):
    """
    FHIR MeasureReport equivalent.
    Used for Aggregate Data Entry (e.g., DHIS2 compatible bulk statistics).
    Not linked to specific individuals.
    """
    __tablename__ = "measure_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    site_id = Column(String, index=True)

    # E.g., 'daily_summary', 'monthly_statistics'
    report_type = Column(String, index=True)

    # JSON string containing the aggregate metrics
    metrics_payload = Column(String)

    period_start = Column(DateTime)
    period_end = Column(DateTime)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
