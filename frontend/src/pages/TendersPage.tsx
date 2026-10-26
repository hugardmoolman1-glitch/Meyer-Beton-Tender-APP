import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Tender } from "../types";

const emptyForm = { title: "", buyer: "", closing_date: "", source_url: "" };

export default function TendersPage() {
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [fetching, setFetching] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    setLoading(true);
    api
      .listTenders()
      .then(setTenders)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleFetch = async () => {
    setFetching(true);
    setError(null);
    setNotice(null);
    try {
      const result = await api.fetchTenders();
      setNotice(
        `Found ${result.fetched} relevant open tenders on eTenders (${result.not_relevant} unrelated ones ignored), ` +
          `added ${result.created} new (${result.skipped} already known).`
      );
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setFetching(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createTender({
        title: form.title,
        buyer: form.buyer || null,
        closing_date: form.closing_date ? new Date(form.closing_date).toISOString() : null,
        source_url: form.source_url || null,
      });
      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h1>Tenders</h1>
      <div className="toolbar">
        <button onClick={handleFetch} disabled={fetching}>
          {fetching ? "Fetching..." : "Fetch from eTenders"}
        </button>
        <button className="secondary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Cancel" : "Add tender manually"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {notice && <div className="notice-banner">{notice}</div>}

      {showForm && (
        <form className="card" onSubmit={handleCreate}>
          <div className="form-grid">
            <input
              placeholder="Title *"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <input
              placeholder="Buyer / client"
              value={form.buyer}
              onChange={(e) => setForm({ ...form, buyer: e.target.value })}
            />
            <input
              type="date"
              placeholder="Closing date"
              value={form.closing_date}
              onChange={(e) => setForm({ ...form, closing_date: e.target.value })}
            />
            <input
              className="wide"
              placeholder="Source URL (optional)"
              value={form.source_url}
              onChange={(e) => setForm({ ...form, source_url: e.target.value })}
            />
          </div>
          <button type="submit">Save tender</button>
        </form>
      )}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : tenders.length === 0 ? (
        <p className="muted">
          No tenders yet. Fetch from eTenders or add one manually to get started.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Buyer</th>
              <th>Closing date</th>
              <th>Source</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tenders.map((t) => (
              <tr key={t.id} className="clickable" onClick={() => navigate(`/tenders/${t.id}`)}>
                <td>{t.title}</td>
                <td>{t.buyer ?? "-"}</td>
                <td>{t.closing_date ? new Date(t.closing_date).toLocaleDateString() : "-"}</td>
                <td>{t.source}</td>
                <td>
                  <span className={`badge ${t.status}`}>{t.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
