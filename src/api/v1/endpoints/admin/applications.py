"""
Admin 신청 관리 라우터 — 대시보드, 상세, 상태 전이.
"""
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.deps import DanggnSvc
from src.api.v1.endpoints.admin._constants import ROLE_LABELS, STATUS_META
from src.core.csrf import CsrfDepend
from src.core.session import get_admin_session
from src.domain.danggn.state import ApplicationStatus, PROGRESS_STEPS
from src.templates_setup import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    service: DanggnSvc,
    status_filter: str = "",
    q: str = "",
) -> HTMLResponse:
    admin = get_admin_session(request)
    cancelled_count = service.auto_cancel_expired()
    apps = service.get_all_with_status()

    if status_filter:
        apps = [a for a in apps if a.get("status") == status_filter]
    if q:
        q_lower = q.lower()
        apps = [
            a for a in apps
            if q_lower in a.get("name", "").lower()
            or q_lower in a.get("phone", "").lower()
            or q_lower in a.get("item_name", "").lower()
            or q_lower in a.get("lookup_code", "").lower()
        ]

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request":        request,
            "applications":   sorted(apps, key=lambda a: a["id"], reverse=True),
            "status_filter":  status_filter,
            "status_meta":    STATUS_META,
            "all_statuses":   list(ApplicationStatus),
            "q":              q,
            "admin":          admin,
            "role_label":     ROLE_LABELS.get(admin["role"], admin["role"]),
            "auto_cancelled": cancelled_count,
        },
    )


@router.get("/applications/{application_id}", response_class=HTMLResponse)
async def application_detail(
    request: Request,
    application_id: int,
    service: DanggnSvc,
) -> HTMLResponse:
    admin = get_admin_session(request)
    app = service.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다.")

    current_status = ApplicationStatus(app["status"])
    allowed = service.get_allowed_transitions_for_role(admin["role"], current_status)
    logs = service.get_event_logs(application_id)

    try:
        current_step = PROGRESS_STEPS.index(current_status)
    except ValueError:
        current_step = -1  # CANCELLED

    return templates.TemplateResponse(
        "admin/application_detail.html",
        {
            "request":          request,
            "app":              app,
            "current_status":   current_status,
            "allowed_transitions": allowed,
            "logs":             logs,
            "progress_steps":   PROGRESS_STEPS,
            "current_step":     current_step,
            "status_meta":      STATUS_META,
            "admin":            admin,
            "role_label":       ROLE_LABELS.get(admin["role"], admin["role"]),
            "show_sale_price":  current_status == ApplicationStatus.LISTED,
        },
    )


@router.post("/applications/{application_id}/transition")
async def transition_status(
    request: Request,
    _csrf: CsrfDepend,
    application_id: int,
    service: DanggnSvc,
    new_status: str = Form(...),
    note: str = Form(default=""),
    sale_price: str = Form(default=""),
) -> RedirectResponse:
    admin = get_admin_session(request)

    try:
        target = ApplicationStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 상태값입니다.")

    parsed_sale_price: int | None = None
    if sale_price.strip():
        try:
            parsed_sale_price = int(sale_price.strip().replace(",", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="판매가는 숫자여야 합니다.")

    try:
        service.transition_status(
            application_id,
            target,
            note=note.strip(),
            changed_by=admin.get("username", "admin"),
            role=admin["role"],
            sale_price=parsed_sale_price,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return RedirectResponse(
        url=f"/admin/applications/{application_id}",
        status_code=303,
    )
