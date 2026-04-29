# OrderSticker / OrderStricker
This is OLLAMA based ordering service.

## Persistence

- **`MONGO_URI`** (alias `ORDERSTRICKER_MONGO_URI`) — When set (e.g. `mongodb://localhost:27017`), products and cart/order snapshots use MongoDB. Optional **`ORDERSTRICKER_MONGO_DB`** (default `orderstricker`).
- **`REDIS_URL`** (`ORDERSTRICKER_REDIS_URL`) — When set, caches product list JSON (`list_products`), command idempotency + payment dedup (with Mongo active), and conversation overlays. TTLs configurable via `ORDERSTRICKER_CATALOG_CACHE_SEC` / `ORDERSTRICKER_CONVERSATION_REDIS_TTL_SEC`.

If neither URI is set, catalog and sessions remain in-memory (good for tests and local hacks).

Compose: `docker compose up -d` for MongoDB and Redis on default ports (`docker-compose.yml`).
