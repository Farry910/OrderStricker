"""Deterministic catalog: stable UUID per product name; 50 seeded items for browsing + chat."""

from __future__ import annotations

from decimal import Decimal
from random import Random
from uuid import UUID, uuid5

# Stable namespace for catalog item ids (do not change — existing DB rows key on these).
CATALOG_NAMESPACE = UUID("8c7b5c2e-4f1a-5b3d-9e2c-1a0f6d4e8b2c")


def stable_product_id(name: str) -> UUID:
    return uuid5(CATALOG_NAMESPACE, name.strip().lower())


def build_product_specs(count: int = 50, seed: int = 42_867_530_9) -> list[tuple[str, Decimal, bool]]:
    """Reproducible pseudo-random products: names unique, prices varied, mostly available."""
    rng = Random(seed)
    moods = ["Arctic", "Velvet", "Urban", "Coastal", "Smoked", "Crisp", "Bold", "Sublime"]
    mains = ["Bowl", "Plate", "Box", "Stack", "Hash", "Slab", "Rounds", "Trio"]
    cores = ["Tuna", "Lamb", "Pork", "Tofu", "Quinoa", "Miso", "Yuzu", "Ginger", "Kale", "Citrus"]

    picked: list[str] = []
    suffix = 401
    while len(picked) < count:
        m = rng.choice(moods)
        n = rng.choice(mains)
        c = rng.choice(cores)
        name = f"{m} {c} {n} #{suffix}"
        suffix += 1
        if name.lower() not in {x.lower() for x in picked}:
            picked.append(name)

    rows: list[tuple[str, Decimal, bool]] = []
    for i, name in enumerate(picked):
        # Pseudo-random price in café range; two items unavailable so UI can distinguish
        frac = Decimal(f"{rng.uniform(7.50, 64.95):.2f}")
        available = i not in (11, 37)  # indices 11 and 37 off-menu
        rows.append((name, frac, available))
    return rows


PRODUCT_SPEC_ROWS: list[tuple[str, Decimal, bool]] = build_product_specs(50)
