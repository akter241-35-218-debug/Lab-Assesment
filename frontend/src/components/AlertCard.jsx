import PriorityBadge from "./PriorityBadge";
import ActionButtons from "./ActionButtons";
import { taka, daysLabel } from "../utils/format";

const ACTION_INFO = {
  RETURN: { title: "Return to company", icon: "↩️", hint: "Company te ferot pathao, deadline shesh hoar age." },
  DISCOUNT: { title: "Sell with discount", icon: "🏷️", hint: "Allowed discount diye drut bikri koro." },
  OTHER: { title: "Other action", icon: "⚠️", hint: "Onno dokane transfer, bundle offer, ba write-off plan koro." },
};

export default function AlertCard({ alert, onAction }) {
  const info = ACTION_INFO[alert.action] || ACTION_INFO.OTHER;
  return (
    <article className={`card alert alert-${alert.action.toLowerCase()}`}>
      <div className="alert-head">
        <div>
          <h3>{alert.name}</h3>
          <p className="muted">
            {alert.company}
            {alert.quantity !== undefined && ` · ${alert.quantity} in stock`}
          </p>
        </div>
        <PriorityBadge risk={alert.risk} priority={alert.priority} />
      </div>

      <div className="action-line">
        <span className="action-chip">{info.icon} {info.title}</span>
        <span className="muted">{info.hint}</span>
      </div>
      <p className="reason">{alert.reason}</p>

      <div className="stats">
        <div><span>Expires in</span><strong>{daysLabel(alert.days_to_expiry)}</strong></div>
        <div>
          <span>Return deadline</span>
          <strong>
            {alert.days_to_return_deadline === null
              ? "No return"
              : alert.days_to_return_deadline < 0
              ? "Closed"
              : daysLabel(alert.days_to_return_deadline)}
          </strong>
        </div>
        <div><span>Possible loss</span><strong>{taka(alert.potential_loss)}</strong></div>
      </div>

      <ActionButtons
        onDone={() => onAction(alert.name, "DONE")}
        onSnooze={() => onAction(alert.name, "SNOOZE", 3)}
        onDismiss={() => onAction(alert.name, "DISMISS")}
      />
    </article>
  );
}
