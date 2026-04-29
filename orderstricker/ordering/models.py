from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CART_ACTIVE = "CART_ACTIVE"
    CHECKOUT = "CHECKOUT"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ABANDONED = "ABANDONED"


class CartItem(BaseModel):
    """Unit price is a server-side snapshot at add time; never trust LLM or client for pricing."""

    product_id: UUID
    quantity: int = Field(gt=0)
    unit_price: str  # Decimal-as-string avoids float; pricing domain sets this


class Cart(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    items: list[CartItem] = Field(default_factory=list)
    status: CartStatus = CartStatus.ACTIVE


class Order(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    status: OrderStatus = OrderStatus.DRAFT
    total_amount: str = "0"  # set by pricing domain
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
