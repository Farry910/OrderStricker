"""Strict order lifecycle: no skips except cancel."""

from __future__ import annotations

from orderstricker.ordering.models import OrderStatus

# Confirm ends the flow at FULFILLED (selection saved via DB/chat); no separate payment stage.
_FORWARD: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.DRAFT: frozenset({OrderStatus.CART_ACTIVE, OrderStatus.CANCELLED}),
    OrderStatus.CART_ACTIVE: frozenset({OrderStatus.CHECKOUT, OrderStatus.CANCELLED}),
    OrderStatus.CHECKOUT: frozenset({OrderStatus.FULFILLED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset(),
    OrderStatus.PAID: frozenset(),
    OrderStatus.FULFILLED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def can_transition(from_status: OrderStatus, to_status: OrderStatus) -> bool:
    if to_status == OrderStatus.CANCELLED:
        return from_status not in (OrderStatus.FULFILLED, OrderStatus.CANCELLED)
    allowed = _FORWARD.get(from_status, frozenset())
    return to_status in allowed


def assert_transition(from_status: OrderStatus, to_status: OrderStatus) -> None:
    if not can_transition(from_status, to_status):
        raise ValueError(f"Illegal transition: {from_status.value} → {to_status.value}")
