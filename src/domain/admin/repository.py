"""
AdminRepository — 레거시 단일 관리자 자격증명 조회 (Supabase).

admin_users 테이블에서 첫 번째 super_admin 계정을 조회하여
기존 AdminService.authenticate() 인터페이스를 유지한다.
"""
from src.core.supabase_client import get_supabase


class AdminRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    def get_credentials(self) -> dict:
        """admin_users 테이블에서 첫 번째 super_admin 계정을 반환."""
        r = (
            self._db.table("admin_users")
            .select("username, hashed_password")
            .eq("role", "super_admin")
            .order("id")
            .limit(1)
            .execute()
        )
        if r.data:
            return r.data[0]
        return {}
