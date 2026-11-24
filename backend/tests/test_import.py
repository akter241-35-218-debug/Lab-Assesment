import io
from datetime import date

from openpyxl import Workbook

from backend.app.services import csv_import


def upload(client, url, name, content, **params):
    return client.post(url, params=params, files={"file": (name, content)})


def test_company_import_parses_policies(client):
    csv_text = (
        "Company,Return Policy,Discount,Max Discount\n"
        "Square,90 din,yes,10\n"
        "Local Herbal,no return,no,\n"
        "Bad Co,60,yes,\n"           # discount allowed but no max -> error
    )
    r = upload(client, "/companies/import", "c.csv", csv_text).json()
    assert (r["created"], r["failed"]) == (2, 1)
    assert r["errors"][0]["row"] == 4
    cs = {c["name"]: c for c in client.get("/companies").json()}
    assert cs["Square"]["return_window_days"] == 90 and cs["Square"]["max_discount_pct"] == 10
    assert cs["Local Herbal"]["return_window_days"] is None


def test_medicine_import_create_update_and_errors(client):
    csv_text = (
        "name,batch,quantity,expiry_date,company,cost_price,selling_price\n"
        "Napa,B1,100,2027-05-01,Beximco,1.2,1.5\n"
        "Seclo,S1,\"1,200\",12/2027,Square,5,7\n"       # thousands comma + MM/YYYY
        "Bad,B2,abc,2027-05-01,Square,5,7\n"            # bad quantity
        "Bad2,B3,5,not-a-date,Square,5,7\n"             # bad date
        ",B4,5,2027-05-01,Square,5,7\n"                 # no name
    )
    r = upload(client, "/medicines/import", "m.csv", csv_text).json()
    assert (r["total_rows"], r["created"], r["failed"]) == (5, 2, 3)
    assert sorted(e["row"] for e in r["errors"]) == [4, 5, 6]

    meds = {m["name"]: m for m in client.get("/medicines").json()}
    assert meds["Seclo"]["quantity"] == 1200 and meds["Seclo"]["expiry_date"] == "2027-12-31"
    assert meds["Napa"]["company_name"] == "Beximco"  # company auto-created

    # re-import same file -> update, not duplicate
    csv2 = "name,batch,quantity,expiry_date,company,cost_price,selling_price\nNapa,B1,55,2027-05-01,Beximco,1.2,1.5\n"
    r = upload(client, "/medicines/import", "m.csv", csv2).json()
    assert (r["created"], r["updated"]) == (0, 1)
    assert client.get("/medicines", params={"q": "Napa"}).json()[0]["quantity"] == 55


def test_medicine_import_bad_files(client):
    assert upload(client, "/medicines/import", "m.csv", "name,quantity\nx,1\n").status_code == 400  # missing columns
    assert upload(client, "/medicines/import", "m.pdf", "x").status_code == 400
    assert upload(client, "/medicines/import", "m.csv", "").status_code == 400
    assert upload(client, "/medicines/import", "m.xlsx", "not really excel").status_code == 400


def test_medicine_import_excel(client):
    wb = Workbook()
    ws = wb.active
    ws.append(["Name", "Quantity", "Expiry Date", "Company", "Batch", "Cost Price", "Selling Price"])
    ws.append(["Ace", 50, date(2027, 6, 30), "Square", "A1", 1, 2])  # real Excel date cell
    buf = io.BytesIO()
    wb.save(buf)
    r = upload(client, "/medicines/import", "m.xlsx", buf.getvalue()).json()
    assert r["created"] == 1 and r["failed"] == 0
    assert client.get("/medicines").json()[0]["expiry_date"] == "2027-06-30"


def test_sales_import(client):
    upload(client, "/medicines/import", "m.csv",
           "name,batch,quantity,expiry_date,company,cost_price,selling_price\nNapa,B1,100,2027-05-01,Beximco,1,2\n")
    csv_text = "medicine,sale_date,quantity_sold\nNapa,2026-11-20,5\nGhost,2026-11-20,1\nNapa,2026-11-21,0\n"
    r = upload(client, "/sales/import", "s.csv", csv_text, deduct_stock=True).json()
    assert (r["created"], r["failed"]) == (1, 2)
    assert client.get("/medicines").json()[0]["quantity"] == 95


def test_parsers():
    assert csv_import.parse_window("90 days") == 90
    assert csv_import.parse_window("No Return") is None
    assert csv_import.parse_window(0) is None
    assert csv_import.parse_date("31/12/2026") == date(2026, 12, 31)
    assert csv_import.parse_date("02/2028") == date(2028, 2, 29)
    assert csv_import.parse_bool("Yes") and not csv_import.parse_bool("no")
