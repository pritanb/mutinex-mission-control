"""Logging in and out, resolving a request's token to an Actor, and changing passwords."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, Unauthenticated
from mission_control.domain.passwords import validate_password
from mission_control.domain.permissions import Actor
from mission_control.infra import security
from mission_control.infra.db import read_tx, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import User

SESSION_LIFETIME = timedelta(hours=12)

_BAD_LOGIN = Unauthenticated("invalid_credentials", "Email or password is incorrect")


@dataclass(frozen=True)
class Session:
    token: str  # shown to the client once; only its hash is stored
    expires_at: datetime
    user: User


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


def login(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    *,
    now: datetime | None = None,
    lifetime: timedelta = SESSION_LIFETIME,
) -> Session:
    """Unknown email, wrong password and deactivated user all get the same refusal, so the
    response never reveals which accounts exist."""
    now = _now(now)
    with write_tx(conn):
        found = security.find_login(conn, email)
        if found is None:
            security.verify_password(security.dummy_hash(), password)  # same cost as a real check
            raise _BAD_LOGIN
        if not security.verify_password(found["password_hash"], password):
            raise _BAD_LOGIN
        if not found["is_active"]:
            raise _BAD_LOGIN
        if security.needs_rehash(found["password_hash"]):
            security.set_password_hash(conn, found["id"], security.hash_password(password))
        token = security.new_token()
        expires = now + lifetime
        security.store_token(conn, found["id"], security.hash_token(token), now, expires)
        user = Repos(conn, found["org_id"]).users.get(found["id"])
    assert user is not None
    return Session(token=token, expires_at=expires, user=user)


def authenticate(
    conn: sqlite3.Connection, token: str | None, *, now: datetime | None = None
) -> Actor:
    """Resolve a bearer token to the current Actor. Nothing is cached: role and active status
    are read on every call, so changes apply to the very next request."""
    if not token:
        raise _session_error()
    with read_tx(conn):
        row = security.find_session(conn, security.hash_token(token), _now(now))
    if row is None:
        raise _session_error()
    return Actor(
        user_id=row["id"],
        org_id=row["org_id"],
        role=Role(row["role"]),
        crew_profile_id=row["crew_profile_id"],
    )


def logout(conn: sqlite3.Connection, token: str, *, now: datetime | None = None) -> None:
    with write_tx(conn):
        security.revoke_token(conn, security.hash_token(token), _now(now))


def revoke_all_sessions(
    conn: sqlite3.Connection, user_id: int, *, now: datetime | None = None
) -> None:
    """End every session of a user. Call inside the caller's transaction when part of a larger
    change (deactivation); this opens its own when used alone."""
    if conn.in_transaction:
        security.revoke_user_tokens(conn, user_id, _now(now))
        return
    with write_tx(conn):
        security.revoke_user_tokens(conn, user_id, _now(now))


def change_password(
    conn: sqlite3.Connection,
    actor: Actor,
    current_password: str,
    new_password: str,
    *,
    now: datetime | None = None,
) -> None:
    """Needs the current password. Every session ends, including the one used to change it."""
    validate_password(new_password)
    now = _now(now)
    with write_tx(conn):
        if not security.verify_password(
            security.password_hash_of(conn, actor.user_id), current_password
        ):
            raise Forbidden("wrong_current_password", "Your current password is incorrect")
        security.set_password_hash(conn, actor.user_id, security.hash_password(new_password))
        security.revoke_user_tokens(conn, actor.user_id, now)
        Repos(conn, actor.org_id).audit.record(actor.user_id, "user.password_changed")


def _session_error() -> Unauthenticated:
    return Unauthenticated(
        "unauthenticated", "Your session has expired or isn't valid; log in again"
    )
