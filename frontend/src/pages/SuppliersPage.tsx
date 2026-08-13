import { useEffect, useState } from "react";
import { api } from "../api";
import type { Supplier } from "../types";

const emptyForm = { name: "", email: "", phone: "", categories: "" };

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    setLoading(true);
    api
      .listSuppliers()
      .then(setSuppliers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createSupplier({
        name: form.name,
        email: form.email,
        phone: form.phone || null,
        categories: form.categories || null,
      });
      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Remove this supplier?")) return;
    try {
      await api.deleteSupplier(id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h1>Suppliers</h1>
      <p className="muted">
        Set "Categories" as comma-separated keywords (e.g. <code>cement, aggregate, steel</code>) so RFQs
        auto-match line items to the right suppliers by description. Leave blank to treat a supplier as general
        (matches everything).
      </p>
      <div className="toolbar">
        <button className="secondary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Cancel" : "Add supplier"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <form className="card" onSubmit={handleCreate}>
          <div className="form-grid">
            <input
              placeholder="Name *"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
              type="email"
              placeholder="Email *"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <input
              placeholder="Phone"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
            <input
              className="wide"
              placeholder="Categories (comma-separated)"
              value={form.categories}
              onChange={(e) => setForm({ ...form, categories: e.target.value })}
            />
          </div>
          <button type="submit">Save supplier</button>
        </form>
      )}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : suppliers.length === 0 ? (
        <p className="muted">No suppliers yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Categories</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{s.email}</td>
                <td>{s.phone ?? "-"}</td>
                <td>{s.categories ?? <span className="muted">general</span>}</td>
                <td>
                  <button className="danger" onClick={() => handleDelete(s.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
