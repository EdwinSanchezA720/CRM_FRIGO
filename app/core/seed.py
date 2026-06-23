"""
Script de datos iniciales (seed).

Crea el primer usuario admin en la BD.
Correr UNA sola vez al iniciar el proyecto.

Comando:
    uv run python -m app.core.seed

¿Qué hace?
    1. Crea las tablas en la BD (si no existen)
    2. Verifica si ya existe el admin (para no duplicarlo)
    3. Crea el admin con email y contraseña por defecto
    4. Imprime el tenant_id generado (guardarlo para configuración)

IMPORTANTE: Cambiar la contraseña después del primer login.
"""
import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.infrastructure.models.user import User

# Credenciales del admin inicial — CAMBIAR después del primer login
ADMIN_EMAIL = "admin@crmfrigo.com"
ADMIN_PASSWORD = "Admin123!"
ADMIN_NOMBRE = "Administrador"


async def seed():
    print("⚙  Iniciando seed...")

    # Paso 1: crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓  Tablas verificadas")

    async with AsyncSessionLocal() as db:
        # Paso 2: verificar si el admin ya existe
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if result.scalar_one_or_none():
            print(f"✓  Admin ya existe: {ADMIN_EMAIL}")
            return

        # Paso 3: crear el admin
        # Todos los usuarios de la misma empresa comparten el mismo tenant_id
        tenant_id = uuid4()

        admin = User(
            tenant_id=tenant_id,
            nombre=ADMIN_NOMBRE,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            rol="admin",
        )
        db.add(admin)
        await db.commit()

    # Paso 4: confirmar
    print(f"✓  Admin creado exitosamente")
    print(f"   Email:     {ADMIN_EMAIL}")
    print(f"   Password:  {ADMIN_PASSWORD}  ← CAMBIAR después del primer login")
    print(f"   tenant_id: {tenant_id}")
    print()
    print("   Ahora corre el servidor:")
    print("   uv run uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(seed())
