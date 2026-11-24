import { daysUntil, expiryStatus, daysLabel } from "../utils/format";

export default function MedicineTable({ rows, onDelete }) {
  if (!rows.length) return <p className="muted center">Kono medicine paoa jayni.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Company</th><th>Qty</th><th>Expiry</th><th>Time left</th><th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => {
            const d = daysUntil(m.expiry_date);
            return (
              <tr key={m.id}>
                <td><strong>{m.name}</strong></td>
                <td>{m.company}</td>
                <td>{m.quantity}</td>
                <td>{m.expiry_date}</td>
                <td><span className={`pill pill-${expiryStatus(d)}`}>{d < 0 ? "Expired" : daysLabel(d)}</span></td>
                <td>
                  {onDelete && (
                    <button className="btn btn-ghost btn-sm" onClick={() => onDelete(m)}>Delete</button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
