from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..config import settings, today_local
from ..database import get_db
from ..models import ActionLog, Medicine
from ..schemas.alert import ActionCreate, ActionOut

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("", response_model=ActionOut, status_code=201)
def create_action(payload: ActionCreate, db: Session = Depends(get_db)):
    """Done / Snooze / Dismiss. Frontend alert-er `action` ta recommended_action hishebe pathabe."""
    med = db.get(Medicine, payload.medicine_id)
    if med is None:
        raise HTTPException(404, "Medicine paoa jayni")
    today = payload.today or today_local()

    snooze_until = None
    if payload.action_type == "snooze":
        snooze_until = today + timedelta(days=payload.snooze_days or settings.default_snooze_days)

    log = ActionLog(
        medicine_id=med.id,
        action_type=payload.action_type,
        recommended_action=payload.recommended_action,
        snooze_until=snooze_until,
        loss_amount=round(med.quantity * med.cost_price, 2),
        note=payload.note,
        acted_on=today,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[ActionOut])
def list_actions(
    medicine_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(ActionLog).options(joinedload(ActionLog.medicine))
    if medicine_id:
        q = q.filter(ActionLog.medicine_id == medicine_id)
    return q.order_by(ActionLog.id.desc()).limit(limit).all()


@router.delete("/{action_id}", status_code=204)
def undo_action(action_id: int, db: Session = Depends(get_db)):
    """Bhul click hole undo: alert abar ashbe."""
    log = db.get(ActionLog, action_id)
    if log is None:
        raise HTTPException(404, "Action paoa jayni")
    db.delete(log)
    db.commit()
