"""Payment only in CHECKOUT→CONFIRMED path; idempotent captures."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class PaymentLedger:
    """Tracks idempotency keys per user/order to prevent double charge."""

    _seen: set[tuple[UUID, str]] = field(default_factory=set)

    def try_charge(self, user_id: UUID, idempotency_key: str, amount: str) -> bool:
        k = (user_id, idempotency_key)
        if k in self._seen:
            return True  # idempotent success (already applied)
        self._seen.add(k)
        # integrate PSP here; scaffold always succeeds
        _ = amount
        return True
