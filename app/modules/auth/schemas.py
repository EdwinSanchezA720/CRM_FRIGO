"""
Auth — Schemas (DTOs)   (Java: LoginRequest.java, TokenResponse.java)

Define qué datos entran y salen en los endpoints de autenticación.
Pydantic valida automáticamente los tipos — si el cliente manda un campo
incorrecto, FastAPI devuelve un error 422 antes de llegar al service.
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    Cuerpo del POST /auth/login.
    EmailStr valida que el formato sea un email válido.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Respuesta exitosa del login.
    El frontend guarda access_token y lo envía en cada request:
        Authorization: Bearer <access_token>
    """

    access_token: str
    token_type: str = "bearer"  # estándar OAuth2
    rol: str  # el frontend lo usa para decidir qué portal mostrar
    nombre: str


class CurrentUserResponse(BaseModel):
    """
    Respuesta del GET /auth/me — datos del usuario autenticado.
    Útil para que el frontend sepa quién está logueado.
    """

    user_id: str
    email: str
    nombre: str
    rol: str
    tenant_id: str
