import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchProducts, getOrCreateUserId, sendChatMessage } from "./api";
import type { Product } from "./types";

const PAGE_SIZE = 10;
const CHAT_SUMMARY_LINES = 3;
const CHAT_WIDTH_LS = "orderstricker_chat_px";
const CHAT_EXPANDED_LS = "orderstricker_chat_expanded";

type ChatTurn = {
  id: string;
  user: string;
  reply: string;
  error?: string;
};

export default function App() {
  const userId = useMemo(() => getOrCreateUserId(), []);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState<{ kind: "ok" | "bad" | "info"; text: string } | null>(null);
  const [chatText, setChatText] = useState("");
  const [chatSending, setChatSending] = useState(false);

  const [page, setPage] = useState(1);
  const [chatExpanded, setChatExpanded] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem(CHAT_EXPANDED_LS) !== "0";
  });
  const [chatWidthPx, setChatWidthPx] = useState(() => {
    if (typeof window === "undefined") return 320;
    const n = Number.parseInt(localStorage.getItem(CHAT_WIDTH_LS) ?? "", 10);
    return Number.isFinite(n) && n >= 240 && n <= 520 ? n : 320;
  });
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);

  const resizeDragging = useRef(false);
  const lastPointerX = useRef(0);

  const loadProducts = useCallback(async () => {
    setProducts(await fetchProducts(userId));
  }, [userId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await fetchProducts(userId);
        if (!cancelled) setProducts(p);
      } catch (e) {
        if (!cancelled) {
          setFlash({
            kind: "bad",
            text:
              e instanceof Error
                ? e.message
                : "Could not reach the API. Start the backend on port 8000.",
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

  const shown = useMemo(
    () => products.filter((p) => p.available).sort((a, b) => a.name.localeCompare(b.name)),
    [products],
  );
  const unavailable = useMemo(
    () => products.filter((p) => !p.available).sort((a, b) => a.name.localeCompare(b.name)),
    [products],
  );

  const totalPages = Math.max(1, Math.ceil(shown.length / PAGE_SIZE));
  const pageSafe = Math.min(Math.max(1, page), totalPages);
  useEffect(() => {
    setPage((p) => Math.min(Math.max(1, p), totalPages));
  }, [totalPages, shown.length]);

  const pageItems = useMemo(() => {
    const start = (pageSafe - 1) * PAGE_SIZE;
    return shown.slice(start, start + PAGE_SIZE);
  }, [shown, pageSafe]);

  const summaryPreview = useMemo(() => {
    const last = chatTurns[chatTurns.length - 1];
    if (!last) return "Ask for ideas or say reset.";
    const t = last.error ?? last.reply;
    return t.slice(0, 120) + (t.length > 120 ? "…" : "");
  }, [chatTurns]);

  function persistExpanded(next: boolean) {
    setChatExpanded(next);
    localStorage.setItem(CHAT_EXPANDED_LS, next ? "1" : "0");
  }

  useEffect(() => {
    const onMove = (ev: PointerEvent) => {
      if (!resizeDragging.current || !chatExpanded) return;
      ev.preventDefault();
      const dx = lastPointerX.current - ev.clientX;
      lastPointerX.current = ev.clientX;
      setChatWidthPx((prev) => {
        const next = Math.min(520, Math.max(240, Math.round(prev + dx)));
        localStorage.setItem(CHAT_WIDTH_LS, String(next));
        return next;
      });
    };
    const onUp = () => {
      resizeDragging.current = false;
      document.body.classList.remove("chat-resizing");
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [chatExpanded]);

  if (loading) {
    return (
      <div className="shell">
        <p className="loading-msg">Loading showroom…</p>
      </div>
    );
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <div>
            <h1>Stride Market</h1>
            <p className="tagline">Discover by chat — the wall updates to match.</p>
          </div>
        </div>
        <button type="button" className="btn-outline" onClick={() => void loadProducts()}>
          Refresh list
        </button>
      </header>

      <div
        className="spread"
        style={{ ["--chat-w" as string]: chatExpanded ? `${chatWidthPx}px` : "100px" }}
      >
        <main className="show-floor">
          <div className="floor-head">
            <h2>In focus</h2>
            <span className="count-chip">{shown.length} picks</span>
          </div>

          {shown.length === 0 ? (
            <p className="empty-note">Nothing here yet — chat to surface candidates.</p>
          ) : (
            <>
              <div className="pager bar-pager">
                <span className="pager-meta">
                  {shown.length <= PAGE_SIZE ? (
                    <>Showing all {shown.length}</>
                  ) : (
                    <>
                      Page {pageSafe} of {totalPages} · {(pageSafe - 1) * PAGE_SIZE + 1}–
                      {Math.min(pageSafe * PAGE_SIZE, shown.length)} of {shown.length}
                    </>
                  )}
                </span>
                <div className="pager-btns">
                  <button
                    type="button"
                    className="btn-outline btn-sm"
                    disabled={pageSafe <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    className="btn-outline btn-sm"
                    disabled={pageSafe >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="product-wall">
                {pageItems.map((p) => (
                  <article key={p.id} className="tile">
                    <div className="tile-img" aria-hidden />
                    <h3>{p.name}</h3>
                    <p className="tile-price">${p.list_price}</p>
                    <span className="pill-in">In stock</span>
                  </article>
                ))}
              </div>
            </>
          )}

          {unavailable.length > 0 ? (
            <section className="muted-rail">
              <h3>Not on the floor today</h3>
              <ul>
                {unavailable.map((p) => (
                  <li key={p.id}>
                    {p.name} <span className="muted">(${p.list_price})</span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {flash ? (
            <div
              className={`banner ${flash.kind === "info" ? "banner-info" : flash.kind}`}
            >
              {flash.text}
            </div>
          ) : null}
        </main>

        <aside
          className={`chat-rail ${chatExpanded ? "chat-rail-open" : "chat-rail-mini"}`}
          aria-label="Style assistant"
        >
          <button
            type="button"
            className={`resize-edge ${chatExpanded ? "" : "resize-edge-off"}`}
            title={chatExpanded ? "Drag to resize" : ""}
            disabled={!chatExpanded}
            onPointerDown={(ev) => {
              resizeDragging.current = true;
              lastPointerX.current = ev.clientX;
              document.body.classList.add("chat-resizing");
              ev.currentTarget.setPointerCapture(ev.pointerId);
            }}
            aria-hidden
          />

          {!chatExpanded ? (
            <button type="button" className="mini-lane" onClick={() => persistExpanded(true)}>
              <span className="mini-title">Chat</span>
              <span className="mini-blurb" title={summaryPreview}>
                {summaryPreview}
              </span>
              <span className="mini-go" aria-hidden>
                ▶
              </span>
            </button>
          ) : (
            <div className="chat-panel">
              <div className="chat-top">
                <h2>Style assistant</h2>
                <button type="button" className="btn-ghost" onClick={() => persistExpanded(false)}>
                  Hide
                </button>
              </div>

              <div className="summary-box">
                <div className="summary-label">Recent</div>
                {chatTurns.length === 0 ? (
                  <p className="summary-empty">Describe what you want — we reshape the wall.</p>
                ) : (
                  <ul className="summary-rows">
                    {chatTurns.slice(-CHAT_SUMMARY_LINES).map((t) => (
                      <li key={t.id}>
                        <span className="sr-you">You</span>
                        <span className="sr-line">
                          {t.user.slice(0, 70)}
                          {t.user.length > 70 ? "…" : ""}
                        </span>
                        <span className="sr-bot">
                          {t.error ?? (t.reply ? `${t.reply.slice(0, 100)}${t.reply.length > 100 ? "…" : ""}` : "")}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <form
                className="chat-form"
                onSubmit={(ev) => {
                  ev.preventDefault();
                  const t = chatText.trim();
                  if (!t || chatSending) return;
                  setChatSending(true);
                  void (async () => {
                    try {
                      const out = await sendChatMessage(userId, t);
                      setChatText("");
                      setProducts(out.products);
                      const id =
                        typeof crypto !== "undefined" && "randomUUID" in crypto
                          ? crypto.randomUUID()
                          : `t-${Date.now()}`;
                      setChatTurns((prev) => [
                        ...prev.slice(-19),
                        {
                          id,
                          user: t,
                          reply: out.reply,
                          ...(out.error ? { error: out.error } : {}),
                        },
                      ]);
                      if (out.degraded) {
                        setFlash(out.reply ? { kind: "info", text: out.reply } : null);
                      } else if (out.error) {
                        setFlash({ kind: "bad", text: out.error });
                      } else {
                        setFlash({
                          kind: "ok",
                          text: `${out.products.length} on display · ${out.reply.slice(0, 140)}${out.reply.length > 140 ? "…" : ""}`,
                        });
                      }
                      setPage(1);
                    } catch (e) {
                      setFlash({
                        kind: "bad",
                        text: e instanceof Error ? e.message : "Request failed",
                      });
                    } finally {
                      setChatSending(false);
                    }
                  })();
                }}
              >
                <textarea
                  rows={3}
                  className="chat-field"
                  placeholder='Try: “Under $35 and citrus” or “Show everything again”'
                  value={chatText}
                  disabled={chatSending}
                  onChange={(ev) => setChatText(ev.target.value)}
                />
                <button type="submit" className="btn-solid" disabled={chatSending || !chatText.trim()}>
                  {chatSending ? "…" : "Update wall"}
                </button>
              </form>
              <p className="foot-hint">
                Optional: run Ollama for chat refinements — the product wall always works without it.
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
