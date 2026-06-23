"""
Auth — Repository   (Java: @Repository que extiende JpaRepository)

Solo tiene una responsabilidad: buscar un usuario por email.
La lógica de qué hacer con el usuario está en service.py.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User


class AuthRepository:
    """
    Accede a la tabla `users` para autenticación.
    Recibe la sesión de BD como parámetro (inyección de dependencias manual).
    """

    def __init__(self, db: AsyncSession):
        # La sesión se inyecta desde el router — el repository no la crea.
        # Java equivalent: @Autowired DataSource / EntityManager
        self.db = db

    async def find_by_email(self, email: str) -> User | None:
        """
        Busca un usuario activo por email.
        Retorna None si no existe o está desactivado.

        `scalar_one_or_none()` retorna:
            - el objeto User si hay exactamente un resultado
            - None si no hay resultados
        """
        result = await self.db.execute(
            select(User).where(User.email == email, User.activo == True)
        )
        return result.scalar_one_or_none()
