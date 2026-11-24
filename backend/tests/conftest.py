import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["AUTO_CREATE_TABLES"] = "false"

from datetime import date, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from backend.app import models  # noqa: E402,F401
from backend.app.database import Base, get_db  # noqa: E402
from backend.app.main import app  # noqa: E402

TODAY = date(2026, 11, 24)


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db(session_factory):
    with session_factory() as s:
        yield s


@pytest.fixture()
def client(session_factory, monkeypatch):
    def _get_db():
        with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    # scheduler job opens its own session -> point it at the test DB too
    from backend.app.scheduler import daily_job
    monkeypatch.setattr(daily_job, "SessionLocal", session_factory)
    yield TestClient(app)
    app.dependency_overrides.clear()


def daily_sales_csv(name: str, per_day: float, days: int = 30) -> str:
    """CSV text with one row per day, averaging `per_day` units/day (integers)."""
    rows = ["medicine,batch,sale_date,quantity_sold"]
    for i in range(1, days + 1):
        qty = int((i + 1) * per_day) - int(i * per_day)
        if qty > 0:
            rows.append(f"{name},B1,{TODAY - timedelta(days=i)},{qty}")
    return "\n".join(rows) + "\n"


@pytest.fixture()
def demo(client):
    """The 3 demo medicines of Member 1's demo (daily_alerts._demo), with 30 days of sales:
    Napa = fast seller (no alert), Seclo = RETURN (deadline in 7 days), Cough Syrup = OTHER."""
    def company(name, window, disc, pct):
        r = client.post("/companies", json=dict(name=name, return_window_days=window,
                                                discount_allowed=disc, max_discount_pct=pct))
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def medicine(name, cid, qty, days, cost, sell, daily):
        r = client.post("/medicines", json=dict(
            name=name, batch="B1", quantity=qty, expiry_date=str(TODAY + timedelta(days=days)),
            cost_price=cost, selling_price=sell, company_id=cid))
        assert r.status_code == 201, r.text
        mid = r.json()["id"]
        r = client.post("/sales/import", files={"file": ("s.csv", daily_sales_csv(name, daily))})
        assert r.status_code == 200 and r.json()["failed"] == 0, r.text
        return mid

    return {
        "napa": medicine("Napa Extra", company("Beximco", 90, False, None), 400, 97, 1.2, 1.5, 15),
        "seclo": medicine("Seclo 20mg", company("Square", 90, True, 10), 900, 97, 5, 7, 2),
        "cough": medicine("Cough Syrup", company("LocalCo", None, False, None), 80, 52, 60, 80, 0.2),
    }
