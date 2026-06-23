"""
Entidades de entrada para el cálculo de carga de refrigeración.
Corresponden exactamente a los campos del formulario Bohn H-ENG-2.1 / H-ENG-3.1.

Analogía con CAD: cada dataclass es un "ensamble" con sus parámetros.
RoomInput es el ensamble principal; los demás son sub-ensambles que agrupa.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class InsulationSpec:
    """Especificación de aislamiento para una superficie.

    Args:
        k_value: Conductividad térmica (BTU·in/hr·ft²·°F). Ver tables.INSULATION_K.
        thickness_in: Espesor en pulgadas.
        is_concrete_floor: True si es piso de concreto sin aislamiento adicional.
    """
    k_value: float = 0.24
    thickness_in: float = 4.0
    is_concrete_floor: bool = False

    def __post_init__(self) -> None:
        if not self.is_concrete_floor and self.thickness_in <= 0:
            raise ValueError("El espesor debe ser positivo.")
        if not self.is_concrete_floor and self.k_value <= 0:
            raise ValueError("El valor K debe ser positivo.")


@dataclass(frozen=True)
class RoomDimensions:
    """Dimensiones interiores del cuarto en pies."""
    length_ft: float
    width_ft: float
    height_ft: float

    def __post_init__(self) -> None:
        for name, val in [("length", self.length_ft), ("width", self.width_ft),
                          ("height", self.height_ft)]:
            if val <= 0:
                raise ValueError(f"{name} debe ser positivo, recibido: {val}")

    @property
    def volume_ft3(self) -> float:
        return self.length_ft * self.width_ft * self.height_ft


@dataclass(frozen=True)
class WallInsulation:
    """Aislamiento de cada superficie del cuarto.

    north/south = paredes paralelas al ancho (L × H)
    east/west   = paredes paralelas al largo (W × H)
    roof        = techo (L × W)
    floor       = piso (L × W)
    """
    roof: InsulationSpec
    north: InsulationSpec
    south: InsulationSpec
    east: InsulationSpec
    west: InsulationSpec
    floor: InsulationSpec


@dataclass(frozen=True)
class ProductLoad:
    """Carga del producto — corresponde a las líneas (a) y (b) del formulario.

    Args:
        daily_lbs: Libras de producto que ingresan por día.
        entry_temp_f: Temperatura de entrada del producto en °F.
        storage_temp_f: Temperatura final de almacenamiento en °F.
        specific_heat_above: Calor específico sobre el punto de congelación
                             (BTU/lb/°F). De Tabla 7 del manual.
        specific_heat_below: Calor específico bajo el punto de congelación
                             (BTU/lb/°F). Solo para cuartos bajo 32°F.
        freezing_point_f: Punto de congelación del producto en °F.
                          Solo necesario para cuartos bajo 32°F.
        latent_heat_btu_lb: Calor latente de fusión (BTU/lb). Solo bajo 32°F.
    """
    daily_lbs: float
    entry_temp_f: float
    storage_temp_f: float
    specific_heat_above: float

    specific_heat_below: float = 0.0
    freezing_point_f: float | None = None
    latent_heat_btu_lb: float = 0.0

    def __post_init__(self) -> None:
        if self.daily_lbs < 0:
            raise ValueError("daily_lbs no puede ser negativo.")
        if self.specific_heat_above <= 0:
            raise ValueError("specific_heat_above debe ser positivo.")


@dataclass(frozen=True)
class MiscLoads:
    """Cargas misceláneas — Sección 3 del formulario.

    Args:
        motor_hp: Potencia total de motores eléctricos en HP.
        lighting_watts: Watts de iluminación instalada.
        num_persons: Número de personas que trabajan en el cuarto.
        num_glass_doors: Número de puertas de cristal (Tabla 20).
    """
    motor_hp: float = 0.0
    lighting_watts: float = 0.0
    num_persons: int = 0
    num_glass_doors: int = 0


@dataclass(frozen=True)
class RoomInput:
    """Datos completos de entrada para el cálculo — equivale al formulario completo.

    Args:
        dimensions: Dimensiones del cuarto.
        insulation: Aislamiento de cada superficie.
        storage_temp_f: Temperatura de almacenamiento del cuarto en °F.
        ambient_temp_f: Temperatura ambiente exterior corregida por carga solar en °F.
        floor_ambient_temp_f: Temperatura del piso (de Tabla 21 o medición local) en °F.
        ambient_humidity_pct: Humedad relativa exterior (50 ó 60). Default 50%.
        products: Lista de productos que entran al cuarto cada día.
        misc: Cargas misceláneas (motores, iluminación, personas, puertas).
        operating_hours: Horas de operación del compresor por día.
                         16 hrs para refrigeradores, 18-20 hrs para congeladores.
        air_changes_multiplier: Multiplicador de cambios de aire.
                                1.0 = uso estándar, 2.0 = uso pesado (Nota Tabla 4/5).
    """
    dimensions: RoomDimensions
    insulation: WallInsulation
    storage_temp_f: float
    ambient_temp_f: float
    floor_ambient_temp_f: float

    ambient_humidity_pct: int = 50
    products: list[ProductLoad] = field(default_factory=list)
    misc: MiscLoads = field(default_factory=MiscLoads)
    operating_hours: float = 16.0
    air_changes_multiplier: float = 1.0

    @property
    def is_below_freezing(self) -> bool:
        return self.storage_temp_f < 32.0

    @property
    def delta_t_walls_f(self) -> float:
        """ΔT para paredes y techo (ambiente − cuarto)."""
        return self.ambient_temp_f - self.storage_temp_f

    @property
    def delta_t_floor_f(self) -> float:
        """ΔT para el piso (temp piso − cuarto)."""
        return self.floor_ambient_temp_f - self.storage_temp_f
