"""
State 패턴 — 신청 상태 머신
Observer 패턴 — 상태 변경 이벤트 발행

전이 테이블:
  접수됨   → 수거예정, 취소됨
  수거예정  → 판매중,   취소됨
  판매중   → 정산완료,  취소됨
  정산완료 → (종단)
  취소됨   → (종단)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol


# ─────────────────────────────────────────────────────────────────
# 상태 열거형
# ─────────────────────────────────────────────────────────────────

class ApplicationStatus(str, Enum):
    RECEIVED  = "접수됨"
    SCHEDULED = "수거예정"
    LISTED    = "판매중"
    SETTLED   = "정산완료"
    CANCELLED = "취소됨"


# 진행 단계 순서 (취소됨 제외) — 진행 상태 바에 사용
PROGRESS_STEPS: list[ApplicationStatus] = [
    ApplicationStatus.RECEIVED,
    ApplicationStatus.SCHEDULED,
    ApplicationStatus.LISTED,
    ApplicationStatus.SETTLED,
]

# 허용 전이 테이블
_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.RECEIVED:  {ApplicationStatus.SCHEDULED, ApplicationStatus.CANCELLED},
    ApplicationStatus.SCHEDULED: {ApplicationStatus.LISTED,    ApplicationStatus.CANCELLED},
    ApplicationStatus.LISTED:    {ApplicationStatus.SETTLED,   ApplicationStatus.CANCELLED},
    ApplicationStatus.SETTLED:   set(),
    ApplicationStatus.CANCELLED: set(),
}


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    return target in _TRANSITIONS.get(current, set())


def get_allowed_transitions(current: ApplicationStatus) -> list[ApplicationStatus]:
    return list(_TRANSITIONS.get(current, set()))


# ─────────────────────────────────────────────────────────────────
# 역할 기반 전이 권한 매트릭스
# ─────────────────────────────────────────────────────────────────

ROLE_TRANSITIONS: dict[str, set[tuple[ApplicationStatus, ApplicationStatus]]] = {
    "super_admin": {
        (ApplicationStatus.RECEIVED, ApplicationStatus.SCHEDULED),
        (ApplicationStatus.RECEIVED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.SCHEDULED, ApplicationStatus.LISTED),
        (ApplicationStatus.SCHEDULED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.LISTED, ApplicationStatus.SETTLED),
        (ApplicationStatus.LISTED, ApplicationStatus.CANCELLED),
    },
    "operator": {
        (ApplicationStatus.RECEIVED, ApplicationStatus.SCHEDULED),
        (ApplicationStatus.RECEIVED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.SCHEDULED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.LISTED, ApplicationStatus.CANCELLED),
    },
    "settler": {
        (ApplicationStatus.LISTED, ApplicationStatus.SETTLED),
        (ApplicationStatus.RECEIVED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.SCHEDULED, ApplicationStatus.CANCELLED),
        (ApplicationStatus.LISTED, ApplicationStatus.CANCELLED),
    },
}


def can_role_transition(
    role: str, current: ApplicationStatus, target: ApplicationStatus
) -> bool:
    return (current, target) in ROLE_TRANSITIONS.get(role, set())


def get_allowed_transitions_for_role(
    role: str, current: ApplicationStatus
) -> list[ApplicationStatus]:
    allowed_pairs = ROLE_TRANSITIONS.get(role, set())
    return [target for (src, target) in allowed_pairs if src == current]


# ─────────────────────────────────────────────────────────────────
# Observer 인터페이스 + 이벤트 데이터
# ─────────────────────────────────────────────────────────────────

@dataclass
class StatusChangedEvent:
    application_id: int
    from_status: ApplicationStatus
    to_status: ApplicationStatus
    changed_by: str = "admin"
    note: str = ""
    occurred_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return {
            "application_id": self.application_id,
            "from_status":    self.from_status.value,
            "to_status":      self.to_status.value,
            "changed_by":     self.changed_by,
            "note":           self.note,
            "occurred_at":    self.occurred_at,
        }


class StatusObserver(Protocol):
    """Observer 인터페이스 — 구조적 서브타이핑(Protocol) 적용."""
    def on_status_changed(self, event: StatusChangedEvent) -> None: ...


# ─────────────────────────────────────────────────────────────────
# 상태 머신 (Subject)
# ─────────────────────────────────────────────────────────────────

class ApplicationStateMachine:
    """
    신청 상태 머신.

    application dict 를 래핑하며, transition() 호출 시
    등록된 모든 Observer 에게 StatusChangedEvent 를 발행한다.
    """

    def __init__(self, application: dict) -> None:
        raw = application.get("status", ApplicationStatus.RECEIVED.value)
        self._app = application
        self._status = ApplicationStatus(raw)
        self._observers: list[StatusObserver] = []

    @property
    def status(self) -> ApplicationStatus:
        return self._status

    def add_observer(self, observer: StatusObserver) -> None:
        self._observers.append(observer)

    def transition(
        self,
        target: ApplicationStatus,
        changed_by: str = "admin",
        note: str = "",
    ) -> StatusChangedEvent:
        """
        상태 전이 수행.

        Raises:
            ValueError: 허용되지 않은 전이인 경우.
        """
        if not can_transition(self._status, target):
            raise ValueError(
                f"'{self._status.value}' → '{target.value}' 전이는 허용되지 않습니다."
            )
        event = StatusChangedEvent(
            application_id=self._app["id"],
            from_status=self._status,
            to_status=target,
            changed_by=changed_by,
            note=note,
        )
        self._status = target
        self._app["status"] = target.value

        for obs in self._observers:
            obs.on_status_changed(event)

        return event
