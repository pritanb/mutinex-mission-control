# Subagent (01): Fix db, security, auth findings

Source: `agent-a85edba8acd3b8a36.jsonl` · 2026-10-11 13:17:22 UTC → 2026-10-11 13:19:28 UTC

Rendered from the raw JSONL without editing message content. Tool results and thinking are collapsed; expand them to read.


---

### 👤 User · 2026-10-11 13:17:22 UTC

You are applying approved fixes to a Python project. Repository: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control. Another agent is editing infra/repositories/* and its tests at the same time.

You own ONLY these files:
- src/mission_control/infra/db.py
- src/mission_control/infra/security.py
- src/mission_control/services/auth.py
- tests/integration/test_db.py
- tests/integration/test_auth.py

Do NOT edit anything else (in particular not infra/repositories/*, seed/*, domain/*, or the other tests). Do NOT run git commands that change state. Do NOT add dependencies.

Verify with:
- `uv run pytest tests/integration/test_db.py tests/integration/test_auth.py tests/integration/test_schema_constraints.py -W error`
- `uv run ruff check src tests && uv run ruff format src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py tests/integration/test_db.py tests/integration/test_auth.py`

Do not run the full suite: other files are mid-edit.

Project rules (CLAUDE.md, docs/technical-design.md §4 Authentication, §5 Transactions, §10):
- Every write runs inside write_tx (BEGIN IMMEDIATE before checks); keep transactions short.
- No PRD IDs in src/ (fine in tests).
- User-facing messages are natural sentences and must stay exactly as they are.
- `@contextmanager` functions are annotated `-> Generator[T]`.
- Tests use cheap Argon2 except tests marked `real_argon2` (see tests/conftest.py).
- Never weaken or delete a test.
- Approved behaviour must be preserved: the same codes, messages and results, except where noted.

Test-first: write each regression test, see it fail, then fix.

FIX H2 (High). Don't run Argon2 while holding the write lock.
Today `services/auth.login` runs `verify_password`, `dummy_hash` and the rehash inside `write_tx`, and `change_password` runs a verify plus `hash_password` inside `write_tx`. Each Argon2 call takes ~40 ms, and failed logins block all writers for that long.
- **login:**
  1. Read `find_login` and do the verify (or the dummy verify for unknown email) OUTSIDE any write transaction. A plain read, or `read_tx`, is fine.
  2. If a rehash is needed, compute the new hash before opening the transaction.
  3. Then, inside a short `write_tx`, re-read the user's password_hash and is_active. If the hash has changed since you verified it, or the user is no longer active, refuse with the same `_BAD_LOGIN`.
  4. Store the token, and the new hash if rehashing, inside that transaction.
  5. Unknown, wrong and deactivated must still be refused identically, at equal cost.
- **change_password:**
  1. Validate the new password first (as now).
  2. Read the current hash and verify the current password outside the transaction.
  3. Compute the new hash outside the transaction.
  4. Inside `write_tx`, confirm the stored hash still equals the one you verified, and refuse with the same `wrong_current_password` Forbidden if not.
  5. Then set the new hash, revoke all sessions and audit, as now.
- **Regression tests:** prove no Argon2 work happens while the write lock is held. For example, monkeypatch `security.verify_password` and `security.hash_password` to record `conn.in_transaction` at call time, and assert it was False for login (right password, wrong password, unknown email, rehash path) and for change_password. Also test the race: if the stored hash changes between the verify and the write (simulate by changing it in the monkeypatched verify), login is refused with `invalid_credentials` and change_password with `wrong_current_password`.

FIX M1 (Medium). `read_tx` commits even if its block raises.
- Make `read_tx` roll back on any exception and commit only on success, guarded by `if conn.in_transaction` so a "no transaction is active" error can never hide the original exception.
- Tests:
  - a write made inside a failing `read_tx` is not kept;
  - an exception raised inside `read_tx` reaches the caller unchanged, even if the block itself ended the transaction (e.g. executed ROLLBACK).

FIX M2 (Medium). `revoke_all_sessions` mode switch.
- Today it branches on `conn.in_transaction`. Make it always open its own `write_tx` (a standalone use case).
- In its docstring, say that a service doing a larger change (deactivation, M9) calls `security.revoke_user_tokens` inside its own `write_tx`, next to its audit write.
- Remove the branch. Keep the existing tests passing.

FIX M3 (Medium). Timestamp helper.
- `security.iso()` drops time zones: an aware +10:00 time is written as if it were UTC. It also writes 6 fractional digits while the schema defaults write 3, so mixed values compare wrongly as text.
- Move it to `infra/db.py` as `utc_timestamp(moment: datetime) -> str`:
  - convert with `astimezone(UTC)`;
  - reject naive datetimes with ValueError;
  - format as `YYYY-MM-DDTHH:MM:SS.mmmZ`, with 3-digit milliseconds, matching `strftime('%Y-%m-%dT%H:%M:%fZ','now')` in schema.sql.
- Update security.py to use it, and remove `iso` (grep src/ and tests/ for other uses; there should be none outside your files).
- Tests:
  - +10:00 converts to UTC correctly;
  - a naive datetime is rejected;
  - the format matches what SQLite's default writes (compare with `SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')` shape, e.g. a regex and the same length);
  - token expiry still works with a non-UTC aware `now`: log in at 19:00+10:00 (09:00 UTC), and the token is valid at 20:59 UTC but not at 21:00 UTC.
- Note: stored auth_tokens timestamps go from 6 to 3 fractional digits. That's the one approved data change.

FIX M5 (Medium). A lock test depends on thread timing.
`tests/integration/test_db.py` `test_a_waiting_writer_proceeds_once_the_lock_is_released` sleeps 0.05 s and assumes the holder thread has taken the lock by then. Give `hold_lock` an `acquired` threading.Event, set right after entering `write_tx`, and have the main thread call `acquired.wait(timeout=5)` (assert True) instead of sleeping. Keep what it proves.

FIX L2, your share (Low). In tests/integration/test_auth.py, `test_ac26_deactivated_user_cannot_log_in` checks the code but not the message. Assert the message is exactly "Email or password is incorrect", identical to the wrong-password refusal.

Report: per fix, what changed (file:line), how you confirmed behaviour is preserved, and the final test output for your files plus ruff.

<details>
<summary>⚙️ System/meta message · 2026-10-11 13:17:22 UTC</summary>

```
<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered.
</system-reminder>
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; cat -n src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py; grep -rn "iso(\|\.iso\b\|import iso\|revoke_all_sessions\|read_tx" src tests | grep -v "^src/mission_control/infra/db.py"
```

<details>
<summary>↳ Result</summary>

```
     1	"""SQLite connections, schema setup and transactions.
     2	
     3	Every connection enforces foreign keys and waits a bounded time for locks. Writes take the
     4	database write lock *before* any checks run, so check-then-write rules can't race.
     5	"""
     6	
     7	import sqlite3
     8	from collections.abc import Generator
     9	from contextlib import contextmanager
    10	from importlib.resources import files
    11	from pathlib import Path
    12	
    13	SCHEMA_VERSION = 1
    14	SCHEMA_SQL = files("mission_control.infra").joinpath("schema.sql").read_text()
    15	MIN_SQLITE_VERSION = (3, 37, 0)  # STRICT tables
    16	
    17	
    18	class UnsupportedSQLite(RuntimeError):
    19	    pass
    20	
    21	
    22	class DatabaseBusy(Exception):
    23	    """Another writer held the lock for longer than the busy timeout."""
    24	
    25	
    26	def check_sqlite_version(version: tuple[int, int, int] = sqlite3.sqlite_version_info) -> None:
    27	    if version < MIN_SQLITE_VERSION:
    28	        need = ".".join(map(str, MIN_SQLITE_VERSION))
    29	        have = ".".join(map(str, version))
    30	        raise UnsupportedSQLite(f"SQLite {need} or later is required, found {have}")
    31	
    32	
    33	def connect(path: str | Path, *, busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    34	    """One connection per request. Python never opens transactions implicitly
    35	    (isolation_level=None); the connection may be used from FastAPI's worker threads, but never
    36	    by two requests at once."""
    37	    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    38	    conn.row_factory = sqlite3.Row
    39	    conn.execute("PRAGMA foreign_keys = ON")
    40	    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    41	    return conn
    42	
    43	
    44	def init_db(conn: sqlite3.Connection) -> None:
    45	    """Create the schema on an empty database; do nothing if it's already current."""
    46	    check_sqlite_version()
    47	    version = conn.execute("PRAGMA user_version").fetchone()[0]
    48	    if version == SCHEMA_VERSION:
    49	        return
    50	    if version != 0:
    51	        raise RuntimeError(
    52	            f"database schema version {version} is not supported (expected {SCHEMA_VERSION})"
    53	        )
    54	    conn.executescript(f"BEGIN;\n{SCHEMA_SQL}\nCOMMIT;")
    55	    conn.execute("PRAGMA journal_mode = WAL")
    56	
    57	
    58	def _is_locked(error: sqlite3.OperationalError) -> bool:
    59	    return "locked" in str(error) or "busy" in str(error)
    60	
    61	
    62	@contextmanager
    63	def write_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    64	    """Run a block in one write transaction: commit on success, roll back on any error.
    65	
    66	    BEGIN IMMEDIATE takes the write lock up front, so the checks inside the block see the same
    67	    data the writes will change. If the lock isn't free within the busy timeout, DatabaseBusy.
    68	    """
    69	    try:
    70	        conn.execute("BEGIN IMMEDIATE")
    71	    except sqlite3.OperationalError as e:
    72	        if _is_locked(e):
    73	            raise DatabaseBusy("the database is busy; try again") from e
    74	        raise
    75	    try:
    76	        yield conn
    77	    except BaseException:
    78	        conn.execute("ROLLBACK")
    79	        raise
    80	    try:
    81	        conn.execute("COMMIT")
    82	    except sqlite3.OperationalError as e:
    83	        conn.execute("ROLLBACK")
    84	        if _is_locked(e):
    85	            raise DatabaseBusy("the database is busy; try again") from e
    86	        raise
    87	
    88	
    89	@contextmanager
    90	def read_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    91	    """Run several reads against one consistent snapshot."""
    92	    conn.execute("BEGIN")
    93	    try:
    94	        yield conn
    95	    finally:
    96	        conn.execute("COMMIT")
     1	"""Password hashing, session tokens, and the only lookups not scoped to an organisation.
     2	
     3	Login and token resolution happen before the caller's organisation is known, so these queries
     4	look users up by email or token hash. Everything else goes through tenant-scoped repositories.
     5	"""
     6	
     7	import hashlib
     8	import secrets
     9	import sqlite3
    10	from datetime import datetime
    11	
    12	from argon2 import PasswordHasher
    13	from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
    14	
    15	_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters
    16	
    17	
    18	def hash_password(password: str) -> str:
    19	    return _hasher.hash(password)
    20	
    21	
    22	def verify_password(password_hash: str, password: str) -> bool:
    23	    try:
    24	        return _hasher.verify(password_hash, password)
    25	    except (VerifyMismatchError, VerificationError, InvalidHashError):
    26	        return False
    27	
    28	
    29	_dummy_hashes: dict[int, str] = {}
    30	
    31	
    32	def dummy_hash() -> str:
    33	    """A real Argon2 hash of a random secret, made with the current hasher. Verifying against
    34	    it when an email doesn't exist makes that path cost the same as a real check, so response
    35	    time doesn't reveal which accounts exist."""
    36	    key = id(_hasher)
    37	    if key not in _dummy_hashes:
    38	        _dummy_hashes[key] = _hasher.hash(secrets.token_urlsafe(32))
    39	    return _dummy_hashes[key]
    40	
    41	
    42	def needs_rehash(password_hash: str) -> bool:
    43	    return _hasher.check_needs_rehash(password_hash)
    44	
    45	
    46	def new_token() -> str:
    47	    """32 random bytes, URL-safe. Returned to the client once and never stored."""
    48	    return secrets.token_urlsafe(32)
    49	
    50	
    51	def hash_token(token: str) -> str:
    52	    return hashlib.sha256(token.encode()).hexdigest()
    53	
    54	
    55	def iso(moment: datetime) -> str:
    56	    """UTC timestamp in one fixed format, so stored values compare correctly as text."""
    57	    return moment.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    58	
    59	
    60	def find_login(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    61	    return conn.execute(
    62	        "SELECT id, org_id, password_hash, is_active FROM users WHERE email = ?", (email,)
    63	    ).fetchone()
    64	
    65	
    66	def password_hash_of(conn: sqlite3.Connection, user_id: int) -> str:
    67	    return conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()[0]
    68	
    69	
    70	def set_password_hash(conn: sqlite3.Connection, user_id: int, password_hash: str) -> None:
    71	    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    72	
    73	
    74	def store_token(
    75	    conn: sqlite3.Connection, user_id: int, token_hash: str, created: datetime, expires: datetime
    76	) -> None:
    77	    conn.execute(
    78	        "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
    79	        (user_id, token_hash, iso(created), iso(expires)),
    80	    )
    81	
    82	
    83	def find_session(conn: sqlite3.Connection, token_hash: str, now: datetime) -> sqlite3.Row | None:
    84	    """The user behind a live session: not revoked, not expired, and still active."""
    85	    return conn.execute(
    86	        """SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id
    87	           FROM auth_tokens t
    88	           JOIN users u ON u.id = t.user_id
    89	           LEFT JOIN crew_profiles p ON p.org_id = u.org_id AND p.user_id = u.id
    90	           WHERE t.token_hash = ? AND t.revoked_at IS NULL AND t.expires_at > ?
    91	             AND u.is_active = 1""",
    92	        (token_hash, iso(now)),
    93	    ).fetchone()
    94	
    95	
    96	def revoke_token(conn: sqlite3.Connection, token_hash: str, now: datetime) -> None:
    97	    conn.execute(
    98	        "UPDATE auth_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
    99	        (iso(now), token_hash),
   100	    )
   101	
   102	
   103	def revoke_user_tokens(conn: sqlite3.Connection, user_id: int, now: datetime) -> None:
   104	    conn.execute(
   105	        "UPDATE auth_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
   106	        (iso(now), user_id),
   107	    )
     1	"""Logging in and out, resolving a request's token to an Actor, and changing passwords."""
     2	
     3	import sqlite3
     4	from dataclasses import dataclass
     5	from datetime import UTC, datetime, timedelta
     6	
     7	from mission_control.domain.enums import Role
     8	from mission_control.domain.errors import Forbidden, Unauthenticated
     9	from mission_control.domain.passwords import validate_password
    10	from mission_control.domain.permissions import Actor
    11	from mission_control.infra import security
    12	from mission_control.infra.db import read_tx, write_tx
    13	from mission_control.infra.repositories import Repos
    14	from mission_control.infra.repositories.models import User
    15	
    16	SESSION_LIFETIME = timedelta(hours=12)
    17	
    18	_BAD_LOGIN = Unauthenticated("invalid_credentials", "Email or password is incorrect")
    19	
    20	
    21	@dataclass(frozen=True)
    22	class Session:
    23	    token: str  # shown to the client once; only its hash is stored
    24	    expires_at: datetime
    25	    user: User
    26	
    27	
    28	def _now(now: datetime | None) -> datetime:
    29	    return now or datetime.now(UTC)
    30	
    31	
    32	def login(
    33	    conn: sqlite3.Connection,
    34	    email: str,
    35	    password: str,
    36	    *,
    37	    now: datetime | None = None,
    38	    lifetime: timedelta = SESSION_LIFETIME,
    39	) -> Session:
    40	    """Unknown email, wrong password and deactivated user all get the same refusal, so the
    41	    response never reveals which accounts exist."""
    42	    now = _now(now)
    43	    with write_tx(conn):
    44	        found = security.find_login(conn, email)
    45	        if found is None:
    46	            security.verify_password(security.dummy_hash(), password)  # same cost as a real check
    47	            raise _BAD_LOGIN
    48	        if not security.verify_password(found["password_hash"], password):
    49	            raise _BAD_LOGIN
    50	        if not found["is_active"]:
    51	            raise _BAD_LOGIN
    52	        if security.needs_rehash(found["password_hash"]):
    53	            security.set_password_hash(conn, found["id"], security.hash_password(password))
    54	        token = security.new_token()
    55	        expires = now + lifetime
    56	        security.store_token(conn, found["id"], security.hash_token(token), now, expires)
    57	        user = Repos(conn, found["org_id"]).users.get(found["id"])
    58	    assert user is not None
    59	    return Session(token=token, expires_at=expires, user=user)
    60	
    61	
    62	def authenticate(
    63	    conn: sqlite3.Connection, token: str | None, *, now: datetime | None = None
    64	) -> Actor:
    65	    """Resolve a bearer token to the current Actor. Nothing is cached: role and active status
    66	    are read on every call, so changes apply to the very next request."""
    67	    if not token:
    68	        raise _session_error()
    69	    with read_tx(conn):
    70	        row = security.find_session(conn, security.hash_token(token), _now(now))
    71	    if row is None:
    72	        raise _session_error()
    73	    return Actor(
    74	        user_id=row["id"],
    75	        org_id=row["org_id"],
    76	        role=Role(row["role"]),
    77	        crew_profile_id=row["crew_profile_id"],
    78	    )
    79	
    80	
    81	def logout(conn: sqlite3.Connection, token: str, *, now: datetime | None = None) -> None:
    82	    with write_tx(conn):
    83	        security.revoke_token(conn, security.hash_token(token), _now(now))
    84	
    85	
    86	def revoke_all_sessions(
    87	    conn: sqlite3.Connection, user_id: int, *, now: datetime | None = None
    88	) -> None:
    89	    """End every session of a user. Call inside the caller's transaction when part of a larger
    90	    change (deactivation); this opens its own when used alone."""
    91	    if conn.in_transaction:
    92	        security.revoke_user_tokens(conn, user_id, _now(now))
    93	        return
    94	    with write_tx(conn):
    95	        security.revoke_user_tokens(conn, user_id, _now(now))
    96	
    97	
    98	def change_password(
    99	    conn: sqlite3.Connection,
   100	    actor: Actor,
   101	    current_password: str,
   102	    new_password: str,
   103	    *,
   104	    now: datetime | None = None,
   105	) -> None:
   106	    """Needs the current password. Every session ends, including the one used to change it."""
   107	    validate_password(new_password)
   108	    now = _now(now)
   109	    with write_tx(conn):
   110	        if not security.verify_password(
   111	            security.password_hash_of(conn, actor.user_id), current_password
   112	        ):
   113	            raise Forbidden("wrong_current_password", "Your current password is incorrect")
   114	        security.set_password_hash(conn, actor.user_id, security.hash_password(new_password))
   115	        security.revoke_user_tokens(conn, actor.user_id, now)
   116	        Repos(conn, actor.org_id).audit.record(actor.user_id, "user.password_changed")
   117	
   118	
   119	def _session_error() -> Unauthenticated:
   120	    return Unauthenticated(
   121	        "unauthenticated", "Your session has expired or isn't valid; log in again"
   122	    )
src/mission_control/infra/security.py:55:def iso(moment: datetime) -> str:
src/mission_control/infra/security.py:79:        (user_id, token_hash, iso(created), iso(expires)),
src/mission_control/infra/security.py:92:        (token_hash, iso(now)),
src/mission_control/infra/security.py:99:        (iso(now), token_hash),
src/mission_control/infra/security.py:106:        (iso(now), user_id),
src/mission_control/services/auth.py:12:from mission_control.infra.db import read_tx, write_tx
src/mission_control/services/auth.py:69:    with read_tx(conn):
src/mission_control/services/auth.py:86:def revoke_all_sessions(
tests/integration/test_auth.py:170:    auth.revoke_all_sessions(db, LEE, now=NOW)
tests/integration/test_db.py:15:    read_tx,
tests/integration/test_db.py:179:def test_read_tx_sees_a_consistent_snapshot(db_path, conn):
tests/integration/test_db.py:184:        with read_tx(conn):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; cat -n tests/integration/test_db.py tests/integration/test_auth.py; cat tests/conftest.py; ls tests tests/integration
```

<details>
<summary>↳ Result</summary>

````
     1	"""M6: connections, transactions and the schema's own guarantees (design §5, Appendix A)."""
     2	
     3	import sqlite3
     4	import threading
     5	import time
     6	
     7	import pytest
     8	
     9	from mission_control.infra.db import (
    10	    DatabaseBusy,
    11	    UnsupportedSQLite,
    12	    check_sqlite_version,
    13	    connect,
    14	    init_db,
    15	    read_tx,
    16	    write_tx,
    17	)
    18	
    19	TABLES = {
    20	    "organisations",
    21	    "users",
    22	    "auth_tokens",
    23	    "crew_profiles",
    24	    "skills",
    25	    "crew_skills",
    26	    "unavailability",
    27	    "missions",
    28	    "slots",
    29	    "slot_requirements",
    30	    "assignments",
    31	    "approvals",
    32	    "audit_events",
    33	}
    34	
    35	
    36	def scalar(conn, sql, *args):
    37	    return conn.execute(sql, args).fetchone()[0]
    38	
    39	
    40	# --- Connection settings ------------------------------------------------------------------
    41	
    42	
    43	def test_every_connection_enables_foreign_keys_and_busy_timeout(db_path):
    44	    first, second = connect(db_path), connect(db_path, busy_timeout_ms=1234)
    45	    try:
    46	        assert scalar(first, "PRAGMA foreign_keys") == 1
    47	        assert scalar(first, "PRAGMA busy_timeout") == 5000
    48	        assert scalar(second, "PRAGMA foreign_keys") == 1
    49	        assert scalar(second, "PRAGMA busy_timeout") == 1234
    50	    finally:
    51	        first.close()
    52	        second.close()
    53	
    54	
    55	def test_rows_can_be_read_by_column_name(conn):
    56	    row = conn.execute("SELECT 1 AS one").fetchone()
    57	    assert row["one"] == 1
    58	
    59	
    60	def test_python_never_opens_transactions_implicitly(conn):
    61	    conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    62	    assert not conn.in_transaction
    63	
    64	
    65	# --- Schema initialisation ----------------------------------------------------------------
    66	
    67	
    68	def test_init_creates_all_tables_as_strict(conn):
    69	    rows = conn.execute("SELECT name, strict FROM pragma_table_list WHERE schema = 'main'")
    70	    tables = {r["name"]: r["strict"] for r in rows if not r["name"].startswith("sqlite_")}
    71	    assert set(tables) == TABLES
    72	    assert all(tables.values())
    73	
    74	
    75	def test_init_sets_schema_version_and_wal(conn):
    76	    assert scalar(conn, "PRAGMA user_version") == 1
    77	    assert scalar(conn, "PRAGMA journal_mode") == "wal"
    78	
    79	
    80	def test_init_is_idempotent(db_path, conn):
    81	    conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    82	    again = connect(db_path)
    83	    try:
    84	        init_db(again)
    85	        assert scalar(again, "SELECT count(*) FROM organisations") == 1
    86	    finally:
    87	        again.close()
    88	
    89	
    90	def test_init_refuses_an_unknown_newer_schema_version(db_path, conn):
    91	    conn.execute("PRAGMA user_version = 99")
    92	    with pytest.raises(RuntimeError, match="99"):
    93	        init_db(conn)
    94	
    95	
    96	def test_sqlite_older_than_3_37_is_refused():
    97	    with pytest.raises(UnsupportedSQLite, match="3.37"):
    98	        check_sqlite_version((3, 36, 0))
    99	    check_sqlite_version((3, 37, 0))
   100	
   101	
   102	# --- Transactions -------------------------------------------------------------------------
   103	
   104	
   105	def test_write_tx_commits_on_success(conn):
   106	    with write_tx(conn):
   107	        conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
   108	    assert scalar(conn, "SELECT count(*) FROM organisations") == 1
   109	    assert not conn.in_transaction
   110	
   111	
   112	def test_write_tx_rolls_back_everything_on_error(conn):
   113	    with pytest.raises(ValueError):
   114	        with write_tx(conn):
   115	            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
   116	            raise ValueError("a rule failed after the first write")
   117	    assert scalar(conn, "SELECT count(*) FROM organisations") == 0
   118	    assert not conn.in_transaction
   119	
   120	
   121	def test_write_tx_rolls_back_on_constraint_failure(conn):
   122	    with pytest.raises(sqlite3.IntegrityError):
   123	        with write_tx(conn):
   124	            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
   125	            conn.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'a')")  # dup slug
   126	    assert scalar(conn, "SELECT count(*) FROM organisations") == 0
   127	
   128	
   129	def test_write_tx_takes_the_write_lock_before_any_statement(db_path, conn):
   130	    # BEGIN IMMEDIATE: while one write transaction is open, a second writer can't even begin.
   131	    other = connect(db_path, busy_timeout_ms=50)
   132	    try:
   133	        with write_tx(conn):
   134	            with pytest.raises(DatabaseBusy):
   135	                with write_tx(other):
   136	                    pass
   137	    finally:
   138	        other.close()
   139	
   140	
   141	def test_lock_timeout_raises_database_busy_after_the_bounded_wait(db_path, conn):
   142	    other = connect(db_path, busy_timeout_ms=200)
   143	    try:
   144	        with write_tx(conn):
   145	            started = time.monotonic()
   146	            with pytest.raises(DatabaseBusy):
   147	                with write_tx(other):
   148	                    pass
   149	            waited = time.monotonic() - started
   150	        assert 0.15 <= waited < 2
   151	        assert not other.in_transaction
   152	    finally:
   153	        other.close()
   154	
   155	
   156	def test_a_waiting_writer_proceeds_once_the_lock_is_released(db_path, conn):
   157	    other = connect(db_path, busy_timeout_ms=2000)
   158	    released = threading.Event()
   159	
   160	    def hold_lock():
   161	        with write_tx(conn):
   162	            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
   163	            time.sleep(0.2)
   164	        released.set()
   165	
   166	    holder = threading.Thread(target=hold_lock)
   167	    holder.start()
   168	    time.sleep(0.05)
   169	    try:
   170	        with write_tx(other):
   171	            other.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'b')")
   172	        assert released.is_set()
   173	    finally:
   174	        holder.join()
   175	        other.close()
   176	    assert scalar(conn, "SELECT count(*) FROM organisations") == 2
   177	
   178	
   179	def test_read_tx_sees_a_consistent_snapshot(db_path, conn):
   180	    with write_tx(conn):
   181	        conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
   182	    writer = connect(db_path)
   183	    try:
   184	        with read_tx(conn):
   185	            before = scalar(conn, "SELECT count(*) FROM organisations")
   186	            with write_tx(writer):
   187	                writer.execute("INSERT INTO organisations(name, slug) VALUES ('B', 'b')")
   188	            assert scalar(conn, "SELECT count(*) FROM organisations") == before
   189	        assert scalar(conn, "SELECT count(*) FROM organisations") == before + 1
   190	    finally:
   191	        writer.close()
   192	
   193	
   194	def _without_comments(sql: str) -> list[str]:
   195	    return " ".join(line.split("--", 1)[0] for line in sql.splitlines()).split()
   196	
   197	
   198	def test_schema_file_matches_design_appendix_a():
   199	    import re
   200	    from pathlib import Path
   201	
   202	    from mission_control.infra.db import SCHEMA_SQL
   203	
   204	    root = Path(__file__).resolve().parents[2]
   205	    appendix = (root / "docs/technical-design.md").read_text().split("## Appendix A")[1]
   206	    appendix = appendix.split("## Appendix B")[0]
   207	    designed = "\n".join(re.findall(r"```sql\n(.*?)```", appendix, re.S))
   208	    designed = designed.replace("<now>", "strftime('%Y-%m-%dT%H:%M:%fZ','now')")
   209	    assert _without_comments(SCHEMA_SQL) == _without_comments(designed)
     1	"""M8: passwords, sessions and request authentication (design §4 Authentication, PRD P7, P10)."""
     2	
     3	import hashlib
     4	from datetime import UTC, datetime, timedelta
     5	
     6	import pytest
     7	
     8	from mission_control.domain.enums import Role
     9	from mission_control.domain.errors import Forbidden, Unauthenticated
    10	from mission_control.domain.passwords import PasswordTooShort
    11	from mission_control.infra import security
    12	from mission_control.seed.data import DEMO_PASSWORD
    13	from mission_control.seed.loader import load_seed
    14	from mission_control.services import auth
    15	
    16	NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)
    17	LEE, BEN, ANA, RUTH = 4, 7, 6, 1
    18	
    19	
    20	@pytest.fixture
    21	def db(conn):
    22	    """The PRD seed with a real Argon2 hash of the demo passphrase."""
    23	    load_seed(conn, password_hash=security.hash_password(DEMO_PASSWORD))
    24	    return conn
    25	
    26	
    27	def login(db, email="lee@aurora.example", password=DEMO_PASSWORD, now=NOW):
    28	    return auth.login(db, email, password, now=now)
    29	
    30	
    31	# --- Password hashing ---------------------------------------------------------------------
    32	
    33	
    34	def test_passwords_are_hashed_with_argon2id_and_verify():
    35	    hashed = security.hash_password("correct horse battery staple")
    36	    assert hashed.startswith("$argon2id$")
    37	    assert security.verify_password(hashed, "correct horse battery staple")
    38	    assert not security.verify_password(hashed, "correct horse battery stapler")
    39	
    40	
    41	def test_the_same_password_hashes_differently_each_time():
    42	    assert security.hash_password("a" * 15) != security.hash_password("a" * 15)
    43	
    44	
    45	def test_verify_handles_a_malformed_hash_as_a_mismatch():
    46	    assert not security.verify_password("not-a-hash", "anything at all here")
    47	
    48	
    49	# --- Login --------------------------------------------------------------------------------
    50	
    51	
    52	def test_login_returns_a_token_valid_for_12_hours(db):
    53	    session = login(db)
    54	    assert session.user.id == LEE and session.user.role == Role.LEAD
    55	    assert session.expires_at == NOW + timedelta(hours=12)
    56	    assert len(session.token) >= 40
    57	
    58	
    59	def test_login_email_is_case_insensitive(db):
    60	    assert login(db, email="LEE@Aurora.Example").user.id == LEE
    61	
    62	
    63	@pytest.mark.parametrize(
    64	    "email, password",
    65	    [
    66	        ("lee@aurora.example", "wrong passphrase entirely"),
    67	        ("nobody@aurora.example", DEMO_PASSWORD),
    68	    ],
    69	)
    70	def test_wrong_password_and_unknown_email_get_the_same_refusal(db, email, password):
    71	    with pytest.raises(Unauthenticated) as err:
    72	        login(db, email=email, password=password)
    73	    assert err.value.code == "invalid_credentials"
    74	    assert err.value.message == "Email or password is incorrect"
    75	
    76	
    77	def test_ac26_deactivated_user_cannot_log_in(db):
    78	    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
    79	    with pytest.raises(Unauthenticated) as err:
    80	        login(db)
    81	    assert err.value.code == "invalid_credentials"
    82	
    83	
    84	def test_only_the_token_hash_is_stored(db):
    85	    session = login(db)
    86	    stored = [r[0] for r in db.execute("SELECT token_hash FROM auth_tokens")]
    87	    assert stored == [hashlib.sha256(session.token.encode()).hexdigest()]
    88	    assert session.token not in stored
    89	
    90	
    91	def test_each_login_creates_a_separate_session(db):
    92	    a, b = login(db), login(db)
    93	    assert a.token != b.token
    94	    assert auth.authenticate(db, a.token, now=NOW).user_id == LEE
    95	    assert auth.authenticate(db, b.token, now=NOW).user_id == LEE
    96	
    97	
    98	def test_login_upgrades_an_outdated_hash(db, monkeypatch):
    99	    old = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
   100	    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
   101	    login(db)
   102	    new = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
   103	    assert new != old and security.verify_password(new, DEMO_PASSWORD)
   104	
   105	
   106	# --- Authenticating a request -------------------------------------------------------------
   107	
   108	
   109	def test_a_valid_token_resolves_to_the_actor(db):
   110	    session = login(db, email="ana@aurora.example")
   111	    actor = auth.authenticate(db, session.token, now=NOW + timedelta(hours=1))
   112	    assert (actor.user_id, actor.org_id, actor.role, actor.crew_profile_id) == (
   113	        ANA,
   114	        1,
   115	        Role.LEAD,
   116	        ANA,
   117	    )
   118	
   119	
   120	def test_actor_without_a_crew_profile_has_none(db):
   121	    actor = auth.authenticate(db, login(db).token, now=NOW)
   122	    assert actor.crew_profile_id is None
   123	
   124	
   125	@pytest.mark.parametrize("token", ["", "made-up-token", None])
   126	def test_missing_or_unknown_token_is_unauthenticated(db, token):
   127	    with pytest.raises(Unauthenticated) as err:
   128	        auth.authenticate(db, token, now=NOW)
   129	    assert err.value.code == "unauthenticated"
   130	
   131	
   132	def test_token_expires_after_12_hours(db):
   133	    token = login(db).token
   134	    auth.authenticate(db, token, now=NOW + timedelta(hours=11, minutes=59))
   135	    with pytest.raises(Unauthenticated):
   136	        auth.authenticate(db, token, now=NOW + timedelta(hours=12))
   137	
   138	
   139	def test_role_is_read_fresh_on_every_request(db):
   140	    token = login(db).token
   141	    assert auth.authenticate(db, token, now=NOW).role == Role.LEAD
   142	    db.execute("UPDATE users SET role = 'director' WHERE id = ?", (LEE,))
   143	    assert auth.authenticate(db, token, now=NOW).role == Role.DIRECTOR
   144	
   145	
   146	def test_a_deactivated_user_is_refused_even_with_a_live_token(db):
   147	    token = login(db).token
   148	    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
   149	    with pytest.raises(Unauthenticated):
   150	        auth.authenticate(db, token, now=NOW)
   151	
   152	
   153	# --- Revocation ---------------------------------------------------------------------------
   154	
   155	
   156	def test_logout_revokes_only_that_session(db):
   157	    first, second = login(db), login(db)
   158	    auth.logout(db, first.token, now=NOW)
   159	    with pytest.raises(Unauthenticated):
   160	        auth.authenticate(db, first.token, now=NOW)
   161	    assert auth.authenticate(db, second.token, now=NOW).user_id == LEE
   162	
   163	
   164	def test_logout_with_an_unknown_token_is_harmless(db):
   165	    auth.logout(db, "not-a-real-token", now=NOW)
   166	
   167	
   168	def test_revoking_all_sessions_ends_every_session_of_that_user_only(db):
   169	    lee_a, lee_b, ben = login(db), login(db), login(db, email="ben@aurora.example")
   170	    auth.revoke_all_sessions(db, LEE, now=NOW)
   171	    for token in (lee_a.token, lee_b.token):
   172	        with pytest.raises(Unauthenticated):
   173	            auth.authenticate(db, token, now=NOW)
   174	    assert auth.authenticate(db, ben.token, now=NOW).user_id == BEN
   175	
   176	
   177	# --- Changing a password (P10) ------------------------------------------------------------
   178	
   179	
   180	def test_p10_password_change_revokes_every_session_including_the_current_one(db):
   181	    current, other = login(db), login(db)
   182	    actor = auth.authenticate(db, current.token, now=NOW)
   183	    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
   184	    for token in (current.token, other.token):
   185	        with pytest.raises(Unauthenticated):
   186	            auth.authenticate(db, token, now=NOW)
   187	    assert login(db, password="a brand new passphrase").user.id == LEE
   188	    with pytest.raises(Unauthenticated):
   189	        login(db)
   190	
   191	
   192	def test_p10_wrong_current_password_is_refused_and_nothing_changes(db):
   193	    session = login(db)
   194	    actor = auth.authenticate(db, session.token, now=NOW)
   195	    with pytest.raises(Forbidden) as err:
   196	        auth.change_password(
   197	            db, actor, "not my passphrase at all", "a brand new passphrase", now=NOW
   198	        )
   199	    assert err.value.code == "wrong_current_password"
   200	    assert auth.authenticate(db, session.token, now=NOW).user_id == LEE
   201	    assert login(db).user.id == LEE
   202	
   203	
   204	def test_p10_new_password_must_be_at_least_15_characters(db):
   205	    actor = auth.authenticate(db, login(db).token, now=NOW)
   206	    with pytest.raises(PasswordTooShort):
   207	        auth.change_password(db, actor, DEMO_PASSWORD, "too short", now=NOW)
   208	    assert login(db).user.id == LEE
   209	
   210	
   211	def test_password_change_is_audited_without_the_password(db):
   212	    actor = auth.authenticate(db, login(db).token, now=NOW)
   213	    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
   214	    event, data = db.execute(
   215	        "SELECT event, data FROM audit_events WHERE actor_id = ? ORDER BY id DESC LIMIT 1", (LEE,)
   216	    ).fetchone()
   217	    assert event == "user.password_changed"
   218	    assert "passphrase" not in data and DEMO_PASSWORD not in data
   219	
   220	
   221	# Regression: an unknown email costs the same Argon2 work as a real one (no timing leak)
   222	
   223	
   224	def test_unknown_email_still_runs_a_password_verification(db, monkeypatch):
   225	    calls = []
   226	    real_verify = security.verify_password
   227	
   228	    def counting_verify(password_hash, password):
   229	        calls.append(password_hash)
   230	        return real_verify(password_hash, password)
   231	
   232	    monkeypatch.setattr(security, "verify_password", counting_verify)
   233	    with pytest.raises(Unauthenticated):
   234	        login(db, email="nobody@aurora.example")
   235	    assert len(calls) == 1
   236	    assert calls[0].startswith("$argon2id$")  # a real Argon2 hash, so the work is the same
   237	
   238	
   239	def test_the_dummy_hash_never_matches_a_password(db):
   240	    assert not security.verify_password(security.dummy_hash(), DEMO_PASSWORD)
   241	    assert not security.verify_password(security.dummy_hash(), "")
   242	
   243	
   244	# Regression: production Argon2 settings stay in place; tests use cheap ones for speed
   245	
   246	
   247	@pytest.mark.real_argon2
   248	def test_production_hashes_use_the_libraries_recommended_argon2id_settings():
   249	    hashed = security.hash_password("correct horse battery staple")
   250	    assert hashed.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
   251	    assert security.verify_password(hashed, "correct horse battery staple")
   252	
   253	
   254	def test_tests_run_with_cheap_but_still_argon2id_hashes():
   255	    hashed = security.hash_password("correct horse battery staple")
   256	    assert hashed.startswith("$argon2id$")
   257	    assert "m=65536,t=3,p=4" not in hashed
"""Shared test setup.

- Puts this directory on sys.path so tests can `import builders`.
- Swaps in cheap Argon2 settings for speed. Tests marked `real_argon2` keep the production
  settings, so those stay covered.
"""

import sys
from pathlib import Path

import pytest
from argon2 import PasswordHasher

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

_CHEAP_HASHER = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


def pytest_configure(config):
    config.addinivalue_line("markers", "real_argon2: use production Argon2 settings")


@pytest.fixture(autouse=True)
def _cheap_argon2(request, monkeypatch):
    if request.node.get_closest_marker("real_argon2") is None:
        from mission_control.infra import security

        monkeypatch.setattr(security, "_hasher", _CHEAP_HASHER)
tests:
__pycache__
api
builders.py
conftest.py
integration
unit

tests/integration:
__pycache__
conftest.py
test_auth.py
test_db.py
test_repositories.py
test_repository_sql.py
test_schema_constraints.py
test_seed.py
````

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; cat tests/integration/conftest.py; grep -n "Argon2\|read_tx\|write_tx" -i docs/technical-design.md | head -30
```

<details>
<summary>↳ Result</summary>

```
import pytest

from mission_control.infra.db import connect, init_db


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "mission_control.db"


@pytest.fixture
def conn(db_path):
    """A fresh, initialised database file per test."""
    c = connect(db_path)
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def seeded_db(conn):
    """A fresh database loaded with the PRD §9 seed."""
    from mission_control.seed.loader import load_seed

    load_seed(conn, password_hash="test-hash")
    return conn
45:**Stack:** Python 3.12 · FastAPI + Pydantic v2 · SQLite through stdlib `sqlite3` · argon2-cffi · Typer + httpx2 · uv, pytest, ruff
139:| Passwords | Argon2id. At least 15 characters. No character-type rules. |
592:  password_hash TEXT    NOT NULL,                               -- Argon2id encoded hash
```

</details>

### 🤖 Claude · 2026-10-11 13:17:35 UTC

Now writing the tests first. test_db.py additions:

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; python3 - <<'EOF'
p='tests/integration/test_db.py'
s=open(p).read()
s=s.replace('''import sqlite3
import threading
import time
''','''import re
import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta, timezone
''')
s=s.replace('''    read_tx,
    write_tx,
)''','''    read_tx,
    utc_timestamp,
    write_tx,
)''')
s=s.replace('''    released = threading.Event()

    def hold_lock():
        with write_tx(conn):
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            time.sleep(0.2)
        released.set()

    holder = threading.Thread(target=hold_lock)
    holder.start()
    time.sleep(0.05)
    try:
''','''    acquired = threading.Event()
    released = threading.Event()

    def hold_lock():
        with write_tx(conn):
            acquired.set()
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            time.sleep(0.2)
        released.set()

    holder = threading.Thread(target=hold_lock)
    holder.start()
    try:
        assert acquired.wait(timeout=5)
''')
s=s.replace('''def _without_comments''','''def test_a_write_inside_a_failing_read_tx_is_not_kept(conn):
    with pytest.raises(ValueError):
        with read_tx(conn):
            conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
            raise ValueError("the block failed")
    assert not conn.in_transaction
    assert scalar(conn, "SELECT count(*) FROM organisations") == 0


def test_read_tx_lets_the_original_error_through_even_if_the_block_ended_the_transaction(conn):
    original = ValueError("the block failed after rolling back")
    with pytest.raises(ValueError) as err:
        with read_tx(conn):
            conn.execute("ROLLBACK")
            raise original
    assert err.value is original
    assert not conn.in_transaction


def test_read_tx_commits_on_success(conn):
    with read_tx(conn):
        conn.execute("INSERT INTO organisations(name, slug) VALUES ('A', 'a')")
    assert not conn.in_transaction
    assert scalar(conn, "SELECT count(*) FROM organisations") == 1


# --- Timestamps ---------------------------------------------------------------------------


def test_utc_timestamp_converts_other_time_zones_to_utc():
    sydney = timezone(timedelta(hours=10))
    moment = datetime(2027, 1, 5, 19, 0, 0, 123456, tzinfo=sydney)
    assert utc_timestamp(moment) == "2027-01-05T09:00:00.123Z"
    assert utc_timestamp(datetime(2027, 1, 5, 9, 0, tzinfo=UTC)) == "2027-01-05T09:00:00.000Z"


def test_utc_timestamp_refuses_a_naive_datetime():
    with pytest.raises(ValueError):
        utc_timestamp(datetime(2027, 1, 5, 9, 0))


def test_utc_timestamp_has_the_same_shape_as_the_schema_defaults(conn):
    shape = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z$")
    from_sqlite = scalar(conn, "SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')")
    ours = utc_timestamp(datetime.now(UTC))
    assert shape.match(from_sqlite)
    assert shape.match(ours)
    assert len(ours) == len(from_sqlite)


def _without_comments''')
open(p,'w').write(s)

p='tests/integration/test_auth.py'
s=open(p).read()
s=s.replace('''from datetime import UTC, datetime, timedelta
''','''from datetime import UTC, datetime, timedelta, timezone
''')
s=s.replace('''        login(db)
    assert err.value.code == "invalid_credentials"


def test_only''','''        login(db)
    assert err.value.code == "invalid_credentials"
    assert err.value.message == "Email or password is incorrect"


def test_only''')
s=s.replace('''def test_role_is_read_fresh''','''def test_token_expiry_works_with_a_non_utc_login_time(db):
    sydney = timezone(timedelta(hours=10))
    token = login(db, now=datetime(2027, 1, 5, 19, 0, tzinfo=sydney)).token  # 09:00 UTC
    auth.authenticate(db, token, now=datetime(2027, 1, 5, 20, 59, tzinfo=UTC))
    with pytest.raises(Unauthenticated):
        auth.authenticate(db, token, now=datetime(2027, 1, 5, 21, 0, tzinfo=UTC))


def test_role_is_read_fresh''')
s += '''

# Regression: no Argon2 work runs while the write lock is held


def _record_transaction_state(db, monkeypatch):
    """Wrap the Argon2 calls to record whether a transaction was open at call time."""
    seen = []
    real_verify, real_hash = security.verify_password, security.hash_password

    def verify(password_hash, password):
        seen.append(("verify", db.in_transaction))
        return real_verify(password_hash, password)

    def hash_password(password):
        seen.append(("hash", db.in_transaction))
        return real_hash(password)

    monkeypatch.setattr(security, "verify_password", verify)
    monkeypatch.setattr(security, "hash_password", hash_password)
    return seen


@pytest.mark.parametrize(
    "email, password, refused",
    [
        ("lee@aurora.example", DEMO_PASSWORD, False),
        ("lee@aurora.example", "wrong passphrase entirely", True),
        ("nobody@aurora.example", DEMO_PASSWORD, True),
    ],
)
def test_login_runs_argon2_outside_the_write_transaction(db, monkeypatch, email, password, refused):
    seen = _record_transaction_state(db, monkeypatch)
    if refused:
        with pytest.raises(Unauthenticated):
            login(db, email=email, password=password)
    else:
        login(db, email=email, password=password)
    assert seen == [("verify", False)]


def test_login_rehash_runs_argon2_outside_the_write_transaction(db, monkeypatch):
    old = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
    seen = _record_transaction_state(db, monkeypatch)
    login(db)
    assert seen == [("verify", False), ("hash", False)]
    new = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    assert new != old


def test_change_password_runs_argon2_outside_the_write_transaction(db, monkeypatch):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    seen = _record_transaction_state(db, monkeypatch)
    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    assert seen == [("verify", False), ("hash", False)]


def _change_hash_during_verify(db, monkeypatch):
    """Simulate another request changing the stored hash between the verify and the write."""
    real_verify = security.verify_password

    def verify(password_hash, password):
        result = real_verify(password_hash, password)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (security.hash_password("someone else's new passphrase"), LEE),
        )
        return result

    monkeypatch.setattr(security, "verify_password", verify)


def test_login_is_refused_if_the_password_changed_after_it_was_verified(db, monkeypatch):
    _change_hash_during_verify(db, monkeypatch)
    with pytest.raises(Unauthenticated) as err:
        login(db)
    assert err.value.code == "invalid_credentials"
    assert err.value.message == "Email or password is incorrect"
    assert db.execute("SELECT count(*) FROM auth_tokens").fetchone()[0] == 0


def test_login_is_refused_if_the_user_was_deactivated_after_the_verify(db, monkeypatch):
    real_verify = security.verify_password

    def verify(password_hash, password):
        db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
        return real_verify(password_hash, password)

    monkeypatch.setattr(security, "verify_password", verify)
    with pytest.raises(Unauthenticated) as err:
        login(db)
    assert err.value.code == "invalid_credentials"
    assert db.execute("SELECT count(*) FROM auth_tokens").fetchone()[0] == 0


def test_change_password_is_refused_if_the_password_changed_after_it_was_verified(
    db, monkeypatch
):
    session = login(db)
    actor = auth.authenticate(db, session.token, now=NOW)
    _change_hash_during_verify(db, monkeypatch)
    with pytest.raises(Forbidden) as err:
        auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    assert err.value.code == "wrong_current_password"
    assert err.value.message == "Your current password is incorrect"
    assert auth.authenticate(db, session.token, now=NOW).user_id == LEE
    stored = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    assert security.verify_password(stored, "someone else's new passphrase")
    assert db.execute(
        "SELECT count(*) FROM audit_events WHERE event = 'user.password_changed'"
    ).fetchone()[0] == 0
'''
open(p,'w').write(s)
EOF
uv run pytest tests/integration/test_db.py tests/integration/test_auth.py -W error -q 2>&1 | tail -25
```

<details>
<summary>↳ Result</summary>

```
==================================== ERRORS ====================================
________________ ERROR collecting tests/integration/test_db.py _________________
ImportError while importing test module '/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/integration/test_db.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../.local/share/uv/python/cpython-3.12.15-macos-aarch64-none/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_db.py:11: in <module>
    from mission_control.infra.db import (
E   ImportError: cannot import name 'utc_timestamp' from 'mission_control.infra.db' (/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/src/mission_control/infra/db.py)
=========================== short test summary info ============================
ERROR tests/integration/test_db.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; uv run pytest tests/integration/test_auth.py -W error -q 2>&1 | grep -E "FAILED|passed|failed"
```

<details>
<summary>↳ Result</summary>

```
FAILED tests/integration/test_auth.py::test_token_expiry_works_with_a_non_utc_login_time
FAILED tests/integration/test_auth.py::test_login_runs_argon2_outside_the_write_transaction[lee@aurora.example-orbital launch window-False]
FAILED tests/integration/test_auth.py::test_login_runs_argon2_outside_the_write_transaction[lee@aurora.example-wrong passphrase entirely-True]
FAILED tests/integration/test_auth.py::test_login_runs_argon2_outside_the_write_transaction[nobody@aurora.example-orbital launch window-True]
FAILED tests/integration/test_auth.py::test_login_rehash_runs_argon2_outside_the_write_transaction
FAILED tests/integration/test_auth.py::test_change_password_runs_argon2_outside_the_write_transaction
FAILED tests/integration/test_auth.py::test_login_is_refused_if_the_password_changed_after_it_was_verified
FAILED tests/integration/test_auth.py::test_login_is_refused_if_the_user_was_deactivated_after_the_verify
FAILED tests/integration/test_auth.py::test_change_password_is_refused_if_the_password_changed_after_it_was_verified
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; python3 - <<'EOF'
p='src/mission_control/infra/db.py'
s=open(p).read()
s=s.replace('''from contextlib import contextmanager
''','''from contextlib import contextmanager
from datetime import UTC, datetime
''')
s=s.replace('''def _is_locked''','''def utc_timestamp(moment: datetime) -> str:
    """A time as stored in the database: UTC with millisecond precision, in the same format the
    schema's defaults write, so stored values compare correctly as text. Naive times are refused,
    because their time zone is unknown."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("a timestamp needs a time zone")
    utc = moment.astimezone(UTC)
    return f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond // 1000:03d}Z"


def _is_locked''')
s=s.replace('''    """Run several reads against one consistent snapshot."""
    conn.execute("BEGIN")
    try:
        yield conn
    finally:
        conn.execute("COMMIT")''','''    """Run several reads against one consistent snapshot. Ends with COMMIT on success and
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
        conn.execute("COMMIT")''')
open(p,'w').write(s)
EOF
uv run pytest tests/integration/test_db.py -W error -q 2>&1 | grep -E "FAILED|passed|failed"
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; uv run pytest tests/integration/test_db.py -W error -q 2>&1 | tail -5
```

<details>
<summary>↳ Result</summary>

```
......................                                                   [100%]
```

</details>

### 🤖 Claude · 2026-10-11 13:18:21 UTC

To confirm the M1 tests fail against the old `read_tx`, I'll temporarily restore the old body and run them.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; cp src/mission_control/infra/db.py /tmp/db_new.py; python3 - <<'EOF'
p='src/mission_control/infra/db.py'
s=open(p).read()
i=s.index('    conn.execute("BEGIN")\n    try:\n        yield conn\n    except')
s=s[:i]+'    conn.execute("BEGIN")\n    try:\n        yield conn\n    finally:\n        conn.execute("COMMIT")\n'
open(p,'w').write(s)
EOF
uv run pytest tests/integration/test_db.py -W error -q -k read_tx 2>&1 | grep -E "FAILED|passed|failed|Error:"; cp /tmp/db_new.py src/mission_control/infra/db.py; uv run pytest tests/integration/test_db.py -q -k read_tx 2>&1 | tail -1
```

<details>
<summary>↳ Result</summary>

```
                raise ValueError("the block failed")
E       AssertionError: assert 1 == 0
        original = ValueError("the block failed after rolling back")
E               ValueError: the block failed after rolling back
        original = ValueError("the block failed after rolling back")
E           sqlite3.OperationalError: cannot commit - no transaction is active
FAILED tests/integration/test_db.py::test_a_write_inside_a_failing_read_tx_is_not_kept
FAILED tests/integration/test_db.py::test_read_tx_lets_the_original_error_through_even_if_the_block_ended_the_transaction
....                                                                     [100%]
```

</details>

### 🤖 Claude · 2026-10-11 13:18:33 UTC

Now security.py and auth.py.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; python3 - <<'EOF'
p='src/mission_control/infra/security.py'
s=open(p).read()
s=s.replace('''from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
''','''from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from mission_control.infra.db import utc_timestamp
''')
s=s.replace('''def iso(moment: datetime) -> str:
    """UTC timestamp in one fixed format, so stored values compare correctly as text."""
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


''','')
s=s.replace('''def password_hash_of(''','''def login_state(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT password_hash, is_active FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def password_hash_of(''')
s=s.replace('iso(created), iso(expires)','utc_timestamp(created), utc_timestamp(expires)')
s=s.replace('iso(now)','utc_timestamp(now)')
open(p,'w').write(s)

p='src/mission_control/services/auth.py'
s=open(p).read()
old_login=s[s.index('    now = _now(now)\n    with write_tx(conn):\n        found'):s.index('    assert user is not None')]
s=s.replace(old_login,'''    now = _now(now)
    # Argon2 is slow, so it runs before the write lock is taken; the transaction then checks
    # that nothing changed since the verify.
    found = security.find_login(conn, email)
    if found is None:
        security.verify_password(security.dummy_hash(), password)  # same cost as a real check
        raise _BAD_LOGIN
    verified_hash = found["password_hash"]
    if not security.verify_password(verified_hash, password):
        raise _BAD_LOGIN
    if not found["is_active"]:
        raise _BAD_LOGIN
    upgraded_hash = (
        security.hash_password(password) if security.needs_rehash(verified_hash) else None
    )
    token = security.new_token()
    expires = now + lifetime
    with write_tx(conn):
        current = security.login_state(conn, found["id"])
        if current is None or current["password_hash"] != verified_hash:
            raise _BAD_LOGIN
        if not current["is_active"]:
            raise _BAD_LOGIN
        if upgraded_hash is not None:
            security.set_password_hash(conn, found["id"], upgraded_hash)
        security.store_token(conn, found["id"], security.hash_token(token), now, expires)
        user = Repos(conn, found["org_id"]).users.get(found["id"])
''')
s=s.replace('''    """End every session of a user. Call inside the caller's transaction when part of a larger
    change (deactivation); this opens its own when used alone."""
    if conn.in_transaction:
        security.revoke_user_tokens(conn, user_id, _now(now))
        return
    with write_tx(conn):''','''    """End every session of a user, in its own write transaction.

    A service making a larger change (such as deactivating a user) doesn't call this: it calls
    security.revoke_user_tokens inside its own write_tx, next to its audit write."""
    with write_tx(conn):''')
s=s.replace('''    now = _now(now)
    with write_tx(conn):
        if not security.verify_password(
            security.password_hash_of(conn, actor.user_id), current_password
        ):
            raise Forbidden("wrong_current_password", "Your current password is incorrect")
        security.set_password_hash(conn, actor.user_id, security.hash_password(new_password))''','''    now = _now(now)
    # Argon2 runs before the write lock is taken; the transaction then checks that the stored
    # hash is still the one the current password was verified against.
    verified_hash = security.password_hash_of(conn, actor.user_id)
    if not security.verify_password(verified_hash, current_password):
        raise _wrong_current_password()
    new_hash = security.hash_password(new_password)
    with write_tx(conn):
        if security.password_hash_of(conn, actor.user_id) != verified_hash:
            raise _wrong_current_password()
        security.set_password_hash(conn, actor.user_id, new_hash)''')
s=s.replace('''def _session_error()''','''def _wrong_current_password() -> Forbidden:
    return Forbidden("wrong_current_password", "Your current password is incorrect")


def _session_error()''')
open(p,'w').write(s)
EOF
grep -rn "\biso\b" src tests; uv run pytest tests/integration/test_db.py tests/integration/test_auth.py tests/integration/test_schema_constraints.py -W error -q 2>&1 | tail -5
```

<details>
<summary>↳ Result</summary>

```
........................................................................ [ 71%]
.............................                                            [100%]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; F="src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py tests/integration/test_db.py tests/integration/test_auth.py"; uv run ruff check src tests; uv run ruff format $F; uv run ruff check src tests && uv run ruff format --check $F; uv run pytest tests/integration/test_db.py tests/integration/test_auth.py tests/integration/test_schema_constraints.py -W error -q 2>&1 | tail -2; grep -n "PRD\|P10\|AC2" src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py
```

<details>
<summary>↳ Result</summary>

```
E501 Line too long (103 > 100)
  --> tests/integration/test_repository_sql.py:80:101
   |
78 |         ("SELECT * FROM organisations WHERE id = ?", "positional ? placeholder"),
79 |         ("SELECT * FROM organisations WHERE id = :id", "no `org_id = :org` filter"),
80 |         ("INSERT INTO audit_events(org_id, event) VALUES (:other, :org)", "no `org_id = :org` filter"),
   |                                                                                                     ^^^
81 |         ("INSERT INTO audit_events(event, org_id) VALUES (:org, :event)", "no `org_id = :org` filter"),
82 |     ],
   |

E501 Line too long (103 > 100)
  --> tests/integration/test_repository_sql.py:81:101
   |
79 |         ("SELECT * FROM organisations WHERE id = :id", "no `org_id = :org` filter"),
80 |         ("INSERT INTO audit_events(org_id, event) VALUES (:other, :org)", "no `org_id = :org` filter"),
81 |         ("INSERT INTO audit_events(event, org_id) VALUES (:org, :event)", "no `org_id = :org` filter"),
   |                                                                                                     ^^^
82 |     ],
83 | )
   |

Found 2 errors.
error: Failed to format src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py tests/integration/test_db.py tests/integration/test_auth.py: No such file or directory (os error 2)
E501 Line too long (103 > 100)
  --> tests/integration/test_repository_sql.py:80:101
   |
78 |         ("SELECT * FROM organisations WHERE id = ?", "positional ? placeholder"),
79 |         ("SELECT * FROM organisations WHERE id = :id", "no `org_id = :org` filter"),
80 |         ("INSERT INTO audit_events(org_id, event) VALUES (:other, :org)", "no `org_id = :org` filter"),
   |                                                                                                     ^^^
81 |         ("INSERT INTO audit_events(event, org_id) VALUES (:org, :event)", "no `org_id = :org` filter"),
82 |     ],
   |

E501 Line too long (103 > 100)
  --> tests/integration/test_repository_sql.py:81:101
   |
79 |         ("SELECT * FROM organisations WHERE id = :id", "no `org_id = :org` filter"),
80 |         ("INSERT INTO audit_events(org_id, event) VALUES (:other, :org)", "no `org_id = :org` filter"),
81 |         ("INSERT INTO audit_events(event, org_id) VALUES (:org, :event)", "no `org_id = :org` filter"),
   |                                                                                                     ^^^
82 |     ],
83 | )
   |

Found 2 errors.
........................................................................ [ 71%]
.............................                                            [100%]
```

</details>

### 🤖 Claude · 2026-10-11 13:18:57 UTC

The only ruff errors are in test_repository_sql.py, which the other agent is editing. zsh didn't split `$F`, so I'll pass the file names directly.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; F=(src/mission_control/infra/db.py src/mission_control/infra/security.py src/mission_control/services/auth.py tests/integration/test_db.py tests/integration/test_auth.py); uv run ruff format "${F[@]}"; uv run ruff check "${F[@]}"; uv run pytest tests/integration/test_db.py tests/integration/test_auth.py tests/integration/test_schema_constraints.py -W error 2>&1 | tail -2; grep -n "def utc_timestamp\|def read_tx\|in_transaction" src/mission_control/infra/db.py; grep -n "def login_state\|utc_timestamp" src/mission_control/infra/security.py; grep -n "def login\|with write_tx\|def revoke_all\|def change_password\|def _wrong" src/mission_control/services/auth.py; grep -n "^def test_\(a_write_inside\|read_tx_lets\|read_tx_commits\|utc_\|a_waiting\)" tests/integration/test_db.py; grep -n "^def test_\(token_expiry_works\|login_runs\|login_rehash\|change_password_\|login_is_refused\|ac26\)" tests/integration/test_auth.py
```

<details>
<summary>↳ Result</summary>

```
1 file reformatted, 4 files left unchanged
All checks passed!
.............................                                            [100%]
101 passed in 1.15s
59:def utc_timestamp(moment: datetime) -> str:
101:def read_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
109:        if conn.in_transaction:
112:    if conn.in_transaction:
15:from mission_control.infra.db import utc_timestamp
63:def login_state(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
82:        (user_id, token_hash, utc_timestamp(created), utc_timestamp(expires)),
95:        (token_hash, utc_timestamp(now)),
102:        (utc_timestamp(now), token_hash),
109:        (utc_timestamp(now), user_id),
32:def login(
59:    with write_tx(conn):
93:    with write_tx(conn):
97:def revoke_all_sessions(
104:    with write_tx(conn):
108:def change_password(
125:    with write_tx(conn):
133:def _wrong_current_password() -> Forbidden:
159:def test_a_waiting_writer_proceeds_once_the_lock_is_released(db_path, conn):
199:def test_a_write_inside_a_failing_read_tx_is_not_kept(conn):
208:def test_read_tx_lets_the_original_error_through_even_if_the_block_ended_the_transaction(conn):
218:def test_read_tx_commits_on_success(conn):
228:def test_utc_timestamp_converts_other_time_zones_to_utc():
235:def test_utc_timestamp_refuses_a_naive_datetime():
240:def test_utc_timestamp_has_the_same_shape_as_the_schema_defaults(conn):
77:def test_ac26_deactivated_user_cannot_log_in(db):
140:def test_token_expiry_works_with_a_non_utc_login_time(db):
298:def test_login_runs_argon2_outside_the_write_transaction(db, monkeypatch, email, password, refused):
308:def test_login_rehash_runs_argon2_outside_the_write_transaction(db, monkeypatch):
318:def test_change_password_runs_argon2_outside_the_write_transaction(db, monkeypatch):
340:def test_login_is_refused_if_the_password_changed_after_it_was_verified(db, monkeypatch):
349:def test_login_is_refused_if_the_user_was_deactivated_after_the_verify(db, monkeypatch):
363:def test_change_password_is_refused_if_the_password_changed_after_it_was_verified(db, monkeypatch):
```

</details>

**🔧 SubagentHandback**

```json
{
  "message": "All six fixes (H2, M1, M2, M3, M5, L2) are in. My files pass 101 tests with `-W error`. Ruff format and check are clean on my five files. `uv run ruff check src tests` still reports 2 E501 (line too long) errors, both in `tests/integration/test_repository_sql.py:80-81`. That file belongs to the other agent, so I left it alone. I edited only my five files, ran no git commands that change state, added no dependencies and left no PRD IDs in src/.\n\nTest-first: the new auth tests failed before the fix (9 failures: the 5 Argon2-outside-the-transaction tests, the 3 race tests and the non-UTC expiry test). The new M1 tests failed against the old `read_tx`, which I checked by putting the old body back temporarily: the write was kept, and \"cannot commit - no transaction is active\" hid the real error. The `utc_timestamp` tests first failed with an ImportError. For M1, I wrote the fix in the same step as the tests, so I proved the failure afterwards by putting the old code back.\n\n**H2: Argon2 no longer runs under the write lock** (`src/mission_control/services/auth.py`)\n- **login (`login` at :32; transaction at :59):**\n  - `find_login`, then the verify (or the dummy verify for an unknown email), the `is_active` check and any rehash all run before the transaction. The token and expiry are created there too.\n  - Inside a short `write_tx`, it re-reads the user with a new helper, `security.login_state` (`security.py:63`, selects `password_hash` and `is_active`).\n  - It refuses with the same `_BAD_LOGIN` if the user is missing, the hash differs from the one verified, or the user is inactive. Otherwise it stores the new hash (if rehashing) and the token.\n  - The order is unchanged, so unknown, wrong and deactivated users each cost exactly one verify. A deactivated user is refused before the rehash, as before.\n- **change_password (`change_password` at :108; transaction at :125):**\n  - It validates the new password, then reads the hash, verifies the current password and computes the new hash, all outside the transaction.\n  - Inside `write_tx`, it refuses if the stored hash no longer equals the verified one. Then it sets the hash, revokes all sessions and audits, as before.\n  - The Forbidden comes from a new `_wrong_current_password()` helper (:133). The code and message are unchanged.\n- **Tests (`tests/integration/test_auth.py`):**\n  - `_record_transaction_state` wraps `security.verify_password` and `hash_password` and records `db.in_transaction` at each call.\n  - `test_login_runs_argon2_outside_the_write_transaction` (:298, covering right password, wrong password and unknown email) asserts exactly `[(\"verify\", False)]`.\n  - The rehash test (:308) and the change_password test (:318) assert `[(\"verify\", False), (\"hash\", False)]`.\n  - Race tests change the stored hash inside the patched verify:\n    - login is refused with `invalid_credentials` and the same message, and no token is stored (:340);\n    - deactivation after the verify is also refused (:349);\n    - change_password is refused with `wrong_current_password`, the session survives, the other hash is kept and nothing is audited (:363).\n\n**M1: `read_tx` rolls back on error** (`src/mission_control/infra/db.py:101-113`)\n- It rolls back on any exception and commits only on success. Both are guarded by `if conn.in_transaction`.\n- **Tests (`test_db.py`):**\n  - a write inside a failing `read_tx` is not kept (:199);\n  - the original exception reaches the caller unchanged (`is original`) even after the block runs ROLLBACK itself (:208);\n  - a commit-on-success test (:218).\n- The existing snapshot test still passes.\n\n**M2: `revoke_all_sessions` always opens its own transaction** (`auth.py:97-105`)\n- The `in_transaction` branch is gone; it always opens its own `write_tx`.\n- The docstring now says a service making a larger change such as deactivation calls `security.revoke_user_tokens` inside its own `write_tx`, next to its audit write.\n- The existing test (`test_revoking_all_sessions_ends_every_session_of_that_user_only`) passes.\n\n**M3: `utc_timestamp`** (`db.py:59`)\n- It refuses naive datetimes with ValueError, converts with `astimezone(UTC)` and formats as `YYYY-MM-DDTHH:MM:SS.mmmZ`.\n- `security.iso` is removed. `security.py` imports `utc_timestamp` (:15) and uses it at :82, :95, :102 and :109. A grep finds no remaining uses of `iso` in src/ or tests/.\n- **Tests:**\n  - 19:00:00.123456+10:00 becomes `2027-01-05T09:00:00.123Z` (`test_db.py:228`);\n  - a naive datetime is refused (:235);\n  - the output has the same regex shape and length as SQLite's `strftime('%Y-%m-%dT%H:%M:%fZ','now')` (:240);\n  - a login at 19:00+10:00 gives a token that is valid at 20:59 UTC and refused at 21:00 UTC (`test_auth.py:140`).\n- As you approved, stored `auth_tokens` timestamps now have 3 fractional digits instead of 6.\n\n**M5: the lock test no longer depends on thread timing** (`test_db.py:159`)\n- `hold_lock` sets an `acquired` Event right after entering `write_tx`. The main thread asserts `acquired.wait(timeout=5)` instead of sleeping 0.05 s.\n- It still proves the waiting writer goes ahead only after the lock is released (`released.is_set()`, count == 2).\n\n**L2** (`test_auth.py:77`): `test_ac26_deactivated_user_cannot_log_in` now also asserts the message is exactly \"Email or password is incorrect\".\n\n**Behaviour preserved:** no existing test was weakened or deleted, and all of them pass unchanged. All codes and messages are the same, and the only data change is the approved 3-digit timestamps.\n\n**Final output:**\n- `uv run pytest tests/integration/test_db.py tests/integration/test_auth.py tests/integration/test_schema_constraints.py -W error`: 101 passed in 1.15s.\n- `ruff format` on the five files: 1 file reformatted, 4 left unchanged.\n- `ruff check` on the five files: All checks passed!"
}
```

<details>
<summary>↳ Result</summary>

```
{"success":true,"message":"Report delivered to your caller."}
```

</details>
