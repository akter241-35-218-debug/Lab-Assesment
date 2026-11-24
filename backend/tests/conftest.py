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


@pytest.fixture()
def demo(client):
    """The 3 demo medicines from the problem statement, with sales history."""
    def company(name, window, disc, pct):
        r = client.post("/companies", json=dict(name=name, return_window_days=window,
                                                discount_allowed=disc, max_discount_pct=pct))
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def medicine(name, cid, qty, days, cost, daily):
        r = client.post("/medicines", json=dict(
            name=name, batch="B1", quantity=qty, expiry_date=str(TODAY + timedelta(days=days)),
            cost_price=cost, selling_price=cost * 1.3, company_id=cid))
        assert r.status_code == 201, r.text
        mid = r.json()["id"]
        total = int(daily * 30)
        if total:
            client.post("/sales", params={"deduct_stock": False},
                        json=dict(medicine_id=mid, quantity_sold=total, sale_date=str(TODAY - timedelta(days=5))))
        return mid

    ids = {
        "napa": medicine("Napa Extra", company("Beximco", 60, True, 15), 500, 120, 1.2, 20),
        "seclo": medicine("Seclo 20mg", company("Square", 90, True, 10), 300, 98, 5.0, 1.5),
        "cough": medicine("Cough Syrup", company("Local Herbal", None, False, None), 80, 60, 45, 0.3),
    }
    return ids
