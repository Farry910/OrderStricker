export type OrderStatus =
  | "DRAFT"
  | "CART_ACTIVE"
  | "CHECKOUT"
  | "CONFIRMED"
  | "PAID"
  | "FULFILLED"
  | "CANCELLED";

export type Product = {
  id: string;
  name: string;
  available: boolean;
  list_price: string;
};

export type CartItem = {
  product_id: string;
  quantity: number;
  unit_price: string;
};

export type Cart = {
  id: string;
  user_id: string;
  items: CartItem[];
};

export type Order = {
  id: string;
  user_id: string;
  status: OrderStatus;
  total_amount: string;
};

export type Session = {
  cart: Cart;
  order: Order;
};

export type ApiResult = {
  ok: boolean;
  message: string;
  data: Record<string, unknown> | null;
};
