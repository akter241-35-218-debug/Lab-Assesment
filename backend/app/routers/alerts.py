"""alerts router [Member 2]"""
from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])

from ..services.digest_service import build_digest

@router.get("/today")
def today_alerts():
    return build_digest()
