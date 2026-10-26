import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { PricedItem } from "../types";

const money = (v: number | null) => (v == null ? "-" : `R ${v.toLocaleString("en-ZA", { minimumFractionDigits: 2 })}`);

export default function PriceHistoryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<PricedItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = (query?: string) => {
    setLoading(true);
    setError(null);
    api
      .pricedItems(query)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(), []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search);
  };

  return (
    <div>
      <h1>Price History</h1>
      <p className="muted">
        Every cost price (what we paid) and selling price (what we quoted) entered on any tender. Search by
        description to see what similar items went for before - matching is fuzzy, so "Crushed stone 19mm" finds
        "19mm crushed stone".
      </p>
      <form className="toolbar" onSubmit={handleSearch}>
        <input placeholder="Search item description..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <button type="submit">Search</button>
        {search && (
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setSearch("");
              load();
            }}
          >
            Clear
          </button>
        )}
      </form>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No priced line items yet. Enter cost/selling prices on a tender's line items to build history.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Unit</th>
              <th>Cost</th>
              <th>Selling</th>
              <th>Margin</th>
              <th>Tender</th>
              <th>Outcome</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.line_item_id} className="clickable" onClick={() => navigate(`/tenders/${i.tender_id}`)}>
                <td>{i.description}</td>
                <td>{i.unit ?? "-"}</td>
                <td>{money(i.cost_price)}</td>
                <td>{money(i.selling_price)}</td>
                <td>{i.margin_pct == null ? "-" : `${i.margin_pct}%`}</td>
                <td>{i.tender_title}</td>
                <td>
                  <span className={`badge ${i.tender_status}`}>{i.tender_status}</span>
                </td>
                <td>{new Date(i.recorded_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
