from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemDto(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    price: float = Field(gt=0)
    qty: int = Field(gt=0, le=100)


class NewOrderDto(BaseModel):
    customer: str = Field(min_length=3, max_length=255)
    items: list[OrderItemDto]
    total: float


class OrderViewDto(BaseModel):
    id: int
    customer: str
    items: list[OrderItemDto]
    total: float
    status: str
    tries: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime
