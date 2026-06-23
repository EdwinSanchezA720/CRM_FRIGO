"""
Proyectos — Rutas HTTP   (Java: @RestController)
Endpoints: crear, listar, ver, actualizar, entregables.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_projects():
    return []


@router.post("/")
def create_project():
    return {"message": "crear proyecto — pendiente"}


@router.get("/{project_id}")
def get_project(project_id: str):
    return {"message": f"proyecto {project_id} — pendiente"}


@router.get("/{project_id}/deliverables")
def get_deliverables(project_id: str):
    return {"message": f"entregables de {project_id} — pendiente"}
