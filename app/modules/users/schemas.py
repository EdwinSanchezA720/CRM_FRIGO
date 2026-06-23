"""
Users — Schemas (DTOs)   (Java: UserCreateRequest.java, UserResponse.java)

Todos los schemas para crear, actualizar y listar usuarios.
El admin los usa para gestionar quién tiene acceso al sistema y con qué rol.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr

# Tipo que solo acepta estos 4 valores exactos.
# Si el admin envía "gerente" o "superadmin", Pydantic lo rechaza con 422.
RolType = Literal["admin", "tecnico", "ventas", "cliente"]


class UserCreate(BaseModel):
    """
    Datos para crear un nuevo usuario.
    El admin llena este formulario en la pantalla "Agregar usuario".
    """

    nombre: str
    email: EmailStr
    password: str  # se hashea en el service — nunca se guarda en texto plano
    rol: RolType


class UserUpdate(BaseModel):
    """
    Datos para actualizar un usuario existente.
    Todos los campos son opcionales — solo se actualiza lo que se envía.
    Java equivalent: @PatchMapping con RequestBody parcial
    """

    nombre: str | None = None
    rol: RolType | None = None
    activo: bool | None = None  # False = desactivar acceso sin borrar el registro


class UserResponse(BaseModel):
    """
    Datos del usuario que se devuelven en las respuestas de la API.
    NO incluye password_hash — nunca se expone.
    """

    id: UUID
    nombre: str
    email: str
    rol: str
    activo: bool
    fecha_creacion: datetime

    # from_attributes=True permite crear este schema desde un objeto SQLAlchemy (User)
    # Java equivalent: ModelMapper / MapStruct
    model_config = {"from_attributes": True}
