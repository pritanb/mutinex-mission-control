import random
from dataclasses import replace

from builders import (
    ANA,
    ASTEROID_SLOTS,
    ASTEROID_WINDOW,
    AURORA_CREW,
    CHEN,
    COMMANDER,
    DANA,
    ELI,
    EVA,
    FAY,
    FLIGHT_ENGINEER,
    GATEWAY_SLOTS,
    GATEWAY_WINDOW,
    GEOLOGIST,
    GEOLOGY,
    GUS,
    LEADERSHIP,
    PILOT,
    PILOTING,
    SPECIALIST,
    SYS_ENG,
    crew,
    date_range,
    req,
    slot,
)
from mission_control.domain.eligibility import is_eligible
from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster
from mission_control.domain.records import Commitment

# PRD §9.1 Aurora seed crew, Lunar Gateway Resupply and Asteroid Survey come from builders.


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
        crew, slots = list(AURORA_CREW), list(GATEWAY_SLOTS)
        shuffler.shuffle(crew)
        shuffler.shuffle(slots)
        assert suggest_roster(slots, crew, GATEWAY_WINDOW) == expected


def test_ac19_s3_asteroid_survey_pilot_is_ana_and_geologist_unfilled():
    s = suggest_roster(ASTEROID_SLOTS, AURORA_CREW, ASTEROID_WINDOW)
    assert roster(s) == {PILOT.id: [ANA.crew_profile_id]}
    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)


def test_ac19_s3b_ana_accepting_gateway_moves_pilot_to_eli():
    gateway = Commitment(1, "Lunar Gateway Resupply", GATEWAY_WINDOW)
    ana_committed = replace(ANA, workload=10, accepted_elsewhere=(gateway,))
    crew = [ana_committed if c is ANA else c for c in AURORA_CREW]
    s = suggest_roster(ASTEROID_SLOTS, crew, ASTEROID_WINDOW)
    assert roster(s) == {PILOT.id: [ELI.crew_profile_id]}
    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)


# --- Each tie-break on its own -----------------------------------------------------------

ONE_SKILL = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=1)
WINDOW = date_range("2027-06-01", "2027-06-05")


def test_lowest_workload_wins():
    busy = crew("Busy", 1, skills={SYS_ENG: 5}, workload=20)
    free = crew("Free", 2, skills={SYS_ENG: 3}, workload=5)
    s = suggest_roster([ONE_SKILL], [busy, free], WINDOW)
    assert s.placements == (Placement(1, 2),)


def test_on_equal_workload_higher_proficiency_wins():
    low = crew("Low", 1, skills={SYS_ENG: 3}, workload=5)
    high = crew("High", 2, skills={SYS_ENG: 4}, workload=5)
    assert suggest_roster([ONE_SKILL], [low, high], WINDOW).placements == (Placement(1, 2),)


def test_proficiency_is_the_sum_across_the_slots_required_skills():
    commander = slot(
        req(PILOTING, 4), req(LEADERSHIP, 3), id=1, position=1, name="Commander", open_places=1
    )
    a = crew("A", 1, skills={PILOTING: 5, LEADERSHIP: 3})  # 8
    b = crew("B", 2, skills={PILOTING: 4, LEADERSHIP: 5})  # 9
    assert suggest_roster([commander], [a, b], WINDOW).placements == (Placement(1, 2),)


def test_skills_the_slot_does_not_require_do_not_count_towards_proficiency():
    a = crew("A", 1, skills={SYS_ENG: 4, EVA: 5, GEOLOGY: 5})
    b = crew("B", 2, skills={SYS_ENG: 5})
    assert suggest_roster([ONE_SKILL], [a, b], WINDOW).placements == (Placement(1, 2),)


def test_on_equal_workload_and_proficiency_lowest_id_wins():
    later = crew("Later", 9, skills={SYS_ENG: 4}, workload=5)
    earlier = crew("Earlier", 3, skills={SYS_ENG: 4}, workload=5)
    assert suggest_roster([ONE_SKILL], [later, earlier], WINDOW).placements == (Placement(1, 3),)


def test_slots_with_equal_candidate_counts_go_in_listed_position():
    first = slot(req(SYS_ENG, 3), id=7, position=1, name="First", open_places=1)
    second = slot(req(SYS_ENG, 3), id=5, position=2, name="Second", open_places=1)
    a = crew("A", 1, skills={SYS_ENG: 4})
    b = crew("B", 2, skills={SYS_ENG: 4})
    s = suggest_roster([second, first], [a, b], WINDOW)
    # "First" (position 1) picks before "Second", so it gets the better-ranked person (A)
    assert s.placements == (Placement(7, 1), Placement(5, 2))


def test_slots_with_equal_count_and_position_fall_back_to_slot_id():
    a_slot = slot(req(SYS_ENG, 3), id=8, position=1, name="A", open_places=1)
    b_slot = slot(req(SYS_ENG, 3), id=4, position=1, name="B", open_places=1)
    x, y = crew("X", 1, skills={SYS_ENG: 4}), crew("Y", 2, skills={SYS_ENG: 4})
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
        [*GATEWAY_SLOTS, slot(req(PILOTING, 1), id=24, position=4, name="Extra", open_places=5)],
        [*AURORA_CREW, crew("Gone", 99, skills={PILOTING: 5}, active=False)],
        GATEWAY_WINDOW,
    )
    placed = {p.crew_profile_id for p in s.placements}
    assert not placed & {FAY.crew_profile_id, GUS.crew_profile_id, 99}


def test_multi_place_slot_takes_several_people_in_rank_order():
    engineer = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=2)
    candidates = [
        crew("A", 1, skills={SYS_ENG: 3}, workload=9),
        crew("B", 2, skills={SYS_ENG: 3}, workload=1),
        crew("C", 3, skills={SYS_ENG: 3}, workload=5),
    ]
    assert suggest_roster([engineer], candidates, WINDOW).placements == (
        Placement(1, 2),
        Placement(1, 3),
    )


def test_places_left_when_candidates_run_out_are_marked_unfilled():
    engineer = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=3)
    s = suggest_roster([engineer], [crew("A", 1, skills={SYS_ENG: 3})], WINDOW)
    assert s.placements == (Placement(1, 1),)
    assert s.unfilled == (Unfilled(1, 2),)


def test_slots_without_open_places_are_ignored():
    full = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=0)
    s = suggest_roster([full], [crew("A", 1, skills={SYS_ENG: 3})], WINDOW)
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
    x = slot(req(SYS_ENG, 1), id=1, position=1, name="X", open_places=2)  # candidates: A, B
    y = slot(req(EVA, 1), id=2, position=2, name="Y", open_places=1)  # candidates: C, D
    w = slot(req(GEOLOGY, 1), id=3, position=3, name="W", open_places=1)  # candidates: B, D
    a = crew("A", 1, skills={SYS_ENG: 1})
    b = crew("B", 2, skills={SYS_ENG: 1, GEOLOGY: 1})
    c = crew("C", 3, skills={EVA: 1}, workload=9)
    d_ = crew("D", 4, skills={EVA: 1, GEOLOGY: 1})
    s = suggest_roster([x, y, w], [a, b, c, d_], WINDOW)
    assert roster(s) == {1: [1, 2], 3: [4], 2: [3]}
    assert s.unfilled == ()
