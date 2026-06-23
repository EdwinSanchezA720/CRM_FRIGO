"""
Reportes — Rutas HTTP   (Java: @RestController)
Memoria de cálculo PDF, cotización PDF, histórico.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/calculation/{project_id}")
def calculation_report(project_id: str):
    return {"message": f"memoria de cálculo {project_id} — pendiente"}


@router.get("/quote/{project_id}")
def quote_report(project_id: str):
    return {"message": f"cotización {project_id} — pendiente"}
