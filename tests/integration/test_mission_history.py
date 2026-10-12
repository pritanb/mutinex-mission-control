"""M13: a mission's history, read from the audit trail (PRD §5.7 V1; AC-1, AC-27; scenario S1;
design §7 `GET /missions/{id}/history`).

Seed ids (PRD §9): Ruth 1 · Marco 2 · Ingrid 3 · Lee 4 · Nora 5 · Ana 6 · Ben 7 · Chen 8 ·
Dana 9 · Sam 14 (Helix). Missions: Gateway 1 · Deep Space Comms 6 (Ben accepted).
"""

from datetime import UTC, datetime

import pytest

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, NotFound
from mission_control.domain.events import Event
from mission_control.domain.permissions import Actor
from mission_control.services import approvals, assignments, audit, missions
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
MARCO = Actor(user_id=2, org_id=1, role=Role.DIRECTOR, crew_profile_id=2)
INGRID = Actor(user_id=3, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
CHEN = Actor(user_id=8, org_id=1, role=Role.CREW, crew_profile_id=8)
DANA = Actor(user_id=9, org_id=1, role=Role.CREW, crew_profile_id=9)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

GATEWAY, DEEP_SPACE = 1, 6
FLIGHT_ENGINEER, SPECIALIST, COMMANDER = 1, 2, 3


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def run_s1(conn):
    """The golden path: propose, accept, submit, Ruth refused, Marco and Ingrid approve,
    complete."""
    made = [
        assignments.propose(as_(conn, LEE), GATEWAY, COMMANDER, 6),
        assignments.propose(as_(conn, LEE), GATEWAY, FLIGHT_ENGINEER, 8),
        assignments.propose(as_(conn, LEE), GATEWAY, SPECIALIST, 9),
    ]
    for actor, assignment in zip((ANA, CHEN, DANA), made, strict=True):
        assignments.accept(as_(conn, actor), assignment.id)
    approvals.submit(as_(conn, LEE), GATEWAY)
    with pytest.raises(Forbidden):
        approvals.approve(as_(conn, RUTH), GATEWAY)
    approvals.approve(as_(conn, MARCO), GATEWAY)
    approvals.approve(as_(conn, INGRID), GATEWAY)
    missions.complete_mission(as_(conn, LEE), GATEWAY)


def test_ac1_s1_every_transition_is_in_the_history_with_who_and_when(seeded_db):
    run_s1(seeded_db)

    history = audit.mission_history(as_(seeded_db, LEE), GATEWAY)

    assert [(h.event, h.actor_name, h.from_status, h.to_status) for h in history] == [
        (Event.MISSION_CREATED, "Ruth Adeyemi", None, "draft"),
        (Event.ASSIGNMENT_PROPOSED, "Lee Park", None, "proposed"),
        (Event.ASSIGNMENT_PROPOSED, "Lee Park", None, "proposed"),
        (Event.ASSIGNMENT_PROPOSED, "Lee Park", None, "proposed"),
        (Event.ASSIGNMENT_ACCEPTED, "Ana Okafor", "proposed", "accepted"),
        (Event.ASSIGNMENT_ACCEPTED, "Chen Wu", "proposed", "accepted"),
        (Event.ASSIGNMENT_ACCEPTED, "Dana Reyes", "proposed", "accepted"),
        (Event.MISSION_SUBMITTED, "Lee Park", "draft", "pending_approval"),
        (Event.MISSION_APPROVED, "Marco Bianchi", None, None),
        (Event.MISSION_APPROVED, "Ingrid Holm", None, None),
        (Event.MISSION_ACTIVATED, "Ingrid Holm", "pending_approval", "active"),
        (Event.MISSION_COMPLETED, "Lee Park", "active", "completed"),
        (Event.ASSIGNMENT_COMPLETED, "Lee Park", "accepted", "completed"),
        (Event.ASSIGNMENT_COMPLETED, "Lee Park", "accepted", "completed"),
        (Event.ASSIGNMENT_COMPLETED, "Lee Park", "accepted", "completed"),
    ]
    assert all(h.at.tzinfo is not None for h in history)
    assert [h.data["crew_name"] for h in history[1:4]] == ["Ana", "Chen", "Dana"]


def test_v1_history_keeps_reasons(seeded_db):
    approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, "Budget not signed off")
    last = audit.mission_history(as_(seeded_db, NORA), DEEP_SPACE)[-1]
    assert (last.event, last.actor_name, last.reason) == (
        Event.MISSION_REJECTED,
        "Ingrid Holm",
        "Budget not signed off",
    )


def test_v1_crew_on_the_mission_can_see_its_history(seeded_db):
    approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, "Budget not signed off")
    assert audit.mission_history(as_(seeded_db, BEN), DEEP_SPACE)[-1].event == (
        Event.MISSION_REJECTED
    )


def test_v2_crew_not_on_the_mission_get_not_found(seeded_db):
    with pytest.raises(NotFound):
        audit.mission_history(as_(seeded_db, BEN), GATEWAY)


def test_ac27_another_organisations_mission_history_is_not_found(seeded_db):
    with pytest.raises(NotFound):
        audit.mission_history(as_(seeded_db, SAM), DEEP_SPACE)


def test_history_includes_what_happened_before_today(seeded_db):
    history = audit.mission_history(as_(seeded_db, NORA), DEEP_SPACE)
    assert [(h.event, h.actor_name) for h in history] == [
        (Event.MISSION_CREATED, "Nora Quinn"),
        (Event.MISSION_SUBMITTED, "Nora Quinn"),
        (Event.MISSION_APPROVED, "Marco Bianchi"),
    ]
