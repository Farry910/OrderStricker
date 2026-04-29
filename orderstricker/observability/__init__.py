from __future__ import annotations

from collections import Counter

_metrics: Counter[str] = Counter()


def record(name: str) -> None:
    _metrics[name] += 1


def snapshot() -> dict[str, int]:
    return dict(_metrics)
