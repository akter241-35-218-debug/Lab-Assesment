"""sales router [Member 2]"""
from fastapi import APIRouter

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/")
def list_sales():
    return []  # TODO
