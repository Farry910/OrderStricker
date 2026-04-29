from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from orderstricker.catalog.repository import CatalogRepository
from orderstricker.order_state.pair_store import MemoryPairStore, PairStoreProtocol
from orderstricker.ordering import commands as c
from orderstricker.ordering.models import Cart, CartItem, Order, OrderStatus
from orderstricker.ordering.state_machine import assert_transition
from orderstricker.persistence.idempotency import IdempotencyStore, MemoryIdempotency
from orderstricker.pricing import order_total_from_cart
from orderstricker import observability

MAX_LINE_QUANTITY = 10


class OrderingService:
    """
    Single entry for cart/order mutations from the application layer.
    Conversation maps LLM output to commands; this service enforces rules.
    """

    def __init__(
        self,
        catalog: CatalogRepository,
        tax_rate: Decimal = Decimal("0"),
        *,
        pair_store: PairStoreProtocol | None = None,
        idempotency: IdempotencyStore | None = None,
    ) -> None:
        self._catalog = catalog
        self._tax_rate = tax_rate
        self._pairs: PairStoreProtocol = pair_store or MemoryPairStore()
        self._idempotency: IdempotencyStore = idempotency or MemoryIdempotency()

    def _idem_key_for(self, cmd: c.OrderingCommand) -> str:
        return f"{c.command_name(cmd)}:{cmd.user_id}:{cmd.idempotency_key}"

    def _recalc_total(self, user_id: UUID) -> None:
        cart, order = self._pairs.load(user_id)
        total = order_total_from_cart(cart, self._tax_rate)
        order.total_amount = str(total.quantize(Decimal("0.01")))
        self._pairs.save(user_id, cart, order)

    def get_cart(self, user_id: UUID) -> Cart:
        cart, _ = self._pairs.load(user_id)
        return cart

    def get_order(self, user_id: UUID) -> Order:
        _, order = self._pairs.load(user_id)
        return order

    def dispatch(self, cmd: c.OrderingCommand) -> c.CommandResult:
        key = self._idem_key_for(cmd)
        if self._idempotency.has_processed(key):
            return c.CommandResult(True, "duplicate idempotency key — no change", None)

        if isinstance(cmd, c.AddItemToCart):
            return self._add_item(cmd, key)
        elif isinstance(cmd, c.RemoveItemFromCart):
            return self._remove_item(cmd, key)
        elif isinstance(cmd, c.StartCheckout):
            return self._start_checkout(cmd, key)
        else:
            return self._confirm(cmd, key)

    def _allow_cart_edit(self, status: OrderStatus) -> bool:
        return status in (OrderStatus.DRAFT, OrderStatus.CART_ACTIVE)

    def _add_item(self, cmd: c.AddItemToCart, idem_key: str) -> c.CommandResult:
        cart, order = self._pairs.load(cmd.user_id)
        if not self._allow_cart_edit(order.status):
            observability.record("failed_checkout_cart_locked")
            return c.CommandResult(False, "Cart cannot change in current order state", None)
        product = self._catalog.get(cmd.product_id)
        if product is None:
            observability.record("invalid_product_attempt")
            return c.CommandResult(False, "Unknown product", None)
        if not product.available:
            observability.record("invalid_product_attempt")
            return c.CommandResult(False, "Product unavailable", None)
        if cmd.quantity <= 0:
            return c.CommandResult(False, "Quantity must be greater than zero", None)
        if cmd.quantity > MAX_LINE_QUANTITY:
            observability.record("business_rule_rejection")
            return c.CommandResult(
                False,
                f"Maximum allowed quantity is {MAX_LINE_QUANTITY}",
                None,
            )

        unit_price = str(product.list_price.quantize(Decimal("0.01")))

        new_items: list[CartItem] = []
        merged = False
        for item in cart.items:
            if item.product_id == cmd.product_id:
                new_qty = item.quantity + cmd.quantity
                if new_qty > MAX_LINE_QUANTITY:
                    observability.record("business_rule_rejection")
                    return c.CommandResult(
                        False,
                        f"Maximum allowed quantity is {MAX_LINE_QUANTITY}",
                        None,
                    )
                new_items.append(
                    CartItem(
                        product_id=item.product_id,
                        quantity=new_qty,
                        unit_price=unit_price,
                    )
                )
                merged = True
            else:
                new_items.append(item)
        if not merged:
            new_items.append(
                CartItem(
                    product_id=cmd.product_id,
                    quantity=cmd.quantity,
                    unit_price=unit_price,
                )
            )

        cart = Cart(
            id=cart.id,
            user_id=cart.user_id,
            items=new_items,
            status=cart.status,
        )

        if order.status == OrderStatus.DRAFT:
            assert_transition(order.status, OrderStatus.CART_ACTIVE)
            order.status = OrderStatus.CART_ACTIVE

        self._pairs.save(cmd.user_id, cart, order)
        self._recalc_total(cmd.user_id)
        self._idempotency.mark_processed(idem_key)
        observability.record("add_item_success")
        _, order2 = self._pairs.load(cmd.user_id)
        return c.CommandResult(True, "Added to cart", {"total": order2.total_amount})

    def _remove_item(self, cmd: c.RemoveItemFromCart, idem_key: str) -> c.CommandResult:
        cart, order = self._pairs.load(cmd.user_id)
        if not self._allow_cart_edit(order.status):
            return c.CommandResult(False, "Cart cannot change in current order state", None)
        new_items = [i for i in cart.items if i.product_id != cmd.product_id]
        cart = Cart(
            id=cart.id,
            user_id=cart.user_id,
            items=new_items,
            status=cart.status,
        )
        self._pairs.save(cmd.user_id, cart, order)
        self._recalc_total(cmd.user_id)
        self._idempotency.mark_processed(idem_key)
        _, ord2 = self._pairs.load(cmd.user_id)
        return c.CommandResult(True, "Removed", {"total": ord2.total_amount})

    def _start_checkout(self, cmd: c.StartCheckout, idem_key: str) -> c.CommandResult:
        cart, order = self._pairs.load(cmd.user_id)
        if order.status != OrderStatus.CART_ACTIVE:
            observability.record("failed_checkout_wrong_state")
            return c.CommandResult(False, "Start checkout only from active cart", None)
        if len(cart.items) < 1:
            observability.record("failed_checkout_empty_cart")
            return c.CommandResult(False, "Cart must have at least one item", None)
        assert_transition(order.status, OrderStatus.CHECKOUT)
        order.status = OrderStatus.CHECKOUT
        self._pairs.save(cmd.user_id, cart, order)
        self._recalc_total(cmd.user_id)
        self._idempotency.mark_processed(idem_key)
        observability.record("checkout_started")
        _, order2 = self._pairs.load(cmd.user_id)
        return c.CommandResult(
            True,
            f"Review total ${order2.total_amount}. Confirm to save?",
            {"total": order2.total_amount, "awaiting_confirmation": True},
        )

    def _confirm(self, cmd: c.ConfirmOrder, idem_key: str) -> c.CommandResult:
        cart, order = self._pairs.load(cmd.user_id)
        if order.status != OrderStatus.CHECKOUT:
            return c.CommandResult(False, "Confirm only during checkout review", None)
        assert_transition(order.status, OrderStatus.FULFILLED)
        order.status = OrderStatus.FULFILLED
        self._pairs.save(cmd.user_id, cart, order)
        self._idempotency.mark_processed(idem_key)
        observability.record("selection_finalized")
        _, order2 = self._pairs.load(cmd.user_id)
        return c.CommandResult(
            True,
            "Selection saved to your profile.",
            {"total": order2.total_amount, "status": "FULFILLED"},
        )
