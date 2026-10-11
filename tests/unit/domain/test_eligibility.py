from dataclasses import replace
from datetime import date

import pytest

from builders import (
    ANA,
    BEN,
    CHEN,
    COMMANDER,
    ELI,
    EVA,
    FAY,
    GUS,
    LEADERSHIP,
    PILOTING,
    SYS_ENG,
    commitment,
    crew,
    date_range,
    req,
    roster_entry,
    slot,
)
from builders import GATEWAY_WINDOW as GATEWAY
from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import (
    DatesEdit,
    SlotEdit,
    SlotRemoval,
    ineligibility_reasons,
    invalidated_by,
    invalidated_by_skill_change,
    is_eligible,
    workload,
)
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem
from mission_control.domain.records import ActiveAssignment, AssignmentFact

# Seed people, skills, the Gateway window (1–10 Mar 2027) and its Commander slot
# (Piloting ≥4, Leadership ≥3) come from builders (PRD §9.1).


# Eligibility: one test per reason (PRD §5.1 "Eligible")


def test_eligible_when_every_condition_holds():
    assert is_eligible(ANA, COMMANDER, GATEWAY)
    assert ineligibility_reasons(ANA, COMMANDER, GATEWAY) == []


def test_inactive_person_is_not_eligible():
    ana = replace(ANA, active=False)
    [problem] = ineligibility_reasons(ana, COMMANDER, GATEWAY)
    assert problem.code == "inactive"
    assert "Ana" in problem.message


def test_skill_below_minimum_is_not_eligible():
    # PRD S2: Eli has Leadership 2, Commander needs 3
    [problem] = ineligibility_reasons(ELI, COMMANDER, GATEWAY)
    assert problem.code == "skill_below_minimum"
    assert "Eli" in problem.message and "Leadership" in problem.message
    assert problem.refs["skill_id"] == LEADERSHIP


def test_missing_skill_is_not_eligible():
    dana = crew(name="Dana", skills={EVA: 4})
    problems = ineligibility_reasons(dana, COMMANDER, GATEWAY)
    assert {p.code for p in problems} == {"skill_below_minimum"}
    assert {p.refs["skill_id"] for p in problems} == {PILOTING, LEADERSHIP}


def test_skill_exactly_at_minimum_is_eligible():
    assert is_eligible(crew(skills={PILOTING: 4, LEADERSHIP: 3}), COMMANDER, GATEWAY)


def test_unavailability_overlapping_the_mission_is_not_eligible():
    # PRD S2: Fay is unavailable 5–8 Mar
    [problem] = ineligibility_reasons(FAY, COMMANDER, GATEWAY)
    assert problem.code == "unavailable"
    assert "Fay" in problem.message


def test_ac17_unavailability_on_the_boundary_day_is_not_eligible():
    fay = replace(FAY, unavailable=(date_range("2027-03-10", "2027-03-12"),))
    assert not is_eligible(fay, COMMANDER, GATEWAY)


def test_overlapping_accepted_assignment_elsewhere_is_not_eligible_and_names_the_mission():
    # PRD S2 / S4: Gus has accepted Station Reboost, 25 Feb – 2 Mar
    [problem] = ineligibility_reasons(GUS, slot(req(SYS_ENG, 3), name="Flight Engineer"), GATEWAY)
    assert problem.code == "overlap"
    assert "Gus" in problem.message and "Station Reboost" in problem.message
    # the message gives the overlapping days (1–2 Mar), not the whole other mission
    assert "2027-03-01" in problem.message and "2027-03-02" in problem.message
    assert problem.refs["mission_id"] == 3


def test_non_overlapping_commitments_do_not_block():
    telescope = commitment(5, "Orbital Telescope Service", "2027-01-10", "2027-01-14")
    chen = replace(
        CHEN,
        accepted_elsewhere=(telescope,),
        unavailable=(date_range("2027-04-01", "2027-04-02"),),
    )
    assert is_eligible(chen, slot(req(SYS_ENG, 3)), GATEWAY)


def test_all_reasons_are_reported_together():
    reboost = commitment(3, "Station Reboost", "2027-02-25", "2027-03-02")
    person = crew(
        active=False,
        skills={},
        accepted_elsewhere=[reboost],
        unavailable=[date_range("2027-03-05", "2027-03-05")],
    )
    codes = [p.code for p in ineligibility_reasons(person, slot(req(SYS_ENG, 3)), GATEWAY)]
    assert sorted(codes) == ["inactive", "overlap", "skill_below_minimum", "unavailable"]


# Workload (PRD §6, AC-20)


def fact(
    *,
    mission_id: int,
    days: int,
    mission_status=MissionStatus.ACTIVE,
    status=AssignmentStatus.ACCEPTED,
) -> AssignmentFact:
    start = date(2027, 1, 1)
    window = DateRange(start, date.fromordinal(start.toordinal() + days - 1))
    return AssignmentFact(
        mission_id=mission_id,
        mission_status=mission_status,
        assignment_status=status,
        window=window,
    )


def test_ac20_chen_workload_counts_telescope_but_not_completed_mars_analog():
    telescope = fact(mission_id=105, days=5, mission_status=MissionStatus.ACTIVE)
    mars_analog = fact(
        mission_id=107,
        days=30,
        mission_status=MissionStatus.COMPLETED,
        status=AssignmentStatus.COMPLETED,
    )
    assert workload([telescope, mars_analog], excluding_mission_id=101) == 5


def test_ac20_accepted_on_a_completed_mission_does_not_count():
    facts = [fact(mission_id=107, days=30, mission_status=MissionStatus.COMPLETED)]
    assert workload(facts, excluding_mission_id=101) == 0


def test_workload_counts_accepted_on_every_non_completed_mission_state():
    facts = [
        fact(mission_id=102, days=1, mission_status=MissionStatus.DRAFT),
        fact(mission_id=103, days=2, mission_status=MissionStatus.PENDING_APPROVAL),
        fact(mission_id=104, days=4, mission_status=MissionStatus.ACTIVE),
    ]
    assert workload(facts, excluding_mission_id=199) == 7


def test_workload_ignores_assignments_that_are_not_accepted():
    facts = [
        fact(mission_id=102, days=3, status=s)
        for s in AssignmentStatus
        if s != AssignmentStatus.ACCEPTED
    ]
    assert workload(facts, excluding_mission_id=199) == 0


def test_workload_excludes_the_mission_being_matched():
    facts = [fact(mission_id=101, days=10), fact(mission_id=102, days=5)]
    assert workload(facts, excluding_mission_id=101) == 5


# Edits that would invalidate open assignments (PRD M7)


def test_m7_removing_a_slot_with_open_assignments_is_refused():
    [problem] = invalidated_by(SlotRemoval(slot_id=COMMANDER.id), [roster_entry(ANA, COMMANDER)])
    assert problem.code == "slot_has_open_assignments"
    assert "Ana" in problem.message and "Commander" in problem.message


def test_m7_removing_a_slot_without_open_assignments_is_allowed():
    other = slot(req(EVA, 3), name="Specialist", id=11)
    assert invalidated_by(SlotRemoval(slot_id=other.id), [roster_entry(ANA, COMMANDER)]) == []


def test_m7_lowering_headcount_below_open_assignments_is_refused():
    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12, open_places=0)
    assignments = [roster_entry(GUS, engineers, 1), roster_entry(CHEN, engineers, 2)]
    problems = invalidated_by(SlotEdit(slot_id=12, headcount=1), assignments)
    assert [p.code for p in problems] == ["headcount_below_open_assignments"]
    assert "Engineer" in problems[0].message


def test_m7_lowering_headcount_to_exactly_the_open_assignments_is_allowed():
    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12)
    assert invalidated_by(SlotEdit(slot_id=12, headcount=1), [roster_entry(GUS, engineers)]) == []


def test_m7_raising_requirements_above_an_assignees_level_is_refused():
    edit = SlotEdit(slot_id=COMMANDER.id, requirements=(req(PILOTING, 4), req(LEADERSHIP, 5)))
    [problem] = invalidated_by(edit, [roster_entry(ANA, COMMANDER)])
    assert problem.code == "skill_below_minimum"
    assert "Ana" in problem.message and "Commander" in problem.message


def test_m7_requirement_edit_on_another_slot_does_not_affect_this_one():
    edit = SlotEdit(slot_id=99, requirements=(req(LEADERSHIP, 5),))
    assert invalidated_by(edit, [roster_entry(ANA, COMMANDER)]) == []


def test_m7_moving_dates_onto_unavailability_is_refused():
    fay = replace(FAY, unavailable=(date_range("2027-04-01", "2027-04-03"),))
    edit = DatesEdit(window=date_range("2027-03-30", "2027-04-05"))
    [problem] = invalidated_by(edit, [roster_entry(fay, COMMANDER)])
    assert problem.code == "unavailable"
    assert "Fay" in problem.message and "Commander" in problem.message


def test_m7_moving_dates_onto_another_accepted_assignment_is_refused():
    comms = commitment(6, "Deep Space Comms Upgrade", "2027-04-01", "2027-04-20")
    ben = replace(BEN, accepted_elsewhere=(comms,))
    fe = slot(req(SYS_ENG, 3), name="Flight Engineer")
    [problem] = invalidated_by(
        DatesEdit(window=date_range("2027-04-15", "2027-04-25")), [roster_entry(ben, fe)]
    )
    assert problem.code == "overlap"
    assert "Deep Space Comms Upgrade" in problem.message


def test_m7_harmless_date_change_is_allowed():
    edit = DatesEdit(window=date_range("2027-03-02", "2027-03-11"))
    assert invalidated_by(edit, [roster_entry(ANA, COMMANDER)]) == []


def test_m7_every_affected_assignment_is_listed():
    fe = slot(req(SYS_ENG, 3), name="Flight Engineer", id=11)
    blocked = (date_range("2027-05-01", "2027-05-02"),)
    a = roster_entry(replace(ANA, unavailable=blocked), COMMANDER, 1)
    b = roster_entry(replace(CHEN, unavailable=blocked), fe, 2)
    problems = invalidated_by(DatesEdit(window=date_range("2027-05-01", "2027-05-05")), [a, b])
    assert [p.refs["assignment_id"] for p in problems] == [1, 2]


# Skill changes against Active assignments (PRD P3)


TELESCOPE_EVA = ActiveAssignment(
    mission_id=5,
    mission_name="Orbital Telescope Service",
    slot_name="EVA Specialist",
    requirements=(req(EVA, 3),),
)


def test_p3_lowering_a_skill_below_an_active_assignments_requirement_is_refused():
    [problem] = invalidated_by_skill_change("Hana", EVA, 2, [TELESCOPE_EVA])
    assert problem.code == "invalidates_active_assignment"
    assert "Hana" in problem.message and "Orbital Telescope Service" in problem.message
    assert problem.refs["mission_id"] == 5


def test_p3_removing_a_skill_needed_by_an_active_assignment_is_refused():
    assert invalidated_by_skill_change("Hana", EVA, None, [TELESCOPE_EVA])


def test_p3_change_that_still_meets_the_requirement_is_allowed():
    assert invalidated_by_skill_change("Hana", EVA, 3, [TELESCOPE_EVA]) == []


def test_p3_change_to_a_skill_the_active_slot_does_not_require_is_allowed():
    assert invalidated_by_skill_change("Hana", PILOTING, None, [TELESCOPE_EVA]) == []


def test_p3_without_active_assignments_any_change_is_allowed():
    # Draft and Pending assignments never block; the caller passes only Active ones
    assert invalidated_by_skill_change("Hana", EVA, None, []) == []


# Regression: M7 refusals must list the affected crew


def test_m7_headcount_refusal_names_every_assigned_person():
    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12)
    [problem] = invalidated_by(
        SlotEdit(slot_id=12, headcount=1),
        [roster_entry(GUS, engineers, 1), roster_entry(CHEN, engineers, 2)],
    )
    assert "Gus" in problem.message and "Chen" in problem.message
    # Gus (12) then Chen (8): assignment order, not id order
    assert problem.refs["crew_profile_ids"] == [12, 8]


# Regression: a dates edit only reports availability conflicts


def test_m7_dates_edit_reports_only_unavailability_and_overlap():
    # inactive, no skills, and unavailable on the new dates: only "unavailable" applies to a
    # date change
    person = crew(
        name="Ivy",
        active=False,
        skills={},
        unavailable=[date_range("2027-04-01", "2027-04-01")],
    )
    problems = invalidated_by(
        DatesEdit(window=date_range("2027-04-01", "2027-04-02")),
        [roster_entry(person, COMMANDER)],
    )
    assert [p.code for p in problems] == ["unavailable"]


# Regression: problems never share or expose a mutable refs mapping


def test_problems_from_one_check_do_not_share_refs():
    person = crew(id=1, active=False, skills={})
    first, second, *_ = ineligibility_reasons(person, COMMANDER, GATEWAY)
    assert first.refs is not second.refs
    assert first.refs == {"crew_profile_id": 1, "slot_id": COMMANDER.id}


def test_problem_refs_cannot_be_mutated():
    [problem] = ineligibility_reasons(replace(ANA, active=False), COMMANDER, GATEWAY)
    with pytest.raises(TypeError):
        problem.refs["slot_id"] = 99  # type: ignore[index]
    assert problem.refs["slot_id"] == COMMANDER.id


def test_problem_copies_the_refs_it_is_given():
    refs = {"slot_id": 1}
    problem = Problem("x", "y", refs)
    refs["slot_id"] = 2
    assert problem.refs == {"slot_id": 1}
