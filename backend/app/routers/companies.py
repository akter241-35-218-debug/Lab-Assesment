from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company, Medicine
from ..schemas.company import CompanyCreate, CompanyOut, CompanyUpdate, check_discount
from ..schemas.imports import ImportResult
from ..services import csv_import

router = APIRouter(prefix="/companies", tags=["companies"])


def _get_or_404(db: Session, company_id: int) -> Company:
    c = db.get(Company, company_id)
    if c is None:
        raise HTTPException(404, "Company paoa jayni")
    return c


def _name_taken(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    q = db.query(Company.id).filter(func.lower(Company.name) == name.lower())
    if exclude_id:
        q = q.filter(Company.id != exclude_id)
    return db.query(q.exists()).scalar()


@router.get("", response_model=list[CompanyOut])
def list_companies(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f"%{q}%"))
    return query.order_by(Company.name).offset(skip).limit(limit).all()


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    if _name_taken(db, payload.name):
        raise HTTPException(409, "Ei naam-er company already ache")
    c = Company(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/import", response_model=ImportResult)
def import_companies(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV/XLSX columns: name, return_window_days, discount_allowed, max_discount_pct"""
    try:
        return csv_import.import_companies(db, file.filename, file.file.read())
    except csv_import.ImportFormatError as e:
        raise HTTPException(400, str(e))


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, company_id)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    c = _get_or_404(db, company_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("name") and _name_taken(db, data["name"], exclude_id=c.id):
        raise HTTPException(409, "Ei naam-er company already ache")
    for k, v in data.items():
        setattr(c, k, v)
    if not c.return_window_days:
        c.return_window_days = None
    try:
        c.max_discount_pct = check_discount(c.discount_allowed, c.max_discount_pct)
    except ValueError as e:
        db.rollback()
        raise HTTPException(422, str(e))
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    c = _get_or_404(db, company_id)
    if db.query(Medicine.id).filter(Medicine.company_id == c.id).first():
        raise HTTPException(409, "Ei company-r medicine ache; age oigulo delete/move koro")
    db.delete(c)
    db.commit()
