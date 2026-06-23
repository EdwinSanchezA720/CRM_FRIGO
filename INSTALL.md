# Guía de Instalación — CRM FRIGO

Guía paso a paso para correr el proyecto en una máquina local desde cero.
Tiempo estimado: **15-20 minutos**.

> Si vienes de Java/Spring Boot: `uv` es el equivalente a Maven/Gradle,
> `uvicorn` es el equivalente a Tomcat/Spring Boot embedded server,
> y `alembic` es el equivalente a Flyway/Liquibase.

---

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Clonar el repositorio](#2-clonar-el-repositorio)
3. [Instalar Python 3.12](#3-instalar-python-312)
4. [Instalar uv (gestor de paquetes)](#4-instalar-uv-gestor-de-paquetes)
5. [Instalar dependencias del proyecto](#5-instalar-dependencias-del-proyecto)
6. [Instalar y levantar Docker Desktop](#6-instalar-y-levantar-docker-desktop)
7. [Configurar variables de entorno (.env)](#7-configurar-variables-de-entorno-env)
8. [Levantar la base de datos](#8-levantar-la-base-de-datos)
9. [Aplicar migraciones](#9-aplicar-migraciones)
10. [Cargar datos iniciales](#10-cargar-datos-iniciales)
11. [Correr el servidor](#11-correr-el-servidor)
12. [Verificar que todo funciona](#12-verificar-que-todo-funciona)
13. [Comandos del día a día](#13-comandos-del-día-a-día)
14. [Solución de problemas frecuentes](#14-solución-de-problemas-frecuentes)

---

## 1. Requisitos previos

Antes de empezar, asegúrate de tener:

| Herramienta | Versión mínima | ¿Para qué sirve? |
|---|---|---|
| **Python** | 3.12 | Lenguaje del backend |
| **uv** | cualquiera | Gestor de paquetes (como Maven) |
| **Docker Desktop** | cualquiera | Corre PostgreSQL en un contenedor |
| **Git** | cualquiera | Clonar el repositorio |

Para verificar lo que ya tienes instalado:

```bash
python3 --version     # debe mostrar Python 3.12.x
docker --version      # debe mostrar Docker version 2x.x.x
git --version         # debe mostrar git version 2.x.x
```

---

## 2. Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd HVAC-Saas
```

> Pídele a tu compañero la URL del repositorio en GitHub/GitLab.

---

## 3. Instalar Python 3.12

### macOS

**Opción A — Homebrew (recomendado):**
```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.12
brew install python@3.12

# Verificar
python3.12 --version
```

**Opción B — pyenv (si manejas múltiples versiones de Python):**
```bash
brew install pyenv
pyenv install 3.12.8
pyenv global 3.12.8
python --version
```

### Windows

1. Ir a https://www.python.org/downloads/
2. Descargar **Python 3.12.x** (el instalador `.exe`)
3. En el instalador: ✅ marcar **"Add Python to PATH"** (importante)
4. Completar la instalación
5. Abrir una terminal nueva y verificar:
   ```
   python --version
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
python3.12 --version
```

---

## 4. Instalar uv (gestor de paquetes)

`uv` es como Maven pero para Python: maneja dependencias, versiones y entornos virtuales.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Después de instalar, **cierra y vuelve a abrir la terminal** para que el PATH se actualice.

```bash
uv --version    # debe mostrar: uv 0.x.x
```

### Windows (PowerShell como administrador)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y vuelve a abrir PowerShell, luego verifica:
```
uv --version
```

---

## 5. Instalar dependencias del proyecto

Dentro de la carpeta del proyecto (`HVAC-Saas/`):

```bash
uv sync
```

Este comando:
- Lee `pyproject.toml` (equivalente a `pom.xml`)
- Crea un entorno virtual en `.venv/`
- Descarga e instala todas las dependencias

> La primera vez tarda 1-2 minutos. Las siguientes veces es casi instantáneo.

Verifica que instaló correctamente:
```bash
uv run python -c "import fastapi; print('FastAPI ok')"
```

Debe imprimir: `FastAPI ok`

---

## 6. Instalar y levantar Docker Desktop

Docker corre PostgreSQL en un contenedor aislado — no necesitas instalarlo directamente en tu máquina.

### macOS / Windows

1. Ir a https://www.docker.com/products/docker-desktop/
2. Descargar e instalar **Docker Desktop**
3. Abrir Docker Desktop y esperar a que el ícono en la barra de menú esté en verde (Running)

### Linux

```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose-v2
sudo systemctl start docker
sudo usermod -aG docker $USER   # para correr docker sin sudo
# Cerrar sesión y volver a abrir
```

### Verificar Docker

```bash
docker --version
docker compose version
```

Ambos deben responder sin error.

---

## 7. Configurar variables de entorno (.env)

El archivo `.env` guarda la configuración local (base de datos, claves secretas).
**No se sube al repositorio** (está en `.gitignore`).

Crea el archivo `.env` en la raíz del proyecto:

```bash
# macOS / Linux — crear el archivo
touch .env
```

Abre `.env` con cualquier editor y pega este contenido:

```env
# Base de datos PostgreSQL (contenedor Docker)
DATABASE_URL=postgresql+asyncpg://crmfrigo:crmfrigo123@localhost:5433/hvac_saas

# Clave para firmar los tokens JWT
# En desarrollo puede ser cualquier string. En producción debe ser larga y aleatoria.
SECRET_KEY=dev-secret-key-cambiar-en-produccion

# Modo desarrollo (muestra SQL en la consola)
DEBUG=true
```

> **Nota sobre el puerto 5433:** Usamos 5433 en vez de 5432 porque macOS tiene
> un PostgreSQL local en 5432 que causaría conflicto. Si en tu máquina el 5432
> está libre, puedes dejarlo en 5432 (cambia en `.env` Y en `docker-compose.yml`).

---

## 8. Levantar la base de datos

```bash
docker compose up -d db
```

Este comando:
- Descarga la imagen de PostgreSQL 16 (solo la primera vez, ~200MB)
- Crea el contenedor `crmfrigo_db`
- Crea la base de datos `hvac_saas` con el usuario `crmfrigo`
- Lo deja corriendo en segundo plano (`-d` = detached)

Verificar que está corriendo:
```bash
docker compose ps
```

Debe mostrar:
```
NAME          IMAGE         STATUS
crmfrigo_db   postgres:16   Up X seconds
```

Esperar a que PostgreSQL acepte conexiones (tarda ~5 segundos la primera vez):
```bash
# macOS/Linux — esperar hasta que esté listo
until docker exec crmfrigo_db pg_isready -U crmfrigo > /dev/null 2>&1; do
  echo "Esperando PostgreSQL..."; sleep 2
done
echo "PostgreSQL listo"
```

```powershell
# Windows — simplemente esperar 10 segundos
Start-Sleep -Seconds 10
```

---

## 9. Aplicar migraciones

Las migraciones crean (o actualizan) las tablas en la base de datos.
Equivalente a `flyway migrate` en Java.

```bash
uv run alembic upgrade head
```

Debe mostrar algo como:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 60527d5f623b, create_users_table
```

Verificar que la tabla se creó:
```bash
docker exec crmfrigo_db psql -U crmfrigo -d hvac_saas -c "\dt"
```

Debe mostrar:
```
         List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | crmfrigo
 public | users           | table | crmfrigo
```

---

## 10. Cargar datos iniciales

Crea el primer usuario administrador:

```bash
uv run python -m app.core.seed
```

Debe mostrar:
```
⚙  Iniciando seed...
✓  Tablas verificadas
✓  Admin creado exitosamente
   Email:     admin@crmfrigo.com
   Password:  Admin123!  ← CAMBIAR después del primer login
   tenant_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

> Guarda el `tenant_id` — es el identificador de tu empresa en el sistema.

Si ya corriste el seed antes y el admin ya existe, verás:
```
✓  Admin ya existe
```
Eso es normal, no hay problema.

---

## 11. Correr el servidor

```bash
uv run uvicorn app.main:app --reload
```

- `--reload` reinicia el servidor automáticamente cuando cambias un archivo (como Spring DevTools)
- El servidor queda corriendo en `http://localhost:8000`

Verás en la consola:
```
INFO:     Started server process [XXXXX]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Para **detener** el servidor: `Ctrl + C`

---

## 12. Verificar que todo funciona

### Opción A — Desde el navegador (más fácil)

Abre: **http://localhost:8000/docs**

Verás Swagger UI — la interfaz visual para probar los endpoints.
Es exactamente igual a Swagger UI en Spring Boot.

Para probar el login:
1. Click en `POST /auth/login`
2. Click en **"Try it out"**
3. En el body escribe:
   ```json
   {
     "email": "admin@crmfrigo.com",
     "password": "Admin123!"
   }
   ```
4. Click **"Execute"**
5. Debes recibir un `access_token` en la respuesta

### Opción B — Desde la terminal

```bash
# 1. Login — obtener token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@crmfrigo.com","password":"Admin123!"}'
```

Respuesta esperada:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "rol": "admin",
  "nombre": "Administrador"
}
```

```bash
# 2. Ver mi perfil (reemplazar TOKEN con el access_token de arriba)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN"
```

Respuesta esperada:
```json
{
  "user_id": "...",
  "email": "admin@crmfrigo.com",
  "nombre": "Administrador",
  "rol": "admin",
  "tenant_id": "..."
}
```

### Opción C — Correr los tests

```bash
uv run pytest tests/ -v
```

Deben pasar los **20 tests** del motor de cálculo.

---

## 13. Comandos del día a día

```bash
# ── Servidor ────────────────────────────────────────────────────────────────
uv run uvicorn app.main:app --reload          # iniciar servidor
# Ctrl+C                                       # detener servidor

# ── Base de datos ────────────────────────────────────────────────────────────
docker compose up -d db                        # iniciar PostgreSQL
docker compose stop db                         # pausar PostgreSQL
docker compose down                            # apagar (datos se preservan)
docker compose down -v                         # apagar y BORRAR todos los datos ⚠️

# ── Migraciones ──────────────────────────────────────────────────────────────
uv run alembic upgrade head                    # aplicar migraciones pendientes
uv run alembic revision --autogenerate -m "descripcion"  # nueva migración
uv run alembic history                         # ver historial
uv run alembic downgrade -1                    # revertir última migración

# ── Dependencias ─────────────────────────────────────────────────────────────
uv sync                                        # instalar/actualizar dependencias
uv add nombre-paquete                          # agregar nueva dependencia
uv remove nombre-paquete                       # quitar dependencia

# ── Tests ────────────────────────────────────────────────────────────────────
uv run pytest                                  # todos los tests
uv run pytest tests/unit/engineering -v        # solo motor de cálculo
uv run pytest -k "nombre_test"                 # un test específico

# ── Calidad de código ────────────────────────────────────────────────────────
uv run ruff check .                            # detectar errores de estilo
uv run ruff format .                           # formatear automáticamente
```

---

## 14. Solución de problemas frecuentes

### ❌ `uv: command not found`
El PATH no se actualizó. Cierra y vuelve a abrir la terminal.
Si persiste en macOS: `source ~/.zshrc` o `source ~/.bashrc`

---

### ❌ `role "crmfrigo" does not exist`
El puerto 5432 está siendo tomado por un PostgreSQL local del sistema.
El archivo `.env` usa el puerto **5433**. Verifica que así esté:
```env
DATABASE_URL=postgresql+asyncpg://crmfrigo:crmfrigo123@localhost:5433/hvac_saas
```
Y que `docker-compose.yml` tenga:
```yaml
ports:
  - "5433:5432"
```

---

### ❌ `Cannot connect to the Docker daemon`
Docker Desktop no está corriendo.
- macOS/Windows: abre la app **Docker Desktop** y espera a que el ícono esté verde
- Linux: `sudo systemctl start docker`

---

### ❌ `ModuleNotFoundError` al correr cualquier comando
Las dependencias no están instaladas. Corre:
```bash
uv sync
```

---

### ❌ El servidor arranca pero `/docs` no abre
Verifica que el servidor esté corriendo en el puerto 8000:
```bash
# macOS/Linux
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```
Si el puerto está ocupado, usa otro:
```bash
uv run uvicorn app.main:app --reload --port 8001
# Abre: http://localhost:8001/docs
```

---

### ❌ `alembic upgrade head` falla con error de conexión
PostgreSQL no está corriendo. Asegúrate de:
1. Docker Desktop está abierto y en verde
2. El contenedor está arriba: `docker compose ps`
3. Si no está arriba: `docker compose up -d db`

---

### ❌ Los tests fallan después de cambiar código
Los 20 tests del motor de cálculo no dependen de la BD — deben pasar siempre:
```bash
uv run pytest tests/unit/engineering -v
```
Si fallan, hay un error en `app/domain/engineering/`.

---

## Estructura del proyecto (referencia rápida)

```
HVAC-Saas/
├── .env                    ← configuración local (NO subir a git)
├── docker-compose.yml      ← define el contenedor de PostgreSQL
├── pyproject.toml          ← dependencias (como pom.xml)
├── alembic/                ← migraciones de base de datos (como Flyway)
│   └── versions/           ← un archivo por migración
├── app/
│   ├── main.py             ← punto de entrada (como @SpringBootApplication)
│   ├── core/               ← configuración, seguridad, base de datos
│   ├── domain/engineering/ ← motor de cálculo térmico (lógica pura)
│   ├── infrastructure/     ← modelos SQLAlchemy (tablas de la BD)
│   └── modules/            ← el CRM: auth, users, projects, clients...
│       └── <modulo>/
│           ├── router.py       (@RestController)
│           ├── schemas.py      (DTOs)
│           ├── service.py      (@Service)
│           └── repository.py   (@Repository)
└── tests/
    └── unit/engineering/   ← 20 tests del motor de cálculo
```

---

## Credenciales de desarrollo

| Qué | Valor |
|---|---|
| URL del servidor | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Admin email | admin@crmfrigo.com |
| Admin password | Admin123! |
| BD host | localhost:5433 |
| BD nombre | hvac_saas |
| BD usuario | admin@crmfrigo.com |
| BD password | Admin123! |

> Estas credenciales son **solo para desarrollo local**.
> En producción todo cambia vía variables de entorno.
