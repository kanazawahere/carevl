from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api.endpoints import router as api_router
from app.api.ui_routes import router as ui_router
from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.api.provision_routes import router as provision_router
from app.api.settings_routes import router as settings_router
from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import app.models  # noqa: F401
from app.services.snapshot import scheduled_snapshot_job
from app.services.pin_vault import is_provisioned
from app.services.provision_state import get_station_id

# Initialize the database tables if they don't exist
Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()


def _hydrate_site_id_from_db() -> None:
    """After provision, snapshot filenames use station id from system_config."""
    try:
        with SessionLocal() as db:
            sid = get_station_id(db)
            if sid:
                settings.SITE_ID = sid
    except Exception:
        pass


_hydrate_site_id_from_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    _hydrate_site_id_from_db()
    # Setup background task to snapshot and cleanup every 15 minutes
    scheduler.add_job(scheduled_snapshot_job, 'interval', minutes=15)
    scheduler.start()
    yield
    # Shutdown scheduler when app exits
    scheduler.shutdown()

app = FastAPI(
    title="CareVL Edge",
    description="Offline-first health screening app for community health stations",
    version="2.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(provision_router)
app.include_router(settings_router)
app.include_router(api_router)
app.include_router(ui_router)
app.include_router(admin_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    db = SessionLocal()
    try:
        if not is_provisioned(db):
            return RedirectResponse(url="/provision/")
        return RedirectResponse(url="/login")
    finally:
        db.close()
