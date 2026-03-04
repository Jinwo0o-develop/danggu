"""
Customer (고객) 엔드포인트 — 회원가입, 로그인, 프로필, 전화번호 연결.
"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.deps import CustomerSvc, DanggnSvc
from src.core.session import CUSTOMER_USER_ID, get_customer_session, set_customer_session
from src.domain.customer.schemas import CustomerCreate
from src.templates_setup import templates

router = APIRouter(prefix="/customer", tags=["customer"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    if get_customer_session(request):
        return RedirectResponse(url="/customer/profile", status_code=302)
    return templates.TemplateResponse("당근마켓/register.html", {"request": request})


@router.post("/register", response_model=None)
async def register(
    request: Request,
    service: CustomerSvc,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    phone: str = Form(default=""),
) -> HTMLResponse | RedirectResponse:
    try:
        customer = service.register(
            CustomerCreate(
                email=email.strip(),
                password=password,
                name=name.strip(),
                phone=phone.strip(),
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
async def login(
    request: Request,
    service: CustomerSvc,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    user = service.authenticate(email.strip(), password)
    if user is None:
        return templates.TemplateResponse(
            "당근마켓/login.html",
            {"request": request, "error": "이메일 또는 비밀번호가 올바르지 않습니다."},
            status_code=401,
        )
    set_customer_session(request, user)
    return RedirectResponse(url="/customer/profile", status_code=303)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
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
    service: CustomerSvc,
    danggn_service: DanggnSvc,
    phone: str = Form(default=""),
) -> HTMLResponse | RedirectResponse:
    user_id = get_customer_session(request)
    if not user_id:
        return RedirectResponse(url="/customer/login", status_code=302)
    phone = phone.strip()
    if not phone:
        customer = service.get_by_id(user_id)
        applications = sorted(
            danggn_service.get_by_user_id(user_id),
            key=lambda a: a["id"],
            reverse=True,
        )
        return templates.TemplateResponse(
            "당근마켓/profile.html",
            {
                "request":      request,
                "customer":     customer,
                "applications": applications,
                "error":        "전화번호를 입력해주세요.",
            },
            status_code=400,
        )
    service.link_phone(user_id, phone)
    return RedirectResponse(url="/customer/profile", status_code=303)
