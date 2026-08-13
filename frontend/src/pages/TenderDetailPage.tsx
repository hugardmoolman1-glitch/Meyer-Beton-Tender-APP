import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import type { LineItem, PriceSuggestion, RFQEmail, Supplier, Tender, TenderStatus } from "../types";

type Tab = "overview" | "line-items" | "rfq";

const STATUSES: TenderStatus[] = ["open", "submitted", "won", "lost", "closed"];

export default function TenderDetailPage() {
  const { id } = useParams();
  const tenderId = Number(id);
  const [tender, setTender] = useState<Tender | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getTender(tenderId).then(setTender).catch((e) => setError(e.message));
  }, [tenderId]);

  const handleStatusChange = async (status: TenderStatus) => {
    try {
      const updated = await api.updateTender(tenderId, { status });
      setTender(updated);
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (!tender) return error ? <div className="error-banner">{error}</div> : <p className="muted">Loading...</p>;

  return (
    <div>
      <Link className="back-link" to="/">
        &larr; Back to tenders
      </Link>
      <h1>{tender.title}</h1>
      <p className="muted">
        {tender.buyer ?? "No buyer set"}
        {tender.closing_date ? ` · closes ${new Date(tender.closing_date).toLocaleDateString()}` : ""}
        {tender.source_url ? (
          <>
            {" · "}
            <a href={tender.source_url} target="_blank" rel="noreferrer">
              source
            </a>
          </>
        ) : null}
      </p>

      <div className="toolbar">
        <span className="muted">Status:</span>
        <select value={tender.status} onChange={(e) => handleStatusChange(e.target.value as TenderStatus)}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="tabs">
        <button className={tab === "overview" ? "active" : ""} onClick={() => setTab("overview")}>
          Overview
        </button>
        <button className={tab === "line-items" ? "active" : ""} onClick={() => setTab("line-items")}>
          BOQ / Line items
        </button>
        <button className={tab === "rfq" ? "active" : ""} onClick={() => setTab("rfq")}>
          Supplier RFQs
        </button>
      </div>

      {tab === "overview" && (
        <div className="card">
          <p>{tender.description ?? <span className="muted">No description.</span>}</p>
          <p className="muted">
            Category: {tender.category ?? "-"} &middot; Province: {tender.province ?? "-"} &middot; Source:{" "}
            {tender.source}
          </p>
        </div>
      )}

      {tab === "line-items" && <LineItemsTab tenderId={tenderId} />}
      {tab === "rfq" && <RfqTab tenderId={tenderId} />}
    </div>
  );
}

function LineItemsTab({ tenderId }: { tenderId: number }) {
  const [items, setItems] = useState<LineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [suggestions, setSuggestions] = useState<Record<number, PriceSuggestion>>({});

  const load = () => {
    setLoading(true);
    api
      .listLineItems(tenderId)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [tenderId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setWarnings([]);
    try {
      const result = await api.uploadBoq(tenderId, file);
      setWarnings(result.warnings);
      load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleFieldChange = async (item: LineItem, field: "cost_price" | "selling_price", value: string) => {
    const num = value === "" ? null : Number(value);
    const updated = await api.updateLineItem(item.id, { [field]: num });
    setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
  };

  const handleSuggest = async (item: LineItem) => {
    const suggestion = await api.suggestPrice(item.id);
    setSuggestions((prev) => ({ ...prev, [item.id]: suggestion }));
  };

  const applySuggestion = async (item: LineItem) => {
    const s = suggestions[item.id];
    if (!s) return;
    const updated = await api.updateLineItem(item.id, {
      cost_price: s.suggested_cost_price ?? item.cost_price,
      selling_price: s.suggested_selling_price ?? item.selling_price,
    });
    setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)));
  };

  const handleDelete = async (itemId: number) => {
    if (!confirm("Delete this line item?")) return;
    await api.deleteLineItem(itemId);
    load();
  };

  return (
    <div>
      <div className="toolbar">
        <label>
          <input type="file" accept=".xlsx,.xlsm,.pdf,.docx" onChange={handleUpload} disabled={uploading} />
        </label>
        {uploading && <span className="muted">Parsing BOQ...</span>}
      </div>
      <p className="muted">Upload a BOQ (.xlsx, .pdf, or .docx) to auto-extract line items, or add them by hand below.</p>

      {error && <div className="error-banner">{error}</div>}
      {warnings.length > 0 && (
        <div className="notice-banner">
          {warnings.map((w, i) => (
            <div key={i}>{w}</div>
          ))}
        </div>
      )}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : items.length === 0 ? (
        <p className="muted">No line items yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Description</th>
              <th>Unit</th>
              <th>Qty</th>
              <th>Cost price</th>
              <th>Selling price</th>
              <th>Margin</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const suggestion = suggestions[item.id];
              return (
                <tr key={item.id}>
                  <td>{item.item_no ?? "-"}</td>
                  <td>{item.description}</td>
                  <td>{item.unit ?? "-"}</td>
                  <td>{item.quantity ?? "-"}</td>
                  <td>
                    <input
                      className="num"
                      type="number"
                      step="0.01"
                      defaultValue={item.cost_price ?? ""}
                      onBlur={(e) => handleFieldChange(item, "cost_price", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="num"
                      type="number"
                      step="0.01"
                      defaultValue={item.selling_price ?? ""}
                      onBlur={(e) => handleFieldChange(item, "selling_price", e.target.value)}
                    />
                  </td>
                  <td>{item.margin !== null ? `${item.margin}%` : "-"}</td>
                  <td>
                    <div style={{ display: "flex", gap: "0.4rem", flexDirection: "column" }}>
                      <button className="secondary" onClick={() => handleSuggest(item)}>
                        Suggest from history
                      </button>
                      {suggestion && (
                        <div className="muted" style={{ fontSize: "0.78rem" }}>
                          {suggestion.based_on.length === 0 ? (
                            "No similar past items found."
                          ) : (
                            <>
                              Cost avg: {suggestion.suggested_cost_price ?? "-"}, Selling avg:{" "}
                              {suggestion.suggested_selling_price ?? "-"} (from {suggestion.based_on.length} match
                              {suggestion.based_on.length === 1 ? "" : "es"})
                              <br />
                              <button className="secondary" onClick={() => applySuggestion(item)}>
                                Apply
                              </button>
                            </>
                          )}
                        </div>
                      )}
                      <button className="danger" onClick={() => handleDelete(item.id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function RfqTab({ tenderId }: { tenderId: number }) {
  const [drafts, setDrafts] = useState<RFQEmail[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState<Record<number, { subject: string; body: string }>>({});

  const load = () => {
    api.listRfqDrafts(tenderId).then(setDrafts).catch((e) => setError(e.message));
    api.listSuppliers().then(setSuppliers).catch((e) => setError(e.message));
  };

  useEffect(load, [tenderId]);

  const toggleSupplier = (id: number) => {
    setSelectedSuppliers((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setNotice(null);
    try {
      const created = await api.generateRfqDrafts(tenderId, {
        supplier_ids: selectedSuppliers.length > 0 ? selectedSuppliers : undefined,
      });
      setNotice(`Generated ${created.length} draft RFQ email(s). Review and send below.`);
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const startEdit = (draft: RFQEmail) => {
    setEditing((prev) => ({ ...prev, [draft.id]: { subject: draft.subject, body: draft.body } }));
  };

  const saveEdit = async (draft: RFQEmail) => {
    const edit = editing[draft.id];
    if (!edit) return;
    const updated = await api.updateRfqDraft(draft.id, edit);
    setDrafts((prev) => prev.map((d) => (d.id === draft.id ? updated : d)));
    setEditing((prev) => {
      const next = { ...prev };
      delete next[draft.id];
      return next;
    });
  };

  const handleSend = async (draft: RFQEmail) => {
    setError(null);
    setNotice(null);
    try {
      const result = await api.sendRfqDraft(draft.id);
      setNotice(result.message);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (draftId: number) => {
    if (!confirm("Delete this draft?")) return;
    await api.deleteRfqDraft(draftId);
    load();
  };

  const supplierName = (id: number) => suppliers.find((s) => s.id === id)?.name ?? `#${id}`;

  return (
    <div>
      <div className="card">
        <p className="muted">
          Select suppliers to send to, or leave none selected to auto-match suppliers by category against every
          line item. This only creates <strong>drafts</strong> - nothing is emailed until you review and hit Send.
        </p>
        <div className="toolbar" style={{ flexWrap: "wrap" }}>
          {suppliers.map((s) => (
            <label key={s.id} style={{ display: "flex", gap: "0.3rem", alignItems: "center" }}>
              <input
                type="checkbox"
                checked={selectedSuppliers.includes(s.id)}
                onChange={() => toggleSupplier(s.id)}
              />
              {s.name}
            </label>
          ))}
        </div>
        <button onClick={handleGenerate} disabled={generating}>
          {generating ? "Generating..." : "Generate RFQ draft(s)"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {notice && <div className="notice-banner">{notice}</div>}

      {drafts.length === 0 ? (
        <p className="muted">No RFQ drafts yet.</p>
      ) : (
        drafts.map((draft) => {
          const edit = editing[draft.id];
          return (
            <div className="card" key={draft.id}>
              <div className="toolbar" style={{ justifyContent: "space-between" }}>
                <div>
                  <strong>{supplierName(draft.supplier_id)}</strong>{" "}
                  <span className={`badge ${draft.status}`}>{draft.status}</span>
                </div>
                <div className="toolbar">
                  {draft.status === "draft" && !edit && (
                    <button className="secondary" onClick={() => startEdit(draft)}>
                      Edit
                    </button>
                  )}
                  {draft.status === "draft" && (
                    <button onClick={() => handleSend(draft)}>Send</button>
                  )}
                  {draft.status === "draft" && (
                    <button className="danger" onClick={() => handleDelete(draft.id)}>
                      Delete
                    </button>
                  )}
                </div>
              </div>

              {edit ? (
                <>
                  <input
                    className="wide"
                    style={{ width: "100%", marginBottom: "0.5rem" }}
                    value={edit.subject}
                    onChange={(e) => setEditing((prev) => ({ ...prev, [draft.id]: { ...edit, subject: e.target.value } }))}
                  />
                  <textarea
                    className="rfq-body"
                    value={edit.body}
                    onChange={(e) => setEditing((prev) => ({ ...prev, [draft.id]: { ...edit, body: e.target.value } }))}
                  />
                  <div className="toolbar">
                    <button onClick={() => saveEdit(draft)}>Save</button>
                    <button
                      className="secondary"
                      onClick={() =>
                        setEditing((prev) => {
                          const next = { ...prev };
                          delete next[draft.id];
                          return next;
                        })
                      }
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p>
                    <strong>{draft.subject}</strong>
                  </p>
                  <pre className="rfq-body">{draft.body}</pre>
                </>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
