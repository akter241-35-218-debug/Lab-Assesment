export const taka = (n) => "৳" + Number(n || 0).toLocaleString("en-US");

export function daysUntil(dateStr) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(dateStr);
  d.setHours(0, 0, 0, 0);
  return Math.round((d - today) / 86400000);
}

export function daysLabel(d) {
  if (d === null || d === undefined) return "N/A";
  if (d < 0) return `${Math.abs(d)} days ago`;
  if (d === 0) return "Today";
  return `${d} days`;
}

// "danger" <= 30 days, "warn" <= 90 days, else "ok"
export function expiryStatus(days) {
  if (days <= 30) return "danger";
  if (days <= 90) return "warn";
  return "ok";
}

export function parseCsv(text) {
  const lines = text.replace(/\r/g, "").split("\n").filter((l) => l.trim());
  if (lines.length < 2) return { headers: [], rows: [] };
  const split = (line) => {
    const out = [];
    let cur = "";
    let q = false;
    for (const ch of line) {
      if (ch === '"') q = !q;
      else if (ch === "," && !q) {
        out.push(cur.trim());
        cur = "";
      } else cur += ch;
    }
    out.push(cur.trim());
    return out;
  };
  const headers = split(lines[0]).map((h) => h.toLowerCase());
  const rows = lines.slice(1).map((l) => {
    const v = split(l);
    const o = {};
    headers.forEach((h, i) => (o[h] = v[i] ?? ""));
    return o;
  });
  return { headers, rows };
}
