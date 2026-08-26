"""Deterministic, realistic signal generators per sensor type.

Every value is a pure function of (sensor description seed, timestamp),
so the backfill phase and the live loop produce a consistent world and
re-runs are reproducible.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone

SIM_TAG = "[sim]"

# Human-readable labels used in sensor descriptions.
TYPE_LABELS = {
    "air_temperature": "Air temperature",
    "air_humidity": "Air humidity",
    "soil_temperature": "Soil temperature",
    "soil_humidity": "Soil moisture",
    "co2": "CO2",
    "ph": "pH",
    "light_intensity": "Light intensity",
}

# Catalog profiles created/looked up by the initializer.
PROFILES = {
    "air_temperature": ("DS18B20", "celsius", 300.0, "Dallas 1-Wire waterproof digital temperature sensor"),
    "soil_temperature": ("DS18B20 Soil", "celsius", 300.0, "Waterproof soil temperature probe"),
    "air_humidity": ("SHT31", "percent", 300.0, "Digital relative humidity sensor"),
    "soil_humidity": ("Resistive Soil Probe", "percent", 300.0, "Resistive soil moisture probe"),
    "co2": ("MH-Z19 NDIR", "ppm", 300.0, "NDIR CO2 sensor module"),
    "ph": ("PH-4502C", "ph", 300.0, "Analog pH probe with breakout board"),
    "light_intensity": ("BH1750", "ppm", 300.0, "Digital light intensity sensor"),
}

# Banded alert thresholds seeded during initialization.
# None means: do not create thresholds for this type (e.g. light swings
# naturally between day and night; static bands would be meaningless).
THRESHOLDS = {
    "air_temperature": (18.0, 27.0, 10.0, 38.0),
    "soil_temperature": (15.0, 24.0, 10.0, 30.0),
    "air_humidity": (55.0, 78.0, 40.0, 90.0),
    "soil_humidity": (35.0, 60.0, 25.0, 70.0),
    "co2": (400.0, 1000.0, 350.0, 1500.0),
    "ph": (5.5, 6.8, 5.0, 7.5),
    "light_intensity": None,
}


def sensor_description(sensor_type: str, index: int) -> str:
    return f"{TYPE_LABELS[sensor_type]} #{index} · {SIM_TAG}"


def is_sim_sensor(description: str) -> bool:
    return SIM_TAG in description


def _seed(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()[:16]


def _noise(seed: str, key: str, bucket: int) -> float:
    """Deterministic pseudo-noise in [-1, 1] for a given key/bucket."""
    digest = hashlib.sha256(f"{seed}|{key}|{bucket}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**63 - 1


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class SignalGenerator:
    """Generates plausible environmental values for one sensor."""

    def __init__(self, sensor_type: str, description: str):
        self.sensor_type = sensor_type
        self.description = description
        self.seed = _seed(description)

    def value_at(self, dt: datetime) -> float:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ts = dt.timestamp()
        hod = ((ts / 3600.0) % 24 + 24) % 24
        fast = _noise(self.seed, "f", int(ts // 300))
        slow = _noise(self.seed, "s", int(ts // 3600))
        day_wave = math.sin((hod - 9) / 24 * 2 * math.pi)

        st = self.sensor_type
        if st == "air_temperature":
            v = 21.5 + 3.4 * day_wave + 1.2 * slow + 0.35 * fast
            return round(_clamp(v, 8.0, 38.0), 2)
        if st == "soil_temperature":
            soil_wave = math.sin((hod - 13) / 24 * 2 * math.pi)
            v = 19.2 + 1.3 * soil_wave + 0.6 * slow + 0.15 * fast
            return round(_clamp(v, 10.0, 32.0), 2)
        if st == "air_humidity":
            v = 66.0 - 9.5 * day_wave - 2.0 * slow + 1.2 * fast
            return round(_clamp(v, 38.0, 96.0), 1)
        if st == "soil_humidity":
            # Sawtooth: drains over ~29h, then an irrigation jump resets it.
            period = 29 * 3600.0
            phase = (ts % period) / period
            v = 58.0 - 14.0 * phase + 0.9 * fast
            return round(_clamp(v, 20.0, 68.0), 1)
        if st == "co2":
            v = 620.0 - 140.0 * max(day_wave, 0.0) + 25.0 * slow + 12.0 * fast
            return float(round(_clamp(v, 380.0, 1100.0)))
        if st == "ph":
            v = 6.3 + 0.06 * fast
            return round(_clamp(v, 5.8, 6.9), 2)
        if st == "light_intensity":
            daylight = max(0.0, math.sin((hod - 6) / 13 * math.pi))
            v = 58000.0 * daylight * (0.85 + 0.3 * slow) + 2500.0 * fast * daylight
            return float(round(_clamp(v, 0.0, 98000.0)))
        raise ValueError(f"unknown sensor type: {st}")
