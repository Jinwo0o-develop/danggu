"""
AuthCodeRepository — SMS 인증코드 저장소 (Supabase).

danggn_auth_codes 테이블은 phone이 PK이므로
upsert로 phone별 최신 코드 1개만 유지된다.
"""
import secrets
from datetime import datetime, timedelta, timezone

from src.core.supabase_client import get_supabase

TTL = 600  # seconds (10분)


class AuthCodeRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def generate(self, phone: str) -> str:
        """전화번호에 대한 6자리 인증코드를 생성하고 반환한다."""
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = (self._now() + timedelta(seconds=TTL)).isoformat()
        payload = {
            "phone": phone,
            "code": code,
            "expires_at": expires_at,
            "used": False,
        }
        # phone이 PK이므로 upsert로 기존 코드를 교체
        self._db.table("danggn_auth_codes").upsert(payload).execute()
        return code

    def verify(self, phone: str, code: str) -> bool:
        """코드가 유효하면 used=True 로 업데이트하고 True 반환."""
        r = (
            self._db.table("danggn_auth_codes")
            .select("*")
            .eq("phone", phone)
            .maybe_single()
            .execute()
        )
        record = r.data
        if not record or record["code"] != code:
            return False
        if record["used"]:
            return False
        expires_at = datetime.fromisoformat(record["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= self._now():
            return False
        self._db.table("danggn_auth_codes").update({"used": True}).eq("phone", phone).execute()
        return True

    def cleanup_expired(self) -> None:
        """만료된 레코드를 삭제한다."""
        now_iso = self._now().isoformat()
        self._db.table("danggn_auth_codes").delete().lt("expires_at", now_iso).execute()
