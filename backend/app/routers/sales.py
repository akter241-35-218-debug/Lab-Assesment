from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import today_local
from ..database import get_db
from ..models import Medicine, Sale
from ..schemas.imports import ImportResult
from ..schemas.sale import SaleCreate, SaleOut
from ..services import csv_import

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=201)
def record_sale(
    payload: SaleCreate,
    deduct_stock: bool = Query(True, description="medicine quantity theke kombe"),
    db: Session = Depends(get_db),
):
    med = db.get(Medicine, payload.medicine_id)
    if med is None:
        raise HTTPException(404, "Medicine paoa jayni")
    if deduct_stock:
        if med.quantity < payload.quantity_sold:
            raise HTTPException(409, f"Stock-e matro {med.quantity} ta ache")
        med.quantity -= payload.quantity_sold
    sale = Sale(
        medicine_id=med.id,
        quantity_sold=payload.quantity_sold,
        sale_date=payload.sale_date or today_local(),
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("", response_model=list[SaleOut])
def list_sales(
    medicine_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(Sale)
    if medicine_id:
        q = q.filter(Sale.medicine_id == medicine_id)
    if date_from:
        q = q.filter(Sale.sale_date >= date_from)
    if date_to:
        q = q.filter(Sale.sale_date <= date_to)
    return q.order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(limit).all()


@router.post("/import", response_model=ImportResult)
def import_sales(
    file: UploadFile = File(...),
    deduct_stock: bool = Query(False, description="history import-e shadharonoto false"),
    db: Session = Depends(get_db),
):
    """CSV/XLSX columns: medicine (name), batch (optional), sale_date, quantity_sold"""
    try:
        return csv_import.import_sales(db, file.filename, file.file.read(), deduct_stock)
    except csv_import.ImportFormatError as e:
        raise HTTPException(400, str(e))
