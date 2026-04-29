"""Redis cache layer for catalog reads (list endpoint)."""

from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from orderstricker.catalog.repository import CatalogRepository, Product
from orderstricker.persistence.settings import catalog_cache_ttl_seconds


class RedisCachedCatalogRepository:
    """Wraps a CatalogRepository; caches list_products in Redis JSON."""

    def __init__(self, inner: CatalogRepository, redis_client: object, ttl_sec: int | None = None) -> None:
        self._inner = inner
        self._r = redis_client
        self._ttl = ttl_sec if ttl_sec is not None else catalog_cache_ttl_seconds()
        self._key = "orderstricker:cache:catalog_products_v1"

    def _invalidate(self) -> None:
        self._r.delete(self._key)

    def get(self, product_id: UUID) -> Product | None:
        return self._inner.get(product_id)

    def resolve_by_name(self, name: str) -> Product | None:
        return self._inner.resolve_by_name(name)

    def list_products(self) -> list[Product]:
        raw = self._r.get(self._key)
        if raw:
            try:
                data = json.loads(raw)
                return [_deserialize_product(o) for o in data]
            except (json.JSONDecodeError, KeyError, TypeError):
                self._invalidate()
        products = self._inner.list_products()
        blob = json.dumps([_serialize_product(p) for p in products])
        self._r.set(self._key, blob, ex=self._ttl)
        return products


def _serialize_product(p: Product) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "available": p.available,
        "list_price": str(p.list_price),
    }


def _deserialize_product(o: dict) -> Product:
    return Product(
        id=UUID(o["id"]),
        name=o["name"],
        available=bool(o["available"]),
        list_price=Decimal(o["list_price"]),
    )
