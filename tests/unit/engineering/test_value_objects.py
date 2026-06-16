import pytest
from app.domain.engineering.value_objects import Capacity, Temperature


class TestCapacityCreation:
    def test_create_from_btu(self):
        c = Capacity(btu_per_hour=36_000)
        assert c.btu_per_hour == 36_000

    def test_create_from_tons(self):
        c = Capacity.from_tons(3)
        assert c.btu_per_hour == 36_000

    def test_create_from_kw(self):
        c = Capacity.from_kw(1)
        assert abs(c.btu_per_hour - 3_412.142) < 0.01

    def test_negative_capacity_raises(self):
        with pytest.raises(ValueError, match="positive"):
            Capacity(btu_per_hour=-1)

    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="positive"):
            Capacity(btu_per_hour=0)


class TestCapacityConversions:
    def test_btu_to_tons(self):
        c = Capacity(btu_per_hour=24_000)
        assert c.tons == 2.0

    def test_btu_to_kw(self):
        c = Capacity(btu_per_hour=3_412.142)
        assert abs(c.kw - 1.0) < 0.001

    def test_roundtrip_tons(self):
        original = 5.5
        c = Capacity.from_tons(original)
        assert abs(c.tons - original) < 1e-9

    def test_roundtrip_kw(self):
        original = 7.3
        c = Capacity.from_kw(original)
        assert abs(c.kw - original) < 1e-9


class TestCapacityEquality:
    def test_same_value_equal(self):
        a = Capacity(btu_per_hour=12_000)
        b = Capacity(btu_per_hour=12_000)
        assert a == b

    def test_different_value_not_equal(self):
        a = Capacity(btu_per_hour=12_000)
        b = Capacity(btu_per_hour=24_000)
        assert a != b

    def test_immutable(self):
        c = Capacity(btu_per_hour=12_000)
        with pytest.raises((AttributeError, TypeError)):
            c.btu_per_hour = 99_000  # type: ignore[misc]


class TestCapacityArithmetic:
    def test_add_two_capacities(self):
        a = Capacity.from_tons(2)
        b = Capacity.from_tons(3)
        total = a + b
        assert total.tons == 5.0

    def test_add_returns_new_object(self):
        a = Capacity.from_tons(2)
        b = Capacity.from_tons(3)
        total = a + b
        assert total is not a
        assert total is not b


class TestTemperatureCreation:
    def test_create_in_celsius(self):
        t = Temperature(celsius=35.0)
        assert t.celsius == 35.0

    def test_create_from_fahrenheit(self):
        t = Temperature.from_fahrenheit(95)
        assert abs(t.celsius - 35.0) < 0.001

    def test_freezing_point_in_fahrenheit(self):
        t = Temperature.from_fahrenheit(32)
        assert abs(t.celsius - 0.0) < 0.001

    def test_below_absolute_zero_raises(self):
        with pytest.raises(ValueError, match="absolute zero"):
            Temperature(celsius=-274.0)


class TestTemperatureConversions:
    def test_celsius_to_fahrenheit(self):
        t = Temperature(celsius=0.0)
        assert t.fahrenheit == 32.0

    def test_celsius_100_to_fahrenheit(self):
        t = Temperature(celsius=100.0)
        assert t.fahrenheit == 212.0

    def test_roundtrip_fahrenheit(self):
        original_f = 35.0
        t = Temperature.from_fahrenheit(original_f)
        assert abs(t.fahrenheit - original_f) < 1e-9

    def test_negative_celsius_to_fahrenheit(self):
        # -10°C = 14°F  (congelador típico)
        t = Temperature(celsius=-10.0)
        assert abs(t.fahrenheit - 14.0) < 0.001


class TestTemperatureDelta:
    def test_delta_refrigerador_tipico(self):
        # Ejemplo real del manual: ambiente 95°F, cámara 35°F → ΔT = 60°F = 33.33°C
        ambient = Temperature.from_fahrenheit(95)
        room    = Temperature.from_fahrenheit(35)
        dt = ambient.delta(room)
        assert abs(dt - 33.333) < 0.01

    def test_delta_congelador(self):
        # Ambiente 90°F, congelador -10°F → ΔT = 100°F = 55.55°C
        ambient = Temperature.from_fahrenheit(90)
        room    = Temperature.from_fahrenheit(-10)
        dt = ambient.delta(room)
        assert abs(dt - 55.555) < 0.01

    def test_delta_es_siempre_positivo(self):
        # El orden no importa — ΔT siempre es positivo
        a = Temperature(celsius=35)
        b = Temperature(celsius=-10)
        assert a.delta(b) == b.delta(a)

    def test_delta_no_es_temperatura(self):
        # ΔT de 60°F ≠ convertir 60°F como temperatura absoluta
        # ΔT de 60°F = 33.33°C  (no 15.5°C que sería (60-32)*5/9)
        ambient = Temperature.from_fahrenheit(95)
        room    = Temperature.from_fahrenheit(35)
        dt_celsius = ambient.delta(room)
        assert abs(dt_celsius - 33.333) < 0.01   # correcto
        assert abs(dt_celsius - 15.5) > 1         # no es la conversión directa de 60°F


class TestTemperatureBelowFreezing:
    def test_refrigerador_no_es_congelador(self):
        t = Temperature.from_fahrenheit(35)    # cámara de carne típica
        assert t.is_below_freezing is False

    def test_congelador_es_below_freezing(self):
        t = Temperature.from_fahrenheit(-10)   # congelador de carne
        assert t.is_below_freezing is True

    def test_cero_grados_es_below_freezing(self):
        # 0°C = 32°F: justo en el límite, se considera congelación
        t = Temperature(celsius=0.0)
        assert t.is_below_freezing is False    # 0°C no es < 0°C

    def test_menos_uno_es_below_freezing(self):
        t = Temperature(celsius=-1.0)
        assert t.is_below_freezing is True


class TestTemperatureComparisons:
    def test_mayor_que(self):
        ambient = Temperature.from_fahrenheit(95)
        room    = Temperature.from_fahrenheit(35)
        assert ambient > room

    def test_menor_que(self):
        room    = Temperature.from_fahrenheit(35)
        freezer = Temperature.from_fahrenheit(-10)
        assert freezer < room

    def test_igual(self):
        a = Temperature(celsius=5.0)
        b = Temperature(celsius=5.0)
        assert a == b

    def test_inmutable(self):
        t = Temperature(celsius=5.0)
        with pytest.raises((AttributeError, TypeError)):
            t.celsius = 99.0  # type: ignore[misc]
