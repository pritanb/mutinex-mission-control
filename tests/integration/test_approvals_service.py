"""M13: the approval round. Submit, approve and reject (PRD §5.4, §5.5; AC-2, AC-3, AC-8 to
AC-13, AC-30; scenarios S1, S6, S7, S8; design §5).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Marco 2 · Ingrid 3 ·
Lee 4 · Nora 5 · Ana 6 · Ben 7 · Chen 8 · Dana 9 · Sam 14 (Helix) · Priya 15 (Helix).
Missions: Gateway 1 (Draft, Lee, created by Ruth) · Medical Study 4 (Draft, Nora, created by
Ruth, Marco accepted) · Telescope 5 (Active) · Deep Space Comms 6 (Pending round 1 of N = 2,
Ben accepted, Marco approved) · Payload Demo 8 (Helix, Draft, Lena and Omar accepted).
Gateway slots: Flight Engineer 1 · Mission Specialist 2 · Commander 3.
"""

import json
from datetime import UTC, datetime

import pytest

from mission_control.domain.enums import MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import approvals, assignments
from mission_control.services.context import ServiceContext
from mission_control.services.missions import get_mission

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
PRIYA = Actor(user_id=15, org_id=2, role=Role.LEAD, crew_profile_id=None)

GATEWAY, MEDICAL, TELESCOPE, DEEP_SPACE, PAYLOAD = 1, 4, 5, 6, 8
FLIGHT_ENGINEER, SPECIALIST, COMMANDER = 1, 2, 3
ANA_ID, CHEN_ID, DANA_ID = 6, 8, 9
SYS_ENG = 3


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def mission_row(conn, mission_id):
    r = conn.execute(
        "SELECT status, approval_round, approvals_required FROM missions WHERE id = ?",
        (mission_id,),
    ).fetchone()
    return tuple(r)


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]


def audit_since(conn, since_id):
    rows = conn.execute(
        "SELECT actor_id, event, mission_id, from_status, to_status, reason, data"
        " FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(*tuple(r)[:6], json.loads(r["data"])) for r in rows]


def snapshot(conn):
    """Every table the approval round could change, to prove a refusal changed nothing."""
    tables = ("missions", "assignments", "approvals", "audit_events")
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


def problems_of(error):
    return [(p.code, p.message) for p in error.problems]


def staff_gateway(conn):
    """S1 up to acceptance: Lee proposes Ana, Chen and Dana, and all three accept."""
    made = [
        assignments.propose(as_(conn, LEE), GATEWAY, COMMANDER, ANA_ID),
        assignments.propose(as_(conn, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID),
        assignments.propose(as_(conn, LEE), GATEWAY, SPECIALIST, DANA_ID),
    ]
    for actor, assignment in zip((ANA, CHEN, DANA), made, strict=True):
        assignments.accept(as_(conn, actor), assignment.id)
    return made


# --- Submit (§5.4, AC-2, AC-12, S7) -------------------------------------------------------


def test_s1_owner_submits_a_fully_staffed_mission(seeded_db):
    staff_gateway(seeded_db)
    since = last_audit_id(seeded_db)

    submitted = approvals.submit(as_(seeded_db, LEE), GATEWAY)

    assert submitted.mission.status == MissionStatus.PENDING_APPROVAL
    assert mission_row(seeded_db, GATEWAY) == ("pending_approval", 1, 2)
    assert audit_since(seeded_db, since) == [
        (
            4,
            "mission.submitted",
            GATEWAY,
            "draft",
            "pending_approval",
            None,
            {"mission_name": "Lunar Gateway Resupply", "round": 1, "approvals_required": 2},
        )
    ]


def test_ac2_submit_lists_unfilled_places_and_unanswered_proposals_at_once(seeded_db):
    assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)
    before = snapshot(seeded_db)

    with pytest.raises(RuleViolation) as caught:
        approvals.submit(as_(seeded_db, LEE), GATEWAY)

    assert caught.value.code == "rule_violation"
    assert caught.value.message == "Lunar Gateway Resupply can't be submitted"
    assert problems_of(caught.value) == [
        ("slot_unfilled", "Flight Engineer: 1 place unfilled"),
        ("slot_unfilled", "Mission Specialist: 1 place unfilled"),
        ("proposal_unanswered", "Commander: Ana hasn't responded to the proposal"),
    ]
    assert snapshot(seeded_db) == before


def test_s7_submit_is_refused_with_too_few_eligible_approvers(seeded_db):
    """Ruth created the Medical Study and Marco is on it, leaving only Ingrid of the 2 needed."""
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as caught:
        approvals.submit(as_(seeded_db, NORA), MEDICAL)
    assert problems_of(caught.value) == [
        ("insufficient_approvers", "1 eligible approver, 2 required")
    ]
    assert snapshot(seeded_db) == before


def test_submit_rechecks_accepted_crew_are_still_eligible(seeded_db):
    staff_gateway(seeded_db)
    seeded_db.execute("DELETE FROM crew_skills WHERE crew_profile_id = ? AND skill_id = ?", (8, 3))
    with pytest.raises(RuleViolation) as caught:
        approvals.submit(as_(seeded_db, LEE), GATEWAY)
    assert [p.code for p in caught.value.problems] == ["skill_below_minimum"]


def test_ac12_deactivated_directors_are_not_eligible_approvers(seeded_db):
    staff_gateway(seeded_db)
    seeded_db.execute("UPDATE users SET is_active = 0 WHERE id = 3")  # Ingrid
    with pytest.raises(RuleViolation) as caught:
        approvals.submit(as_(seeded_db, LEE), GATEWAY)
    assert problems_of(caught.value) == [
        ("insufficient_approvers", "1 eligible approver, 2 required")
    ]


def test_ac7_only_the_owner_can_submit(seeded_db):
    staff_gateway(seeded_db)
    for actor, code in ((NORA, "not_owner"), (RUTH, "role_forbidden"), (ANA, "not_owner")):
        with pytest.raises(Forbidden) as caught:
            approvals.submit(as_(seeded_db, actor), GATEWAY)
        assert caught.value.code == code


def test_submitting_a_pending_mission_is_an_invalid_transition(seeded_db):
    with pytest.raises(StateConflict) as caught:
        approvals.submit(as_(seeded_db, NORA), DEEP_SPACE)
    assert (caught.value.code, caught.value.message) == (
        "invalid_transition",
        "Can't submit a mission pending approval",
    )


def test_tr10_crew_submitting_a_mission_they_are_not_on_gets_not_found(seeded_db):
    with pytest.raises(NotFound):
        approvals.submit(as_(seeded_db, BEN), GATEWAY)


# --- Approve (§5.5, AC-3, AC-8, AC-9, AC-11, AC-13) ---------------------------------------


def test_ac3_approvals_before_the_nth_leave_the_mission_pending(seeded_db):
    staff_gateway(seeded_db)
    approvals.submit(as_(seeded_db, LEE), GATEWAY)
    since = last_audit_id(seeded_db)

    after = approvals.approve(as_(seeded_db, MARCO), GATEWAY)

    assert after.mission.status == MissionStatus.PENDING_APPROVAL
    assert audit_since(seeded_db, since) == [
        (
            2,
            "mission.approved",
            GATEWAY,
            None,
            None,
            None,
            {"mission_name": "Lunar Gateway Resupply", "round": 1, "approvals": 1, "required": 2},
        )
    ]


def test_ac3_the_nth_approval_makes_the_mission_active(seeded_db):
    since = last_audit_id(seeded_db)
    after = approvals.approve(as_(seeded_db, INGRID), DEEP_SPACE)  # Marco already approved

    assert after.mission.status == MissionStatus.ACTIVE
    assert mission_row(seeded_db, DEEP_SPACE) == ("active", 1, 2)
    events = audit_since(seeded_db, since)
    assert [(e[0], e[1], e[3], e[4]) for e in events] == [
        (3, "mission.approved", None, None),
        (3, "mission.activated", "pending_approval", "active"),
    ]
    assert events[0][6]["approvals"] == 2


def test_ac8_s1_the_creator_cannot_approve(seeded_db):
    staff_gateway(seeded_db)
    approvals.submit(as_(seeded_db, LEE), GATEWAY)
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as caught:
        approvals.approve(as_(seeded_db, RUTH), GATEWAY)
    assert (caught.value.code, caught.value.message) == (
        "approver_is_creator",
        "You can't approve a mission you created",
    )
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize("actor", [LEE, BEN], ids=["lead", "crew_on_the_mission"])
def test_ac9_leads_and_crew_cannot_approve_or_reject(seeded_db, actor):
    for decide in (
        lambda ctx: approvals.approve(ctx, DEEP_SPACE),
        lambda ctx: approvals.reject(ctx, DEEP_SPACE, "Not ready"),
    ):
        with pytest.raises(Forbidden) as caught:
            decide(as_(seeded_db, actor))
        assert caught.value.code == "role_forbidden"


def test_ac11_a_director_on_the_roster_cannot_approve(seeded_db):
    seeded_db.execute("UPDATE organisations SET required_approvals = 1 WHERE id = 1")
    approvals.submit(as_(seeded_db, NORA), MEDICAL)  # Ingrid is the one eligible approver
    with pytest.raises(Forbidden) as caught:
        approvals.approve(as_(seeded_db, MARCO), MEDICAL)
    assert caught.value.code == "approver_is_rostered"
    assert approvals.approve(as_(seeded_db, INGRID), MEDICAL).mission.status == MissionStatus.ACTIVE


def test_s8_helix_needs_a_single_approval(seeded_db):
    approvals.submit(as_(seeded_db, PRIYA), PAYLOAD)
    assert mission_row(seeded_db, PAYLOAD) == ("pending_approval", 1, 1)
    assert approvals.approve(as_(seeded_db, SAM), PAYLOAD).mission.status == MissionStatus.ACTIVE


def test_a1_n_is_fixed_when_the_mission_is_submitted(seeded_db):
    """Deep Space Comms was submitted needing 2; raising the setting to 3 doesn't change that."""
    seeded_db.execute("UPDATE organisations SET required_approvals = 3 WHERE id = 1")
    assert (
        approvals.approve(as_(seeded_db, INGRID), DEEP_SPACE).mission.status == MissionStatus.ACTIVE
    )


@pytest.mark.parametrize(
    "change",
    ["UPDATE users SET is_active = 0 WHERE id = 2", "UPDATE users SET role = 'lead' WHERE id = 2"],
    ids=["deactivated", "demoted"],
)
def test_a1_an_approval_still_counts_after_its_director_leaves(seeded_db, change):
    seeded_db.execute(change)  # Marco, who already approved Deep Space Comms
    assert (
        approvals.approve(as_(seeded_db, INGRID), DEEP_SPACE).mission.status == MissionStatus.ACTIVE
    )


def test_approval_rechecks_the_roster_and_writes_nothing_if_it_fails(seeded_db):
    seeded_db.execute("DELETE FROM crew_skills WHERE crew_profile_id = 7 AND skill_id = ?", (3,))
    before = snapshot(seeded_db)

    with pytest.raises(RuleViolation) as caught:
        approvals.approve(as_(seeded_db, INGRID), DEEP_SPACE)

    assert caught.value.message == "Deep Space Comms Upgrade can't be approved"
    assert [p.code for p in caught.value.problems] == ["skill_below_minimum"]
    assert snapshot(seeded_db) == before
    assert mission_row(seeded_db, DEEP_SPACE) == ("pending_approval", 1, 2)


@pytest.mark.parametrize(
    ("mission_id", "code", "message"),
    [
        (GATEWAY, "invalid_transition", "Can't approve a mission in draft"),
        (TELESCOPE, "mission_frozen", "Can't approve an active mission"),
    ],
)
def test_only_a_pending_mission_can_be_approved(seeded_db, mission_id, code, message):
    with pytest.raises(StateConflict) as caught:
        approvals.approve(as_(seeded_db, INGRID), mission_id)
    assert (caught.value.code, caught.value.message) == (code, message)


# --- Reject and deciding twice (A3, AC-10, S6) --------------------------------------------


def test_ac10_s6_a_director_cannot_decide_the_same_round_twice(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as caught:
        approvals.approve(as_(seeded_db, MARCO), DEEP_SPACE)
    assert (caught.value.code, caught.value.message) == (
        "already_decided",
        "You've already approved this round",
    )
    with pytest.raises(StateConflict):
        approvals.reject(as_(seeded_db, MARCO), DEEP_SPACE, "Changed my mind")
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_s6_rejecting_needs_a_reason(seeded_db, reason):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as caught:
        approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, reason)
    assert caught.value.message == "Rejecting Deep Space Comms Upgrade needs a reason"
    assert snapshot(seeded_db) == before


def test_s6_rejecting_sends_the_mission_to_draft_and_clears_approvals(seeded_db):
    since = last_audit_id(seeded_db)

    after = approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, "  Budget not signed off ")

    assert after.mission.status == MissionStatus.DRAFT
    assert get_mission(as_(seeded_db, NORA), DEEP_SPACE).approvals == ()
    assert audit_since(seeded_db, since) == [
        (
            3,
            "mission.rejected",
            DEEP_SPACE,
            "pending_approval",
            "draft",
            "Budget not signed off",
            {"mission_name": "Deep Space Comms Upgrade", "round": 1},
        )
    ]
    decisions = seeded_db.execute(
        "SELECT director_id, decision, reason FROM approvals WHERE mission_id = 6 ORDER BY id"
    )
    assert [tuple(r) for r in decisions] == [
        (2, "approve", None),
        (3, "reject", "Budget not signed off"),
    ]


def test_a3_resubmitting_starts_a_fresh_round(seeded_db):
    approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, "Budget not signed off")
    approvals.submit(as_(seeded_db, NORA), DEEP_SPACE)
    assert mission_row(seeded_db, DEEP_SPACE) == ("pending_approval", 2, 2)

    # Marco's round-1 approval no longer counts, and he may decide round 2.
    assert approvals.approve(as_(seeded_db, MARCO), DEEP_SPACE).mission.status == (
        MissionStatus.PENDING_APPROVAL
    )
    assert [a.director_name for a in get_mission(as_(seeded_db, NORA), DEEP_SPACE).approvals] == [
        "Marco Bianchi"
    ]


def test_rejecting_a_draft_mission_is_an_invalid_transition(seeded_db):
    with pytest.raises(StateConflict) as caught:
        approvals.reject(as_(seeded_db, INGRID), GATEWAY, "No")
    assert caught.value.code == "invalid_transition"


def test_the_creator_cannot_reject(seeded_db):
    staff_gateway(seeded_db)
    approvals.submit(as_(seeded_db, LEE), GATEWAY)
    with pytest.raises(Forbidden) as caught:
        approvals.reject(as_(seeded_db, RUTH), GATEWAY, "No")
    assert caught.value.code == "approver_is_creator"


# --- Tenant isolation (AC-30) -------------------------------------------------------------


def test_ac30_approving_or_rejecting_another_organisations_mission_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        approvals.approve(as_(seeded_db, SAM), DEEP_SPACE)
    with pytest.raises(NotFound):
        approvals.reject(as_(seeded_db, SAM), DEEP_SPACE, "No")
    with pytest.raises(NotFound):
        approvals.submit(as_(seeded_db, PRIYA), GATEWAY)
    assert snapshot(seeded_db) == before


# --- S1 end to end, up to Active ----------------------------------------------------------


def test_s1_submit_then_marco_and_ingrid_approve(seeded_db):
    staff_gateway(seeded_db)
    approvals.submit(as_(seeded_db, LEE), GATEWAY)
    with pytest.raises(Forbidden):
        approvals.approve(as_(seeded_db, RUTH), GATEWAY)
    assert approvals.approve(as_(seeded_db, MARCO), GATEWAY).mission.status == (
        MissionStatus.PENDING_APPROVAL
    )
    assert approvals.approve(as_(seeded_db, INGRID), GATEWAY).mission.status == MissionStatus.ACTIVE
