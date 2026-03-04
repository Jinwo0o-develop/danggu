"""
Admin 인증 라우터 — 로그인 / 로그아웃 / 관리자 등록.
"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.deps import AdminUserSvc
from src.core.brute_force import brute_force
from src.core.csrf import CsrfDepend
from src.core.session import get_admin_session, set_admin_session
from src.templates_setup import templates

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if request.session.get("admin_user_id"):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login", response_model=None)
@limiter.limit("10/minute")
async def login(
    request: Request,
    _csrf: CsrfDepend,
    service: AdminUserSvc,
    username: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    ip = request.client.host if request.client else "unknown"

    locked, remaining_secs = brute_force.is_locked(ip)
    if locked:
        minutes = remaining_secs // 60 + 1
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": f"로그인 시도가 너무 많습니다. {minutes}분 후 다시 시도해주세요."},
            status_code=429,
        )

    user = service.authenticate(username, password)
    if user:
        brute_force.record_success(ip)
        set_admin_session(request, user)
        return RedirectResponse(url="/admin", status_code=303)

    brute_force.record_failure(ip)
    remaining = brute_force.remaining_attempts(ip)
    error = "아이디 또는 비밀번호가 올바르지 않습니다."
    if remaining <= 2:
        error += f" (남은 시도 {remaining}회)"
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": error},
        status_code=401,
    )


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request, _csrf: CsrfDepend) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    if request.session.get("admin_user_id"):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin/register.html", {"request": request})


@router.post("/register", response_model=None)
@limiter.limit("5/minute")
async def register(
    request: Request,
    _csrf: CsrfDepend,
    service: AdminUserSvc,
    register_key: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    def _error(msg: str) -> HTMLResponse:
        return templates.TemplateResponse(
            "admin/register.html",
            {"request": request, "error": msg, "username": username},
            status_code=400,
        )

    key   = register_key.strip().upper()
    uname = username.strip()

    if not service._key_repo.is_valid(key):
        return _error("등록 키가 올바르지 않거나 이미 사용된 키입니다.")
    if len(uname) < 2:
        return _error("아이디는 2자 이상이어야 합니다.")
    if len(password) < 12:
        return _error("비밀번호는 12자 이상이어야 합니다.")
    if password != password_confirm:
        return _error("비밀번호가 일치하지 않습니다.")

    try:
        service.create_admin(uname, password, "operator")
    except ValueError:
        return _error("이미 사용 중인 아이디입니다.")

    service.consume_register_key(key, uname)
    return RedirectResponse(url="/admin/login?registered=1", status_code=303)
