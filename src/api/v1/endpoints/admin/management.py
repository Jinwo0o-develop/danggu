"""
Admin 관리 라우터 — 수수료, 설정, 등록키, 관리자 계정, 고객 관리.
"""
import urllib.parse

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.deps import AdminUserSvc, CommissionRepo, CustomerSvc, DanggnSvc, SettingsRepo
from src.api.v1.endpoints.admin._constants import ROLE_LABELS, STATUS_META, VALID_ROLES
from src.core.csrf import CsrfDepend
from src.core.session import GuestBlock, get_admin_session
from src.templates_setup import templates

router = APIRouter()


# ── Commission (super_admin only) ─────────────────────────────────────────────

@router.get("/commission", response_class=HTMLResponse)
async def commission_page(
    request: Request,
    commission_repo: CommissionRepo,
) -> HTMLResponse:
    admin = get_admin_session(request)
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    return templates.TemplateResponse(
        "admin/commission.html",
        {
            "request":    request,
            "rates":      commission_repo.get_all(),
            "admin":      admin,
            "role_label": ROLE_LABELS.get(admin["role"], admin["role"]),
        },
    )


@router.post("/commission")
async def commission_save(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    commission_repo: CommissionRepo,
) -> RedirectResponse:
    admin = get_admin_session(request)
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    form = await request.form()
    new_rates: dict[str, float] = {}
    for key, value in form.items():
        if key.startswith("rate_"):
            category = key[5:]
            try:
                rate = float(str(value))
                if 0.0 <= rate <= 1.0:
                    new_rates[category] = rate
            except ValueError:
                pass
    commission_repo.save_all(new_rates)
    return RedirectResponse(url="/admin/commission?saved=1", status_code=303)


# ── Settings ──────────────────────────────────────────────────────────────────

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    settings_repo: SettingsRepo,
) -> HTMLResponse:
    admin = get_admin_session(request)
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request":          request,
            "auto_cancel_days": settings_repo.get_auto_cancel_days(),
            "admin":            admin,
            "role_label":       ROLE_LABELS.get(admin["role"], admin["role"]),
        },
    )


@router.post("/settings")
async def settings_save(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    settings_repo: SettingsRepo,
    auto_cancel_days: int = Form(...),
) -> RedirectResponse:
    get_admin_session(request)
    if auto_cancel_days < 0:
        raise HTTPException(status_code=400, detail="일수는 0 이상이어야 합니다.")
    settings_repo.set_auto_cancel_days(auto_cancel_days)
    return RedirectResponse(url="/admin/settings?saved=1", status_code=303)


# ── Register Keys ─────────────────────────────────────────────────────────────

@router.get("/register-keys", response_class=HTMLResponse)
async def register_keys_page(
    request: Request,
    service: AdminUserSvc,
) -> HTMLResponse:
    admin = get_admin_session(request)
    return templates.TemplateResponse(
        "admin/register_keys.html",
        {
            "request":    request,
            "keys":       service.get_register_keys(),
            "admin":      admin,
            "role_label": ROLE_LABELS.get(admin["role"], admin["role"]),
            "saved":      request.query_params.get("saved"),
            "error":      request.query_params.get("error"),
        },
    )


@router.post("/register-keys/generate")
async def register_keys_generate(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    service: AdminUserSvc,
) -> RedirectResponse:
    admin = get_admin_session(request)
    service.generate_register_key(admin["username"])
    return RedirectResponse(url="/admin/register-keys?saved=1", status_code=303)


@router.post("/register-keys/{key_id}/revoke")
async def register_keys_revoke(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    key_id: int,
    service: AdminUserSvc,
) -> RedirectResponse:
    get_admin_session(request)
    if not service.revoke_register_key(key_id):
        return RedirectResponse(
            url=f"/admin/register-keys?error={urllib.parse.quote('이미 사용된 키는 폐지할 수 없습니다.')}",
            status_code=303,
        )
    return RedirectResponse(url="/admin/register-keys?saved=1", status_code=303)


# ── Admin User Management ─────────────────────────────────────────────────────

@router.get("/admins", response_class=HTMLResponse)
async def admins_page(
    request: Request,
    service: AdminUserSvc,
) -> HTMLResponse:
    admin = get_admin_session(request)
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    return templates.TemplateResponse(
        "admin/admins.html",
        {
            "request":     request,
            "admin_users": service.get_all(),
            "admin":       admin,
            "role_label":  ROLE_LABELS.get(admin["role"], admin["role"]),
            "role_labels": ROLE_LABELS,
            "saved":       request.query_params.get("saved"),
            "error":       request.query_params.get("error"),
        },
    )


@router.post("/admins/create")
async def admins_create(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    service: AdminUserSvc,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
) -> RedirectResponse:
    admin = get_admin_session(request)
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다.")
    try:
        service.create_admin(username.strip(), password, role)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/admin/admins?error={urllib.parse.quote(str(exc))}",
            status_code=303,
        )
    return RedirectResponse(url="/admin/admins?saved=1", status_code=303)


@router.post("/admins/{admin_id}/delete")
async def admins_delete(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    admin_id: int,
    service: AdminUserSvc,
) -> RedirectResponse:
    current = get_admin_session(request)
    if current["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    if current["id"] == admin_id:
        raise HTTPException(status_code=400, detail="자신의 계정은 삭제할 수 없습니다.")
    service.delete_admin(admin_id)
    return RedirectResponse(url="/admin/admins?saved=1", status_code=303)


@router.post("/admins/{admin_id}/role")
async def admins_update_role(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    admin_id: int,
    service: AdminUserSvc,
    role: str = Form(...),
) -> RedirectResponse:
    current = get_admin_session(request)
    if current["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다.")
    service.update_role(admin_id, role)
    return RedirectResponse(url="/admin/admins?saved=1", status_code=303)


# ── Customer Management ────────────────────────────────────────────────────────

@router.get("/customers", response_class=HTMLResponse)
async def customers_page(
    request: Request,
    customer_service: CustomerSvc,
    danggn_service: DanggnSvc,
    q: str = "",
) -> HTMLResponse:
    admin = get_admin_session(request)
    customers = customer_service.get_all()
    all_apps = danggn_service.get_all_with_status()

    # 고객별 신청 건수 집계
    app_count: dict[int, int] = {}
    for app in all_apps:
        uid = app.get("user_id")
        if uid:
            app_count[uid] = app_count.get(uid, 0) + 1

    if q:
        q_lower = q.lower()
        customers = [
            c for c in customers
            if q_lower in c.email.lower()
            or q_lower in c.name.lower()
            or q_lower in (c.phone or "").lower()
        ]

    customers_sorted = sorted(customers, key=lambda c: c.id, reverse=True)
    return templates.TemplateResponse(
        "admin/customers.html",
        {
            "request":    request,
            "customers":  customers_sorted,
            "app_count":  app_count,
            "admin":      admin,
            "role_label": ROLE_LABELS.get(admin["role"], admin["role"]),
            "q":          q,
            "total":      len(customers_sorted),
        },
    )


@router.post("/customers/{customer_id}/delete")
async def customers_delete(
    request: Request,
    _csrf: CsrfDepend,
    _no_guest: GuestBlock,
    customer_id: int,
    customer_service: CustomerSvc,
) -> RedirectResponse:
    admin = get_admin_session(request)
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="슈퍼관리자만 접근 가능합니다.")
    customer_service.delete(customer_id)
    return RedirectResponse(url="/admin/customers?saved=1", status_code=303)
