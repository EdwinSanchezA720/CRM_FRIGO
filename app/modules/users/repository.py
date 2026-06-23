"""
Users — Repository   (Java: @Repository UserRepository extends JpaRepository<User, UUID>)

CRUD de usuarios en la base de datos.
No contiene lógica de negocio — solo operaciones de BD.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self, tenant_id: UUID) -> list[User]:
        """
        Lista todos los usuarios de una empresa, del más reciente al más antiguo.
        Java equivalent: findAllByTenantIdOrderByFechaCreacionDesc(tenantId)
        """
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.fecha_creacion.desc())
        )
        return list(result.scalars().all())

    async def find_by_id(self, user_id: UUID) -> User | None:
        """Busca por ID. Retorna None si no existe."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        """Busca por email (para verificar unicidad al crear). Incluye desactivados."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        """
        Guarda un nuevo usuario.
        flush() escribe a la BD dentro de la transacción para obtener el ID,
        sin hacer commit todavía (el commit lo hace get_db() al terminar el request).
        """
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)  # recarga el objeto con los valores generados por la BD
        return user
