import type { ApiResult, Product, Session } from "./types";

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

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch("/api/products");
  return parse(res);
}

export async function fetchSession(userId: string): Promise<Session> {
  const res = await fetch(`/api/session/${userId}`);
  return parse(res);
}

export async function addToCart(
  userId: string,
  productId: string,
  quantity: number,
): Promise<ApiResult> {
  const res = await fetch(`/api/session/${userId}/cart/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, quantity }),
  });
  return parse(res);
}

export async function removeFromCart(
  userId: string,
  productId: string,
): Promise<ApiResult> {
  const res = await fetch(`/api/session/${userId}/cart/items/${productId}`, {
    method: "DELETE",
  });
  return parse(res);
}

export async function startCheckout(userId: string): Promise<ApiResult> {
  const res = await fetch(`/api/session/${userId}/checkout/start`, {
    method: "POST",
  });
  return parse(res);
}

export async function confirmOrder(userId: string): Promise<ApiResult> {
  const res = await fetch(`/api/session/${userId}/checkout/confirm`, {
    method: "POST",
  });
  return parse(res);
}

export async function payOrder(userId: string): Promise<ApiResult> {
  const res = await fetch(`/api/session/${userId}/checkout/pay`, {
    method: "POST",
  });
  return parse(res);
}
