"""ReviewRepository — 후기 데이터 저장소 (Supabase)."""
from src.core.supabase_client import get_supabase
from src.domain.danggn.schemas import ReviewCreate


class ReviewRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def get_all(self) -> list[dict]:
        r = self._db.table("danggn_reviews").select("*").order("id").execute()
        return r.data or []

    def create(self, data: ReviewCreate) -> dict:
        r = self._db.table("danggn_reviews").insert(data.model_dump()).execute()
        return r.data[0]
