from datetime import timedelta

from backend.app.services import notification
from backend.tests.conftest import TODAY


def digest(client, **params):
    r = client.get("/alerts/today", params={"today": str(TODAY), **params})
    assert r.status_code == 200, r.text
    return r.json()


def by_name(d):
    return {a["medicine"]["name"]: a for a in d["alerts"]}


def test_problem_statement_scenario(client, demo):
    d = digest(client)
    alerts = by_name(d)
    assert "Napa Extra" not in alerts                              # fast seller -> no alert
    seclo = alerts["Seclo 20mg"]
    assert seclo["action"]["type"] == "RETURN"                     # deadline in 7 days
    assert seclo["action"]["return_deadline_in_days"] == 7
    assert seclo["risk"]["days_to_return_deadline"] == 7
    assert alerts["Cough Syrup"]["action"]["type"] == "OTHER"      # no return, no discount
    assert alerts["Cough Syrup"]["action"]["suggestions"]
    assert d["total"] == 2 and all(a["reason"] for a in d["alerts"])
    assert d["total_loss_at_risk"] == round(sum(a["risk"]["expected_loss"] for a in d["alerts"]), 2)
    assert d["total_loss_at_risk"] > 0
    assert {a["priority"]["level"] for a in d["alerts"]} <= {"HIGH", "MEDIUM", "LOW"}
    scores = [a["priority"]["score"] for a in d["alerts"]]
    assert scores == sorted(scores, reverse=True)


def test_medicine_without_sales_is_not_selling(client):
    cid = client.post("/companies", json={"name": "C"}).json()["id"]
    client.post("/medicines", json=dict(name="Dead Stock", batch="x", quantity=100, cost_price=20,
                                        selling_price=30, expiry_date=str(TODAY + timedelta(days=30)),
                                        company_id=cid))
    a = by_name(digest(client))["Dead Stock"]
    assert a["risk"]["days_of_stock_left"] is None and a["risk"]["avg_daily_sales"] == 0


def test_expired_stock_always_alerts_high(client):
    cid = client.post("/companies", json={"name": "C"}).json()["id"]
    client.post("/medicines", json=dict(name="Old", batch="x", quantity=10, cost_price=30, selling_price=40,
                                        expiry_date=str(TODAY - timedelta(days=5)), company_id=cid))
    a = by_name(digest(client))["Old"]
    assert a["risk"]["expired"] and a["action"]["type"] == "OTHER" and a["priority"]["level"] == "HIGH"


def test_done_hides_alert_and_undo_restores(client, demo):
    seclo = demo["seclo"]
    r = client.post("/actions", json=dict(medicine_id=seclo, action_type="done",
                                          recommended_action="RETURN", today=str(TODAY)))
    assert r.status_code == 201 and r.json()["loss_amount"] == 4500   # 900 x 5
    d = digest(client)
    assert "Seclo 20mg" not in by_name(d) and d["suppressed"] == 1
    assert "Seclo 20mg" in by_name(digest(client, include_suppressed=True))

    assert client.delete(f"/actions/{r.json()['id']}").status_code == 204
    assert "Seclo 20mg" in by_name(digest(client))


def test_snooze_comes_back_after_N_days(client, demo):
    cough = demo["cough"]
    client.post("/actions", json=dict(medicine_id=cough, action_type="snooze",
                                      recommended_action="OTHER", snooze_days=3, today=str(TODAY)))
    assert "Cough Syrup" not in by_name(digest(client))
    day2 = client.get("/alerts/today", params={"today": str(TODAY + timedelta(days=2))}).json()
    assert "Cough Syrup" not in by_name(day2)
    day3 = client.get("/alerts/today", params={"today": str(TODAY + timedelta(days=3))}).json()
    assert "Cough Syrup" in by_name(day3)


def test_dismiss_expires_and_escalation_reappears(client, demo):
    cough = demo["cough"]
    client.post("/actions", json=dict(medicine_id=cough, action_type="dismiss",
                                      recommended_action="OTHER", today=str(TODAY)))
    assert "Cough Syrup" not in by_name(digest(client))
    # after DISMISS_DAYS (30) it is shown again
    later = client.get("/alerts/today", params={"today": str(TODAY + timedelta(days=31))}).json()
    assert "Cough Syrup" in by_name(later)

    # escalation: Seclo marked done for RETURN; once the return deadline has passed the
    # action is no longer RETURN -> a *new* decision -> the alert shows again
    client.post("/actions", json=dict(medicine_id=demo["seclo"], action_type="done",
                                      recommended_action="RETURN", today=str(TODAY)))
    later = client.get("/alerts/today", params={"today": str(TODAY + timedelta(days=85))}).json()
    assert by_name(later)["Seclo 20mg"]["action"]["type"] in ("DISCOUNT", "OTHER")


def test_action_validation(client, demo):
    assert client.post("/actions", json=dict(medicine_id=999, action_type="done")).status_code == 404
    assert client.post("/actions", json=dict(medicine_id=demo["napa"], action_type="bogus")).status_code == 422


def test_dashboard_and_loss_saved(client, demo):
    client.post("/actions", json=dict(medicine_id=demo["seclo"], action_type="done",
                                      recommended_action="RETURN", today=str(TODAY)))
    client.post("/actions", json=dict(medicine_id=demo["cough"], action_type="done",
                                      recommended_action="OTHER", today=str(TODAY)))
    s = client.get("/dashboard/summary", params={"today": str(TODAY)}).json()
    assert s["total_medicines"] == 3
    assert s["actions_this_month"]["done"] == 2
    assert s["loss_saved_this_month"] == 4500          # only RETURN/DISCOUNT count as saved
    assert (s["expiring_60_days"], s["expiring_90_days"]) == (1, 1)  # only Cough Syrup (+52d)

    rep = client.get("/dashboard/loss-saved", params={"month": "2026-11"}).json()
    assert rep["total_loss_saved"] == 4500 and rep["by_action"] == {"RETURN": 4500.0}
    assert client.get("/dashboard/loss-saved", params={"month": "2026-13"}).status_code == 422
    assert client.get("/dashboard/loss-saved", params={"month": "bad"}).status_code == 422


def test_notification_message_and_run_job(client, demo):
    d = digest(client)
    msg = notification.format_digest_message(d)
    assert "Seclo 20mg" in msg and "- RETURN" in msg and "2 ta medicine" in msg

    r = client.post("/alerts/run-job", params={"today": str(TODAY)}).json()
    assert r["total"] == 2
    assert r["notifications"]["email"] == "disabled"   # channels are off by default
    empty = notification.send_digest({"total": 0, "alerts": [], "date": TODAY, "total_loss_at_risk": 0})
    assert "skipped" in empty["all"]


def test_notification_failure_does_not_raise(monkeypatch, client, demo):
    monkeypatch.setattr(notification.settings, "telegram_enabled", True)
    monkeypatch.setattr(notification.settings, "telegram_bot_token", "x")
    monkeypatch.setattr(notification.settings, "telegram_chat_id", "1")
    monkeypatch.setattr(notification.urllib.request, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("network down")))
    res = notification.send_digest(digest(client))
    assert res["telegram"].startswith("failed")
