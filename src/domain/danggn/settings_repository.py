"""SettingsRepository — 앱 설정 저장소 (Supabase)."""
from src.core.supabase_client import get_supabase


class SettingsRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def get_auto_cancel_days(self) -> int:
        r = (
            self._db.table("danggn_settings")
            .select("value")
            .eq("key", "auto_cancel_days")
            .maybe_single()
            .execute()
        )
        return int(r.data["value"]) if r.data else 7

    def set_auto_cancel_days(self, days: int) -> None:
        self._db.table("danggn_settings").upsert(
            {"key": "auto_cancel_days", "value": str(days)}
        ).execute()
