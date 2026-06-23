# CLAUDE.md

> Archivo de contexto para **Claude Code**. Define qué es este proyecto, cómo
> está arquitecturado y cómo quiero trabajar. Claude Code debe leerlo y respetarlo
> en cada sesión.

---

## 1. Qué es este proyecto

**HVAC SaaS** — plataforma web B2B para empresas de refrigeración y aire
acondicionado. Gestiona proyectos de ingeniería HVAC de principio a fin:
levantamiento → cálculo de carga térmica → selección de equipos →
memoria de cálculo (PDF) → cotización (PDF) → seguimiento de garantías.

**Referencia técnica completa:** ver [`README.md`](README.md).

**Estado actual:** Fase 0 completa. Construyendo el **MVP**.

**Método de cálculo:** Manual de Ingeniería **Frigus Bohn BCT-025-H-ENG-1APM**,
formularios **H-ENG-2.1** (≥32°F) y **H-ENG-3.1** (<32°F). El archivo fuente
del manual está en [`BCT-025-H-ENG-1APM-Manual-Ingenieria (1).md`].

**Alcance del MVP:**
- Capturar un proyecto con datos de la cámara (dimensiones, aislamiento, temperaturas).
- Calcular la carga térmica con el **método Bohn** (5 fuentes de calor).
- Seleccionar equipo de un catálogo.
- Generar memoria de cálculo y cotización en PDF.
- CRM: clientes, proyectos, garantías, manuales — acceso por rol.

**Fuera del MVP (no implementar):** app offline, selección automática optimizada,
diseño de ductos, estimación con IA, integración con Revit.

---

## 2. Modo de trabajo (IMPORTANTE — soy junior)

Soy ingeniero mecánico aprendiendo Python, FastAPI y arquitectura de software.
Quiero **entender**, no solo tener código que funcione. Por eso:

- **Explica antes de codear.** Antes de escribir un archivo importante, dime en
  2-4 frases qué vas a hacer y por qué, en lenguaje simple.
- **Usa analogías de ingeniería mecánica / CAD** cuando expliques un concepto
  nuevo (parametrización, ensambles, análisis dimensional, tolerancias).
- **El colaborador que revisa el código solo sabe Java/Spring Boot.** Cuando hagas
  algo que tiene equivalente en Spring Boot (`@Service`, `@Repository`, DTO, etc.),
  menciónalo en el docstring del archivo.
- **Construye en pasos pequeños y verificables.** Un archivo o concepto a la vez.
  No sueltes 8 archivos de golpe.
- **Corre los tests después de cada paso** y muéstrame que pasan.
- **Si pido algo que rompe la arquitectura, dímelo.** Prefiero una corrección
  honesta a que me sigas la corriente.
- Háblame en **español**; el código e identificadores van en **inglés**.

---

## 3. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Gestor de paquetes | `uv` |
| API | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Validación / schemas | Pydantic v2 |
| Base de datos | PostgreSQL 16 |
| Migraciones | Alembic |
| Tests | pytest |
| Lint / formato | ruff |
| PDF | WeasyPrint + Jinja2 (Fase 5) |
| Contenedores | Docker + docker-compose (Fase 2) |

---

## 4. Principios de arquitectura (reglas inviolables)

### Regla 1 — La regla de dependencia
`app/domain/` NO importa nada de frameworks (ni FastAPI, ni SQLAlchemy, ni Pydantic).
Es Python puro con `dataclasses`. El dominio es el activo; los frameworks son detalles.

```
modules/ (FastAPI routers) → llaman a domain/engineering/ (lógica pura)
infrastructure/ (SQLAlchemy, PDF) → implementa interfaces del dominio
```

### Regla 2 — DDD solo en el motor de cálculo
El único código con tratamiento de dominio rico es `app/domain/engineering/`.
Todo lo demás (`app/modules/`) es **CRUD simple**: service + repository directo.
Un cliente es CRUD. Una carga térmica es dominio. No confundir.

### Regla 3 — Resultados de ingeniería inmutables
Un cálculo terminado no se edita. Se crea una nueva versión si cambian los datos.
Los dataclasses del dominio son `frozen=True`.

### Regla 4 — Multi-tenant desde el día uno
Toda tabla de negocio lleva `tenant_id` (UUID). Aunque haya un solo usuario hoy,
la columna va desde el inicio.

### Regla 5 — Roles en un solo sistema
No hay dos aplicaciones separadas para técnico y cliente. Un solo backend, un solo
login. El campo `rol` en `users` determina qué endpoints y datos puede ver cada uno.

---

## 5. Estructura real del proyecto (estado actual)

```
app/
├── main.py                          # FastAPI arranca aquí
│
├── domain/engineering/              # ⭐ MOTOR DE CÁLCULO — Python puro, sin frameworks
│   ├── tables.py                    # Tablas Bohn: Tabla 1, 4, 5, 6, 11, 12, 20
│   ├── entities.py                  # RoomInput, ProductLoad, MiscLoads (inputs del formulario)
│   └── services.py                  # RefrigerationLoadCalculator (las 5 secciones)
│
└── modules/                         # CRM — CRUD simple, un módulo por sección del menú
    ├── auth/                        # Login y JWT
    │   ├── router.py                  # URLs  (Java: @RestController)
    │   ├── schemas.py                 # DTOs  (Java: Request/Response classes)
    │   ├── service.py                 # Lógica (Java: @Service)
    │   └── repository.py             # BD     (Java: @Repository)
    ├── projects/                    # Proyectos — módulo central del MVP
    ├── clients/                     # Clientes
    ├── equipment/                   # Catálogo de equipos
    ├── warranties/                  # Garantías
    └── reports/                     # Generación de PDFs

tests/
└── unit/engineering/
    └── test_load_calculator.py      # 20 tests — validados contra ejemplos del manual Bohn
```

**Regla práctica:** ¿Es del motor de cálculo? → `domain/engineering/`.
¿Es CRM / gestión? → `modules/<nombre>/` con los 4 archivos de siempre.

---

## 6. Roles de usuario

| Rol | Qué ve |
|---|---|
| `admin` | Todo |
| `tecnico` | Proyectos, clientes, equipos, garantías, reportes |
| `cliente` | Solo sus proyectos (lectura), sus garantías, manuales, perfil |

En FastAPI: `Depends(require_role("tecnico"))` en cada router.
En Spring Boot sería: `@PreAuthorize("hasRole('TECNICO')")`.

---

## 7. Estado del motor de cálculo (Fase 0 — COMPLETA)

El motor implementa el método Bohn BCT-025. Las 5 secciones:

| Sección | Fuente de calor | Archivos |
|---|---|---|
| 1 | Transmisión por paredes, techo, piso | `tables.py` → `wall_heat_load_factor` |
| 2 | Infiltración por cambios de aire | `tables.py` → `air_changes_per_day` × `air_heat_content` |
| 3 | Misceláneos (motores, luces, personas, puertas de cristal) | `tables.py` → constantes |
| 4 | Carga sensible del producto | `services.py` → `_section4_product_sensible` |
| 5 | Respiración (frutas/vegetales) | parámetro externo |

Formula final:
```
Total BTU/24hr = (S1 + S2 + S3 + S4 + S5) × 1.10
BTU/hr requeridos = Total / horas_de_operación
```

**Los 20 tests están validados contra los ejemplos impresos del manual (págs. 5-8).**
Tolerancia de ≤3% en todos los valores.

---

## 8. Plan de construcción

| Fase | Qué se construye | Estado |
|---|---|---|
| **0** | Motor de cálculo Bohn — `domain/engineering/` + 20 tests | ✅ Completo |
| **1** | Use case `RunLoadCalculationUseCase` + repo en memoria | 🔲 Siguiente |
| **2** | PostgreSQL + SQLAlchemy + Alembic | 🔲 Pendiente |
| **3** | API FastAPI — endpoints de cálculo end-to-end | 🔲 Pendiente |
| **4** | Módulos de soporte completos — auth con JWT, clients, equipment, warranties | 🔲 Pendiente |
| **5** | Generación de PDFs — memoria de cálculo y cotización | 🔲 Pendiente |

**Regla:** No empezar una fase sin que la anterior tenga todos sus tests pasando.

---

## 9. Siguiente paso — Fase 1

Construir el **use case** que orquesta el cálculo. Esto es la capa que conecta
el motor de cálculo (`domain/`) con el exterior (API, tests de integración).

Archivos a crear en `app/application/engineering/`:
- `commands.py` — datos de entrada del use case (lo que llega desde el router)
- `results.py` — datos de salida (lo que el router devuelve como JSON)
- `use_case.py` — `RunLoadCalculationUseCase` (orquesta el cálculo)
- `repository.py` — interfaz `Protocol` (contrato que implementará SQLAlchemy)

Repo en memoria para tests (sin base de datos):
- `tests/application/in_memory_repository.py`
- `tests/application/test_run_load_calculation.py`

El hito es: el test del use case corre end-to-end sin base de datos.

---

## 10. Convenciones de código

- Identificadores en **inglés snake_case**. Clases en `PascalCase`.
- **Type hints siempre.**
- Value objects y resultados de dominio = `@dataclass(frozen=True)`.
- Un repositorio por **aggregate root**.
- Comentarios solo donde el *por qué* no es obvio.
- Pydantic v2 en `modules/` (schemas de API). Nunca en `domain/`.

---

## 11. Anti-patrones (NO hacer)

- NO importar SQLAlchemy / FastAPI / Pydantic dentro de `app/domain/`.
- NO crear value objects o lógica rica en `app/modules/` (ahí solo CRUD).
- NO lógica de negocio en los routers.
- NO features fuera del MVP (ver sección 1).
- NO soltar muchos archivos de golpe — pasos pequeños, explicados, testeados.
- NO dos sistemas separados para técnico y cliente — es un solo sistema con roles.

---

## 12. Comandos

```bash
# Instalar dependencias
uv sync

# Tests — motor de cálculo (Fase 0)
uv run pytest tests/unit/engineering -v

# Tests — todos
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .

# Servidor (Fase 3+)
uv run uvicorn app.main:app --reload
# Docs en: http://localhost:8000/docs

# Base de datos (Fase 2+)
docker compose up -d db
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head
```
