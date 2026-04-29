import { useCallback, useEffect, useMemo, useState } from "react";
import {
  addToCart,
  confirmOrder,
  fetchProducts,
  fetchSession,
  getOrCreateUserId,
  payOrder,
  removeFromCart,
  startCheckout,
} from "./api";
import type { OrderStatus, Product, Session } from "./types";

function money(n: string, qty: number): string {
  const a = Number.parseFloat(n);
  if (Number.isNaN(a)) return "—";
  return (a * qty).toFixed(2);
}

const STATUS_LABEL: Record<OrderStatus, string> = {
  DRAFT: "Draft",
  CART_ACTIVE: "Cart active",
  CHECKOUT: "Checkout — confirm required",
  CONFIRMED: "Confirmed — pay to complete",
  PAID: "Paid",
  FULFILLED: "Fulfilled",
  CANCELLED: "Cancelled",
};

export default function App() {
  const userId = useMemo(() => getOrCreateUserId(), []);
  const [products, setProducts] = useState<Product[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState<{ kind: "ok" | "bad"; text: string } | null>(null);
  const [quantities, setQuantities] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    setSession(await fetchSession(userId));
  }, [userId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [p, s] = await Promise.all([fetchProducts(), fetchSession(userId)]);
        if (!cancelled) {
          setProducts(p);
          setSession(s);
          const q: Record<string, string> = {};
          for (const x of p) q[x.id] = "1";
          setQuantities((prev) => ({ ...q, ...prev }));
        }
      } catch (e) {
        if (!cancelled) {
          setFlash({
            kind: "bad",
            text:
              e instanceof Error
                ? e.message
                : "Could not reach API. Start the backend (orderstricker-api on port 8000).",
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const productNameById = useMemo(() => {
    const m = new Map<string, string>();
    for (const p of products) m.set(p.id, p.name);
    return m;
  }, [products]);

  const status = session?.order.status ?? "DRAFT";
  const canEditCart = status === "DRAFT" || status === "CART_ACTIVE";
  const canStartCheckout = status === "CART_ACTIVE" && (session?.cart.items.length ?? 0) > 0;
  const canConfirm = status === "CHECKOUT";
  const canPay = status === "CONFIRMED";

  async function run(
    action: () => Promise<{ ok: boolean; message: string }>,
    successPrefix?: string,
  ) {
    setFlash(null);
    try {
      const r = await action();
      await refresh();
      setFlash({
        kind: r.ok ? "ok" : "bad",
        text: successPrefix && r.ok ? `${successPrefix} ${r.message}` : r.message,
      });
    } catch (e) {
      setFlash({
        kind: "bad",
        text: e instanceof Error ? e.message : "Request failed",
      });
    }
  }

  if (loading) {
    return (
      <div className="app">
        <p className="loading">Loading menu…</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-head">
        <div>
          <h1>OrderStricker</h1>
          <p>
            Order management engine with a conversational-ready API. Cart rules and totals are enforced on
            the server — this UI only sends commands.
          </p>
        </div>
        <span className={`badge ${status !== "DRAFT" ? "badge-strong" : ""}`}>
          {STATUS_LABEL[status]}
        </span>
      </header>

      <div className="layout">
        <section>
          <h2>Menu</h2>
          <div className="card-grid">
            {products.map((p) => (
              <article key={p.id} className={`product-card ${p.available ? "" : "disabled"}`}>
                <h3>{p.name}</h3>
                <div className="product-meta">
                  <span className="price">${p.list_price}</span>
                  {!p.available ? <span className="unavailable">Unavailable</span> : null}
                </div>
                <div className="qty-row">
                  <input
                    type="number"
                    min={1}
                    max={10}
                    disabled={!p.available || !canEditCart}
                    value={quantities[p.id] ?? "1"}
                    onChange={(ev) =>
                      setQuantities((prev) => ({ ...prev, [p.id]: ev.target.value }))
                    }
                  />
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={!p.available || !canEditCart}
                    onClick={() => {
                      const raw = quantities[p.id] ?? "1";
                      const q = Math.max(1, Math.min(10, Number.parseInt(raw, 10) || 1));
                      void run(() => addToCart(userId, p.id, q));
                    }}
                  >
                    Add to cart
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="panel">
          <div className="panel-head">
            <h2>Your order</h2>
            <button type="button" className="btn-ghost" onClick={() => void refresh()}>
              Refresh
            </button>
          </div>

          {!session?.cart.items.length ? (
            <p className="empty-hint">Cart is empty. Add items while status is Draft or Cart active.</p>
          ) : (
            <ul className="line-items">
              {session.cart.items.map((item) => (
                <li key={item.product_id}>
                  <div className="line-body">
                    <strong>{productNameById.get(item.product_id) ?? "Product"}</strong>
                    <span>
                      {item.quantity} × ${item.unit_price}
                    </span>
                  </div>
                  <div className="line-right">
                    <div className="line-price">${money(item.unit_price, item.quantity)}</div>
                    <button
                      type="button"
                      className="btn-ghost"
                      disabled={!canEditCart}
                      onClick={() => void run(() => removeFromCart(userId, item.product_id))}
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="total-row">
            <span>Total (server)</span>
            <span className="amt">${session?.order.total_amount ?? "0.00"}</span>
          </div>

          <div className="actions">
            <button
              type="button"
              className="btn-primary"
              disabled={!canStartCheckout}
              onClick={() => void run(() => startCheckout(userId))}
            >
              Start checkout
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={!canConfirm}
              onClick={() => void run(() => confirmOrder(userId), "✓")}
            >
              Confirm order
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={!canPay}
              onClick={() => void run(() => payOrder(userId), "✓")}
            >
              Pay now
            </button>
          </div>

          {flash ? <div className={`flash ${flash.kind}`}>{flash.text}</div> : null}
        </aside>
      </div>
    </div>
  );
}
