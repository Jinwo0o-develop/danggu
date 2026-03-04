import logging

from src.core.security import verify_password
from src.domain.admin.repository import AdminRepository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repo: AdminRepository) -> None:
        self._repo = repo

    def authenticate(self, username: str, password: str) -> bool:
        """Verify credentials. Returns True on success, False otherwise."""
        creds = self._repo.get_credentials()
        if creds.get("username") != username:
            logger.warning("Admin login failed: unknown username '%s'", username)
            return False
        if not verify_password(password, creds["hashed_password"]):
            logger.warning("Admin login failed: wrong password for '%s'", username)
            return False
        return True
