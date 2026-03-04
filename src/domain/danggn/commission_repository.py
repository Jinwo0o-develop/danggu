"""CommissionRepository — 카테고리별 수수료율 저장소 (Supabase)."""
from src.core.supabase_client import get_supabase

DEFAULT_RATES: dict[str, float] = {
    "전자제품": 0.20,
    "가구": 0.15,
    "의류": 0.10,
    "기타": 0.15,
}


class CommissionRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def _rows_to_dict(self, rows: list[dict]) -> dict[str, float]:
        return {row["category"]: row["rate"] for row in rows}

    def get_all(self) -> dict[str, float]:
        r = self._db.table("danggn_commission_rates").select("*").execute()
        return self._rows_to_dict(r.data or [])

    def get_categories(self) -> list[str]:
        r = self._db.table("danggn_commission_rates").select("category").execute()
        return [row["category"] for row in (r.data or [])]

    def get_rate(self, category: str) -> float:
        """카테고리 수수료율 반환. 없으면 '기타' 요율로 폴백."""
        r = (
            self._db.table("danggn_commission_rates")
            .select("rate")
            .eq("category", category)
            .maybe_single()
            .execute()
        )
        if r.data:
            return r.data["rate"]
        # 폴백: '기타' 조회
        r2 = (
            self._db.table("danggn_commission_rates")
            .select("rate")
            .eq("category", "기타")
            .maybe_single()
            .execute()
        )
        return r2.data["rate"] if r2.data else DEFAULT_RATES["기타"]

    def set_rate(self, category: str, rate: float) -> None:
        self._db.table("danggn_commission_rates").upsert(
            {"category": category, "rate": rate}
        ).execute()

    def save_all(self, rates: dict[str, float]) -> None:
        rows = [{"category": cat, "rate": r} for cat, r in rates.items()]
        self._db.table("danggn_commission_rates").upsert(rows).execute()
