export type Product = {
  id: string;
  name: string;
  available: boolean;
  list_price: string;
};

export type ChatResponse = {
  reply: string;
  error: string | null;
  degraded: boolean;
  products: Product[];
};
