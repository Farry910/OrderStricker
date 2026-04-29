import type { ChatResponse, Product } from "./types";

function uid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const USER_KEY = "orderstricker_user_id";

export function getOrCreateUserId(): string {
  let id = localStorage.getItem(USER_KEY);
  if (!id) {
    id = uid();
    localStorage.setItem(USER_KEY, id);
  }
  return id;
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

/** Candidate products for this shopper (defaults to full catalog server-side until chat narrows). */
export async function fetchProducts(userId: string): Promise<Product[]> {
  const res = await fetch(`/api/products?user_id=${encodeURIComponent(userId)}`);
  return parse(res);
}

export async function sendChatMessage(userId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`/api/session/${userId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return parse(res);
}
