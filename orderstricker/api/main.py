from __future__ import annotations

import os
from decimal import Decimal
from uuid import UUID, uuid4

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from orderstricker.api.bootstrap import _catalog, ordering
from orderstricker.ordering import commands as c
from orderstricker.ordering.models import OrderStatus


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

    class ProductOut(BaseModel):
        id: UUID
        name: str
        available: bool
        list_price: str

    class CartItemOut(BaseModel):
        product_id: UUID
        quantity: int
        unit_price: str

    class CartOut(BaseModel):
        id: UUID
        user_id: UUID
        items: list[CartItemOut]

    class OrderOut(BaseModel):
        id: UUID
        user_id: UUID
        status: OrderStatus
        total_amount: str

    class SessionOut(BaseModel):
        cart: CartOut
        order: OrderOut

    class AddToCartBody(BaseModel):
        product_id: UUID
        quantity: int = Field(ge=1)

    class ApiResult(BaseModel):
        ok: bool
        message: str
        data: dict | None = None

    @app.get("/api/products", response_model=list[ProductOut])
    def list_products() -> list[ProductOut]:
        q = Decimal("0.01")
        return [
            ProductOut(
                id=p.id,
                name=p.name,
                available=p.available,
                list_price=str(p.list_price.quantize(q)),
            )
            for p in _catalog.list_products()
        ]

    @app.get("/api/session/{user_id}", response_model=SessionOut)
    def get_session(user_id: UUID) -> SessionOut:
        cart = ordering.get_cart(user_id)
        order = ordering.get_order(user_id)
        return SessionOut(
            cart=CartOut(
                id=cart.id,
                user_id=cart.user_id,
                items=[
                    CartItemOut(
                        product_id=i.product_id,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                    )
                    for i in cart.items
                ],
            ),
            order=OrderOut(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
            ),
        )

    def wrap(r: c.CommandResult) -> ApiResult:
        return ApiResult(ok=r.ok, message=r.message, data=r.data)

    @app.post("/api/session/{user_id}/cart/items", response_model=ApiResult)
    def add_to_cart(user_id: UUID, body: AddToCartBody) -> ApiResult:
        cmd = c.AddItemToCart(user_id, body.product_id, body.quantity, str(uuid4()))
        return wrap(ordering.dispatch(cmd))

    @app.delete("/api/session/{user_id}/cart/items/{product_id}", response_model=ApiResult)
    def remove_from_cart(user_id: UUID, product_id: UUID) -> ApiResult:
        cmd = c.RemoveItemFromCart(user_id, product_id, str(uuid4()))
        return wrap(ordering.dispatch(cmd))

    @app.post("/api/session/{user_id}/checkout/start", response_model=ApiResult)
    def start_checkout(user_id: UUID) -> ApiResult:
        return wrap(ordering.dispatch(c.StartCheckout(user_id, str(uuid4()))))

    @app.post("/api/session/{user_id}/checkout/confirm", response_model=ApiResult)
    def confirm_order(user_id: UUID) -> ApiResult:
        return wrap(ordering.dispatch(c.ConfirmOrder(user_id, str(uuid4()))))

    @app.post("/api/session/{user_id}/checkout/pay", response_model=ApiResult)
    def pay(user_id: UUID) -> ApiResult:
        return wrap(ordering.dispatch(c.PayOrder(user_id, str(uuid4()))))

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
