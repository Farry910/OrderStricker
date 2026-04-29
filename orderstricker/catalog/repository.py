"""Product definitions and availability. All references by ID only."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Product:
    id: UUID
    name: str
    available: bool
    list_price: Decimal  # reference for pricing snapshot at add-to-cart


class CatalogRepository:
    """Replace with DB; in-memory for scaffold."""

    def __init__(self, products: dict[UUID, Product]) -> None:
        self._products = products

    def get(self, product_id: UUID) -> Product | None:
        return self._products.get(product_id)

    def resolve_by_name(self, name: str) -> Product | None:
        needle = name.strip().lower()
        for p in self._products.values():
            if p.name.lower() == needle:
                return p
        return None

    def list_products(self) -> list[Product]:
        return sorted(self._products.values(), key=lambda p: p.name.lower())
