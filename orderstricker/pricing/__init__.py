"""Totals, tax, discounts — always computed server-side."""

from __future__ import annotations

from decimal import Decimal

from orderstricker.ordering.models import Cart, CartItem


def line_total(item: CartItem) -> Decimal:
    return Decimal(item.unit_price) * item.quantity


def cart_subtotal(cart: Cart) -> Decimal:
    return sum((line_total(i) for i in cart.items), start=Decimal("0"))


def order_total_from_cart(cart: Cart, tax_rate: Decimal = Decimal("0")) -> Decimal:
    """MVP: subtotal * (1 + tax_rate). Extend with discount rules in this module only."""
    sub = cart_subtotal(cart)
    return sub * (Decimal("1") + tax_rate)
