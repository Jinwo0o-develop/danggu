"""
DanggnApplicationRepository — 당근마켓 신청 데이터 저장소.

BaseJsonRepository(Template Method) 상속으로 Singleton·_load·_save 자동 확보.
lookup_code 자동 생성·보정 로직은 이 클래스의 고유 책임.
"""
import secrets
from datetime import datetime
from pathlib import Path

from src.core.repository import BaseJsonRepository
from src.domain.danggn.schemas import ApplicationCreate


class DanggnApplicationRepository(BaseJsonRepository):
    """JSON repository for danggn applications."""

    @property
    def file_path(self) -> Path:
        return Path("data/danggn_applications.json")

    # ── lookup_code 관리 ──────────────────────────────────────────

    def _generate_lookup_code(self) -> str:
        return secrets.token_urlsafe(4)[:6].upper()

    def _fill_missing_codes(self, apps: list[dict]) -> tuple[list[dict], bool]:
        """누락된 lookup_code를 채우고 (apps, 변경여부) 반환."""
        changed = False
        for app in apps:
            if not app.get("lookup_code"):
                app["lookup_code"] = self._generate_lookup_code()
                changed = True
        return apps, changed

    # ── 조회 ─────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        apps = self._load()
        apps, changed = self._fill_missing_codes(apps)
        if changed:
            self._save(apps)
        return apps

    def get_by_id(self, application_id: int) -> dict | None:
        apps = self._load()
        app = next((a for a in apps if a["id"] == application_id), None)
        if app is None:
            return None
        if not app.get("lookup_code"):
            code = self._generate_lookup_code()
            self.update_fields(application_id, {"lookup_code": code})
            app["lookup_code"] = code
        return app

    def get_by_phone(self, phone: str) -> list[dict]:
        apps = self._load()
        matched = [a for a in apps if a.get("phone") == phone]
        changed = False
        lookup = {}
        for app in matched:
            if not app.get("lookup_code"):
                app["lookup_code"] = self._generate_lookup_code()
                changed = True
                lookup[app["id"]] = app
        if changed:
            full = self._load()
            for i, a in enumerate(full):
                if a["id"] in lookup:
                    full[i] = lookup[a["id"]]
            self._save(full)
        return matched

    def get_by_lookup_code(self, code: str) -> dict | None:
        return next(
            (a for a in self._load() if a.get("lookup_code") == code.upper()),
            None,
        )

    # ── 쓰기 ─────────────────────────────────────────────────────

    def create(self, data: ApplicationCreate) -> dict:
        apps = self._load()
        new_app = {
            "id": self._next_id(apps),
            **data.model_dump(),
            "status": "접수됨",
            "lookup_code": self._generate_lookup_code(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "sale_price": None,
            "commission_rate": None,
            "commission_amount": None,
            "settlement_amount": None,
        }
        apps.append(new_app)
        self._save(apps)
        return new_app

    def update_status(self, application_id: int, new_status: str) -> dict | None:
        """Convenience wrapper — delegates to update_fields()."""
        return self.update_fields(application_id, {"status": new_status})

    def update_fields(self, application_id: int, fields: dict) -> dict | None:
        """임의 필드를 업데이트하고 갱신된 레코드를 반환."""
        apps = self._load()
        for i, a in enumerate(apps):
            if a["id"] == application_id:
                apps[i] = {**a, **fields}
                self._save(apps)
                return apps[i]
        return None
