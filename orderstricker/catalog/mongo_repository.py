"""Mongo-backed product catalog."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from orderstricker.catalog.repository import Product


class MongoCatalogRepository:
    """Backed by pymongo Collection with documents shaped like Product."""

    def __init__(self, coll: object) -> None:
        self._coll = coll

    def get(self, product_id: UUID) -> Product | None:
        doc = self._coll.find_one({"_id": str(product_id)})
        if doc is None:
            return None
        return _doc_to_product(doc)

    def resolve_by_name(self, name: str) -> Product | None:
        needle = name.strip().lower()
        doc = self._coll.find_one({"name_lower": needle})
        if doc is None:
            return None
        return _doc_to_product(doc)

    def list_products(self) -> list[Product]:
        cur = self._coll.find({}).sort("name_lower", 1)
        return [_doc_to_product(d) for d in cur]


def _doc_to_product(doc: dict) -> Product:
    rid = doc["_id"]
    if isinstance(rid, UUID):
        pid = rid
    else:
        pid = UUID(str(rid))
    return Product(
        id=pid,
        name=doc["name"],
        available=bool(doc["available"]),
        list_price=Decimal(str(doc["list_price"])),
    )


def seed_products_collection(coll: object, rows: list[tuple[Product, str]]) -> None:
    """Upsert products; rows are (Product, name_lower)."""
    for p, name_lower in rows:
        coll.update_one(
            {"_id": str(p.id)},
            {
                "$set": {
                    "name": p.name,
                    "name_lower": name_lower,
                    "available": p.available,
                    "list_price": str(p.list_price),
                },
            },
            upsert=True,
        )
    coll.create_index("name_lower", unique=True)
