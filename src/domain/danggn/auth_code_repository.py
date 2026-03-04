"""
AuthCodeRepository — SMS 인증코드 시뮬레이션 저장소.

data/danggn_auth_codes.json 에 코드를 저장하고,
TTL(10분) 기반 만료 처리를 담당한다.
"""
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.paths import DATA_DIR

DATA_FILE = DATA_DIR / "danggn_auth_codes.json"
TTL = 600  # seconds (10분)


class AuthCodeRepository:
    def __init__(self) -> None:
        DATA_FILE.parent.mkdir(exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]")

    # ── 내부 헬퍼 ────────────────────────────────────────────

    def _load(self) -> list[dict]:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: list[dict]) -> None:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    # ── 공개 API ─────────────────────────────────────────────

    def generate(self, phone: str) -> str:
        """전화번호에 대한 6자리 인증코드를 생성하고 반환한다."""
        self.cleanup_expired()
        records = self._load()

        # 기존 미사용 코드 제거
        records = [r for r in records if r["phone"] != phone]

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = (self._now() + timedelta(seconds=TTL)).isoformat()

        records.append(
            {
                "phone": phone,
                "code": code,
                "expires_at": expires_at,
                "used": False,
            }
        )
        self._save(records)
        return code

    def verify(self, phone: str, code: str) -> bool:
        """코드가 유효하면 used=True 로 업데이트하고 True 반환."""
        records = self._load()
        now = self._now()

        for i, r in enumerate(records):
            if r["phone"] != phone or r["code"] != code:
                continue
            if r["used"]:
                return False
            expires_at = datetime.fromisoformat(r["expires_at"])
            if expires_at <= now:
                return False
            records[i]["used"] = True
            self._save(records)
            return True
        return False

    def cleanup_expired(self) -> None:
        """만료된 레코드를 삭제한다."""
        records = self._load()
        now = self._now()
        active = [
            r for r in records
            if datetime.fromisoformat(r["expires_at"]) > now
        ]
        if len(active) < len(records):
            self._save(active)
