"""
DanggnService — 당근마켓 위탁 서비스 비즈니스 레이어.

의존성 주입(DI) 원칙:
  - 모든 저장소(Repository)는 생성자에서 주입받는다.
  - 기본값은 Singleton 인스턴스를 반환하므로
    운영 코드에서는 별도 인자 없이 호출 가능하다.
  - 테스트 시 모의(Mock) 객체를 주입해 격리 테스트 가능하다.

Observer 연동:
  - transition_status() 호출 시 ApplicationStateMachine이
    등록된 EventLogRepository(Observer)에게 이벤트를 자동 발행한다.
"""
import logging
from datetime import datetime, timedelta

from src.domain.danggn.auth_code_repository import AuthCodeRepository
from src.domain.danggn.commission_repository import CommissionRepository
from src.domain.danggn.event_log_repository import EventLogRepository
from src.domain.danggn.repository import DanggnApplicationRepository
from src.domain.danggn.review_repository import ReviewRepository
from src.domain.danggn.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ReviewCreate,
    ReviewResponse,
)
from src.domain.danggn.settings_repository import SettingsRepository
from src.domain.danggn.state import (
    ApplicationStatus,
    ApplicationStateMachine,
    can_role_transition,
    get_allowed_transitions,
    get_allowed_transitions_for_role,
)

logger = logging.getLogger(__name__)

# ── 정규화 ────────────────────────────────────────────────────────────────────

_APP_DEFAULTS: dict = {
    "status":            ApplicationStatus.RECEIVED.value,
    "category":          "기타",
    "user_id":           None,
    "created_at":        "",
    "sale_price":        None,
    "commission_rate":   None,
    "commission_amount": None,
    "settlement_amount": None,
}


def _normalize(app: dict) -> dict:
    """누락된 필드를 기본값으로 채운다 (하위 호환)."""
    for key, default in _APP_DEFAULTS.items():
        app.setdefault(key, default)
    return app


def _earliest_log_date(application_id: int, event_log: EventLogRepository) -> str | None:
    """해당 신청의 이벤트 로그 중 가장 이른 날짜를 반환."""
    logs = event_log.get_by_application_id(application_id)
    dates = [lg.get("occurred_at") for lg in logs if lg.get("occurred_at")]
    return min(dates) if dates else None


# ── 서비스 ────────────────────────────────────────────────────────────────────

class DanggnService:
    def __init__(
        self,
        repo: DanggnApplicationRepository,
        event_log: EventLogRepository | None = None,
        review_repo: ReviewRepository | None = None,
        auth_code_repo: AuthCodeRepository | None = None,
        commission_repo: CommissionRepository | None = None,
        settings_repo: SettingsRepository | None = None,
    ) -> None:
        self._repo            = repo
        self._event_log       = event_log       or EventLogRepository()
        self._review_repo     = review_repo     or ReviewRepository()
        self._auth_code_repo  = auth_code_repo  or AuthCodeRepository()
        self._commission_repo = commission_repo or CommissionRepository()
        self._settings_repo   = settings_repo   or SettingsRepository()

    # ── 신청 ──────────────────────────────────────────────────────

    def create(self, data: ApplicationCreate) -> ApplicationResponse:
        return ApplicationResponse(**self._repo.create(data))

    def get_all(self) -> list[ApplicationResponse]:
        return [ApplicationResponse(**_normalize(a)) for a in self._repo.get_all()]

    def get_all_with_status(self) -> list[dict]:
        """관리자용 — 정규화된 raw dict 목록 반환."""
        return [_normalize(a) for a in self._repo.get_all()]

    def get_by_id(self, application_id: int) -> dict | None:
        app = self._repo.get_by_id(application_id)
        return _normalize(app) if app else None

    def get_by_phone(self, phone: str) -> list[dict]:
        return [_normalize(a) for a in self._repo.get_by_phone(phone)]

    def get_by_lookup_code(self, code: str) -> dict | None:
        app = self._repo.get_by_lookup_code(code)
        return _normalize(app) if app else None

    def get_by_user_id(self, user_id: int) -> list[dict]:
        return [a for a in self.get_all_with_status() if a.get("user_id") == user_id]

    # ── 인증코드 (OTP 시뮬) ───────────────────────────────────────

    def generate_auth_code(self, phone: str) -> str:
        if not self._repo.get_by_phone(phone):
            raise ValueError("등록되지 않은 전화번호입니다.")
        return self._auth_code_repo.generate(phone)

    def verify_auth_code(self, phone: str, code: str) -> bool:
        return self._auth_code_repo.verify(phone, code)

    # ── 상태 전이 (State 패턴 + Observer 패턴) ─────────────────────

    def transition_status(
        self,
        application_id: int,
        target: ApplicationStatus,
        note: str = "",
        changed_by: str = "admin",
        role: str = "super_admin",
        sale_price: int | None = None,
    ) -> None:
        """
        역할 권한 검증 후 State 머신으로 전이, DB 반영,
        EventLogObserver 에게 이벤트 발행.

        Raises:
            ValueError: 신청 미존재, 허용되지 않은 전이, 또는 권한 없음.
        """
        app = self.get_by_id(application_id)
        if app is None:
            raise ValueError(f"신청 {application_id}을 찾을 수 없습니다.")

        current = ApplicationStatus(app["status"])

        if not can_role_transition(role, current, target):
            raise ValueError(
                f"'{role}' 역할은 '{current.value}' → '{target.value}' 전이 권한이 없습니다."
            )

        machine = ApplicationStateMachine(app)
        machine.add_observer(self._event_log)
        event = machine.transition(target, changed_by=changed_by, note=note)

        update_fields: dict = {"status": target.value}
        if target == ApplicationStatus.SETTLED:
            if sale_price is None:
                raise ValueError("정산완료 전환 시 판매가(sale_price)를 입력해야 합니다.")
            rate = self._commission_repo.get_rate(app.get("category", "기타"))
            commission_amount = round(sale_price * rate)
            update_fields.update({
                "sale_price":        sale_price,
                "commission_rate":   rate,
                "commission_amount": commission_amount,
                "settlement_amount": sale_price - commission_amount,
            })

        self._repo.update_fields(application_id, update_fields)

        logger.info(
            "Transition app=%d  %s → %s  by=%s  role=%s",
            event.application_id,
            event.from_status.value,
            event.to_status.value,
            event.changed_by,
            role,
        )

    def get_allowed_transitions(
        self, current: ApplicationStatus
    ) -> list[ApplicationStatus]:
        return get_allowed_transitions(current)

    def get_allowed_transitions_for_role(
        self, role: str, current: ApplicationStatus
    ) -> list[ApplicationStatus]:
        return get_allowed_transitions_for_role(role, current)

    def auto_cancel_expired(self) -> int:
        """접수됨 상태에서 N일 이상 된 신청을 자동 취소한다."""
        days = self._settings_repo.get_auto_cancel_days()
        cutoff = datetime.now() - timedelta(days=days)
        cancelled = 0

        for app in self._repo.get_all():
            if app.get("status") != ApplicationStatus.RECEIVED.value:
                continue
            date_str = app.get("created_at") or _earliest_log_date(app["id"], self._event_log)
            if not date_str:
                continue
            try:
                created = datetime.fromisoformat(date_str)
            except ValueError:
                continue
            if created >= cutoff:
                continue
            try:
                self.transition_status(
                    app["id"],
                    ApplicationStatus.CANCELLED,
                    note=f"자동 취소: 접수 후 {days}일 경과",
                    changed_by="system",
                    role="super_admin",
                )
                cancelled += 1
            except ValueError as exc:
                logger.warning("Auto-cancel failed for app %d: %s", app["id"], exc)

        return cancelled

    def get_event_logs(self, application_id: int) -> list[dict]:
        return self._event_log.get_by_application_id(application_id)

    # ── 후기 ──────────────────────────────────────────────────────

    def create_review(self, data: ReviewCreate) -> ReviewResponse:
        return ReviewResponse(**self._review_repo.create(data))

    def get_all_reviews(self) -> list[ReviewResponse]:
        return [ReviewResponse(**r) for r in self._review_repo.get_all()]
