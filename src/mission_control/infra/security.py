"""Password hashing, session tokens, and the only lookups not scoped to an organisation.

Login and token resolution happen before the caller's organisation is known, so these queries
look users up by email or token hash. Everything else goes through tenant-scoped repositories.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


_dummy_hashes: dict[int, str] = {}


def dummy_hash() -> str:
    """A real Argon2 hash of a random secret, made with the current hasher. Verifying against
    it when an email doesn't exist makes that path cost the same as a real check, so response
    time doesn't reveal which accounts exist."""
    key = id(_hasher)
    if key not in _dummy_hashes:
        _dummy_hashes[key] = _hasher.hash(secrets.token_urlsafe(32))
    return _dummy_hashes[key]


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_token() -> str:
    """32 random bytes, URL-safe. Returned to the client once and never stored."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def iso(moment: datetime) -> str:
    """UTC timestamp in one fixed format, so stored values compare correctly as text."""
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def find_login(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, org_id, password_hash, is_active FROM users WHERE email = ?", (email,)
    ).fetchone()


def password_hash_of(conn: sqlite3.Connection, user_id: int) -> str:
    return conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()[0]


def set_password_hash(conn: sqlite3.Connection, user_id: int, password_hash: str) -> None:
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def store_token(
    conn: sqlite3.Connection, user_id: int, token_hash: str, created: datetime, expires: datetime
) -> None:
    conn.execute(
        "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token_hash, iso(created), iso(expires)),
    )


def find_session(conn: sqlite3.Connection, token_hash: str, now: datetime) -> sqlite3.Row | None:
    """The user behind a live session: not revoked, not expired, and still active."""
    return conn.execute(
        """SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id
           FROM auth_tokens t
           JOIN users u ON u.id = t.user_id
           LEFT JOIN crew_profiles p ON p.org_id = u.org_id AND p.user_id = u.id
           WHERE t.token_hash = ? AND t.revoked_at IS NULL AND t.expires_at > ?
             AND u.is_active = 1""",
        (token_hash, iso(now)),
    ).fetchone()


def revoke_token(conn: sqlite3.Connection, token_hash: str, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
        (iso(now), token_hash),
    )


def revoke_user_tokens(conn: sqlite3.Connection, user_id: int, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
        (iso(now), user_id),
    )
