"""Application singletons (catalog, ordering, optional MongoDB + Redis)."""

from __future__ import annotations

from uuid import UUID

from orderstricker.catalog.candidate_store import CandidateStore
from orderstricker.catalog.mongo_repository import MongoCatalogRepository, seed_products_collection
from orderstricker.catalog.redis_cached_repository import RedisCachedCatalogRepository
from orderstricker.catalog.repository import CatalogRepository, Product
from orderstricker.catalog.seed_data import PRODUCT_SPEC_ROWS, stable_product_id
from orderstricker.conversation import SessionStore
from orderstricker.conversation.redis_session_store import RedisConversationSessionStore
from orderstricker.order_state.pair_store import MemoryPairStore, MongoPairStore
from orderstricker.ordering.service import OrderingService
from orderstricker.persistence.idempotency import (
    MongoIdempotency,
    RedisIdempotency,
    MemoryIdempotency,
)
from orderstricker.persistence.settings import mongo_db_name, mongo_uri, redis_url


def _memory_catalog() -> CatalogRepository:
    products: dict[UUID, Product] = {}
    for name, price, available in PRODUCT_SPEC_ROWS:
        pid = stable_product_id(name)
        products[pid] = Product(id=pid, name=name, available=available, list_price=price)
    return CatalogRepository(products)


def _bootstrap() -> tuple[CatalogRepository, OrderingService, object, object]:
    """Wire MongoDB catalogue + user sessions when MONGO_URI is set; Redis when REDIS_URL is set."""

    catalog: CatalogRepository = _memory_catalog()
    pair_store: object = MemoryPairStore()
    idem: object = MemoryIdempotency()
    mongo_client = None

    redis_cli = None
    rurl = redis_url()
    if rurl:
        import redis as redis_lib

        redis_cli = redis_lib.from_url(rurl, decode_responses=True)

    muri = mongo_uri()
    if muri:
        from pymongo import MongoClient

        mongo_client = MongoClient(muri)
        db = mongo_client[mongo_db_name()]
        prod_coll = db["products"]

        rows_seed: list[tuple[Product, str]] = []
        for name, price, available in PRODUCT_SPEC_ROWS:
            pid = stable_product_id(name)
            rows_seed.append(
                (
                    Product(id=pid, name=name, available=available, list_price=price),
                    name.strip().lower(),
                )
            )
        seed_products_collection(prod_coll, rows_seed)

        mongo_catalog = MongoCatalogRepository(prod_coll)
        catalog = mongo_catalog
        pair_store = MongoPairStore(db, "user_sessions")

        if redis_cli:
            catalog = RedisCachedCatalogRepository(mongo_catalog, redis_cli)
            idem = RedisIdempotency(redis_cli)
        else:
            db["processed_commands"].create_index("_id", unique=True)
            idem = MongoIdempotency(db["processed_commands"])

    ordering = OrderingService(
        catalog,
        pair_store=pair_store,
        idempotency=idem,
    )

    if redis_cli is not None:
        conversation_store = RedisConversationSessionStore(redis_cli)
    else:
        conversation_store = SessionStore()

    return catalog, ordering, conversation_store, mongo_client


_catalog, ordering, conversation_store, _mongo_keepalive = _bootstrap()
_candidates = CandidateStore()

__all__ = ["_catalog", "ordering", "conversation_store", "_candidates"]
