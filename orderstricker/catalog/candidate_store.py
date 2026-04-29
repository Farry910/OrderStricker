"""Per-user visible candidate product IDs (chat-driven storefront)."""

from __future__ import annotations

from uuid import UUID

from orderstricker.catalog.repository import CatalogRepository, Product


class CandidateStore:
    """In-memory map user_id → ordered list of catalog product ids to show."""

    def __init__(self) -> None:
        self._by_user: dict[str, list[UUID]] = {}

    def _default_ids(self, catalog: CatalogRepository) -> list[UUID]:
        return [p.id for p in catalog.list_products() if p.available]

    def get_ids(self, user_id: UUID, catalog: CatalogRepository) -> list[UUID]:
        key = str(user_id)
        if key not in self._by_user:
            self._by_user[key] = self._default_ids(catalog)
        return list(self._by_user[key])

    def set_from_names(self, user_id: UUID, catalog: CatalogRepository, names: list[str]) -> list[UUID]:
        """
        Resolve exact catalog names → product ids (order preserved, unique).
        Empty `names` ⇒ reset to all available products.
        Non-empty but no matches ⇒ keep previous ids for this user.
        """
        key = str(user_id)
        prev = self.get_ids(user_id, catalog)

        if not names:
            self._by_user[key] = self._default_ids(catalog)
            return list(self._by_user[key])

        resolved: list[UUID] = []
        seen: set[UUID] = set()
        for raw in names:
            if not isinstance(raw, str):
                continue
            p = catalog.resolve_by_name(raw)
            if p is not None and p.id not in seen:
                seen.add(p.id)
                resolved.append(p.id)

        if not resolved:
            self._by_user[key] = prev
            return prev

        self._by_user[key] = resolved
        return resolved

    def list_products(self, catalog: CatalogRepository, user_id: UUID) -> list[Product]:
        out: list[Product] = []
        for pid in self.get_ids(user_id, catalog):
            pr = catalog.get(pid)
            if pr is not None:
                out.append(pr)
        return out
