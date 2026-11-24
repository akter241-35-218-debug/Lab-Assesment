"""actions router [Member 2]"""
from fastapi import APIRouter

router = APIRouter(prefix="/actions", tags=["actions"])

@router.get("/")
def list_actions():
    return []  # TODO
