"""AdminUserRepository — 다중 관리자 계정 저장소 (Supabase)."""
import logging

from src.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class AdminUserRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    # ── 조회 ──────────────────────────────────────────────────────

    def get_by_username(self, username: str) -> dict | None:
        r = (
            self._db.table("admin_users")
            .select("*")
            .eq("username", username)
            .maybe_single()
            .execute()
        )
        return r.data

    def get_by_id(self, admin_id: int) -> dict | None:
        r = (
            self._db.table("admin_users")
            .select("*")
            .eq("id", admin_id)
            .maybe_single()
            .execute()
        )
        return r.data

    def get_all(self) -> list[dict]:
        r = self._db.table("admin_users").select("*").order("id").execute()
        return r.data or []

    # ── 쓰기 ──────────────────────────────────────────────────────

    def create(self, username: str, hashed_password: str, role: str) -> dict:
        if self.get_by_username(username) is not None:
            raise ValueError(f"이미 존재하는 사용자명입니다: {username}")
        payload = {
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
        }
        r = self._db.table("admin_users").insert(payload).execute()
        return r.data[0]

    def delete(self, admin_id: int) -> bool:
        r = self._db.table("admin_users").delete().eq("id", admin_id).execute()
        return bool(r.data)

    def update_role(self, admin_id: int, role: str) -> dict | None:
        r = (
            self._db.table("admin_users")
            .update({"role": role})
            .eq("id", admin_id)
            .execute()
        )
        return r.data[0] if r.data else None
