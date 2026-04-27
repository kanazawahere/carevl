from sqlalchemy import Column, String, Integer, DateTime, Boolean
from datetime import datetime, timezone
from app.core.database import Base

class Encounter(Base):
    __tablename__ = "encounters"

    uuid = Column(String, primary_key=True, index=True)
    sticker_id = Column(String, index=True, nullable=True) # Physical sticker barcode
    patient_id = Column(String, index=True) # Should link to a Patient model eventually

    encounter_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    package_id = Column(String, nullable=True)
    author = Column(String, nullable=True)
    station_id = Column(String, index=True)
    commune_code = Column(String, nullable=True)

    sync_state = Column(Boolean, default=False, index=True)
    summary_text = Column(String, nullable=True)
    classification_display = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
