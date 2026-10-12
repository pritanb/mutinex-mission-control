"""API test setup: a freshly seeded database file per test, an in-process client against it,
and a helper that logs in as a seeded user.

Seed ids (PRD §9): a crew profile's id equals its user's id. Emails are
`<first name>@<org slug>.example`, e.g. lee@aurora.example, kai@helix.example.
"""

import pytest
from fastapi.testclient import TestClient

from mission_control.api.app import create_app
from mission_control.infra import security
from mission_control.infra.db import connect, init_db
from mission_control.infra.settings import Settings
from mission_control.seed.data import DEMO_PASSWORD
from mission_control.seed.loader import load_seed


@pytest.fixture
def db_path(tmp_path):
    """The PRD seed, with a real (cheap in tests) Argon2 hash of the demo passphrase."""
    path = tmp_path / "mission_control.db"
    conn = connect(path)
    init_db(conn)
    load_seed(conn, password_hash=security.hash_password(DEMO_PASSWORD))
    conn.close()
    return path


@pytest.fixture
def settings(db_path):
    return Settings(database_path=db_path)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def db(db_path):
    """A separate connection to the same file, for checking what the API wrote."""
    conn = connect(db_path)
    yield conn
    conn.close()


@pytest.fixture
def login(client):
    """`login("lee")` logs in as a seeded user and returns the request headers to use."""

    def _login(who: str, org: str | None = None, password: str = DEMO_PASSWORD) -> dict:
        email = who if "@" in who else f"{who}@{org or _org_of(who)}.example"
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return _login


_HELIX = {"sam", "priya", "kai", "lena", "omar", "tess"}


def _org_of(first_name: str) -> str:
    return "helix" if first_name in _HELIX else "aurora"


def snapshot(conn) -> dict[str, list[tuple]]:
    """Every table's rows, to prove a request changed nothing."""
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


@pytest.fixture
def snap(db):
    return lambda: snapshot(db)
