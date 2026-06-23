# HVAC SaaS — CRM de Ingeniería de Refrigeración

Plataforma web B2B para empresas de refrigeración y aire acondicionado.
Gestiona proyectos de ingeniería HVAC de principio a fin:
**levantamiento → cálculo de carga térmica → selección de equipos → memoria de cálculo (PDF) → cotización (PDF) → seguimiento de garantías**.

---

## Índice

1. [Roles de usuario](#1-roles-de-usuario)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [Equivalencias Java ↔ FastAPI](#3-equivalencias-java--fastapi)
4. [Módulos del CRM](#4-módulos-del-crm)
5. [Motor de cálculo térmico (Domain)](#5-motor-de-cálculo-térmico-domain)
6. [Base de datos — Modelos principales](#6-base-de-datos--modelos-principales)
7. [API — Convenciones de rutas](#7-api--convenciones-de-rutas)
8. [Cómo correr el proyecto](#8-cómo-correr-el-proyecto)
9. [Plan de construcción (Fases)](#9-plan-de-construcción-fases)

---

## 1. Roles de usuario

El sistema tiene **dos tipos de usuario**. No son sistemas separados — es un solo
sistema con vistas diferentes según el rol.

### Técnico / Admin
Empleado de la empresa de refrigeración.

| Módulo | Acceso |
|---|---|
| Dashboard | ✅ Métricas globales |
| Proyectos | ✅ Crear, editar, calcular, generar PDFs |
| Clientes | ✅ Crear y gestionar todos los clientes |
| Equipos | ✅ Catálogo completo |
| Garantías | ✅ Todas las garantías |
| Reportes | ✅ Todos los reportes |
| Administración | ✅ Usuarios, configuración |

### Cliente
Usuario externo (dueño del negocio donde se instaló el equipo).

| Módulo | Acceso |
|---|---|
| Mis Proyectos | ✅ Solo los suyos (solo lectura) |
| Garantías | ✅ Solo las suyas — ver estado |
| Manuales | ✅ Manuales de sus equipos |
| Perfil | ✅ Sus datos de contacto |

> **Decisión de arquitectura:** Un solo sistema, un solo login. El `rol` del usuario
> determina qué ve. En FastAPI esto se implementa con **dependencias de autorización**
> en cada router. En Spring Boot sería `@PreAuthorize("hasRole('ADMIN')")`.

---

## 2. Estructura de carpetas

```
HVAC-SaaS/
│
├── app/                              # Todo el código Python
│   │
│   ├── main.py                       # FastAPI arranca aquí (= main() en Spring Boot)
│   │
│   ├── domain/                       # Motor de cálculo — LÓGICA PURA sin frameworks
│   │   └── engineering/              # Cálculo de carga térmica (Manual Bohn BCT-025)
│   │       ├── tables.py             # Tablas del manual (Tabla 1, 4, 5, 6, 11, 12, 20)
│   │       ├── entities.py           # Datos de entrada del formulario H-ENG-2.1/3.1
│   │       └── services.py           # RefrigerationLoadCalculator (las 5 secciones)
│   │
│   └── modules/                      # El CRM — un módulo por sección del menú
│       ├── auth/                     # Login y tokens
│       ├── projects/                 # Proyectos (crear, calcular, entregables)
│       ├── clients/                  # Clientes
│       ├── equipment/                # Catálogo de equipos
│       ├── warranties/               # Garantías
│       └── reports/                  # Generación de PDFs
│
└── tests/
    └── unit/engineering/             # Tests del motor de cálculo
        └── test_load_calculator.py   # 20 tests — validados contra manual Bohn
```

### Dentro de cada módulo (siempre los mismos 4 archivos)

```
modules/projects/
├── router.py       # Las URLs (endpoints)
├── schemas.py      # Qué datos entran y salen (JSON)
├── service.py      # La lógica de negocio
└── repository.py   # Acceso a la base de datos
```

---

## 3. Equivalencias Java ↔ FastAPI

Para el colaborador que conoce Java/Spring Boot, la correspondencia es directa:

| Spring Boot | FastAPI (Python) | ¿Qué hace? |
|---|---|---|
| `@RestController` | `router.py` con `APIRouter()` | Define las URLs y verbos HTTP |
| DTO / Request class | `schemas.py` con `class X(BaseModel)` | Valida y serializa JSON |
| `@Service` | `service.py` con `class XService` | Lógica de negocio |
| `@Repository` / JPA | `repository.py` con `class XRepository` | SQL / base de datos |
| `@Entity` | `models.py` con SQLAlchemy | Tabla de base de datos |
| `@Autowired` | `Depends()` en FastAPI | Inyección de dependencias |
| `@PreAuthorize` | `Depends(require_role("admin"))` | Autorización por rol |
| `application.properties` | `.env` + `pydantic-settings` | Configuración |
| `pom.xml` | `pyproject.toml` | Dependencias del proyecto |
| `mvn spring-boot:run` | `uv run uvicorn app.main:app --reload` | Correr el servidor |

### Ejemplo concreto — Crear un cliente

**Java (Spring Boot):**
```java
// ClientController.java
@RestController
@RequestMapping("/clients")
public class ClientController {
    @PostMapping
    public ClientResponse create(@RequestBody ClientRequest req) {
        return clientService.create(req);
    }
}
```

**FastAPI (Python):**
```python
# modules/clients/router.py
@router.post("/", response_model=ClientResponse)
def create_client(req: ClientCreate, service: ClientService = Depends()):
    return service.create(req)
```

---

## 4. Módulos del CRM

### `auth/` — Login
- **¿Qué hace?** Verifica credenciales y entrega un JWT token.
- **Roles:** Todos los usuarios pasan por aquí.
- **Flujo:** `POST /auth/login` → verifica email+password → retorna `access_token`.
- **Pendiente:** JWT, refresh tokens, middleware de autenticación.

### `projects/` — Proyectos ⭐ (módulo principal)
- **¿Qué hace?** Gestiona el ciclo de vida de un proyecto de ingeniería.
- **Flujo completo:**
  1. Técnico crea el proyecto y lo asocia a un cliente
  2. Ingresa datos del cuarto (dimensiones, temperatura, aislamiento)
  3. El motor de cálculo (`domain/engineering/`) calcula la carga térmica
  4. Se selecciona el equipo del catálogo
  5. Se genera la memoria de cálculo PDF
  6. Se genera la cotización PDF
- **Roles:** Técnico crea/edita. Cliente solo lee sus proyectos.

### `clients/` — Clientes
- **¿Qué hace?** CRUD de clientes de la empresa.
- **Información clave a recopilar:**
  - Datos de contacto: nombre, email, teléfono, WhatsApp
  - Empresa / razón social + RFC
  - Dirección de la instalación (donde va el equipo)
  - Tipo de negocio: restaurante, farmacia, supermercado, bodega, etc.
  - Contacto técnico (quién recibe el servicio) vs contacto administrativo (quien paga)
- **Relaciones:** Un cliente puede tener **múltiples proyectos**.

### `equipment/` — Equipos (Catálogo)
- **¿Qué hace?** Catálogo de equipos disponibles para cotizar.
- **Incluye:** Evaporadores, unidades condensadoras, sistemas divididos.
- **Datos:** Modelo, marca, capacidad BTU/h, refrigerante, precio lista.
- **Pendiente:** Importar catálogo Bohn/Heatcraft desde Excel o PDF.

### `warranties/` — Garantías
- **¿Qué hace?** Registra y da seguimiento a garantías de equipos instalados.
- **Flujo:** Proyecto finalizado → se activa la garantía → cliente puede consultar estado.
- **Vista cliente:** Solo ve sus propias garantías.
- **Vista técnico:** Ve todas, puede actualizar estado (activa, en proceso, cerrada).

### `reports/` — Reportes
- **¿Qué hace?** Genera PDFs a partir de los datos del proyecto.
- **Tipos de reporte:**
  - Memoria de cálculo (usa datos del motor `domain/engineering/`)
  - Cotización (usa datos del catálogo + proyecto)
- **Tecnología:** WeasyPrint + Jinja2 (plantillas HTML → PDF).

---

## 5. Motor de cálculo térmico (Domain)

Este es el **núcleo diferenciador** del sistema. Es Python puro — no sabe que
existe FastAPI ni base de datos.

Implementa el método del **Manual de Ingeniería Frigus Bohn BCT-025-H-ENG-1APM**,
formularios **H-ENG-2.1** (cuartos arriba de 32°F) y **H-ENG-3.1** (abajo de 32°F).

### Las 5 fuentes de calor (= las 5 secciones del formulario)

```
Carga Total = (S1 + S2 + S3 + S4 + S5) × 1.10   [BTU/24hrs]
BTU/hr = Carga Total / horas de operación
```

| Sección | Fuente de calor | Tabla del manual |
|---|---|---|
| 1 | Transmisión por paredes, techo, piso | Tabla 1 |
| 2 | Infiltración por cambios de aire | Tablas 4/5 × Tabla 6 |
| 3 | Misceláneos (motores, luces, personas, puertas) | Tablas 11, 12, 20 |
| 4 | Carga sensible del producto | Tabla 7 |
| 5 | Respiración (solo frescos/vegetales) | Tabla 8 |

### Ejemplo validado (Ejemplo 1 del manual, pág. 5)
```
Refrigerador tienda de conveniencia a 35°F, 28×8×8 ft
Aislamiento: 4" Estireno paredes/techo, piso concreto 6"
Temperatura ambiente: 85°F

Resultado:
  S1 Transmisión:    85,600 BTU/24hr
  S2 Aire:           64,996 BTU/24hr
  S3 Misceláneos:   225,368 BTU/24hr  (incluye 10 puertas de cristal)
  S4 Producto:       90,700 BTU/24hr
  S5 Respiración:         0
  ─────────────────────────────────
  Subtotal:         466,664 BTU/24hr
  + 10% seguridad:   46,666 BTU/24hr
  Total:            513,330 BTU/24hr
  ÷ 16 hrs =         32,083 BTU/hr  ← capacidad del equipo a seleccionar
```

### ¿Por qué las tablas del manual están en Python y no en PostgreSQL?

Las Tablas 1, 4, 5, 6, 11, 12, 20 del Bohn son **constantes físicas empíricas** —
como la conductividad térmica del poliestireno o el contenido de calor del aire a 35°F.
No tienen usuarios que las creen, editen o borren. No tienen CRUD.

> Analogía: es la diferencia entre una *tabla de propiedades termodinámicas* de un
> manual (fija, no cambia) y una *lista de precios de tu distribuidor* (cambia cada
> mes, la administra alguien).

**Razones concretas para dejarlas en `tables.py`:**

- `domain/engineering/` no puede depender de la base de datos (regla arquitectural).
  Si se mueven a Postgres, el dominio puro deja de ser puro.
- Los tests de Fase 0 corren **sin Postgres levantado**. Si las tablas estuvieran en
  BD, los 20 tests necesitarían una conexión activa.
- Un cálculo llama estas tablas 20-30 veces. En memoria: microsegundos.
  En Postgres: milisegundos × 30 = lento sin beneficio.
- Son ~100 filas en total. No hay ganancia operativa en una BD.

**Lo que SÍ va en PostgreSQL** (porque un humano lo administra):

| Dato | Módulo | Razón |
|---|---|---|
| Catálogo de equipos (modelos, precios, BTU/hr) | `equipment/` | Los precios cambian, el admin agrega modelos |
| Propiedades de productos por tipo (Cp, calor latente) | `product_catalog/` | La empresa puede agregar productos nuevos |
| Proyectos, cálculos, clientes, garantías | todos los módulos | Son datos de negocio con ciclo de vida |

> **Regla:** ¿Un humano necesita crear, editar o borrar este dato? → PostgreSQL.
> ¿Es una constante física de un manual de ingeniería? → Python.

---

## 6. Base de datos — Modelos principales

> La base de datos se implementa en **Fase 2**. Aquí está el diseño.
> Todos los IDs son **UUID**. Toda tabla de negocio lleva `tenant_id` (multi-empresa).

### Tabla `users`
```sql
users
├── id            UUID PRIMARY KEY
├── tenant_id     UUID NOT NULL           -- a qué empresa pertenece
├── nombre        VARCHAR(100) NOT NULL
├── email         VARCHAR(255) UNIQUE NOT NULL
├── password_hash VARCHAR(255) NOT NULL
├── rol           VARCHAR(20) NOT NULL    -- 'admin' | 'tecnico' | 'cliente'
├── activo        BOOLEAN DEFAULT TRUE
└── fecha_creacion TIMESTAMP DEFAULT NOW()
```

### Tabla `clients`
```sql
clients
├── id              UUID PRIMARY KEY
├── tenant_id       UUID NOT NULL
├── nombre          VARCHAR(100) NOT NULL
├── empresa         VARCHAR(100)
├── rfc             VARCHAR(20)
├── email           VARCHAR(255)
├── telefono        VARCHAR(20)
├── whatsapp        VARCHAR(20)
├── tipo_negocio    VARCHAR(50)           -- restaurante, farmacia, bodega...
├── direccion_instalacion TEXT
├── contacto_tecnico  VARCHAR(100)        -- quién recibe el servicio
├── contacto_admin    VARCHAR(100)        -- quién paga / firma
└── fecha_creacion  TIMESTAMP DEFAULT NOW()
```

### Tabla `projects`
```sql
projects
├── id              UUID PRIMARY KEY
├── tenant_id       UUID NOT NULL
├── client_id       UUID REFERENCES clients(id)
├── nombre          VARCHAR(150) NOT NULL
├── descripcion     TEXT
├── status          VARCHAR(30)           -- borrador | calculado | cotizado | cerrado
├── btuh_calculados FLOAT                 -- resultado del motor de cálculo
├── fecha_inicio    DATE
└── fecha_creacion  TIMESTAMP DEFAULT NOW()
```

### Tabla `warranties`
```sql
warranties
├── id              UUID PRIMARY KEY
├── tenant_id       UUID NOT NULL
├── project_id      UUID REFERENCES projects(id)
├── numero_serie    VARCHAR(50)
├── modelo_equipo   VARCHAR(100)
├── fecha_instalacion DATE
├── fecha_inicio    DATE
├── fecha_fin       DATE
├── status          VARCHAR(30)           -- activa | en_proceso | expirada | cerrada
└── notas           TEXT
```

### Relaciones clave
```
tenant (empresa)
  └── users (empleados + clientes)
  └── clients
        └── projects
              ├── load_calculations (resultado del cálculo térmico)
              ├── equipment_selections (equipos cotizados)
              └── warranties (garantías activas)
```

---

## 7. Autenticación y control de acceso

### Cómo funciona el login (JWT)

```
1. Cliente → POST /auth/login  { email, password }
2. Servidor verifica password contra el hash en BD
3. Servidor genera un JWT firmado con los datos del usuario
4. Cliente recibe el token y lo guarda (localStorage / cookie)
5. En cada request siguiente:
      Authorization: Bearer eyJhbGci...
6. Servidor lee el JWT, extrae el usuario — SIN consultar la BD
```

> **Analogía:** el JWT es como un pase de acceso firmado. El portero (servidor)
> lo lee y sabe quién eres sin llamar a la oficina central (base de datos).

**En Spring Boot:** `JwtAuthenticationFilter` + `@BearerTokenAuthentication`
**En FastAPI:** `Depends(get_current_user)` en cada router

### Roles y permisos

| Rol | Quién es | Acceso |
|---|---|---|
| `admin` | Dueño / gerente de la empresa | Todo — incluyendo crear/editar usuarios |
| `tecnico` | Ingeniero en campo | Proyectos, cálculos, reportes técnicos |
| `ventas` | Asesor comercial | Clientes, cotizaciones, pipeline |
| `cliente` | Cliente externo | Solo sus proyectos y garantías (lectura) |

En FastAPI, el control por rol se hace con:
```python
# Solo admins pueden acceder:
@router.get("/users")
async def listar(user = Depends(require_role("admin"))):  ...

# Admins O técnicos:
@router.post("/projects/{id}/calculate")
async def calcular(user = Depends(require_role("admin", "tecnico"))): ...
```

Java equivalent: `@PreAuthorize("hasAnyRole('ADMIN', 'TECNICO')")`

### Archivos del sistema de auth

| Archivo | Java equivalent | ¿Qué hace? |
|---|---|---|
| [`app/core/config.py`](app/core/config.py) | `application.properties` | SECRET_KEY, tiempo de expiración del token |
| [`app/core/security.py`](app/core/security.py) | `JwtUtil` + `PasswordEncoder` | Crear/leer JWT, hashear contraseñas con bcrypt |
| [`app/core/exceptions.py`](app/core/exceptions.py) | Custom exceptions | 401, 403, 404, 409 con mensajes claros |
| [`app/core/database.py`](app/core/database.py) | `DataSource` + `EntityManager` | Conexión async a SQLite/PostgreSQL |
| [`app/core/dependencies.py`](app/core/dependencies.py) | Spring Security filters | `get_current_user`, `require_role()` |
| [`app/infrastructure/models/user.py`](app/infrastructure/models/user.py) | `@Entity User.java` | Tabla `users` en la BD |
| [`app/modules/auth/`](app/modules/auth/) | `AuthController` + `AuthService` | Login, GET /me |
| [`app/modules/users/`](app/modules/users/) | `UserController` + `UserService` | CRUD de usuarios (solo admin) |

### Endpoints activos (✅ funcionando)

| Verbo | Ruta | Rol requerido | ¿Qué hace? |
|---|---|---|---|
| `POST` | `/auth/login` | Ninguno (público) | Email + password → JWT token |
| `GET` | `/auth/me` | Cualquier usuario autenticado | Ver mis datos desde el token |
| `GET` | `/users/` | `admin` | Listar todos los usuarios |
| `POST` | `/users/` | `admin` | Crear usuario con rol asignado |
| `PUT` | `/users/{id}` | `admin` | Cambiar nombre, rol o desactivar |
| `DELETE` | `/users/{id}` | `admin` | Desactivar acceso (soft delete) |

### Endpoints pendientes (próximas fases)

| Verbo | Ruta | Fase |
|---|---|---|
| `POST` | `/projects` | Fase 3 |
| `POST` | `/projects/{id}/calculate` | Fase 3 |
| `GET` | `/projects/{id}/report` | Fase 5 |
| `GET` | `/clients` | Fase 4 |
| `GET` | `/warranties` | Fase 4 |

---

## 8. Cómo correr el proyecto

### Requisitos
- Python 3.12
- `uv` (gestor de paquetes)
- Docker Desktop

### Base de datos (PostgreSQL con Docker)

El proyecto usa PostgreSQL 16 en un contenedor Docker.

```bash
# Levantar el contenedor de base de datos
docker compose up -d db

# Verificar que está corriendo
docker compose ps
```

> **Nota:** El puerto es **5433** (no 5432) porque macOS ya tiene PostgreSQL local en 5432.
> Si en tu máquina el 5432 está libre, puedes cambiarlo en `docker-compose.yml` y `.env`.

**Credenciales de desarrollo:**

| | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5433` |
| Base de datos | `hvac_saas` |
| Usuario | `crmfrigo` |
| Password | `crmfrigo123` |

### Migraciones (Alembic)

Alembic gestiona los cambios de esquema de la BD.
Java equivalent: **Flyway** o **Liquibase**.

```bash
# Aplicar todas las migraciones pendientes (crear/actualizar tablas)
uv run alembic upgrade head

# Crear una nueva migración cuando agregas o modificas un modelo SQLAlchemy
uv run alembic revision --autogenerate -m "descripcion_del_cambio"

# Ver el historial de migraciones aplicadas
uv run alembic history

# Revertir la última migración
uv run alembic downgrade -1
```

**¿Cuándo crear una migración?**
Cada vez que modifiques un archivo en `app/infrastructure/models/` — agregar tabla,
columna, índice o constraint — genera una nueva migración con `--autogenerate`.

### Primera vez (setup completo)
```bash
# 1. Instalar dependencias
uv sync

# 2. Levantar PostgreSQL
docker compose up -d db

# 3. Aplicar migraciones (crear tablas)
uv run alembic upgrade head

# 4. Crear el primer usuario admin
uv run python -m app.core.seed
#    Crea: admin@crmfrigo.com / Admin123!

# 5. Correr el servidor
uv run uvicorn app.main:app --reload
```

### Probar el login desde terminal
```bash
# Login — obtener token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@crmfrigo.com","password":"Admin123!"}'

# Ver mi perfil (reemplazar TOKEN con el access_token de la respuesta)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN"

# Crear un técnico
curl -X POST http://localhost:8000/users/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Carlos Técnico","email":"carlos@empresa.com","password":"Pass123!","rol":"tecnico"}'
```

### Documentación interactiva (Swagger)
```
http://localhost:8000/docs    ← probar endpoints desde el navegador
                                 equivalente a Swagger UI en Spring Boot
```
Click en "Authorize" → pegar el token → todos los endpoints quedan autenticados.

### Tests y lint
```bash
uv run pytest                           # todos los tests
uv run pytest tests/unit/engineering -v # solo el motor de cálculo
uv run ruff check .                     # lint
uv run ruff format .                    # formato
```

---

## 9. Plan de construcción (Fases)

| Fase | Qué se construye | Estado |
|---|---|---|
| **0** | Motor de cálculo Bohn — `domain/engineering/` + 20 tests | ✅ Completo |
| **Auth** | Login JWT + administración de usuarios por rol | ✅ Completo |
| **1** | Use case `RunLoadCalculationUseCase` + repo en memoria | 🔲 Pendiente |
| **2** | PostgreSQL + SQLAlchemy + Alembic (migrar de SQLite) | 🔲 Pendiente |
| **3** | API — endpoints de proyectos y cálculo end-to-end | 🔲 Pendiente |
| **4** | Módulos CRUD — clients, equipment, warranties | 🔲 Pendiente |
| **5** | Generación de PDFs — memoria de cálculo y cotización | 🔲 Pendiente |

---

## Referencia técnica rápida

### Motor de cálculo
| Archivo | ¿Qué contiene? |
|---|---|
| [`app/domain/engineering/tables.py`](app/domain/engineering/tables.py) | Tablas Bohn 1, 4, 5, 6, 11, 12, 20 |
| [`app/domain/engineering/entities.py`](app/domain/engineering/entities.py) | `RoomInput`, `ProductLoad`, `MiscLoads` |
| [`app/domain/engineering/services.py`](app/domain/engineering/services.py) | `RefrigerationLoadCalculator` — 5 secciones |

### Infraestructura core
| Archivo | ¿Qué contiene? |
|---|---|
| [`app/core/config.py`](app/core/config.py) | Variables de entorno y configuración |
| [`app/core/security.py`](app/core/security.py) | JWT + bcrypt |
| [`app/core/database.py`](app/core/database.py) | Conexión SQLAlchemy async |
| [`app/core/dependencies.py`](app/core/dependencies.py) | `get_current_user`, `require_role` |
| [`app/core/exceptions.py`](app/core/exceptions.py) | Errores HTTP personalizados |
| [`app/core/seed.py`](app/core/seed.py) | Datos iniciales — primer admin |
