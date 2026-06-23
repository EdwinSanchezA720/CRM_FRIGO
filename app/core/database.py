"""
Conexión a la base de datos con SQLAlchemy asíncrono.

Java equivalent: DataSource + EntityManagerFactory (Spring Data JPA)

¿Por qué async?
    FastAPI es un servidor asíncrono. Si hacemos consultas síncronas a la BD,
    el servidor se bloquea mientras espera la respuesta. Con async, puede
    atender otras requests mientras espera — como tener varios empleados
    en vez de uno que hace todo en secuencia.

Configuración por entorno:
    Desarrollo → SQLite (archivo local, sin Docker, sin instalación)
    Producción  → PostgreSQL (cambiar DATABASE_URL en .env)
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Motor de BD ──────────────────────────────────────────────────────────────
# Java equivalent: DataSource bean
# echo=True imprime el SQL generado en consola (útil para depurar en desarrollo)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # SQLite necesita este argumento extra para funcionar con async
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# ── Fábrica de sesiones ──────────────────────────────────────────────────────
# Java equivalent: EntityManager / Session
# Cada request HTTP obtiene su propia sesión — aislamiento entre requests
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # los objetos siguen accesibles después del commit
)


# ── Base declarativa ─────────────────────────────────────────────────────────
# Todos los modelos SQLAlchemy heredan de esta clase.
# Java equivalent: @Entity base class
class Base(DeclarativeBase):
    pass


# ── Dependency de FastAPI ────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    Abre una sesión de BD, la entrega al endpoint, y la cierra al terminar.
    Si ocurre un error hace rollback automático.

    Java equivalent: @Transactional scope por request

    Uso en un router:
        async def mi_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
