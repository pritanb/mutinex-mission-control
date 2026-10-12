"""What every use case runs with: who is acting, their organisation's repositories, the time,
one transaction and its audit trail.

A use case follows one shape: load through `ctx.repos`, check with domain rules, then write and
audit inside `with ctx.write():`. Refusals raise `Forbidden`, `NotFound` or `RuleViolation`.
"""

import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control.domain.errors import Forbidden, NotFound, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import NO_CONTEXT, Action, Actor, Context, authorize
from mission_control.infra.db import read_tx, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission


class ServiceContext:
    def __init__(self, conn: sqlite3.Connection, actor: Actor, now: datetime | None = None):
        if now is not None and now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        self.conn = conn
        self.actor = actor
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.repos = Repos(conn, actor.org_id)

    @contextmanager
    def write(self) -> Generator[Repos]:
        """One write transaction: the lock is taken before any check inside the block, and
        everything, audit included, commits together or not at all."""
        with write_tx(self.conn):
            yield self.repos

    @contextmanager
    def read(self) -> Generator[Repos]:
        """Several reads against one consistent snapshot."""
        with read_tx(self.conn):
            yield self.repos

    def audit(self, event: Event, **fields: object) -> None:
        """Record an event as the acting user. Only inside `write()`, so it commits with the
        change it describes."""
        if not self.conn.in_transaction:
            raise RuntimeError("audit events are written inside ctx.write()")
        self.repos.audit.record(self.actor.user_id, event, **fields)  # type: ignore[arg-type]

    def authorize(self, action: Action, context: Context = NO_CONTEXT) -> None:
        """For a resource the actor can see: refusal is Forbidden (403)."""
        authorize(self.actor, action, context)

    def authorize_view(self, action: Action, context: Context, what: str) -> None:
        """For looking at something: a refusal is reported as NotFound (404), so the response
        never reveals that it exists."""
        try:
            authorize(self.actor, action, context)
        except Forbidden as refused:
            raise NotFound(what) from refused


def found[T](value: T | None, what: str) -> T:
    """The loaded record, or NotFound if the repository returned None."""
    if value is None:
        raise NotFound(what)
    return value


def visible_mission(ctx: ServiceContext, repos: Repos, mission_id: int) -> Mission:
    """The mission if the actor may see it; NotFound if it's missing or hidden from them."""
    return found(repos.missions.get_visible(ctx.actor, mission_id), "Mission")


def mission_context(repos: Repos, mission: Mission) -> Context:
    """Everything the permission rules may ask about a mission."""
    return Context(
        owner_id=mission.owner_id,
        created_by_id=mission.created_by_id,
        rostered_user_ids=repos.missions.rostered_user_ids(mission.id),
    )


def check(problems: Sequence[Problem], message: str) -> None:
    """Raise every problem at once as a RuleViolation; do nothing if there are none."""
    if problems:
        raise RuleViolation(message, problems)
