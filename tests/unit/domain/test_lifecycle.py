from datetime import date

import pytest

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus as A
from mission_control.domain.enums import MissionStatus as M
from mission_control.domain.lifecycle import (
    AssignmentAction,
    MissionAction,
    RosterEntry,
    assignment_problem,
    assignment_status_after,
    cascade,
    mission_status_after,
    mission_status_after_assignment_action,
    state_problem,
    submit_problems,
)
from mission_control.domain.records import CandidateFacts, Requirement, SlotSpec

WINDOW = DateRange(date(2027, 3, 1), date(2027, 3, 10))
EVA = Requirement(4, "EVA", 3)
ALL_STATUSES = list(M)


# --- Mission transition table -------------------------------------------------------------

ALLOWED = {
    MissionAction.SUBMIT: {M.DRAFT},
    MissionAction.APPROVE: {M.PENDING_APPROVAL},
    MissionAction.REJECT: {M.PENDING_APPROVAL},
    MissionAction.TRANSFER: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
    MissionAction.COMPLETE: {M.ACTIVE},
    MissionAction.CANCEL: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
    MissionAction.EDIT: {M.DRAFT, M.PENDING_APPROVAL},
}


@pytest.mark.parametrize("action", list(MissionAction))
@pytest.mark.parametrize("status", ALL_STATUSES)
def test_transition_table_allows_exactly_the_designed_states(action, status):
    problem = state_problem(status, action)
    if status in ALLOWED[action]:
        assert problem is None
    else:
        assert problem is not None


@pytest.mark.parametrize("action", list(MissionAction))
@pytest.mark.parametrize("status", [M.COMPLETED, M.CANCELLED])
def test_finished_missions_refuse_everything_with_mission_final(action, status):
    assert state_problem(status, action).code == "mission_final"


@pytest.mark.parametrize(
    "action",
    [MissionAction.EDIT, MissionAction.SUBMIT, MissionAction.APPROVE, MissionAction.REJECT],
)
def test_ac5_active_mission_refuses_changes_with_mission_frozen(action):
    assert state_problem(M.ACTIVE, action).code == "mission_frozen"


@pytest.mark.parametrize(
    "action", [MissionAction.COMPLETE, MissionAction.CANCEL, MissionAction.TRANSFER]
)
def test_ac5_active_mission_still_allows_complete_cancel_and_transfer(action):
    assert state_problem(M.ACTIVE, action) is None


@pytest.mark.parametrize(
    "status, action",
    [
        (M.DRAFT, MissionAction.APPROVE),
        (M.DRAFT, MissionAction.REJECT),
        (M.DRAFT, MissionAction.COMPLETE),
        (M.PENDING_APPROVAL, MissionAction.SUBMIT),
        (M.PENDING_APPROVAL, MissionAction.COMPLETE),
    ],
)
def test_wrong_state_in_draft_or_pending_is_invalid_transition(status, action):
    problem = state_problem(status, action)
    assert problem.code == "invalid_transition"
    assert status.value.replace("_", " ") in problem.message.lower()


def test_submit_moves_draft_to_pending():
    assert mission_status_after(M.DRAFT, MissionAction.SUBMIT) == M.PENDING_APPROVAL


def test_ac3_approval_before_quorum_stays_pending_and_at_quorum_goes_active():
    assert (
        mission_status_after(M.PENDING_APPROVAL, MissionAction.APPROVE, reaches_quorum=False)
        == M.PENDING_APPROVAL
    )
    assert (
        mission_status_after(M.PENDING_APPROVAL, MissionAction.APPROVE, reaches_quorum=True)
        == M.ACTIVE
    )


def test_reject_returns_to_draft():
    assert mission_status_after(M.PENDING_APPROVAL, MissionAction.REJECT) == M.DRAFT


def test_ac4_any_change_to_a_pending_mission_returns_it_to_draft():
    assert mission_status_after(M.PENDING_APPROVAL, MissionAction.EDIT) == M.DRAFT
    assert mission_status_after(M.DRAFT, MissionAction.EDIT) == M.DRAFT


def test_m1_transfer_sends_pending_back_to_draft_but_leaves_draft_and_active_alone():
    assert mission_status_after(M.PENDING_APPROVAL, MissionAction.TRANSFER) == M.DRAFT
    assert mission_status_after(M.DRAFT, MissionAction.TRANSFER) == M.DRAFT
    assert mission_status_after(M.ACTIVE, MissionAction.TRANSFER) == M.ACTIVE


def test_complete_and_cancel_reach_final_states():
    assert mission_status_after(M.ACTIVE, MissionAction.COMPLETE) == M.COMPLETED
    for s in (M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE):
        assert mission_status_after(s, MissionAction.CANCEL) == M.CANCELLED


def test_status_after_refuses_a_transition_the_table_does_not_allow():
    with pytest.raises(ValueError):
        mission_status_after(M.DRAFT, MissionAction.COMPLETE)


# --- Assignment transitions ---------------------------------------------------------------

ASSIGNMENT_CASES = [
    # action, assignment status, allowed mission states
    (AssignmentAction.PROPOSE, None, {M.DRAFT, M.PENDING_APPROVAL}),
    (AssignmentAction.ACCEPT, A.PROPOSED, {M.DRAFT}),
    (AssignmentAction.DECLINE, A.PROPOSED, {M.DRAFT}),
    (AssignmentAction.WITHDRAW, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
    (AssignmentAction.REMOVE, A.PROPOSED, {M.DRAFT, M.PENDING_APPROVAL}),
    (AssignmentAction.REMOVE, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
]


@pytest.mark.parametrize("action, current, allowed", ASSIGNMENT_CASES)
@pytest.mark.parametrize("mission", ALL_STATUSES)
def test_assignment_actions_only_in_allowed_mission_states(action, current, allowed, mission):
    problem = assignment_problem(action, current, mission)
    assert (problem is None) == (mission in allowed)


def test_ac5_active_mission_refuses_assignment_changes_with_mission_frozen():
    for action, current, _ in ASSIGNMENT_CASES:
        assert assignment_problem(action, current, M.ACTIVE).code == "mission_frozen"


@pytest.mark.parametrize(
    "action, current",
    [
        (AssignmentAction.ACCEPT, A.ACCEPTED),
        (AssignmentAction.DECLINE, A.ACCEPTED),
        (AssignmentAction.WITHDRAW, A.PROPOSED),
        (AssignmentAction.REMOVE, A.DECLINED),
        (AssignmentAction.ACCEPT, A.WITHDRAWN),
    ],
)
def test_assignment_action_from_the_wrong_assignment_status_is_invalid(action, current):
    assert assignment_problem(action, current, M.DRAFT).code == "invalid_transition"


def test_assignment_status_after_each_action():
    assert assignment_status_after(AssignmentAction.PROPOSE) == A.PROPOSED
    assert assignment_status_after(AssignmentAction.ACCEPT) == A.ACCEPTED
    assert assignment_status_after(AssignmentAction.DECLINE) == A.DECLINED
    assert assignment_status_after(AssignmentAction.WITHDRAW) == A.WITHDRAWN
    assert assignment_status_after(AssignmentAction.REMOVE) == A.REMOVED


@pytest.mark.parametrize(
    "action", [AssignmentAction.PROPOSE, AssignmentAction.WITHDRAW, AssignmentAction.REMOVE]
)
def test_ac4_roster_changes_send_a_pending_mission_back_to_draft(action):
    assert mission_status_after_assignment_action(M.PENDING_APPROVAL, action) == M.DRAFT
    assert mission_status_after_assignment_action(M.DRAFT, action) == M.DRAFT


@pytest.mark.parametrize("action", [AssignmentAction.ACCEPT, AssignmentAction.DECLINE])
def test_responding_to_a_proposal_does_not_change_the_mission(action):
    assert mission_status_after_assignment_action(M.DRAFT, action) == M.DRAFT


def test_cascade_on_complete_turns_accepted_into_completed():
    assert cascade(M.COMPLETED, A.ACCEPTED) == A.COMPLETED


def test_cascade_on_cancel_turns_open_assignments_into_cancelled():
    assert cascade(M.CANCELLED, A.PROPOSED) == A.CANCELLED
    assert cascade(M.CANCELLED, A.ACCEPTED) == A.CANCELLED


def test_cascade_leaves_closed_assignments_alone():
    for closed in (A.DECLINED, A.WITHDRAWN, A.REMOVED):
        assert cascade(M.CANCELLED, closed) == closed
        assert cascade(M.COMPLETED, closed) == closed


# --- Submit guard (AC-2, AC-12) -----------------------------------------------------------


def slot(id, name, open_places):
    return SlotSpec(id=id, position=id, name=name, open_places=open_places, requirements=(EVA,))


def entry(assignment_id, slot_spec, name, status=A.ACCEPTED, eva=4, unavailable=()):
    crew = CandidateFacts(
        crew_profile_id=assignment_id,
        name=name,
        active=True,
        skills={EVA.skill_id: eva},
        unavailable=tuple(unavailable),
        accepted_elsewhere=(),
        workload=0,
    )
    return RosterEntry(assignment_id=assignment_id, slot=slot_spec, crew=crew, status=status)


def test_complete_accepted_roster_with_enough_approvers_can_be_submitted():
    s = slot(1, "Specialist", 0)
    assert (
        submit_problems(
            [s], [entry(1, s, "Dana")], WINDOW, eligible_approvers=2, approvals_required=2
        )
        == []
    )


def test_ac2_every_problem_is_reported_at_once():
    commander = slot(1, "Commander", 1)  # nobody assigned yet
    specialist = slot(2, "Specialist", 0)
    roster = [
        entry(1, specialist, "Dana", status=A.PROPOSED),
        entry(2, specialist, "Hana", eva=2),
    ]  # accepted but no longer qualifies
    problems = submit_problems(
        [commander, specialist], roster, WINDOW, eligible_approvers=1, approvals_required=2
    )
    codes = [p.code for p in problems]
    assert codes == [
        "slot_unfilled",
        "proposal_unanswered",
        "skill_below_minimum",
        "insufficient_approvers",
    ]


def test_ac2_unfilled_place_message_names_the_slot_and_count():
    [p] = submit_problems([slot(1, "Commander", 1)], [], WINDOW, 2, 2)
    assert p.code == "slot_unfilled"
    assert "Commander" in p.message and p.refs["slot_id"] == 1


def test_ac2_unanswered_proposal_names_the_person_and_slot():
    s = slot(1, "Specialist", 0)
    [p] = submit_problems([s], [entry(7, s, "Dana", status=A.PROPOSED)], WINDOW, 2, 2)
    assert p.code == "proposal_unanswered"
    assert "Dana" in p.message and "Specialist" in p.message
    assert p.refs["assignment_id"] == 7


def test_roster_member_who_became_unavailable_blocks_submission():
    s = slot(1, "Specialist", 0)
    leave = [DateRange(date(2027, 3, 5), date(2027, 3, 6))]
    [p] = submit_problems([s], [entry(1, s, "Fay", unavailable=leave)], WINDOW, 2, 2)
    assert p.code == "unavailable"


def test_ac12_too_few_eligible_approvers_blocks_submission():
    s = slot(1, "Flight Surgeon", 0)
    [p] = submit_problems(
        [s], [entry(1, s, "Marco")], WINDOW, eligible_approvers=1, approvals_required=2
    )
    assert p.code == "insufficient_approvers"
    assert "1" in p.message and "2" in p.message


# Regression: refusal wording reads naturally


@pytest.mark.parametrize(
    "status, action, message",
    [
        (M.DRAFT, MissionAction.APPROVE, "Can't approve a mission in draft"),
        (M.PENDING_APPROVAL, MissionAction.SUBMIT, "Can't submit a mission pending approval"),
        (M.ACTIVE, MissionAction.EDIT, "Can't edit an active mission"),
        (M.COMPLETED, MissionAction.CANCEL, "Can't cancel a mission that's completed"),
    ],
)
def test_mission_refusal_wording(status, action, message):
    assert state_problem(status, action).message == message


@pytest.mark.parametrize(
    "action, current, mission, message",
    [
        (AssignmentAction.WITHDRAW, A.ACCEPTED, M.ACTIVE, "Can't withdraw from an active mission"),
        (
            AssignmentAction.ACCEPT,
            A.PROPOSED,
            M.PENDING_APPROVAL,
            "Can't accept a proposal on a mission pending approval",
        ),
        (
            AssignmentAction.PROPOSE,
            None,
            M.COMPLETED,
            "Can't propose crew for a mission that's completed",
        ),
        (
            AssignmentAction.REMOVE,
            A.ACCEPTED,
            M.CANCELLED,
            "Can't remove crew from a mission that's cancelled",
        ),
        (
            AssignmentAction.DECLINE,
            A.PROPOSED,
            M.ACTIVE,
            "Can't decline a proposal on an active mission",
        ),
    ],
)
def test_assignment_refusal_wording(action, current, mission, message):
    assert assignment_problem(action, current, mission).message == message
