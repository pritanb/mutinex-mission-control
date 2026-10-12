"""`mc-admin`: operator commands for the machine that runs the server. They work on the database
file directly rather than through the API: set up the schema, load the demo data, and create an
organisation with its first Director (there is no self-service signup)."""

import getpass
import os
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

import typer

from mission_control.cli.base import HelpWhenBare, version_flag
from mission_control.domain.enums import Role
from mission_control.domain.passwords import (
    MIN_PASSWORD_LENGTH,
    PasswordTooShort,
    validate_password,
)
from mission_control.infra import platform, security
from mission_control.infra.db import DatabaseBusy, UnsupportedSQLite, connect, init_db, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.settings import Settings
from mission_control.seed import data
from mission_control.seed.loader import load_seed

OK, FAILED, USAGE, INTERRUPTED = 0, 1, 2, 130
_RESET = "uv run mc-admin seed --reset (deletes everything in it)"


class Failure(Exception):
    """Something to tell the operator, with an optional next step, and the exit code to use."""

    def __init__(self, message: str, *, hint: str | None = None, exit_code: int = FAILED):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.exit_code = exit_code


class _Group(HelpWhenBare):
    """A bare `mc-admin` prints its help and exits 0. Failures are reported in words with their
    exit code, never as a traceback."""

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except Failure as failure:
            _error(failure.message, failure.hint)
            raise typer.Exit(failure.exit_code) from None
        except KeyboardInterrupt:
            _error("Interrupted. Nothing was changed.")
            raise typer.Exit(INTERRUPTED) from None


app = typer.Typer(
    cls=_Group,
    name="mc-admin",
    rich_markup_mode=None,
    add_completion=False,
    pretty_exceptions_enable=False,
)


def _example(*lines: str) -> str:
    heading = "Example:" if len(lines) == 1 else "Examples:"
    # \b stops the help formatter from re-wrapping the lines.
    return "\b\n" + heading + "\n" + "\n".join(f"  {line}" for line in lines)


Version = Annotated[bool, version_flag("mc-admin")]


@app.callback()
def root(show_version: Version = False) -> None:
    """Operator commands for Mission Control.

    They work on the database file directly, so run them on the machine that runs mc-server.
    The file is MC_DATABASE_PATH, or mission_control.db in the current folder.

    Exit codes: 0 OK, 1 refused or failed, 2 usage, 130 interrupted.
    """


# --- Commands -----------------------------------------------------------------------------


@app.command("init-db", epilog=_example("mc-admin init-db"))
def init_database() -> None:
    """Create an empty database with the current schema. Safe to run again."""
    settings = _settings()
    path = _shown(settings.database_path)
    with _database(settings) as conn:
        created = _prepare(conn, path)
    if created:
        typer.echo(f"Created an empty database at {path}.")
        _next_steps(["uv run mc-admin seed", "uv run mc-admin create-org --help"])
    else:
        typer.echo(f"The database at {path} is already set up.")


@app.command("seed", epilog=_example("mc-admin seed", "mc-admin seed --reset"))
def seed(
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Delete the database file first, and everything in it"),
    ] = False,
) -> None:
    """Load the demo organisations, people and missions.

    Every demo user's password is the demo passphrase. Without --reset, a database that already
    has data is left as it is. Stop mc-server before using --reset.
    """
    settings = _settings()
    path = _shown(settings.database_path)
    password_hash = security.hash_password(data.DEMO_PASSWORD)  # slow, so before any lock
    replaced = _delete_database(settings.database_path) if reset else False
    with _database(settings) as conn:
        _prepare(conn, path)
        try:
            load_seed(conn, password_hash)
        except RuntimeError:  # the database already has organisations
            raise Failure(
                f"The database at {path} already has data. Nothing was changed.",
                hint=f"Start over with only the demo data: {_RESET}",
            ) from None

    if replaced:
        typer.echo(f"Replaced the database at {path} with the demo data.")
    else:
        typer.echo(f"Loaded the demo data into {path}.")
    typer.echo(
        f"  {len(data.ORGANISATIONS)} organisations, {len(data.USERS)} users and "
        f'{len(data.MISSIONS)} missions. Every user\'s password is "{data.DEMO_PASSWORD}".'
    )
    _next_steps(["uv run mc-server", "uv run mc login --email lee@aurora.example"])


@app.command(
    "create-org",
    epilog=_example(
        'mc-admin create-org --name "Orion Labs" --director-email zoe@orion.example '
        '--director-name "Zoe Lin"',
    ),
)
def create_org(
    name: Annotated[str, typer.Option("--name", metavar="NAME", help="The organisation's name")],
    director_email: Annotated[
        str,
        typer.Option("--director-email", metavar="EMAIL", help="The first Director's email"),
    ],
    director_name: Annotated[
        str,
        typer.Option("--director-name", metavar="NAME", help="The first Director's full name"),
    ],
) -> None:
    """Create an organisation and its first Director.

    The Director's password is asked for twice with the input hidden. Without a terminal, pipe
    it on stdin. It must be at least 15 characters; passphrases are welcome.
    """
    org_name = _required(name, "The organisation needs a name.")
    slug = _slug(org_name)
    if not slug:
        raise Failure(
            "The organisation's name needs at least one letter or number.", exit_code=USAGE
        )
    email = _required(director_email, "The Director needs an email address.")
    person = _required(director_name, "The Director needs a name.")

    settings = _settings()
    path = _shown(settings.database_path)
    with _database(settings) as conn:
        _prepare(conn, path)
        _refuse_if_taken(conn, slug, email)  # before asking, so no password is typed for nothing
        password = _new_password(person)
        try:
            validate_password(password)
        except PasswordTooShort:
            raise Failure(
                f"The password must be at least {MIN_PASSWORD_LENGTH} characters. "
                "Nothing was changed.",
                hint="A few words make a good passphrase. Run the command again.",
                exit_code=USAGE,
            ) from None
        password_hash = security.hash_password(password)  # slow, so before the write lock
        with write_tx(conn):
            _refuse_if_taken(conn, slug, email)  # again, now that nothing else can write
            org_id = platform.create_organisation(conn, org_name, slug)
            repos = Repos(conn, org_id)
            repos.users.create(email, person, Role.DIRECTOR, password_hash)
            approvals = repos.organisation.get().required_approvals

    typer.echo(f"Created {org_name} with {person} ({email}) as its first Director.")
    typer.echo(
        f"  Missions need {approvals} approval{'' if approvals == 1 else 's'} to go active. "
        f"{person.split()[0]} can change that with mc org set-approvals."
    )
    _next_steps(
        [
            f"uv run mc login --email {email}",
            "uv run mc skills add NAME",
            "uv run mc users add --email EMAIL --name NAME --role lead",
        ]
    )


# --- Database -----------------------------------------------------------------------------


def _settings() -> Settings:
    try:
        return Settings.from_env(os.environ)
    except ValueError as e:
        raise Failure(f"{e}.", exit_code=USAGE) from None


def _shown(path: Path) -> Path:
    """The database path as the operator should see it: absolute, so there's no doubt which
    file was used."""
    return path.expanduser().resolve()


@contextmanager
def _database(settings: Settings) -> Generator[sqlite3.Connection]:
    """A connection to the configured file, with database failures put into words."""
    path = _shown(settings.database_path)
    try:
        conn = connect(settings.database_path, busy_timeout_ms=settings.busy_timeout_ms)
    except sqlite3.OperationalError:
        raise Failure(
            f"Can't open the database at {path}.",
            hint="Check that its folder exists, or set MC_DATABASE_PATH to another file.",
        ) from None
    try:
        yield conn
    except DatabaseBusy:
        raise Failure(
            f"The database at {path} is busy. Nothing was changed.",
            hint="Try again in a moment.",
        ) from None
    except sqlite3.DatabaseError as e:
        if type(e) is not sqlite3.DatabaseError:  # constraint failures etc. are real bugs
            raise
        raise Failure(
            f"{path} isn't a Mission Control database. Nothing was changed.",
            hint=f"Set MC_DATABASE_PATH to another file, or start over: {_RESET}",
        ) from None
    finally:
        conn.close()


def _prepare(conn: sqlite3.Connection, path: Path) -> bool:
    """Make sure the schema is there. True if it was created just now."""
    try:
        return init_db(conn)
    except UnsupportedSQLite as e:
        raise Failure(f"{e}.", hint="Use a Python built with a newer SQLite.") from None
    except RuntimeError as e:  # a schema version this code doesn't know
        raise Failure(
            f"The database at {path} can't be used: {e}.",
            hint=f"Set MC_DATABASE_PATH to another file, or start over: {_RESET}",
        ) from None


def _delete_database(path: Path) -> bool:
    """Remove the database file and SQLite's side files, so a stale log can't be replayed into
    the new one. True if there was a database to delete."""
    existed = path.exists()
    for victim in (path, *(path.with_name(path.name + s) for s in ("-wal", "-shm", "-journal"))):
        try:
            victim.unlink(missing_ok=True)
        except OSError as e:
            raise Failure(
                f"Can't delete {_shown(victim)}: {e.strerror}.",
                hint="Stop mc-server and check the file's permissions, then try again.",
            ) from None
    return existed


def _refuse_if_taken(conn: sqlite3.Connection, slug: str, email: str) -> None:
    existing = platform.organisation_with_slug(conn, slug)
    if existing is not None:
        raise Failure(
            f"An organisation called {existing} already exists. Nothing was changed.",
            hint="Give the new organisation a different name.",
        )
    # Emails are unique across every organisation, because login is by email alone.
    if security.find_login(conn, email) is not None:
        raise Failure(
            f"The email address {email} is already in use. Nothing was changed.",
            hint="Use another email address for this organisation's Director.",
        )


# --- Input and output ---------------------------------------------------------------------


def _required(value: str, message: str) -> str:
    value = value.strip()
    if not value:
        raise Failure(message, exit_code=USAGE)
    return value


def _slug(name: str) -> str:
    """A name's short form, e.g. "Orion Labs" → "orion-labs". Names that differ only in case,
    spacing or punctuation give the same slug, so they count as the same organisation."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def _is_interactive() -> bool:
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _new_password(person: str) -> str:
    """Asked twice with the input hidden at a terminal; otherwise one line from stdin."""
    if _is_interactive():
        try:
            first = getpass.getpass(f"Password for {person}: ")
            second = getpass.getpass("Repeat the password: ")
        except EOFError:
            raise KeyboardInterrupt from None
        if first != second:
            raise Failure("The passwords don't match. Nothing was changed.", exit_code=USAGE)
        return first
    line = sys.stdin.readline()
    if not line:
        raise Failure(
            "No password given, and there's no terminal to ask on.",
            hint="Run this in a terminal, or pipe the password on stdin.",
            exit_code=USAGE,
        )
    return line.rstrip("\r\n")


def _error(message: str, hint: str | None = None) -> None:
    typer.echo(f"Error: {message}", err=True)
    if hint:
        typer.echo(f"  {hint}", err=True)


def _next_steps(commands: list[str]) -> None:
    for i, step in enumerate(commands):
        typer.echo(f"{'Next:' if i == 0 else '     '} {step}", err=True)


def main() -> None:
    app(prog_name="mc-admin")
