"""
Servicio de dominio: calcula la carga de refrigeración siguiendo
el método del formulario Frigus Bohn H-ENG-2.1 (arriba de 32°F)
y H-ENG-3.1 (abajo de 32°F).

Las 5 fuentes de calor son exactamente las 5 secciones del formulario:
  1. Transmisión por paredes/techo/piso
  2. Cambios de aire (infiltración)
  3. Cargas misceláneas (motores, luces, personas, puertas)
  4. Carga sensible del producto
  5. Respiración (solo productos frescos — se agrega externamente)
"""
from dataclasses import dataclass

from app.domain.engineering.entities import RoomInput, ProductLoad
from app.domain.engineering import tables


@dataclass(frozen=True)
class TransmissionDetail:
    """Desglose de la Sección 1 por superficie."""
    roof_btu: float
    north_btu: float
    south_btu: float
    east_btu: float
    west_btu: float
    floor_btu: float

    @property
    def total(self) -> float:
        return (self.roof_btu + self.north_btu + self.south_btu
                + self.east_btu + self.west_btu + self.floor_btu)


@dataclass(frozen=True)
class LoadCalculationResult:
    """Resultado completo del cálculo — equivale al formulario llenado.

    Todos los valores en BTU/24hrs salvo btuh_required.
    """
    # ── Secciones del formulario ──────────────────────────────────────────────
    transmission: TransmissionDetail    # Sección 1
    air_infiltration_btu: float         # Sección 2
    miscellaneous_btu: float            # Sección 3
    product_sensible_btu: float         # Sección 4
    product_respiration_btu: float      # Sección 5

    # ── Totales ───────────────────────────────────────────────────────────────
    operating_hours: float

    @property
    def subtotal_btu(self) -> float:
        return (self.transmission.total
                + self.air_infiltration_btu
                + self.miscellaneous_btu
                + self.product_sensible_btu
                + self.product_respiration_btu)

    @property
    def safety_factor_btu(self) -> float:
        """10% adicional por factor de seguridad (Bohn BCT-025, sección 5)."""
        return self.subtotal_btu * 0.10

    @property
    def total_btu_per_day(self) -> float:
        """Total BTU/24hrs con factor de seguridad del 10%."""
        return self.subtotal_btu + self.safety_factor_btu

    @property
    def btuh_required(self) -> float:
        """Capacidad requerida en BTU/hr — base para selección de equipo."""
        return self.total_btu_per_day / self.operating_hours


class RefrigerationLoadCalculator:
    """Calcula la carga de refrigeración según el método Frigus Bohn.

    Uso:
        calc = RefrigerationLoadCalculator()
        result = calc.calculate(room_input)
    """

    def calculate(
        self,
        room: RoomInput,
        respiration_btu: float = 0.0,
    ) -> LoadCalculationResult:
        """Ejecuta el cálculo completo de las 5 secciones.

        Args:
            room: Todos los datos de entrada del formulario.
            respiration_btu: Sección 5 — calor de respiración BTU/24hrs.
                             Solo para frutas/vegetales frescos (Tabla 8).
                             El llamador calcula: lbs_almacenadas × BTU/lb/24hrs.

        Returns:
            LoadCalculationResult con todas las secciones y el BTU/hr final.
        """
        transmission = self._section1_transmission(room)
        air_infiltration = self._section2_air_infiltration(room)
        misc = self._section3_miscellaneous(room)
        product_sensible = self._section4_product_sensible(room)

        return LoadCalculationResult(
            transmission=transmission,
            air_infiltration_btu=air_infiltration,
            miscellaneous_btu=misc,
            product_sensible_btu=product_sensible,
            product_respiration_btu=respiration_btu,
            operating_hours=room.operating_hours,
        )

    # ── Sección 1: Transmisión ────────────────────────────────────────────────

    def _section1_transmission(self, room: RoomInput) -> TransmissionDetail:
        dims = room.dimensions
        ins = room.insulation
        dt_walls = room.delta_t_walls_f
        dt_floor = room.delta_t_floor_f

        def surface_load(insulation, area_ft2: float, delta_t: float) -> float:
            if insulation.is_concrete_floor:
                factor = tables.concrete_floor_heat_load_factor(delta_t)
            else:
                factor = tables.wall_heat_load_factor(
                    insulation.k_value, insulation.thickness_in, delta_t
                )
            return area_ft2 * factor

        roof_area = dims.length_ft * dims.width_ft
        north_south_area = dims.length_ft * dims.height_ft
        east_west_area = dims.width_ft * dims.height_ft
        floor_area = dims.length_ft * dims.width_ft

        return TransmissionDetail(
            roof_btu=surface_load(ins.roof, roof_area, dt_walls),
            north_btu=surface_load(ins.north, north_south_area, dt_walls),
            south_btu=surface_load(ins.south, north_south_area, dt_walls),
            east_btu=surface_load(ins.east, east_west_area, dt_walls),
            west_btu=surface_load(ins.west, east_west_area, dt_walls),
            floor_btu=surface_load(ins.floor, floor_area, dt_floor),
        )

    # ── Sección 2: Cambios de Aire ────────────────────────────────────────────

    def _section2_air_infiltration(self, room: RoomInput) -> float:
        volume = room.dimensions.volume_ft3
        changes = tables.air_changes_per_day(volume, room.is_below_freezing)
        changes *= room.air_changes_multiplier
        heat_per_ft3 = tables.air_heat_content(
            room.storage_temp_f,
            room.ambient_temp_f,
            room.ambient_humidity_pct,
        )
        return volume * changes * heat_per_ft3

    # ── Sección 3: Cargas Misceláneas ─────────────────────────────────────────

    def _section3_miscellaneous(self, room: RoomInput) -> float:
        m = room.misc
        motor = m.motor_hp * tables.MOTOR_BTU_PER_HP_PER_DAY
        lighting = m.lighting_watts * tables.LIGHTING_BTU_PER_WATT_PER_DAY
        persons = m.num_persons * tables.person_heat_per_day(room.storage_temp_f)
        doors = m.num_glass_doors * tables.glass_door_heat_per_day(room.storage_temp_f)
        return motor + lighting + persons + doors

    # ── Sección 4: Carga Sensible del Producto ────────────────────────────────

    def _section4_product_sensible(self, room: RoomInput) -> float:
        total = 0.0
        for product in room.products:
            total += self._product_heat(product, room.storage_temp_f)
        return total

    def _product_heat(self, product: ProductLoad, storage_temp_f: float) -> float:
        """BTU/24hrs para un producto según si cruza el punto de congelación."""
        is_above = product.entry_temp_f > 32.0 and storage_temp_f >= 32.0

        if is_above or product.freezing_point_f is None:
            # Caso simple (H-ENG-2.1): todo sensible, sin congelación
            delta_t = product.entry_temp_f - storage_temp_f
            return product.daily_lbs * product.specific_heat_above * delta_t

        # Caso con congelación (H-ENG-3.1): 3 etapas
        fp = product.freezing_point_f

        # Etapa 1: desde entrada hasta el punto de congelación (sensible, arriba)
        heat_above = (product.daily_lbs
                      * product.specific_heat_above
                      * (product.entry_temp_f - fp))

        # Etapa 2: calor latente de fusión
        heat_latent = product.daily_lbs * product.latent_heat_btu_lb

        # Etapa 3: desde punto de congelación hasta temperatura final (sensible, abajo)
        heat_below = (product.daily_lbs
                      * product.specific_heat_below
                      * (fp - storage_temp_f))

        return heat_above + heat_latent + heat_below
