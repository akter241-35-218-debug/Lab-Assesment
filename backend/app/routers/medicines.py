from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..config import today_local
from ..database import get_db
from ..models import Company, Medicine
from ..schemas.imports import ImportResult
from ..schemas.medicine import MedicineCreate, MedicineOut, MedicineUpdate
from ..services import csv_import

router = APIRouter(prefix="/medicines", tags=["medicines"])


def _get_or_404(db: Session, medicine_id: int) -> Medicine:
    m = db.get(Medicine, medicine_id)
    if m is None:
        raise HTTPException(404, "Medicine paoa jayni")
    return m


def _duplicate(db: Session, name: str, batch: str, exclude_id: Optional[int] = None) -> bool:
    q = db.query(Medicine.id).filter(
        func.lower(Medicine.name) == name.lower(), func.lower(Medicine.batch) == batch.lower()
    )
    if exclude_id:
        q = q.filter(Medicine.id != exclude_id)
    return db.query(q.exists()).scalar()


@router.get("", response_model=list[MedicineOut])
def list_medicines(
    response: Response,
    q: Optional[str] = Query(None, description="name/batch search"),
    company_id: Optional[int] = None,
    expiring_within_days: Optional[int] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Total count is returned in the X-Total-Count header (for pagination)."""
    query = db.query(Medicine)
    if q:
        query = query.filter(Medicine.name.ilike(f"%{q}%") | Medicine.batch.ilike(f"%{q}%"))
    if company_id:
        query = query.filter(Medicine.company_id == company_id)
    if expiring_within_days is not None:
        query = query.filter(Medicine.expiry_date <= today_local() + timedelta(days=expiring_within_days))
    response.headers["X-Total-Count"] = str(query.count())
    return (
        query.options(joinedload(Medicine.company))
        .order_by(Medicine.expiry_date, Medicine.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("", response_model=MedicineOut, status_code=201)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    if db.get(Company, payload.company_id) is None:
        raise HTTPException(404, "Company paoa jayni")
    if _duplicate(db, payload.name, payload.batch):
        raise HTTPException(409, "Ei name + batch-er medicine already ache")
    m = Medicine(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.post("/import", response_model=ImportResult)
def import_medicines(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV/XLSX columns: name, quantity, expiry_date, company, batch, cost_price, selling_price.
    Existing (name + batch) rows are updated, new ones created; unknown companies are auto-created."""
    try:
        return csv_import.import_medicines(db, file.filename, file.file.read())
    except csv_import.ImportFormatError as e:
        raise HTTPException(400, str(e))


@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, medicine_id)


@router.put("/{medicine_id}", response_model=MedicineOut)
def update_medicine(medicine_id: int, payload: MedicineUpdate, db: Session = Depends(get_db)):
    m = _get_or_404(db, medicine_id)
    data = payload.model_dump(exclude_unset=True)
    if "company_id" in data and db.get(Company, data["company_id"]) is None:
        raise HTTPException(404, "Company paoa jayni")
    new_name, new_batch = data.get("name", m.name), data.get("batch", m.batch)
    if ("name" in data or "batch" in data) and _duplicate(db, new_name, new_batch, exclude_id=m.id):
        raise HTTPException(409, "Ei name + batch-er medicine already ache")
    for k, v in data.items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{medicine_id}", status_code=204)
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, medicine_id))
    db.commit()
