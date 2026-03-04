import logging

from src.core.security import verify_password
from src.domain.admin.admin_user_repository import AdminUserRepository
from src.domain.admin.register_key_repository import RegisterKeyRepository

logger = logging.getLogger(__name__)


class AdminUserService:
    def __init__(
        self,
        repo: AdminUserRepository | None = None,
        key_repo: RegisterKeyRepository | None = None,
    ) -> None:
        self._repo = repo or AdminUserRepository()
        self._key_repo = key_repo or RegisterKeyRepository()

    def authenticate(self, username: str, password: str) -> dict | None:
        """Verify credentials. Returns full user dict (without hashed_password) on success, None otherwise."""
        user = self._repo.get_by_username(username)
        if user is None:
            logger.warning("Admin login failed: unknown username '%s'", username)
            return None
        if not verify_password(password, user["hashed_password"]):
            logger.warning("Admin login failed: wrong password for '%s'", username)
            return None
        return {k: v for k, v in user.items() if k != "hashed_password"}

    def get_by_id(self, admin_id: int) -> dict | None:
        user = self._repo.get_by_id(admin_id)
        if user is None:
            return None
        return {k: v for k, v in user.items() if k != "hashed_password"}

    def get_all(self) -> list[dict]:
        return [{k: v for k, v in u.items() if k != "hashed_password"} for u in self._repo.get_all()]

    def create_admin(self, username: str, password: str, role: str) -> dict:
        """Create a new admin user. Raises ValueError if username already exists."""
        from src.core.security import hash_password
        hashed = hash_password(password)
        user = self._repo.create(username, hashed, role)
        return {k: v for k, v in user.items() if k != "hashed_password"}

    def delete_admin(self, admin_id: int) -> bool:
        """Delete admin user. Returns False if not found."""
        return self._repo.delete(admin_id)

    def update_role(self, admin_id: int, role: str) -> dict | None:
        user = self._repo.update_role(admin_id, role)
        if user is None:
            return None
        return {k: v for k, v in user.items() if k != "hashed_password"}

    # ── 등록 키 관리 ──────────────────────────────────────────────────────────

    def generate_register_key(self, created_by: str) -> dict:
        return self._key_repo.create(created_by)

    def get_register_keys(self) -> list[dict]:
        return self._key_repo.get_all()

    def revoke_register_key(self, key_id: int) -> bool:
        return self._key_repo.revoke(key_id)

    def consume_register_key(self, key: str, used_by: str) -> bool:
        """키 유효성 검사 후 사용 처리. 실패 시 False 반환."""
        if not self._key_repo.is_valid(key):
            return False
        return self._key_repo.consume(key, used_by)
