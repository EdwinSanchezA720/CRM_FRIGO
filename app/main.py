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
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
