"""Phase 2: push a live reading for every simulated sensor every interval."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from typing import Callable

from .client import ApiClient, ApiError
from .initialize import iso_utc
from .signals import SignalGenerator, is_sim_sensor


def collect_sim_sensors(client: ApiClient, log: Callable[[str], None] = print) -> list[tuple[SignalGenerator, dict]]:
    sensors = [s for s in client.list_sensors() if s.get("is_active") and is_sim_sensor(s.get("description", ""))]
    generators = [(SignalGenerator(s["sensor_type"], s["description"]), s) for s in sensors]
    log(f"live loop will feed {len(generators)} simulated sensors")
    return generators


def aligned_tick(now: float, interval_seconds: int) -> float:
    """The next tick boundary strictly in the future."""
    current = int(now) // interval_seconds * interval_seconds
    return float(current + interval_seconds)


def compute_readings(generators: list[tuple[SignalGenerator, dict]], at: datetime) -> list[tuple[dict, float]]:
    return [(sensor, gen.value_at(at)) for gen, sensor in generators]


def tick_once(
    client: ApiClient,
    generators: list[tuple[SignalGenerator, dict]],
    at: datetime,
    log: Callable[[str], None] = print,
) -> int:
    pushed = 0
    stamp = iso_utc(at)
    for sensor, value in compute_readings(generators, at):
        try:
            client.create_measurement(sensor["id"], value, stamp)
            pushed += 1
        except ApiError as exc:
            log(f"failed to post reading for sensor #{sensor['id']}: {exc}")
    log(f"{stamp} · pushed {pushed}/{len(generators)} readings")
    return pushed


def loop(
    client,
    generators: list[tuple[SignalGenerator, dict]],
    interval: int,
    max_cycles: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
    log: Callable[[str], None] = print,
) -> int:
    """Run the tick loop until max_cycles (or forever); returns cycle count."""
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        target = aligned_tick(clock(), interval)
        wait = target - clock()
        if wait > 0:
            sleep(wait)
        at = datetime.fromtimestamp(target, tz=timezone.utc)
        tick_once(client, generators, at, log=log)
        cycles += 1
    return cycles


def run(config_path: str, interval_override: int | None = None, max_cycles: int | None = None,
        log: Callable[[str], None] = print) -> None:
    from .world import load_world

    world = load_world(config_path)
    client = ApiClient(world.base_url, world.username, world.password)
    client.login()
    log("logged in")

    generators = collect_sim_sensors(client, log=log)
    if not generators:
        log("no simulated sensors found - did you run 'python -m simulator.initialize' first?")
        return

    interval = interval_override or world.interval_seconds
    loop(client, generators, interval, max_cycles=max_cycles, log=log)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Feed live measurements to terraGEM every interval.")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument("--interval", type=int, default=None, help="override seconds between readings")
    parser.add_argument("--max-cycles", type=int, default=None, help="exit after N cycles (testing)")
    args = parser.parse_args(argv)
    try:
        run(args.config, interval_override=args.interval, max_cycles=args.max_cycles)
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
