"""
Tests del calculador de carga de refrigeración.
Validados contra los 4 ejemplos del manual Frigus Bohn BCT-025-H-ENG-1APM.

Ejemplos del manual:
  Ej-1: Refrigerador tienda de conveniencia 35°F  (H-ENG-2.1, pág. 5)
  Ej-2: Refrigerador de carne 35°F               (H-ENG-2.1, pág. 6)
  Ej-3: Congelador endurecimiento de helado -20°F (H-ENG-3.1, pág. 7)
  Ej-4: Congelador de carne -10°F                 (H-ENG-3.1, pág. 8)
"""
import pytest
from app.domain.engineering.entities import (
    InsulationSpec, RoomDimensions, WallInsulation,
    ProductLoad, MiscLoads, RoomInput,
)
from app.domain.engineering.services import RefrigerationLoadCalculator
from app.domain.engineering import tables


CALC = RefrigerationLoadCalculator()
TOLERANCE = 0.03  # 3% — diferencias mínimas por redondeo en la tabla impresa


# ── Tests de Tabla 1 (factores de transmisión) ────────────────────────────────

def test_tabla1_polystyrene_4in_dt50():
    """4" Estireno, ΔT=50°F → 72 BTU/24hr/ft² (Ejemplo 1, pág. 5)."""
    factor = tables.wall_heat_load_factor(k=0.24, thickness_in=4, delta_t_f=50)
    assert abs(factor - 72) < 1.0, f"Esperado ≈72, obtenido {factor:.1f}"


def test_tabla1_polystyrene_4in_dt60():
    """4" Estireno, ΔT=60°F → 87 BTU/24hr/ft² (Ejemplo 2, pág. 6)."""
    factor = tables.wall_heat_load_factor(k=0.24, thickness_in=4, delta_t_f=60)
    assert abs(factor - 87) < 1.0, f"Esperado ≈87, obtenido {factor:.1f}"


def test_tabla1_urethane_4in_dt105():
    """4" Uretano, ΔT=105°F → 76 BTU/24hr/ft² (Ejemplo 3, pág. 7)."""
    factor = tables.wall_heat_load_factor(k=0.12, thickness_in=4, delta_t_f=105)
    assert abs(factor - 75.6) < 1.0, f"Esperado ≈75.6, obtenido {factor:.1f}"


def test_tabla1_concrete_floor_dt25():
    """Piso concreto 6", ΔT=25°F → 125 BTU/24hr/ft² (Ejemplo 1, pág. 5)."""
    factor = tables.concrete_floor_heat_load_factor(delta_t_f=25)
    assert abs(factor - 125) < 1.0, f"Esperado ≈125, obtenido {factor:.1f}"


# ── Tests de Tablas 4 y 5 (cambios de aire) ───────────────────────────────────

def test_tabla4_interpolation_1792ft3():
    """1,792 ft³ sobre 32°F → ~12.83 cambios/día (base para Ejemplo 2)."""
    changes = tables.air_changes_per_day(1792, below_freezing=False)
    assert abs(changes - 12.83) < 0.5, f"Esperado ≈12.83, obtenido {changes:.2f}"


def test_tabla5_interpolation_1344ft3():
    """1,344 ft³ bajo 32°F → 12 cambios/día (Ejemplo 3, pág. 7)."""
    changes = tables.air_changes_per_day(1344, below_freezing=True)
    assert abs(changes - 12) < 0.5, f"Esperado ≈12, obtenido {changes:.2f}"


def test_tabla5_interpolation_5760ft3():
    """5,760 ft³ bajo 32°F → 5.2 cambios/día (Ejemplo 4, pág. 8)."""
    changes = tables.air_changes_per_day(5760, below_freezing=True)
    assert abs(changes - 5.2) < 0.3, f"Esperado ≈5.2, obtenido {changes:.2f}"


# ── Tests de Tabla 6 (calor por ft³ de infiltración) ─────────────────────────

def test_tabla6_35f_85f_50pct():
    """35°F cuarto, 85°F ext, 50% HR → 1.86 BTU/ft³ (Ejemplo 1)."""
    val = tables.air_heat_content(35, 85, 50)
    assert val == 1.86


def test_tabla6_35f_95f_50pct():
    """35°F cuarto, 95°F ext, 50% HR → 2.49 BTU/ft³ (Ejemplo 2)."""
    val = tables.air_heat_content(35, 95, 50)
    assert val == 2.49


def test_tabla6_minus20f_85f_50pct():
    """-20°F cuarto, 85°F ext, 50% HR → 3.49 BTU/ft³ (Ejemplo 3)."""
    val = tables.air_heat_content(-20, 85, 50)
    assert val == 3.49


def test_tabla6_minus10f_90f_60pct():
    """-10°F cuarto, 90°F ext, 60% HR → 3.85 BTU/ft³ (Ejemplo 4)."""
    val = tables.air_heat_content(-10, 90, 60)
    assert val == 3.85


# ── Ejemplo 1 completo: Refrigerador de Tienda de Conveniencia 35°F ───────────
# Fuente: Manual Bohn BCT-025, pág. 5

@pytest.fixture
def room_ejemplo1() -> RoomInput:
    """Refrigerador de tienda de conveniencia a 35°F, 28×8×8 ft."""
    styrene_4in = InsulationSpec(k_value=0.24, thickness_in=4)
    concrete_floor = InsulationSpec(is_concrete_floor=True)
    return RoomInput(
        dimensions=RoomDimensions(length_ft=28, width_ft=8, height_ft=8),
        insulation=WallInsulation(
            roof=styrene_4in, north=styrene_4in, south=styrene_4in,
            east=styrene_4in, west=styrene_4in, floor=concrete_floor,
        ),
        storage_temp_f=35,
        ambient_temp_f=85,
        floor_ambient_temp_f=60,
        ambient_humidity_pct=50,
        products=[
            ProductLoad(
                daily_lbs=2000, entry_temp_f=85, storage_temp_f=35,
                specific_heat_above=0.9,
            ),
            ProductLoad(
                daily_lbs=200, entry_temp_f=40, storage_temp_f=35,
                specific_heat_above=0.7,
            ),
        ],
        misc=MiscLoads(
            motor_hp=0.2,
            lighting_watts=224,
            num_persons=0,
            num_glass_doors=10,
        ),
        operating_hours=16,
        air_changes_multiplier=1.5,   # tienda de conveniencia = uso pesado
    )


def test_ejemplo1_seccion1_transmision(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 16128+16128+16128+4608+4608+28000 = 85,600
    assert abs(result.transmission.total - 85_600) < 85_600 * TOLERANCE


def test_ejemplo1_seccion2_aire(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 1792 × 19.5 × 1.86 = 64,996 (con multiplicador 1.5)
    assert abs(result.air_infiltration_btu - 64_996) < 64_996 * TOLERANCE


def test_ejemplo1_seccion3_miscelaneos(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 15000 + 18368 + 0 + 192000 = 225,368
    assert abs(result.miscellaneous_btu - 225_368) < 225_368 * TOLERANCE


def test_ejemplo1_seccion4_producto(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 2000×0.9×50 + 200×0.7×5 = 90000 + 700 = 90,700
    assert abs(result.product_sensible_btu - 90_700) < 90_700 * TOLERANCE


def test_ejemplo1_total_btu_dia(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 466,664 × 1.10 = 513,330
    assert abs(result.total_btu_per_day - 513_330) < 513_330 * TOLERANCE


def test_ejemplo1_btuh(room_ejemplo1):
    result = CALC.calculate(room_ejemplo1)
    # Manual: 513,330 / 16 hrs = 32,083 BTU/hr
    assert abs(result.btuh_required - 32_083) < 32_083 * TOLERANCE


# ── Ejemplo 2 completo: Refrigerador de Carne 35°F ───────────────────────────
# Fuente: Manual Bohn BCT-025, pág. 6

@pytest.fixture
def room_ejemplo2() -> RoomInput:
    """Refrigerador de carne a 35°F, 16×14×8 ft."""
    styrene_4in = InsulationSpec(k_value=0.24, thickness_in=4)
    concrete_floor = InsulationSpec(is_concrete_floor=True)
    return RoomInput(
        dimensions=RoomDimensions(length_ft=16, width_ft=14, height_ft=8),
        insulation=WallInsulation(
            roof=styrene_4in, north=styrene_4in, south=styrene_4in,
            east=styrene_4in, west=styrene_4in, floor=concrete_floor,
        ),
        storage_temp_f=35,
        ambient_temp_f=95,
        floor_ambient_temp_f=60,
        ambient_humidity_pct=50,
        products=[
            ProductLoad(
                daily_lbs=1000, entry_temp_f=50, storage_temp_f=35,
                specific_heat_above=0.77,
            ),
        ],
        misc=MiscLoads(motor_hp=0.1, lighting_watts=224, num_persons=0),
        operating_hours=16,
        air_changes_multiplier=1.0,
    )


def test_ejemplo2_seccion1_transmision(room_ejemplo2):
    result = CALC.calculate(room_ejemplo2)
    # Manual: 19488+11136+11136+9744+9744+28000 = 89,248
    assert abs(result.transmission.total - 89_248) < 89_248 * TOLERANCE


def test_ejemplo2_seccion2_aire(room_ejemplo2):
    result = CALC.calculate(room_ejemplo2)
    # Manual: 1792 × 13 × 2.49 = 58,007
    assert abs(result.air_infiltration_btu - 58_007) < 58_007 * TOLERANCE


def test_ejemplo2_total_btu_dia(room_ejemplo2):
    result = CALC.calculate(room_ejemplo2)
    # Manual: 184,673 × 1.10 = 203,140
    assert abs(result.total_btu_per_day - 203_140) < 203_140 * TOLERANCE
