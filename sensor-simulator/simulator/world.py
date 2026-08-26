"""World layout: parses config.yaml into typed greenhouse/sensor plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .signals import PROFILES

VALID_SENSOR_TYPES = set(PROFILES.keys())


@dataclass(frozen=True)
class SensorSpec:
    sensor_type: str
    description: str


@dataclass(frozen=True)
class GreenhouseSpec:
    name: str
    description: str
    latitude: float | None
    longitude: float | None
    sensors: tuple[SensorSpec, ...] = field(default=())


@dataclass(frozen=True)
class WorldConfig:
    base_url: str
    username: str
    password: str
    backfill_hours: int
    backfill_step_minutes: int
    workers: int
    interval_seconds: int
    greenhouses: tuple[GreenhouseSpec, ...]


def _parse_greenhouse(raw: dict) -> GreenhouseSpec:
    name = raw.get("name")
    if not name:
        raise ValueError("greenhouse entry is missing 'name'")
    sensors: list[SensorSpec] = []
    for sensor_type, count in (raw.get("sensors") or {}).items():
        if sensor_type not in VALID_SENSOR_TYPES:
            raise ValueError(f"unknown sensor type '{sensor_type}' (valid: {sorted(VALID_SENSOR_TYPES)})")
        if count < 1:
            continue
        from .signals import sensor_description

        for i in range(1, count + 1):
            sensors.append(SensorSpec(sensor_type, sensor_description(sensor_type, i)))
    descriptions = [s.description for s in sensors]
    if len(descriptions) != len(set(descriptions)):
        raise ValueError(f"duplicate sensor descriptions in greenhouse '{name}'")
    return GreenhouseSpec(
        name=name,
        description=raw.get("description", ""),
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        sensors=tuple(sensors),
    )


def load_world(path: str | Path) -> WorldConfig:
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    api = raw.get("api") or {}
    sim = raw.get("simulation") or {}
    gh_raw = raw.get("greenhouses") or []
    if not gh_raw:
        raise ValueError("config must define at least one greenhouse")

    names = [g.get("name") for g in gh_raw]
    if len(names) != len(set(names)):
        raise ValueError("greenhouse names must be unique")

    return WorldConfig(
        base_url=str(api.get("base_url", "http://127.0.0.1:8000/api")).rstrip("/"),
        username=str(api.get("username", "")),
        password=str(api.get("password", "")),
        backfill_hours=int(sim.get("backfill_hours", 26)),
        backfill_step_minutes=int(sim.get("backfill_step_minutes", 5)),
        workers=int(sim.get("workers", 8)),
        interval_seconds=int(sim.get("interval_seconds", 300)),
        greenhouses=tuple(_parse_greenhouse(g) for g in gh_raw),
    )
