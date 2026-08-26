"""Tests for deterministic signal generation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from simulator.signals import SIM_TAG, SignalGenerator, sensor_description, is_sim_sensor, THRESHOLDS

ALL_TYPES = [
    "air_temperature",
    "soil_temperature",
    "air_humidity",
    "soil_humidity",
    "co2",
    "ph",
    "light_intensity",
]

BOUNDS = {
    "air_temperature": (8.0, 38.0),
    "soil_temperature": (10.0, 32.0),
    "air_humidity": (38.0, 96.0),
    "soil_humidity": (20.0, 68.0),
    "co2": (380.0, 1100.0),
    "ph": (5.8, 6.9),
    "light_intensity": (0.0, 98000.0),
}


def sample_day(sensor_type: str, description: str, start=None, step_minutes=15):
    gen = SignalGenerator(sensor_type, description)
    start = start or datetime(2026, 6, 15, 0, 0, tzinfo=timezone.utc)
    return [
        (start + timedelta(minutes=i * step_minutes), gen.value_at(start + timedelta(minutes=i * step_minutes)))
        for i in range(24 * 60 // step_minutes)
    ]


class TestNaming:
    def test_description_contains_sim_tag(self):
        assert SIM_TAG in sensor_description("air_temperature", 1)

    def test_is_sim_sensor_matches(self):
        assert is_sim_sensor(sensor_description("co2", 3))
        assert not is_sim_sensor("Canopy probe, middle row")

    def test_unknown_type_raises(self):
        gen = SignalGenerator("not_specified", "x · [sim]")
        with pytest.raises(ValueError):
            gen.value_at(datetime.now(timezone.utc))


class TestDeterminism:
    def test_same_input_same_value(self):
        dt = datetime(2026, 6, 15, 12, 30, tzinfo=timezone.utc)
        a = SignalGenerator("air_temperature", "Air temperature #1 · [sim]")
        b = SignalGenerator("air_temperature", "Air temperature #1 · [sim]")
        assert a.value_at(dt) == b.value_at(dt)

    def test_different_descriptions_diverge(self):
        dt = datetime(2026, 6, 15, 12, 30, tzinfo=timezone.utc)
        a = SignalGenerator("air_temperature", "Air temperature #1 · [sim]")
        b = SignalGenerator("air_temperature", "Air temperature #2 · [sim]")
        values_a = [a.value_at(dt + timedelta(minutes=m)) for m in range(0, 600, 5)]
        values_b = [b.value_at(dt + timedelta(minutes=m)) for m in range(0, 600, 5)]
        assert values_a != values_b

    def test_naive_datetime_treated_as_utc(self):
        naive = datetime(2026, 6, 15, 12, 30)
        aware = naive.replace(tzinfo=timezone.utc)
        gen = SignalGenerator("ph", "pH #1 · [sim]")
        assert gen.value_at(naive) == gen.value_at(aware)


class TestRealism:
    @pytest.mark.parametrize("sensor_type", ALL_TYPES)
    def test_values_stay_in_bounds(self, sensor_type):
        samples = sample_day(sensor_type, f"{sensor_description(sensor_type, 1)}")
        lo, hi = BOUNDS[sensor_type]
        for _, v in samples:
            assert lo <= v <= hi, f"{sensor_type} out of bounds: {v}"

    def test_light_zero_at_night_positive_midday(self):
        samples = sample_day("light_intensity", sensor_description("light_intensity", 1))
        night = [v for dt, v in samples if dt.hour in (0, 1, 23)]
        noon = [v for dt, v in samples if dt.hour in (11, 12, 13)]
        assert all(v == 0 for v in night)
        assert min(noon) > 10000

    def test_air_temperature_peaks_afternoon(self):
        samples = sample_day("air_temperature", sensor_description("air_temperature", 1))
        by_hour = {}
        for dt, v in samples:
            by_hour.setdefault(dt.hour, []).append(v)
        night_avg = sum(sum(by_hour[h]) / len(by_hour[h]) for h in (2, 3, 4)) / 3
        day_avg = sum(sum(by_hour[h]) / len(by_hour[h]) for h in (14, 15)) / 2
        assert day_avg > night_avg + 1.0

    def test_soil_humidity_sawtooth_drains_then_jumps(self):
        # One full drain cycle spans 29h; sample across two cycles.
        gen = SignalGenerator("soil_humidity", sensor_description("soil_humidity", 1))
        start = datetime(2026, 6, 15, 7, 0, tzinfo=timezone.utc)
        series = [gen.value_at(start + timedelta(minutes=m * 30)) for m in range(62)]
        # Within the first 28h the trend must be downward overall.
        assert series[0] > series[-48]  # after ~24h it drained
        # And it resets upward at some point within the next hours.
        assert max(series[48:]) > min(series[:24])

    def test_co2_and_light_anticorrelated(self):
        light = sample_day("light_intensity", sensor_description("light_intensity", 1))
        co2 = sample_day("co2", sensor_description("co2", 1))
        mid = lambda samples: [v for dt, v in samples if 11 <= dt.hour <= 13]
        night = lambda samples: [v for dt, v in samples if dt.hour in (0, 23)]
        assert sum(mid(co2)) / len(mid(co2)) < sum(night(co2)) / len(night(co2))

    def test_ph_stays_near_neutral(self):
        samples = sample_day("ph", sensor_description("ph", 1))
        values = [v for _, v in samples]
        assert abs(sum(values) / len(values) - 6.3) < 0.05


class TestThresholdConfig:
    def test_every_type_has_band_or_explicit_none(self):
        for stype in ALL_TYPES:
            assert stype in THRESHOLDS
