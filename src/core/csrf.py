import hmac
import secrets
from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status


def get_csrf_token(request: Request) -> str:
    """세션에서 CSRF 토큰을 반환하고, 없으면 새로 생성합니다."""
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_hex(32)
    return request.session["csrf_token"]


def csrf_input(request: Request) -> str:
    """폼에 삽입할 hidden input HTML을 반환합니다."""
    token = get_csrf_token(request)
    return f'<input type="hidden" name="csrf_token" value="{token}">'


async def validate_csrf(
    request: Request,
    csrf_token: str = Form(default=""),
) -> None:
    """POST 요청의 CSRF 토큰을 검증합니다. 불일치 시 403 반환."""
    expected = request.session.get("csrf_token", "")
    if not expected or not hmac.compare_digest(expected, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요.",
        )


CsrfDepend = Annotated[None, Depends(validate_csrf)]
