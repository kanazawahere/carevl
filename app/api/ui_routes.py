from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.identity import generate_encounter_uuid
from app.core.config import settings
from app.models.encounter import Encounter

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/operator", response_class=HTMLResponse)
def get_operator_page(request: Request, db: Session = Depends(get_db)):
    # Get today's encounters for the waiting list
    today_encounters = db.query(Encounter).order_by(Encounter.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        request=request, name="operator.html",
        context={"request": request, "encounters": today_encounters, "site_id": settings.SITE_ID}
    )

@router.post("/operator/assign", response_class=HTMLResponse)
def assign_sticker(
    request: Request,
    cccd: str = Form(...),
    sticker_id: str = Form(...),
    db: Session = Depends(get_db)
):
    timestamp_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    encounter_uuid = generate_encounter_uuid(settings.SITE_ID, cccd, timestamp_iso)

    new_encounter = Encounter(
        uuid=encounter_uuid,
        sticker_id=sticker_id,
        patient_id=cccd, # Assuming CCCD acts as temporary patient identifier here
        station_id=settings.SITE_ID
    )

    db.add(new_encounter)
    db.commit()
    db.refresh(new_encounter)

    # Return just the updated row to be appended or replace the table body via HTMX
    return templates.TemplateResponse(
        request=request, name="partials/encounter_row.html",
        context={"request": request, "encounter": new_encounter}
    )

@router.get("/contributor", response_class=HTMLResponse)
def get_contributor_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="contributor.html",
        context={"request": request}
    )

@router.get("/contributor/scan", response_class=HTMLResponse)
def handle_scan(request: Request, sticker_id: str, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.sticker_id == sticker_id).first()

    return templates.TemplateResponse(
        request=request, name="partials/contributor_form.html",
        context={"request": request, "encounter": encounter, "sticker_id": sticker_id}
    )

@router.post("/contributor/submit/{uuid}", response_class=HTMLResponse)
def submit_form(
    request: Request,
    uuid: str,
    blood_pressure: str = Form(None),
    heart_rate: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    encounter = db.query(Encounter).filter(Encounter.uuid == uuid).first()
    if encounter:
        # Here you would actually save the form data to an Observation table.
        # For Sprint 2 scope, we update a dummy summary field to indicate completion.
        encounter.summary_text = f"BP: {blood_pressure}, HR: {heart_rate}. Notes: {notes}"
        encounter.updated_at = datetime.now(timezone.utc)
        db.commit()

        return HTMLResponse(
            """
            <div class='text-center py-8'>
                <svg class='mx-auto h-12 w-12 text-green-500' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M5 13l4 4L19 7' />
                </svg>
                <h3 class='mt-2 text-lg font-medium text-gray-900'>Đã lưu thành công!</h3>
                <p class='mt-1 text-sm text-gray-500'>Dữ liệu khám đã được cập nhật.</p>
                <button onclick="document.getElementById('form-container').classList.add('hidden')" class='mt-4 text-primary hover:text-blue-700 font-medium'>Đóng</button>
            </div>
            """
        )
    return HTMLResponse("<div>Error: Encounter not found.</div>", status_code=404)
