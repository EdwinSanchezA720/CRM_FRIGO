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
from uuid import UUID, uuid4

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

    async def create_user(self, data: UserCreate, tenant_id: UUID) -> UserResponse:
        """
        Crea un nuevo usuario.
        Verifica que el email no esté registrado antes de guardar.
        """
        # Verificar unicidad del email (en toda la tabla, no solo por tenant)
        existing = await self.repo.find_by_email(data.email)
        if existing:
            raise ConflictError(f"El email '{data.email}' ya está registrado en el sistema")

        user = User(
            tenant_id=tenant_id,
            nombre=data.nombre,
            email=data.email.lower(),  # normalizar a minúsculas
            password_hash=hash_password(data.password),
            rol=data.rol,
        )
        saved = await self.repo.save(user)
        return UserResponse.model_validate(saved)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """
        Actualiza solo los campos que llegaron (los que no son None).
        Permite cambiar nombre, rol o activar/desactivar acceso.
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuario")

        # Solo modificamos los campos que el cliente envió explícitamente
        if data.nombre is not None:
            user.nombre = data.nombre
        if data.rol is not None:
            user.rol = data.rol
        if data.activo is not None:
            user.activo = data.activo

        return UserResponse.model_validate(user)

    async def deactivate_user(self, user_id: UUID) -> None:
        """
        Soft delete: desactiva el usuario sin borrar su registro.
        Sus proyectos y datos históricos se preservan.
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuario")
        user.activo = False
