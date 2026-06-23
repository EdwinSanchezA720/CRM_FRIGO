"""
Reportes — Schemas (DTOs)   (Java: Request/Response classes)
"""
from pydantic import BaseModel


class ReportResponse(BaseModel):
    project_id: str
    report_type: str
    download_url: str
