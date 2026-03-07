"""
DanggnApplicationRepository — 당근마켓 신청 데이터 저장소 (Supabase).

lookup_code 자동 생성 로직은 이 클래스의 고유 책임.
Supabase 미설정 시 데모 모드로 동작한다.
"""
import secrets

from src.core.supabase_client import get_supabase
from src.domain.danggn.schemas import ApplicationCreate


_DEMO_APPLICATIONS: list[dict] = [
    {"id": 1,  "name": "이수연", "phone": "010-1234-5678", "item_name": "삼성 노트북 15인치",   "description": "사용감 거의 없음, 충전기 포함", "listed_price": "무료나눔", "category": "전자제품", "status": "정산완료", "lookup_code": "ABC123", "created_at": "2026-01-10", "user_id": None, "media_files": [], "sale_price": 185000, "commission_rate": 0.2, "commission_amount": 37000, "settlement_amount": 148000},
    {"id": 2,  "name": "김민지", "phone": "010-2345-6789", "item_name": "원목 책상 + 의자 세트", "description": "이사로 처분, 흠집 약간 있음",       "listed_price": "무료나눔", "category": "가구",   "status": "판매중",   "lookup_code": "DEF456", "created_at": "2026-01-18", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 3,  "name": "오미래", "phone": "010-3456-7890", "item_name": "LG 공기청정기 AS401",   "description": "필터 교체 완료, 정상 작동",   "listed_price": "무료나눔", "category": "가전",   "status": "수거예정", "lookup_code": "GHI789", "created_at": "2026-02-02", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 4,  "name": "정유나", "phone": "010-4567-8901", "item_name": "아이 장난감 박스 (대)",  "description": "레고·피셔프라이스 등 포함",   "listed_price": "무료나눔", "category": "육아",   "status": "접수됨",   "lookup_code": "JKL012", "created_at": "2026-02-14", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 5,  "name": "박성훈", "phone": "010-5678-9012", "item_name": "나이키 러닝화 270",     "description": "세탁 완료, 밑창 양호",       "listed_price": "무료나눔", "category": "의류",   "status": "정산완료", "lookup_code": "MNO345", "created_at": "2026-01-25", "user_id": None, "media_files": [], "sale_price": 42000, "commission_rate": 0.2, "commission_amount": 8400, "settlement_amount": 33600},
    {"id": 6,  "name": "강민서", "phone": "010-6789-0123", "item_name": "소파 2인용 패브릭",     "description": "중간 사용감, 세탁 가능",     "listed_price": "무료나눔", "category": "가구",   "status": "판매중",   "lookup_code": "PQR678", "created_at": "2026-02-20", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 7,  "name": "최재현", "phone": "010-7890-1234", "item_name": "다이슨 드라이기 V11",   "description": "박스·액세서리 완비",         "listed_price": "무료나눔", "category": "가전",   "status": "수거예정", "lookup_code": "STU901", "created_at": "2026-03-01", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 8,  "name": "한동준", "phone": "010-8901-2345", "item_name": "겨울 패딩 L (롱)",      "description": "건조 상태 양호, 지퍼 정상", "listed_price": "무료나눔", "category": "의류",   "status": "접수됨",   "lookup_code": "VWX234", "created_at": "2026-03-04", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 9,  "name": "강지현", "phone": "010-9012-3456", "item_name": "유아 바운서 + 모빌",    "description": "사용 횟수 적음, 세척 완료", "listed_price": "무료나눔", "category": "육아",   "status": "취소됨",   "lookup_code": "YZA567", "created_at": "2026-02-08", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 10, "name": "윤성민", "phone": "010-0123-4567", "item_name": "애플워치 SE 2세대",     "description": "배터리 92%, 스크래치 없음", "listed_price": "무료나눔", "category": "전자제품","status": "정산완료", "lookup_code": "BCD890", "created_at": "2026-01-30", "user_id": None, "media_files": [], "sale_price": 210000, "commission_rate": 0.2, "commission_amount": 42000, "settlement_amount": 168000},
    {"id": 11, "name": "임도현", "phone": "010-1234-5678", "item_name": "침대 프레임 퀸사이즈",  "description": "분리 가능, 매트리스 별도",  "listed_price": "무료나눔", "category": "가구",   "status": "접수됨",   "lookup_code": "EFG123", "created_at": "2026-03-05", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
    {"id": 12, "name": "송하영", "phone": "010-2345-6789", "item_name": "요가매트 + 폼롤러",     "description": "3회 사용, 거의 새것",       "listed_price": "무료나눔", "category": "스포츠", "status": "판매중",   "lookup_code": "HIJ456", "created_at": "2026-03-06", "user_id": None, "media_files": [], "sale_price": None, "commission_rate": None, "commission_amount": None, "settlement_amount": None},
]


class DanggnApplicationRepository:
    def __init__(self) -> None:
        self._db = get_supabase()

    # ── lookup_code 관리 ──────────────────────────────────────────

    def _generate_lookup_code(self) -> str:
        return secrets.token_urlsafe(4)[:6].upper()

    # ── 조회 ─────────────────────────────────────────────────────

    def get_all(self) -> list[dict]:
        if self._db is None:
            return [dict(a) for a in _DEMO_APPLICATIONS]
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
        if self._db is None:
            return next((dict(a) for a in _DEMO_APPLICATIONS if a["id"] == application_id), None)
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
        if self._db is None:
            return [dict(a) for a in _DEMO_APPLICATIONS if a["phone"] == phone]
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
        if self._db is None:
            return next((dict(a) for a in _DEMO_APPLICATIONS if a["lookup_code"] == code.upper()), None)
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
        if self._db is None:
            # 데모 모드: 실제 저장 없이 가상 응답 반환
            return {
                "id": 0,
                "lookup_code": self._generate_lookup_code(),
                "status": "접수됨",
                **data.model_dump(),
                "created_at": "",
                "sale_price": None,
                "commission_rate": None,
                "commission_amount": None,
                "settlement_amount": None,
            }
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
        if self._db is None:
            return None
        r = (
            self._db.table("danggn_applications")
            .update(fields)
            .eq("id", application_id)
            .execute()
        )
        return r.data[0] if r.data else None
