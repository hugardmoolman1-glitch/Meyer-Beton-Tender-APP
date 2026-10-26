import type { LineItem, PricedItem, PriceSuggestion, RFQEmail, Supplier, Tender } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Tenders
  listTenders: () => request<Tender[]>("/api/tenders"),
  getTender: (id: number) => request<Tender>(`/api/tenders/${id}`),
  createTender: (payload: Partial<Tender>) =>
    request<Tender>("/api/tenders", { method: "POST", body: JSON.stringify(payload) }),
  updateTender: (id: number, payload: Partial<Tender>) =>
    request<Tender>(`/api/tenders/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTender: (id: number) => request<void>(`/api/tenders/${id}`, { method: "DELETE" }),
  fetchTenders: () =>
    request<{ fetched: number; created: number; skipped: number; not_relevant: number; message?: string }>("/api/tenders/fetch", {
      method: "POST",
    }),

  // Line items
  listLineItems: (tenderId: number) => request<LineItem[]>(`/api/tenders/${tenderId}/line-items`),
  createLineItem: (tenderId: number, payload: Partial<LineItem>) =>
    request<LineItem>(`/api/tenders/${tenderId}/line-items`, { method: "POST", body: JSON.stringify(payload) }),
  updateLineItem: (id: number, payload: Partial<LineItem>) =>
    request<LineItem>(`/api/line-items/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteLineItem: (id: number) => request<void>(`/api/line-items/${id}`, { method: "DELETE" }),
  uploadBoq: (tenderId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ line_items_created: number; items: LineItem[]; warnings: string[] }>(
      `/api/tenders/${tenderId}/boq/upload`,
      { method: "POST", body: form }
    );
  },

  // Pricing
  priceHistory: (description: string) =>
    request<import("./types").PriceHistoryEntry[]>(`/api/pricing/history?description=${encodeURIComponent(description)}`),
  pricedItems: (search?: string) =>
    request<PricedItem[]>(`/api/pricing/items${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  suggestPrice: (lineItemId: number) => request<PriceSuggestion>(`/api/pricing/suggest/${lineItemId}`),

  // Suppliers
  listSuppliers: () => request<Supplier[]>("/api/suppliers"),
  createSupplier: (payload: Partial<Supplier>) =>
    request<Supplier>("/api/suppliers", { method: "POST", body: JSON.stringify(payload) }),
  updateSupplier: (id: number, payload: Partial<Supplier>) =>
    request<Supplier>(`/api/suppliers/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteSupplier: (id: number) => request<void>(`/api/suppliers/${id}`, { method: "DELETE" }),

  // RFQ
  listRfqDrafts: (tenderId: number) => request<RFQEmail[]>(`/api/tenders/${tenderId}/rfq`),
  generateRfqDrafts: (
    tenderId: number,
    payload: { supplier_ids?: number[]; line_item_ids?: number[]; extra_message?: string }
  ) =>
    request<RFQEmail[]>(`/api/tenders/${tenderId}/rfq/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateRfqDraft: (id: number, payload: { subject?: string; body?: string }) =>
    request<RFQEmail>(`/api/rfq/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteRfqDraft: (id: number) => request<void>(`/api/rfq/${id}`, { method: "DELETE" }),
  sendRfqDraft: (id: number) => request<{ sent: boolean; message: string }>(`/api/rfq/${id}/send`, { method: "POST" }),
  sendAllRfqDrafts: (tenderId: number) =>
    request<{ sent: number; failed: number; errors: string[] }>(`/api/tenders/${tenderId}/rfq/send-all`, {
      method: "POST",
    }),
};
