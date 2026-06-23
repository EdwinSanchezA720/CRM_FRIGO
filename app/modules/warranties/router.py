"""
Garantías — Rutas HTTP   (Java: @RestController)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_warranties():
    return []


@router.post("/")
def create_warranty():
    return {"message": "crear garantía — pendiente"}


@router.get("/{warranty_id}")
def get_warranty(warranty_id: str):
    return {"message": f"garantía {warranty_id} — pendiente"}
