"""
Equipos — Rutas HTTP   (Java: @RestController)
Catálogo de equipos de refrigeración: evaporadores, condensadores, etc.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_equipment():
    return []


@router.post("/")
def create_equipment():
    return {"message": "crear equipo — pendiente"}


@router.get("/{equipment_id}")
def get_equipment(equipment_id: str):
    return {"message": f"equipo {equipment_id} — pendiente"}
