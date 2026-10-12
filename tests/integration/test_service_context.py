"""SF: the service context every use case runs in (design §2, §4)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, NotFound, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, Actor, Context
from mission_control.services.context import ServiceContext, check, found

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)


def audit_count(conn):
    return conn.execute("SELECT count(*) FROM audit_events").fetchone()[0]


def test_context_is_scoped_to_the_actors_organisation(seeded_db):
    ctx = ServiceContext(seeded_db, LEE, now=NOW)
    assert ctx.repos.org_id == 1
    assert ctx.repos.missions.get(8) is None  # Helix mission


def test_now_must_be_timezone_aware_and_is_kept_in_utc(seeded_db):
    with pytest.raises(ValueError):
        ServiceContext(seeded_db, LEE, now=datetime(2027, 1, 5, 9, 0))
    ctx = ServiceContext(
        seeded_db, LEE, now=datetime(2027, 1, 5, 19, tzinfo=timezone(timedelta(hours=10)))
    )
    assert ctx.now == NOW


def test_now_defaults_to_the_current_utc_time(seeded_db):
    ctx = ServiceContext(seeded_db, LEE)
    assert ctx.now.tzinfo is not None
    assert abs((datetime.now(UTC) - ctx.now).total_seconds()) < 5


def test_write_commits_the_change_and_its_audit_together(seeded_db):
    ctx = ServiceContext(seeded_db, LEE, now=NOW)
    before = audit_count(seeded_db)
    with ctx.write():
        ctx.audit(Event.MISSION_CREATED, mission_id=1, data={"mission_name": "x"})
    assert audit_count(seeded_db) == before + 1
    actor_id, event = seeded_db.execute(
        "SELECT actor_id, event FROM audit_events ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert (actor_id, event) == (LEE.user_id, "mission.created")


def test_a_refused_write_leaves_no_audit_behind(seeded_db):
    ctx = ServiceContext(seeded_db, LEE, now=NOW)
    before = audit_count(seeded_db)
    with pytest.raises(RuleViolation):
        with ctx.write():
            ctx.audit(Event.MISSION_CREATED, mission_id=1)
            check([Problem("slot_unfilled", "Commander: 1 place unfilled")], "Can't submit")
    assert audit_count(seeded_db) == before


def test_audit_outside_a_write_transaction_is_a_programming_error(seeded_db):
    with pytest.raises(RuntimeError):
        ServiceContext(seeded_db, LEE, now=NOW).audit(Event.MISSION_CREATED, mission_id=1)


def test_authorize_raises_forbidden_for_a_visible_resource(seeded_db):
    ctx = ServiceContext(seeded_db, LEE, now=NOW)
    with pytest.raises(Forbidden) as err:
        ctx.authorize(Action.MANAGE_ORG)
    assert err.value.code == "role_forbidden"


def test_a_refused_view_is_reported_as_not_found(seeded_db):
    ctx = ServiceContext(seeded_db, BEN, now=NOW)
    with pytest.raises(NotFound) as err:
        ctx.authorize_view(Action.VIEW_CREW, Context(target_user_id=11), "Crew member")
    assert (err.value.code, err.value.message) == ("not_found", "Crew member not found")


def test_an_allowed_view_passes(seeded_db):
    ServiceContext(seeded_db, BEN, now=NOW).authorize_view(
        Action.VIEW_CREW, Context(target_user_id=BEN.user_id), "Crew member"
    )


def test_found_returns_the_value_or_raises_not_found():
    assert found(5, "Mission") == 5
    with pytest.raises(NotFound, match="Mission not found"):
        found(None, "Mission")


def test_check_passes_with_no_problems_and_raises_every_problem_otherwise():
    check([], "fine")
    problems = [Problem("a", "first"), Problem("b", "second")]
    with pytest.raises(RuleViolation) as err:
        check(problems, "Mission can't be submitted")
    assert err.value.problems == tuple(problems)
