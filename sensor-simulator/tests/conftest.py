"""Shared test doubles: a fake API client and config helpers."""

from __future__ import annotations

import textwrap

from simulator.signals import PROFILES, THRESHOLDS, sensor_description


class FakeApiClient:
    """In-memory stand-in mirroring the ApiClient surface the simulator uses."""

    def __init__(self):
        self.profiles: list[dict] = []
        self.greenhouses: list[dict] = []
        self.sensors: list[dict] = []
        self.thresholds: list[dict] = []
        self.measurements: list[dict] = []
        self._next_id = 1
        self.login_calls = 0

    def login(self):
        self.login_calls += 1

    def _id(self) -> int:
        i = self._next_id
        self._next_id += 1
        return i

    # profiles

    def list_sensor_profiles(self):
        return [dict(p) for p in self.profiles]

    def create_sensor_profile(self, name, sensor_type, unit, period, description):
        profile = {
            "id": self._id(),
            "name": name,
            "sensor_type": sensor_type,
            "unit": unit,
            "period": period,
            "description": description,
        }
        self.profiles.append(profile)
        return dict(profile)

    def seed_profiles(self):
        for stype, (name, unit, period, desc) in PROFILES.items():
            self.create_sensor_profile(name, stype, unit, period, desc)

    # greenhouses

    def list_greenhouses(self):
        return [dict(g) for g in self.greenhouses]

    def create_greenhouse(self, name, description, latitude, longitude):
        gh = {
            "id": self._id(),
            "name": name,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
        }
        self.greenhouses.append(gh)
        return dict(gh)

    # sensors

    def list_sensors(self):
        return [dict(s) for s in self.sensors]

    def create_sensor(self, greenhouse_id, profile_id, description):
        stype = next(p["sensor_type"] for p in self.profiles if p["id"] == profile_id)
        sensor = {
            "id": self._id(),
            "greenhouse": greenhouse_id,
            "profile": profile_id,
            "sensor_type": stype,
            "description": description,
            "is_active": True,
        }
        self.sensors.append(sensor)
        return dict(sensor)

    # thresholds

    def list_thresholds(self):
        return [dict(t) for t in self.thresholds]

    def create_threshold(self, sensor_id, warning_min, warning_max, critical_min, critical_max):
        thr = {
            "id": self._id(),
            "sensor": sensor_id,
            "warning_min": warning_min,
            "warning_max": warning_max,
            "critical_min": critical_min,
            "critical_max": critical_max,
            "is_active": True,
        }
        self.thresholds.append(thr)
        return dict(thr)

    # measurements

    def create_measurement(self, sensor_id, value, measurement_time):
        m = {
            "id": self._id(),
            "sensor": sensor_id,
            "value": value,
            "measurement_time": measurement_time,
        }
        self.measurements.append(m)
        return dict(m)

    def measurement_count_for(self, sensor_id):
        return sum(1 for m in self.measurements if m["sensor"] == sensor_id)


def make_test_world_yaml(tmp_path, backfill_hours=26, step_minutes=60, greenhouses=None):
    """Write a minimal valid config.yaml and return its path as string."""
    gh_blocks = greenhouses or [
        """
  - name: North Tunnel
    description: test tunnel [sim]
    latitude: 52.09
    longitude: 5.10
    sensors:
      air_temperature: 2
      air_humidity: 1
"""
    ]
    body = "".join(textwrap.dedent(b) for b in gh_blocks)
    config = f"""
api:
  base_url: http://testserver/api
  username: tester
  password: secret

simulation:
  backfill_hours: {backfill_hours}
  backfill_step_minutes: {step_minutes}
  workers: 2
  interval_seconds: 300

greenhouses:
{body}
"""
    path = tmp_path / "config.yaml"
    path.write_text(config)
    return str(path)


__all__ = ["FakeApiClient", "PROFILES", "THRESHOLDS", "make_test_world_yaml", "sensor_description"]
