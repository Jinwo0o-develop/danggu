from pydantic import BaseModel


class CustomerCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: str = ""


class CustomerLogin(BaseModel):
    email: str
    password: str


class CustomerResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    created_at: str
