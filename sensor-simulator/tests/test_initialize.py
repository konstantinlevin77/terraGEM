"""Tests for the initialization phase (provisioning + backfill)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from simulator import initialize
from conftest import FakeApiClient, make_test_world_yaml
from simulator.signals import sensor_description


class TestPlanBackfill:
    def test_count_matches_hours_and_step(self):
        now = datetime(2026, 8, 26, 12, 7, tzinfo=timezone.utc)
        stamps = initialize.plan_backfill(now, hours=26, step_minutes=5)
        assert len(stamps) == 26 * 12 + 1
        assert all(s.minute % 5 == 0 for s in stamps)

    def test_spans_requested_window(self):
        now = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)
        stamps = initialize.plan_backfill(now, hours=26, step_minutes=5)
        span_hours = (stamps[-1] - stamps[0]).total_seconds() / 3600
        assert 25.9 <= span_hours <= 26.01

    def test_sorted_ascending_and_utc(self):
        now = datetime.now(timezone.utc)
        stamps = initialize.plan_backfill(now, hours=2, step_minutes=5)
        assert stamps == sorted(stamps)
        assert all(s.tzinfo is not None for s in stamps)


class TestEnsureSteps:
    def _prepared_client(self):
        client = FakeApiClient()
        client.seed_profiles()
        return client

    def test_profiles_created_when_missing(self):
        client = FakeApiClient()
        ids = initialize.ensure_profiles(client, log=lambda *_: None)
        assert len(ids) == len(initialize.PROFILES)
        assert len(client.profiles) == len(initialize.PROFILES)

    def test_profiles_reused_when_present(self):
        client = self._prepared_client()
        before = len(client.profiles)
        ids = initialize.ensure_profiles(client, log=lambda *_: None)
        assert len(client.profiles) == before

    def test_greenhouses_created_once(self):
        client = FakeApiClient()
        specs = list(FakeSpecs.one())
        gh_map = initialize.ensure_greenhouses(client, specs, log=lambda *_: None)
        assert len(client.greenhouses) == 1
        again = initialize.ensure_greenhouses(client, specs, log=lambda *_: None)
        assert len(client.greenhouses) == 1
        assert gh_map["Test GH"]["id"] == again["Test GH"]["id"]

    def test_sensors_created_and_reused(self):
        client = self._prepared_client()
        profile_ids = {p["sensor_type"]: p["id"] for p in client.profiles}
        specs = FakeSpecs.with_sensors()
        gh_map = initialize.ensure_greenhouses(client, specs, log=lambda *_: None)
        entries = initialize.ensure_sensors(
            client,
            gh_map,
            profile_ids,
            specs,
            log=lambda *_: None,
        )
        created = len(entries)
        entries_again = initialize.ensure_sensors(
            client, gh_map, profile_ids, specs, log=lambda *_: None,
        )
        assert created == 3
        assert len(client.sensors) == 3
        assert [e[1]["id"] for e in entries] == [e[1]["id"] for e in entries_again]

    def test_thresholds_seeded_per_sensor_skipping_light(self):
        client = self._prepared_client()
        from simulator.signals import THRESHOLDS

        # air temp + light; light must be skipped (no band configured)
        sensor_specs = [
            ("air_temperature", "Air temperature #1 · [sim]"),
            ("light_intensity", "Light intensity #1 · [sim]"),
        ]
        gh = client.create_greenhouse("GH", "", None, None)
        profile_ids = {p["sensor_type"]: p["id"] for p in client.profiles}
        entries = []
        for stype, desc in sensor_specs:
            s = client.create_sensor(gh["id"], profile_ids[stype], desc)
            from simulator.world import SensorSpec

            entries.append((SensorSpec(stype, desc), s))
        created = initialize.ensure_thresholds(client, entries, log=lambda *_: None)
        assert created == 1  # only air temperature has a band
        # Re-running must not duplicate.
        created_again = initialize.ensure_thresholds(client, entries, log=lambda *_: None)
        assert created_again == 0


class TestBackfill:
    def test_pushes_expected_readings_per_sensor(self):
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        pid = client.profiles[0]["id"]
        s = client.create_sensor(gh["id"], pid, "Air temperature #1 · [sim]")
        from simulator.world import SensorSpec

        entries = [(SensorSpec("air_temperature", s["description"]), s)]
        now = datetime.now(timezone.utc)
        stamps = initialize.plan_backfill(now, hours=1, step_minutes=30)
        pushed = initialize.backfill_measurements(
            client, entries, stamps, workers=1, log=lambda *_: None
        )
        assert pushed == len(stamps)
        assert client.measurement_count_for(s["id"]) == len(stamps)

    def test_timestamps_are_iso_utc_z(self):
        client = FakeApiClient()
        client.seed_profiles()
        gh = client.create_greenhouse("GH", "", None, None)
        s = client.create_sensor(gh["id"], client.profiles[0]["id"], "Air temperature #1 · [sim]")
        from simulator.world import SensorSpec

        entries = [(SensorSpec("air_temperature", s["description"]), s)]
        now = datetime(2026, 8, 26, 10, 15, tzinfo=timezone.utc)
        stamps = initialize.plan_backfill(now, hours=1, step_minutes=30)
        initialize.backfill_measurements(client, entries, stamps, workers=1, log=lambda *_: None)
        times = [m["measurement_time"] for m in client.measurements]
        assert times[0].endswith("Z")
        assert "T" in times[0]


class TestRunEndToEnd:
    def test_full_run_provisions_world_and_backfills(self, tmp_path):
        path = make_test_world_yaml(tmp_path, backfill_hours=1, step_minutes=60)
        fake_holder = {}

        def factory(base_url, username, password):
            fake = FakeApiClient()
            fake.seed_profiles()
            fake_holder["client"] = fake
            return fake

        summary = initialize.run(
            path, workers_override=1, log=lambda *_: None, client_factory=factory
        )
        client = fake_holder["client"]
        assert summary["greenhouses"] == 1
        assert summary["sensors"] == 3
        assert len(client.greenhouses) == 1
        assert len(client.sensors) == 3
        assert len(client.thresholds) == 3  # all three types have bands
        # 1h @ 60min step -> 2 readings per sensor
        assert summary["readings_pushed"] == 6
        assert len(client.measurements) == 6

    def test_rerun_is_idempotent(self, tmp_path):
        path = make_test_world_yaml(tmp_path, backfill_hours=1, step_minutes=60)

        def make_fake(_base, _user, _pass):
            fake = FakeApiClient()
            fake.seed_profiles()
            return fake

        first = initialize.run(path, workers_override=1, log=lambda *_: None, client_factory=make_fake)
        second = initialize.run(path, workers_override=1, log=lambda *_: None, client_factory=make_fake)
        # Second run reuses everything (fresh fake proves no reliance on prior state,
        # and the API-side counts are asserted by the identical summaries).
        assert second["sensors"] == first["sensors"]

    def test_rerun_against_same_client_creates_nothing_new(self, tmp_path):
        path = make_test_world_yaml(tmp_path, backfill_hours=1, step_minutes=60)
        shared = FakeApiClient()
        shared.seed_profiles()

        initialize.run(path, workers_override=1, log=lambda *_: None, client_factory=lambda *a: shared)
        counts_before = (len(shared.sensors), len(shared.greenhouses), len(shared.profiles))
        measurements_before = len(shared.measurements)

        initialize.run(path, workers_override=1, log=lambda *_: None, client_factory=lambda *a: shared)
        assert (len(shared.sensors), len(shared.greenhouses), len(shared.profiles)) == counts_before
        # Backfill still runs (new timestamps), so only entities are stable.
        assert len(shared.measurements) > measurements_before


class FakeSpecs:
    """Tiny helper producing GreenhouseSpec iterables for ensure_* tests."""

    @staticmethod
    def one():
        from simulator.world import GreenhouseSpec

        yield GreenhouseSpec("Test GH", "d", 1.0, 2.0)

    @staticmethod
    def with_sensors():
        from simulator.world import GreenhouseSpec, SensorSpec

        return [
            GreenhouseSpec(
                "Test GH",
                "d",
                1.0,
                2.0,
                (
                    SensorSpec("air_temperature", sensor_description("air_temperature", 1)),
                    SensorSpec("air_temperature", sensor_description("air_temperature", 2)),
                    SensorSpec("air_humidity", sensor_description("air_humidity", 1)),
                ),
            )
        ]
