"""
Proyectos — Schemas (DTOs)   (Java: Request/Response classes)
"""
from pydantic import BaseModel
from datetime import date


class ProjectCreate(BaseModel):
    name: str
    client_id: str
    description: str | None = None
    start_date: date | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    client_id: str
    status: str
