import json
from pathlib import Path

from src.core.security import hash_password

DATA_FILE = Path("data/admin.json")

_DEFAULT_USERNAME = "admin"
_DEFAULT_PASSWORD = "admin1234"


class AdminRepository:
    """Singleton JSON repository for admin credentials."""

    _instance: "AdminRepository | None" = None

    def __new__(cls) -> "AdminRepository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        DATA_FILE.parent.mkdir(exist_ok=True)
        if not DATA_FILE.exists():
            self._save(
                {
                    "username": _DEFAULT_USERNAME,
                    "hashed_password": hash_password(_DEFAULT_PASSWORD),
                }
            )
        self._initialized = True

    def _load(self) -> dict:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_credentials(self) -> dict:
        """Return stored admin credentials dict."""
        return self._load()
