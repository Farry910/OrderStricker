"""Store conversation overlays in Redis JSON (TTL)."""

from __future__ import annotations

import json
from dataclasses import asdict

from orderstricker.conversation import ConversationSession
from orderstricker.persistence.settings import redis_conversation_ttl_seconds


class RedisConversationSessionStore:
    def __init__(self, client: object, prefix: str = "orderstricker:conversation:") -> None:
        self._r = client
        self._pfx = prefix
        self._ttl = redis_conversation_ttl_seconds()

    def get(self, session_id: str) -> ConversationSession | None:
        raw = self._r.get(self._pfx + session_id)
        if raw is None:
            return None
        try:
            d = json.loads(raw)
            return ConversationSession(
                session_id=d["session_id"],
                last_intent=d.get("last_intent"),
                current_step=d.get("current_step"),
                extra=d.get("extra"),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save(self, session: ConversationSession) -> None:
        blob = json.dumps(asdict(session))
        self._r.set(self._pfx + session.session_id, blob, ex=self._ttl)
