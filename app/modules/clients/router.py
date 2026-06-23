"""
Clientes — Rutas HTTP   (Java: @RestController)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_clients():
    return []


@router.post("/")
def create_client():
    return {"message": "crear cliente — pendiente"}


@router.get("/{client_id}")
def get_client(client_id: str):
    return {"message": f"cliente {client_id} — pendiente"}
