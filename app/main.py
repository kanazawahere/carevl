from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api.endpoints import router as api_router
from app.api.ui_routes import router as ui_router
from app.core.database import engine, Base
from app.models.encounter import Encounter  # noqa: F401

# Initialize the database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareVL Backend Engine",
    description="Offline-first FastAPI engine for Care Vinh Long mobile health screening.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router)
app.include_router(ui_router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/operator")
