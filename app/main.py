"""
Punto de entrada de la aplicación CRM FRIGO.

FastAPI arranca aquí, registra todos los módulos (routers) y gestiona
el ciclo de vida de la aplicación (conectar/desconectar la BD).

Para correr:
    uv run uvicorn app.main:app --reload

URLs importantes:
    http://localhost:8000/login      ← pantalla de login
    http://localhost:8000/docs       ← Swagger UI (equivalente a Spring Boot)
    http://localhost:8000/redoc      ← documentación alternativa
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.database import Base, engine

# ── Rutas absolutas a carpetas de assets ─────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent   # raíz del proyecto (HVAC-Saas/)
STATIC_DIR    = BASE_DIR / "static"       # CSS, JS, imágenes web
TEMPLATES_DIR = BASE_DIR / "templates"    # HTML Jinja2


# ── Lifespan: código que corre al iniciar y al apagar la app ─────────────────
# Java equivalent: @PostConstruct / @PreDestroy
@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ── Instancia principal de FastAPI ───────────────────────────────────────────
app = FastAPI(
    title="CRM FRIGO",
    description="""
CRM de ingeniería para empresas de refrigeración y A/C.

**Roles de acceso:**
- `admin` — gestión de usuarios, catálogo, configuración
- `tecnico` — levantamiento de campo, cálculo térmico, reportes
- `ventas` — clientes, cotizaciones, pipeline
- `cliente` — portal externo (solo sus proyectos y garantías)

**Autenticación:** Bearer JWT — usar `POST /auth/login` para obtener el token.
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# ── Archivos estáticos (CSS, JS, imágenes) ───────────────────────────────────
# Monta la carpeta `static/` en la URL `/static`
# Ej: static/css/login.css → accesible en http://localhost:8000/static/css/login.css
# Java equivalent: src/main/resources/static/
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Motor de templates Jinja2 ────────────────────────────────────────────────
# Lee los archivos HTML de la carpeta templates/
# Java equivalent: Thymeleaf / FreeMarker template engine
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ── Manejadores de error con branding ────────────────────────────────────────
# En Spring Boot sería: @ControllerAdvice + @ExceptionHandler
# Interceptan errores HTTP y errores de servidor antes de devolver la respuesta,
# para mostrar una página con nuestro branding en lugar del texto plano de Starlette.

_ERROR_MESSAGES = {
    404: ("Página no encontrada",   "La URL que buscas no existe o fue movida."),
    403: ("Sin permiso",            "No tienes acceso a esta sección."),
    500: ("Error del servidor",     "Algo salió mal en el servidor. El equipo ya fue notificado."),
}

def _error_response(request: Request, status_code: int) -> HTMLResponse:
    title, message = _ERROR_MESSAGES.get(status_code, ("Error", "Ocurrió un error inesperado."))
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": status_code, "title": title, "message": message},
        status_code=status_code,
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    # Solo devuelve HTML para peticiones de navegador (Accept: text/html).
    # Las llamadas de la API (fetch/curl) siguen recibiendo JSON.
    if "text/html" in request.headers.get("accept", ""):
        return _error_response(request, exc.status_code)
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    if "text/html" in request.headers.get("accept", ""):
        return _error_response(request, 500)
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


# ── Páginas HTML (rutas que devuelven HTML, no JSON) ─────────────────────────

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """
    Sirve la pantalla de login.
    `include_in_schema=False` la oculta del Swagger — no es una API REST.
    """
    return templates.TemplateResponse(request, "login/index.html")


@app.get("/", include_in_schema=False)
async def root():
    """Redirige la raíz al login."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    """
    Pantalla de inicio después del login.
    El JS de base.html verifica el token y redirige a /login si no existe.
    """
    return templates.TemplateResponse(request, "app/dashboard/index.html")


@app.get("/admin/users", response_class=HTMLResponse, include_in_schema=False)
async def users_page(request: Request):
    """
    Módulo de Usuarios & Roles — solo accesible para admins.
    La verificación de rol la hace el JS del lado del cliente,
    y los endpoints de la API la hacen con require_role("admin").
    """
    return templates.TemplateResponse(request, "app/users/index.html")


# ── Routers de API (JSON) ────────────────────────────────────────────────────

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

app.include_router(auth_router,  prefix="/auth",  tags=["🔐 Autenticación"])
app.include_router(users_router, prefix="/users", tags=["👥 Usuarios & Roles"])


# ── Routers pendientes (se activan por fases) ─────────────────────────────────
# from app.modules.projects.router   import router as projects_router
# from app.modules.clients.router    import router as clients_router
# from app.modules.equipment.router  import router as equipment_router
# from app.modules.warranties.router import router as warranties_router
# from app.modules.reports.router    import router as reports_router
