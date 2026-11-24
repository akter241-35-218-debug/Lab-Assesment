"""companies router [Member 2]"""
from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/")
def list_companies():
    return []  # TODO
