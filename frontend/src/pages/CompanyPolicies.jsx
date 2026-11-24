import { useEffect, useState } from "react";
import { api } from "../api/client";
import CompanyForm from "../components/CompanyForm";

export default function CompanyPolicies() {
  const [companies, setCompanies] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    try { setCompanies(await api.getCompanies()); } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);

  const save = async (c) => {
    try {
      await api.saveCompany(c);
      setEditing(null);
      load();
    } catch (e) { setError(e.message); }
  };

  const remove = async (c) => {
    if (!window.confirm(`Delete ${c.name}?`)) return;
    try { await api.deleteCompany(c.id); load(); } catch (e) { setError(e.message); }
  };

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Company policies</h1>
          <p className="muted">Prottek company-r return o discount niyom</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}

      <div className="two-col">
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Company</th><th>Return window</th><th>Discount</th><th></th></tr></thead>
              <tbody>
                {companies.map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.name}</strong></td>
                    <td>{c.return_window_days > 0 ? `${c.return_window_days} days before expiry` : <span className="pill pill-danger">No return</span>}</td>
                    <td>{c.discount_allowed ? `Up to ${c.max_discount_pct}%` : <span className="pill pill-danger">Not allowed</span>}</td>
                    <td className="nowrap">
                      <button className="btn btn-ghost btn-sm" onClick={() => setEditing(c)}>Edit</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => remove(c)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <CompanyForm key={editing ? editing.id : "new"} initial={editing}
                     onSave={save} onCancel={editing ? () => setEditing(null) : undefined} />
      </div>
    </div>
  );
}
