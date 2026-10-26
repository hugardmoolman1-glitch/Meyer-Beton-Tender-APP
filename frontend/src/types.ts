export type TenderStatus = "open" | "submitted" | "won" | "lost" | "closed";
export type RFQStatus = "draft" | "sent";

export interface Tender {
  id: number;
  source: string;
  external_id: string | null;
  title: string;
  buyer: string | null;
  category: string | null;
  description: string | null;
  province: string | null;
  published_date: string | null;
  closing_date: string | null;
  status: TenderStatus;
  source_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface LineItem {
  id: number;
  tender_id: number;
  item_no: string | null;
  description: string;
  unit: string | null;
  quantity: number | null;
  category: string | null;
  cost_price: number | null;
  selling_price: number | null;
  margin: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  categories: string | null;
  notes: string | null;
  created_at: string;
}

export interface RFQEmail {
  id: number;
  tender_id: number;
  supplier_id: number;
  subject: string;
  body: string;
  status: RFQStatus;
  created_at: string;
  sent_at: string | null;
  line_items: LineItem[];
}

export interface PriceHistoryEntry {
  line_item_id: number;
  tender_id: number;
  tender_title: string;
  description: string;
  unit: string | null;
  cost_price: number | null;
  selling_price: number | null;
  recorded_at: string;
  match_score: number;
}

export interface PricedItem {
  line_item_id: number;
  tender_id: number;
  tender_title: string;
  tender_status: TenderStatus;
  item_no: string | null;
  description: string;
  unit: string | null;
  quantity: number | null;
  cost_price: number | null;
  selling_price: number | null;
  margin_pct: number | null;
  recorded_at: string;
}

export interface PriceSuggestion {
  suggested_cost_price: number | null;
  suggested_selling_price: number | null;
  based_on: PriceHistoryEntry[];
}
