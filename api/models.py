from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class OrderStatus(StrEnum):
    QUEUED = 'queued'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'
    MANUAL_REVIEW = 'manual_review'


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String(255))
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    total: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.QUEUED.value)
    tries: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
