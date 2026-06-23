"""
Garantías — Schemas (DTOs)   (Java: Request/Response classes)
"""
from pydantic import BaseModel
from datetime import date


class WarrantyCreate(BaseModel):
    equipment_id: str
    project_id: str
    start_date: date
    end_date: date


class WarrantyResponse(BaseModel):
    id: str
    equipment_id: str
    project_id: str
    start_date: date
    end_date: date
