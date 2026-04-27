from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api.endpoints import router as api_router
from app.api.ui_routes import router as ui_router
from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.core.database import engine, Base
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import app.models  # noqa: F401
from app.services.snapshot import scheduled_snapshot_job

# Initialize the database tables if they don't exist
Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup background task to snapshot and cleanup every 15 minutes
    scheduler.add_job(scheduled_snapshot_job, 'interval', minutes=15)
    scheduler.start()
    yield
    # Shutdown scheduler when app exits
    scheduler.shutdown()

app = FastAPI(
    title="CareVL Backend Engine",
    description="Offline-first FastAPI engine for Care Vinh Long mobile health screening.",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router)
app.include_router(ui_router)
app.include_router(admin_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/login")
