"""Apply parsed LLM actions through OrderingService (names → UUIDs here)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from orderstricker.catalog.repository import CatalogRepository
from orderstricker.ordering import commands as c
from orderstricker.ordering.service import OrderingService
from orderstricker.conversation.ollama_translate import ChatParsed, fresh_idem


@dataclass
class ActionOutcome:
    action: str
    ok: bool
    message: str


def run_parsed_actions(
    user_id: UUID,
    parsed: ChatParsed,
    catalog: CatalogRepository,
    ordering: OrderingService,
) -> list[ActionOutcome]:
    out: list[ActionOutcome] = []
    for raw in parsed.actions:
        if not isinstance(raw, dict):
            out.append(ActionOutcome("unknown", False, "Invalid action entry"))
            continue
        kind = raw.get("action")
        if not isinstance(kind, str):
            out.append(ActionOutcome("unknown", False, "Missing action type"))
            continue

        if kind == "add_item":
            name = raw.get("product_name")
            qty = raw.get("quantity", 1)
            if not isinstance(name, str) or not name.strip():
                out.append(ActionOutcome(kind, False, "add_item needs product_name"))
                continue
            if not isinstance(qty, int):
                try:
                    qty = int(qty)
                except (TypeError, ValueError):
                    out.append(ActionOutcome(kind, False, "add_item needs integer quantity"))
                    continue
            prod = catalog.resolve_by_name(name)
            if prod is None:
                out.append(ActionOutcome(kind, False, f"No product matching {name!r}"))
                continue
            cmd = c.AddItemToCart(user_id, prod.id, qty, fresh_idem())
            r = ordering.dispatch(cmd)
            out.append(ActionOutcome(kind, r.ok, r.message))
            continue

        if kind == "remove_item":
            name = raw.get("product_name")
            if not isinstance(name, str) or not name.strip():
                out.append(ActionOutcome(kind, False, "remove_item needs product_name"))
                continue
            prod = catalog.resolve_by_name(name)
            if prod is None:
                out.append(ActionOutcome(kind, False, f"No product matching {name!r}"))
                continue
            cmd = c.RemoveItemFromCart(user_id, prod.id, fresh_idem())
            r = ordering.dispatch(cmd)
            out.append(ActionOutcome(kind, r.ok, r.message))
            continue

        if kind == "start_checkout":
            r = ordering.dispatch(c.StartCheckout(user_id, fresh_idem()))
            out.append(ActionOutcome(kind, r.ok, r.message))
            continue

        if kind == "confirm_order":
            r = ordering.dispatch(c.ConfirmOrder(user_id, fresh_idem()))
            out.append(ActionOutcome(kind, r.ok, r.message))
            continue

        out.append(ActionOutcome(kind, False, f"Unknown action {kind!r}"))

    return out
