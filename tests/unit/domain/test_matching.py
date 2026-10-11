import random
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import is_eligible
from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster
from mission_control.domain.records import CandidateFacts, Commitment, Requirement, SlotSpec

# --- PRD §9.1 Aurora seed, expressed as matcher inputs ------------------------------------

PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY = 1, 2, 3, 4, 5
SKILL = {
    PILOTING: "Piloting",
    LEADERSHIP: "Leadership",
    SYS_ENG: "Systems Eng",
    EVA: "EVA",
    GEOLOGY: "Geology",
}


def req(skill_id: int, min_level: int) -> Requirement:
    return Requirement(skill_id, SKILL[skill_id], min_level)


def rng(start: str, end: str) -> DateRange:
    return DateRange(date.fromisoformat(start), date.fromisoformat(end))


def person(id, name, skills, workload=0, unavailable=(), accepted_elsewhere=(), active=True):
    return CandidateFacts(
        crew_profile_id=id,
        name=name,
        active=active,
        skills=skills,
        unavailable=tuple(unavailable),
        accepted_elsewhere=tuple(accepted_elsewhere),
        workload=workload,
    )


STATION_REBOOST = Commitment(3, "Station Reboost", rng("2027-02-25", "2027-03-02"))

# IDs follow the PRD §9 table order (the stable identifier used for the last tie-break).
ANA = person(6, "Ana", {PILOTING: 5, LEADERSHIP: 4, SYS_ENG: 4}, workload=0)
BEN = person(7, "Ben", {SYS_ENG: 4, EVA: 3}, workload=20)
CHEN = person(8, "Chen", {SYS_ENG: 3}, workload=5)
DANA = person(9, "Dana", {EVA: 4}, workload=5)
ELI = person(10, "Eli", {EVA: 4, PILOTING: 4, LEADERSHIP: 2}, workload=5)
FAY = person(11, "Fay", {PILOTING: 4, LEADERSHIP: 4}, unavailable=[rng("2027-03-05", "2027-03-08")])
GUS = person(12, "Gus", {SYS_ENG: 5}, workload=6, accepted_elsewhere=[STATION_REBOOST])
HANA = person(13, "Hana", {EVA: 3, GEOLOGY: 2}, workload=5)
AURORA_CREW = [ANA, BEN, CHEN, DANA, ELI, FAY, GUS, HANA]

# Lunar Gateway Resupply, 1–10 Mar 2027. Slots listed Flight Engineer first, as in the PRD.
GATEWAY_WINDOW = rng("2027-03-01", "2027-03-10")
FLIGHT_ENGINEER = SlotSpec(21, 1, "Flight Engineer", 1, (req(SYS_ENG, 3),))
SPECIALIST = SlotSpec(22, 2, "Mission Specialist", 1, (req(EVA, 3),))
COMMANDER = SlotSpec(23, 3, "Commander", 1, (req(PILOTING, 4), req(LEADERSHIP, 3)))
GATEWAY_SLOTS = [FLIGHT_ENGINEER, SPECIALIST, COMMANDER]

# Asteroid Survey, 5–12 Mar 2027.
ASTEROID_WINDOW = rng("2027-03-05", "2027-03-12")
PILOT = SlotSpec(31, 1, "Pilot", 1, (req(PILOTING, 4),))
GEOLOGIST = SlotSpec(32, 2, "Geologist", 1, (req(GEOLOGY, 4),))
ASTEROID_SLOTS = [PILOT, GEOLOGIST]


def roster(s: Suggestion) -> dict[int, list[int]]:
    """slot_id -> crew ids placed there, in pick order."""
    out: dict[int, list[int]] = {}
    for p in s.placements:
        out.setdefault(p.slot_id, []).append(p.crew_profile_id)
    return out


# --- PRD scenarios -----------------------------------------------------------------------


def test_s2_gateway_roster_is_ana_chen_dana():
    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
    assert roster(s) == {
        COMMANDER.id: [ANA.crew_profile_id],
        FLIGHT_ENGINEER.id: [CHEN.crew_profile_id],
        SPECIALIST.id: [DANA.crew_profile_id],
    }
    assert s.unfilled == ()


def test_s2_commander_is_filled_first_because_it_is_most_constrained():
    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
    assert s.placements[0] == Placement(COMMANDER.id, ANA.crew_profile_id)


def test_s2_listed_order_would_have_left_commander_unfilled():
    # The counterfactual from the PRD: filling Flight Engineer first gives it Ana (workload 0),
    # and then nobody eligible is left for Commander. Most-constrained-first avoids this.
    only_fe = suggest_roster([FLIGHT_ENGINEER], AURORA_CREW, GATEWAY_WINDOW)
    assert only_fe.placements == (Placement(FLIGHT_ENGINEER.id, ANA.crew_profile_id),)
    without_ana = [c for c in AURORA_CREW if c is not ANA]
    assert suggest_roster([COMMANDER], without_ana, GATEWAY_WINDOW).unfilled == (
        Unfilled(COMMANDER.id, 1),
    )


def test_ac18_s2_is_identical_on_every_run():
    first = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
    for _ in range(20):
        assert suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW) == first


def test_ac18_input_order_does_not_change_the_result():
    expected = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
    shuffler = random.Random(42)
    for _ in range(20):
        crew, slots = AURORA_CREW[:], GATEWAY_SLOTS[:]
        shuffler.shuffle(crew)
        shuffler.shuffle(slots)
        assert suggest_roster(slots, crew, GATEWAY_WINDOW) == expected


def test_ac19_s3_asteroid_survey_pilot_is_ana_and_geologist_unfilled():
    s = suggest_roster(ASTEROID_SLOTS, AURORA_CREW, ASTEROID_WINDOW)
    assert roster(s) == {PILOT.id: [ANA.crew_profile_id]}
    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)


def test_ac19_s3b_ana_accepting_gateway_moves_pilot_to_eli():
    gateway = Commitment(1, "Lunar Gateway Resupply", GATEWAY_WINDOW)
    ana_committed = person(6, "Ana", ANA.skills, workload=10, accepted_elsewhere=[gateway])
    crew = [ana_committed if c is ANA else c for c in AURORA_CREW]
    s = suggest_roster(ASTEROID_SLOTS, crew, ASTEROID_WINDOW)
    assert roster(s) == {PILOT.id: [ELI.crew_profile_id]}
    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)


# --- Each tie-break on its own -----------------------------------------------------------

ONE_SKILL = SlotSpec(1, 1, "Engineer", 1, (req(SYS_ENG, 3),))
WINDOW = rng("2027-06-01", "2027-06-05")


def test_lowest_workload_wins():
    busy = person(1, "Busy", {SYS_ENG: 5}, workload=20)
    free = person(2, "Free", {SYS_ENG: 3}, workload=5)
    s = suggest_roster([ONE_SKILL], [busy, free], WINDOW)
    assert s.placements == (Placement(1, 2),)


def test_on_equal_workload_higher_proficiency_wins():
    low = person(1, "Low", {SYS_ENG: 3}, workload=5)
    high = person(2, "High", {SYS_ENG: 4}, workload=5)
    assert suggest_roster([ONE_SKILL], [low, high], WINDOW).placements == (Placement(1, 2),)


def test_proficiency_is_the_sum_across_the_slots_required_skills():
    slot = SlotSpec(1, 1, "Commander", 1, (req(PILOTING, 4), req(LEADERSHIP, 3)))
    a = person(1, "A", {PILOTING: 5, LEADERSHIP: 3})  # 8
    b = person(2, "B", {PILOTING: 4, LEADERSHIP: 5})  # 9
    assert suggest_roster([slot], [a, b], WINDOW).placements == (Placement(1, 2),)


def test_skills_the_slot_does_not_require_do_not_count_towards_proficiency():
    a = person(1, "A", {SYS_ENG: 4, EVA: 5, GEOLOGY: 5})
    b = person(2, "B", {SYS_ENG: 5})
    assert suggest_roster([ONE_SKILL], [a, b], WINDOW).placements == (Placement(1, 2),)


def test_on_equal_workload_and_proficiency_lowest_id_wins():
    later = person(9, "Later", {SYS_ENG: 4}, workload=5)
    earlier = person(3, "Earlier", {SYS_ENG: 4}, workload=5)
    assert suggest_roster([ONE_SKILL], [later, earlier], WINDOW).placements == (Placement(1, 3),)


def test_slots_with_equal_candidate_counts_go_in_listed_position():
    first = SlotSpec(7, 1, "First", 1, (req(SYS_ENG, 3),))
    second = SlotSpec(5, 2, "Second", 1, (req(SYS_ENG, 3),))
    a = person(1, "A", {SYS_ENG: 4})
    b = person(2, "B", {SYS_ENG: 4})
    s = suggest_roster([second, first], [a, b], WINDOW)
    # "First" (position 1) picks before "Second", so it gets the better-ranked person (A)
    assert s.placements == (Placement(7, 1), Placement(5, 2))


def test_slots_with_equal_count_and_position_fall_back_to_slot_id():
    a_slot = SlotSpec(8, 1, "A", 1, (req(SYS_ENG, 3),))
    b_slot = SlotSpec(4, 1, "B", 1, (req(SYS_ENG, 3),))
    x, y = person(1, "X", {SYS_ENG: 4}), person(2, "Y", {SYS_ENG: 4})
    assert suggest_roster([a_slot, b_slot], [x, y], WINDOW).placements[0].slot_id == 4


# --- Structural guarantees ---------------------------------------------------------------


def test_ac21_nobody_is_placed_in_two_slots():
    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
    ids = [p.crew_profile_id for p in s.placements]
    assert len(ids) == len(set(ids))


def test_ac21_every_placement_is_eligible_for_its_slot():
    by_id = {c.crew_profile_id: c for c in AURORA_CREW}
    slots = {sl.id: sl for sl in GATEWAY_SLOTS + ASTEROID_SLOTS}
    for slot_list, window in [(GATEWAY_SLOTS, GATEWAY_WINDOW), (ASTEROID_SLOTS, ASTEROID_WINDOW)]:
        for p in suggest_roster(slot_list, AURORA_CREW, window).placements:
            assert is_eligible(by_id[p.crew_profile_id], slots[p.slot_id], window)


def test_ac21_inactive_unavailable_and_overlapping_people_are_never_suggested():
    s = suggest_roster(
        GATEWAY_SLOTS + [SlotSpec(24, 4, "Extra", 5, (req(PILOTING, 1),))],
        AURORA_CREW + [person(99, "Gone", {PILOTING: 5}, active=False)],
        GATEWAY_WINDOW,
    )
    placed = {p.crew_profile_id for p in s.placements}
    assert not placed & {FAY.crew_profile_id, GUS.crew_profile_id, 99}


def test_multi_place_slot_takes_several_people_in_rank_order():
    slot = SlotSpec(1, 1, "Engineer", 2, (req(SYS_ENG, 3),))
    crew = [
        person(1, "A", {SYS_ENG: 3}, workload=9),
        person(2, "B", {SYS_ENG: 3}, workload=1),
        person(3, "C", {SYS_ENG: 3}, workload=5),
    ]
    assert suggest_roster([slot], crew, WINDOW).placements == (Placement(1, 2), Placement(1, 3))


def test_places_left_when_candidates_run_out_are_marked_unfilled():
    slot = SlotSpec(1, 1, "Engineer", 3, (req(SYS_ENG, 3),))
    s = suggest_roster([slot], [person(1, "A", {SYS_ENG: 3})], WINDOW)
    assert s.placements == (Placement(1, 1),)
    assert s.unfilled == (Unfilled(1, 2),)


def test_slots_without_open_places_are_ignored():
    full = SlotSpec(1, 1, "Engineer", 0, (req(SYS_ENG, 3),))
    s = suggest_roster([full], [person(1, "A", {SYS_ENG: 3})], WINDOW)
    assert s == Suggestion(placements=(), unfilled=())


def test_no_slots_or_no_candidates_gives_an_empty_or_unfilled_suggestion():
    assert suggest_roster([], AURORA_CREW, WINDOW) == Suggestion((), ())
    assert suggest_roster([ONE_SKILL], [], WINDOW) == Suggestion((), (Unfilled(1, 1),))


def test_candidate_counts_are_recounted_after_every_pick():
    # Every slot starts with 2 candidates, so they would be filled in listed order X, Y, W if
    # counts were only taken once:
    #   X (2 places) gets A and B; Y then picks D over C (D has lower workload); W is left with
    #   nobody, because its candidates were B and D.
    # Recounting after each pick notices that once B is gone W has only D left (1 candidate)
    # while Y still has C and D (2), so W picks D first and Y takes C. Every place is filled.
    x = SlotSpec(1, 1, "X", 2, (req(SYS_ENG, 1),))  # candidates: A, B
    y = SlotSpec(2, 2, "Y", 1, (req(EVA, 1),))  # candidates: C, D
    w = SlotSpec(3, 3, "W", 1, (req(GEOLOGY, 1),))  # candidates: B, D
    a = person(1, "A", {SYS_ENG: 1})
    b = person(2, "B", {SYS_ENG: 1, GEOLOGY: 1})
    c = person(3, "C", {EVA: 1}, workload=9)
    d_ = person(4, "D", {EVA: 1, GEOLOGY: 1})
    s = suggest_roster([x, y, w], [a, b, c, d_], WINDOW)
    assert roster(s) == {1: [1, 2], 3: [4], 2: [3]}
    assert s.unfilled == ()
