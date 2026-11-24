import { useState } from "react";
import { api } from "../api/client";
import { parseCsv } from "../utils/format";

const REQUIRED = ["name", "quantity", "expiry_date", "company", "cost_price"];
const TEMPLATE = "name,quantity,expiry_date,company,cost_price\nNapa Extra,40,2027-03-31,ACI,20\n";

export default function ImportData() {
  const [file, setFile] = useState(null);
  const [parsed, setParsed] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const onFile = async (e) => {
    const f = e.target.files[0];
    setStatus("");
    setError("");
    setParsed(null);
    if (!f) return;
    setFile(f);
    const result = parseCsv(await f.text());
    const missing = REQUIRED.filter((c) => !result.headers.includes(c));
    if (missing.length) setError(`Column missing: ${missing.join(", ")}`);
    else if (!result.rows.length) setError("File-e kono row nei.");
    else setParsed(result);
  };

  const upload = async () => {
    try {
      const res = await api.importMedicines(file, parsed.rows);
      setStatus(`✓ ${res.imported ?? parsed.rows.length} medicines imported.`);
      setParsed(null);
      setFile(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const downloadTemplate = () => {
    const url = URL.createObjectURL(new Blob([TEMPLATE], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "medicines_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Import medicines</h1>
          <p className="muted">CSV file theke ek sathe onek medicine add koro</p>
        </div>
        <button className="btn" onClick={downloadTemplate}>⬇ Download template</button>
      </div>

      <div className="card form">
        <p className="muted">Required columns: <code>{REQUIRED.join(", ")}</code></p>
        <input type="file" accept=".csv" onChange={onFile} />
        {error && <div className="error">{error}</div>}
        {status && <div className="success">{status}</div>}
      </div>

      {parsed && (
        <div className="card">
          <h3>Preview ({parsed.rows.length} rows)</h3>
          <div className="table-wrap">
            <table>
              <thead><tr>{REQUIRED.map((h) => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {parsed.rows.slice(0, 10).map((r, i) => (
                  <tr key={i}>{REQUIRED.map((h) => <td key={h}>{r[h]}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          {parsed.rows.length > 10 && <p className="muted">...ar {parsed.rows.length - 10} ta row</p>}
          <div className="row end">
            <button className="btn btn-primary" onClick={upload}>Import {parsed.rows.length} rows</button>
          </div>
        </div>
      )}
    </div>
  );
}
