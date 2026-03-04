"""
Danggn (당근마켓) 공개 엔드포인트 — 신청, 조회, 인증, 후기.
"""
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.deps import CommissionRepo, DanggnSvc
from src.config import settings
from src.core.media import save_uploads
from src.core.session import VERIFIED_PHONE
from src.domain.danggn.schemas import ApplicationCreate, ReviewCreate
from src.domain.danggn.state import ApplicationStatus, PROGRESS_STEPS
from src.templates_setup import templates

router = APIRouter(prefix="/danggn", tags=["danggn"])


def _check_status_auth(request: Request, app: dict, code: str) -> bool:
    """신청 조회 인증: 식별코드 일치 또는 세션 전화번호 일치."""
    if code and app.get("lookup_code") == code.upper():
        return True
    verified_phone = request.session.get(VERIFIED_PHONE)
    return bool(verified_phone and verified_phone == app.get("phone"))


# ── 진입 ──────────────────────────────────────────────────────────────────────

@router.get("/admin")
async def danggn_admin_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


@router.get("", response_class=HTMLResponse)
async def danggn_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("당근마켓/index.html", {"request": request})


# ── 신청 ──────────────────────────────────────────────────────────────────────

@router.get("/apply", response_class=HTMLResponse)
async def danggn_apply(
    request: Request,
    commission_repo: CommissionRepo,
) -> HTMLResponse:
    return templates.TemplateResponse(
        "당근마켓/apply.html",
        {
            "request":       request,
            "logo_href":     "/danggn#intro",
            "categories":    commission_repo.get_categories(),
            "prefill_phone": request.session.get(VERIFIED_PHONE, ""),
            "user_id":       request.session.get("user_id"),
        },
    )


@router.post("/apply", response_class=HTMLResponse)
async def danggn_apply_submit(
    request: Request,
    service: DanggnSvc,
    commission_repo: CommissionRepo,
    last_name: str = Form(...),
    first_name: str = Form(...),
    phone: str = Form(...),
    item_name: str = Form(...),
    description: str = Form(...),
    listed_price: str = Form(default="무료나눔"),
    category: str = Form(default="기타"),
    media: list[UploadFile] = File(default=[]),
) -> HTMLResponse:
    application = service.create(
        ApplicationCreate(
            name=(last_name.strip() + first_name.strip()),
            phone=phone.strip(),
            item_name=item_name.strip(),
            description=description.strip(),
            listed_price=listed_price.strip() or "무료나눔",
            media_files=save_uploads(media),
            category=category.strip() or "기타",
            user_id=request.session.get("user_id"),
        )
    )
    return templates.TemplateResponse(
        "당근마켓/apply.html",
        {
            "request":     request,
            "logo_href":   "/danggn#intro",
            "success":     True,
            "application": application,
            "categories":  commission_repo.get_categories(),
        },
    )


# ── 조회 ──────────────────────────────────────────────────────────────────────

@router.get("/lookup", response_class=HTMLResponse)
async def danggn_lookup(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "당근마켓/lookup.html",
        {"request": request, "logo_href": "/danggn#intro"},
    )


@router.post("/lookup", response_class=HTMLResponse, response_model=None)
async def danggn_lookup_submit(
    request: Request,
    service: DanggnSvc,
    method: str = Form(...),
    phone: str = Form(default=""),
    code: str = Form(default=""),
) -> HTMLResponse | RedirectResponse:
    ctx = {"request": request, "logo_href": "/danggn#intro"}

    if method == "phone":
        phone = phone.strip()
        if not phone:
            return templates.TemplateResponse(
                "당근마켓/lookup.html", {**ctx, "error": "전화번호를 입력해주세요."}
            )
        results = service.get_by_phone(phone)
        if not results:
            return templates.TemplateResponse(
                "당근마켓/lookup.html",
                {**ctx, "error": "해당 전화번호로 등록된 신청이 없습니다."},
            )
        request.session[VERIFIED_PHONE] = phone
        return templates.TemplateResponse(
            "당근마켓/lookup.html",
            {**ctx, "results": results, "verified_phone": phone},
        )
    else:  # code
        code = code.strip().upper()
        if not code:
            return templates.TemplateResponse(
                "당근마켓/lookup.html", {**ctx, "error": "식별코드를 입력해주세요."}
            )
        app = service.get_by_lookup_code(code)
        if app is None:
            return templates.TemplateResponse(
                "당근마켓/lookup.html",
                {**ctx, "error": "해당 식별코드로 등록된 신청이 없습니다."},
            )
        return RedirectResponse(url=f"/danggn/status/{app['id']}?code={code}", status_code=302)


# ── 인증코드 ──────────────────────────────────────────────────────────────────

@router.post("/auth-code/request", response_class=HTMLResponse)
async def auth_code_request(
    request: Request,
    service: DanggnSvc,
    phone: str = Form(...),
) -> HTMLResponse:
    phone = phone.strip()
    ctx = {"request": request, "logo_href": "/danggn#intro", "active_tab": "auth"}
    try:
        code = service.generate_auth_code(phone)
    except ValueError as e:
        return templates.TemplateResponse(
            "당근마켓/lookup.html", {**ctx, "error": str(e)}
        )
    # 개발 환경에서만 시뮬레이션 코드 노출 (프로덕션에서는 실제 SMS 발송)
    sim_code = code if not settings.is_production else None
    return templates.TemplateResponse(
        "당근마켓/lookup.html",
        {**ctx, "auth_pending": True, "auth_phone": phone, "sim_code": sim_code},
    )


@router.post("/auth-code/verify", response_class=HTMLResponse)
async def auth_code_verify(
    request: Request,
    service: DanggnSvc,
    phone: str = Form(...),
    code: str = Form(...),
) -> HTMLResponse:
    ctx = {"request": request, "logo_href": "/danggn#intro"}
    if not service.verify_auth_code(phone, code.strip()):
        return templates.TemplateResponse(
            "당근마켓/lookup.html",
            {
                **ctx,
                "error":        "인증코드가 올바르지 않거나 만료되었습니다.",
                "auth_pending": True,
                "auth_phone":   phone,
                "active_tab":   "auth",
            },
        )
    results = service.get_by_phone(phone)
    request.session[VERIFIED_PHONE] = phone
    return templates.TemplateResponse(
        "당근마켓/lookup.html",
        {**ctx, "results": results, "verified_phone": phone, "active_tab": "phone"},
    )


# ── 상태 ──────────────────────────────────────────────────────────────────────

@router.get("/status/{application_id}", response_class=HTMLResponse, response_model=None)
async def danggn_status(
    request: Request,
    application_id: int,
    service: DanggnSvc,
    code: str = "",
) -> HTMLResponse | RedirectResponse:
    app = service.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다.")

    if not _check_status_auth(request, app, code):
        return RedirectResponse(url="/danggn/lookup", status_code=302)

    current_status = ApplicationStatus(app["status"])
    try:
        current_step = PROGRESS_STEPS.index(current_status)
    except ValueError:
        current_step = -1

    return templates.TemplateResponse(
        "당근마켓/status.html",
        {
            "request":        request,
            "logo_href":      "/danggn#intro",
            "app":            app,
            "current_status": current_status,
            "progress_steps": PROGRESS_STEPS,
            "current_step":   current_step,
            "logs":           service.get_event_logs(application_id),
        },
    )


# ── 후기 ──────────────────────────────────────────────────────────────────────

@router.get("/reviews", response_class=HTMLResponse)
async def danggn_reviews_list(request: Request, service: DanggnSvc) -> HTMLResponse:
    return templates.TemplateResponse(
        "당근마켓/reviews.html",
        {"request": request, "logo_href": "/danggn#intro", "reviews": service.get_all_reviews()},
    )


@router.get("/review", response_class=HTMLResponse)
async def danggn_review(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "당근마켓/review.html",
        {"request": request, "logo_href": "/danggn#intro"},
    )


@router.post("/review", response_class=HTMLResponse)
async def danggn_review_submit(
    request: Request,
    service: DanggnSvc,
    rating: str = Form(...),
    comment: str = Form(default=""),
) -> HTMLResponse:
    service.create_review(ReviewCreate(rating=rating, comment=comment.strip()))
    return templates.TemplateResponse(
        "당근마켓/review.html",
        {"request": request, "logo_href": "/danggn#intro", "success": True},
    )
