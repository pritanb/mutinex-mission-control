"""M11: the missions service. Viewing, creating and editing missions and their slots, and
transferring ownership (PRD M1–M3, M5, M7, §5.7, AC-4, AC-5, AC-7, AC-24, AC-27, AC-29)."""

import json
from datetime import UTC, date, datetime

import pytest

from builders import make_assignment
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import missions
from mission_control.services.context import ServiceContext
from mission_control.services.missions import SlotInput

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(1, 1, Role.DIRECTOR, None)
MARCO = Actor(2, 1, Role.DIRECTOR, 2)
INGRID = Actor(3, 1, Role.DIRECTOR, None)
LEE = Actor(4, 1, Role.LEAD, None)
NORA = Actor(5, 1, Role.LEAD, None)
ANA = Actor(6, 1, Role.LEAD, 6)
BEN = Actor(7, 1, Role.CREW, 7)
CHEN = Actor(8, 1, Role.CREW, 8)
SAM = Actor(14, 2, Role.DIRECTOR, None)
PRIYA = Actor(15, 2, Role.LEAD, None)

# Seeded missions
GATEWAY, ASTEROID, REBOOST, MEDICAL, TELESCOPE, COMMS, MARS, PAYLOAD = range(1, 9)
# Seeded slots
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT, GEOLOGIST, REBOOST_ENGINEER = range(1, 7)
TELESCOPE_ENGINEER, COMMS_ENGINEER = 8, 10
# Aurora skills
PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, FLIGHT_MEDICINE = range(1, 7)
HELIX_PILOTING = 7


def svc(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def d(iso):
    return date.fromisoformat(iso)


def snapshot(conn):
    """Everything a missions use case can change."""
    return {
        table: [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
        for table in ("missions", "slots", "slot_requirements", "audit_events", "approvals")
    }


def events(conn, mission_id):
    rows = conn.execute(
        "SELECT actor_id, event, from_status, to_status, data FROM audit_events"
        " WHERE mission_id = ? ORDER BY id",
        (mission_id,),
    ).fetchall()
    return [(r[0], r[1], r[2], r[3], json.loads(r[4])) for r in rows]


def last_events(conn, mission_id, n):
    return events(conn, mission_id)[-n:]


def status_of(conn, mission_id):
    return conn.execute("SELECT status FROM missions WHERE id = ?", (mission_id,)).fetchone()[0]


def propose_chen_for_reboost(conn):
    """Chen proposed as Station Reboost's second Engineer (Gus is already accepted)."""
    return make_assignment(conn, 1, REBOOST, REBOOST_ENGINEER, 8, 5, status="proposed")


def engineer(name="Engineer", headcount=1, **requirements):
    return SlotInput(name, headcount, requirements or {SYS_ENG: 3})


# --- View (§5.7, TR-10) -------------------------------------------------------------------


def test_s57_directors_and_leads_list_every_mission_in_their_org(seeded_db):
    for actor in (RUTH, LEE):
        assert [m.id for m in missions.list_missions(svc(seeded_db, actor))] == [
            MARS,
            TELESCOPE,
            REBOOST,
            GATEWAY,
            ASTEROID,
            MEDICAL,
            COMMS,
        ]


def test_ac24_crew_mission_list_shows_only_missions_they_are_on(seeded_db):
    assert [m.id for m in missions.list_missions(svc(seeded_db, BEN))] == [COMMS]
    assert [m.id for m in missions.list_missions(svc(seeded_db, CHEN))] == [MARS, TELESCOPE]


def test_ac28_mission_list_contains_only_the_callers_org(seeded_db):
    assert [m.id for m in missions.list_missions(svc(seeded_db, PRIYA))] == [PAYLOAD]


def test_s57_view_has_slots_requirements_assignments_and_the_current_rounds_approvals(seeded_db):
    view = missions.get_mission(svc(seeded_db, RUTH), COMMS)
    assert (view.mission.name, view.mission.status) == (
        "Deep Space Comms Upgrade",
        MissionStatus.PENDING_APPROVAL,
    )
    assert (view.owner_name, view.created_by_name) == ("Nora Quinn", "Nora Quinn")
    [slot] = view.slots
    assert (slot.id, slot.name, slot.headcount, slot.open_places) == (
        COMMS_ENGINEER,
        "Engineer",
        1,
        0,
    )
    assert [(r.skill_name, r.min_level) for r in slot.requirements] == [("Systems Engineering", 3)]
    assert [(a.crew_name, a.slot_name, a.status) for a in view.assignments] == [
        ("Ben", "Engineer", AssignmentStatus.ACCEPTED)
    ]
    assert [(a.director_name, a.decision) for a in view.approvals] == [("Marco Bianchi", "approve")]


def test_s57_view_of_a_draft_mission_lists_open_places_and_no_approvals(seeded_db):
    view = missions.get_mission(svc(seeded_db, LEE), REBOOST)
    assert [(s.name, s.headcount, s.open_places) for s in view.slots] == [("Engineer", 2, 1)]
    assert view.approvals == ()
    assert (view.owner_name, view.created_by_name) == ("Nora Quinn", "Nora Quinn")


def test_ac24_crew_on_a_mission_see_their_teammates_names_and_slots(seeded_db):
    view = missions.get_mission(svc(seeded_db, CHEN), TELESCOPE)
    assert [(a.crew_name, a.slot_name) for a in view.assignments] == [
        ("Chen", "Engineer"),
        ("Dana", "EVA Specialist"),
        ("Eli", "EVA Specialist"),
        ("Hana", "EVA Specialist"),
    ]


def test_tr10_crew_viewing_a_mission_they_are_not_on_get_not_found(seeded_db):
    with pytest.raises(NotFound) as err:
        missions.get_mission(svc(seeded_db, BEN), GATEWAY)
    assert err.value.message == "Mission not found"


def test_v2_a_former_assignee_can_no_longer_view_the_mission(seeded_db):
    seeded_db.execute(
        "UPDATE assignments SET status = 'withdrawn', reason = 'Family' WHERE mission_id = ?",
        (COMMS,),
    )
    with pytest.raises(NotFound):
        missions.get_mission(svc(seeded_db, BEN), COMMS)


@pytest.mark.parametrize("mission_id", [PAYLOAD, 999])
def test_ac27_another_orgs_mission_looks_the_same_as_a_missing_one(seeded_db, mission_id):
    with pytest.raises(NotFound) as err:
        missions.get_mission(svc(seeded_db, LEE), mission_id)
    assert err.value.message == "Mission not found"


# --- Create (M1, M2) ----------------------------------------------------------------------


def test_m1_a_lead_creates_a_draft_mission_for_themselves(seeded_db):
    view = missions.create_mission(
        svc(seeded_db, LEE),
        name="Lunar Relay",
        start=d("2027-07-01"),
        end=d("2027-07-04"),
        slots=[
            SlotInput("Commander", 1, {PILOTING: 4, LEADERSHIP: 3}),
            SlotInput("Engineer", 2, {SYS_ENG: 3}),
        ],
    )
    m = view.mission
    assert (m.name, m.status, m.owner_id, m.created_by_id) == (
        "Lunar Relay",
        MissionStatus.DRAFT,
        LEE.user_id,
        LEE.user_id,
    )
    assert (m.window.start, m.window.end) == (d("2027-07-01"), d("2027-07-04"))
    assert [(s.position, s.name, s.headcount, s.open_places) for s in view.slots] == [
        (1, "Commander", 1, 1),
        (2, "Engineer", 2, 2),
    ]
    assert [(r.skill_name, r.min_level) for r in view.slots[0].requirements] == [
        ("Piloting", 4),
        ("Leadership", 3),
    ]
    [(actor, event, _, to_status, data)] = events(seeded_db, m.id)
    assert (actor, event, to_status) == (LEE.user_id, "mission.created", "draft")
    assert data["mission_name"] == "Lunar Relay"
    assert data["owner_name"] == "Lee Park"
    assert [s["slot_name"] for s in data["slots"]] == ["Commander", "Engineer"]


def test_m1_a_director_creates_a_mission_for_a_lead_and_is_recorded_as_its_creator(seeded_db):
    view = missions.create_mission(
        svc(seeded_db, RUTH),
        name="Lunar Relay",
        start=d("2027-07-01"),
        end=d("2027-07-04"),
        slots=[engineer()],
        owner_id=NORA.user_id,
    )
    assert (view.mission.owner_id, view.mission.created_by_id) == (NORA.user_id, RUTH.user_id)
    assert (view.owner_name, view.created_by_name) == ("Nora Quinn", "Ruth Adeyemi")
    [(actor, event, *_)] = events(seeded_db, view.mission.id)
    assert (actor, event) == (RUTH.user_id, "mission.created")


def test_m1_a_lead_cannot_create_a_mission_for_another_lead(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        missions.create_mission(
            svc(seeded_db, LEE),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
            owner_id=NORA.user_id,
        )
    assert err.value.code == "not_owner"
    assert snapshot(seeded_db) == before


def test_m1_crew_cannot_create_missions(seeded_db):
    with pytest.raises(Forbidden) as err:
        missions.create_mission(
            svc(seeded_db, BEN),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
        )
    assert (err.value.code, err.value.message) == ("role_forbidden", "Crew can't create missions")


def deactivate(conn, user_id):
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))


@pytest.mark.parametrize(
    ("owner_id", "message"),
    [
        (7, "Ben Ito can't own a mission: only Mission Leads can"),
        (3, "Ingrid Holm can't own a mission: only Mission Leads can"),
        (6, "Ana Okafor can't own a mission because they're deactivated"),
    ],
)
def test_m1_only_an_active_lead_can_own_a_new_mission(seeded_db, owner_id, message):
    deactivate(seeded_db, 6)
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.create_mission(
            svc(seeded_db, RUTH),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
            owner_id=owner_id,
        )
    assert err.value.code == "rule_violation"
    [problem] = err.value.problems
    assert (problem.code, problem.message, dict(problem.refs)) == (
        "owner_not_active_lead",
        message,
        {"user_id": owner_id},
    )
    assert snapshot(seeded_db) == before


def test_m1_a_director_must_name_the_lead_who_will_own_the_mission(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as err:
        missions.create_mission(
            svc(seeded_db, RUTH),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
        )
    assert (err.value.code, err.value.message) == (
        "validation_error",
        "Name the Lead who will own the mission",
    )
    assert [p.message for p in err.value.problems] == ["Name the Lead who will own the mission"]
    assert snapshot(seeded_db) == before


def test_m1_a_missing_owner_is_listed_with_the_directors_other_mistakes(seeded_db):
    with pytest.raises(InvalidInput) as err:
        missions.create_mission(
            svc(seeded_db, RUTH),
            name=" ",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
        )
    assert err.value.message == "Some values aren't valid"
    assert [p.message for p in err.value.problems] == [
        "The mission needs a name",
        "Name the Lead who will own the mission",
    ]


@pytest.mark.parametrize(
    ("actor", "code", "message"),
    [
        (BEN, "role_forbidden", "Crew can't create missions"),
        (LEE, "not_owner", "Leads can only create missions they own"),
    ],
)
def test_tr10_a_refused_creator_gets_the_same_403_whether_or_not_the_owner_exists(
    seeded_db, actor, code, message
):
    """Permission is checked before the named owner is looked up, so a refusal never reveals
    whether that user exists."""
    for owner_id in (999, INGRID.user_id, PRIYA.user_id):
        with pytest.raises(Forbidden) as err:
            missions.create_mission(
                svc(seeded_db, actor),
                name="Lunar Relay",
                start=d("2027-07-01"),
                end=d("2027-07-04"),
                slots=[engineer()],
                owner_id=owner_id,
            )
        assert (err.value.code, err.value.message) == (code, message)


def test_tr10_crew_naming_an_unknown_skill_are_refused_before_it_is_looked_up(seeded_db):
    with pytest.raises(Forbidden) as err:
        missions.create_mission(
            svc(seeded_db, BEN),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[SlotInput("Pilot", 1, {999: 3})],
        )
    assert err.value.code == "role_forbidden"


def test_ac29_an_owner_from_another_org_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        missions.create_mission(
            svc(seeded_db, RUTH),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[engineer()],
            owner_id=PRIYA.user_id,
        )
    assert err.value.message == "User not found"
    assert snapshot(seeded_db) == before


def test_ac29_a_skill_from_another_orgs_catalogue_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        missions.create_mission(
            svc(seeded_db, LEE),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=[SlotInput("Pilot", 1, {HELIX_PILOTING: 4})],
        )
    assert err.value.message == "Skill not found"
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    ("start", "end"), [("2020-01-01", "2020-01-03"), ("2027-07-01", "2027-07-01")]
)
def test_m2_dates_may_be_in_the_past_and_a_mission_may_last_one_day(seeded_db, start, end):
    view = missions.create_mission(
        svc(seeded_db, LEE), name="Retro", start=d(start), end=d(end), slots=[engineer()]
    )
    assert view.mission.window.start == d(start)


def create_invalid(conn, **overrides):
    args = {
        "name": "Lunar Relay",
        "start": d("2027-07-01"),
        "end": d("2027-07-04"),
        "slots": [engineer()],
    } | overrides
    before = snapshot(conn)
    with pytest.raises(InvalidInput) as err:
        missions.create_mission(svc(conn, LEE), **args)
    assert snapshot(conn) == before
    assert err.value.code == "validation_error"
    return err.value


def test_m2_the_end_date_cannot_be_before_the_start_date(seeded_db):
    err = create_invalid(seeded_db, start=d("2027-07-04"), end=d("2027-07-01"))
    assert [p.message for p in err.problems] == [
        "The end date 2027-07-01 is before the start date 2027-07-04"
    ]


def test_m2_a_mission_needs_a_name(seeded_db):
    err = create_invalid(seeded_db, name="  ")
    assert [p.message for p in err.problems] == ["The mission needs a name"]
    assert err.message == "The mission needs a name"


def test_m2_a_mission_needs_at_least_one_slot(seeded_db):
    err = create_invalid(seeded_db, slots=[])
    assert [p.message for p in err.problems] == ["The mission needs at least one slot"]


@pytest.mark.parametrize(
    ("slot", "message"),
    [
        (SlotInput("Engineer", 0, {SYS_ENG: 3}), "Engineer needs a headcount of at least 1"),
        (SlotInput("Engineer", 1, {}), "Engineer needs at least one required skill"),
        (
            SlotInput("Engineer", 1, {SYS_ENG: 0}),
            "Engineer: a minimum skill level must be from 1 to 5, not 0",
        ),
        (
            SlotInput("Engineer", 1, {SYS_ENG: 6}),
            "Engineer: a minimum skill level must be from 1 to 5, not 6",
        ),
        (SlotInput(" ", 1, {SYS_ENG: 3}), "Every slot needs a name"),
    ],
)
def test_m2_each_slot_needs_a_name_a_headcount_and_a_required_skill(seeded_db, slot, message):
    err = create_invalid(seeded_db, slots=[slot])
    assert [(p.code, p.message) for p in err.problems] == [("validation_error", message)]


def test_m2_every_input_problem_is_listed_at_once(seeded_db):
    err = create_invalid(
        seeded_db,
        name="",
        slots=[SlotInput("Engineer", 0, {SYS_ENG: 3}), SlotInput("Pilot", 1, {})],
    )
    assert err.message == "Some values aren't valid"
    assert [p.message for p in err.problems] == [
        "The mission needs a name",
        "Engineer needs a headcount of at least 1",
        "Pilot needs at least one required skill",
    ]


def create_duplicate(conn, slots):
    before = snapshot(conn)
    with pytest.raises(RuleViolation) as err:
        missions.create_mission(
            svc(conn, LEE),
            name="Lunar Relay",
            start=d("2027-07-01"),
            end=d("2027-07-04"),
            slots=slots,
        )
    assert snapshot(conn) == before
    assert err.value.code == "rule_violation"
    return err.value


def test_m2_a_new_mission_cannot_have_two_slots_with_the_same_name(seeded_db):
    err = create_duplicate(
        seeded_db, [engineer("Engineer"), engineer("Pilot"), engineer(" engineer ", headcount=2)]
    )
    assert err.message == "More than one slot is called Engineer"
    assert [(p.code, p.message, dict(p.refs)) for p in err.problems] == [
        ("already_exists", "More than one slot is called Engineer", {})
    ]


def test_m2_every_repeated_slot_name_is_listed_at_once(seeded_db):
    err = create_duplicate(
        seeded_db,
        [engineer("Engineer"), engineer("Pilot"), engineer("ENGINEER"), engineer("pilot")],
    )
    assert err.message == "Some slots share a name"
    assert [p.message for p in err.problems] == [
        "More than one slot is called Engineer",
        "More than one slot is called Pilot",
    ]


# --- Edit name and dates (M3, M5, M7, AC-4, AC-5) -----------------------------------------


def test_m3_the_owner_renames_and_moves_a_draft_mission(seeded_db):
    view = missions.update_mission(
        svc(seeded_db, LEE),
        GATEWAY,
        name="Gateway Resupply II",
        start=d("2027-03-02"),
        end=d("2027-03-09"),
    )
    assert (view.mission.name, view.mission.status) == ("Gateway Resupply II", MissionStatus.DRAFT)
    assert (view.mission.window.start, view.mission.window.end) == (
        d("2027-03-02"),
        d("2027-03-09"),
    )
    [(actor, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert (actor, event) == (LEE.user_id, "mission.updated")
    assert data["mission_name"] == "Gateway Resupply II"
    assert data["changes"] == {
        "name": ["Lunar Gateway Resupply", "Gateway Resupply II"],
        "start_date": ["2027-03-01", "2027-03-02"],
        "end_date": ["2027-03-10", "2027-03-09"],
    }


def test_m3_only_the_start_or_end_date_can_be_given(seeded_db):
    view = missions.update_mission(svc(seeded_db, LEE), GATEWAY, end=d("2027-03-12"))
    assert (view.mission.window.start, view.mission.window.end) == (
        d("2027-03-01"),
        d("2027-03-12"),
    )


def test_m2_an_edit_cannot_put_the_end_before_the_start(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, start=d("2027-03-11"))
    assert err.value.message == ("The end date 2027-03-10 is before the start date 2027-03-11")
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    ("actor", "mission_id", "error", "code"),
    [
        (NORA, GATEWAY, Forbidden, "not_owner"),  # another Lead
        (RUTH, GATEWAY, Forbidden, "role_forbidden"),  # Directors don't edit mission details
        (BEN, COMMS, Forbidden, "role_forbidden"),  # crew on the mission
        (BEN, GATEWAY, NotFound, "not_found"),  # crew not on the mission can't see it
        (PRIYA, GATEWAY, NotFound, "not_found"),  # another org
    ],
)
def test_m3_ac7_only_the_owning_lead_can_edit_a_mission(seeded_db, actor, mission_id, error, code):
    before = snapshot(seeded_db)
    with pytest.raises(error) as err:
        missions.update_mission(svc(seeded_db, actor), mission_id, name="Renamed")
    assert err.value.code == code
    assert snapshot(seeded_db) == before


def test_ac4_editing_a_pending_mission_returns_it_to_draft_and_clears_its_approvals(seeded_db):
    view = missions.update_mission(svc(seeded_db, NORA), COMMS, end=d("2027-04-21"))
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    # Approvals are never deleted: Marco's stays in round 1, which no longer counts.
    rows = seeded_db.execute(
        "SELECT round, director_id FROM approvals WHERE mission_id = ?", (COMMS,)
    ).fetchall()
    assert [tuple(r) for r in rows] == [(1, MARCO.user_id)]
    assert [e[:4] for e in last_events(seeded_db, COMMS, 2)] == [
        (NORA.user_id, "mission.updated", None, None),
        (NORA.user_id, "mission.returned_to_draft", "pending_approval", "draft"),
    ]
    revert = last_events(seeded_db, COMMS, 1)[0][4]
    assert revert == {"mission_name": "Deep Space Comms Upgrade", "cause": "mission.updated"}
    # Remaining accepted assignments stay accepted.
    assert [a.status for a in view.assignments] == [AssignmentStatus.ACCEPTED]


def test_m3_renaming_a_pending_mission_keeps_it_pending_with_its_approvals(seeded_db):
    """Only changes to dates, slots, roster or owner send a Pending mission back to Draft."""
    view = missions.update_mission(svc(seeded_db, NORA), COMMS, name="Deep Space Comms Upgrade II")
    assert (view.mission.name, view.mission.status) == (
        "Deep Space Comms Upgrade II",
        MissionStatus.PENDING_APPROVAL,
    )
    assert [(a.director_name, a.decision) for a in view.approvals] == [("Marco Bianchi", "approve")]
    [(actor, event, from_status, to_status, data)] = last_events(seeded_db, COMMS, 1)
    assert (actor, event, from_status, to_status) == (NORA.user_id, "mission.updated", None, None)
    assert data == {
        "mission_name": "Deep Space Comms Upgrade II",
        "changes": {"name": ["Deep Space Comms Upgrade", "Deep Space Comms Upgrade II"]},
    }


def test_ac4_renaming_and_moving_a_pending_mission_returns_it_to_draft(seeded_db):
    view = missions.update_mission(
        svc(seeded_db, NORA), COMMS, name="Deep Space Comms Upgrade II", end=d("2027-04-21")
    )
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[1] for e in last_events(seeded_db, COMMS, 2)] == [
        "mission.updated",
        "mission.returned_to_draft",
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "mission.updated"


def test_ac5_m5_an_active_mission_cannot_be_renamed(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        missions.update_mission(svc(seeded_db, LEE), TELESCOPE, name="Telescope II")
    assert (err.value.code, err.value.message) == (
        "mission_frozen",
        "Can't edit an active mission",
    )
    assert snapshot(seeded_db) == before


def test_ac4_an_edit_that_changes_nothing_leaves_a_pending_mission_alone(seeded_db):
    before = snapshot(seeded_db)
    view = missions.update_mission(
        svc(seeded_db, NORA), COMMS, name="Deep Space Comms Upgrade", start=d("2027-04-01")
    )
    assert view.mission.status == MissionStatus.PENDING_APPROVAL
    assert snapshot(seeded_db) == before


def test_ac5_m5_an_active_missions_details_are_frozen(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        missions.update_mission(svc(seeded_db, LEE), TELESCOPE, end=d("2027-01-15"))
    assert (err.value.code, err.value.message) == (
        "mission_frozen",
        "Can't edit an active mission",
    )
    assert snapshot(seeded_db) == before


def test_m5_a_completed_mission_cannot_be_edited_either(seeded_db):
    with pytest.raises(StateConflict) as err:
        missions.update_mission(svc(seeded_db, LEE), MARS, name="Mars Analog II")
    assert (err.value.code, err.value.message) == (
        "mission_final",
        "Can't edit a mission that's completed",
    )


def test_m7_a_date_change_that_breaks_open_assignments_is_refused_naming_everyone(seeded_db):
    propose_chen_for_reboost(seeded_db)  # Chen is on Telescope, 10–14 Jan
    seeded_db.execute(
        "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
        " VALUES (1, 12, '2027-03-05', '2027-03-06', 'Training')"
    )
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.update_mission(
            svc(seeded_db, NORA), REBOOST, start=d("2027-01-12"), end=d("2027-03-06")
        )
    assert err.value.code == "rule_violation"
    assert err.value.message == (
        "Can't change the dates of Station Reboost: Gus and Chen would no longer be "
        "eligible. Remove them from the mission first."
    )
    assert [(p.code, p.message, p.refs["crew_profile_id"]) for p in err.value.problems] == [
        ("unavailable", "Engineer: Gus is unavailable 2027-03-05 to 2027-03-06", 12),
        (
            "overlap",
            "Engineer: Chen has an accepted assignment on Orbital Telescope Service "
            "overlapping 2027-01-12 to 2027-01-14",
            8,
        ),
    ]
    assert snapshot(seeded_db) == before


def test_m7_a_date_change_that_keeps_the_crew_eligible_is_allowed(seeded_db):
    view = missions.update_mission(svc(seeded_db, NORA), REBOOST, start=d("2027-02-20"))
    assert view.mission.window.start == d("2027-02-20")


def chen_on_reboost_and_proposed_for_gateway(conn):
    """Chen accepted Station Reboost (25 Feb – 2 Mar) and is proposed on Gateway (1–10 Mar), so
    he already isn't eligible for Gateway: the two overlap on 1–2 Mar."""
    make_assignment(conn, 1, REBOOST, REBOOST_ENGINEER, 8, NORA.user_id, status="accepted")
    make_assignment(conn, 1, GATEWAY, FLIGHT_ENGINEER, 8, LEE.user_id, status="proposed")


def test_m7_a_date_change_is_not_refused_for_a_conflict_that_already_existed(seeded_db):
    chen_on_reboost_and_proposed_for_gateway(seeded_db)
    view = missions.update_mission(svc(seeded_db, LEE), GATEWAY, end=d("2027-03-12"))
    assert view.mission.window.end == d("2027-03-12")


def test_m7_a_date_change_is_refused_only_for_the_conflicts_it_introduces(seeded_db):
    chen_on_reboost_and_proposed_for_gateway(seeded_db)
    seeded_db.execute(
        "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
        " VALUES (1, 8, '2027-03-11', '2027-03-12', 'Training')"
    )
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, end=d("2027-03-12"))
    assert err.value.code == "rule_violation"
    assert err.value.message == (
        "Can't change the dates of Lunar Gateway Resupply: Chen would no longer be eligible. "
        "Remove them from the mission first."
    )
    # The Station Reboost overlap was there before the edit, so it isn't listed.
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("unavailable", "Flight Engineer: Chen is unavailable 2027-03-11 to 2027-03-12")
    ]
    assert snapshot(seeded_db) == before


def test_m7_a_date_change_into_another_accepted_mission_is_refused(seeded_db):
    chen_on_reboost_and_proposed_for_gateway(seeded_db)  # Chen is also on Telescope, 10–14 Jan
    with pytest.raises(RuleViolation) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, start=d("2027-01-14"))
    assert [(p.code, p.refs["mission_name"]) for p in err.value.problems] == [
        ("overlap", "Orbital Telescope Service")
    ]


# --- Slots (M2, M3, M5, M7, AC-4, AC-5) ---------------------------------------------------


def test_m2_the_owner_adds_a_slot_after_the_last_one(seeded_db):
    view = missions.add_slot(
        svc(seeded_db, LEE), GATEWAY, SlotInput("Medic", 1, {FLIGHT_MEDICINE: 3})
    )
    assert [(s.position, s.name) for s in view.slots][-1] == (4, "Medic")
    assert view.mission.status == MissionStatus.DRAFT
    [(actor, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert (actor, event) == (LEE.user_id, "slot.added")
    assert data["mission_name"] == "Lunar Gateway Resupply"
    assert data["slot_name"] == "Medic"
    assert data["headcount"] == 1
    assert data["requirements"] == [
        {"skill_id": FLIGHT_MEDICINE, "skill_name": "Flight Medicine", "min_level": 3}
    ]


def test_ac4_adding_a_slot_to_a_pending_mission_returns_it_to_draft(seeded_db):
    view = missions.add_slot(svc(seeded_db, NORA), COMMS, engineer("Backup Engineer"))
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[1] for e in last_events(seeded_db, COMMS, 2)] == [
        "slot.added",
        "mission.returned_to_draft",
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "slot.added"


def test_ac5_a_slot_cannot_be_added_to_an_active_mission(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        missions.add_slot(svc(seeded_db, LEE), TELESCOPE, engineer("Backup Engineer"))
    assert err.value.code == "mission_frozen"
    assert snapshot(seeded_db) == before


def test_m3_only_the_owner_can_add_a_slot(seeded_db):
    with pytest.raises(Forbidden) as err:
        missions.add_slot(svc(seeded_db, LEE), COMMS, engineer())
    assert (err.value.code, err.value.message) == (
        "not_owner",
        "Only the mission's owner can edit this mission",
    )


@pytest.mark.parametrize(
    ("actor", "mission_id", "code"),
    [(LEE, COMMS, "not_owner"), (LEE, TELESCOPE, "mission_frozen")],
)
@pytest.mark.parametrize("skill_id", [999, HELIX_PILOTING])
def test_tr10_permission_and_state_are_checked_before_the_skills_are_looked_up(
    seeded_db, actor, mission_id, code, skill_id
):
    for change in (
        lambda c: missions.add_slot(c, mission_id, SlotInput("Pilot", 1, {skill_id: 3})),
        lambda c: missions.replace_requirements(
            c, mission_id, missions.get_mission(c, mission_id).slots[0].id, {skill_id: 3}
        ),
    ):
        with pytest.raises((Forbidden, StateConflict)) as err:
            change(svc(seeded_db, actor))
        assert err.value.code == code


def test_m2_a_mission_cannot_have_two_slots_with_the_same_name(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer(" flight ENGINEER "))
    assert err.value.code == "rule_violation"
    assert err.value.message == "Lunar Gateway Resupply already has a slot called Flight Engineer"
    assert [(p.code, p.message, dict(p.refs)) for p in err.value.problems] == [
        (
            "already_exists",
            "Lunar Gateway Resupply already has a slot called Flight Engineer",
            {"slot_id": FLIGHT_ENGINEER},
        )
    ]
    assert snapshot(seeded_db) == before


def test_m2_a_removed_slots_name_can_be_used_again(seeded_db):
    missions.remove_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER)
    view = missions.add_slot(svc(seeded_db, LEE), GATEWAY, SlotInput("Commander", 1, {PILOTING: 4}))
    assert [s.name for s in view.slots] == ["Flight Engineer", "Mission Specialist", "Commander"]


def test_m2_a_new_slot_is_validated(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(InvalidInput):
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, SlotInput("Medic", 1, {}))
    assert snapshot(seeded_db) == before


def test_ac29_a_new_slot_cannot_require_another_orgs_skill(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound):
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, SlotInput("Pilot", 1, {HELIX_PILOTING: 3}))
    assert snapshot(seeded_db) == before


def test_m3_the_owner_renames_a_slot_and_changes_its_headcount(seeded_db):
    view = missions.update_slot(
        svc(seeded_db, LEE), GATEWAY, COMMANDER, name="Mission Commander", headcount=2
    )
    assert [(s.name, s.headcount, s.open_places) for s in view.slots][-1] == (
        "Mission Commander",
        2,
        2,
    )
    [(_, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert event == "slot.updated"
    assert data["slot_id"] == COMMANDER
    assert data["changes"] == {"name": ["Commander", "Mission Commander"], "headcount": [1, 2]}


def test_m7_lowering_headcount_below_assigned_crew_is_refused(seeded_db):
    propose_chen_for_reboost(seeded_db)
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.update_slot(svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, headcount=1)
    assert err.value.code == "rule_violation"
    assert err.value.message == (
        "Can't lower the headcount of Engineer on Station Reboost: Gus and Chen are assigned. "
        "Remove crew from the slot first."
    )
    [problem] = err.value.problems
    assert problem.code == "headcount_below_open_assignments"
    assert problem.message == (
        "Engineer: Gus and Chen are assigned, more than the new headcount of 1"
    )
    assert problem.refs["crew_profile_ids"] == [12, 8]
    assert snapshot(seeded_db) == before


def test_m7_lowering_headcount_to_the_number_of_assigned_crew_is_allowed(seeded_db):
    view = missions.update_slot(svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, headcount=1)
    assert [(s.headcount, s.open_places) for s in view.slots] == [(1, 0)]


def test_ac4_raising_headcount_on_a_pending_mission_returns_it_to_draft(seeded_db):
    view = missions.update_slot(svc(seeded_db, NORA), COMMS, COMMS_ENGINEER, headcount=2)
    assert view.mission.status == MissionStatus.DRAFT
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "slot.updated"


def test_ac4_renaming_a_slot_on_a_pending_mission_returns_it_to_draft(seeded_db):
    view = missions.update_slot(svc(seeded_db, NORA), COMMS, COMMS_ENGINEER, name="Comms Engineer")
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[1] for e in last_events(seeded_db, COMMS, 2)] == [
        "slot.updated",
        "mission.returned_to_draft",
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "slot.updated"


def test_m2_an_edited_slot_still_needs_a_name_and_a_headcount_of_at_least_one(seeded_db):
    with pytest.raises(InvalidInput) as err:
        missions.update_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER, name="", headcount=0)
    assert err.value.message == "Some values aren't valid"
    assert [(p.message, dict(p.refs)) for p in err.value.problems] == [
        ("Every slot needs a name", {"slot_id": COMMANDER}),
        ("Commander needs a headcount of at least 1", {"slot_id": COMMANDER}),
    ]


def test_m2_a_slot_cannot_be_renamed_to_another_slots_name(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.update_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER, name="mission specialist")
    assert [(p.code, p.message, dict(p.refs)) for p in err.value.problems] == [
        (
            "already_exists",
            "Lunar Gateway Resupply already has a slot called Mission Specialist",
            {"slot_id": SPECIALIST},
        )
    ]
    assert snapshot(seeded_db) == before


def test_m2_a_slot_can_change_the_case_of_its_own_name(seeded_db):
    view = missions.update_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER, name="COMMANDER")
    assert view.slots[-1].name == "COMMANDER"


@pytest.mark.parametrize("slot_id", [PILOT, 12, 999])  # another mission's, another org's, none
def test_t2_ac29_a_slot_that_is_not_on_the_mission_is_not_found(seeded_db, slot_id):
    with pytest.raises(NotFound) as err:
        missions.update_slot(svc(seeded_db, LEE), GATEWAY, slot_id, headcount=2)
    assert err.value.message == "Slot not found"


def test_m2_m3_the_owner_replaces_a_slots_requirements(seeded_db):
    view = missions.replace_requirements(
        svc(seeded_db, LEE), GATEWAY, COMMANDER, {PILOTING: 5, LEADERSHIP: 4}
    )
    commander = next(s for s in view.slots if s.id == COMMANDER)
    assert [(r.skill_name, r.min_level) for r in commander.requirements] == [
        ("Piloting", 5),
        ("Leadership", 4),
    ]
    [(_, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert event == "slot.requirements_changed"
    assert data["slot_name"] == "Commander"
    assert data["requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 5},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 4},
    ]
    assert data["previous_requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 4},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 3},
    ]


def test_m7_a_requirement_change_that_breaks_an_assignee_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.replace_requirements(
            svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, {SYS_ENG: 3, EVA: 1}
        )
    assert err.value.code == "rule_violation"
    assert err.value.message == (
        "Can't change the requirements of Engineer on Station Reboost: Gus would no longer be "
        "eligible. Remove them from the mission first."
    )
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("skill_below_minimum", "Engineer: Gus doesn't have EVA (needs 1)")
    ]
    assert snapshot(seeded_db) == before


def test_m7_a_requirement_refusal_names_everyone_it_breaks_including_proposed_crew(seeded_db):
    propose_chen_for_reboost(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.replace_requirements(
            svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, {SYS_ENG: 3, EVA: 1}
        )
    assert err.value.message == (
        "Can't change the requirements of Engineer on Station Reboost: Gus and Chen would no "
        "longer be eligible. Remove them from the mission first."
    )
    assert [(p.message, p.refs["crew_profile_id"]) for p in err.value.problems] == [
        ("Engineer: Gus doesn't have EVA (needs 1)", 12),
        ("Engineer: Chen doesn't have EVA (needs 1)", 8),
    ]


def test_m7_a_requirement_refusal_names_a_crew_member_who_is_only_proposed(seeded_db):
    propose_chen_for_reboost(seeded_db)  # Chen has Systems Engineering 3, Gus 5
    with pytest.raises(RuleViolation) as err:
        missions.replace_requirements(svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, {SYS_ENG: 4})
    assert err.value.message == (
        "Can't change the requirements of Engineer on Station Reboost: Chen would no longer be "
        "eligible. Remove them from the mission first."
    )
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("skill_below_minimum", "Engineer: Chen has Systems Engineering 3 (needs 4)")
    ]


def lower_chens_systems_engineering(conn):
    """P3 allows lowering a skill that makes someone ineligible on a Draft mission."""
    conn.execute(
        "UPDATE crew_skills SET level = 2 WHERE crew_profile_id = 8 AND skill_id = ?", (SYS_ENG,)
    )


def test_m7_after_a_skill_was_lowered_a_requirement_change_refuses_only_new_shortfalls(seeded_db):
    propose_chen_for_reboost(seeded_db)
    lower_chens_systems_engineering(seeded_db)
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.replace_requirements(
            svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, {SYS_ENG: 3, EVA: 1}
        )
    # Chen's Systems Engineering 2 already fell short of 3, so only EVA is listed for him.
    assert [(p.message, p.refs["crew_profile_id"]) for p in err.value.problems] == [
        ("Engineer: Gus doesn't have EVA (needs 1)", 12),
        ("Engineer: Chen doesn't have EVA (needs 1)", 8),
    ]
    assert snapshot(seeded_db) == before


def test_m7_after_a_skill_was_lowered_an_existing_shortfall_does_not_block_a_change(seeded_db):
    propose_chen_for_reboost(seeded_db)
    lower_chens_systems_engineering(seeded_db)
    view = missions.replace_requirements(
        svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, {SYS_ENG: 4}
    )
    assert [(r.skill_id, r.min_level) for r in view.slots[0].requirements] == [(SYS_ENG, 4)]


def test_m7_a_refused_edit_leaves_a_pending_mission_pending_with_its_approvals(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.replace_requirements(svc(seeded_db, NORA), COMMS, COMMS_ENGINEER, {SYS_ENG: 5})
    assert err.value.code == "rule_violation"
    assert snapshot(seeded_db) == before
    view = missions.get_mission(svc(seeded_db, NORA), COMMS)
    assert view.mission.status == MissionStatus.PENDING_APPROVAL
    assert [(a.director_name, a.decision) for a in view.approvals] == [("Marco Bianchi", "approve")]


def test_m2_a_slot_must_keep_at_least_one_requirement(seeded_db):
    with pytest.raises(InvalidInput) as err:
        missions.replace_requirements(svc(seeded_db, LEE), GATEWAY, COMMANDER, {})
    assert [(p.message, dict(p.refs)) for p in err.value.problems] == [
        ("Commander needs at least one required skill", {"slot_id": COMMANDER})
    ]
    assert err.value.message == "Commander needs at least one required skill"


def test_ac29_requirements_cannot_name_another_orgs_skill(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        missions.replace_requirements(svc(seeded_db, LEE), GATEWAY, COMMANDER, {HELIX_PILOTING: 4})
    assert err.value.message == "Skill not found"
    assert snapshot(seeded_db) == before


def test_ac4_changing_requirements_on_a_pending_mission_returns_it_to_draft(seeded_db):
    view = missions.replace_requirements(svc(seeded_db, NORA), COMMS, COMMS_ENGINEER, {SYS_ENG: 4})
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[1] for e in last_events(seeded_db, COMMS, 2)] == [
        "slot.requirements_changed",
        "mission.returned_to_draft",
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4] == {
        "mission_name": "Deep Space Comms Upgrade",
        "cause": "slot.requirements_changed",
    }


def test_m2_m3_the_owner_removes_an_empty_slot_softly(seeded_db):
    view = missions.remove_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER)
    assert [s.name for s in view.slots] == ["Flight Engineer", "Mission Specialist"]
    removed_at = seeded_db.execute(
        "SELECT removed_at FROM slots WHERE id = ?", (COMMANDER,)
    ).fetchone()[0]
    assert removed_at is not None  # soft delete
    [(_, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert (event, data["slot_name"], data["slot_id"]) == ("slot.removed", "Commander", COMMANDER)
    with pytest.raises(NotFound):
        missions.remove_slot(svc(seeded_db, LEE), GATEWAY, COMMANDER)


def test_m7_removing_a_slot_with_open_assignments_is_refused(seeded_db):
    missions.add_slot(svc(seeded_db, NORA), REBOOST, engineer("Backup Engineer"))
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.remove_slot(svc(seeded_db, NORA), REBOOST, REBOOST_ENGINEER)
    assert err.value.code == "rule_violation"
    assert err.value.message == (
        "Can't remove Engineer from Station Reboost while Gus is assigned to it. "
        "Remove them from the mission first."
    )
    assert [(p.code, p.message) for p in err.value.problems] == [
        ("slot_has_open_assignments", "Engineer: Gus is still assigned")
    ]
    assert snapshot(seeded_db) == before


def test_m2_a_missions_last_slot_cannot_be_removed(seeded_db):
    missions.remove_slot(svc(seeded_db, NORA), ASTEROID, GEOLOGIST)
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.remove_slot(svc(seeded_db, NORA), ASTEROID, PILOT)
    message = "Can't remove Pilot: Asteroid Survey needs at least one slot"
    assert (err.value.code, err.value.message) == ("rule_violation", message)
    assert [(p.code, p.message, dict(p.refs)) for p in err.value.problems] == [
        ("mission_needs_a_slot", message, {"slot_id": PILOT})
    ]
    assert snapshot(seeded_db) == before


def test_ac29_another_orgs_slot_cannot_be_removed(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        missions.remove_slot(svc(seeded_db, LEE), GATEWAY, 12)  # Payload Demo 1's slot
    assert err.value.message == "Slot not found"
    assert snapshot(seeded_db) == before


SLOT_CHANGES = {
    "update_slot": lambda c, m, s: missions.update_slot(c, m, s, name="Renamed"),
    "replace_requirements": lambda c, m, s: missions.replace_requirements(c, m, s, {SYS_ENG: 2}),
    "remove_slot": lambda c, m, s: missions.remove_slot(c, m, s),
}


@pytest.mark.parametrize("change", SLOT_CHANGES.values(), ids=SLOT_CHANGES.keys())
def test_m3_ac7_only_the_owner_can_change_a_slot(seeded_db, change):
    missions.add_slot(svc(seeded_db, NORA), REBOOST, engineer("Backup Engineer"))
    backup = missions.get_mission(svc(seeded_db, NORA), REBOOST).slots[-1].id
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        change(svc(seeded_db, LEE), REBOOST, backup)
    assert (err.value.code, err.value.message) == (
        "not_owner",
        "Only the mission's owner can edit this mission",
    )
    assert snapshot(seeded_db) == before


SLOT_OPERATIONS = {
    "add_slot": lambda c: missions.add_slot(c, GATEWAY, engineer("Backup Engineer")),
    **{name: (lambda c, f=f: f(c, GATEWAY, COMMANDER)) for name, f in SLOT_CHANGES.items()},
}


@pytest.mark.parametrize("operation", SLOT_OPERATIONS.values(), ids=SLOT_OPERATIONS.keys())
def test_tr10_crew_not_on_the_mission_get_not_found_for_its_slots(seeded_db, operation):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        operation(svc(seeded_db, BEN))
    assert err.value.message == "Mission not found"
    assert snapshot(seeded_db) == before


MISSION_EDITS = {
    "update_mission": lambda c: missions.update_mission(c, GATEWAY, name="Renamed"),
    **SLOT_OPERATIONS,
}


@pytest.mark.parametrize("edit", MISSION_EDITS.values(), ids=MISSION_EDITS.keys())
def test_m5_a_cancelled_mission_cannot_be_edited(seeded_db, edit):
    seeded_db.execute("UPDATE missions SET status = 'cancelled' WHERE id = ?", (GATEWAY,))
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        edit(svc(seeded_db, LEE))
    assert (err.value.code, err.value.message) == (
        "mission_final",
        "Can't edit a mission that's cancelled",
    )
    assert snapshot(seeded_db) == before


def test_ac4_removing_a_slot_from_a_pending_mission_returns_it_to_draft(seeded_db):
    missions.add_slot(svc(seeded_db, NORA), COMMS, engineer("Backup Engineer"))  # now Draft
    seeded_db.execute("UPDATE missions SET status = 'pending_approval' WHERE id = ?", (COMMS,))
    backup = missions.get_mission(svc(seeded_db, NORA), COMMS).slots[-1].id
    view = missions.remove_slot(svc(seeded_db, NORA), COMMS, backup)
    assert view.mission.status == MissionStatus.DRAFT
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "slot.removed"


@pytest.mark.parametrize(
    "change",
    [
        lambda c: missions.update_slot(c, TELESCOPE, TELESCOPE_ENGINEER, headcount=2),
        lambda c: missions.replace_requirements(c, TELESCOPE, TELESCOPE_ENGINEER, {SYS_ENG: 2}),
        lambda c: missions.remove_slot(c, TELESCOPE, TELESCOPE_ENGINEER),
    ],
)
def test_ac5_an_active_missions_slots_are_frozen(seeded_db, change):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        change(svc(seeded_db, LEE))
    assert err.value.code == "mission_frozen"
    assert snapshot(seeded_db) == before


# --- Transfer ownership (M1, AC-7) --------------------------------------------------------


def test_ac7_after_transfer_the_new_owner_can_edit_and_the_old_cannot(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, RUTH), GATEWAY, NORA.user_id)
    assert (view.mission.owner_id, view.owner_name) == (NORA.user_id, "Nora Quinn")
    assert view.mission.created_by_id == RUTH.user_id  # the creator is unchanged
    assert view.mission.status == MissionStatus.DRAFT
    [(actor, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert (actor, event) == (RUTH.user_id, "mission.transferred")
    assert data == {
        "mission_name": "Lunar Gateway Resupply",
        "from_owner_id": LEE.user_id,
        "from_owner_name": "Lee Park",
        "to_owner_id": NORA.user_id,
        "to_owner_name": "Nora Quinn",
    }

    missions.update_mission(svc(seeded_db, NORA), GATEWAY, name="Gateway (Nora)")
    with pytest.raises(Forbidden) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, name="Gateway (Lee)")
    assert err.value.code == "not_owner"
    with pytest.raises(Forbidden):
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer())


def test_m1_transferring_a_pending_mission_returns_it_to_draft_and_clears_approvals(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, RUTH), COMMS, LEE.user_id)
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[:4] for e in last_events(seeded_db, COMMS, 2)] == [
        (RUTH.user_id, "mission.transferred", None, None),
        (RUTH.user_id, "mission.returned_to_draft", "pending_approval", "draft"),
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "mission.transferred"


def test_m1_transferring_an_active_mission_keeps_it_active(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, INGRID), TELESCOPE, NORA.user_id)
    assert (view.mission.status, view.mission.owner_id) == (MissionStatus.ACTIVE, NORA.user_id)
    assert [e[1] for e in last_events(seeded_db, TELESCOPE, 1)] == ["mission.transferred"]


@pytest.mark.parametrize(
    ("mission_id", "message"),
    [
        (MARS, "Can't transfer a mission that's completed"),
        (GATEWAY, "Can't transfer a mission that's cancelled"),
    ],
)
def test_m1_a_final_mission_cannot_be_transferred(seeded_db, mission_id, message):
    seeded_db.execute("UPDATE missions SET status = 'cancelled' WHERE id = ?", (GATEWAY,))
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        missions.transfer_ownership(svc(seeded_db, RUTH), mission_id, NORA.user_id)
    assert (err.value.code, err.value.message) == ("mission_final", message)
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    ("actor", "mission_id", "error", "code", "message"),
    [
        (LEE, GATEWAY, Forbidden, "role_forbidden", "Leads can't transfer mission ownership"),
        (NORA, GATEWAY, Forbidden, "role_forbidden", "Leads can't transfer mission ownership"),
        (BEN, COMMS, Forbidden, "role_forbidden", "Crew can't transfer mission ownership"),
        (BEN, GATEWAY, NotFound, "not_found", "Mission not found"),  # crew not on it
        (SAM, GATEWAY, NotFound, "not_found", "Mission not found"),  # another org's Director
    ],
)
def test_m1_only_directors_can_transfer_ownership(
    seeded_db, actor, mission_id, error, code, message
):
    before = snapshot(seeded_db)
    with pytest.raises(error) as err:
        missions.transfer_ownership(svc(seeded_db, actor), mission_id, ANA.user_id)
    assert (err.value.code, err.value.message) == (code, message)
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize("new_owner_id", [999, PRIYA.user_id, NORA.user_id])
def test_tr10_a_refused_transfer_gets_the_same_403_whether_or_not_the_new_owner_exists(
    seeded_db, new_owner_id
):
    with pytest.raises(Forbidden) as err:
        missions.transfer_ownership(svc(seeded_db, LEE), GATEWAY, new_owner_id)
    assert (err.value.code, err.value.message) == (
        "role_forbidden",
        "Leads can't transfer mission ownership",
    )


@pytest.mark.parametrize(
    ("owner_id", "message"),
    [
        (7, "Ben Ito can't own a mission: only Mission Leads can"),
        (3, "Ingrid Holm can't own a mission: only Mission Leads can"),
        (6, "Ana Okafor can't own a mission because they're deactivated"),
    ],
)
def test_m1_the_new_owner_must_be_an_active_lead(seeded_db, owner_id, message):
    deactivate(seeded_db, 6)
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.transfer_ownership(svc(seeded_db, RUTH), COMMS, owner_id)
    assert [(p.code, p.message) for p in err.value.problems] == [("owner_not_active_lead", message)]
    assert snapshot(seeded_db) == before


def test_ac29_transferring_to_another_orgs_lead_is_not_found(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(NotFound) as err:
        missions.transfer_ownership(svc(seeded_db, RUTH), GATEWAY, PRIYA.user_id)
    assert err.value.message == "User not found"
    assert snapshot(seeded_db) == before


def test_m1_transferring_to_the_current_owner_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        missions.transfer_ownership(svc(seeded_db, RUTH), COMMS, NORA.user_id)
    message = "Nora Quinn already owns Deep Space Comms Upgrade"
    assert (err.value.code, err.value.message) == ("rule_violation", message)
    assert [(p.code, p.message, dict(p.refs)) for p in err.value.problems] == [
        ("already_owner", message, {"user_id": NORA.user_id})
    ]
    assert snapshot(seeded_db) == before
