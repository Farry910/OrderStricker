from __future__ import annotations

import os


def mongo_uri() -> str | None:
    v = os.environ.get("MONGO_URI") or os.environ.get("ORDERSTRICKER_MONGO_URI")
    return v.strip() if v else None


def mongo_db_name() -> str:
    return os.environ.get("ORDERSTRICKER_MONGO_DB", "orderstricker")


def redis_url() -> str | None:
    v = os.environ.get("REDIS_URL") or os.environ.get("ORDERSTRICKER_REDIS_URL")
    return v.strip() if v else None


def catalog_cache_ttl_seconds() -> int:
    return max(15, int(os.environ.get("ORDERSTRICKER_CATALOG_CACHE_SEC", "90")))


def redis_conversation_ttl_seconds() -> int:
    return max(300, int(os.environ.get("ORDERSTRICKER_CONVERSATION_REDIS_TTL_SEC", "86400")))
