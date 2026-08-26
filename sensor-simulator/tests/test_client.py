"""Tests for the JWT API client (transport mocked, no network)."""

from __future__ import annotations

import pytest

from simulator.client import ApiClient, ApiError


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data
        if json_data is None:
            self.content = b""
        else:
            import json as _json

            self.content = _json.dumps(json_data).encode()

    def json(self):
        import json as _json

        return _json.loads(self.content)


class FakeSession:
    """Records requests and replays scripted responses per (method, path)."""

    def __init__(self, script=None):
        # script: dict[(method, path)] -> list[FakeResponse] popped in order
        self.script = script or {}
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method, url, json=None, headers=None, timeout=None):
        path = "/" + url.split("/api/", 1)[1]
        self.calls.append((method.upper(), path, {"json": json, "headers": headers}))
        responses = self.script.get((method.upper(), path), [FakeResponse(404, {})])
        return responses.pop(0) if len(responses) > 1 else responses[0]

    def post(self, url, json=None, timeout=None):
        path = "/" + url.split("/api/", 1)[1]
        self.calls.append(("POST", path, {"json": json}))
        responses = self.script.get(("POST", path), [])
        resp = responses.pop(0)
        return resp


def make_client(script=None) -> ApiClient:
    client = ApiClient("http://testserver/api", "user", "pass")
    client.session = FakeSession(script)
    return client


class TestLogin:
    def test_login_stores_token_pair(self):
        client = make_client(
            {("POST", "/auth/token/"): [FakeResponse(200, {"access": "A1", "refresh": "R1"})]}
        )
        client.login()
        assert client._access == "A1"
        assert client._refresh == "R1"

    def test_login_failure_raises_api_error(self):
        client = make_client({("POST", "/auth/token/"): [FakeResponse(401, {"detail": "bad creds"})]})
        with pytest.raises(ApiError) as exc:
            client.login()
        assert exc.value.status == 401

    def test_login_sends_credentials(self):
        client = make_client({("POST", "/auth/token/"): [FakeResponse(200, {"access": "A", "refresh": "R"})]})
        client.login()
        method, path, kwargs = client.session.calls[0]
        assert method == "POST" and path == "/auth/token/"
        assert kwargs["json"] == {"username": "user", "password": "pass"}


class TestRequest:
    def test_bearer_header_attached(self):
        client = make_client({("GET", "/sensors/"): [FakeResponse(200, [])]})
        client._access = "tok123"
        client.request("GET", "/sensors/")
        _, _, kwargs = client.session.calls[-1]
        assert kwargs["headers"]["Authorization"] == "Bearer tok123"

    def test_success_returns_parsed_json(self):
        client = make_client({("GET", "/greenhouses/"): [FakeResponse(200, [{"id": 1}])]})
        client._access = "a"
        assert client.request("GET", "/greenhouses/") == [{"id": 1}]

    def test_empty_body_returns_none(self):
        client = make_client({("DELETE", "/greenhouses/1/"): [FakeResponse(204)]})
        client._access = "a"
        assert client.request("DELETE", "/greenhouses/1/") is None

    def test_http_error_raises(self):
        client = make_client({("GET", "/nope/"): [FakeResponse(404, {"detail": "nf"})]})
        client._access = "a"
        with pytest.raises(ApiError) as exc:
            client.request("GET", "/nope/")
        assert exc.value.status == 404
        assert exc.value.data == {"detail": "nf"}


class TestRefreshFlow:
    def _script_with_expired_then_ok(self):
        return {
            ("GET", "/sensors/"): [
                FakeResponse(401, {"detail": "expired"}),
                FakeResponse(200, [{"id": 7}]),
            ],
            ("POST", "/auth/token/refresh/"): [FakeResponse(200, {"access": "A2"})],
        }

    def test_401_refreshes_and_retries_once(self):
        client = make_client(self._script_with_expired_then_ok())
        client._access = "A1"
        client._refresh = "R1"
        data = client.request("GET", "/sensors/")
        assert data == [{"id": 7}]
        assert client._access == "A2"

    def test_failed_refresh_raises_session_expired(self):
        script = {
            ("GET", "/sensors/"): [FakeResponse(401, {"detail": "expired"})],
            ("POST", "/auth/token/refresh/"): [FakeResponse(401, {"detail": "invalid"})],
        }
        client = make_client(script)
        client._access = "A1"
        client._refresh = "BAD"
        with pytest.raises(ApiError) as exc:
            client.request("GET", "/sensors/")
        assert exc.value.status == 401

    def test_no_retry_loop_when_second_attempt_also_401(self):
        script = {
            ("GET", "/sensors/"): [
                FakeResponse(401, {}),
                FakeResponse(401, {}),
            ],
            ("POST", "/auth/token/refresh/"): [FakeResponse(200, {"access": "A2"})],
        }
        client = make_client(script)
        client._access = "A1"
        client._refresh = "R1"
        with pytest.raises(ApiError):
            client.request("GET", "/sensors/")
        sensor_calls = [c for c in client.session.calls if c[1] == "/sensors/" and c[0] == "GET"]
        assert len(sensor_calls) == 2


class TestPayloads:
    def test_create_sensor_sends_is_active_true(self):
        # Regression: Sensor.is_active defaults to False server-side, so the
        # simulator must always request active sensors explicitly.
        script = {("POST", "/sensors/"): [FakeResponse(201, {"id": 1})]}
        client = make_client(script)
        client._access = "a"
        client.create_sensor(greenhouse_id=3, profile_id=5, description="Air temperature #1 · [sim]")
        _, _, kwargs = client.session.calls[-1]
        assert kwargs["json"]["is_active"] is True
        assert kwargs["json"]["greenhouse"] == 3
        assert kwargs["json"]["profile"] == 5

    def test_measurement_payload_shape(self):
        script = {("POST", "/measurements/"): [FakeResponse(201, {"id": 9})]}
        client = make_client(script)
        client._access = "a"
        client.create_measurement(sensor_id=7, value=23.4, measurement_time="2026-08-26T10:00:00Z")
        method, path, kwargs = client.session.calls[-1]
        assert (method, path) == ("POST", "/measurements/")
        assert kwargs["json"] == {
            "sensor": 7,
            "value": 23.4,
            "measurement_time": "2026-08-26T10:00:00Z",
        }
