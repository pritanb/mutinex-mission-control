"""M17: `mc-admin`, the operator commands that work on the database file directly (design §2,
§11). Covers init-db, seed (PRD §9 data, R10) and create-org (PRD T3, P10).

Every test uses a database under `tmp_path`, never the repo's or the user's own.
"""

import sqlite3

import pytest
from typer.testing import CliRunner

from mission_control import admin_cli
from mission_control.infra import security
from mission_control.infra.db import connect
from mission_control.seed import data
from mission_control.services import auth

PASSPHRASE = "a long enough director passphrase"


@pytest.fixture(autouse=True)
def _no_ambient_settings(monkeypatch):
    """The developer's own settings must not point a test at a real database."""
    for name in ("MC_DATABASE_PATH", "MC_DB_BUSY_TIMEOUT_MS", "MC_TOKEN_TTL_HOURS"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "admin.db"


@pytest.fixture
def admin(db_path):
    """Run `mc-admin ARGS` in-process against `db_path`."""
    runner = CliRunner()

    def run(*args, input=None, env=None):
        environment = {"MC_DATABASE_PATH": str(db_path), **(env or {})}
        return runner.invoke(admin_cli.app, list(args), input=input, env=environment)

    return run


def query(path, sql, *args):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def count(path, table):
    return query(path, f"SELECT count(*) FROM {table}")[0][0]


def assert_no_traceback(result):
    assert "Traceback" not in result.stdout + result.stderr
    assert result.exception is None or isinstance(result.exception, SystemExit)


# --- Help ---------------------------------------------------------------------------------


def test_m17_bare_command_and_help_list_every_command(admin):
    for args in ((), ("--help",)):
        result = admin(*args)
        assert result.exit_code == 0
        for name in ("init-db", "seed", "create-org"):
            assert name in result.stdout


def test_m17_each_command_has_help_with_an_example(admin):
    for name in ("init-db", "seed", "create-org"):
        result = admin(name, "--help")
        assert result.exit_code == 0
        assert "Example" in result.stdout
        assert f"mc-admin {name}" in result.stdout


def test_m17_version(admin):
    result = admin("--version")
    assert result.exit_code == 0
    assert result.stdout.startswith("mc-admin ")


def test_m17_unknown_command_is_a_usage_error(admin):
    result = admin("seeed")
    assert result.exit_code == 2


# --- Database location --------------------------------------------------------------------


def test_m17_init_db_creates_the_schema_at_mc_database_path(admin, db_path):
    result = admin("init-db")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == f"Created an empty database at {db_path.resolve()}.\n"
    assert query(db_path, "PRAGMA user_version") == [(1,)]
    assert count(db_path, "organisations") == 0
    assert "mc-admin seed" in result.stderr  # next steps go to stderr


def test_m17_init_db_twice_changes_nothing(admin, db_path):
    admin("init-db")
    result = admin("init-db")

    assert result.exit_code == 0
    assert result.stdout == f"The database at {db_path.resolve()} is already set up.\n"


def test_m17_database_defaults_to_mission_control_db_in_the_working_directory(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(admin_cli.app, ["init-db"])

    assert result.exit_code == 0, result.stderr
    assert (tmp_path / "mission_control.db").exists()


def test_m17_a_folder_that_doesnt_exist_is_reported_with_a_fix(admin, tmp_path):
    missing = tmp_path / "nowhere" / "mc.db"
    result = admin("init-db", env={"MC_DATABASE_PATH": str(missing)})

    assert result.exit_code == 1
    assert f"Can't open the database at {missing.resolve()}" in result.stderr
    assert "MC_DATABASE_PATH" in result.stderr
    assert_no_traceback(result)


def test_m17_a_file_that_isnt_a_database_is_reported(admin, db_path):
    db_path.write_text("not a database, just some text " * 100)
    result = admin("init-db")

    assert result.exit_code == 1
    assert f"{db_path.resolve()} isn't a Mission Control database" in result.stderr
    assert_no_traceback(result)


def test_m17_an_unsupported_schema_version_is_reported(admin, db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA user_version = 7")
    conn.close()

    for args in (("init-db",), ("seed",)):
        result = admin(*args)
        assert result.exit_code == 1
        assert "schema version 7" in result.stderr
        assert "mc-admin seed --reset" in result.stderr
        assert_no_traceback(result)


def test_m17_a_bad_busy_timeout_setting_is_a_usage_error(admin):
    result = admin("init-db", env={"MC_DB_BUSY_TIMEOUT_MS": "soon"})

    assert result.exit_code == 2
    assert "MC_DB_BUSY_TIMEOUT_MS must be a whole number" in result.stderr
    assert_no_traceback(result)


# --- seed ---------------------------------------------------------------------------------


def test_r10_seed_loads_the_prd_demo_data(admin, db_path):
    result = admin("seed")

    assert result.exit_code == 0, result.stderr
    assert f"Loaded the demo data into {db_path.resolve()}." in result.stdout
    assert "2 organisations, 19 users and 8 missions" in result.stdout
    assert 'password is "orbital launch window"' in result.stdout
    assert "mc login --email lee@aurora.example" in result.stderr
    assert count(db_path, "organisations") == 2
    assert count(db_path, "users") == 19
    assert count(db_path, "missions") == 8
    assert count(db_path, "assignments") == 10


def test_r10_every_demo_user_has_the_hashed_demo_passphrase(admin, db_path):
    admin("seed")

    hashes = [h for (h,) in query(db_path, "SELECT password_hash FROM users")]
    assert len(hashes) == 19
    for stored in hashes:
        assert stored != data.DEMO_PASSWORD
        assert stored.startswith("$argon2id$")
        assert security.verify_password(stored, data.DEMO_PASSWORD)


def test_r10_a_seeded_user_can_log_in_with_the_demo_passphrase(admin, db_path):
    admin("seed")
    conn = connect(db_path)
    try:
        session = auth.login(conn, "lee@aurora.example", data.DEMO_PASSWORD)
    finally:
        conn.close()
    assert session.user.name == "Lee Park"


def test_m17_seed_fills_an_empty_schema(admin, db_path):
    admin("init-db")
    result = admin("seed")

    assert result.exit_code == 0, result.stderr
    assert count(db_path, "users") == 19


def test_m17_seed_refuses_a_database_that_already_has_data(admin, db_path):
    admin("seed")
    before = query(db_path, "SELECT id, password_hash FROM users ORDER BY id")

    result = admin("seed")

    assert result.exit_code == 1
    assert result.stderr.startswith(
        f"Error: The database at {db_path.resolve()} already has data. Nothing was changed.\n"
    )
    assert "mc-admin seed --reset" in result.stderr
    assert "deletes everything" in result.stderr
    assert query(db_path, "SELECT id, password_hash FROM users ORDER BY id") == before
    assert count(db_path, "organisations") == 2
    assert_no_traceback(result)


def test_m17_seed_reset_replaces_everything_with_the_demo_data(admin, db_path):
    admin("seed")
    admin(
        "create-org",
        "--name",
        "Orion Labs",
        "--director-email",
        "zoe@orion.example",
        "--director-name",
        "Zoe Lin",
        input=PASSPHRASE + "\n",
    )
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE missions SET name = 'Renamed' WHERE id = 1")
    conn.commit()
    conn.close()
    assert count(db_path, "organisations") == 3

    result = admin("seed", "--reset")

    assert result.exit_code == 0, result.stderr
    assert f"Replaced the database at {db_path.resolve()} with the demo data." in result.stdout
    assert count(db_path, "organisations") == 2
    assert query(db_path, "SELECT name FROM missions WHERE id = 1") == [("Lunar Gateway Resupply",)]


def test_m17_seed_reset_removes_the_old_write_ahead_log_too(admin, db_path):
    admin("seed")
    stale = db_path.with_name(db_path.name + "-wal")
    stale.write_bytes(b"stale")  # a leftover log must not be replayed into the new file

    result = admin("seed", "--reset")

    assert result.exit_code == 0, result.stderr
    assert count(db_path, "users") == 19


def test_m17_seed_reset_works_when_there_is_no_database_yet(admin, db_path):
    result = admin("seed", "--reset")

    assert result.exit_code == 0, result.stderr
    assert f"Loaded the demo data into {db_path.resolve()}." in result.stdout
    assert count(db_path, "users") == 19


# --- create-org ---------------------------------------------------------------------------


def create_orion(admin, *extra, input=PASSPHRASE + "\n"):
    return admin(
        "create-org",
        "--name",
        "Orion Labs",
        "--director-email",
        "zoe@orion.example",
        "--director-name",
        "Zoe Lin",
        *extra,
        input=input,
    )


def test_t3_create_org_makes_an_organisation_and_its_first_director(admin, db_path):
    result = create_orion(admin)

    assert result.exit_code == 0, result.stderr
    assert result.stdout.startswith(
        "Created Orion Labs with Zoe Lin (zoe@orion.example) as its first Director.\n"
    )
    assert "Missions need 1 approval" in result.stdout
    assert "mc login --email zoe@orion.example" in result.stderr
    assert query(db_path, "SELECT name, slug, required_approvals FROM organisations") == [
        ("Orion Labs", "orion-labs", 1)
    ]
    assert query(db_path, "SELECT email, name, role, is_active FROM users") == [
        ("zoe@orion.example", "Zoe Lin", "director", 1)
    ]
    # Directors get a crew profile only when they ask for one; the catalogue starts empty.
    assert count(db_path, "crew_profiles") == 0
    assert count(db_path, "skills") == 0


def test_t3_the_new_director_can_log_in_with_their_password(admin, db_path):
    create_orion(admin)
    stored = query(db_path, "SELECT password_hash FROM users")[0][0]
    assert stored.startswith("$argon2id$") and PASSPHRASE not in stored

    conn = connect(db_path)
    try:
        session = auth.login(conn, "zoe@orion.example", PASSPHRASE)
    finally:
        conn.close()
    assert session.user.role == "director"


def test_t3_create_org_sits_alongside_the_demo_data(admin, db_path):
    admin("seed")
    result = create_orion(admin)

    assert result.exit_code == 0, result.stderr
    assert count(db_path, "organisations") == 3
    org_id = query(db_path, "SELECT org_id FROM users WHERE email = 'zoe@orion.example'")[0][0]
    assert org_id not in (1, 2)


def test_t3_create_org_asks_for_the_password_twice_with_input_hidden(admin, monkeypatch):
    asked = []

    def getpass(prompt):
        asked.append(prompt)
        return PASSPHRASE

    monkeypatch.setattr(admin_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(admin_cli.getpass, "getpass", getpass)

    result = create_orion(admin, input="")

    assert result.exit_code == 0, result.stderr
    assert asked == ["Password for Zoe Lin: ", "Repeat the password: "]


def test_t3_passwords_that_dont_match_change_nothing(admin, db_path, monkeypatch):
    answers = iter([PASSPHRASE, PASSPHRASE + "!"])
    monkeypatch.setattr(admin_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(admin_cli.getpass, "getpass", lambda prompt: next(answers))

    result = create_orion(admin, input="")

    assert result.exit_code == 2
    assert result.stderr == "Error: The passwords don't match. Nothing was changed.\n"
    assert count(db_path, "organisations") == 0


def test_t3_ctrl_c_at_the_password_prompt_changes_nothing(admin, db_path, monkeypatch):
    def interrupted(prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr(admin_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(admin_cli.getpass, "getpass", interrupted)

    result = create_orion(admin, input="")

    assert result.exit_code == 130
    assert "Nothing was changed" in result.stderr
    assert count(db_path, "organisations") == 0
    assert_no_traceback(result)


def test_t3_without_a_terminal_or_a_piped_password_it_says_how(admin, db_path):
    result = create_orion(admin, input="")

    assert result.exit_code == 2
    assert "No password given, and there's no terminal to ask on." in result.stderr
    assert "pipe the password on stdin" in result.stderr
    assert count(db_path, "organisations") == 0


def test_t3_the_password_is_never_a_flag(admin, db_path):
    result = create_orion(admin, "--password", PASSPHRASE)

    assert result.exit_code == 2
    assert "No such option: --password" in result.stderr
    assert not db_path.exists()  # refused before the database was touched


def test_p10_a_password_shorter_than_15_characters_is_refused(admin, db_path):
    result = create_orion(admin, input="fourteen chars\n")

    assert result.exit_code == 2
    assert result.stderr.startswith(
        "Error: The password must be at least 15 characters. Nothing was changed.\n"
    )
    assert count(db_path, "organisations") == 0


def test_p10_a_15_character_passphrase_is_enough(admin):
    result = create_orion(admin, input="fifteen chars!!\n")

    assert result.exit_code == 0, result.stderr


def test_t3_an_email_already_in_use_is_refused_before_asking_for_a_password(
    admin, db_path, monkeypatch
):
    admin("seed")
    monkeypatch.setattr(admin_cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(admin_cli.getpass, "getpass", lambda prompt: pytest.fail("asked"))

    result = admin(
        "create-org",
        "--name",
        "Orion Labs",
        "--director-email",
        "LEE@aurora.example",
        "--director-name",
        "Lee Again",
    )

    assert result.exit_code == 1
    assert result.stderr.startswith(
        "Error: The email address LEE@aurora.example is already in use. Nothing was changed.\n"
    )
    assert count(db_path, "organisations") == 2


def test_t3_an_organisation_with_the_same_name_is_refused(admin, db_path):
    create_orion(admin)
    result = admin(
        "create-org",
        "--name",
        "orion  LABS",
        "--director-email",
        "max@orion.example",
        "--director-name",
        "Max Lin",
        input=PASSPHRASE + "\n",
    )

    assert result.exit_code == 1
    assert result.stderr.startswith(
        "Error: An organisation called Orion Labs already exists. Nothing was changed.\n"
    )
    assert count(db_path, "organisations") == 1
    assert count(db_path, "users") == 1


@pytest.mark.parametrize(
    "flag, value, message",
    [
        ("--name", "   ", "The organisation needs a name."),
        ("--name", "!!!", "The organisation's name needs at least one letter or number."),
        ("--director-name", " ", "The Director needs a name."),
        ("--director-email", " ", "The Director needs an email address."),
    ],
)
def test_t3_blank_values_are_usage_errors(admin, db_path, flag, value, message):
    values = {
        "--name": "Orion Labs",
        "--director-email": "zoe@orion.example",
        "--director-name": "Zoe Lin",
    }
    values[flag] = value
    args = [part for pair in values.items() for part in pair]

    result = admin("create-org", *args, input=PASSPHRASE + "\n")

    assert result.exit_code == 2
    assert result.stderr == f"Error: {message}\n"
    assert not db_path.exists() or count(db_path, "organisations") == 0


def test_t3_missing_flags_are_usage_errors(admin):
    result = admin("create-org", "--name", "Orion Labs", input=PASSPHRASE + "\n")

    assert result.exit_code == 2
    assert "--director-email" in result.stderr


def test_t3_names_and_emails_are_trimmed(admin, db_path):
    result = admin(
        "create-org",
        "--name",
        "  Orion Labs ",
        "--director-email",
        " zoe@orion.example ",
        "--director-name",
        " Zoe Lin ",
        input=PASSPHRASE + "\n",
    )

    assert result.exit_code == 0, result.stderr
    assert query(db_path, "SELECT name FROM organisations") == [("Orion Labs",)]
    assert query(db_path, "SELECT email, name FROM users") == [("zoe@orion.example", "Zoe Lin")]
