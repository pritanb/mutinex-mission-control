"""The CLI against the real API in-process (no stand-in): every read command renders the real
responses, and S4 runs end to end (PRD S4, AC-14, AC-15, AC-24, AC-27; design §11 CLI tests).
S1 runs through the installed binaries in test_readme_smoke.py.
"""

import json

import pytest
from cli_fakes import FakeApi, Mc
from fastapi.testclient import TestClient

from mission_control.api.app import create_app
from mission_control.infra import security
from mission_control.infra.db import connect, init_db
from mission_control.infra.settings import Settings
from mission_control.seed.data import DEMO_PASSWORD
from mission_control.seed.loader import load_seed


@pytest.fixture
def server(tmp_path):
    path = tmp_path / "mission_control.db"
    conn = connect(path)
    init_db(conn)
    load_seed(conn, password_hash=security.hash_password(DEMO_PASSWORD))
    conn.close()
    with TestClient(create_app(Settings(database_path=path))) as client:
        yield client


@pytest.fixture
def as_(server, tmp_path):
    """`as_("lee")` is an `mc` logged in as that seeded user, with its own config directory."""
    people: dict[str, Mc] = {}

    def _as(who: str):
        if who not in people:
            org = "helix" if who in {"sam", "priya", "kai"} else "aurora"
            mc = Mc(api=FakeApi(), config_dir=tmp_path / who)
            logged_in = mc(
                "login", "--email", f"{who}@{org}.example", input=f"{DEMO_PASSWORD}\n", http=server
            )
            assert logged_in.exit_code == 0, logged_in.stderr
            people[who] = mc

        def run(*args: str, input: str | None = None):
            return people[who](*args, input=input, http=server)

        return run

    return _as


@pytest.mark.parametrize(
    ("who", "command"),
    [
        ("lee", "whoami"),
        ("lee", "inbox"),
        ("nora", "inbox"),
        ("ingrid", "inbox"),
        ("lee", "missions list"),
        ("lee", "missions show 1"),
        ("lee", "missions show 6"),
        ("lee", "missions match 1"),
        ("lee", "missions history 6"),
        ("lee", "crew list"),
        ("lee", "crew show fay@aurora.example"),
        ("lee", "crew history chen@aurora.example"),
        ("ben", "me show"),
        ("ben", "me unavailable list"),
        ("ben", "assignments list"),
        ("ruth", "users list"),
        ("ruth", "skills list"),
        ("ruth", "org show"),
    ],
)
def test_every_read_command_renders_the_real_response(as_, who, command):
    mc = as_(who)
    for args in (command.split(), [*command.split(), "--json"]):
        result = mc(*args)
        assert result.exit_code == 0, (args, result.stderr, result.exception)
        assert result.exception is None
        assert result.stdout.strip()


def test_ac24_a_lead_sees_fay_busy_but_not_why(as_):
    shown = as_("lee")("crew", "show", "fay@aurora.example")
    assert "5–8 Mar 2027" in shown.stdout
    assert "Medical" not in shown.stdout


def test_s4_through_the_cli_against_the_real_api(as_):
    lee, nora, chen = as_("lee"), as_("nora"), as_("chen")

    gus = lee(
        "missions", "propose", "1", "--slot", "Flight Engineer", "--crew", "gus@aurora.example"
    )
    assert gus.exit_code == 1
    assert "Station Reboost" in gus.stderr

    fay = lee("missions", "propose", "1", "--slot", "Commander", "--crew", "fay@aurora.example")
    assert fay.exit_code == 1
    assert "unavailable" in fay.stderr

    on_reboost = nora(
        "missions", "propose", "3", "--slot", "Engineer", "--crew", "chen@aurora.example"
    )
    on_gateway = lee(
        "missions", "propose", "1", "--slot", "Flight Engineer", "--crew", "chen@aurora.example"
    )
    assert on_reboost.exit_code == on_gateway.exit_code == 0

    pending = chen("assignments", "list", "--pending", "--json")
    ids = {a["mission_name"]: a["assignment_id"] for a in json.loads(pending.stdout)}
    assert chen("assignments", "accept", str(ids["Station Reboost"])).exit_code == 0
    second = chen("assignments", "accept", str(ids["Lunar Gateway Resupply"]))
    assert second.exit_code == 1
    assert "Station Reboost" in second.stderr


def test_ac27_another_organisations_mission_is_not_found_through_the_cli(as_):
    result = as_("sam")("missions", "show", "1")
    assert result.exit_code == 1
    assert "Mission 1 not found" in result.stderr


def test_ac26_deactivating_shows_in_the_user_list(as_):
    ruth = as_("ruth")
    assert ruth("users", "deactivate", "hana@aurora.example").exit_code == 1  # still on Telescope
    assert ruth("users", "deactivate", "fay@aurora.example").exit_code == 0
    listed = [line for line in ruth("users", "list").stdout.splitlines() if "Fay" in line]
    assert listed and listed[0].rstrip().endswith("deactivated")
