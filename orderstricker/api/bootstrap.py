from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from orderstricker.catalog.repository import CatalogRepository, Product
from orderstricker.ordering.service import OrderingService


def seed_catalog() -> CatalogRepository:
    products: dict[UUID, Product] = {}
    specs = [
        ("Classic Burger", Decimal("12.50"), True),
        ("Garden Salad", Decimal("9.00"), True),
        ("Truffle Fries", Decimal("6.75"), True),
        ("Iced Tea", Decimal("3.25"), True),
        ("Chef Special", Decimal("24.00"), False),
    ]
    for name, price, available in specs:
        pid = uuid4()
        products[pid] = Product(id=pid, name=name, available=available, list_price=price)
    return CatalogRepository(products)


_catalog = seed_catalog()
ordering = OrderingService(_catalog)

__all__ = ["_catalog", "ordering", "seed_catalog"]
