"""Phase 1: provision the world and backfill 26 hours of measurements."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from .client import ApiClient, ApiError
from .signals import PROFILES, THRESHOLDS
from .world import GreenhouseSpec, SensorSpec, WorldConfig, load_world

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(ISO_FMT)


def plan_backfill(now: datetime, hours: int, step_minutes: int) -> list[datetime]:
    """Aligned timestamps from `hours` ago up to now, at step boundaries."""
    step = step_minutes * 60
    anchor = int(now.timestamp()) // step * step
    count = int(hours * 3600 / step) + 1
    return [datetime.fromtimestamp(anchor - i * step, tz=timezone.utc) for i in range(count - 1, -1, -1)]


def ensure_profiles(client: ApiClient, log: Callable[[str], None] = print) -> dict[str, int]:
    existing = {p["name"]: p["id"] for p in client.list_sensor_profiles()}
    ids: dict[str, int] = {}
    for sensor_type, (name, unit, period, description) in PROFILES.items():
        if name in existing:
            ids[sensor_type] = existing[name]
            log(f"profile '{name}' found (#{existing[name]})")
        else:
            created = client.create_sensor_profile(name, sensor_type, unit, period, description)
            ids[sensor_type] = created["id"]
            log(f"profile '{name}' created (#{created['id']})")
    return ids


def ensure_greenhouses(
    client: ApiClient, specs: Iterable[GreenhouseSpec], log: Callable[[str], None] = print
) -> dict[str, dict]:
    by_name = {g["name"]: g for g in client.list_greenhouses()}
    result: dict[str, dict] = {}
    for spec in specs:
        gh = by_name.get(spec.name)
        if gh:
            log(f"greenhouse '{spec.name}' found (#{gh['id']})")
        else:
            gh = client.create_greenhouse(spec.name, spec.description, spec.latitude, spec.longitude)
            log(f"greenhouse '{spec.name}' created (#{gh['id']})")
        result[spec.name] = gh
    return result


def ensure_sensors(
    client: ApiClient,
    greenhouse_map: dict[str, dict],
    profile_ids: dict[str, int],
    specs: Iterable[GreenhouseSpec],
    log: Callable[[str], None] = print,
) -> list[tuple[SensorSpec, dict]]:
    existing = {(s["greenhouse"], s["description"]): s for s in client.list_sensors()}
    entries: list[tuple[SensorSpec, dict]] = []
    for spec in specs:
        gh = greenhouse_map[spec.name]
        for sensor_spec in spec.sensors:
            key = (gh["id"], sensor_spec.description)
            sensor = existing.get(key)
            if sensor:
                log(f"sensor '{sensor_spec.description}' found (#{sensor['id']})")
            else:
                sensor = client.create_sensor(gh["id"], profile_ids[sensor_spec.sensor_type], sensor_spec.description)
                log(f"sensor '{sensor_spec.description}' created (#{sensor['id']})")
            entries.append((sensor_spec, sensor))
    return entries


def ensure_thresholds(
    client: ApiClient, entries: list[tuple[SensorSpec, dict]], log: Callable[[str], None] = print
) -> int:
    existing_sensors = {t["sensor"] for t in client.list_thresholds()}
    created = 0
    for sensor_spec, sensor in entries:
        band = THRESHOLDS.get(sensor_spec.sensor_type)
        if band is None or sensor["id"] in existing_sensors:
            continue
        wmin, wmax, cmin, cmax = band
        client.create_threshold(sensor["id"], wmin, wmax, cmin, cmax)
        created += 1
    log(f"thresholds created: {created}")
    return created


def backfill_measurements(
    client: ApiClient,
    entries: list[tuple[SensorSpec, dict]],
    timestamps: list[datetime],
    workers: int,
    log: Callable[[str], None] = print,
) -> int:
    from .signals import SignalGenerator

    total = len(entries) * len(timestamps)
    done = 0

    generators = {
        sensor["id"]: SignalGenerator(sensor_spec.sensor_type, sensor_spec.description)
        for sensor_spec, sensor in entries
    }

    def push(sensor_id: int) -> int:
        gen = generators[sensor_id]
        pushed = 0
        for ts in timestamps:
            client.create_measurement(sensor_id, gen.value_at(ts), iso_utc(ts))
            pushed += 1
        return pushed

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(push, sensor["id"]): sensor for _, sensor in entries}
        errors: list[Exception] = []
        for future in as_completed(futures):
            sensor = futures[future]
            try:
                done += future.result()
                print(f"\rbackfill progress: {done}/{total}", end="", flush=True)
            except ApiError as exc:
                errors.append(exc)
                print()
                log(f"backfill failed for sensor #{sensor['id']}: {exc}")
        print()
        if errors:
            raise errors[0]
    return done


def run(
    config_path: str,
    workers_override: int | None = None,
    log: Callable[[str], None] = print,
    client_factory=ApiClient,
) -> dict:
    world: WorldConfig = load_world(config_path)
    client = client_factory(world.base_url, world.username, world.password)
    client.login()
    log("logged in")

    profile_ids = ensure_profiles(client, log=log)
    greenhouse_map = ensure_greenhouses(client, world.greenhouses, log=log)
    entries = ensure_sensors(client, greenhouse_map, profile_ids, world.greenhouses, log=log)
    ensure_thresholds(client, entries, log=log)

    now = datetime.now(timezone.utc)
    workers = workers_override or world.workers
    timestamps = plan_backfill(now, world.backfill_hours, world.backfill_step_minutes)
    log(f"backfilling {len(entries)} sensors x {len(timestamps)} readings ({world.backfill_hours}h @ {world.backfill_step_minutes}min)")

    pushed = backfill_measurements(client, entries, timestamps, workers, log=log)
    summary = {
        "greenhouses": len(greenhouse_map),
        "sensors": len(entries),
        "readings_pushed": pushed,
    }
    log(f"done: {summary}")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Provision and backfill a simulated terraGEM world.")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument("--workers", type=int, default=None, help="override parallel workers")
    args = parser.parse_args(argv)
    try:
        run(args.config, workers_override=args.workers)
    except ApiError as exc:
        raise SystemExit(f"API error: {exc}") from exc


if __name__ == "__main__":
    main()
