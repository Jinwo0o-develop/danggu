from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from src.api.v1.router import router as api_router
from src.config import settings
from src.core.exceptions import NotAuthenticatedException
from src.templates_setup import templates


class HSTSMiddleware:
    """프로덕션에서 Strict-Transport-Security 헤더를 추가합니다."""

    def __init__(self, app: ASGIApp, max_age: int = 31536000) -> None:
        self.app = app
        self.max_age = max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_hsts(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"strict-transport-security"] = (
                    f"max-age={self.max_age}; includeSubDomains".encode()
                )
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_with_hsts)


limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda req, exc: JSONResponse(
        status_code=429,
        content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
    ),
)

if settings.is_production:
    app.add_middleware(HSTSMiddleware)
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(api_router)


@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException) -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=302)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/nanumsell", response_class=HTMLResponse)
async def nanumsell(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("nanumsell.html", {"request": request})


PAI_CHAT_DIST = BASE_DIR.parent / "PAI_CHAT" / "dist"


@app.get("/PAI")
async def pai_chat_index() -> FileResponse:
    """슬래시 없는 /PAI 경로에서 직접 index.html을 반환 (리다이렉트 방지)."""
    return FileResponse(PAI_CHAT_DIST / "index.html")


app.mount("/PAI", StaticFiles(directory=PAI_CHAT_DIST, html=True), name="pai-chat")
