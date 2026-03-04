import logging

from src.core.security import verify_password
from src.domain.customer.repository import CustomerRepository
from src.domain.customer.schemas import CustomerCreate, CustomerResponse

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, repo: CustomerRepository | None = None) -> None:
        self._repo = repo or CustomerRepository()

    def register(self, data: CustomerCreate) -> CustomerResponse:
        """Register a new customer. Raises ValueError if email already exists."""
        if self._repo.get_by_email(data.email):
            raise ValueError("이미 사용 중인 이메일입니다.")
        customer = self._repo.create(data)
        return CustomerResponse(**{k: v for k, v in customer.items() if k != "hashed_password"})

    def authenticate(self, email: str, password: str) -> dict | None:
        """Verify credentials. Returns customer dict (without password) on success, None otherwise."""
        customer = self._repo.get_by_email(email)
        if customer is None:
            logger.warning("Customer login failed: unknown email '%s'", email)
            return None
        if not verify_password(password, customer["hashed_password"]):
            logger.warning("Customer login failed: wrong password for '%s'", email)
            return None
        return {k: v for k, v in customer.items() if k != "hashed_password"}

    def get_by_id(self, customer_id: int) -> CustomerResponse | None:
        customer = self._repo.get_by_id(customer_id)
        if customer is None:
            return None
        return CustomerResponse(**{k: v for k, v in customer.items() if k != "hashed_password"})

    def get_all(self) -> list[CustomerResponse]:
        return [
            CustomerResponse(**{k: v for k, v in c.items() if k != "hashed_password"})
            for c in self._repo.get_all()
        ]

    def link_phone(self, customer_id: int, phone: str) -> CustomerResponse | None:
        updated = self._repo.update_phone(customer_id, phone)
        if updated is None:
            return None
        return CustomerResponse(**{k: v for k, v in updated.items() if k != "hashed_password"})

    def delete(self, customer_id: int) -> bool:
        return self._repo.delete(customer_id)
