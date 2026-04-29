"""Command idempotency and payment deduplication backends (Redis or Mongo)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from pymongo.errors import DuplicateKeyError


class IdempotencyStore(Protocol):
    def has_processed(self, key: str) -> bool:
        ...

    def mark_processed(self, key: str) -> None:
        ...


class MemoryIdempotency:
    """Process-level idempotency (single worker)."""

    def __init__(self) -> None:
        self._keys: set[str] = set()

    def has_processed(self, key: str) -> bool:
        return key in self._keys

    def mark_processed(self, key: str) -> None:
        self._keys.add(key)


class RedisIdempotency:
    def __init__(self, client: object, key_prefix: str = "orderstricker:processed:") -> None:
        object.__setattr__(self, "_redis", client)
        object.__setattr__(self, "_pfx", key_prefix)

    def has_processed(self, key: str) -> bool:
        return bool(self._redis.exists(self._pfx + key))

    def mark_processed(self, key: str) -> None:
        self._redis.set(self._pfx + key, "1")


class MongoIdempotency:
    def __init__(self, collection: object) -> None:
        self._col = collection

    def has_processed(self, key: str) -> bool:
        return self._col.find_one({"_id": key}, {"_id": 1}) is not None

    def mark_processed(self, key: str) -> None:
        doc = {"_id": key, "at": datetime.now(timezone.utc)}
        try:
            self._col.insert_one(doc)
        except DuplicateKeyError:
            pass


class PaymentDedupBackend(Protocol):
    def capture_once(self, user_id: str, idempotency_key: str, amount_str: str) -> bool:
        """Returns True only the first charge for this (user,idempotency_key)."""


class MemoryPaymentDedup(PaymentDedupBackend):
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def capture_once(self, user_id: str, idempotency_key: str, amount_str: str) -> bool:
        k = (user_id, idempotency_key)
        if k in self._seen:
            return False
        self._seen.add(k)
        _ = amount_str
        return True


class MongoPaymentDedup(PaymentDedupBackend):
    def __init__(self, coll: object) -> None:
        self._coll = coll

    def capture_once(self, user_id: str, idempotency_key: str, amount_str: str) -> bool:
        _id = f"{user_id}:{idempotency_key}"
        doc = {"_id": _id, "amount": amount_str, "charged_at": datetime.now(timezone.utc)}
        try:
            self._coll.insert_one(doc)
            return True
        except DuplicateKeyError:
            return False


class RedisPaymentDedup(PaymentDedupBackend):
    def __init__(self, client: object, prefix: str = "orderstricker:pay:") -> None:
        self._r = client
        self._pfx = prefix

    def capture_once(self, user_id: str, idempotency_key: str, amount_str: str) -> bool:
        k = self._pfx + f"{user_id}:{idempotency_key}"
        return bool(self._r.set(k, amount_str, nx=True))
