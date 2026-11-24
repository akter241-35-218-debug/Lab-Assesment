"""Email / Telegram / SMS. Every channel is off unless enabled in .env.
send_digest() never raises: it returns a status string per channel."""
import json
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage

from ..config import settings


def format_digest_message(digest: dict, top_n: int = 10) -> str:
    alerts = digest["alerts"]
    lines = [
        f"Pharmacy Shelf - Aj-er digest ({digest['date']})",
        f"{digest['total']} ta medicine-e decision lagbe. Loss at risk: Tk {digest['total_loss_at_risk']:,.0f}",
        "",
    ]
    for i, a in enumerate(alerts[:top_n], 1):
        m = a["medicine"]
        lines.append(f"{i}. [{a['priority']['level'].upper()} {a['priority']['score']:.0f}] "
                     f"{m['name']} ({m['batch'] or '-'}) - {a['action']['type']}")
        lines.append(f"   {a['reason']}")
    if len(alerts) > top_n:
        lines.append(f"... ar {len(alerts) - top_n} ta dashboard-e dekho.")
    return "\n".join(lines)


def format_short(digest: dict) -> str:
    top = digest["alerts"][0]
    return (f"Pharmacy Shelf: aj {digest['total']} ta alert. "
            f"Sob-theke urgent: {top['medicine']['name']} ({top['action']['type']}).")


def _send_email(body: str, subject: str) -> str:
    s = settings
    if not (s.smtp_host and s.email_to and s.email_from):
        return "skipped: SMTP_HOST/EMAIL_FROM/EMAIL_TO set kora nei"
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, s.email_from, ", ".join(s.email_to)
    msg.set_content(body)
    smtp_cls = smtplib.SMTP_SSL if s.smtp_port == 465 else smtplib.SMTP
    with smtp_cls(s.smtp_host, s.smtp_port, timeout=15) as smtp:
        if s.smtp_port != 465:
            smtp.starttls()
        if s.smtp_user:
            smtp.login(s.smtp_user, s.smtp_password)
        smtp.send_message(msg)
    return "sent"


def _send_telegram(body: str) -> str:
    s = settings
    if not (s.telegram_bot_token and s.telegram_chat_id):
        return "skipped: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID set kora nei"
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage",
        data=json.dumps({"chat_id": s.telegram_chat_id, "text": body}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return "sent" if resp.status == 200 else f"failed: HTTP {resp.status}"


def _send_sms(text: str) -> str:
    """Generic HTTP gateway (api_key, senderid, number, message form POST).
    Most BD gateways look like this; adjust the field names for your provider."""
    s = settings
    if not (s.sms_api_url and s.sms_api_key and s.sms_to):
        return "skipped: SMS_API_URL/SMS_API_KEY/SMS_TO set kora nei"
    data = urllib.parse.urlencode({
        "api_key": s.sms_api_key, "senderid": s.sms_sender_id,
        "number": ",".join(s.sms_to), "message": text,
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(s.sms_api_url, data=data), timeout=15) as resp:
        return "sent" if resp.status == 200 else f"failed: HTTP {resp.status}"


def send_digest(digest: dict) -> dict[str, str]:
    if digest["total"] == 0:
        return {"all": "skipped: aj kono alert nei"}

    body = format_digest_message(digest)
    subject = f"Pharmacy Shelf: {digest['total']} ta decision lagbe ({digest['date']})"
    channels = [
        (settings.email_enabled, "email", lambda: _send_email(body, subject)),
        (settings.telegram_enabled, "telegram", lambda: _send_telegram(body)),
        (settings.sms_enabled, "sms", lambda: _send_sms(format_short(digest))),
    ]
    results: dict[str, str] = {}
    for enabled, name, fn in channels:
        if not enabled:
            results[name] = "disabled"
            continue
        try:
            results[name] = fn()
        except Exception as exc:
            results[name] = f"failed: {exc}"
    return results
