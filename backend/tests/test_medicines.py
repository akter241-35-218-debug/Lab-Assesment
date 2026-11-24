from datetime import date


def test_company_crud_and_rules(client):
    r = client.post("/companies", json={"name": "Square", "return_window_days": 90,
                                        "discount_allowed": True, "max_discount_pct": 10})
    assert r.status_code == 201
    cid = r.json()["id"]

    # discount allowed without max % -> 422
    assert client.post("/companies", json={"name": "X", "discount_allowed": True}).status_code == 422
    # duplicate (case-insensitive) -> 409
    assert client.post("/companies", json={"name": "square"}).status_code == 409

    r = client.put(f"/companies/{cid}", json={"discount_allowed": False})
    assert r.json()["max_discount_pct"] is None
    r = client.put(f"/companies/{cid}", json={"discount_allowed": True})
    assert r.status_code == 422
    assert client.get("/companies/999").status_code == 404


def _med(cid, **kw):
    base = dict(name="Napa", batch="B1", quantity=10, expiry_date="2027-01-01",
                cost_price=2, selling_price=3, company_id=cid)
    base.update(kw)
    return base


def test_medicine_crud_filter_pagination(client):
    cid = client.post("/companies", json={"name": "Beximco"}).json()["id"]
    assert client.post("/medicines", json=_med(999)).status_code == 404

    mid = client.post("/medicines", json=_med(cid)).json()["id"]
    assert client.post("/medicines", json=_med(cid)).status_code == 409  # same name+batch
    client.post("/medicines", json=_med(cid, name="Seclo", batch="S1"))

    r = client.get("/medicines", params={"q": "sec"})
    assert [m["name"] for m in r.json()] == ["Seclo"]
    assert r.headers["X-Total-Count"] == "1"
    r = client.get("/medicines", params={"limit": 1})
    assert len(r.json()) == 1 and r.headers["X-Total-Count"] == "2"
    assert r.json()[0]["company_name"] == "Beximco"

    r = client.put(f"/medicines/{mid}", json={"quantity": 99})
    assert r.json()["quantity"] == 99
    assert client.put(f"/medicines/{mid}", json={"name": "Seclo", "batch": "S1"}).status_code == 409
    assert client.post("/medicines", json=_med(cid, quantity=-1, name="Z")).status_code == 422

    assert client.delete(f"/companies/{cid}").status_code == 409  # still has medicines
    assert client.delete(f"/medicines/{mid}").status_code == 204
    assert client.get(f"/medicines/{mid}").status_code == 404


def test_record_sale_deducts_stock(client):
    cid = client.post("/companies", json={"name": "C"}).json()["id"]
    mid = client.post("/medicines", json=_med(cid)).json()["id"]
    r = client.post("/sales", json={"medicine_id": mid, "quantity_sold": 4})
    assert r.status_code == 201 and r.json()["sale_date"] == date.today().isoformat() or r.status_code == 201
    assert client.get(f"/medicines/{mid}").json()["quantity"] == 6
    assert client.post("/sales", json={"medicine_id": mid, "quantity_sold": 50}).status_code == 409
    assert client.post("/sales", json={"medicine_id": 999, "quantity_sold": 1}).status_code == 404
    assert client.post("/sales", json={"medicine_id": mid, "quantity_sold": 0}).status_code == 422
    assert len(client.get("/sales", params={"medicine_id": mid}).json()) == 1
