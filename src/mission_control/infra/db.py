"""SQLite connections, schema setup and transactions.

Every connection enforces foreign keys and waits a bounded time for locks. Writes take the
database write lock *before* any checks run, so check-then-write rules can't race.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA_SQL = files("mission_control.infra").joinpath("schema.sql").read_text()
MIN_SQLITE_VERSION = (3, 37, 0)  # STRICT tables


class UnsupportedSQLite(RuntimeError):
    pass


class DatabaseBusy(Exception):
    """Another writer held the lock for longer than the busy timeout."""


def check_sqlite_version(version: tuple[int, int, int] = sqlite3.sqlite_version_info) -> None:
    if version < MIN_SQLITE_VERSION:
        need = ".".join(map(str, MIN_SQLITE_VERSION))
        have = ".".join(map(str, version))
        raise UnsupportedSQLite(f"SQLite {need} or later is required, found {have}")


def connect(path: str | Path, *, busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    """One connection per request. Python never opens transactions implicitly
    (isolation_level=None); the connection may be used from FastAPI's worker threads, but never
    by two requests at once."""
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema on an empty database; do nothing if it's already current."""
    check_sqlite_version()
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == SCHEMA_VERSION:
        return
    if version != 0:
        raise RuntimeError(
            f"database schema version {version} is not supported (expected {SCHEMA_VERSION})"
        )
    conn.executescript(f"BEGIN;\n{SCHEMA_SQL}\nCOMMIT;")
    conn.execute("PRAGMA journal_mode = WAL")


def utc_timestamp(moment: datetime) -> str:
    """A time as stored in the database: UTC with millisecond precision, in the same format the
    schema's defaults write, so stored values compare correctly as text. Naive times are refused,
    because their time zone is unknown."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("a timestamp needs a time zone")
    utc = moment.astimezone(UTC)
    return f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond // 1000:03d}Z"


def _is_locked(error: sqlite3.OperationalError) -> bool:
    return "locked" in str(error) or "busy" in str(error)


@contextmanager
def write_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Run a block in one write transaction: commit on success, roll back on any error.

    BEGIN IMMEDIATE takes the write lock up front, so the checks inside the block see the same
    data the writes will change. If the lock isn't free within the busy timeout, DatabaseBusy.
    """
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        if _is_locked(e):
            raise DatabaseBusy("the database is busy; try again") from e
        raise
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    try:
        conn.execute("COMMIT")
    except sqlite3.OperationalError as e:
        conn.execute("ROLLBACK")
        if _is_locked(e):
            raise DatabaseBusy("the database is busy; try again") from e
        raise


@contextmanager
def read_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Run several reads against one consistent snapshot. Ends with COMMIT on success and
    ROLLBACK on any error, so nothing written by a failing block is kept and the original error
    always reaches the caller."""
    conn.execute("BEGIN")
    try:
        yield conn
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    if conn.in_transaction:
        conn.execute("COMMIT")
