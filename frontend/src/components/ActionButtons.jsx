export default function ActionButtons({ onDone, onSnooze, onDismiss }) {
  return (
    <div className="actions">
      <button className="btn btn-primary" onClick={onDone}>✓ Done</button>
      <button className="btn" onClick={onSnooze}>⏰ Snooze 3 days</button>
      <button className="btn btn-ghost" onClick={onDismiss}>Dismiss</button>
    </div>
  );
}
