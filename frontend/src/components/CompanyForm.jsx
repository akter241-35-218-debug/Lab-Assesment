import { useState } from "react";

const EMPTY = { name: "", return_window_days: 90, discount_allowed: true, max_discount_pct: 10 };

export default function CompanyForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial || EMPTY);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    onSave({
      ...form,
      name: form.name.trim(),
      return_window_days: Number(form.return_window_days),
      max_discount_pct: form.discount_allowed ? Number(form.max_discount_pct) : 0,
    });
    if (!initial) setForm(EMPTY);
  };

  return (
    <form className="card form" onSubmit={submit}>
      <h3>{initial ? `Edit ${initial.name}` : "Add company"}</h3>
      <label>Company name
        <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
      </label>
      <label>Return window (expiry-r koto din age porjonto ferot nei)
        <select value={form.return_window_days} onChange={(e) => set("return_window_days", e.target.value)}>
          <option value={0}>No return</option>
          <option value={30}>30 days</option>
          <option value={60}>60 days</option>
          <option value={90}>90 days</option>
          <option value={120}>120 days</option>
        </select>
      </label>
      <label className="check">
        <input type="checkbox" checked={form.discount_allowed}
               onChange={(e) => set("discount_allowed", e.target.checked)} />
        Discount allowed
      </label>
      {form.discount_allowed && (
        <label>Max discount (%)
          <input type="number" min="1" max="100" value={form.max_discount_pct}
                 onChange={(e) => set("max_discount_pct", e.target.value)} />
        </label>
      )}
      <div className="row">
        <button className="btn btn-primary" type="submit">Save</button>
        {onCancel && <button className="btn" type="button" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  );
}
