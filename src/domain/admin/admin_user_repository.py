"""
AdminUserRepository — 다중 관리자 계정 저장소 (Singleton).

BaseJsonRepository 상속으로 Singleton·_load·_save·_next_id 자동 확보.
최초 실행 시 레거시 admin.json → admin_users.json 마이그레이션 지원.
"""
import json
import logging
from pathlib import Path

from src.core.repository import BaseJsonRepository
from src.core.security import hash_password

LEGACY_FILE = Path("data/admin.json")

logger = logging.getLogger(__name__)


class AdminUserRepository(BaseJsonRepository):
    """Singleton JSON repository for multi-admin accounts with roles."""

    @property
    def file_path(self) -> Path:
        return Path("data/admin_users.json")

    def _write_default(self) -> None:
        """레거시 마이그레이션 또는 기본 관리자 계정 생성."""
        if LEGACY_FILE.exists():
            try:
                legacy = json.loads(LEGACY_FILE.read_text(encoding="utf-8"))
                admin_users = [
                    {
                        "id": 1,
                        "username": legacy.get("username", "admin"),
                        "hashed_password": legacy["hashed_password"],
                        "role": "super_admin",
                    }
                ]
                self.file_path.write_text(
                    json.dumps(admin_users, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info("Migrated admin.json → admin_users.json (role=super_admin)")
                return
            except Exception as exc:
                logger.warning("Migration failed: %s — creating default admin", exc)

        # 기본 관리자 계정
        admin_users = [
            {
                "id": 1,
                "username": "admin",
                "hashed_password": hash_password("admin1234"),
                "role": "super_admin",
            }
        ]
        self.file_path.write_text(
            json.dumps(admin_users, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── 조회 ──────────────────────────────────────────────────────

    def get_by_username(self, username: str) -> dict | None:
        return next((u for u in self._load() if u["username"] == username), None)

    def get_by_id(self, admin_id: int) -> dict | None:
        return next((u for u in self._load() if u["id"] == admin_id), None)

    def get_all(self) -> list[dict]:
        return self._load()

    # ── 쓰기 ──────────────────────────────────────────────────────

    def create(self, username: str, hashed_password: str, role: str) -> dict:
        users = self._load()
        if any(u["username"] == username for u in users):
            raise ValueError(f"이미 존재하는 사용자명입니다: {username}")
        new_user = {
            "id": self._next_id(users),
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
        }
        users.append(new_user)
        self._save(users)
        return new_user

    def delete(self, admin_id: int) -> bool:
        users = self._load()
        filtered = [u for u in users if u["id"] != admin_id]
        if len(filtered) == len(users):
            return False
        self._save(filtered)
        return True

    def update_role(self, admin_id: int, role: str) -> dict | None:
        users = self._load()
        for i, u in enumerate(users):
            if u["id"] == admin_id:
                users[i] = {**u, "role": role}
                self._save(users)
                return users[i]
        return None
