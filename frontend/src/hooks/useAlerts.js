import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export default function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setAlerts(await api.getAlertsToday());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // action: "DONE" | "SNOOZE" | "DISMISS"
  const act = useCallback(
    async (name, action, snoozeDays) => {
      const previous = alerts;
      setAlerts((list) => list.filter((a) => a.name !== name)); // card sathe sathe soriye dao
      try {
        await api.sendAction({ medicine_name: name, action, snooze_days: snoozeDays });
      } catch (e) {
        setAlerts(previous);
        setError(e.message);
      }
    },
    [alerts]
  );

  return { alerts, loading, error, reload: load, act };
}
