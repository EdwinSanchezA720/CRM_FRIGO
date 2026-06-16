# CLAUDE.md

> Archivo de contexto para **Claude Code**. Define qué es este proyecto, cómo
> está arquitecturado y cómo quiero trabajar. Claude Code debe leerlo y respetarlo
> en cada sesión.

---

## 1. Qué es este proyecto

**HVAC SaaS** — plataforma web B2B para empresas de refrigeración y aire
acondicionado. Gestiona proyectos de ingeniería HVAC de principio a fin:
levantamiento en campo → cálculo de carga térmica → selección de equipos →
memoria de cálculo (PDF) → cotización (PDF) → histórico.

**Diseño completo:** ver `/docs/arquitectura-hvac-saas.md` y
`/docs/arquitectura-hvac-clean-ddd.md`. Léelos antes de tomar decisiones grandes.

**Estado actual:** proyecto nuevo, desde cero. Construimos el **MVP**.

**Alcance del MVP (lo único que importa ahora):**
- Capturar un proyecto con sus zonas (espacios) de forma manual.
- Calcular la carga térmica con **un** método: **CLTD simplificado**.
- Seleccionar equipo de un catálogo.
- Generar memoria de cálculo y cotización en PDF.
- Todo end-to-end, un solo método, sin features avanzadas.

**Fuera del MVP (NO implementar todavía, aunque parezca tentador):** app de campo
offline, selección automática optimizada, diseño de ductos, dashboards,
estimación con IA, integración con Revit. Existen en el roadmap; sacarlos de
aquí es intencional para no morir por scope creep.

---

## 2. Modo de trabajo (IMPORTANTE — soy junior)

Soy ingeniero mecánico aprendiendo Python, FastAPI y arquitectura de software.
Quiero **entender**, no solo tener código que funcione. Por eso:

- **Explica antes de codear.** Antes de escribir un archivo importante, dime en
  2-4 frases qué vas a hacer y por qué, en lenguaje simple.
- **Usa analogías de ingeniería mecánica / CAD** cuando expliques un concepto
  nuevo (parametrización, ensambles, análisis dimensional, tolerancias).
- **Construye en pasos pequeños y verificables.** Un archivo o concepto a la vez.
  No me sueltes 8 archivos de golpe. Prefiero entender 1 bien que 8 a medias.
- **Corre los tests después de cada paso** y muéstrame que pasan.
- **Cuando uses un patrón de DDD** (value object, agregado, repositorio), recuérdame
  en una línea qué es y por qué aplica aquí.
- **Si me equivoco o pido algo que rompe la arquitectura, dímelo.** Prefiero una
  corrección honesta a que me sigas la corriente.
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
| Tests | pytest + pytest-asyncio |
| Lint / formato | ruff |
| PDF (más adelante) | WeasyPrint + Jinja2 |
| Contenedores | Docker + docker-compose |

---

## 4. Principios de arquitectura (reglas inviolables)

Combinamos **Clean Architecture** (regla de dependencia) + **DDD** (modelado),
pero de forma **pragmática**. Las reglas:

### Regla 1 — La regla de dependencia
Las dependencias apuntan hacia adentro. **`app/domain/` NO importa nada de
frameworks** (ni FastAPI, ni SQLAlchemy, ni Pydantic). Es Python puro con
`dataclasses`. El dominio es el activo; los frameworks son detalles reemplazables.

```
interface (FastAPI) → application (use cases) → domain (núcleo puro)
infrastructure (SQLAlchemy, PDF, S3) → implementa interfaces definidas hacia adentro
```

### Regla 2 — DDD completo SOLO en el contexto núcleo
El único contexto con tratamiento DDD completo (agregados, value objects, domain
services) es **`engineering`** (el motor de cálculo). Es nuestro diferenciador.

**Todo lo demás (clientes, catálogo, proyectos, auth) es CRUD simple** en
`app/modules/`: service + repository, SQLAlchemy directo, SIN agregados ricos ni
value objects. Un cliente es CRUD; una carga térmica es dominio. No confundir.

### Regla 3 — Referencias entre agregados por ID
Un agregado guarda el **id** de otro, no el objeto. `LoadCalculation` guarda
`project_id`, nunca un objeto `Project`.

### Regla 4 — Resultados de ingeniería inmutables
Un cálculo finalizado no se edita: se crea una nueva versión. La invariante vive
dentro del agregado (`finalize()` bloquea cambios posteriores).

### Regla 5 — Multi-tenant desde el día uno
Toda tabla de negocio lleva `tenant_id`. PK con UUID. Aunque haya un solo usuario
ahora, la columna va desde el inicio.

---

## 5. Estructura de carpetas

```
app/
├── main.py                     # crea la app FastAPI
├── core/                       # transversal (config, db, security, exceptions)
├── shared/                     # base de DDD: Entity, AggregateRoot, DomainEvent
├── domain/engineering/         # ⭐ NÚCLEO PURO — sin frameworks
│   ├── value_objects.py        # Capacity, HeatLoad, Temperature
│   ├── entities.py             # SpaceLoad
│   ├── load_calculation.py     # Aggregate Root
│   ├── services.py             # ThermalLoadCalculator (CLTD)
│   ├── events.py               # LoadCalculationFinalized
│   └── repository.py           # interfaces (Protocol)
├── application/engineering/    # use cases (RunLoadCalculation), commands, results
├── infrastructure/             # SQLAlchemy repos, mappers, PDF, storage, event bus
├── interface/api/              # routers FastAPI + schemas Pydantic
└── modules/                    # subdominios de SOPORTE — CRUD simple
    ├── auth/  tenants/  clients/  projects/  catalog/

tests/
├── unit/engineering/           # dominio puro, sin BD
├── application/                # use cases con repos en memoria
└── integration/                # con Postgres de prueba
```

Regla práctica: si dudas dónde va un archivo, pregunta "¿esto es del motor de
cálculo (núcleo) o es CRUD de soporte?". Núcleo → capas (`domain`/`application`/
`infrastructure`/`interface`). Soporte → `modules/<contexto>/`.

---

## 6. Orden de construcción (CONSTRUIR EN ESTE ORDEN)

De adentro hacia afuera. Cada fase es entregable y testeable por sí sola.
**No saltes fases.** No empieces FastAPI antes de tener el dominio probado.

**Fase 0 — Dominio núcleo puro** ← EMPEZAMOS AQUÍ
- Value objects: `Capacity`, `HeatLoad`, `Temperature` (+ sus tests)
- Entity: `SpaceLoad`
- Aggregate: `LoadCalculation` con `finalize()` e invariantes
- Domain service: `ThermalLoadCalculator` (CLTD simplificado)
- Tests con pytest. Sin BD, sin FastAPI. Validar contra un cálculo a mano.

**Fase 1 — Un use case con repo en memoria**
- `RunLoadCalculationUseCase`, `commands.py`, `results.py`
- Interfaz `LoadCalculationRepository` (Protocol)
- `InMemoryLoadCalculationRepository`
- Test del use case end-to-end, sin BD.

**Fase 2 — Infraestructura real**
- Modelos SQLAlchemy + Alembic
- Mapeo dominio ↔ ORM (usar **Imperative Mapping** de SQLAlchemy)
- `SqlAlchemyLoadCalculationRepository`
- Hito: los tests de Fase 1 deben pasar SIN CAMBIOS al cambiar el repo.

**Fase 3 — API / presentación**
- Router FastAPI + schemas Pydantic + inyección de dependencias
- Endpoint `POST /calculations` funcionando end-to-end.

**Fase 4 — Subdominios de soporte (CRUD simple, sin DDD)**
- `projects`, `clients`, `catalog`, `auth` como service + repository.

**Fase 5 — Eventos de dominio**
- `EventBus` en proceso. `LoadCalculationFinalized` → habilita memoria.

---

## 7. Convenciones de código

- Identificadores en **inglés snake_case**. Clases en `PascalCase`.
- **Type hints siempre.** Código async para I/O (BD, HTTP, archivos).
- Value objects = `@dataclass(frozen=True)` (inmutables).
- Un repositorio por **aggregate root**, nunca por entidades internas.
- Excepciones de dominio heredan de `DomainError` (en `core/exceptions.py`).
- Nada de lógica de negocio en los routers; los routers solo traducen HTTP →
  use case → HTTP.
- Pydantic v2 para schemas de API (`interface/`), NO en el dominio.
- Comentarios solo donde el *por qué* no es obvio; el código se explica solo.

---

## 8. Comandos

```bash
# Dependencias
uv sync

# Tests
uv run pytest                              # todo
uv run pytest tests/unit/engineering -v    # solo el núcleo (Fase 0)
uv run pytest -k "capacity"                # por nombre

# Lint y formato
uv run ruff check .
uv run ruff format .

# Base de datos (Fase 2+)
docker compose up -d db
uv run alembic revision --autogenerate -m "mensaje"
uv run alembic upgrade head

# Correr la API (Fase 3+)
uv run uvicorn app.main:app --reload
```

---

## 9. Lo que NO se debe hacer (anti-patrones)

- ❌ NO importar SQLAlchemy/FastAPI/Pydantic dentro de `app/domain/`.
- ❌ NO crear agregados ricos ni value objects en `modules/` (soporte = CRUD).
- ❌ NO CQRS, NO Event Sourcing, NO microservicios, NO broker de mensajes. Es un
  monolito modular con eventos en proceso.
- ❌ NO meter lógica de negocio en los routers.
- ❌ NO implementar features fuera del alcance del MVP (sección 1).
- ❌ NO crear 8 archivos de golpe. Pasos pequeños, explicados y testeados.
- ❌ NO interfaces para cada clase; solo donde invertimos dependencias (repos,
  providers externos).

---

## 10. Próximo paso

Estamos por empezar la **Fase 0**. El primer entregable es el value object
`Capacity` (capacidad térmica con conversiones BTU/h ↔ toneladas ↔ kW) junto con
su archivo de tests. Explícame el concepto, escríbelo, y corre los tests.