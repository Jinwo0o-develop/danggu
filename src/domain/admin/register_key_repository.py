"""RegisterKeyRepository — 관리자 등록 키 저장소 (Supabase)."""
import secrets
import string

from src.core.supabase_client import get_supabase


class RegisterKeyRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    @staticmethod
    def _make_key() -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(12))

    def create(self, created_by: str) -> dict:
        if self._db is None:
            return {}
        key = self._make_key()
        while self.get_by_key(key) is not None:
            key = self._make_key()
        payload = {
            "key": key,
            "created_by": created_by,
            "used": False,
            "used_by": None,
            "used_at": None,
            "revoked": False,
        }
        r = self._db.table("admin_register_keys").insert(payload).execute()
        return r.data[0]

    def get_all(self) -> list[dict]:
        if self._db is None:
            return []
        r = (
            self._db.table("admin_register_keys")
            .select("*")
            .order("id", desc=True)
            .execute()
        )
        return r.data or []

    def get_by_key(self, key: str) -> dict | None:
        if self._db is None:
            return None
        r = (
            self._db.table("admin_register_keys")
            .select("*")
            .eq("key", key)
            .maybe_single()
            .execute()
        )
        return r.data

    def is_valid(self, key: str) -> bool:
        record = self.get_by_key(key)
        return record is not None and not record["used"] and not record["revoked"]

    def consume(self, key: str, used_by: str) -> bool:
        """사용 처리. 이미 사용됐거나 폐지된 키는 False 반환."""
        record = self.get_by_key(key)
        if record is None or record["used"] or record["revoked"]:
            return False
        r = (
            self._db.table("admin_register_keys")
            .update({"used": True, "used_by": used_by, "used_at": "now()"})
            .eq("key", key)
            .execute()
        )
        return bool(r.data)

    def revoke(self, key_id: int) -> bool:
        """폐지 처리. 이미 사용된 키는 False 반환."""
        if self._db is None:
            return False
        r_find = (
            self._db.table("admin_register_keys")
            .select("used")
            .eq("id", key_id)
            .maybe_single()
            .execute()
        )
        if not r_find.data or r_find.data["used"]:
            return False
        r = (
            self._db.table("admin_register_keys")
            .update({"revoked": True})
            .eq("id", key_id)
            .execute()
        )
        return bool(r.data)
