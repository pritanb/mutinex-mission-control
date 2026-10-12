"""M13: ending a mission. Complete and cancel, and what they do to its assignments (PRD §5.4;
AC-5, AC-6, AC-7; scenario S1; design §5).

Seed ids (PRD §9): Ruth 1 · Ingrid 3 · Lee 4 · Nora 5 · Chen 8 · Sam 14 (Helix).
Missions: Gateway 1 (Draft, Lee) · Station Reboost 3 (Draft, Nora, Gus accepted) · Telescope 5
(Active, Lee: Chen, Dana, Eli and Hana accepted) · Deep Space Comms 6 (Pending, Nora, Ben
accepted) · Mars Analog 7 (Completed, Lee).
"""

import json
from datetime import UTC, datetime

import pytest

from mission_control.domain.enums import MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import missions
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
INGRID = Actor(user_id=3, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
CHEN = Actor(user_id=8, org_id=1, role=Role.CREW, crew_profile_id=8)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

GATEWAY, REBOOST, TELESCOPE, DEEP_SPACE, MARS = 1, 3, 5, 6, 7


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def statuses(conn, mission_id):
    """{crew profile id: assignment status} on the mission."""
    return dict(
        conn.execute(
            "SELECT crew_profile_id, status FROM assignments WHERE mission_id = ? ORDER BY id",
            (mission_id,),
        ).fetchall()
    )


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]


def audit_since(conn, since_id):
    rows = conn.execute(
        "SELECT actor_id, event, crew_profile_id, from_status, to_status, reason, data"
        " FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(*tuple(r)[:6], json.loads(r["data"])) for r in rows]


def snapshot(conn):
    tables = ("missions", "assignments", "approvals", "audit_events")
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


# --- Complete (§5.4, S1) ------------------------------------------------------------------


def test_s1_owner_completes_an_active_mission_and_its_crew_are_completed(seeded_db):
    since = last_audit_id(seeded_db)

    done = missions.complete_mission(as_(seeded_db, LEE), TELESCOPE)

    assert done.mission.status == MissionStatus.COMPLETED
    assert set(statuses(seeded_db, TELESCOPE).values()) == {"completed"}
    events = audit_since(seeded_db, since)
    assert events[0] == (
        4,
        "mission.completed",
        None,
        "active",
        "completed",
        None,
        {"mission_name": "Orbital Telescope Service"},
    )
    assert [(e[1], e[2], e[3], e[4]) for e in events[1:]] == [
        ("assignment.completed", crew, "accepted", "completed") for crew in (8, 9, 10, 13)
    ]


def test_a_director_can_complete_any_mission(seeded_db):
    done = missions.complete_mission(as_(seeded_db, INGRID), TELESCOPE)
    assert done.mission.status == MissionStatus.COMPLETED


@pytest.mark.parametrize(
    ("actor", "code"), [(NORA, "not_owner"), (CHEN, "role_forbidden")], ids=["lead", "crew"]
)
def test_only_the_owner_or_a_director_can_complete(seeded_db, actor, code):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as caught:
        missions.complete_mission(as_(seeded_db, actor), TELESCOPE)
    assert caught.value.code == code
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    ("mission_id", "actor", "code", "message"),
    [
        (GATEWAY, LEE, "invalid_transition", "Can't complete a mission in draft"),
        (DEEP_SPACE, NORA, "invalid_transition", "Can't complete a mission pending approval"),
        (MARS, LEE, "mission_final", "Can't complete a mission that's completed"),
    ],
)
def test_only_an_active_mission_can_be_completed(seeded_db, mission_id, actor, code, message):
    with pytest.raises(StateConflict) as caught:
        missions.complete_mission(as_(seeded_db, actor), mission_id)
    assert (caught.value.code, caught.value.message) == (code, message)


# --- Cancel (AC-5, AC-6) ------------------------------------------------------------------


@pytest.mark.parametrize("reason", [None, "", "  "])
def test_ac6_cancelling_needs_a_reason(seeded_db, reason):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as caught:
        missions.cancel_mission(as_(seeded_db, NORA), REBOOST, reason)
    assert caught.value.message == "Cancelling Station Reboost needs a reason"
    assert snapshot(seeded_db) == before


def test_ac6_owner_cancels_and_open_assignments_are_cancelled(seeded_db):
    since = last_audit_id(seeded_db)

    cancelled = missions.cancel_mission(as_(seeded_db, NORA), REBOOST, " Funding pulled ")

    assert cancelled.mission.status == MissionStatus.CANCELLED
    assert statuses(seeded_db, REBOOST) == {12: "cancelled"}  # Gus
    assert audit_since(seeded_db, since) == [
        (
            5,
            "mission.cancelled",
            None,
            "draft",
            "cancelled",
            "Funding pulled",
            {"mission_name": "Station Reboost"},
        ),
        (
            5,
            "assignment.cancelled",
            12,
            "accepted",
            "cancelled",
            None,
            {"mission_name": "Station Reboost", "slot_name": "Engineer", "crew_name": "Gus"},
        ),
    ]


def test_ac5_ac6_any_director_can_cancel_an_active_mission(seeded_db):
    cancelled = missions.cancel_mission(as_(seeded_db, RUTH), TELESCOPE, "Launch scrubbed")
    assert cancelled.mission.status == MissionStatus.CANCELLED
    assert set(statuses(seeded_db, TELESCOPE).values()) == {"cancelled"}


def test_cancelling_a_pending_mission_cancels_its_crew_and_hides_its_approvals(seeded_db):
    cancelled = missions.cancel_mission(as_(seeded_db, NORA), DEEP_SPACE, "Superseded")
    assert cancelled.mission.status == MissionStatus.CANCELLED
    assert statuses(seeded_db, DEEP_SPACE) == {7: "cancelled"}  # Ben
    assert cancelled.approvals == ()


def test_ac6_another_lead_cannot_cancel(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as caught:
        missions.cancel_mission(as_(seeded_db, LEE), REBOOST, "Not mine")
    assert caught.value.code == "not_owner"
    assert snapshot(seeded_db) == before


def test_crew_cannot_cancel_a_mission_they_are_on(seeded_db):
    with pytest.raises(Forbidden) as caught:
        missions.cancel_mission(as_(seeded_db, CHEN), TELESCOPE, "Tired")
    assert caught.value.code == "role_forbidden"


def test_a_finished_mission_cannot_be_cancelled(seeded_db):
    with pytest.raises(StateConflict) as caught:
        missions.cancel_mission(as_(seeded_db, LEE), MARS, "Too late")
    assert (caught.value.code, caught.value.message) == (
        "mission_final",
        "Can't cancel a mission that's completed",
    )


def test_completing_leaves_closed_assignments_alone(seeded_db):
    seeded_db.execute(
        "UPDATE assignments SET status = 'withdrawn', reason = 'x' WHERE id = ?",
        (
            seeded_db.execute(
                "SELECT id FROM assignments WHERE mission_id = 5 AND crew_profile_id = 13"
            ).fetchone()[0],
        ),
    )
    missions.complete_mission(as_(seeded_db, LEE), TELESCOPE)
    assert statuses(seeded_db, TELESCOPE)[13] == "withdrawn"


# --- Tenant isolation (AC-29) -------------------------------------------------------------


def test_ac29_ending_another_organisations_mission_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        missions.complete_mission(as_(seeded_db, SAM), TELESCOPE)
    with pytest.raises(NotFound):
        missions.cancel_mission(as_(seeded_db, SAM), REBOOST, "Not ours")
    assert snapshot(seeded_db) == before
