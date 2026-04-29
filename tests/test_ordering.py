from decimal import Decimal
from uuid import uuid4

import pytest

from orderstricker.catalog import CatalogRepository, Product
from orderstricker.ordering.commands import (
    AddItemToCart,
    ConfirmOrder,
    StartCheckout,
)
from orderstricker.ordering.models import OrderStatus
from orderstricker.ordering.service import MAX_LINE_QUANTITY, OrderingService


@pytest.fixture
def burger_id():
    return uuid4()


@pytest.fixture
def catalog(burger_id):
    p = Product(
        id=burger_id,
        name="burger",
        available=True,
        list_price=Decimal("8.50"),
    )
    return CatalogRepository({burger_id: p})


@pytest.fixture
def svc(catalog):
    return OrderingService(catalog)


@pytest.fixture
def user_id():
    return uuid4()


def test_add_item_rejects_over_max(svc, user_id, burger_id):
    r = svc.dispatch(
        AddItemToCart(user_id, burger_id, MAX_LINE_QUANTITY + 1, "k1"),
    )
    assert r.ok is False
    assert "Maximum" in r.message


def test_happy_path_checkout_then_confirm_saved(svc, user_id, burger_id):
    assert svc.dispatch(AddItemToCart(user_id, burger_id, 2, "a")).ok
    assert svc.get_order(user_id).status == OrderStatus.CART_ACTIVE
    assert svc.dispatch(StartCheckout(user_id, "c")).ok
    assert svc.get_order(user_id).status == OrderStatus.CHECKOUT
    assert svc.dispatch(ConfirmOrder(user_id, "d")).ok
    assert svc.get_order(user_id).status == OrderStatus.FULFILLED


def test_confirm_after_checkout_only(svc, user_id, burger_id):
    svc.dispatch(AddItemToCart(user_id, burger_id, 1, "a"))
    r = svc.dispatch(ConfirmOrder(user_id, "d"))
    assert r.ok is False


def test_idempotent_confirm(svc, user_id, burger_id):
    svc.dispatch(AddItemToCart(user_id, burger_id, 1, "a"))
    svc.dispatch(StartCheckout(user_id, "c"))
    svc.dispatch(ConfirmOrder(user_id, "same"))
    r2 = svc.dispatch(ConfirmOrder(user_id, "same"))
    assert r2.ok and "duplicate" in r2.message.lower()
