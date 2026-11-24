import { useMemo, useState } from "react";
import useAlerts from "../hooks/useAlerts";
import AlertCard from "../components/AlertCard";
import { taka } from "../utils/format";

const TABS = ["ALL", "RETURN", "DISCOUNT", "OTHER"];

export default function DailyDigest() {
  const { alerts, loading, error, reload, act } = useAlerts();
  const [tab, setTab] = useState("ALL");

  const counts = useMemo(() => {
    const c = { ALL: alerts.length, RETURN: 0, DISCOUNT: 0, OTHER: 0 };
    alerts.forEach((a) => (c[a.action] = (c[a.action] || 0) + 1));
    return c;
  }, [alerts]);

  const totalLoss = alerts.reduce((s, a) => s + (a.potential_loss || 0), 0);
  const shown = tab === "ALL" ? alerts : alerts.filter((a) => a.action === tab);
  const today = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Today's decisions</h1>
          <p className="muted">{today}</p>
        </div>
        <button className="btn" onClick={reload}>↻ Refresh</button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="summary">
        <div className="card stat"><span>Need decision</span><strong>{counts.ALL}</strong></div>
        <div className="card stat"><span>Return</span><strong>{counts.RETURN}</strong></div>
        <div className="card stat"><span>Discount</span><strong>{counts.DISCOUNT}</strong></div>
        <div className="card stat"><span>Possible loss</span><strong>{taka(totalLoss)}</strong></div>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {t === "ALL" ? "All" : t[0] + t.slice(1).toLowerCase()} ({counts[t] || 0})
          </button>
        ))}
      </div>

      {loading ? (
        <p className="muted center">Loading...</p>
      ) : shown.length === 0 ? (
        <div className="card empty">
          <div className="big">🎉</div>
          <h3>Aj kono decision lagbe na</h3>
          <p className="muted">Shob medicine thik ache. Kal sokale abar dekhbo.</p>
        </div>
      ) : (
        <div className="list">
          {shown.map((a) => (
            <AlertCard key={a.name} alert={a} onAction={act} />
          ))}
        </div>
      )}
    </div>
  );
}
