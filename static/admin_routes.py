# admin_routes.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from .utils import get_supabase, hash_password
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Replace with hashed in prod

def is_admin(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

@router.get("/admin", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/admin")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if is_admin(username, password):
        response = RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
        response.set_cookie("admin_auth", "1")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@router.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/admin/users", response_class=HTMLResponse)
def manage_users(request: Request):
    client = get_supabase()
    users = client.table("users").select("*").execute().data
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.get("/admin/versions", response_class=HTMLResponse)
def manage_versions(request: Request):
    client = get_supabase()
    versions = client.table("app_versions").select("*").execute().data
    return templates.TemplateResponse("versions.html", {"request": request, "versions": versions})

@router.post("/admin/add-user")
def add_user(username: str = Form(...), password: str = Form(...), expiry_date: str = Form(...)):
    client = get_supabase()
    password_hash = hash_password(password)
    client.table("users").insert({
        "username": username,
        "password_hash": password_hash,
        "expiry_date": expiry_date
    }).execute()
    return RedirectResponse("/admin/users", status_code=HTTP_302_FOUND)
