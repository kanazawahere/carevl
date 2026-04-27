from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.identity import generate_encounter_uuid
from app.core.config import settings
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.observation import Observation
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/intake", response_class=HTMLResponse)
@router.get("/operator", response_class=HTMLResponse)
def get_operator_page(request: Request, db: Session = Depends(get_db)):
    # Get today's encounters for the waiting list
    today_encounters = db.query(Encounter).order_by(Encounter.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        request=request, name="operator.html",
        context={"request": request, "encounters": today_encounters, "site_id": settings.SITE_ID}
    )

@router.post("/intake/assign", response_class=HTMLResponse)
@router.post("/operator/assign", response_class=HTMLResponse)
def assign_sticker(
    request: Request,
    cccd: str = Form(...),
    sticker_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # Explicitly create or get Patient for PIXm support
    patient = db.query(Patient).filter(Patient.id == cccd).first()
    if not patient:
        patient = Patient(id=cccd)
        db.add(patient)

    timestamp_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    encounter_uuid = generate_encounter_uuid(settings.SITE_ID, cccd, timestamp_iso)

    new_encounter = Encounter(
        uuid=encounter_uuid,
        sticker_id=sticker_id,
        patient_id=cccd,
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

@router.get("/results-update", response_class=HTMLResponse)
@router.get("/contributor", response_class=HTMLResponse)
def get_contributor_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="contributor.html",
        context={"request": request}
    )

@router.get("/results-update/scan", response_class=HTMLResponse)
@router.get("/contributor/scan", response_class=HTMLResponse)
def handle_scan(request: Request, sticker_id: str, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.sticker_id == sticker_id).first()

    return templates.TemplateResponse(
        request=request, name="partials/contributor_form.html",
        context={"request": request, "encounter": encounter, "sticker_id": sticker_id}
    )

@router.post("/results-update/submit/{uuid}", response_class=HTMLResponse)
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
        # Save real Observations instead of just the dummy text
        if blood_pressure:
            obs_bp = Observation(encounter_uuid=uuid, code="blood_pressure", value_string=blood_pressure)
            db.add(obs_bp)
        if heart_rate:
            try:
                hr_val = float(heart_rate)
                obs_hr = Observation(encounter_uuid=uuid, code="heart_rate", value_numeric=hr_val)
                db.add(obs_hr)
            except ValueError:
                pass

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


# Placeholders for unimplemented Sidebar items
@router.get("/queue", response_class=HTMLResponse)
def get_queue_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "2. Lượt khám (Queue)"})

@router.get("/patient-record", response_class=HTMLResponse)
def get_patient_record_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "3. Hồ sơ bệnh nhân"})

@router.get("/aggregate", response_class=HTMLResponse)
def get_aggregate_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "4. Nhập liệu (Aggregate)"})

@router.get("/reports", response_class=HTMLResponse)
def get_reports_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "6. Báo cáo"})

@router.get("/audit", response_class=HTMLResponse)
def get_audit_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "8. Liên thông (Audit)"})

@router.get("/settings", response_class=HTMLResponse)
def get_settings_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "9. Cài đặt trạm"})

@router.get("/about", response_class=HTMLResponse)
def get_about_page(request: Request):
    return templates.TemplateResponse(request=request, name="placeholders/coming_soon.html", context={"request": request, "title": "10. Giới thiệu"})
