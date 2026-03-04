"""CustomerRepository — 고객 계정 저장소 (Supabase)."""
from src.core.security import hash_password
from src.core.supabase_client import get_supabase
from src.domain.customer.schemas import CustomerCreate


class CustomerRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    # ── 조회 ──────────────────────────────────────────────────────

    def get_by_email(self, email: str) -> dict | None:
        if self._db is None:
            return None
        r = self._db.table("customers").select("*").eq("email", email).maybe_single().execute()
        return r.data

    def get_by_id(self, customer_id: int) -> dict | None:
        if self._db is None:
            return None
        r = self._db.table("customers").select("*").eq("id", customer_id).maybe_single().execute()
        return r.data

    def get_all(self) -> list[dict]:
        if self._db is None:
            return []
        r = self._db.table("customers").select("*").order("id").execute()
        return r.data or []

    # ── 쓰기 ──────────────────────────────────────────────────────

    def create(self, data: CustomerCreate) -> dict:
        if self._db is None:
            raise ValueError("데모 모드: 회원가입을 사용할 수 없습니다.")
        payload = {
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "name": data.name,
            "phone": data.phone,
        }
        r = self._db.table("customers").insert(payload).execute()
        return r.data[0]

    def update_phone(self, customer_id: int, phone: str) -> dict | None:
        if self._db is None:
            return None
        r = (
            self._db.table("customers")
            .update({"phone": phone})
            .eq("id", customer_id)
            .execute()
        )
        return r.data[0] if r.data else None

    def delete(self, customer_id: int) -> bool:
        if self._db is None:
            return False
        r = self._db.table("customers").delete().eq("id", customer_id).execute()
        return bool(r.data)
