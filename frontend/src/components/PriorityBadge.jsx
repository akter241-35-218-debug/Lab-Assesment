export default function PriorityBadge({ risk, priority }) {
  const level = risk || (priority >= 60 ? "HIGH" : priority >= 40 ? "MEDIUM" : "LOW");
  return (
    <span className={`badge badge-${level.toLowerCase()}`}>
      {level} {priority !== undefined && <small>· {Math.round(priority)}</small>}
    </span>
  );
}
