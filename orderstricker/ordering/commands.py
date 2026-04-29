"""All mutations enter through typed commands; LLM never calls service methods directly — app layer maps intents here."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from orderstricker.ordering.models import OrderStatus


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    message: str
    data: dict | None = None


@dataclass(frozen=True)
class AddItemToCart:
    user_id: UUID
    product_id: UUID
    quantity: int
    idempotency_key: str


@dataclass(frozen=True)
class RemoveItemFromCart:
    user_id: UUID
    product_id: UUID
    idempotency_key: str


@dataclass(frozen=True)
class StartCheckout:
    user_id: UUID
    idempotency_key: str


@dataclass(frozen=True)
class ConfirmOrder:
    user_id: UUID
    idempotency_key: str


@dataclass(frozen=True)
class PayOrder:
    user_id: UUID
    idempotency_key: str


OrderingCommand = (
    AddItemToCart | RemoveItemFromCart | StartCheckout | ConfirmOrder | PayOrder
)

CommandName = Literal[
    "add_item",
    "remove_item",
    "start_checkout",
    "confirm_order",
    "pay_order",
]


def command_name(cmd: OrderingCommand) -> CommandName:
    if isinstance(cmd, AddItemToCart):
        return "add_item"
    if isinstance(cmd, RemoveItemFromCart):
        return "remove_item"
    if isinstance(cmd, StartCheckout):
        return "start_checkout"
    if isinstance(cmd, ConfirmOrder):
        return "confirm_order"
    return "pay_order"
