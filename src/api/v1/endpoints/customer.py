"""
Customer (고객) 엔드포인트 — 회원가입, 로그인, 프로필, 전화번호 연결.
"""
import re

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.deps import CustomerSvc, DanggnSvc
from src.core.brute_force import brute_force
from src.core.csrf import CsrfDepend
from src.core.session import CUSTOMER_USER_ID, get_customer_session, set_customer_session
from src.domain.customer.schemas import CustomerCreate
from src.templates_setup import templates

router = APIRouter(prefix="/customer", tags=["customer"])
limiter = Limiter(key_func=get_remote_address)

_PHONE_RE = re.compile(r"^01[0-9]{8,9}$")


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    if get_customer_session(request):
        return RedirectResponse(url="/customer/profile", status_code=302)
    return templates.TemplateResponse("당근마켓/register.html", {"request": request})


@router.post("/register", response_model=None)
async def register(
    request: Request,
    _csrf: CsrfDepend,
    service: CustomerSvc,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    phone: str = Form(default=""),
) -> HTMLResponse | RedirectResponse:
    phone_stripped = phone.strip()
    if phone_stripped and not _PHONE_RE.match(phone_stripped.replace("-", "")):
        return templates.TemplateResponse(
            "당근마켓/register.html",
            {"request": request, "error": "올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)"},
            status_code=400,
        )
    try:
        customer = service.register(
            CustomerCreate(
                email=email.strip(),
                password=password,
                name=name.strip(),
                phone=phone_stripped,
            )
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            "당근마켓/register.html",
            {"request": request, "error": str(exc)},
            status_code=400,
        )
    set_customer_session(request, {"id": customer.id, "name": customer.name, "email": customer.email})
    return RedirectResponse(url="/customer/profile", status_code=303)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if get_customer_session(request):
        return RedirectResponse(url="/customer/profile", status_code=302)
    return templates.TemplateResponse("당근마켓/login.html", {"request": request})


@router.post("/login", response_model=None)
@limiter.limit("10/minute")
async def login(
    request: Request,
    _csrf: CsrfDepend,
    service: CustomerSvc,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    ip = request.client.host if request.client else "unknown"

    locked, remaining_secs = brute_force.is_locked(ip)
    if locked:
        minutes = remaining_secs // 60 + 1
        return templates.TemplateResponse(
            "당근마켓/login.html",
            {"request": request, "error": f"로그인 시도가 너무 많습니다. {minutes}분 후 다시 시도해주세요."},
            status_code=429,
        )

    user = service.authenticate(email.strip(), password)
    if user is None:
        brute_force.record_failure(ip)
        remaining = brute_force.remaining_attempts(ip)
        error = "이메일 또는 비밀번호가 올바르지 않습니다."
        if remaining <= 2:
            error += f" (남은 시도 {remaining}회)"
        return templates.TemplateResponse(
            "당근마켓/login.html",
            {"request": request, "error": error},
            status_code=401,
        )
    brute_force.record_success(ip)
    set_customer_session(request, user)
    return RedirectResponse(url="/customer/profile", status_code=303)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request, _csrf: CsrfDepend) -> RedirectResponse:
    request.session.pop(CUSTOMER_USER_ID, None)
    return RedirectResponse(url="/danggn", status_code=303)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    customer_service: CustomerSvc,
    danggn_service: DanggnSvc,
) -> HTMLResponse:
    user_id = get_customer_session(request)
    if not user_id:
        return RedirectResponse(url="/customer/login", status_code=302)
    customer = customer_service.get_by_id(user_id)
    if customer is None:
        request.session.pop(CUSTOMER_USER_ID, None)
        return RedirectResponse(url="/customer/login", status_code=302)
    applications = sorted(
        danggn_service.get_by_user_id(user_id),
        key=lambda a: a["id"],
        reverse=True,
    )
    return templates.TemplateResponse(
        "당근마켓/profile.html",
        {"request": request, "customer": customer, "applications": applications},
    )


# ── Link Phone ────────────────────────────────────────────────────────────────

@router.post("/link-phone", response_model=None)
async def link_phone(
    request: Request,
    _csrf: CsrfDepend,
    service: CustomerSvc,
    danggn_service: DanggnSvc,
    phone: str = Form(default=""),
) -> HTMLResponse | RedirectResponse:
    user_id = get_customer_session(request)
    if not user_id:
        return RedirectResponse(url="/customer/login", status_code=302)
    phone = phone.strip()

    def _phone_error(msg: str) -> HTMLResponse:
        customer = service.get_by_id(user_id)
        applications = sorted(
            danggn_service.get_by_user_id(user_id),
            key=lambda a: a["id"],
            reverse=True,
        )
        return templates.TemplateResponse(
            "당근마켓/profile.html",
            {"request": request, "customer": customer, "applications": applications, "error": msg},
            status_code=400,
        )

    if not phone:
        return _phone_error("전화번호를 입력해주세요.")
    if not _PHONE_RE.match(phone.replace("-", "")):
        return _phone_error("올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)")
    service.link_phone(user_id, phone)
    return RedirectResponse(url="/customer/profile", status_code=303)
