import json
from pathlib import Path

DATA_FILE = Path("data/danggn_commission_rates.json")

DEFAULT_RATES: dict[str, float] = {
    "전자제품": 0.20,
    "가구": 0.15,
    "의류": 0.10,
    "기타": 0.15,
}


class CommissionRepository:
    """Singleton JSON repository for category commission rates."""

    _instance: "CommissionRepository | None" = None

    def __new__(cls) -> "CommissionRepository":
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
                json.dumps(DEFAULT_RATES, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        self._initialized = True

    def _load(self) -> dict[str, float]:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, float]) -> None:
        DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_all(self) -> dict[str, float]:
        return self._load()

    def get_categories(self) -> list[str]:
        return list(self._load().keys())

    def get_rate(self, category: str) -> float:
        """Return commission rate for the given category. Falls back to '기타'."""
        rates = self._load()
        return rates.get(category, rates.get("기타", 0.15))

    def set_rate(self, category: str, rate: float) -> None:
        rates = self._load()
        rates[category] = rate
        self._save(rates)

    def save_all(self, rates: dict[str, float]) -> None:
        self._save(rates)
