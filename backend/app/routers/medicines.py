"""medicines router [Member 2]"""
from fastapi import APIRouter

router = APIRouter(prefix="/medicines", tags=["medicines"])

@router.get("/")
def list_medicines():
    return []  # TODO
