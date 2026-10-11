"""M6: connections, transactions and the schema's own guarantees (design §5, Appendix A)."""

import sqlite3
import threading
import time

import pytest

from mission_control.infra.db import (
    DatabaseBusy,
    UnsupportedSQLite,
    check_sqlite_version,
    connect,
    init_db,
    read_tx,
    write_tx,
)

TABLES = {
    "organisations",
    "users",
    "auth_tokens",
    "crew_profiles",
    "skills",
    "crew_skills",
    "unavailability",
    "missions",
    "slots",
    "slot_requirements",
    "assignments",
    "approvals",
    "audit_events",
}


def scalar(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


# --- Connection settings ------------------------------------------------------------------


def test_every_connection_enables_foreign_keys_and_busy_timeout(db_path):
    first, second = connect(db_path), connect(db_path, busy_timeout_ms=1234)
    try:
        assert scalar(first, "PRAGMA foreign_keys") == 1
        assert scalar(first, "PRAGMA busy_timeout") == 5000
        assert scalar(second, "PRAGMA foreign_keys") == 1
        assert scalar(second, "PRAGMA busy_timeout") == 1234
    finally:
        first.close()
        second.close()


def test_rows_can_be_read_by_column_name(conn):
    row = conn.execute("SELECT 1 AS one").fetchone()
    assert row["one"] == 1


def test_python_never_opens_transactions_implicitly(conn):
    conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    assert not conn.in_transaction


# --- Schema initialisation ----------------------------------------------------------------


def test_init_creates_all_tables_as_strict(conn):
    rows = conn.execute("SELECT name, strict FROM pragma_table_list WHERE schema = 'main'")
    tables = {r["name"]: r["strict"] for r in rows if not r["name"].startswith("sqlite_")}
    assert set(tables) == TABLES
    assert all(tables.values())


def test_init_sets_schema_version_and_wal(conn):
    assert scalar(conn, "PRAGMA user_version") == 1
    assert scalar(conn, "PRAGMA journal_mode") == "wal"


def test_init_is_idempotent(db_path, conn):
    conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    again = connect(db_path)
    try:
        init_db(again)
        assert scalar(again, "SELECT count(*) FROM organisations") == 1
    finally:
        again.close()


def test_init_refuses_an_unknown_newer_schema_version(db_path, conn):
    conn.execute("PRAGMA user_version = 99")
    with pytest.raises(RuntimeError, match="99"):
        init_db(conn)


def test_sqlite_older_than_3_37_is_refused():
    with pytest.raises(UnsupportedSQLite, match="3.37"):
        check_sqlite_version((3, 36, 0))
    check_sqlite_version((3, 37, 0))


# --- Transactions -------------------------------------------------------------------------


def test_write_tx_commits_on_success(conn):
    with write_tx(conn):
        conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    assert scalar(conn, "SELECT count(*) FROM organisations") == 1
    assert not conn.in_transaction


def test_write_tx_rolls_back_everything_on_error(conn):
    with pytest.raises(ValueError):
        with write_tx(conn):
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            raise ValueError("a rule failed after the first write")
    assert scalar(conn, "SELECT count(*) FROM organisations") == 0
    assert not conn.in_transaction


def test_write_tx_rolls_back_on_constraint_failure(conn):
    with pytest.raises(sqlite3.IntegrityError):
        with write_tx(conn):
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'a')")  # dup slug
    assert scalar(conn, "SELECT count(*) FROM organisations") == 0


def test_write_tx_takes_the_write_lock_before_any_statement(db_path, conn):
    # BEGIN IMMEDIATE: while one write transaction is open, a second writer can't even begin.
    other = connect(db_path, busy_timeout_ms=50)
    try:
        with write_tx(conn):
            with pytest.raises(DatabaseBusy):
                with write_tx(other):
                    pass
    finally:
        other.close()


def test_lock_timeout_raises_database_busy_after_the_bounded_wait(db_path, conn):
    other = connect(db_path, busy_timeout_ms=200)
    try:
        with write_tx(conn):
            started = time.monotonic()
            with pytest.raises(DatabaseBusy):
                with write_tx(other):
                    pass
            waited = time.monotonic() - started
        assert 0.15 <= waited < 2
        assert not other.in_transaction
    finally:
        other.close()


def test_a_waiting_writer_proceeds_once_the_lock_is_released(db_path, conn):
    other = connect(db_path, busy_timeout_ms=2000)
    released = threading.Event()

    def hold_lock():
        with write_tx(conn):
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            time.sleep(0.2)
        released.set()

    holder = threading.Thread(target=hold_lock)
    holder.start()
    time.sleep(0.05)
    try:
        with write_tx(other):
            other.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'b')")
        assert released.is_set()
    finally:
        holder.join()
        other.close()
    assert scalar(conn, "SELECT count(*) FROM organisations") == 2


def test_read_tx_sees_a_consistent_snapshot(db_path, conn):
    with write_tx(conn):
        conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    writer = connect(db_path)
    try:
        with read_tx(conn):
            before = scalar(conn, "SELECT count(*) FROM organisations")
            with write_tx(writer):
                writer.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'b')")
            assert scalar(conn, "SELECT count(*) FROM organisations") == before
        assert scalar(conn, "SELECT count(*) FROM organisations") == before + 1
    finally:
        writer.close()


def _without_comments(sql: str) -> list[str]:
    return " ".join(line.split("--", 1)[0] for line in sql.splitlines()).split()


def test_schema_file_matches_design_appendix_a():
    import re
    from pathlib import Path

    from mission_control.infra.db import SCHEMA_SQL

    root = Path(__file__).resolve().parents[2]
    appendix = (root / "docs/technical-design.md").read_text().split("## Appendix A")[1]
    appendix = appendix.split("## Appendix B")[0]
    designed = "\n".join(re.findall(r"```sql\n(.*?)```", appendix, re.S))
    designed = designed.replace("<now>", "strftime('%Y-%m-%dT%H:%M:%fZ','now')")
    assert _without_comments(SCHEMA_SQL) == _without_comments(designed)
