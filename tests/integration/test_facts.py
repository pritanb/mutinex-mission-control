"""SF: fact loaders build the domain records from the database (design §6 inputs)."""

from datetime import date

import pytest

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.matching import suggest_roster
from mission_control.infra.repositories import Repos

GATEWAY, ASTEROID, REBOOST, MEDICAL, TELESCOPE, COMMS, MARS, PAYLOAD = 1, 2, 3, 4, 5, 6, 7, 8
NAMES = {
    2: "Marco",
    6: "Ana",
    7: "Ben",
    8: "Chen",
    9: "Dana",
    10: "Eli",
    11: "Fay",
    12: "Gus",
    13: "Hana",
}


@pytest.fixture
def facts(seeded_db):
    return Repos(seeded_db, 1).facts


def window(a, b):
    return DateRange(date.fromisoformat(a), date.fromisoformat(b))


# --- Slots as matcher input ---------------------------------------------------------------


def test_slot_specs_carry_open_places_and_named_requirements(facts):
    specs = facts.slot_specs(GATEWAY)
    assert [(s.name, s.position, s.open_places) for s in specs] == [
        ("Flight Engineer", 1, 1),
        ("Mission Specialist", 2, 1),
        ("Commander", 3, 1),
    ]
    assert {(r.skill_name, r.min_level) for r in specs[2].requirements} == {
        ("Piloting", 4),
        ("Leadership", 3),
    }


def test_open_places_subtract_open_assignments_only(seeded_db, facts):
    [engineer] = facts.slot_specs(REBOOST)  # headcount 2, Gus accepted
    assert engineer.open_places == 1
    seeded_db.execute(
        "UPDATE assignments SET status = 'declined' WHERE crew_profile_id = 12 AND mission_id = 3"
    )
    assert facts.slot_specs(REBOOST)[0].open_places == 2


# --- Candidate facts ----------------------------------------------------------------------


def test_candidates_are_every_profile_in_the_org_with_workload(facts):
    candidates = {c.crew_profile_id: c for c in facts.candidates(excluding_mission_id=GATEWAY)}
    assert {i: NAMES[i] for i in candidates} == NAMES
    assert {i: c.workload for i, c in candidates.items()} == {
        2: 4,
        6: 0,
        7: 20,
        8: 5,
        9: 5,
        10: 5,
        11: 0,
        12: 6,
        13: 5,
    }


def test_candidate_facts_match_the_seed(facts):
    gus = facts.candidate(12, excluding_mission_id=GATEWAY)
    assert (gus.name, gus.active, dict(gus.skills)) == ("Gus", True, {3: 5})
    assert [(c.mission_name, c.window) for c in gus.accepted_elsewhere] == [
        ("Station Reboost", window("2027-02-25", "2027-03-02"))
    ]
    fay = facts.candidate(11, excluding_mission_id=GATEWAY)
    assert fay.unavailable == (window("2027-03-05", "2027-03-08"),)


def test_accepted_elsewhere_excludes_the_mission_itself_and_finished_missions(facts):
    chen_on_telescope = facts.candidate(8, excluding_mission_id=TELESCOPE)
    assert chen_on_telescope.accepted_elsewhere == ()  # Mars Analog is completed
    chen = facts.candidate(8, excluding_mission_id=GATEWAY)
    assert [c.mission_id for c in chen.accepted_elsewhere] == [TELESCOPE]


def test_workload_excludes_the_mission_being_matched(facts):
    assert facts.candidate(12, excluding_mission_id=REBOOST).workload == 0
    assert facts.candidate(12, excluding_mission_id=GATEWAY).workload == 6


def test_a_deactivated_user_is_an_inactive_candidate(seeded_db, facts):
    seeded_db.execute("UPDATE users SET is_active = 0 WHERE id = 11")
    assert facts.candidate(11, excluding_mission_id=GATEWAY).active is False


def test_unknown_or_foreign_candidate_is_none(seeded_db, facts):
    assert facts.candidate(999, excluding_mission_id=GATEWAY) is None
    assert facts.candidate(17, excluding_mission_id=GATEWAY) is None  # Lena is Helix's
    assert {c.crew_profile_id for c in Repos(seeded_db, 2).facts.candidates(PAYLOAD)} == {
        16,
        17,
        18,
        19,
    }


def test_candidates_can_be_limited_to_some_profiles(facts):
    assert [c.crew_profile_id for c in facts.candidates(GATEWAY, crew_profile_ids=[9, 6])] == [6, 9]
    assert facts.candidates(GATEWAY, crew_profile_ids=[]) == []


# --- End to end: database facts drive the matcher -----------------------------------------


def test_s2_from_the_database_gives_ana_chen_dana(facts):
    s = suggest_roster(
        facts.slot_specs(GATEWAY), facts.candidates(GATEWAY), window("2027-03-01", "2027-03-10")
    )
    assert [NAMES[p.crew_profile_id] for p in s.placements] == ["Ana", "Chen", "Dana"]


def test_s3_from_the_database_gives_ana_and_an_unfilled_geologist(facts):
    s = suggest_roster(
        facts.slot_specs(ASTEROID), facts.candidates(ASTEROID), window("2027-03-05", "2027-03-12")
    )
    assert [NAMES[p.crew_profile_id] for p in s.placements] == ["Ana"]
    assert [u.count for u in s.unfilled] == [1]


# --- Roster, workload facts and active assignments ----------------------------------------


def test_roster_lists_open_assignments_with_their_slot_and_crew(facts):
    roster = facts.roster(TELESCOPE)
    assert [(e.slot.name, e.crew.name, e.status) for e in roster] == [
        ("Engineer", "Chen", AssignmentStatus.ACCEPTED),
        ("EVA Specialist", "Dana", AssignmentStatus.ACCEPTED),
        ("EVA Specialist", "Eli", AssignmentStatus.ACCEPTED),
        ("EVA Specialist", "Hana", AssignmentStatus.ACCEPTED),
    ]
    assert all(
        e.crew.accepted_elsewhere == ()
        or all(c.mission_id != TELESCOPE for c in e.crew.accepted_elsewhere)
        for e in roster
    )


def test_roster_skips_closed_assignments(seeded_db, facts):
    seeded_db.execute(
        "UPDATE assignments SET status = 'withdrawn', reason = 'x'"
        " WHERE mission_id = 5 AND crew_profile_id = 13"
    )
    assert [e.crew.name for e in facts.roster(TELESCOPE)] == ["Chen", "Dana", "Eli"]


def test_assignment_facts_for_workload(facts):
    chen = facts.assignment_facts(8)
    assert {
        (f.mission_id, f.mission_status, f.assignment_status, f.window.mission_days) for f in chen
    } == {
        (TELESCOPE, MissionStatus.ACTIVE, AssignmentStatus.ACCEPTED, 5),
        (MARS, MissionStatus.COMPLETED, AssignmentStatus.COMPLETED, 30),
    }


def test_active_assignments_are_accepted_ones_on_active_missions(facts):
    [hana] = facts.active_assignments(13)
    assert (hana.mission_name, hana.slot_name) == ("Orbital Telescope Service", "EVA Specialist")
    assert [(r.skill_name, r.min_level) for r in hana.requirements] == [("EVA", 3)]
    assert facts.active_assignments(7) == []  # Ben's mission is only pending
    assert facts.active_assignments(8)[0].mission_id == TELESCOPE  # Mars Analog is completed


def test_commitments_are_accepted_assignments_on_unfinished_missions(facts):
    assert [c.mission_name for c in facts.commitments(13)] == ["Orbital Telescope Service"]
    assert [c.mission_name for c in facts.commitments(8)] == ["Orbital Telescope Service"]
    assert facts.commitments(11) == []
