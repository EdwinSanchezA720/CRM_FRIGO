"""
Clientes — Schemas (DTOs)   (Java: Request/Response classes)
"""
from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    company: str | None = None


class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
