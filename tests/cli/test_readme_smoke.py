"""M17 (design §9): smoke-test the README. Its `mc-admin`, `mc-server` and `mc` commands are read
from the README itself and run for real, in order, as separate processes.

- The commands are every `uv run mc…` line inside a ```bash block. A line whose comment starts
  with "refused" must exit 1; every other line must exit 0.
- `mc-admin` and `mc` run as the installed console scripts (what `uv run` starts), in a temporary
  working folder with a temporary HOME, so the default `mission_control.db` and the saved session
  never touch the developer's own.
- `mc-server` is started in-process on a free port instead of 8000, and `mc` is pointed at it with
  `MC_API_URL`.
- Passwords are piped on stdin, which the README says works without a terminal.
"""

import os
import shlex
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

from mission_control.infra import security
from mission_control.seed.data import DEMO_PASSWORD

README = Path(__file__).resolve().parents[2] / "README.md"
PROGRAMS = ("mc", "mc-admin", "mc-server")
NEW_DIRECTOR_PASSWORD = "a passphrase for the new director"


@dataclass(frozen=True)
class Step:
    line: int  # in the README, for failure messages
    args: tuple[str, ...]  # without `uv run`, e.g. ("mc", "login", "--email", "lee@...")
    refused: bool

    @property
    def program(self) -> str:
        return self.args[0]

    def __str__(self) -> str:
        return f"README.md:{self.line}: {shlex.join(self.args)}"


def readme_steps() -> list[Step]:
    steps = []
    in_bash = False
    for number, text in enumerate(README.read_text(encoding="utf-8").splitlines(), start=1):
        if text.startswith("```"):
            in_bash = not in_bash and text.strip() == "```bash"
            continue
        if not in_bash:
            continue
        command, _, comment = text.partition(" #")
        words = shlex.split(command)
        if words[:2] == ["uv", "run"] and len(words) > 2 and words[2] in PROGRAMS:
            refused = comment.strip().lower().startswith("refused")
            steps.append(Step(number, tuple(words[2:]), refused))
    return steps


# --- The command list ---------------------------------------------------------------------


def test_m17_readme_quick_start_seeds_starts_the_server_then_logs_in():
    first = [s.args for s in readme_steps()[:3]]
    assert first == [
        ("mc-admin", "seed", "--reset"),
        ("mc-server",),
        ("mc", "login", "--email", "lee@aurora.example"),
    ]


def as_user(steps: list[Step]) -> list[tuple[str | None, Step]]:
    """Each step with the email of whoever the last `mc login` signed in."""
    who, result = None, []
    for step in steps:
        if step.args[:3] == ("mc", "login", "--email"):
            who = step.args[3]
        result.append((who, step))
    return result


def test_s1_readme_demo_follows_the_golden_path_in_order():
    s1_actions = {"match", "accept", "submit", "approve", "complete", "history"}
    done = [
        (who.split("@")[0], " ".join(step.args[1:]))
        for who, step in as_user(readme_steps())
        if step.program == "mc"
        and len(step.args) > 2
        and step.args[2] in s1_actions
        and step.args[3] in ("1", "11", "12", "13")
    ]
    assert done == [
        ("lee", "missions match 1"),
        ("lee", "missions match 1 --apply"),
        ("ana", "assignments accept 11"),
        ("chen", "assignments accept 12"),
        ("dana", "assignments accept 13"),
        ("lee", "missions submit 1"),
        ("ruth", "missions approve 1"),
        ("marco", "missions approve 1"),
        ("ingrid", "missions approve 1"),
        ("lee", "missions complete 1"),
        ("lee", "missions history 1"),
    ]


def test_ac8_ac27_only_ruths_approval_and_the_cross_tenant_read_are_expected_to_fail():
    refused = [(who, step.args) for who, step in as_user(readme_steps()) if step.refused]
    assert refused == [
        ("ruth@aurora.example", ("mc", "missions", "approve", "1")),
        ("sam@helix.example", ("mc", "missions", "show", "1")),
    ]


# --- Running it ---------------------------------------------------------------------------


@pytest.fixture
def workdir(tmp_path):
    folder = tmp_path / "work"
    (tmp_path / "home").mkdir()
    folder.mkdir()
    return folder


def _environment(workdir: Path, api_url: str | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("MC_")}
    env.update(HOME=str(workdir.parent / "home"), NO_COLOR="1")
    if api_url:
        env["MC_API_URL"] = api_url
    return env


def _script(name: str) -> str:
    path = Path(sys.executable).parent / name
    if not path.exists():
        pytest.fail(f"{name} isn't installed in this environment. Run `uv sync` first.")
    return str(path)


def _stdin(step: Step) -> str:
    if step.args[:2] == ("mc", "login"):
        return DEMO_PASSWORD + "\n"
    if step.args[:2] == ("mc-admin", "create-org"):
        return NEW_DIRECTOR_PASSWORD + "\n"
    return ""


def _run(step: Step, workdir: Path, env: dict[str, str]) -> None:
    result = subprocess.run(
        [_script(step.program), *step.args[1:]],
        cwd=workdir,
        env=env,
        input=_stdin(step),
        capture_output=True,
        text=True,
        timeout=60,
    )
    expected = 1 if step.refused else 0
    assert result.returncode == expected, (
        f"{step}\nexpected exit {expected}, got {result.returncode}\n"
        f"--- stdout\n{result.stdout}--- stderr\n{result.stderr}"
    )
    assert "Traceback" not in result.stdout + result.stderr, str(step)


@contextmanager
def _server(database: Path) -> Generator[str]:
    """The API app on a free local port, in a background thread, for as long as the block runs."""
    import uvicorn

    from mission_control.api.app import create_app
    from mission_control.infra.settings import Settings

    app = create_app(Settings(database_path=database))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            pytest.fail("the API server didn't start")
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=15)


def _rows(database: Path, sql: str) -> list[tuple]:
    conn = sqlite3.connect(database)
    try:
        return [tuple(r) for r in conn.execute(sql)]
    finally:
        conn.close()


def test_r10_readme_mc_admin_commands_run(workdir):
    """Runs now: only `mc-admin` is needed."""
    env = _environment(workdir, api_url=None)
    steps = [s for s in readme_steps() if s.program == "mc-admin"]
    assert [s.args[1] for s in steps] == ["seed", "init-db", "create-org"]

    for step in steps:
        _run(step, workdir, env)

    database = workdir / "mission_control.db"
    assert _rows(database, "SELECT name FROM organisations ORDER BY id") == [
        ("Aurora Space Agency",),
        ("Helix Orbital",),
        ("Orion Labs",),
    ]
    lee = _rows(database, "SELECT password_hash FROM users WHERE email = 'lee@aurora.example'")
    assert security.verify_password(lee[0][0], DEMO_PASSWORD)
    zoe = _rows(database, "SELECT password_hash, role FROM users WHERE email = 'zoe@orion.example'")
    assert zoe[0][1] == "director"
    assert security.verify_password(zoe[0][0], NEW_DIRECTOR_PASSWORD)


def test_ac1_readme_quick_start_and_demo_run_end_to_end(workdir):
    database = workdir / "mission_control.db"
    steps = readme_steps()
    server_at = next(i for i, s in enumerate(steps) if s.program == "mc-server")

    env = _environment(workdir, api_url=None)
    for step in steps[:server_at]:
        _run(step, workdir, env)

    with _server(database) as url:
        env = _environment(workdir, api_url=url)
        for step in steps[server_at + 1 :]:
            assert step.program != "mc-server", f"{step}: the server is already running"
            _run(step, workdir, env)

    assert _rows(database, "SELECT status FROM missions WHERE id = 1") == [("completed",)]
    assert _rows(
        database, "SELECT crew_profile_id, status FROM assignments WHERE mission_id = 1 ORDER BY id"
    ) == [(6, "completed"), (8, "completed"), (9, "completed")]
    events = [e for (e,) in _rows(database, "SELECT event FROM audit_events WHERE mission_id = 1")]
    assert events.count("mission.approved") == 2  # Marco and Ingrid; Ruth's refusal wrote nothing
    # Completing records the mission first, then each accepted assignment it completes.
    assert events[-4:] == ["mission.completed"] + ["assignment.completed"] * 3
