"""All mutations enter through typed commands; LLM maps intents here."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID


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


OrderingCommand = (
    AddItemToCart | RemoveItemFromCart | StartCheckout | ConfirmOrder
)

CommandName = Literal["add_item", "remove_item", "start_checkout", "confirm_order"]


def command_name(cmd: OrderingCommand) -> CommandName:
    if isinstance(cmd, AddItemToCart):
        return "add_item"
    if isinstance(cmd, RemoveItemFromCart):
        return "remove_item"
    if isinstance(cmd, StartCheckout):
        return "start_checkout"
    return "confirm_order"
