"""Tests for the live loop."""

from __future__ import annotations

from datetime import datetime, timezone

from simulator import live
from conftest import FakeApiClient


class TestAlignedTick:
    def test_next_boundary_strictly_future(self):
        assert live.aligned_tick(1000.0, 300) == 1200.0
        assert live.aligned_tick(1200.0, 300) == 1500.0
        assert live.aligned_tick(1199.999, 300) == 1200.0

    def test_respects_custom_interval(self):
        assert live.aligned_tick(0.0, 60) == 60
        assert live.aligned_tick(61.0, 60) == 120


class TestCollectSimSensors:
    def test_only_active_sim_sensors_selected(self):
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        pid = client.profiles[0]["id"]
        sim = client.create_sensor(gh["id"], pid, "Air temperature #1 · [sim]")
        manual = client.create_sensor(gh["id"], pid, "Canopy probe, middle row")
        inactive = client.create_sensor(gh["id"], pid, "Air temperature #2 · [sim]")
        client.sensors = [
            s if s["id"] != inactive["id"] else {**s, "is_active": False} for s in client.sensors
        ]

        generators = live.collect_sim_sensors(client, log=lambda *_: None)
        ids = [s["id"] for _, s in generators]
        assert ids == [sim["id"]]
        assert manual["id"] not in ids


class TestTickOnce:
    def _setup(self):
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        profile_by_type = {p["sensor_type"]: p["id"] for p in client.profiles}
        entries = []
        for stype in ("air_temperature", "soil_humidity"):
            s = client.create_sensor(gh["id"], profile_by_type[stype], f"{stype} #1 · [sim]")
            entries.append((live.SignalGenerator(stype, s["description"]), s))
        return client, entries

    def test_pushes_one_reading_per_sensor_at_same_timestamp(self):
        client, generators = self._setup()
        at = datetime(2026, 8, 26, 12, 5, tzinfo=timezone.utc)
        pushed = live.tick_once(client, generators, at, log=lambda *_: None)
        assert pushed == 2
        stamps = {m["measurement_time"] for m in client.measurements}
        assert stamps == {"2026-08-26T12:05:00Z"}

    def test_values_match_signal_function(self):
        client, generators = self._setup()
        at = datetime(2026, 8, 26, 12, 10, tzinfo=timezone.utc)
        live.tick_once(client, generators, at, log=lambda *_: None)
        by_sensor = {m["sensor"]: m["value"] for m in client.measurements}
        for gen, sensor in generators:
            assert by_sensor[sensor["id"]] == gen.value_at(at)

    def test_api_error_does_not_abort_cycle(self):
        client, generators = self._setup()

        original = client.create_measurement

        def flaky(sensor_id, value, ts):
            if sensor_id == generators[0][1]["id"]:
                raise live.ApiError(500, "boom")
            return original(sensor_id, value, ts)

        client.create_measurement = flaky
        pushed = live.tick_once(client, generators, datetime.now(timezone.utc), log=lambda *_: None)
        assert pushed == 1


class TestLoop:
    def test_loop_runs_exact_cycles_and_posts_readings(self, tmp_path):
        # Build a standalone fake with two sensors (bypass config/run).
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        pid = client.profiles[0]["id"]
        sensors = [
            client.create_sensor(gh["id"], pid, "Air temperature #1 · [sim]"),
            client.create_sensor(gh["id"], pid, "Air humidity #1 · [sim]"),
        ]
        generators = [(live.SignalGenerator(s["sensor_type"], s["description"]), s) for s in sensors]

        sleeps: list[float] = []

        class FakeClock:
            def __init__(self, start=1_000_000.0):
                self.now = start

            def __call__(self):
                return self.now

        clock = FakeClock()

        def advance(s):
            sleeps.append(s)
            clock.now += s

        cycles = live.loop(
            client,
            generators,
            interval=300,
            max_cycles=3,
            sleep=advance,
            clock=clock,
            log=lambda *_: None,
        )

        assert cycles == 3
        assert len(sleeps) == 3
        # First wait is the partial remainder of the current interval.
        assert 0 < sleeps[0] <= 300
        assert all(abs(s - 300.0) < 1e-9 for s in sleeps[1:])
        # 2 sensors x 3 cycles
        assert len(client.measurements) == 6
        stamps = sorted({m["measurement_time"] for m in client.measurements})
        assert len(stamps) == 3  # one aligned timestamp per cycle

    def test_loop_stops_forever_mode_only_via_max_cycles_in_tests(self, tmp_path):
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        s = client.create_sensor(gh["id"], client.profiles[0]["id"], "pH #1 · [sim]")
        gen = live.SignalGenerator("ph", s["description"])
        cycles = live.loop(
            client,
            [(gen, s)],
            interval=60,
            max_cycles=5,
            sleep=lambda *_: None,
            clock=lambda: 500.0,
            log=lambda *_: None,
        )
        assert cycles == 5
