from __future__ import annotations

import os
from decimal import Decimal
from uuid import UUID

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from orderstricker.api.bootstrap import _candidates, _catalog
from orderstricker.conversation.ollama_translate import translate_user_message


class ProductOut(BaseModel):
    id: UUID
    name: str
    available: bool
    list_price: str


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatOut(BaseModel):
    reply: str
    error: str | None = None
    """True when assistant is unavailable or reply could not be applied; grid unchanged."""

    degraded: bool = False
    products: list[ProductOut]


def create_app() -> FastAPI:
    app = FastAPI(title="OrderStricker API", version="0.1.0")

    origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/products", response_model=list[ProductOut])
    def list_products(user_id: UUID | None = Query(default=None)) -> list[ProductOut]:
        q = Decimal("0.01")
        if user_id is not None:
            products = _candidates.list_products(_catalog, user_id)
        else:
            products = _catalog.list_products()
        return [
            ProductOut(
                id=p.id,
                name=p.name,
                available=p.available,
                list_price=str(p.list_price.quantize(q)),
            )
            for p in products
        ]

    @app.post("/api/session/{user_id}/chat", response_model=ChatOut)
    def chat_nl(user_id: UUID, payload: ChatBody) -> ChatOut:
        tr = translate_user_message(payload.message, _catalog)
        q = Decimal("0.01")
        prods_raw = _candidates.list_products(_catalog, user_id)

        product_outs = [
            ProductOut(
                id=p.id,
                name=p.name,
                available=p.available,
                list_price=str(p.list_price.quantize(q)),
            )
            for p in prods_raw
        ]

        if tr.degraded_mode:
            return ChatOut(
                reply=tr.reply,
                error=None,
                degraded=True,
                products=product_outs,
            )

        _candidates.set_from_names(user_id, _catalog, tr.parsed.show_products)
        return ChatOut(
            reply=tr.reply,
            error=None,
            degraded=False,
            products=[
                ProductOut(
                    id=p.id,
                    name=p.name,
                    available=p.available,
                    list_price=str(p.list_price.quantize(q)),
                )
                for p in _candidates.list_products(_catalog, user_id)
            ],
        )

    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "orderstricker.api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "").lower() in ("1", "true", "yes"),
    )


if __name__ == "__main__":
    run()
