"""M12: the assignments service. Propose, accept, decline, withdraw, remove, and the cascade a
completed or cancelled mission applies (PRD §5.1, §5.4, S1–S4, §5.7, V1; AC-4, AC-5, AC-14,
AC-15, AC-29; scenarios S1, S4, S5).

Seed ids (PRD §9): a crew profile's id equals its user's id.
Missions: Gateway 1 (Draft, Lee) · Station Reboost 3 (Nora, Gus accepted) · Telescope 5 (Active)
· Deep Space Comms 6 (Pending, Ben accepted, Marco approved) · Payload Demo 8 (Helix).
Slots: Gateway Flight Engineer 1, Mission Specialist 2, Commander 3 · Asteroid Pilot 4 ·
Station Reboost Engineer 6 · Telescope EVA Specialist 9 · Deep Space Comms Engineer 10 ·
Payload Specialist 12 (Helix).
"""

import json
from datetime import UTC, datetime

import pytest

from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import Actor
from mission_control.infra.repositories import Repos
from mission_control.services import assignments
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
MARCO = Actor(user_id=2, org_id=1, role=Role.DIRECTOR, crew_profile_id=2)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
CHEN = Actor(user_id=8, org_id=1, role=Role.CREW, crew_profile_id=8)
DANA = Actor(user_id=9, org_id=1, role=Role.CREW, crew_profile_id=9)
HANA = Actor(user_id=13, org_id=1, role=Role.CREW, crew_profile_id=13)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)
PRIYA = Actor(user_id=15, org_id=2, role=Role.LEAD, crew_profile_id=None)

ANA_ID, BEN_ID, CHEN_ID, DANA_ID, ELI_ID, FAY_ID, GUS_ID, HANA_ID = 6, 7, 8, 9, 10, 11, 12, 13
KAI_ID, LENA_ID = 16, 17
GATEWAY, ASTEROID, REBOOST, TELESCOPE, DEEP_SPACE, PAYLOAD = 1, 2, 3, 5, 6, 8
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT = 1, 2, 3, 4
REBOOST_ENGINEER, DEEP_SPACE_ENGINEER, PAYLOAD_SPECIALIST = 6, 10, 12
SYS_ENG = 3

A = AssignmentStatus


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def assignment_id(conn, mission_id, crew_id):
    return conn.execute(
        "SELECT id FROM assignments WHERE mission_id = ? AND crew_profile_id = ? ORDER BY id DESC",
        (mission_id, crew_id),
    ).fetchone()[0]


def status_of(conn, assignment):
    return conn.execute("SELECT status FROM assignments WHERE id = ?", (assignment,)).fetchone()[0]


def mission_status(conn, mission_id):
    return conn.execute("SELECT status FROM missions WHERE id = ?", (mission_id,)).fetchone()[0]


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]


def audit_since(conn, since_id):
    rows = conn.execute(
        "SELECT actor_id, event, mission_id, assignment_id, crew_profile_id, from_status,"
        " to_status, reason, data FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(*tuple(r)[:8], json.loads(r["data"])) for r in rows]


def snapshot(conn):
    """Every table an assignment use case could change, to prove a refusal changed nothing."""
    tables = ("missions", "slots", "assignments", "approvals", "audit_events")
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


def refused(fn, *args, **kwargs):
    with pytest.raises(RuleViolation) as caught:
        fn(*args, **kwargs)
    return caught.value


# --- Propose (S1, AC-14) ------------------------------------------------------------------


def test_s1_owner_proposes_an_eligible_crew_member(seeded_db):
    before = last_audit_id(seeded_db)
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert (made.mission_id, made.slot_id, made.crew_profile_id, made.status) == (
        GATEWAY,
        FLIGHT_ENGINEER,
        CHEN_ID,
        A.PROPOSED,
    )
    proposed_by = seeded_db.execute(
        "SELECT proposed_by_id FROM assignments WHERE id = ?", (made.id,)
    ).fetchone()[0]
    assert proposed_by == LEE.user_id
    assert audit_since(seeded_db, before) == [
        (
            LEE.user_id,
            Event.ASSIGNMENT_PROPOSED,
            GATEWAY,
            made.id,
            CHEN_ID,
            None,
            "proposed",
            None,
            {
                "mission_name": "Lunar Gateway Resupply",
                "slot_name": "Flight Engineer",
                "crew_name": "Chen",
            },
        )
    ]
    assert mission_status(seeded_db, GATEWAY) == "draft"


def test_s4_gus_proposal_is_refused_for_overlapping_station_reboost(seeded_db):
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, GUS_ID)
    assert error.code == "overlap"
    assert [p.code for p in error.problems] == ["overlap"]
    problem = error.problems[0]
    assert "Gus" in problem.message and "Station Reboost" in problem.message
    assert problem.refs["mission_id"] == REBOOST
    assert problem.refs["mission_name"] == "Station Reboost"
    assert snapshot(seeded_db) == before


def test_s4_fay_proposal_is_refused_for_unavailability(seeded_db):
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, COMMANDER, FAY_ID)
    assert error.code == "unavailable"
    assert [p.code for p in error.problems] == ["unavailable"]
    assert "Fay" in error.problems[0].message
    assert "Medical" not in error.message  # the reason stays private
    assert snapshot(seeded_db) == before


def test_ac14_every_ineligibility_reason_is_listed(seeded_db):
    # Hana (EVA 3, Geology 2) for Commander (Piloting >= 4, Leadership >= 3): both skills short.
    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, COMMANDER, HANA_ID)
    assert error.code == "rule_violation"
    assert [p.code for p in error.problems] == ["skill_below_minimum", "skill_below_minimum"]
    assert "Hana" in error.message
    assert "Commander" in error.message and "Lunar Gateway Resupply" in error.message


def test_s1_full_slot_is_refused(seeded_db):
    assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, ANA_ID)
    assert error.code == "slot_full"
    assert dict(error.problems[0].refs) == {"slot_id": FLIGHT_ENGINEER}
    assert "Flight Engineer" in error.message
    assert snapshot(seeded_db) == before


def test_s1_second_open_assignment_on_the_same_mission_is_refused(seeded_db):
    first = assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, ANA_ID)
    assert error.code == "already_assigned"
    assert dict(error.problems[0].refs) == {
        "assignment_id": first.id,
        "crew_profile_id": ANA_ID,
        "mission_id": GATEWAY,
    }
    assert "Ana" in error.message and "Commander" in error.message
    assert snapshot(seeded_db) == before


def test_s1_someone_who_declined_can_be_proposed_again(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assignments.decline(as_(seeded_db, CHEN), made.id)
    again = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert again.status == A.PROPOSED and again.id != made.id


def test_s1_lead_can_propose_themselves_but_must_accept(seeded_db):
    Repos(seeded_db, 1).missions.set_owner(GATEWAY, ANA.user_id)
    made = assignments.propose(as_(seeded_db, ANA), GATEWAY, COMMANDER, ANA_ID)
    assert made.status == A.PROPOSED
    accepted = assignments.accept(as_(seeded_db, ANA), made.id)
    assert accepted.status == A.ACCEPTED


def test_s2_overlapping_proposals_on_different_missions_are_allowed(seeded_db):
    # Proposals block nothing: Chen can be proposed for two overlapping missions.
    assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)
    assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert status_of(seeded_db, assignment_id(seeded_db, REBOOST, CHEN_ID)) == "proposed"
    assert status_of(seeded_db, assignment_id(seeded_db, GATEWAY, CHEN_ID)) == "proposed"


def test_ac4_proposing_on_a_pending_mission_returns_it_to_draft(seeded_db):
    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, "Backup Engineer", 1, {SYS_ENG: 3})
    before = last_audit_id(seeded_db)
    made = assignments.propose(as_(seeded_db, NORA), DEEP_SPACE, backup.id, GUS_ID)
    assert made.status == A.PROPOSED
    assert mission_status(seeded_db, DEEP_SPACE) == "draft"
    events = audit_since(seeded_db, before)
    assert [e[1] for e in events] == [Event.ASSIGNMENT_PROPOSED, Event.MISSION_RETURNED_TO_DRAFT]
    assert events[1] == (
        NORA.user_id,
        Event.MISSION_RETURNED_TO_DRAFT,
        DEEP_SPACE,
        None,
        None,
        "pending_approval",
        "draft",
        None,
        {"mission_name": "Deep Space Comms Upgrade", "cause": "assignment.proposed"},
    )


def test_ac5_proposing_on_an_active_mission_is_refused(seeded_db):
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), TELESCOPE, 9, BEN_ID)
    assert error.code == "mission_frozen"
    assert snapshot(seeded_db) == before


def test_slot_from_another_mission_is_not_found(seeded_db):
    with pytest.raises(NotFound):
        assignments.propose(as_(seeded_db, LEE), GATEWAY, PILOT, ANA_ID)


# --- Who may propose (M3, AC-7, §5.7) -----------------------------------------------------


def test_ac7_non_owner_lead_gets_not_owner(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as caught:
        assignments.propose(as_(seeded_db, NORA), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert caught.value.code == "not_owner"
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize("crew_id", [KAI_ID, 9999], ids=["other_org", "missing"])
def test_tr10_non_owner_is_refused_before_the_crew_id_is_looked_up(seeded_db, crew_id):
    """Permission comes first, so a refusal never reveals whether a crew id exists."""
    with pytest.raises(Forbidden) as caught:
        assignments.propose(as_(seeded_db, NORA), GATEWAY, FLIGHT_ENGINEER, crew_id)
    assert caught.value.code == "not_owner"


def test_owner_proposing_another_orgs_crew_gets_not_found(seeded_db):
    with pytest.raises(NotFound):
        assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, KAI_ID)


def test_m3_director_cannot_propose(seeded_db):
    with pytest.raises(Forbidden) as caught:
        assignments.propose(as_(seeded_db, RUTH), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert caught.value.code == "role_forbidden"


def test_m3_crew_cannot_propose_on_a_mission_they_are_on(seeded_db):
    with pytest.raises(Forbidden) as caught:
        assignments.propose(as_(seeded_db, BEN), DEEP_SPACE, DEEP_SPACE_ENGINEER, BEN_ID)
    assert caught.value.code == "role_forbidden"


def test_tr10_crew_proposing_on_a_mission_they_are_not_on_gets_not_found(seeded_db):
    with pytest.raises(NotFound):
        assignments.propose(as_(seeded_db, BEN), GATEWAY, FLIGHT_ENGINEER, BEN_ID)


# --- Accept (S2, AC-15) -------------------------------------------------------------------


def test_s1_crew_accepts_their_proposal(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    before = last_audit_id(seeded_db)
    accepted = assignments.accept(as_(seeded_db, CHEN), made.id)
    assert accepted.status == A.ACCEPTED
    assert audit_since(seeded_db, before) == [
        (
            CHEN.user_id,
            Event.ASSIGNMENT_ACCEPTED,
            GATEWAY,
            made.id,
            CHEN_ID,
            "proposed",
            "accepted",
            None,
            {
                "mission_name": "Lunar Gateway Resupply",
                "slot_name": "Flight Engineer",
                "crew_name": "Chen",
            },
        )
    ]


def test_ac15_chens_second_acceptance_names_station_reboost(seeded_db):
    on_reboost = assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)
    on_gateway = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assignments.accept(as_(seeded_db, CHEN), on_reboost.id)

    before = snapshot(seeded_db)
    error = refused(assignments.accept, as_(seeded_db, CHEN), on_gateway.id)
    assert error.code == "overlap"
    assert error.problems[0].refs["mission_name"] == "Station Reboost"
    assert "Station Reboost" in error.message
    assert snapshot(seeded_db) == before
    assert status_of(seeded_db, on_gateway.id) == "proposed"


def test_s2_acceptance_rechecks_skills(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    Repos(seeded_db, 1).crew.set_skill(CHEN_ID, SYS_ENG, 2, updated_by=LEE.user_id)
    error = refused(assignments.accept, as_(seeded_db, CHEN), made.id)
    assert error.code == "skill_below_minimum"
    assert "Chen" in error.message


def test_s2_accepting_twice_is_refused(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assignments.accept(as_(seeded_db, CHEN), made.id)
    error = refused(assignments.accept, as_(seeded_db, CHEN), made.id)
    assert error.code == "invalid_transition"


def test_s2_accepting_on_a_pending_mission_is_refused(seeded_db):
    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, "Backup Engineer", 1, {SYS_ENG: 3})
    repos = Repos(seeded_db, 1)
    made = repos.assignments.create(DEEP_SPACE, backup.id, GUS_ID, proposed_by_id=NORA.user_id)
    gus = Actor(user_id=GUS_ID, org_id=1, role=Role.CREW, crew_profile_id=GUS_ID)
    before = snapshot(seeded_db)
    error = refused(assignments.accept, as_(seeded_db, gus), made.id)
    assert error.code == "invalid_transition"
    assert snapshot(seeded_db) == before


def test_tr10_another_crew_members_assignment_is_not_found(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        assignments.accept(as_(seeded_db, DANA), made.id)
    with pytest.raises(NotFound):
        assignments.withdraw(as_(seeded_db, BEN), assignment_id(seeded_db, TELESCOPE, HANA_ID), "x")
    assert snapshot(seeded_db) == before


def test_s4_lead_cannot_accept_for_someone_else(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    with pytest.raises(Forbidden) as caught:
        assignments.accept(as_(seeded_db, LEE), made.id)
    assert caught.value.code == "not_owner"
    with pytest.raises(Forbidden) as caught:
        assignments.accept(as_(seeded_db, RUTH), made.id)
    assert caught.value.code == "not_owner"


# --- Decline (S3) -------------------------------------------------------------------------


def test_s3_decline_with_a_reason_stores_it(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    before = last_audit_id(seeded_db)
    declined = assignments.decline(as_(seeded_db, CHEN), made.id, "  Training that week  ")
    assert (declined.status, declined.reason) == (A.DECLINED, "Training that week")
    events = audit_since(seeded_db, before)
    assert [(e[1], e[5], e[6], e[7]) for e in events] == [
        (Event.ASSIGNMENT_DECLINED, "proposed", "declined", "Training that week")
    ]


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_s3_decline_without_a_reason(seeded_db, reason):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, DANA_ID)
    declined = assignments.decline(as_(seeded_db, DANA), made.id, reason)
    assert (declined.status, declined.reason) == (A.DECLINED, None)


def test_s3_declining_an_accepted_assignment_is_refused(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assignments.accept(as_(seeded_db, CHEN), made.id)
    error = refused(assignments.decline, as_(seeded_db, CHEN), made.id)
    assert error.code == "invalid_transition"


# --- Withdraw (S3, S5, AC-4, AC-5) --------------------------------------------------------


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_s5_withdrawal_without_reason_is_refused(seeded_db, reason):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput):
        assignments.withdraw(
            as_(seeded_db, BEN), assignment_id(seeded_db, DEEP_SPACE, BEN_ID), reason
        )
    assert snapshot(seeded_db) == before
    assert mission_status(seeded_db, DEEP_SPACE) == "pending_approval"


def test_s5_withdrawal_returns_pending_mission_to_draft_and_clears_approvals(seeded_db):
    ben_on_comms = assignment_id(seeded_db, DEEP_SPACE, BEN_ID)
    before = last_audit_id(seeded_db)
    withdrawn = assignments.withdraw(as_(seeded_db, BEN), ben_on_comms, " Family emergency ")
    assert (withdrawn.status, withdrawn.reason) == (A.WITHDRAWN, "Family emergency")
    assert mission_status(seeded_db, DEEP_SPACE) == "draft"
    # Marco's approval stays on record, but only a Pending mission's round counts, and the next
    # submission opens a new round.
    assert [e[1:] for e in audit_since(seeded_db, before)] == [
        (
            Event.ASSIGNMENT_WITHDRAWN,
            DEEP_SPACE,
            ben_on_comms,
            BEN_ID,
            "accepted",
            "withdrawn",
            "Family emergency",
            {
                "mission_name": "Deep Space Comms Upgrade",
                "slot_name": "Engineer",
                "crew_name": "Ben",
            },
        ),
        (
            Event.MISSION_RETURNED_TO_DRAFT,
            DEEP_SPACE,
            None,
            None,
            "pending_approval",
            "draft",
            None,
            {"mission_name": "Deep Space Comms Upgrade", "cause": "assignment.withdrawn"},
        ),
    ]


def test_s5_withdrawing_from_an_active_mission_is_refused(seeded_db):
    before = snapshot(seeded_db)
    error = refused(
        assignments.withdraw,
        as_(seeded_db, HANA),
        assignment_id(seeded_db, TELESCOPE, HANA_ID),
        "Injured",
    )
    assert error.code == "mission_frozen"
    assert "active" in error.message
    assert snapshot(seeded_db) == before


def test_s3_withdrawing_from_a_draft_mission_keeps_it_draft(seeded_db):
    gus = Actor(user_id=GUS_ID, org_id=1, role=Role.CREW, crew_profile_id=GUS_ID)
    withdrawn = assignments.withdraw(
        as_(seeded_db, gus), assignment_id(seeded_db, REBOOST, GUS_ID), "Reassigned"
    )
    assert withdrawn.status == A.WITHDRAWN
    assert mission_status(seeded_db, REBOOST) == "draft"


def test_s3_withdrawing_a_proposal_is_refused(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    error = refused(assignments.withdraw, as_(seeded_db, CHEN), made.id, "Changed my mind")
    assert error.code == "invalid_transition"


# --- Remove (M3, AC-4, AC-5) --------------------------------------------------------------


def test_m3_owner_retracts_a_proposal(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    before = last_audit_id(seeded_db)
    removed = assignments.remove(as_(seeded_db, LEE), made.id)
    assert removed.status == A.REMOVED
    assert [(e[1], e[5], e[6]) for e in audit_since(seeded_db, before)] == [
        (Event.ASSIGNMENT_REMOVED, "proposed", "removed")
    ]


def test_ac4_owner_removes_accepted_crew_from_pending_mission_which_returns_to_draft(seeded_db):
    ben_on_comms = assignment_id(seeded_db, DEEP_SPACE, BEN_ID)
    before = last_audit_id(seeded_db)
    removed = assignments.remove(as_(seeded_db, NORA), ben_on_comms)
    assert removed.status == A.REMOVED
    assert mission_status(seeded_db, DEEP_SPACE) == "draft"
    events = audit_since(seeded_db, before)
    assert [(e[1], e[5], e[6]) for e in events] == [
        (Event.ASSIGNMENT_REMOVED, "accepted", "removed"),
        (Event.MISSION_RETURNED_TO_DRAFT, "pending_approval", "draft"),
    ]
    assert events[1][8]["cause"] == "assignment.removed"


def test_ac5_removing_from_an_active_mission_is_refused(seeded_db):
    before = snapshot(seeded_db)
    error = refused(
        assignments.remove, as_(seeded_db, LEE), assignment_id(seeded_db, TELESCOPE, HANA_ID)
    )
    assert error.code == "mission_frozen"
    assert snapshot(seeded_db) == before


def test_m3_non_owner_lead_cannot_remove(seeded_db):
    with pytest.raises(Forbidden) as caught:
        assignments.remove(as_(seeded_db, LEE), assignment_id(seeded_db, DEEP_SPACE, BEN_ID))
    assert caught.value.code == "not_owner"


def test_m3_crew_cannot_remove_their_own_assignment(seeded_db):
    with pytest.raises(Forbidden) as caught:
        assignments.remove(as_(seeded_db, BEN), assignment_id(seeded_db, DEEP_SPACE, BEN_ID))
    assert caught.value.code == "role_forbidden"


def test_removing_a_declined_assignment_is_refused(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assignments.decline(as_(seeded_db, CHEN), made.id)
    error = refused(assignments.remove, as_(seeded_db, LEE), made.id)
    assert error.code == "invalid_transition"


# --- My assignments (GET /assignments, mc assignments list [--pending]) ------------------


def test_my_assignments_lists_the_callers_own_newest_first(seeded_db):
    assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, BEN_ID)
    mine = assignments.my_assignments(as_(seeded_db, BEN))
    assert [(m.mission_name, m.slot_name, m.status) for m in mine] == [
        ("Deep Space Comms Upgrade", "Engineer", A.ACCEPTED),
        ("Lunar Gateway Resupply", "Mission Specialist", A.PROPOSED),
    ]


def test_my_assignments_pending_shows_only_proposals_awaiting_a_reply(seeded_db):
    assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, BEN_ID)
    pending = assignments.my_assignments(as_(seeded_db, BEN), pending=True)
    assert [(p.mission_name, p.status) for p in pending] == [("Lunar Gateway Resupply", A.PROPOSED)]


def test_my_assignments_is_empty_without_a_crew_profile(seeded_db):
    assert assignments.my_assignments(as_(seeded_db, RUTH)) == []


def test_ac27_my_assignments_never_shows_another_organisations(seeded_db):
    assert assignments.my_assignments(as_(seeded_db, PRIYA)) == []
    assert all(m.mission_id != PAYLOAD for m in assignments.my_assignments(as_(seeded_db, BEN)))


# --- Tenant isolation (T2, AC-27, AC-29) --------------------------------------------------


def both_orgs(conn):
    return snapshot(conn)


@pytest.mark.parametrize(
    "actor, call",
    [
        (LEE, lambda c: assignments.propose(c, PAYLOAD, PAYLOAD_SPECIALIST, CHEN_ID)),
        (LEE, lambda c: assignments.propose(c, GATEWAY, PAYLOAD_SPECIALIST, CHEN_ID)),
        (LEE, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, KAI_ID)),
        (LEE, lambda c: assignments.remove(c, 9)),  # Lena's Helix assignment
        (BEN, lambda c: assignments.accept(c, 9)),
        (BEN, lambda c: assignments.decline(c, 9)),
        (BEN, lambda c: assignments.withdraw(c, 9, "Not mine")),
        (SAM, lambda c: assignments.remove(c, 7)),  # Ben's Aurora assignment
        (PRIYA, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, CHEN_ID)),
        (PRIYA, lambda c: assignments.propose(c, PAYLOAD, PAYLOAD_SPECIALIST, CHEN_ID)),
        (LEE, lambda c: assignments.accept(c, 999)),
    ],
)
def test_ac29_other_organisations_ids_are_not_found_and_nothing_changes(seeded_db, actor, call):
    before = both_orgs(seeded_db)
    with pytest.raises(NotFound):
        call(as_(seeded_db, actor))
    assert both_orgs(seeded_db) == before


# --- Every refusal writes nothing (§5 cross-cutting: refused actions write nothing) -------


def _refusals():
    return [
        ("overlap", LEE, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, GUS_ID)),
        ("unavailable", LEE, lambda c: assignments.propose(c, GATEWAY, COMMANDER, FAY_ID)),
        ("frozen propose", LEE, lambda c: assignments.propose(c, TELESCOPE, 9, BEN_ID)),
        ("not owner", NORA, lambda c: assignments.propose(c, GATEWAY, COMMANDER, ANA_ID)),
        ("blank reason", BEN, lambda c: assignments.withdraw(c, 7, " ")),
        ("frozen withdraw", HANA, lambda c: assignments.withdraw(c, 6, "Injured")),
        ("frozen remove", LEE, lambda c: assignments.remove(c, 6)),
        ("accept accepted", BEN, lambda c: assignments.accept(c, 7)),
        ("decline accepted", BEN, lambda c: assignments.decline(c, 7)),
        ("remove completed", LEE, lambda c: assignments.remove(c, 8)),
        ("not mine", CHEN, lambda c: assignments.withdraw(c, 7, "x")),
    ]


@pytest.mark.parametrize("name, actor, call", _refusals(), ids=[r[0] for r in _refusals()])
def test_every_refusal_leaves_the_tables_unchanged(seeded_db, name, actor, call):
    before = snapshot(seeded_db)
    with pytest.raises((RuleViolation, Forbidden, NotFound, InvalidInput)):
        call(as_(seeded_db, actor))
    assert snapshot(seeded_db) == before


# --- Cascades when a mission completes or is cancelled (§5.4) -----------------------------


def test_m4_completing_a_mission_completes_accepted_assignments(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = last_audit_id(seeded_db)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert sorted(a.crew_profile_id for a in changed) == [CHEN_ID, DANA_ID, ELI_ID, HANA_ID]
    assert {a.status for a in changed} == {A.COMPLETED}
    events = audit_since(seeded_db, before)
    assert [(e[1], e[5], e[6]) for e in events] == [
        (Event.ASSIGNMENT_COMPLETED, "accepted", "completed")
    ] * 4
    assert events[0][8] == {
        "mission_name": "Orbital Telescope Service",
        "slot_name": "Engineer",
        "crew_name": "Chen",
    }


def test_m4_cancelling_a_mission_cancels_open_assignments_only(seeded_db):
    proposed = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    accepted = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, DANA_ID)
    assignments.accept(as_(seeded_db, DANA), accepted.id)
    declined = assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)
    assignments.decline(as_(seeded_db, ANA), declined.id, "Busy")

    ctx = as_(seeded_db, RUTH)
    mission = Repos(seeded_db, 1).missions.get(GATEWAY)
    before = last_audit_id(seeded_db)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.CANCELLED)
    assert [(a.id, a.status) for a in changed] == [
        (proposed.id, A.CANCELLED),
        (accepted.id, A.CANCELLED),
    ]
    assert status_of(seeded_db, declined.id) == "declined"
    assert [(e[0], e[1], e[5], e[6]) for e in audit_since(seeded_db, before)] == [
        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, "proposed", "cancelled"),
        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, "accepted", "cancelled"),
    ]


def test_m4_completing_leaves_proposals_and_closed_assignments_alone(seeded_db):
    # Not reachable through the lifecycle (Active missions have only accepted crew), but the
    # cascade must not touch anything that isn't accepted.
    repos = Repos(seeded_db, 1)
    mission = repos.missions.get(REBOOST)
    proposal = repos.assignments.create(REBOOST, REBOOST_ENGINEER, CHEN_ID, proposed_by_id=5)
    ctx = as_(seeded_db, NORA)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert [a.crew_profile_id for a in changed] == [GUS_ID]
    assert status_of(seeded_db, proposal.id) == "proposed"


def test_cascade_runs_only_inside_the_callers_write(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = snapshot(seeded_db)
    with pytest.raises(RuntimeError):
        assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert snapshot(seeded_db) == before


def test_cascade_rolls_back_with_the_callers_transaction(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = snapshot(seeded_db)
    with pytest.raises(RuntimeError, match="caller failed"):
        with ctx.write():
            assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
            raise RuntimeError("caller failed")
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    "status", [MissionStatus.DRAFT, MissionStatus.PENDING_APPROVAL, MissionStatus.ACTIVE]
)
def test_cascade_needs_a_final_status(seeded_db, status):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    with ctx.write(), pytest.raises(ValueError):
        assignments.cascade_mission_end(ctx, mission, status)


# --- Scenarios end to end -----------------------------------------------------------------


def test_s4_scenario(seeded_db):
    with pytest.raises(RuleViolation, match="Station Reboost"):
        assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, GUS_ID)
    with pytest.raises(RuleViolation) as fay:
        assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, FAY_ID)
    assert fay.value.code == "unavailable"
    on_reboost = assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)
    on_gateway = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert assignments.accept(as_(seeded_db, CHEN), on_reboost.id).status == A.ACCEPTED
    with pytest.raises(RuleViolation) as second:
        assignments.accept(as_(seeded_db, CHEN), on_gateway.id)
    assert second.value.problems[0].refs["mission_name"] == "Station Reboost"


def test_s1_propose_and_accept_steps(seeded_db):
    picks = [
        (COMMANDER, ANA, ANA_ID),
        (FLIGHT_ENGINEER, CHEN, CHEN_ID),
        (SPECIALIST, DANA, DANA_ID),
    ]
    made = [
        (actor, assignments.propose(as_(seeded_db, LEE), GATEWAY, slot, crew_id))
        for slot, actor, crew_id in picks
    ]
    for actor, assignment in made:
        assert assignments.accept(as_(seeded_db, actor), assignment.id).status == A.ACCEPTED
    open_places = [s.open_places for s in Repos(seeded_db, 1).facts.slot_specs(GATEWAY)]
    assert open_places == [0, 0, 0]
    assert mission_status(seeded_db, GATEWAY) == "draft"
