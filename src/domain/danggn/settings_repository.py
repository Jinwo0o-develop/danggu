"""SettingsRepository — 앱 설정 저장소 (Supabase)."""
from src.core.supabase_client import get_supabase

DEFAULT_AUTO_CANCEL_DAYS = 7


class SettingsRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def get_auto_cancel_days(self) -> int:
        if self._db is None:
            return DEFAULT_AUTO_CANCEL_DAYS
        r = (
            self._db.table("danggn_settings")
            .select("value")
            .eq("key", "auto_cancel_days")
            .maybe_single()
            .execute()
        )
        return int(r.data["value"]) if r.data else DEFAULT_AUTO_CANCEL_DAYS

    def set_auto_cancel_days(self, days: int) -> None:
        if self._db is None:
            return
        self._db.table("danggn_settings").upsert(
            {"key": "auto_cancel_days", "value": str(days)}
        ).execute()
