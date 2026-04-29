"""Session context for chat (Redis in production)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConversationSession:
    session_id: str
    last_intent: str | None = None
    current_step: str | None = None  # e.g. awaiting_confirmation, browse, checkout
    extra: dict[str, Any] | None = None


class SessionStore:
    """In-memory store; bootstrap uses Redis when REDIS_URL is set."""

    def __init__(self) -> None:
        self._data: dict[str, ConversationSession] = {}

    def get(self, session_id: str) -> ConversationSession | None:
        return self._data.get(session_id)

    def save(self, session: ConversationSession) -> None:
        self._data[session.session_id] = session
