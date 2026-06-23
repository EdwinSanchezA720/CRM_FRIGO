"""
Modelo SQLAlchemy para la tabla `users`.

Java equivalent: @Entity User.java + @Table(name = "users")

Este archivo le dice a SQLAlchemy CÓMO mapear la clase User a la tabla
`users` en PostgreSQL (o SQLite en desarrollo).

Roles disponibles:
    admin    → acceso total, gestiona usuarios y configuración
    tecnico  → levantamiento de campo, cálculos térmicos, reportes
    ventas   → clientes, cotizaciones, pipeline comercial
    cliente  → portal externo, solo sus propios proyectos y garantías

IMPORTANTE: Este archivo define la estructura de la BD.
La lógica de negocio (crear, validar, actualizar) va en service.py.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    Tabla: users

    Todos los usuarios del sistema — empleados y clientes externos —
    se guardan en la misma tabla. El campo `rol` determina qué ve cada uno.

    tenant_id agrupa a todos los usuarios de una misma empresa.
    Esto permite que el sistema sea multi-empresa (multi-tenant) en el futuro.
    """

    __tablename__ = "users"

    # Identificador único universal — no es un número secuencial para evitar
    # que alguien enumere /users/1, /users/2, etc.
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # A qué empresa pertenece este usuario.
    # Aunque hoy solo tengamos una empresa, la columna existe desde el inicio.
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    # index=True porque buscamos por email en cada login → debe ser rápido
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Nunca guardar contraseñas en texto plano. Solo el hash bcrypt.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Enum informal: "admin" | "tecnico" | "ventas" | "cliente"
    rol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Soft delete: en vez de borrar el registro, lo desactivamos.
    # Esto preserva el historial (proyectos asociados, auditoría).
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
