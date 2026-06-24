"""
Users — Router   (Java: @RestController @RequestMapping("/users"))

Endpoints para gestión de usuarios. TODOS requieren rol "admin".

GET    /users/         → listar todos los usuarios de la empresa
POST   /users/         → crear nuevo usuario
PUT    /users/{id}     → actualizar nombre, rol o estado activo
DELETE /users/{id}     → desactivar usuario (soft delete)

¿Por qué soft delete y no borrar?
    Un usuario que creó proyectos no puede desaparecer de la BD —
    los proyectos quedan huérfanos. En su lugar, activo=False
    impide el login sin perder la trazabilidad.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Función auxiliar que construye el service con su repository.
    Java equivalent: @Autowired UserService — aquí lo hacemos manual.
    """
    return UserService(UserRepository(db))


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    description="Lista todos los usuarios de la empresa. Admins y ventas.",
)
async def list_users(
    current_user: dict = Depends(require_role("admin", "ventas")),
    service: UserService = Depends(_get_service),
):
    tenant_id = UUID(current_user["tenant_id"])
    return await service.list_users(tenant_id)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Crear usuario",
    description="Admin crea usuarios activos. Ventas crea usuarios en estado 'pendiente' que requieren aprobación.",
)
async def create_user(
    data: UserCreate,
    current_user: dict = Depends(require_role("admin", "ventas")),
    service: UserService = Depends(_get_service),
):
    tenant_id = UUID(current_user["tenant_id"])
    return await service.create_user(data, tenant_id, creator_rol=current_user["rol"])


@router.post(
    "/{user_id}/approve",
    response_model=UserResponse,
    summary="Aprobar usuario pendiente",
    description="Cambia el status de 'pendiente' a 'activo'. Solo admins.",
)
async def approve_user(
    user_id: UUID,
    _: dict = Depends(require_role("admin")),
    service: UserService = Depends(_get_service),
):
    return await service.approve_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Cambia nombre o rol. Solo admins.",
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    _: dict = Depends(require_role("admin")),
    service: UserService = Depends(_get_service),
):
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Desactivar usuario",
    description="Desactiva el acceso del usuario (soft delete). Solo admins.",
)
async def deactivate_user(
    user_id: UUID,
    _: dict = Depends(require_role("admin")),
    service: UserService = Depends(_get_service),
):
    await service.deactivate_user(user_id)
