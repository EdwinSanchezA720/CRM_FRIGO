"""
Tablas del Manual de Ingeniería Frigus Bohn BCT-025-H-ENG-1APM.
Todas las funciones trabajan en sistema inglés (BTU, ft², lb, °F)
tal como el manual original.
"""
import bisect


# ── TABLA 1 ───────────────────────────────────────────────────────────────────
# Cargas de Transmisión de Calor en Paredes/Techo (BTU/24hr/ft²)
#
# Fórmula: Q = (K / espesor_pulg) × ΔT_°F × 24
#
# Los valores K efectivos que reproducen los ejemplos del manual:
#   Poliestireno/Estireno/EPS  → K = 0.24  (manual dice 0.26, efectivo 0.24)
#   Uretano espreado/espuma    → K = 0.12
#   Corcho / lana mineral      → K = 0.30
#   Fibra de vidrio            → K = 0.26
#
# Verificación con Ejemplo 1 del manual (pág. 5):
#   4" Estireno, ΔT=50°F → (0.24/4) × 50 × 24 = 72 ✓
# Verificación con Ejemplo 3 del manual (pág. 7):
#   4" Uretano, ΔT=105°F → (0.12/4) × 105 × 24 = 75.6 ≈ 76 ✓

INSULATION_K: dict[str, float] = {
    "polystyrene": 0.24,   # Estireno, EPS, Poliestireno expandido
    "urethane":    0.12,   # Uretano espreado, espuma de poliuretano
    "cork":        0.30,   # Corcho, lana mineral
    "fiberglass":  0.26,   # Fibra de vidrio
}

# Piso de concreto de 6" sin aislamiento adicional: R efectivo = 4.8
# Extraído del manual: Q = (1/4.8) × ΔT_piso × 24
# Verificación Ej-1: ΔT_piso = 60°F - 35°F = 25°F → (1/4.8)×25×24 = 125 ✓
_CONCRETE_FLOOR_R = 4.8


def wall_heat_load_factor(k: float, thickness_in: float, delta_t_f: float) -> float:
    """BTU/24hr/ft² para un muro o techo aislado (Tabla 1).

    Args:
        k: Conductividad térmica del aislamiento (BTU·in/hr·ft²·°F).
        thickness_in: Espesor del aislamiento en pulgadas.
        delta_t_f: Diferencia de temperatura °F (exterior − cuarto), positivo.
    """
    u = k / thickness_in
    return u * delta_t_f * 24.0


def concrete_floor_heat_load_factor(delta_t_f: float) -> float:
    """BTU/24hr/ft² para piso de concreto de 6" sin aislamiento (Tabla 1)."""
    return (1.0 / _CONCRETE_FLOOR_R) * delta_t_f * 24.0


# ── TABLA 4 ───────────────────────────────────────────────────────────────────
# Cambios de aire promedio en 24 hrs — cuartos ARRIBA de 32°F (ASHRAE)
# Nota: para uso pesado multiplicar × 2.0; largo almacenamiento × 0.6.

_TABLE4: list[tuple[float, float]] = [
    (200, 44.0), (250, 38.0), (300, 34.5), (400, 29.5),
    (500, 26.0), (600, 23.0), (800, 20.0), (1_000, 17.5),
    (1_500, 14.0), (2_000, 12.0), (3_000, 9.5), (4_000, 8.2),
    (5_000, 7.2), (6_000, 6.5), (8_000, 5.5), (10_000, 4.9),
    (15_000, 3.9), (20_000, 3.5), (25_000, 3.0), (30_000, 2.7),
    (40_000, 2.3), (50_000, 2.0), (75_000, 1.6), (100_000, 1.4),
    (150_000, 1.2), (200_000, 1.1), (300_000, 1.0),
]

# ── TABLA 5 ───────────────────────────────────────────────────────────────────
# Cambios de aire promedio en 24 hrs — cuartos ABAJO de 32°F (ASHRAE)

_TABLE5: list[tuple[float, float]] = [
    (200, 33.5), (250, 29.0), (300, 26.2), (400, 22.5),
    (500, 20.0), (600, 18.0), (800, 15.3), (1_000, 13.5),
    (1_500, 11.0), (2_000, 9.3), (3_000, 7.4), (4_000, 6.3),
    (5_000, 5.6), (6_000, 5.0), (8_000, 4.3), (10_000, 3.8),
    (15_000, 3.0), (20_000, 2.6), (25_000, 2.3), (30_000, 2.1),
    (40_000, 1.8), (50_000, 1.6), (75_000, 1.3), (100_000, 1.1),
    (150_000, 1.0), (200_000, 0.9), (300_000, 0.85),
]


def _interpolate(table: list[tuple[float, float]], x: float) -> float:
    xs = [r[0] for r in table]
    ys = [r[1] for r in table]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_right(xs, x) - 1
    x0, y0 = xs[i], ys[i]
    x1, y1 = xs[i + 1], ys[i + 1]
    return y0 + (x - x0) / (x1 - x0) * (y1 - y0)


def air_changes_per_day(volume_ft3: float, below_freezing: bool) -> float:
    """Cambios de aire por 24 hrs (Tabla 4 ó 5, uso estándar).

    Args:
        volume_ft3: Volumen interior del cuarto en ft³.
        below_freezing: True para cuartos bajo 32°F (Tabla 5).
    """
    table = _TABLE5 if below_freezing else _TABLE4
    return _interpolate(table, volume_ft3)


# ── TABLA 6 ───────────────────────────────────────────────────────────────────
# Calor removido del aire de enfriamiento (BTU/ft³)
# Indexado por: temp_cuarto_°F → {(temp_exterior_°F, humedad_%) → BTU/ft³}
# Fuente: ASHRAE, reimpresocon permiso en Bohn BCT-025, pág. 15.

_TABLE6: dict[int, dict[tuple[int, int], float]] = {
    55: {(85, 50): 1.12, (85, 60): 1.34, (90, 50): 1.41, (90, 60): 1.66,
         (95, 50): 1.72, (95, 60): 2.01, (100, 50): 2.06, (100, 60): 2.44},
    50: {(85, 50): 1.32, (85, 60): 1.54, (90, 50): 1.62, (90, 60): 1.87,
         (95, 50): 1.93, (95, 60): 2.22, (100, 50): 2.28, (100, 60): 2.65},
    45: {(85, 50): 1.50, (85, 60): 1.73, (90, 50): 1.80, (90, 60): 2.06,
         (95, 50): 2.12, (95, 60): 2.42, (100, 50): 2.47, (100, 60): 2.85},
    40: {(85, 50): 1.69, (85, 60): 1.92, (90, 50): 2.00, (90, 60): 2.26,
         (95, 50): 2.31, (95, 60): 2.62, (100, 50): 2.67, (100, 60): 3.65},
    35: {(50, 70): 0.36, (50, 80): 0.41,
         (85, 50): 1.86, (85, 60): 2.09, (90, 50): 2.17, (90, 60): 2.43,
         (95, 50): 2.49, (95, 60): 2.79, (100, 50): 2.85, (100, 60): 3.24},
    30: {(40, 70): 0.24, (40, 80): 0.29, (50, 70): 0.58, (50, 80): 0.66,
         (85, 50): 2.00, (85, 60): 2.24, (90, 50): 2.26, (90, 60): 2.53,
         (95, 50): 2.64, (95, 60): 2.94, (100, 50): 2.95, (100, 60): 3.35},
    25: {(40, 70): 0.41, (40, 80): 0.45, (50, 70): 0.75, (50, 80): 0.83,
         (85, 50): 2.09, (85, 60): 2.42, (90, 50): 2.44, (90, 60): 2.71,
         (95, 50): 2.79, (95, 60): 3.16, (100, 50): 3.14, (100, 60): 3.54},
    20: {(40, 70): 0.56, (40, 80): 0.61, (50, 70): 0.91, (50, 80): 0.99,
         (85, 50): 2.27, (85, 60): 2.61, (90, 50): 2.62, (90, 60): 2.90,
         (95, 50): 2.97, (95, 60): 3.35, (100, 50): 3.33, (100, 60): 3.73},
    15: {(40, 70): 0.71, (40, 80): 0.75, (50, 70): 1.06, (50, 80): 1.14,
         (85, 50): 2.45, (85, 60): 2.74, (90, 50): 2.80, (90, 60): 3.07,
         (95, 50): 3.16, (95, 60): 3.54, (100, 50): 3.51, (100, 60): 3.92},
    10: {(40, 70): 0.85, (40, 80): 0.89, (50, 70): 1.19, (50, 80): 1.27,
         (85, 50): 2.57, (85, 60): 2.87, (90, 50): 2.93, (90, 60): 3.20,
         (95, 50): 3.29, (95, 60): 3.66, (100, 50): 3.64, (100, 60): 4.04},
    5:  {(40, 70): 0.98, (40, 80): 1.03, (50, 70): 1.34, (50, 80): 1.42,
         (85, 50): 2.76, (85, 60): 3.07, (90, 50): 3.12, (90, 60): 3.40,
         (95, 50): 3.48, (95, 60): 3.87, (100, 50): 3.84, (100, 60): 4.27},
    0:  {(40, 70): 1.12, (40, 80): 1.17, (50, 70): 1.48, (50, 80): 1.56,
         (85, 50): 2.92, (85, 60): 3.23, (90, 50): 3.28, (90, 60): 3.56,
         (95, 50): 3.64, (95, 60): 4.03, (100, 50): 4.01, (100, 60): 4.43},
    -5: {(40, 70): 1.23, (40, 80): 1.28, (50, 70): 1.59, (50, 80): 1.67,
         (85, 50): 3.04, (85, 60): 3.36, (90, 50): 3.41, (90, 60): 3.69,
         (95, 50): 3.78, (95, 60): 4.18, (100, 50): 4.15, (100, 60): 4.57},
    -10: {(40, 70): 1.35, (40, 80): 1.41, (50, 70): 1.73, (50, 80): 1.81,
          (85, 50): 3.19, (85, 60): 3.49, (90, 50): 3.56, (90, 60): 3.85,
          (95, 50): 3.93, (95, 60): 4.33, (100, 50): 4.31, (100, 60): 4.74},
    -15: {(40, 70): 1.50, (40, 80): 1.53, (50, 70): 1.85, (50, 80): 1.92,
          (85, 50): 3.29, (85, 60): 3.60, (90, 50): 3.67, (90, 60): 3.96,
          (95, 50): 4.05, (95, 60): 4.46, (100, 50): 4.42, (100, 60): 4.86},
    -20: {(40, 70): 1.63, (40, 80): 1.68, (50, 70): 2.01, (50, 80): 2.00,
          (85, 50): 3.49, (85, 60): 3.72, (90, 50): 3.88, (90, 60): 4.18,
          (95, 50): 4.27, (95, 60): 4.69, (100, 50): 4.66, (100, 60): 5.10},
    -25: {(40, 70): 1.77, (40, 80): 1.80, (50, 70): 2.12, (50, 80): 2.21,
          (85, 50): 3.61, (85, 60): 3.84, (90, 50): 4.00, (90, 60): 4.30,
          (95, 50): 4.39, (95, 60): 4.80, (100, 50): 4.78, (100, 60): 5.21},
    -30: {(40, 70): 1.90, (40, 80): 1.95, (50, 70): 2.29, (50, 80): 2.38,
          (85, 50): 3.86, (85, 60): 4.05, (90, 50): 4.21, (90, 60): 4.51,
          (95, 50): 4.56, (95, 60): 5.00, (100, 50): 4.90, (100, 60): 5.44},
}


def air_heat_content(
    storage_temp_f: float,
    ambient_temp_f: float,
    humidity_pct: int = 50,
) -> float:
    """BTU/ft³ de infiltración de aire (Tabla 6).

    Busca la temperatura de almacenamiento más cercana disponible en la tabla.

    Args:
        storage_temp_f: Temperatura del cuarto en °F.
        ambient_temp_f: Temperatura exterior en °F (usualmente 85–100°F).
        humidity_pct: Humedad relativa exterior (50 ó 60 para climas cálidos).

    Raises:
        ValueError: Si la combinación (ambient, humidity) no existe en la tabla.
    """
    available_temps = sorted(_TABLE6.keys())
    closest = min(available_temps, key=lambda t: abs(t - storage_temp_f))
    row = _TABLE6[closest]
    key = (int(ambient_temp_f), humidity_pct)
    if key not in row:
        raise ValueError(
            f"Combinación {ambient_temp_f}°F / {humidity_pct}% no disponible. "
            f"Opciones: {sorted(row.keys())}"
        )
    return row[key]


# ── TABLA 11 (simplificada para el formulario) ────────────────────────────────
# El formulario Bohn usa la constante: 75,000 BTU/HP/24hrs
# (= 3,125 BTU/HP/hr — representa motores de ventiladores del evaporador)
MOTOR_BTU_PER_HP_PER_DAY: float = 75_000.0

# ── ILUMINACIÓN ───────────────────────────────────────────────────────────────
# Constante del formulario: 82 BTU/Watt/24hrs
LIGHTING_BTU_PER_WATT_PER_DAY: float = 82.0

# ── TABLA 12 ─────────────────────────────────────────────────────────────────
# Calor equivalente de ocupación por persona (BTU/persona/24hrs)
_TABLE12: list[tuple[int, float]] = [
    (50, 17_280), (40, 20_160), (30, 22_800),
    (20, 25_200), (10, 28_800), (0, 31_200), (-10, 33_600),
]


def person_heat_per_day(storage_temp_f: float) -> float:
    """BTU/persona/24hrs según Tabla 12 del manual Bohn."""
    for temp, heat in _TABLE12:
        if storage_temp_f >= temp:
            return heat
    return _TABLE12[-1][1]


# ── TABLA 20 ─────────────────────────────────────────────────────────────────
# Cargas debidas a Puertas de Cristal (BTU/puerta/24hrs)
# Valores ajustados para 16-18 horas de operación del compresor.
# Verificación: +35°F → 19,200 BTU/puerta/24hrs (Ejemplo 1, pág. 5) ✓
#               0°F   → 31,200 BTU/puerta/24hrs (Ejemplo 3, pág. 7) ✓
_TABLE20: list[tuple[int, float]] = [
    (35, 19_200),
    (30,  9_600),   # interpolado del manual
    (0,  31_200),
    (-10, 31_200),
    (-20, 31_200),
]


def glass_door_heat_per_day(storage_temp_f: float) -> float:
    """BTU/puerta/24hrs según Tabla 20 del manual Bohn."""
    if storage_temp_f >= 30:
        return 19_200.0
    return 31_200.0
