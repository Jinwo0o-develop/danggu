"""
DanggnApplicationRepository — 당근마켓 신청 데이터 저장소 (Supabase).

lookup_code 자동 생성 로직은 이 클래스의 고유 책임.
"""
import secrets

from src.core.supabase_client import get_supabase
from src.domain.danggn.schemas import ApplicationCreate


class DanggnApplicationRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    # ── lookup_code 관리 ──────────────────────────────────────────

    def _generate_lookup_code(self) -> str:
        return secrets.token_urlsafe(4)[:6].upper()

    # ── 조회 ─────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        r = self._db.table("danggn_applications").select("*").order("id").execute()
        apps = r.data or []
        # 누락된 lookup_code 보정
        for app in apps:
            if not app.get("lookup_code"):
                code = self._generate_lookup_code()
                self._db.table("danggn_applications").update(
                    {"lookup_code": code}
                ).eq("id", app["id"]).execute()
                app["lookup_code"] = code
        return apps

    def get_by_id(self, application_id: int) -> dict | None:
        r = (
            self._db.table("danggn_applications")
            .select("*")
            .eq("id", application_id)
            .maybe_single()
            .execute()
        )
        app = r.data
        if app and not app.get("lookup_code"):
            code = self._generate_lookup_code()
            self._db.table("danggn_applications").update(
                {"lookup_code": code}
            ).eq("id", application_id).execute()
            app["lookup_code"] = code
        return app

    def get_by_phone(self, phone: str) -> list[dict]:
        r = (
            self._db.table("danggn_applications")
            .select("*")
            .eq("phone", phone)
            .order("id")
            .execute()
        )
        apps = r.data or []
        for app in apps:
            if not app.get("lookup_code"):
                code = self._generate_lookup_code()
                self._db.table("danggn_applications").update(
                    {"lookup_code": code}
                ).eq("id", app["id"]).execute()
                app["lookup_code"] = code
        return apps

    def get_by_lookup_code(self, code: str) -> dict | None:
        r = (
            self._db.table("danggn_applications")
            .select("*")
            .eq("lookup_code", code.upper())
            .maybe_single()
            .execute()
        )
        return r.data

    # ── 쓰기 ─────────────────────────────────────────────────────

    def create(self, data: ApplicationCreate) -> dict:
        payload = {
            **data.model_dump(),
            "status": "접수됨",
            "lookup_code": self._generate_lookup_code(),
            "sale_price": None,
            "commission_rate": None,
            "commission_amount": None,
            "settlement_amount": None,
        }
        r = self._db.table("danggn_applications").insert(payload).execute()
        return r.data[0]

    def update_status(self, application_id: int, new_status: str) -> dict | None:
        return self.update_fields(application_id, {"status": new_status})

    def update_fields(self, application_id: int, fields: dict) -> dict | None:
        r = (
            self._db.table("danggn_applications")
            .update(fields)
            .eq("id", application_id)
            .execute()
        )
        return r.data[0] if r.data else None
