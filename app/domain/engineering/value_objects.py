from dataclasses import dataclass

# Factores de conversión estándar ASHRAE
_BTU_PER_TON = 12_000.0      # 1 tonelada de refrigeración = 12 000 BTU/h
_BTU_PER_KW = 3_412.142       # 1 kW = 3 412.142 BTU/h


@dataclass(frozen=True)
class Capacity:
    """Capacidad térmica de refrigeración, almacenada internamente en BTU/h."""

    btu_per_hour: float

    def __post_init__(self) -> None:
        if self.btu_per_hour <= 0:
            raise ValueError(
                f"Capacity must be positive, got {self.btu_per_hour} BTU/h"
            )

    # ── Constructores alternativos ──────────────────────────────────────────

    @classmethod
    def from_tons(cls, tons: float) -> "Capacity":
        return cls(btu_per_hour=tons * _BTU_PER_TON)

    @classmethod
    def from_kw(cls, kw: float) -> "Capacity":
        return cls(btu_per_hour=kw * _BTU_PER_KW)

    # ── Conversiones de salida ──────────────────────────────────────────────

    @property
    def tons(self) -> float:
        return self.btu_per_hour / _BTU_PER_TON

    @property
    def kw(self) -> float:
        return self.btu_per_hour / _BTU_PER_KW

    # ── Aritmética (devuelve un nuevo Capacity, no muta) ───────────────────

    def __add__(self, other: "Capacity") -> "Capacity":
        return Capacity(self.btu_per_hour + other.btu_per_hour)

    def __repr__(self) -> str:
        return f"Capacity({self.tons:.2f} tons | {self.btu_per_hour:.0f} BTU/h | {self.kw:.2f} kW)"


# ── Límite físico absoluto ─────────────────────────────────────────────────────
_ABSOLUTE_ZERO_C = -273.15


@dataclass(frozen=True)
class Temperature:
    """Temperatura almacenada internamente en °C (unidad SI)."""

    celsius: float

    def __post_init__(self) -> None:
        if self.celsius < _ABSOLUTE_ZERO_C:
            raise ValueError(
                f"Temperature below absolute zero: {self.celsius}°C"
            )

    # ── Constructores alternativos ─────────────────────────────────────────────

    @classmethod
    def from_fahrenheit(cls, fahrenheit: float) -> "Temperature":
        return cls(celsius=(fahrenheit - 32) * 5 / 9)

    # ── Conversiones de salida ─────────────────────────────────────────────────

    @property
    def fahrenheit(self) -> float:
        return self.celsius * 9 / 5 + 32

    # ── Operaciones de dominio ─────────────────────────────────────────────────

    def delta(self, other: "Temperature") -> float:
        """Diferencial ΔT en °C entre dos temperaturas (siempre positivo).

        Un ΔT no es una temperatura absoluta, por eso devuelve float.
        ΔT de 60°F = ΔT de 33.3°C (no se convierte como temperatura absoluta).
        """
        return abs(self.celsius - other.celsius)

    @property
    def is_below_freezing(self) -> bool:
        """True si la temperatura está por debajo de 0°C (32°F).

        Determina si aplica Tabla 4 (>0°C) o Tabla 5 (<0°C) del manual Frigus Bohn.
        """
        return self.celsius < 0.0

    # ── Comparaciones ──────────────────────────────────────────────────────────

    def __lt__(self, other: "Temperature") -> bool:
        return self.celsius < other.celsius

    def __le__(self, other: "Temperature") -> bool:
        return self.celsius <= other.celsius

    def __gt__(self, other: "Temperature") -> bool:
        return self.celsius > other.celsius

    def __ge__(self, other: "Temperature") -> bool:
        return self.celsius >= other.celsius

    def __repr__(self) -> str:
        return f"Temperature({self.celsius:.2f}°C | {self.fahrenheit:.2f}°F)"
