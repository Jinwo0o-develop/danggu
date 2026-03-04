"""
Admin 엔드포인트 패키지 — Facade 패턴.

/admin 접두사 하에 auth, applications, management 서브 라우터를 조합한다.
router.py 는 이 패키지의 `router` 를 include하여 기존 인터페이스를 유지한다.
"""
from fastapi import APIRouter

from src.api.v1.endpoints.admin.applications import router as apps_router
from src.api.v1.endpoints.admin.auth import router as auth_router
from src.api.v1.endpoints.admin.management import router as mgmt_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(auth_router)
router.include_router(apps_router)
router.include_router(mgmt_router)
