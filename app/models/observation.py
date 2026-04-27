from sqlalchemy import Column, String, Integer, DateTime, Float
from datetime import datetime, timezone
from app.core.database import Base

class Observation(Base):
    """
    FHIR Observation equivalent.
    Used for clinical data points like vital signs.
    Linked to an Encounter.
    """
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    encounter_uuid = Column(String, index=True)

    # E.g., 'blood_pressure', 'heart_rate', 'temperature'
    code = Column(String, index=True)

    # Simple value mapping for now. Can be extended for units or complex structures.
    value_string = Column(String, nullable=True)
    value_numeric = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
