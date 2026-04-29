from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from orderstricker.ordering.models import Cart, Order, OrderStatus


class PairStoreProtocol(Protocol):
    def load(self, user_id: UUID) -> tuple[Cart, Order]:
        ...

    def save(self, user_id: UUID, cart: Cart, order: Order) -> None:
        ...


class MemoryPairStore:
    """In-process carts and orders (tests and offline dev without MongoDB)."""

    def __init__(self) -> None:
        self._carts: dict[UUID, Cart] = {}
        self._orders: dict[UUID, Order] = {}

    def load(self, user_id: UUID) -> tuple[Cart, Order]:
        if user_id not in self._carts:
            self._carts[user_id] = Cart(user_id=user_id)
            self._orders[user_id] = Order(user_id=user_id, status=OrderStatus.DRAFT)
        return self._carts[user_id], self._orders[user_id]

    def save(self, user_id: UUID, cart: Cart, order: Order) -> None:
        self._carts[user_id] = cart
        self._orders[user_id] = order


class MongoPairStore:
    """Persist cart + order snapshots per user in MongoDB."""

    def __init__(self, db: object, collection_name: str = "user_sessions") -> None:
        self._col = db[collection_name]

    def load(self, user_id: UUID) -> tuple[Cart, Order]:
        uid = str(user_id)
        doc = self._col.find_one({"_id": uid})
        if doc is None:
            return Cart(user_id=user_id), Order(user_id=user_id, status=OrderStatus.DRAFT)
        cart_raw = doc.get("cart")
        ord_raw = doc.get("order")
        cart = (
            Cart.model_validate(cart_raw) if cart_raw else Cart(user_id=user_id)
        )
        order = (
            Order.model_validate(ord_raw)
            if ord_raw
            else Order(user_id=user_id, status=OrderStatus.DRAFT)
        )
        return cart, order

    def save(self, user_id: UUID, cart: Cart, order: Order) -> None:
        uid = str(user_id)
        self._col.update_one(
            {"_id": uid},
            {
                "$set": {
                    "cart": cart.model_dump(mode="python"),
                    "order": order.model_dump(mode="python"),
                    "updated_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
