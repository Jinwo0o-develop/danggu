"""MenuRepository — 점심 메뉴 저장소 (Supabase)."""
from src.core.supabase_client import get_supabase


class MenuRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def get_all(self) -> list[dict]:
        if self._db is None:
            return []
        r = self._db.table("menus").select("*").order("id").execute()
        return r.data or []

    def add(self, emoji: str, name: str, desc: str) -> dict:
        if self._db is None:
            return {}
        r = self._db.table("menus").insert({"emoji": emoji, "name": name, "desc": desc}).execute()
        return r.data[0]

    def delete(self, name: str) -> bool:
        if self._db is None:
            return False
        r = self._db.table("menus").delete().eq("name", name).execute()
        return bool(r.data)
