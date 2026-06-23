"""
Dependencias de FastAPI para autenticación y control de acceso por rol.

Java equivalent: Spring Security Filter Chain + @PreAuthorize

¿Cómo funciona?
    1. El cliente hace login → recibe un JWT token
    2. En cada request incluye: Authorization: Bearer <token>
    3. FastAPI llama a get_current_user() automáticamente (inyección de dependencias)
    4. get_current_user() valida el token y retorna los datos del usuario
    5. require_role() verifica que el usuario tenga el rol necesario

Uso en un router:
    # Solo usuarios autenticados:
    @router.get("/me")
    def mi_perfil(user = Depends(get_current_user)):
        return user

    # Solo admins:
    @router.get("/users")
    def listar_usuarios(user = Depends(require_role("admin"))):
        return ...

    # Admins O técnicos:
    @router.post("/projects")
    def crear_proyecto(user = Depends(require_role("admin", "tecnico"))):
        return ...
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_access_token

# HTTPBearer extrae el token del header: Authorization: Bearer eyJ...
# Java equivalent: BearerTokenAuthenticationFilter
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Valida el JWT y retorna el payload con los datos del usuario.

    El payload contiene:
        user_id   → UUID del usuario
        email     → correo del usuario
        nombre    → nombre completo
        rol       → "admin" | "tecnico" | "ventas" | "cliente"
        tenant_id → UUID de la empresa a la que pertenece
    """
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise AuthError("Token inválido o expirado. Inicia sesión nuevamente.")
    return payload


def require_role(*roles: str):
    """
    Fábrica de dependencias: genera un verificador para uno o más roles.
    Java equivalent: @PreAuthorize("hasAnyRole('ADMIN', 'TECNICO')")

    Retorna el usuario si su rol está en la lista. Lanza 403 si no.
    """

    async def check_role(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("rol") not in roles:
            allowed = " o ".join(f'"{r}"' for r in roles)
            raise ForbiddenError(f"Se requiere rol {allowed}. Tu rol es: \"{current_user.get('rol')}\"")
        return current_user

    return check_role
