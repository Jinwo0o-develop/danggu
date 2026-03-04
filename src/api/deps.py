"""
중앙화된 의존성 주입 컨테이너 (Dependency Injection Container).

모든 엔드포인트는 여기에서 서비스 인스턴스를 가져온다.
Singleton Repository들이 조합되어 단일 DanggnService를 반환하며,
향후 기능 추가(알림, 결제 등) 시 이 파일만 수정하면 된다.

사용 예:
    from src.api.deps import DanggnSvc

    @router.get("/")
    async def handler(service: DanggnSvc) -> ...:
        ...
"""
from typing import Annotated

from fastapi import Depends

from src.domain.admin.admin_user_repository import AdminUserRepository
from src.domain.admin.admin_user_service import AdminUserService
from src.domain.admin.repository import AdminRepository
from src.domain.admin.service import AdminService
from src.domain.customer.repository import CustomerRepository
from src.domain.customer.service import CustomerService
from src.domain.danggn.auth_code_repository import AuthCodeRepository
from src.domain.danggn.commission_repository import CommissionRepository
from src.domain.danggn.event_log_repository import EventLogRepository
from src.domain.danggn.repository import DanggnApplicationRepository
from src.domain.danggn.review_repository import ReviewRepository
from src.domain.danggn.service import DanggnService
from src.domain.danggn.settings_repository import SettingsRepository


def get_danggn_service() -> DanggnService:
    """Singleton 리포지토리 조합 → 서비스 인스턴스 반환."""
    return DanggnService(
        repo=DanggnApplicationRepository(),
        event_log=EventLogRepository(),
        review_repo=ReviewRepository(),
        auth_code_repo=AuthCodeRepository(),
        commission_repo=CommissionRepository(),
        settings_repo=SettingsRepository(),
    )


DanggnSvc = Annotated[DanggnService, Depends(get_danggn_service)]


def get_admin_service() -> AdminService:
    return AdminService(repo=AdminRepository())


AdminSvc = Annotated[AdminService, Depends(get_admin_service)]


def get_admin_user_service() -> AdminUserService:
    return AdminUserService(repo=AdminUserRepository())


AdminUserSvc = Annotated[AdminUserService, Depends(get_admin_user_service)]


def get_customer_service() -> CustomerService:
    return CustomerService(repo=CustomerRepository())


CustomerSvc = Annotated[CustomerService, Depends(get_customer_service)]


def get_commission_repo() -> CommissionRepository:
    return CommissionRepository()


CommissionRepo = Annotated[CommissionRepository, Depends(get_commission_repo)]


def get_settings_repo() -> SettingsRepository:
    return SettingsRepository()


SettingsRepo = Annotated[SettingsRepository, Depends(get_settings_repo)]
