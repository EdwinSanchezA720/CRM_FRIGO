"""
Excepciones personalizadas del sistema.

Java equivalent: Custom Exception classes que extienden RuntimeException

Por qué crear excepciones propias:
    Permiten manejar errores en un solo lugar y devolver respuestas HTTP claras.
    En vez de que el router maneje el error, el service lanza la excepción
    y FastAPI la convierte automáticamente en la respuesta HTTP correcta.

Flujo:
    service.py lanza NotFoundError("Usuario")
    → FastAPI captura HTTPException
    → Devuelve {"detail": "Usuario no encontrado"} con status 404
"""
from fastapi import HTTPException, status


class DomainError(Exception):
    """
    Base para errores de lógica de negocio pura (en domain/engineering/).
    NO es una HTTPException — no sabe que existe HTTP.
    """

    pass


class AuthError(HTTPException):
    """Credenciales inválidas, token expirado o ausente. → HTTP 401"""

    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    """El usuario está autenticado pero no tiene permiso. → HTTP 403"""

    def __init__(self, detail: str = "Acceso denegado — permisos insuficientes"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    """El recurso solicitado no existe en la BD. → HTTP 404"""

    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} no encontrado",
        )


class ConflictError(HTTPException):
    """Viola una restricción de unicidad (ej: email duplicado). → HTTP 409"""

    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
