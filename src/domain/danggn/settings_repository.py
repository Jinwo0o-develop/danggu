import json
from pathlib import Path

from src.core.paths import DATA_DIR

DATA_FILE = DATA_DIR / "danggn_settings.json"

DEFAULT_SETTINGS: dict = {"auto_cancel_days": 7}


class SettingsRepository:
    """Singleton JSON repository for app-level settings."""

    _instance: "SettingsRepository | None" = None

    def __new__(cls) -> "SettingsRepository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        DATA_FILE.parent.mkdir(exist_ok=True)
        if not DATA_FILE.exists():
            DATA_FILE.write_text(
                json.dumps(DEFAULT_SETTINGS, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        self._initialized = True

    def _load(self) -> dict:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_auto_cancel_days(self) -> int:
        return int(self._load().get("auto_cancel_days", 7))

    def set_auto_cancel_days(self, days: int) -> None:
        settings = self._load()
        settings["auto_cancel_days"] = days
        self._save(settings)
