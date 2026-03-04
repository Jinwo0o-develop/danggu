"""
CustomerRepository — 고객 계정 저장소 (Singleton).

BaseJsonRepository 상속으로 Singleton·_load·_save·_next_id 자동 확보.
"""
from datetime import datetime
from pathlib import Path

from src.core.repository import BaseJsonRepository
from src.core.security import hash_password
from src.domain.customer.schemas import CustomerCreate


class CustomerRepository(BaseJsonRepository):
    """Singleton JSON repository for customer accounts."""

    @property
    def file_path(self) -> Path:
        return Path("data/customers.json")

    # ── 조회 ──────────────────────────────────────────────────────

    def get_by_email(self, email: str) -> dict | None:
        return next((c for c in self._load() if c["email"] == email), None)

    def get_by_id(self, customer_id: int) -> dict | None:
        return next((c for c in self._load() if c["id"] == customer_id), None)

    def get_all(self) -> list[dict]:
        return self._load()

    # ── 쓰기 ──────────────────────────────────────────────────────

    def create(self, data: CustomerCreate) -> dict:
        customers = self._load()
        new_customer = {
            "id": self._next_id(customers),
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "name": data.name,
            "phone": data.phone,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        customers.append(new_customer)
        self._save(customers)
        return new_customer

    def update_phone(self, customer_id: int, phone: str) -> dict | None:
        customers = self._load()
        for i, c in enumerate(customers):
            if c["id"] == customer_id:
                customers[i] = {**c, "phone": phone}
                self._save(customers)
                return customers[i]
        return None

    def delete(self, customer_id: int) -> bool:
        customers = self._load()
        filtered = [c for c in customers if c["id"] != customer_id]
        if len(filtered) == len(customers):
            return False
        self._save(filtered)
        return True
