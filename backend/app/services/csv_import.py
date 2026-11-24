"""CSV / Excel import for medicines, company policies and sales.

Headers are case-insensitive; common aliases are accepted (see *_ALIASES).
Rows with errors are skipped and reported; good rows are still saved.
"""
import csv
import io
import re
from datetime import date, datetime, timedelta
from typing import Callable, Optional

from openpyxl import load_workbook
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Company, Medicine, Sale
from ..schemas.company import check_discount
from ..schemas.imports import ImportResult, RowError


class ImportFormatError(ValueError):
    """File is unreadable or has missing columns (-> HTTP 400)."""


# ------------------------------------------------------------------ parsing
MEDICINE_ALIASES = {
    "medicine": "name", "medicine_name": "name", "item": "name", "product": "name",
    "qty": "quantity", "stock": "quantity",
    "expiry": "expiry_date", "exp_date": "expiry_date", "expiry_dt": "expiry_date", "exp": "expiry_date",
    "company_name": "company", "supplier": "company", "manufacturer": "company",
    "batch_no": "batch", "batch_number": "batch",
    "cost": "cost_price", "purchase_price": "cost_price", "tp": "cost_price",
    "mrp": "selling_price", "price": "selling_price", "sell_price": "selling_price",
}
COMPANY_ALIASES = {
    "company": "name", "company_name": "name", "supplier": "name",
    "return_window": "return_window_days", "return_policy": "return_window_days",
    "return_days": "return_window_days",
    "discount": "discount_allowed", "discount_allow": "discount_allowed",
    "max_discount": "max_discount_pct", "discount_pct": "max_discount_pct",
    "max_discount_percent": "max_discount_pct",
}
SALE_ALIASES = {
    "medicine": "name", "medicine_name": "name", "item": "name",
    "date": "sale_date", "sold_on": "sale_date",
    "qty": "quantity_sold", "quantity": "quantity_sold", "sold": "quantity_sold",
    "qty_sold": "quantity_sold", "batch_no": "batch",
}

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d")
_MONTH_FORMATS = ("%m/%Y", "%Y-%m", "%b-%Y", "%b %Y", "%b-%y", "%B %Y")  # -> last day of month


def _norm_header(h) -> str:
    return re.sub(r"\s+", "_", str(h or "").strip().lower())


def parse_date(v) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v or "").strip()
    if not s:
        raise ValueError("date khali")
    for f in _DATE_FORMATS:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    for f in _MONTH_FORMATS:  # medicines often only print MM/YYYY
        try:
            d = datetime.strptime(s, f).date()
            nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
            return nxt - timedelta(days=1)
        except ValueError:
            pass
    raise ValueError(f"date bujhte parini: '{s}'")


def _num(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.\-]", "", str(v or "").replace(",", ""))
    if s in ("", "-", "."):
        raise ValueError(f"number bujhte parini: '{v}'")
    return float(s)


def parse_int(v) -> int:
    n = _num(v)
    if n != int(n):
        raise ValueError(f"purno songkha dite hobe: '{v}'")
    return int(n)


def parse_window(v) -> Optional[int]:
    """'90', '90 din', '90 days' -> 90; blank/'no return'/'nei'/0 -> None."""
    s = str(v if v is not None else "").strip().lower()
    m = re.search(r"\d+", s)
    if not m:
        return None
    n = int(m.group())
    return n or None


def parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "ha", "haa", "allowed", "t"}


# ------------------------------------------------------------------ reading
def read_rows(filename: str, content: bytes, aliases: dict, required: set) -> list[tuple[int, dict]]:
    name = (filename or "").lower()
    raw: list[list]
    try:
        if name.endswith((".xlsx", ".xlsm")):
            wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            raw = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
        elif name.endswith((".csv", ".txt")):
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = content.decode("cp1252")
            raw = list(csv.reader(io.StringIO(text)))
        else:
            raise ImportFormatError("Shudhu .csv ba .xlsx file dite hobe")
    except ImportFormatError:
        raise
    except Exception as exc:  # corrupt file
        raise ImportFormatError(f"File poda gelo na: {exc}") from exc

    raw = [r for r in raw if r is not None]
    if not raw:
        raise ImportFormatError("File khali")
    headers = [aliases.get(h, h) for h in map(_norm_header, raw[0])]
    missing = required - set(headers)
    if missing:
        raise ImportFormatError(f"Column nei: {', '.join(sorted(missing))}")

    rows = []
    for i, r in enumerate(raw[1:], start=2):
        if all(c is None or str(c).strip() == "" for c in r):
            continue  # blank line
        rows.append((i, {h: (r[j] if j < len(r) else None) for j, h in enumerate(headers)}))
    return rows


def _run(rows, handler: Callable[[dict], str]) -> ImportResult:
    created = updated = 0
    errors: list[RowError] = []
    for rownum, row in rows:
        try:
            outcome = handler(row)
            created += outcome == "created"
            updated += outcome == "updated"
        except Exception as exc:  # one bad row must not kill the import
            errors.append(RowError(row=rownum, error=str(exc)))
    return ImportResult(
        total_rows=len(rows), created=created, updated=updated, failed=len(errors), errors=errors
    )


def _text(row, key) -> str:
    return str(row.get(key) if row.get(key) is not None else "").strip()


# ------------------------------------------------------------------ companies
def import_companies(db: Session, filename: str, content: bytes) -> ImportResult:
    rows = read_rows(filename, content, COMPANY_ALIASES, {"name"})
    cache = {c.name.lower(): c for c in db.query(Company).all()}

    def handle(row: dict) -> str:
        name = _text(row, "name")
        if not name:
            raise ValueError("company name khali")
        window = parse_window(row.get("return_window_days"))
        allowed = parse_bool(row.get("discount_allowed"))
        pct = _num(row["max_discount_pct"]) if _text(row, "max_discount_pct") else None
        if pct is not None and not 0 <= pct <= 100:
            raise ValueError("max_discount_pct 0-100 er moddhe hote hobe")
        pct = check_discount(allowed, pct)

        c = cache.get(name.lower())
        outcome = "updated"
        if c is None:
            c = Company(name=name)
            db.add(c)
            cache[name.lower()] = c
            outcome = "created"
        c.return_window_days, c.discount_allowed, c.max_discount_pct = window, allowed, pct
        return outcome

    result = _run(rows, handle)
    db.commit()
    return result


# ------------------------------------------------------------------ medicines
def import_medicines(db: Session, filename: str, content: bytes) -> ImportResult:
    required = {"name", "quantity", "expiry_date", "company", "cost_price", "selling_price"}
    rows = read_rows(filename, content, MEDICINE_ALIASES, required)
    companies = {c.name.lower(): c for c in db.query(Company).all()}
    meds = {(m.name.lower(), (m.batch or "").lower()): m for m in db.query(Medicine).all()}

    def handle(row: dict) -> str:
        name, batch, cname = _text(row, "name"), _text(row, "batch"), _text(row, "company")
        if not name:
            raise ValueError("medicine name khali")
        if not cname:
            raise ValueError("company khali")
        qty = parse_int(row.get("quantity"))
        cost, sell = _num(row.get("cost_price")), _num(row.get("selling_price"))
        if qty < 0 or cost < 0 or sell < 0:
            raise ValueError("quantity/price negative hote pare na")
        expiry = parse_date(row.get("expiry_date"))

        company = companies.get(cname.lower())
        if company is None:  # auto-create with no-return/no-discount; fix later in Company Policies
            company = Company(name=cname, discount_allowed=False)
            db.add(company)
            db.flush()
            companies[cname.lower()] = company

        key = (name.lower(), batch.lower())
        m = meds.get(key)
        outcome = "updated"
        if m is None:
            m = Medicine(name=name, batch=batch)
            db.add(m)
            meds[key] = m
            outcome = "created"
        m.quantity, m.expiry_date, m.cost_price, m.selling_price = qty, expiry, cost, sell
        m.company = company
        return outcome

    result = _run(rows, handle)
    db.commit()
    return result


# ------------------------------------------------------------------ sales
def import_sales(db: Session, filename: str, content: bytes, deduct_stock: bool = False) -> ImportResult:
    rows = read_rows(filename, content, SALE_ALIASES, {"name", "sale_date", "quantity_sold"})

    def handle(row: dict) -> str:
        name, batch = _text(row, "name"), _text(row, "batch")
        q = db.query(Medicine).filter(func.lower(Medicine.name) == name.lower())
        if batch:
            q = q.filter(func.lower(Medicine.batch) == batch.lower())
        med = q.order_by(Medicine.expiry_date).first()  # FEFO: earliest expiry first
        if med is None:
            raise ValueError(f"medicine paoa jayni: '{name}' {batch}".strip())
        qty = parse_int(row.get("quantity_sold"))
        if qty <= 0:
            raise ValueError("quantity_sold 0-er beshi hote hobe")
        db.add(Sale(medicine_id=med.id, quantity_sold=qty, sale_date=parse_date(row.get("sale_date"))))
        if deduct_stock:
            med.quantity = max(0, med.quantity - qty)
        db.flush()
        return "created"

    result = _run(rows, handle)
    db.commit()
    return result
