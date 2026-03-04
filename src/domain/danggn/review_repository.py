"""
ReviewRepository — 후기 데이터 저장소 (Singleton).

BaseJsonRepository 상속으로 Singleton·_load·_save·_next_id 자동 확보.
"""
from pathlib import Path

from src.core.paths import DATA_DIR
from src.core.repository import BaseJsonRepository
from src.domain.danggn.schemas import ReviewCreate


class ReviewRepository(BaseJsonRepository):
    """Singleton JSON repository for reviews."""

    @property
    def file_path(self) -> Path:
        return DATA_DIR / "danggn_reviews.json"

    def get_all(self) -> list[dict]:
        return self._load()

    def create(self, data: ReviewCreate) -> dict:
        reviews = self._load()
        new_review = {"id": self._next_id(reviews), **data.model_dump()}
        reviews.append(new_review)
        self._save(reviews)
        return new_review
