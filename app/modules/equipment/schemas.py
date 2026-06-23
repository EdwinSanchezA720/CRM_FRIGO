"""
Equipos — Schemas (DTOs)   (Java: Request/Response classes)
"""
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    model: str
    brand: str
    capacity_btuh: float
    refrigerant: str | None = None


class EquipmentResponse(BaseModel):
    id: str
    model: str
    brand: str
    capacity_btuh: float
