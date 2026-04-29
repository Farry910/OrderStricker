"""Map natural language to storefront refresh via Ollama (HTTP)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from orderstricker.catalog.repository import CatalogRepository


def _catalog_block(catalog: CatalogRepository) -> str:
    lines = []
    for p in catalog.list_products():
        st = "available" if p.available else "unavailable — do not feature"
        lines.append(f"- {p.name!r}: spelling must match exactly; ({st}), ${p.list_price:.2f}")
    return "\n".join(lines) if lines else "(empty catalog)"


SYSTEM_PROMPT = """You are a helpful retail stylist for a product showroom. Customers chat to narrow down what appears on screen.

Respond with ONE JSON object only (no markdown), shape:
{"reply":"<short friendly message for the shopper>","show_products":["Exact Name 1", "Exact Name 2", ...]}

Rules for "show_products":
- Use 1–24 product names copied EXACTLY from the CATALOG list (same spelling and punctuation).
- Pick items that best match what the user asked for (style, price range, ingredients, mood, etc.).
- If the user asks to see everything again, or says "show all" / "reset", use an empty array: "show_products": []
- An empty "show_products" resets the screen to show all available products.
- If nothing matches well, still suggest a small set of reasonable alternatives and explain in "reply".

Do not include any other top-level keys."""


class ChatParsed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reply: str = ""
    show_products: list[str] = Field(default_factory=list)


@dataclass
class ChatTranslationResult:
    reply: str
    parsed: ChatParsed
    error: str | None = None
    """When True, do not mutate storefront candidates (e.g. Ollama unreachable)."""

    degraded_mode: bool = False


_REPLY_OFFLINE = (
    "The style assistant isn't available right now, so your product wall stays exactly as-is. "
    "You're still browsing normally — start Ollama when you'd like chat-driven refinements."
)

_REPLY_MODEL_MISMATCH = (
    "The assistant replied in an unexpected format, so nothing was changed. Try again after starting Ollama."
)


_REQUEST_TIMEOUT = httpx.Timeout(45.0, connect=5.0)


def translate_user_message(text: str, catalog: CatalogRepository) -> ChatTranslationResult:
    """Call Ollama /api/chat. On unreachable service, return degraded_mode with a friendly reply (no exceptions)."""

    base = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    user_block = (
        f"CATALOG:\n{_catalog_block(catalog)}\n\n"
        f"USER MESSAGE:\n{text.strip()}\n"
        "Produce the JSON response."
    )

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_block},
        ],
    }

    try:
        with httpx.Client(timeout=_REQUEST_TIMEOUT) as client:
            r = client.post(f"{base}/api/chat", json=payload)
            r.raise_for_status()
            body = r.json()
    except (httpx.RequestError, OSError):
        return ChatTranslationResult(
            reply=_REPLY_OFFLINE,
            parsed=ChatParsed(),
            error=None,
            degraded_mode=True,
        )
    except httpx.HTTPStatusError:
        return ChatTranslationResult(
            reply=_REPLY_OFFLINE,
            parsed=ChatParsed(),
            error=None,
            degraded_mode=True,
        )
    try:
        content = body["message"]["content"]
        data = json.loads(content) if isinstance(content, str) else content
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        _ = e
        return ChatTranslationResult(
            reply=_REPLY_MODEL_MISMATCH,
            parsed=ChatParsed(),
            error=None,
            degraded_mode=True,
        )

    try:
        parsed = ChatParsed.model_validate(data)
    except ValidationError:
        return ChatTranslationResult(
            reply=_REPLY_MODEL_MISMATCH,
            parsed=ChatParsed(),
            error=None,
            degraded_mode=True,
        )

    return ChatTranslationResult(
        reply=parsed.reply.strip() or "OK.",
        parsed=parsed,
        error=None,
        degraded_mode=False,
    )
