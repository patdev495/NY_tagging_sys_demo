
from pydantic import BaseModel


class CustomerBase(BaseModel):
    code: str
    name: str

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    code: str | None = None
    name: str | None = None

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True
