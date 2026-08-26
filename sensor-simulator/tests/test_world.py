"""Tests for config parsing and world layout validation."""

from __future__ import annotations

import pytest

from simulator.signals import SIM_TAG, sensor_description
from simulator.world import load_world
from conftest import make_test_world_yaml


class TestLoadWorld:
    def test_parses_basic_config(self, tmp_path):
        path = make_test_world_yaml(tmp_path)
        world = load_world(path)
        assert world.base_url == "http://testserver/api"
        assert world.username == "tester"
        assert world.password == "secret"
        assert world.backfill_hours == 26
        assert world.backfill_step_minutes == 60
        assert world.interval_seconds == 300
        assert len(world.greenhouses) == 1

    def test_sensor_counts_become_descriptions(self, tmp_path):
        path = make_test_world_yaml(
            tmp_path,
            greenhouses=[
                """
  - name: GH1
    description: d
    sensors:
      air_temperature: 3
      ph: 1
"""
            ],
        )
        world = load_world(path)
        gh = world.greenhouses[0]
        descriptions = [s.description for s in gh.sensors]
        assert len(descriptions) == 4
        assert descriptions.count(sensor_description("air_temperature", 2)) == 1
        assert all(SIM_TAG in d for d in descriptions)

    def test_trailing_slash_stripped_from_base_url(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(
            "api:\n  base_url: http://x/api/\n  username: u\n  password: p\n"
            "greenhouses:\n  - name: G\n    sensors: {}\n"
        )
        assert load_world(str(path)).base_url == "http://x/api"

    def test_zero_count_sensor_type_skipped(self, tmp_path):
        path = make_test_world_yaml(
            tmp_path,
            greenhouses=[
                """
  - name: GH1
    sensors:
      air_temperature: 2
      co2: 0
"""
            ],
        )
        world = load_world(path)
        assert len(world.greenhouses[0].sensors) == 2


class TestValidation:
    def test_unknown_sensor_type_rejected(self, tmp_path):
        path = make_test_world_yaml(
            tmp_path,
            greenhouses=[
                """
  - name: GH1
    sensors:
      moisture: 2
"""
            ],
        )
        with pytest.raises(ValueError, match="unknown sensor type"):
            load_world(path)

    def test_missing_name_rejected(self, tmp_path):
        path = make_test_world_yaml(
            tmp_path,
            greenhouses=[
                """
  - description: no name here
    sensors: {}
"""
            ],
        )
        with pytest.raises(ValueError, match="missing 'name'"):
            load_world(path)

    def test_duplicate_greenhouse_names_rejected(self, tmp_path):
        path = make_test_world_yaml(
            tmp_path,
            greenhouses=[
                """
  - name: Same
    sensors: {}
""",
                """
  - name: Same
    sensors: {}
""",
            ],
        )
        with pytest.raises(ValueError, match="unique"):
            load_world(path)

    def test_no_greenhouses_rejected(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("api:\n  base_url: http://x/api\n  username: u\n  password: p\ngreenhouses: []\n")
        with pytest.raises(ValueError, match="at least one greenhouse"):
            load_world(path)
