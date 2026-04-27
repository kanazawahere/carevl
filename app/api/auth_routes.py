from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/github_auth.html", context={"request": request})

@router.get("/setup/repo", response_class=HTMLResponse)
def get_repo_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/repo_config.html", context={"request": request})

@router.post("/setup/repo")
def post_repo_setup(repo_url: str = Form(...)):
    # In a real app, save to .env or DB.
    return RedirectResponse(url="/setup/permission", status_code=303)

@router.get("/setup/permission", response_class=HTMLResponse)
def get_permission_gate(request: Request):
    return templates.TemplateResponse(request=request, name="auth/permission_gate.html", context={"request": request, "username": "kanazawahere"})

@router.post("/setup/permission/check")
def check_permission():
    # Simulate checking write access, then redirect to data setup
    return RedirectResponse(url="/setup/data", status_code=303)

@router.get("/setup/data", response_class=HTMLResponse)
def get_data_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/data_setup.html", context={"request": request})

@router.post("/setup/data/init")
def post_data_init():
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.post("/setup/data/restore")
def post_data_restore(private_key: str = Form(...)):
    # Handle DB restore logic here
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.get("/setup/pin", response_class=HTMLResponse)
def get_pin_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/pin_setup.html", context={"request": request})

@router.post("/setup/pin")
def post_pin_setup(pin: str = Form(...)):
    # Encrypt local token with PIN, then proceed to app
    return RedirectResponse(url="/intake", status_code=303)
