import { useEffect, useState } from "react";
import { api } from "../api/client";
import MedicineTable from "../components/MedicineTable";

const EMPTY = { name: "", quantity: "", expiry_date: "", company: "", cost_price: "" };

export default function MedicineRegister() {
  const [medicines, setMedicines] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [m, c] = await Promise.all([api.getMedicines(), api.getCompanies()]);
      setMedicines(m);
      setCompanies(c);
    } catch (e) {
      setError(e.message);
    }
  };
  useEffect(() => { load(); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.addMedicine({
        ...form,
        quantity: Number(form.quantity),
        cost_price: Number(form.cost_price),
      });
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async (m) => {
    if (!window.confirm(`Delete ${m.name}?`)) return;
    try {
      await api.deleteMedicine(m.id);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const rows = medicines
    .filter((m) => (m.name + m.company).toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => a.expiry_date.localeCompare(b.expiry_date));

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Medicine register</h1>
          <p className="muted">{medicines.length} medicines · expiry onujayi sajano</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "+ Add medicine"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showForm && (
        <form className="card form grid" onSubmit={submit}>
          <label>Name<input value={form.name} onChange={(e) => set("name", e.target.value)} required /></label>
          <label>Quantity<input type="number" min="0" value={form.quantity} onChange={(e) => set("quantity", e.target.value)} required /></label>
          <label>Expiry date<input type="date" value={form.expiry_date} onChange={(e) => set("expiry_date", e.target.value)} required /></label>
          <label>Company
            <select value={form.company} onChange={(e) => set("company", e.target.value)} required>
              <option value="">Select...</option>
              {companies.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
            </select>
          </label>
          <label>Cost price (৳)<input type="number" min="0" value={form.cost_price} onChange={(e) => set("cost_price", e.target.value)} required /></label>
          <div className="row end"><button className="btn btn-primary" type="submit">Save medicine</button></div>
        </form>
      )}

      <input className="search" placeholder="Search by name or company..." value={search}
             onChange={(e) => setSearch(e.target.value)} />
      <div className="card"><MedicineTable rows={rows} onDelete={remove} /></div>
    </div>
  );
}
