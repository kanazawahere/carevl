"""Persist station identity after invite-code provisioning."""

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig

STATION_ID_KEY = "carevl_station_id"
STATION_NAME_KEY = "carevl_station_name"
REPO_URL_KEY = "carevl_repo_url"


def save_station_identity(db: Session, station_id: str, station_name: str, repo_url: str) -> None:
    pairs = {
        STATION_ID_KEY: station_id,
        STATION_NAME_KEY: station_name,
        REPO_URL_KEY: repo_url,
    }
    for key, value in pairs.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemConfig(key=key, value=value))


def get_station_id(db: Session) -> str | None:
    row = db.query(SystemConfig).filter(SystemConfig.key == STATION_ID_KEY).first()
    return row.value if row else None


def get_station_repo_url(db: Session) -> str | None:
    row = db.query(SystemConfig).filter(SystemConfig.key == REPO_URL_KEY).first()
    return row.value if row else None
