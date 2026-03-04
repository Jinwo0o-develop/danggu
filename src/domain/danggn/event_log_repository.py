"""
EventLogRepository — Observer 구현체 (Singleton).

상태 변경 이벤트를 data/danggn_event_logs.json 에 영속화한다.
BaseJsonRepository 상속으로 Singleton·_load·_save 자동 확보.
"""
from pathlib import Path

from src.core.paths import DATA_DIR
from src.core.repository import BaseJsonRepository
from src.domain.danggn.state import StatusChangedEvent, StatusObserver


class EventLogRepository(BaseJsonRepository, StatusObserver):
    """Singleton Observer — 상태 변경 이벤트를 JSON에 영속화."""

    @property
    def file_path(self) -> Path:
        return DATA_DIR / "danggn_event_logs.json"

    # ── Observer 인터페이스 ────────────────────────────────────────

    def on_status_changed(self, event: StatusChangedEvent) -> None:
        """이벤트를 JSON 파일에 append."""
        logs = self._load()
        logs.append({"id": self._next_id(logs), **event.to_dict()})
        self._save(logs)

    # ── 조회 ──────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        return self._load()

    def get_by_application_id(self, application_id: int) -> list[dict]:
        return [lg for lg in self._load() if lg["application_id"] == application_id]
