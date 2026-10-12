"""M14: the matching service, preview only. Suggests crew for a Draft mission's open places and
writes nothing (PRD §6, AC-18 to AC-22, AC-31, S2, S3, S3b; design §6).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Lee 4 · Nora 5 · Ana 6 ·
Ben 7 · Chen 8 · Dana 9 · Eli 10 · Fay 11 · Gus 12 · Hana 13 · Sam 14 (Helix) · Kai 16 (Helix).
Missions: Gateway 1 · Asteroid 2 · Reboost 3 · Telescope 5 · Comms 6 · Mars 7 · Payload 8 (Helix).
Gateway slots: Flight Engineer 1 · Mission Specialist 2 · Commander 3. Asteroid: Pilot 4 ·
Geologist 5. Skills: Piloting 1 · Leadership 2.
"""

from datetime import UTC, date, datetime

import pytest

from builders import make_assignment, make_mission, make_slot
from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, NotFound, RuleViolation
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import matching
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

GATEWAY, ASTEROID, REBOOST, TELESCOPE, COMMS, MARS, PAYLOAD = 1, 2, 3, 5, 6, 7, 8
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT, GEOLOGIST = 1, 2, 3, 4, 5
PILOTING = 1
ANA_ID, BEN_ID, CHEN_ID, DANA_ID, ELI_ID, KAI_ID = 6, 7, 8, 9, 10, 16
HELIX_CREW = {16, 17, 18, 19}


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def picks(preview):
    """{slot name: [(person, workload, proficiency), ...]} in listed slot order."""
    return {
        s.name: [(p.name, p.workload, p.proficiency) for p in s.suggested] for s in preview.slots
    }


def suggested_ids(preview):
    return [p.crew_profile_id for s in preview.slots for p in s.suggested]


def snapshot(conn):
    """Every table, to prove a preview changed nothing."""
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            " ORDER BY name"
        )
    ]
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


def accept(conn, mission_id, slot_id, crew_profile_id, owner_id=4, status="accepted", reason=None):
    return make_assignment(
        conn, 1, mission_id, slot_id, crew_profile_id, owner_id, status=status, reason=reason
    )


# --- S2: Lunar Gateway Resupply -----------------------------------------------------------


def test_s2_gateway_preview_suggests_ana_chen_dana_with_workload_and_proficiency(seeded_db):
    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert picks(preview) == {
        "Flight Engineer": [("Chen", 5, 3)],
        "Mission Specialist": [("Dana", 5, 4)],
        "Commander": [("Ana", 0, 9)],  # Piloting 5 + Leadership 4
    }
    assert [s.unfilled for s in preview.slots] == [0, 0, 0]
    assert preview.unfilled_places == 0


def test_s2_preview_names_the_mission_and_lists_slots_in_listed_order(seeded_db):
    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert (preview.mission_id, preview.mission_name) == (GATEWAY, "Lunar Gateway Resupply")
    assert preview.window == DateRange(date(2027, 3, 1), date(2027, 3, 10))
    assert [(s.slot_id, s.name, s.open_places) for s in preview.slots] == [
        (FLIGHT_ENGINEER, "Flight Engineer", 1),
        (SPECIALIST, "Mission Specialist", 1),
        (COMMANDER, "Commander", 1),
    ]
    assert preview.open_places == 3


def test_s2_pick_order_shows_the_most_constrained_slot_was_filled_first(seeded_db):
    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    order = {p.name: p.pick for s in preview.slots for p in s.suggested}
    assert order == {"Ana": 1, "Chen": 2, "Dana": 3}


def test_ac18_same_inputs_give_the_same_preview(seeded_db):
    first = matching.preview(as_(seeded_db, LEE), GATEWAY)
    again = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert first == again


def test_ac20_chens_workload_ignores_his_completed_mission(seeded_db):
    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    [chen] = [p for s in preview.slots for p in s.suggested if p.crew_profile_id == CHEN_ID]
    assert chen.workload == 5  # Telescope only; Mars Analog is Completed


# --- S3 and S3b: Asteroid Survey ----------------------------------------------------------


def test_ac19_s3_geologist_is_reported_unfilled(seeded_db):
    preview = matching.preview(as_(seeded_db, NORA), ASTEROID)

    assert picks(preview) == {"Pilot": [("Ana", 0, 5)], "Geologist": []}
    assert [(s.name, s.open_places, s.unfilled) for s in preview.slots] == [
        ("Pilot", 1, 0),
        ("Geologist", 1, 1),
    ]
    assert preview.unfilled_places == 1


def test_s3b_new_accepted_assignment_changes_the_suggestion(seeded_db):
    # S1 up to acceptance: Ana, Chen and Dana accepted on Gateway (1–10 Mar).
    accept(seeded_db, GATEWAY, COMMANDER, ANA_ID)
    accept(seeded_db, GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    accept(seeded_db, GATEWAY, SPECIALIST, DANA_ID)

    preview = matching.preview(as_(seeded_db, NORA), ASTEROID)

    assert picks(preview) == {"Pilot": [("Eli", 5, 4)], "Geologist": []}
    assert preview.unfilled_places == 1


# --- Candidates (PRD §6, AC-21) -----------------------------------------------------------


def test_preview_leaves_out_crew_who_declined_this_mission(seeded_db):
    accept(seeded_db, GATEWAY, COMMANDER, ANA_ID, status="declined")

    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    # Without Ana nobody else qualifies as Commander (Fay unavailable, Eli's Leadership is 2).
    assert ANA_ID not in suggested_ids(preview)
    commander = preview.slots[2]
    assert (commander.name, commander.suggested, commander.unfilled) == ("Commander", (), 1)


def test_preview_leaves_out_crew_who_withdrew_from_this_mission(seeded_db):
    accept(seeded_db, GATEWAY, FLIGHT_ENGINEER, CHEN_ID, status="withdrawn", reason="Family")

    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert picks(preview)["Flight Engineer"] == [("Ben", 20, 4)]
    assert CHEN_ID not in suggested_ids(preview)


def test_preview_leaves_out_crew_already_on_this_mission_and_skips_their_place(seeded_db):
    accept(seeded_db, GATEWAY, COMMANDER, ANA_ID, status="proposed")

    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    commander = preview.slots[2]
    assert (commander.open_places, commander.suggested, commander.unfilled) == (0, (), 0)
    assert ANA_ID not in suggested_ids(preview)
    # Ana is spoken for, so Flight Engineer still goes to Chen on workload.
    assert picks(preview)["Flight Engineer"] == [("Chen", 5, 3)]


def test_preview_leaves_out_crew_removed_from_this_mission(seeded_db):
    accept(seeded_db, GATEWAY, COMMANDER, ANA_ID, status="removed")

    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert ANA_ID not in suggested_ids(preview)
    commander = preview.slots[2]
    assert (commander.open_places, commander.suggested, commander.unfilled) == (1, (), 1)


def test_ac21_deactivated_crew_are_never_suggested(seeded_db):
    seeded_db.execute("UPDATE users SET is_active = 0 WHERE id = :id", {"id": CHEN_ID})

    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)

    assert CHEN_ID not in suggested_ids(preview)
    assert picks(preview)["Flight Engineer"] == [("Ben", 20, 4)]


def test_ac21_nobody_is_suggested_for_two_places(seeded_db):
    mission = make_mission(seeded_db, 1, owner_id=4, start="2027-03-01", end="2027-03-10")
    for position, name in enumerate(("EVA One", "EVA Two"), start=1):
        slot_id = make_slot(seeded_db, 1, mission, name=name, headcount=2, position=position)
        seeded_db.execute(
            "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
            " VALUES (1, :slot, 4, 3)",
            {"slot": slot_id},
        )

    preview = matching.preview(as_(seeded_db, LEE), mission)

    ids = suggested_ids(preview)
    assert len(ids) == len(set(ids)) == 4  # Ben, Dana, Eli, Hana: one place each
    assert preview.unfilled_places == 0


def test_a_slot_with_several_places_lists_its_people_in_pick_order(seeded_db):
    [reboost_engineer] = matching.preview(as_(seeded_db, NORA), REBOOST).slots

    assert (reboost_engineer.open_places, reboost_engineer.unfilled) == (1, 0)  # Gus accepted
    assert [p.name for p in reboost_engineer.suggested] == ["Ana"]


# --- Tenant isolation (AC-31, AC-27) ------------------------------------------------------


def test_ac31_other_orgs_crew_never_appear(seeded_db):
    # Only Ana has Piloting 5 in Aurora; Helix's Kai has Piloting 5 in Helix's own catalogue.
    mission = make_mission(seeded_db, 1, owner_id=4, start="2027-03-01", end="2027-03-10")
    slot_id = make_slot(seeded_db, 1, mission, name="Ace Pilot")
    seeded_db.execute(
        "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
        " VALUES (1, :slot, :skill, 5)",
        {"slot": slot_id, "skill": PILOTING},
    )
    accept(seeded_db, mission, slot_id, ANA_ID, status="declined")

    preview = matching.preview(as_(seeded_db, LEE), mission)

    assert suggested_ids(preview) == []
    assert preview.slots[0].unfilled == 1
    for mission_id, actor in ((GATEWAY, LEE), (ASTEROID, NORA)):
        assert not HELIX_CREW & set(
            suggested_ids(matching.preview(as_(seeded_db, actor), mission_id))
        )


def test_ac27_another_orgs_mission_is_not_found(seeded_db):
    with pytest.raises(NotFound):
        matching.preview(as_(seeded_db, LEE), PAYLOAD)
    with pytest.raises(NotFound):
        matching.preview(as_(seeded_db, SAM), GATEWAY)


def test_unknown_mission_is_not_found(seeded_db):
    with pytest.raises(NotFound) as refused:
        matching.preview(as_(seeded_db, LEE), 999)
    assert refused.value.message == "Mission not found"


# --- Who may preview (§6, design §4) ------------------------------------------------------


def test_owner_lee_can_preview(seeded_db):
    assert matching.preview(as_(seeded_db, LEE), GATEWAY).slots


def test_the_owner_may_apply_the_suggestion(seeded_db):
    assert matching.preview(as_(seeded_db, LEE), GATEWAY).can_apply is True
    assert matching.preview(as_(seeded_db, NORA), ASTEROID).can_apply is True


def test_a_director_may_preview_but_not_apply(seeded_db):
    assert matching.preview(as_(seeded_db, RUTH), GATEWAY).can_apply is False


def test_director_ruth_can_preview_a_mission_she_does_not_own(seeded_db):
    assert picks(matching.preview(as_(seeded_db, RUTH), ASTEROID))["Pilot"] == [("Ana", 0, 5)]


def test_nora_cannot_preview_a_mission_owned_by_another_lead(seeded_db):
    with pytest.raises(Forbidden) as refused:
        matching.preview(as_(seeded_db, NORA), GATEWAY)
    assert refused.value.code == "not_owner"


def test_ana_lead_on_crew_cannot_preview_a_mission_she_does_not_own(seeded_db):
    with pytest.raises(Forbidden):
        matching.preview(as_(seeded_db, ANA), GATEWAY)


def test_crew_ben_cannot_see_a_mission_he_is_not_on(seeded_db):
    with pytest.raises(NotFound):
        matching.preview(as_(seeded_db, BEN), GATEWAY)


def test_crew_ben_on_a_mission_is_forbidden_to_preview_it(seeded_db):
    with pytest.raises(Forbidden) as refused:
        matching.preview(as_(seeded_db, BEN), COMMS)
    assert refused.value.code == "role_forbidden"


def test_permission_is_checked_before_the_mission_state(seeded_db):
    with pytest.raises(Forbidden):
        matching.preview(as_(seeded_db, NORA), TELESCOPE)  # Lee's, and Active


# --- Draft only (§6) ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("actor", "mission_id", "code", "message"),
    [
        (LEE, TELESCOPE, "mission_frozen", "Can't suggest crew for an active mission"),
        (NORA, COMMS, "invalid_transition", "Can't suggest crew for a mission pending approval"),
        (LEE, MARS, "mission_final", "Can't suggest crew for a mission that's completed"),
        (RUTH, TELESCOPE, "mission_frozen", "Can't suggest crew for an active mission"),
    ],
)
def test_preview_is_refused_for_a_mission_that_is_not_draft(
    seeded_db, actor, mission_id, code, message
):
    # The wording and codes come from the lifecycle's state table.
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as refused:
        matching.preview(as_(seeded_db, actor), mission_id)
    assert refused.value.code == code
    assert refused.value.message == message
    assert [p.code for p in refused.value.problems] == [code]
    assert snapshot(seeded_db) == before


def test_preview_is_refused_for_a_cancelled_mission(seeded_db):
    seeded_db.execute("UPDATE missions SET status = 'cancelled' WHERE id = :id", {"id": ASTEROID})

    with pytest.raises(RuleViolation) as refused:
        matching.preview(as_(seeded_db, NORA), ASTEROID)
    assert refused.value.code == "mission_final"
    assert refused.value.message == "Can't suggest crew for a mission that's cancelled"


# --- Read only (AC-22) --------------------------------------------------------------------


def test_ac22_preview_writes_nothing(seeded_db):
    before = snapshot(seeded_db)
    changes = seeded_db.total_changes

    matching.preview(as_(seeded_db, LEE), GATEWAY)
    matching.preview(as_(seeded_db, NORA), ASTEROID)
    matching.preview(as_(seeded_db, RUTH), GATEWAY)

    assert seeded_db.total_changes == changes
    assert snapshot(seeded_db) == before
    assert not seeded_db.in_transaction


def test_ac22_a_refused_preview_writes_nothing(seeded_db):
    before = snapshot(seeded_db)
    for actor, mission_id in ((NORA, GATEWAY), (BEN, GATEWAY), (SAM, GATEWAY)):
        with pytest.raises((Forbidden, NotFound)):
            matching.preview(as_(seeded_db, actor), mission_id)
    assert snapshot(seeded_db) == before
    assert not seeded_db.in_transaction


# --- Output shape -------------------------------------------------------------------------


def test_preview_records_are_frozen(seeded_db):
    preview = matching.preview(as_(seeded_db, LEE), GATEWAY)
    with pytest.raises(AttributeError):
        preview.mission_name = "Other"  # type: ignore[misc]
    assert isinstance(preview.slots, tuple)
    assert all(isinstance(s.suggested, tuple) for s in preview.slots)
