"""
Auth — Router   (Java: @RestController @RequestMapping("/auth"))

Endpoints públicos de autenticación. Estos NO requieren token.

POST /auth/login  → recibe email+password, retorna JWT
GET  /auth/me     → requiere token, retorna datos del usuario actual
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import CurrentUserResponse, LoginRequest, TokenResponse
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Recibe email y contraseña. Retorna un Bearer token JWT si son correctos.",
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Java equivalent:
        @PostMapping("/login")
        public TokenResponse login(@RequestBody LoginRequest request) { ... }

    El router NO tiene lógica — solo conecta HTTP con el service.
    """
    service = AuthService(AuthRepository(db))
    return await service.login(request)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Mi perfil",
    description="Retorna los datos del usuario autenticado. Requiere: Authorization: Bearer <token>",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Lee los datos directamente del JWT — sin consultar la BD.
    Los datos vienen del payload que se firmó al hacer login.
    """
    return CurrentUserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        nombre=current_user["nombre"],
        rol=current_user["rol"],
        tenant_id=current_user["tenant_id"],
    )
