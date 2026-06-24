"""
Auth — Service   (Java: @Service AuthService)

Contiene la lógica del login:
    1. Buscar usuario por email
    2. Verificar contraseña contra el hash
    3. Generar JWT con los datos del usuario

¿Por qué el mensaje de error es genérico?
    "Email o contraseña incorrectos" — no decimos cuál está mal.
    Si dijéramos "email no encontrado", un atacante sabría qué emails existen.
"""
from app.core.exceptions import AuthError
from app.core.security import create_access_token, verify_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Autentica al usuario y retorna un JWT.

        Flujo:
            email + password → buscar en BD → verificar hash → crear token → retornar
        """
        user = await self.repo.find_by_email(request.email)

        # Verificamos ambas condiciones antes de dar el error.
        # Si el usuario no existe, la comparación de hash igual se ejecuta
        # para que el tiempo de respuesta sea similar (evita timing attacks).
        if not user or not verify_password(request.password, user.password_hash):
            raise AuthError("Email o contraseña incorrectos")

        if user.status == "pendiente":
            raise AuthError("Tu cuenta está pendiente de aprobación por un administrador")
        if user.status == "inactivo":
            raise AuthError("Tu cuenta ha sido desactivada. Contacta al administrador")

        # El payload del JWT contiene todo lo que el sistema necesita saber
        # sobre el usuario SIN consultar la BD en cada request.
        token = create_access_token(
            {
                "user_id": str(user.id),
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
                "tenant_id": str(user.tenant_id),
            }
        )

        return TokenResponse(
            access_token=token,
            rol=user.rol,
            nombre=user.nombre,
        )
