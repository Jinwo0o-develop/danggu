from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    name: str
    phone: str
    item_name: str
    description: str
    listed_price: str = "무료나눔"
    media_files: list[str] = []
    category: str = "기타"
    user_id: int | None = None


class ApplicationResponse(ApplicationCreate):
    id: int
    status: str = "접수됨"        # 기존 레코드 backward-compatibility용 기본값
    lookup_code: str = ""          # 6자리 대문자 영숫자 식별코드
    created_at: str = ""
    sale_price: int | None = None
    commission_rate: float | None = None
    commission_amount: int | None = None
    settlement_amount: int | None = None


class ReviewCreate(BaseModel):
    rating: str       # "like" | "dislike"
    comment: str = ""


class ReviewResponse(ReviewCreate):
    id: int
