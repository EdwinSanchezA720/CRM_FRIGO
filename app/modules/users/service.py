"""
Users — Service   (Java: @Service UserService)

Lógica de negocio para gestión de usuarios.
Solo el admin puede usar estos métodos (el router lo verifica).

Responsabilidades:
    - Validar que el email no esté duplicado antes de crear
    - Hashear la contraseña antes de guardar
    - Aplicar cambios parciales (solo los campos que llegaron en el update)
    - Soft delete: desactivar en vez de borrar
"""
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.infrastructure.models.user import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def list_users(self, tenant_id: UUID) -> list[UserResponse]:
        """Lista todos los usuarios de la empresa del admin que hace la petición."""
        users = await self.repo.find_all(tenant_id)
        return [UserResponse.model_validate(u) for u in users]

    async def create_user(
        self, data: UserCreate, tenant_id: UUID, creator_rol: str
    ) -> UserResponse:
        """
        Crea un nuevo usuario.
        Si el creador es "ventas", el usuario queda en "pendiente" hasta que un admin lo apruebe.
        Si el creador es "admin", el usuario queda "activo" de inmediato.
        """
        existing = await self.repo.find_by_email(data.email)
        if existing:
            raise ConflictError(f"El email '{data.email}' ya está registrado en el sistema")

        # Un vendedor no puede auto-aprobar: el usuario nace en "pendiente"
        initial_status = "activo" if creator_rol == "admin" else "pendiente"

        user = User(
            tenant_id=tenant_id,
            nombre=data.nombre,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            rol=data.rol,
            status=initial_status,
        )
        saved = await self.repo.save(user)
        return UserResponse.model_validate(saved)

    async def approve_user(self, user_id: UUID) -> UserResponse:
        """
        Admin aprueba un usuario pendiente: cambia status a "activo".
        Solo tiene efecto si el usuario está en "pendiente".
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuario")
        if user.status != "pendiente":
            raise ConflictError("El usuario no está en estado pendiente")
        user.status = "activo"
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """
        Actualiza solo los campos que llegaron (los que no son None).
        Permite cambiar nombre, rol o activar/desactivar acceso.
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuario")

        if data.nombre is not None:
            user.nombre = data.nombre
        if data.rol is not None:
            user.rol = data.rol
        if data.status is not None:
            user.status = data.status

        return UserResponse.model_validate(user)

    async def deactivate_user(self, user_id: UUID) -> None:
        """
        Soft delete: cambia status a "inactivo" sin borrar el registro.
        Sus proyectos y datos históricos se preservan.
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuario")
        user.status = "inactivo"
