"""M15: one error body for every status (design §7 Errors). Every body has a code, a message and
a non-empty `problems` list; a 422 lists every mistake; a 409 lists every problem. Also the
startup wiring: settings from the environment and the login dummy hash.

Seed ids: Gateway 1 (Lee, Draft) · Telescope 5 (Active) · Gateway slots 1–3 · Fay 11 ·
Skills: Piloting 1, Leadership 2, Systems Engineering 3, EVA 4, Geology 5, Flight Medicine 6.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mission_control.api.app import create_app
from mission_control.infra import security
from mission_control.infra.settings import Settings

API = "/api/v1"


def assert_error(response, status, code):
    """The shared error shape, with at least one problem, each with code, message and refs."""
    assert response.status_code == status, response.text
    error = response.json()["error"]
    assert set(error) == {"code", "message", "problems"}
    assert error["code"] == code
    assert error["message"]
    assert error["problems"], "every error lists at least one problem"
    for p in error["problems"]:
        assert set(p) == {"code", "message", "refs"}
        assert p["code"] and p["message"]
    return error


# --- 401 ----------------------------------------------------------------------------------


def test_401_missing_token_is_unauthenticated_with_problems(client):
    error = assert_error(client.get(f"{API}/me"), 401, "unauthenticated")
    assert error["message"] == "Your session has expired or isn't valid; log in again"
    assert error["problems"] == [
        {"code": "unauthenticated", "message": error["message"], "refs": {}}
    ]


def test_401_carries_a_bearer_challenge(client):
    assert client.get(f"{API}/me").headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "header", ["Bearer not-a-real-token", "Basic bGVlOnB3", "Bearer", "lee@aurora.example"]
)
def test_401_bad_or_malformed_token(client, header):
    assert_error(client.get(f"{API}/me", headers={"Authorization": header}), 401, "unauthenticated")


def test_401_wrong_password_is_invalid_credentials(client):
    response = client.post(
        f"{API}/auth/login", json={"email": "lee@aurora.example", "password": "x" * 20}
    )
    error = assert_error(response, 401, "invalid_credentials")
    assert error["message"] == "Email or password is incorrect"


def test_401_comes_before_checking_the_body_fields(client):
    """A well-formed JSON body with wrong or missing fields gets 401, not 422: an
    unauthenticated caller learns nothing about what the endpoint expects."""
    assert_error(client.post(f"{API}/missions", json={"name": 7}), 401, "unauthenticated")


def test_malformed_json_is_refused_before_authentication(client):
    """A body that isn't JSON at all is a 422 even without a token: FastAPI reads the body
    before it runs the authentication dependency. It reveals nothing about the endpoint."""
    response = client.post(
        f"{API}/missions", headers={"Content-Type": "application/json"}, content=b"{not json"
    )
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "The request body isn't valid JSON"


# --- 403 ----------------------------------------------------------------------------------


def test_403_lists_its_single_reason_in_problems(client, login):
    error = assert_error(client.get(f"{API}/users", headers=login("lee")), 403, "role_forbidden")
    assert error["message"] == "Leads can't manage the organisation"
    assert error["problems"] == [
        {"code": "role_forbidden", "message": error["message"], "refs": {}}
    ]


def test_403_wrong_current_password(client, login):
    response = client.post(
        f"{API}/me/password",
        headers=login("lee"),
        json={"current_password": "not my password at all", "new_password": "a brand new phrase"},
    )
    error = assert_error(response, 403, "wrong_current_password")
    assert error["message"] == "Your current password is incorrect"


# --- 404 ----------------------------------------------------------------------------------


def test_404_missing_record_is_not_found_with_problems(client, login):
    error = assert_error(client.get(f"{API}/missions/999", headers=login("lee")), 404, "not_found")
    assert error["message"] == "Mission not found"
    assert error["problems"] == [{"code": "not_found", "message": "Mission not found", "refs": {}}]


def test_404_unknown_route_uses_the_same_shape(client, login):
    error = assert_error(client.get(f"{API}/nowhere", headers=login("lee")), 404, "not_found")
    assert error["message"] == "Not found"


# --- 405 ----------------------------------------------------------------------------------


def test_405_wrong_method_uses_the_same_shape(client, login):
    response = client.delete(f"{API}/missions", headers=login("lee"))
    error = assert_error(response, 405, "method_not_allowed")
    assert error["message"] == "Method Not Allowed"
    assert error["problems"] == [
        {"code": "method_not_allowed", "message": "Method Not Allowed", "refs": {}}
    ]
    # The Allow header is kept. Starlette fills it from the first route matching the path, so
    # it names GET here even though POST /missions exists too.
    assert "GET" in response.headers["allow"]


# --- 409 ----------------------------------------------------------------------------------


def test_409_state_conflict_carries_its_own_code(client, login):
    """Editing an Active mission: a StateConflict is a 409 under the lifecycle's code."""
    response = client.patch(f"{API}/missions/5", headers=login("lee"), json={"name": "Renamed"})
    error = assert_error(response, 409, "mission_frozen")
    assert error["message"] == "Can't edit an active mission"
    assert error["problems"] == [
        {"code": "mission_frozen", "message": "Can't edit an active mission", "refs": {}}
    ]


def test_409_lists_every_problem_with_refs(client, login):
    """Proposing Fay (unavailable 5–8 Mar) for Gateway's Commander once Ana fills it: both
    reasons are listed together under rule_violation, each with its refs."""
    lee = login("lee")
    # Fill Commander with Ana so a second proposal there is both full and Fay unavailable.
    assert (
        client.post(
            f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 3, "crew_profile_id": 6}
        ).status_code
        == 201
    )
    response = client.post(
        f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 3, "crew_profile_id": 11}
    )
    error = assert_error(response, 409, "rule_violation")
    assert error["message"] == "Fay can't be proposed as Commander on Lunar Gateway Resupply"
    codes = [p["code"] for p in error["problems"]]
    assert codes == ["slot_full", "unavailable"]
    assert error["problems"][0]["refs"] == {"slot_id": 3}


# --- 422 ----------------------------------------------------------------------------------


def test_422_request_shape_lists_every_mistake(client, login):
    response = client.post(
        f"{API}/missions",
        headers=login("lee"),
        json={"start_date": "not a date", "end_date": "2027-03-10", "slots": "nope"},
    )
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "Some values aren't valid"
    assert [p["message"] for p in error["problems"]] == [
        "name is required",
        "start_date must be a date (YYYY-MM-DD)",
        "slots must be a list",
    ]
    assert error["problems"][0]["refs"] == {"field": "name"}
    assert all(p["code"] == "validation_error" for p in error["problems"])


def test_422_single_shape_mistake_is_the_message(client, login):
    response = client.patch(f"{API}/org", headers=login("ruth"), json={"required_approvals": "x"})
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "required_approvals must be a whole number"
    assert len(error["problems"]) == 1


def test_422_invalid_json_body(client, login):
    response = client.post(
        f"{API}/skills",
        headers={**login("ruth"), "Content-Type": "application/json"},
        content=b"{not json",
    )
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "The request body isn't valid JSON"


def test_422_nested_field_names_the_path(client, login):
    response = client.post(
        f"{API}/missions",
        headers=login("lee"),
        json={
            "name": "Probe",
            "start_date": "2027-06-01",
            "end_date": "2027-06-02",
            "slots": [{"name": "Pilot", "headcount": "two", "requirements": []}],
        },
    )
    error = assert_error(response, 422, "validation_error")
    assert error["problems"][0]["message"] == "slots[0].headcount must be a whole number"
    assert error["problems"][0]["refs"] == {"field": "slots[0].headcount"}


def test_422_service_invalid_input_lists_every_mistake(client, login):
    """Malformed mission values found by the service are all listed at once (design §7)."""
    response = client.post(
        f"{API}/missions",
        headers=login("lee"),
        json={
            "name": " ",
            "start_date": "2027-06-10",
            "end_date": "2027-06-01",
            "slots": [{"name": "Pilot", "headcount": 0, "requirements": []}],
        },
    )
    error = assert_error(response, 422, "validation_error")
    assert [p["message"] for p in error["problems"]] == [
        "The mission needs a name",
        "The end date 2027-06-01 is before the start date 2027-06-10",
        "Pilot needs a headcount of at least 1",
        "Pilot needs at least one required skill",
    ]


def test_422_single_service_mistake_repeats_its_message(client, login):
    response = client.post(f"{API}/skills", headers=login("ruth"), json={"name": "  "})
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "The skill name can't be blank"
    assert error["problems"] == [
        {"code": "validation_error", "message": "The skill name can't be blank", "refs": {}}
    ]


def test_422_password_too_short(client, login):
    response = client.post(
        f"{API}/users",
        headers=login("ruth"),
        json={"email": "zoe@aurora.example", "name": "Zoe", "role": "crew", "password": "short"},
    )
    error = assert_error(response, 422, "password_too_short")
    assert error["message"] == "Passwords must be at least 15 characters"
    assert error["problems"] == [
        {"code": "password_too_short", "message": error["message"], "refs": {}}
    ]


def test_422_invalid_date_range_is_not_a_500(client, login):
    """Fay records unavailability ending before it starts."""
    response = client.post(
        f"{API}/crew/11/unavailability",
        headers=login("fay"),
        json={"start_date": "2027-07-10", "end_date": "2027-07-01", "reason": "Leave"},
    )
    error = assert_error(response, 422, "validation_error")
    assert error["message"] == "The end date 2027-07-01 is before the start date 2027-07-10"


def test_422_out_of_range_integer_is_refused_not_a_500(client, login):
    """An id too large for the database is malformed input, not a server error."""
    lee = login("lee")
    assert_error(client.get(f"{API}/missions/{2**70}", headers=lee), 422, "validation_error")
    response = client.post(
        f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 1, "crew_profile_id": 2**70}
    )
    assert_error(response, 422, "validation_error")


# --- 503 ----------------------------------------------------------------------------------


def test_503_busy_when_the_write_lock_is_held(db_path, login):
    """Another writer holds the lock past the busy timeout: retryable 503 `busy`."""
    app = create_app(Settings(database_path=db_path, busy_timeout_ms=50))
    with TestClient(app) as c:
        token = c.post(
            f"{API}/auth/login",
            json={"email": "ruth@aurora.example", "password": "orbital launch window"},
        ).json()["token"]
        blocker = sqlite3.connect(db_path, isolation_level=None)
        blocker.execute("BEGIN IMMEDIATE")
        try:
            response = c.post(
                f"{API}/skills", headers={"Authorization": f"Bearer {token}"}, json={"name": "X"}
            )
        finally:
            blocker.execute("ROLLBACK")
            blocker.close()
    error = assert_error(response, 503, "busy")
    assert error["message"] == "The database is busy; try again"


# --- 500 ----------------------------------------------------------------------------------


@pytest.fixture
def broken_client(settings):
    """The real app with one extra route that fails with an unexpected error, as a bug would.
    The client returns the 500 response instead of re-raising the error into the test."""
    app = create_app(settings)

    @app.get(f"{API}/boom")
    def boom() -> None:
        raise ValueError("secret detail: /srv/db password=hunter2")

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_500_unexpected_error_uses_the_same_shape_and_hides_the_details(broken_client, caplog):
    with caplog.at_level("ERROR", logger="mission_control.api"):
        response = broken_client.get(f"{API}/boom")
    error = assert_error(response, 500, "internal_error")
    assert error["message"] == "Something went wrong on the server"
    assert error["problems"] == [
        {"code": "internal_error", "message": "Something went wrong on the server", "refs": {}}
    ]
    assert "secret" not in response.text and "ValueError" not in response.text
    assert "Traceback" not in response.text
    logged = [r.getMessage() for r in caplog.records if r.name == "mission_control.api.errors"]
    assert logged == ["Unhandled ValueError on GET /api/v1/boom"]


def test_500_handler_leaves_expected_refusals_to_their_own_handlers(broken_client, login):
    """Refusals, malformed input and unknown routes keep their own status and code."""
    lee = login("lee")
    assert_error(broken_client.get(f"{API}/missions/999", headers=lee), 404, "not_found")
    assert_error(broken_client.get(f"{API}/missions/x", headers=lee), 422, "validation_error")
    assert_error(broken_client.get(f"{API}/nowhere", headers=lee), 404, "not_found")
    assert_error(broken_client.get(f"{API}/me"), 401, "unauthenticated")
    response = broken_client.patch(f"{API}/missions/5", headers=lee, json={"name": "Renamed"})
    assert_error(response, 409, "mission_frozen")
    assert_error(broken_client.post(f"{API}/missions/5"), 405, "method_not_allowed")


# --- Settings and startup -----------------------------------------------------------------


def test_settings_defaults():
    s = Settings.from_env({})
    assert s.database_path == Path("mission_control.db")
    assert s.busy_timeout_ms == 5000
    assert s.token_ttl_hours == 12


def test_settings_read_from_the_environment(tmp_path):
    s = Settings.from_env(
        {
            "MC_DATABASE_PATH": str(tmp_path / "x.db"),
            "MC_DB_BUSY_TIMEOUT_MS": "250",
            "MC_TOKEN_TTL_HOURS": "3",
        }
    )
    assert s == Settings(database_path=tmp_path / "x.db", busy_timeout_ms=250, token_ttl_hours=3)


@pytest.mark.parametrize("env", [{"MC_DB_BUSY_TIMEOUT_MS": "soon"}, {"MC_TOKEN_TTL_HOURS": "0"}])
def test_settings_refuse_bad_values(env):
    with pytest.raises(ValueError, match=next(iter(env))):
        Settings.from_env(env)


def test_busy_timeout_setting_reaches_each_connection(settings, client, login, monkeypatch):
    from mission_control.api import deps

    seen = []
    real_connect = deps.connect

    def spy(path, *, busy_timeout_ms):
        seen.append((Path(path), busy_timeout_ms))
        return real_connect(path, busy_timeout_ms=busy_timeout_ms)

    monkeypatch.setattr(deps, "connect", spy)
    client.get(f"{API}/me", headers=login("lee"))
    assert seen and all(s == (settings.database_path, 5000) for s in seen)


def test_token_lifetime_setting_is_used(db_path):
    with TestClient(create_app(Settings(database_path=db_path, token_ttl_hours=1))) as c:
        c.post(
            f"{API}/auth/login",
            json={"email": "lee@aurora.example", "password": "orbital launch window"},
        )
    conn = sqlite3.connect(db_path)
    created, expires = conn.execute(
        "SELECT created_at, expires_at FROM auth_tokens ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    gap = datetime.fromisoformat(expires) - datetime.fromisoformat(created)
    assert gap.total_seconds() == 3600


def test_dummy_hash_is_built_at_startup(db_path, monkeypatch):
    """Login for an unknown email verifies against a dummy hash. It's made when the app starts,
    so the first unknown-email login costs the same as any other."""
    built = []
    real = security.dummy_hash
    monkeypatch.setattr(security, "dummy_hash", lambda: built.append(1) or real())
    with TestClient(create_app(Settings(database_path=db_path))):
        assert built, "dummy hash built during startup, before any request"


def test_startup_creates_the_schema_on_an_empty_database(tmp_path):
    path = tmp_path / "fresh.db"
    with TestClient(create_app(Settings(database_path=path))) as c:
        assert c.get("/health").json() == {"status": "ok"}
    conn = sqlite3.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    conn.close()
