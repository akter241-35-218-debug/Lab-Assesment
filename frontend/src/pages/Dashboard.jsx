import { useEffect, useState } from "react";
import { api } from "../api/client";
import useAlerts from "../hooks/useAlerts";
import { daysUntil, taka } from "../utils/format";

function Bar({ label, value, max, tone }) {
  const pct = max ? Math.round((value / max) * 100) : 0;
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track"><div className={`bar-fill bar-${tone}`} style={{ width: `${pct}%` }} /></div>
      <span className="bar-value">{value}</span>
    </div>
  );
}

export default function Dashboard() {
  const { alerts } = useAlerts();
  const [medicines, setMedicines] = useState([]);

  useEffect(() => {
    api.getMedicines().then(setMedicines).catch(() => {});
  }, []);

  const withDays = medicines.map((m) => ({ ...m, days: daysUntil(m.expiry_date) }));
  const within = (n) => withDays.filter((m) => m.days >= 0 && m.days <= n).length;
  const expired = withDays.filter((m) => m.days < 0).length;
  const stockValue = medicines.reduce((s, m) => s + m.quantity * m.cost_price, 0);
  const atRisk = alerts.reduce((s, a) => s + (a.potential_loss || 0), 0);

  const byAction = ["RETURN", "DISCOUNT", "OTHER"].map((a) => ({
    a, n: alerts.filter((x) => x.action === a).length,
  }));
  const maxAction = Math.max(1, ...byAction.map((x) => x.n));

  const buckets = [
    { label: "Expired", value: expired, tone: "danger" },
    { label: "0-30 days", value: within(30), tone: "danger" },
    { label: "31-90 days", value: within(90) - within(30), tone: "warn" },
    { label: "91-180 days", value: within(180) - within(90), tone: "ok" },
  ];
  const maxBucket = Math.max(1, ...buckets.map((b) => b.value));

  return (
    <div>
      <div className="page-head"><div><h1>Dashboard</h1><p className="muted">Shelf-er ekta overview</p></div></div>

      <div className="summary">
        <div className="card stat"><span>Total medicines</span><strong>{medicines.length}</strong></div>
        <div className="card stat"><span>Expiring in 90 days</span><strong>{within(90)}</strong></div>
        <div className="card stat"><span>Stock value</span><strong>{taka(stockValue)}</strong></div>
        <div className="card stat"><span>Loss at risk</span><strong>{taka(atRisk)}</strong></div>
      </div>

      <div className="two-col">
        <div className="card">
          <h3>Pending actions today</h3>
          {byAction.map((x) => (
            <Bar key={x.a} label={x.a[0] + x.a.slice(1).toLowerCase()} value={x.n} max={maxAction}
                 tone={x.a === "RETURN" ? "primary" : x.a === "DISCOUNT" ? "warn" : "danger"} />
          ))}
        </div>
        <div className="card">
          <h3>Expiry timeline</h3>
          {buckets.map((b) => <Bar key={b.label} {...b} max={maxBucket} />)}
        </div>
      </div>
    </div>
  );
}
