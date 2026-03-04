"""
EventLogRepository — Observer 구현체 (Supabase).

상태 변경 이벤트를 danggn_event_logs 테이블에 영속화한다.
state.py의 StatusChangedEvent.to_dict()는 'occurred_at' 키를 사용하며,
DB 컬럼명도 occurred_at으로 일치시킨다.
"""
from src.core.supabase_client import get_supabase
from src.domain.danggn.state import StatusChangedEvent, StatusObserver


class EventLogRepository(StatusObserver):
    def __init__(self) -> None:
        self._db = get_supabase()

    # ── Observer 인터페이스 ────────────────────────────────────────

    def on_status_changed(self, event: StatusChangedEvent) -> None:
        """이벤트를 Supabase에 insert."""
        self._db.table("danggn_event_logs").insert(event.to_dict()).execute()

    # ── 조회 ──────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        r = self._db.table("danggn_event_logs").select("*").order("id").execute()
        return r.data or []

    def get_by_application_id(self, application_id: int) -> list[dict]:
        r = (
            self._db.table("danggn_event_logs")
            .select("*")
            .eq("application_id", application_id)
            .order("id")
            .execute()
        )
        return r.data or []
