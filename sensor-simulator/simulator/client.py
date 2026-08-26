"""Thin API client for the terraGEM backend.

The simulator never touches the database directly; everything goes
through the REST API with JWT bearer authentication and automatic
token refresh.
"""

from __future__ import annotations

import threading
from typing import Any

import requests


class ApiError(Exception):
    def __init__(self, status: int, data: Any = None):
        self.status = status
        self.data = data
        super().__init__(f"HTTP {status}: {data}")


class ApiClient:
    """JWT-authenticated REST client for the terraGEM API."""

    def __init__(self, base_url: str, username: str, password: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self._access: str | None = None
        self._refresh: str | None = None
        self._refresh_lock = threading.Lock()

    # ------------------------------------------------------------------ auth

    def login(self) -> None:
        resp = self.session.post(
            f"{self.base_url}/auth/token/",
            json={"username": self.username, "password": self.password},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise ApiError(resp.status_code, self._safe_json(resp))
        data = resp.json()
        self._access = data["access"]
        self._refresh = data["refresh"]

    def _try_refresh(self) -> bool:
        if not self._refresh:
            return False
        resp = self.session.post(
            f"{self.base_url}/auth/token/refresh/",
            json={"refresh": self._refresh},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return False
        self._access = resp.json()["access"]
        return True

    # --------------------------------------------------------------- request

    def request(self, method: str, path: str, body: Any = None, retry_auth: bool = True) -> Any:
        headers = {}
        if self._access:
            headers["Authorization"] = f"Bearer {self._access}"
        resp = self.session.request(
            method,
            f"{self.base_url}{path}",
            json=body,
            headers=headers,
            timeout=self.timeout,
        )
        if resp.status_code == 401 and retry_auth and self._access:
            with self._refresh_lock:
                refreshed = self._refresh_token_once()
            if refreshed:
                return self.request(method, path, body, retry_auth=False)
            raise ApiError(401, {"detail": "session expired and refresh failed"})
        if resp.status_code >= 400:
            raise ApiError(resp.status_code, self._safe_json(resp))
        if not resp.content:
            return None
        return resp.json()

    def _refresh_token_once(self) -> bool:
        # Double-checked inside the lock so concurrent 401s only refresh once.
        if getattr(self, "_last_refresh_failed", False):
            return False
        ok = self._try_refresh()
        if not ok:
            self._last_refresh_failed = True
        return ok

    @staticmethod
    def _safe_json(resp: requests.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            return None

    # ------------------------------------------------------------ endpoints

    def list_sensor_profiles(self) -> list[dict]:
        return self.request("GET", "/sensor-profiles/")

    def create_sensor_profile(self, name: str, sensor_type: str, unit: str, period: float, description: str) -> dict:
        return self.request(
            "POST",
            "/sensor-profiles/",
            {
                "name": name,
                "sensor_type": sensor_type,
                "unit": unit,
                "period": period,
                "description": description,
            },
        )

    def list_greenhouses(self) -> list[dict]:
        return self.request("GET", "/greenhouses/")

    def create_greenhouse(self, name: str, description: str, latitude: float | None, longitude: float | None) -> dict:
        return self.request(
            "POST",
            "/greenhouses/",
            {
                "name": name,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    def list_sensors(self) -> list[dict]:
        return self.request("GET", "/sensors/")

    def create_sensor(self, greenhouse_id: int, profile_id: int, description: str) -> dict:
        return self.request(
            "POST",
            "/sensors/",
            {
                "greenhouse": greenhouse_id,
                "profile": profile_id,
                "description": description,
                "is_active": True,
            },
        )

    def list_thresholds(self) -> list[dict]:
        return self.request("GET", "/thresholds/")

    def create_threshold(
        self,
        sensor_id: int,
        warning_min: float,
        warning_max: float,
        critical_min: float,
        critical_max: float,
    ) -> dict:
        return self.request(
            "POST",
            "/thresholds/",
            {
                "sensor": sensor_id,
                "warning_min": warning_min,
                "warning_max": warning_max,
                "critical_min": critical_min,
                "critical_max": critical_max,
                "is_active": True,
            },
        )

    def create_measurement(self, sensor_id: int, value: float, measurement_time: str) -> dict:
        return self.request(
            "POST",
            "/measurements/",
            {"sensor": sensor_id, "value": value, "measurement_time": measurement_time},
        )
