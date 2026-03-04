from fastapi import APIRouter

from src.api.v1.endpoints import admin, customer, danggn, menu

router = APIRouter()
router.include_router(menu.router)
router.include_router(danggn.router)
router.include_router(admin.router)
router.include_router(customer.router)
