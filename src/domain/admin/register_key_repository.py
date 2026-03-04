import json
import secrets
import string
from datetime import datetime
from pathlib import Path

from src.core.paths import DATA_DIR

DATA_FILE = DATA_DIR / "admin_register_keys.json"


class RegisterKeyRepository:
    def __init__(self) -> None:
        DATA_FILE.parent.mkdir(exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: list[dict]) -> None:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _make_key() -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(12))

    def create(self, created_by: str) -> dict:
        keys = self._load()
        existing = {k["key"] for k in keys}
        key = self._make_key()
        while key in existing:
            key = self._make_key()
        new_id = max((k["id"] for k in keys), default=0) + 1
        record = {
            "id": new_id,
            "key": key,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "used": False,
            "used_by": None,
            "used_at": None,
            "revoked": False,
        }
        keys.append(record)
        self._save(keys)
        return record

    def get_all(self) -> list[dict]:
        return sorted(self._load(), key=lambda k: k["id"], reverse=True)

    def get_by_key(self, key: str) -> dict | None:
        return next((k for k in self._load() if k["key"] == key), None)

    def is_valid(self, key: str) -> bool:
        record = self.get_by_key(key)
        return record is not None and not record["used"] and not record["revoked"]

    def consume(self, key: str, used_by: str) -> bool:
        """사용 처리. 이미 사용됐거나 폐지된 키는 False 반환."""
        keys = self._load()
        for i, k in enumerate(keys):
            if k["key"] == key:
                if k["used"] or k["revoked"]:
                    return False
                keys[i] = {
                    **k,
                    "used": True,
                    "used_by": used_by,
                    "used_at": datetime.now().isoformat(timespec="seconds"),
                }
                self._save(keys)
                return True
        return False

    def revoke(self, key_id: int) -> bool:
        """폐지 처리. 이미 사용된 키는 False 반환."""
        keys = self._load()
        for i, k in enumerate(keys):
            if k["id"] == key_id:
                if k["used"]:
                    return False
                keys[i] = {**k, "revoked": True}
                self._save(keys)
                return True
        return False
