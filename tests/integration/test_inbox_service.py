"""The inbox: what is waiting on the caller to act, computed from current data (PRD §4 workflow 1;
design §7 Inbox).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Marco 2 · Ingrid 3 ·
Lee 4 · Nora 5 · Ana 6 · Ben 7 · Chen 8 · Dana 9 · Sam 14 (Helix) · Priya 15 (Helix).
Missions: Gateway 1 (Draft, Lee, created by Ruth) · Asteroid 2 (Draft, Nora) · Station Reboost
3 (Draft, Nora, Gus accepted, 1 open place) · Medical Study 4 (Draft, Nora, created by Ruth,
Marco accepted) · Telescope 5 (Active, Lee) · Deep Space Comms 6 (Pending, Nora, Ben accepted,
Marco approved) · Mars 7 (Completed, Lee) · Payload Demo 8 (Helix, Draft, Priya).
"""

from datetime import UTC, datetime

from mission_control.domain.enums import AssignmentStatus, Role
from mission_control.domain.permissions import Actor
from mission_control.services import approvals, assignments, inbox, matching
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
PRIYA = Actor(user_id=15, org_id=2, role=Role.LEAD, crew_profile_id=None)

GATEWAY, MEDICAL, DEEP_SPACE = 1, 4, 6
SPECIALIST = 2


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def box(conn, actor):
    return inbox.inbox(as_(conn, actor))


def missions_of(conn, actor):
    """[(mission name, [(slot, open places)], unanswered proposals, ready to submit)]."""
    return [
        (m.mission_name, [(u.slot_name, u.open_places) for u in m.unfilled], m.unanswered, m.ready)
        for m in box(conn, actor).missions
    ]


def approvals_of(conn, actor):
    return [(a.mission_name, a.approvals, a.required) for a in box(conn, actor).approvals]


# --- Proposals waiting on me -------------------------------------------------------------


def test_crew_see_proposals_waiting_for_their_reply(seeded_db):
    assert box(seeded_db, BEN).proposals == ()  # his Deep Space assignment is already accepted
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, 7)

    items = box(seeded_db, BEN).proposals
    assert [(p.assignment_id, p.mission_name, p.slot_name, p.status) for p in items] == [
        (made.id, "Lunar Gateway Resupply", "Mission Specialist", AssignmentStatus.PROPOSED)
    ]


def test_a_proposal_disappears_once_answered(seeded_db):
    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, 7)
    assignments.decline(as_(seeded_db, BEN), made.id)
    assert box(seeded_db, BEN).proposals == ()


def test_a_lead_with_a_crew_profile_sees_their_proposals_too(seeded_db):
    matching.apply(as_(seeded_db, LEE), GATEWAY)
    assert [p.slot_name for p in box(seeded_db, ANA).proposals] == ["Commander"]


def test_someone_with_nothing_waiting_has_an_empty_inbox(seeded_db):
    empty = box(seeded_db, CHEN)
    assert (empty.proposals, empty.approvals, empty.missions) == ((), (), ())


# --- Approvals waiting on me (Directors) --------------------------------------------------


def test_directors_see_pending_missions_they_can_still_approve(seeded_db):
    assert approvals_of(seeded_db, INGRID) == [("Deep Space Comms Upgrade", 1, 2)]
    assert approvals_of(seeded_db, RUTH) == [("Deep Space Comms Upgrade", 1, 2)]


def test_a_director_who_already_approved_sees_nothing_to_do(seeded_db):
    assert approvals_of(seeded_db, MARCO) == []


def test_the_creator_is_not_asked_to_approve(seeded_db):
    matching.apply(as_(seeded_db, LEE), GATEWAY)
    for actor in (ANA, CHEN, DANA):
        (proposal,) = box(seeded_db, actor).proposals
        assignments.accept(as_(seeded_db, actor), proposal.assignment_id)
    approvals.submit(as_(seeded_db, LEE), GATEWAY)

    assert "Lunar Gateway Resupply" not in [a[0] for a in approvals_of(seeded_db, RUTH)]
    assert ("Lunar Gateway Resupply", 0, 2) in approvals_of(seeded_db, MARCO)


def test_a_director_on_the_roster_is_not_asked_to_approve(seeded_db):
    seeded_db.execute("UPDATE organisations SET required_approvals = 1 WHERE id = 1")
    approvals.submit(as_(seeded_db, NORA), MEDICAL)
    assert "Lunar Surface Medical Study" not in [a[0] for a in approvals_of(seeded_db, MARCO)]
    assert ("Lunar Surface Medical Study", 0, 1) in approvals_of(seeded_db, INGRID)


def test_an_approved_mission_leaves_every_inbox(seeded_db):
    approvals.approve(as_(seeded_db, INGRID), DEEP_SPACE)
    assert approvals_of(seeded_db, RUTH) == []


def test_leads_and_crew_never_see_approvals(seeded_db):
    assert box(seeded_db, LEE).approvals == ()
    assert box(seeded_db, BEN).approvals == ()


# --- My draft missions (owning Lead) ------------------------------------------------------


def test_owners_see_their_draft_missions_and_what_each_is_waiting_on(seeded_db):
    assert missions_of(seeded_db, NORA) == [
        ("Station Reboost", [("Engineer", 1)], 0, False),
        ("Asteroid Survey", [("Pilot", 1), ("Geologist", 1)], 0, False),
        ("Lunar Surface Medical Study", [], 0, True),
    ]


def test_active_finished_and_pending_missions_are_not_listed(seeded_db):
    # Lee also owns Telescope (Active) and Mars (Completed); Nora owns Deep Space (Pending).
    assert [m[0] for m in missions_of(seeded_db, LEE)] == ["Lunar Gateway Resupply"]
    assert "Deep Space Comms Upgrade" not in [m[0] for m in missions_of(seeded_db, NORA)]


def test_a_mission_moves_from_unfilled_to_unanswered_to_ready_to_gone(seeded_db):
    assert missions_of(seeded_db, LEE) == [
        (
            "Lunar Gateway Resupply",
            [("Flight Engineer", 1), ("Mission Specialist", 1), ("Commander", 1)],
            0,
            False,
        )
    ]
    matching.apply(as_(seeded_db, LEE), GATEWAY)
    assert missions_of(seeded_db, LEE) == [("Lunar Gateway Resupply", [], 3, False)]

    for actor in (ANA, CHEN, DANA):
        (proposal,) = box(seeded_db, actor).proposals
        assignments.accept(as_(seeded_db, actor), proposal.assignment_id)
    assert missions_of(seeded_db, LEE) == [("Lunar Gateway Resupply", [], 0, True)]

    approvals.submit(as_(seeded_db, LEE), GATEWAY)
    assert missions_of(seeded_db, LEE) == []


def test_a_rejected_mission_comes_back_to_its_owner(seeded_db):
    approvals.reject(as_(seeded_db, INGRID), DEEP_SPACE, "Budget not signed off")
    assert ("Deep Space Comms Upgrade", [], 0, True) in missions_of(seeded_db, NORA)


def test_crew_and_directors_own_no_missions(seeded_db):
    assert box(seeded_db, BEN).missions == ()
    assert box(seeded_db, RUTH).missions == ()


# --- Tenant isolation ----------------------------------------------------------------------


def test_an_inbox_only_ever_shows_the_callers_organisation(seeded_db):
    helix = box(seeded_db, SAM)
    assert (helix.proposals, helix.approvals, helix.missions) == ((), (), ())
    assert [m[0] for m in missions_of(seeded_db, PRIYA)] == ["Payload Demo 1"]
