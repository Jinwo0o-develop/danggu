"""
세션 관리 헬퍼 — 세션 키 상수 + 관리자/고객 세션 읽기·쓰기 유틸리티.

Strategy 패턴 적용:
  엔드포인트마다 흩어진 세션 키 문자열과 session.get() 호출을
  단일 모듈로 통합하여 오타·불일치를 방지한다.
"""
from fastapi import Request

from src.core.exceptions import NotAuthenticatedException

# ── 세션 키 상수 ──────────────────────────────────────────────────────────────

ADMIN_USER_ID  = "admin_user_id"
ADMIN_ROLE     = "admin_role"
ADMIN_USERNAME = "admin_username"

CUSTOMER_USER_ID = "user_id"
CUSTOMER_NAME    = "user_name"
CUSTOMER_EMAIL   = "user_email"

VERIFIED_PHONE = "verified_phone"

# ── 관리자 세션 ───────────────────────────────────────────────────────────────


def get_admin_session(request: Request) -> dict:
    """세션에서 관리자 정보 반환. 세션 없으면 NotAuthenticatedException 발생."""
    admin_id = request.session.get(ADMIN_USER_ID)
    if not admin_id:
        raise NotAuthenticatedException()
    return {
        "id":       admin_id,
        "role":     request.session.get(ADMIN_ROLE, "operator"),
        "username": request.session.get(ADMIN_USERNAME, ""),
    }


def set_admin_session(request: Request, user: dict) -> None:
    """관리자 세션 저장."""
    request.session[ADMIN_USER_ID]  = user["id"]
    request.session[ADMIN_ROLE]     = user["role"]
    request.session[ADMIN_USERNAME] = user["username"]


# ── 고객 세션 ─────────────────────────────────────────────────────────────────


def get_customer_session(request: Request) -> int | None:
    """세션에서 고객 user_id 반환. 없으면 None."""
    return request.session.get(CUSTOMER_USER_ID)


def set_customer_session(request: Request, user: dict) -> None:
    """고객 세션 저장."""
    request.session[CUSTOMER_USER_ID] = user["id"]
    request.session[CUSTOMER_NAME]    = user.get("name", "")
    request.session[CUSTOMER_EMAIL]   = user.get("email", "")
