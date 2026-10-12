import pytest

from builders import EVA, crew, date_range, req, roster_entry, slot
from mission_control.domain import lifecycle, permissions
from mission_control.domain.enums import Action
from mission_control.domain.enums import AssignmentStatus as A
from mission_control.domain.enums import MissionStatus as M
from mission_control.domain.lifecycle import (
    MISSION_ALLOWED_FROM,
    StateConflict,
    assignment_problem,
    assignment_status_after,
    cascade,
    check_submit,
    mission_status_after,
    mission_status_after_assignment_action,
    state_problem,
    touch_for_change,
)

WINDOW = date_range("2027-03-01", "2027-03-10")
EVA_3 = req(EVA, 3)
ALL_STATUSES = list(M)


# --- Mission transition table -------------------------------------------------------------

MISSION_ACTIONS = [
    Action.SUBMIT,
    Action.APPROVE,
    Action.REJECT,
    Action.TRANSFER,
    Action.COMPLETE,
    Action.CANCEL,
    Action.EDIT_MISSION,
    Action.PREVIEW_MATCH,
    Action.APPLY_MATCH,
]
ASSIGNMENT_ACTIONS = [
    Action.PROPOSE_CREW,
    Action.ACCEPT,
    Action.DECLINE,
    Action.WITHDRAW,
    Action.REMOVE_CREW,
]

ALLOWED = {
    Action.SUBMIT: {M.DRAFT},
    Action.APPROVE: {M.PENDING_APPROVAL},
    Action.REJECT: {M.PENDING_APPROVAL},
    Action.TRANSFER: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
    Action.COMPLETE: {M.ACTIVE},
    Action.CANCEL: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
    Action.EDIT_MISSION: {M.DRAFT, M.PENDING_APPROVAL},
    Action.PREVIEW_MATCH: {M.DRAFT},  # the matcher suggests crew for draft missions only
    Action.APPLY_MATCH: {M.DRAFT},
}


@pytest.mark.parametrize("action", MISSION_ACTIONS)
@pytest.mark.parametrize("status", ALL_STATUSES)
def test_transition_table_allows_exactly_the_designed_states(action, status):
    problem = state_problem(status, action)
    if status in ALLOWED[action]:
        assert problem is None
    else:
        assert problem is not None


@pytest.mark.parametrize("action", MISSION_ACTIONS)
@pytest.mark.parametrize("status", [M.COMPLETED, M.CANCELLED])
def test_finished_missions_refuse_everything_with_mission_final(action, status):
    assert state_problem(status, action).code == "mission_final"


@pytest.mark.parametrize(
    "action",
    [Action.EDIT_MISSION, Action.SUBMIT, Action.APPROVE, Action.REJECT, Action.PREVIEW_MATCH],
)
def test_ac5_active_mission_refuses_changes_with_mission_frozen(action):
    assert state_problem(M.ACTIVE, action).code == "mission_frozen"


@pytest.mark.parametrize("action", [Action.COMPLETE, Action.CANCEL, Action.TRANSFER])
def test_ac5_active_mission_still_allows_complete_cancel_and_transfer(action):
    assert state_problem(M.ACTIVE, action) is None


@pytest.mark.parametrize(
    "status, action",
    [
        (M.DRAFT, Action.APPROVE),
        (M.DRAFT, Action.REJECT),
        (M.DRAFT, Action.COMPLETE),
        (M.PENDING_APPROVAL, Action.SUBMIT),
        (M.PENDING_APPROVAL, Action.COMPLETE),
        (M.PENDING_APPROVAL, Action.PREVIEW_MATCH),
    ],
)
def test_wrong_state_in_draft_or_pending_is_invalid_transition(status, action):
    problem = state_problem(status, action)
    assert problem.code == "invalid_transition"
    assert status.value.replace("_", " ") in problem.message.lower()


def test_submit_moves_draft_to_pending():
    assert mission_status_after(M.DRAFT, Action.SUBMIT) == M.PENDING_APPROVAL


def test_ac3_approval_before_quorum_stays_pending_and_at_quorum_goes_active():
    assert (
        mission_status_after(M.PENDING_APPROVAL, Action.APPROVE, reaches_quorum=False)
        == M.PENDING_APPROVAL
    )
    assert mission_status_after(M.PENDING_APPROVAL, Action.APPROVE, reaches_quorum=True) == M.ACTIVE


def test_reject_returns_to_draft():
    assert mission_status_after(M.PENDING_APPROVAL, Action.REJECT) == M.DRAFT


def test_ac4_any_change_to_a_pending_mission_returns_it_to_draft():
    assert mission_status_after(M.PENDING_APPROVAL, Action.EDIT_MISSION) == M.DRAFT
    assert mission_status_after(M.DRAFT, Action.EDIT_MISSION) == M.DRAFT


def test_m1_transfer_sends_pending_back_to_draft_but_leaves_draft_and_active_alone():
    assert mission_status_after(M.PENDING_APPROVAL, Action.TRANSFER) == M.DRAFT
    assert mission_status_after(M.DRAFT, Action.TRANSFER) == M.DRAFT
    assert mission_status_after(M.ACTIVE, Action.TRANSFER) == M.ACTIVE


# --- Back to Draft: touch_for_change ------------------------------------------------------


def test_touch_for_change_leaves_a_draft_mission_in_draft():
    assert touch_for_change(M.DRAFT) == M.DRAFT


def test_ac4_touch_for_change_sends_a_pending_mission_back_to_draft():
    assert touch_for_change(M.PENDING_APPROVAL) == M.DRAFT


def test_ac5_touch_for_change_refuses_an_active_mission_as_frozen():
    with pytest.raises(StateConflict) as raised:
        touch_for_change(M.ACTIVE)
    assert raised.value.problem.code == "mission_frozen"
    assert raised.value.problem.message == "Can't edit an active mission"


@pytest.mark.parametrize(
    "status, message",
    [
        (M.COMPLETED, "Can't edit a mission that's completed"),
        (M.CANCELLED, "Can't edit a mission that's cancelled"),
    ],
)
def test_touch_for_change_refuses_a_finished_mission_as_final(status, message):
    with pytest.raises(StateConflict) as raised:
        touch_for_change(status)
    assert raised.value.problem.code == "mission_final"
    assert raised.value.problem.message == message


def test_previewing_a_match_leaves_a_draft_mission_in_draft():
    assert mission_status_after(M.DRAFT, Action.PREVIEW_MATCH) == M.DRAFT


def test_applying_a_match_leaves_a_draft_mission_in_draft():
    assert mission_status_after(M.DRAFT, Action.APPLY_MATCH) == M.DRAFT


def test_complete_and_cancel_reach_final_states():
    assert mission_status_after(M.ACTIVE, Action.COMPLETE) == M.COMPLETED
    for s in (M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE):
        assert mission_status_after(s, Action.CANCEL) == M.CANCELLED


def test_status_after_refuses_a_transition_the_table_does_not_allow():
    with pytest.raises(ValueError):
        mission_status_after(M.DRAFT, Action.COMPLETE)


# --- Assignment transitions ---------------------------------------------------------------

ASSIGNMENT_CASES = [
    # action, assignment status, allowed mission states
    (Action.PROPOSE_CREW, None, {M.DRAFT, M.PENDING_APPROVAL}),
    (Action.ACCEPT, A.PROPOSED, {M.DRAFT}),
    (Action.DECLINE, A.PROPOSED, {M.DRAFT}),
    (Action.WITHDRAW, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
    (Action.REMOVE_CREW, A.PROPOSED, {M.DRAFT, M.PENDING_APPROVAL}),
    (Action.REMOVE_CREW, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
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
        (Action.ACCEPT, A.ACCEPTED),
        (Action.DECLINE, A.ACCEPTED),
        (Action.WITHDRAW, A.PROPOSED),
        (Action.REMOVE_CREW, A.DECLINED),
        (Action.ACCEPT, A.WITHDRAWN),
    ],
)
def test_assignment_action_from_the_wrong_assignment_status_is_invalid(action, current):
    assert assignment_problem(action, current, M.DRAFT).code == "invalid_transition"


def test_assignment_status_after_each_action():
    assert assignment_status_after(Action.PROPOSE_CREW) == A.PROPOSED
    assert assignment_status_after(Action.ACCEPT) == A.ACCEPTED
    assert assignment_status_after(Action.DECLINE) == A.DECLINED
    assert assignment_status_after(Action.WITHDRAW) == A.WITHDRAWN
    assert assignment_status_after(Action.REMOVE_CREW) == A.REMOVED


@pytest.mark.parametrize("action", [Action.PROPOSE_CREW, Action.WITHDRAW, Action.REMOVE_CREW])
def test_ac4_roster_changes_send_a_pending_mission_back_to_draft(action):
    assert mission_status_after_assignment_action(M.PENDING_APPROVAL, action) == M.DRAFT
    assert mission_status_after_assignment_action(M.DRAFT, action) == M.DRAFT


@pytest.mark.parametrize("action", [Action.ACCEPT, Action.DECLINE])
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


def test_complete_accepted_roster_with_enough_approvers_can_be_submitted():
    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    dana = roster_entry(crew("Dana", 1, skills={EVA: 4}), s, id=1)
    assert check_submit([s], [dana], WINDOW, eligible_approvers=2, approvals_required=2) == []


def test_ac2_every_problem_is_reported_at_once():
    commander = slot(EVA_3, id=1, position=1, name="Commander", open_places=1)  # nobody yet
    specialist = slot(EVA_3, id=2, position=2, name="Specialist", open_places=0)
    roster = [
        roster_entry(crew("Dana", 1, skills={EVA: 4}), specialist, id=1, status=A.PROPOSED),
        roster_entry(crew("Hana", 2, skills={EVA: 2}), specialist, id=2),
    ]  # accepted but no longer qualifies
    problems = check_submit(
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
    commander = slot(EVA_3, id=1, position=1, name="Commander", open_places=1)
    [p] = check_submit([commander], [], WINDOW, 2, 2)
    assert p.code == "slot_unfilled"
    assert "Commander" in p.message and p.refs["slot_id"] == 1


def test_ac2_unanswered_proposal_names_the_person_and_slot():
    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    dana = roster_entry(crew("Dana", 7, skills={EVA: 4}), s, id=7, status=A.PROPOSED)
    [p] = check_submit([s], [dana], WINDOW, 2, 2)
    assert p.code == "proposal_unanswered"
    assert "Dana" in p.message and "Specialist" in p.message
    assert p.refs["assignment_id"] == 7


def test_roster_member_who_became_unavailable_blocks_submission():
    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    leave = [date_range("2027-03-05", "2027-03-06")]
    fay = roster_entry(crew("Fay", 1, skills={EVA: 4}, unavailable=leave), s, id=1)
    [p] = check_submit([s], [fay], WINDOW, 2, 2)
    assert p.code == "unavailable"


def test_ac12_too_few_eligible_approvers_blocks_submission():
    s = slot(EVA_3, id=1, position=1, name="Flight Surgeon", open_places=0)
    marco = roster_entry(crew("Marco", 1, skills={EVA: 4}), s, id=1)
    [p] = check_submit([s], [marco], WINDOW, eligible_approvers=1, approvals_required=2)
    assert p.code == "insufficient_approvers"
    assert p.message == "Only 1 Director can approve this mission; it needs 2"


@pytest.mark.parametrize(
    ("eligible", "required", "message"),
    [
        (0, 1, "No Director can approve this mission; it needs 1"),
        (2, 3, "Only 2 Directors can approve this mission; it needs 3"),
    ],
)
def test_ac12_insufficient_approvers_wording(eligible, required, message):
    s = slot(EVA_3, id=1, position=1, name="Flight Surgeon", open_places=0)
    [p] = check_submit([s], [], WINDOW, eligible_approvers=eligible, approvals_required=required)
    assert p.message == message


# Regression: refusal wording reads naturally


@pytest.mark.parametrize(
    "status, action, message",
    [
        (M.DRAFT, Action.APPROVE, "Can't approve a mission in draft"),
        (M.PENDING_APPROVAL, Action.SUBMIT, "Can't submit a mission pending approval"),
        (M.ACTIVE, Action.EDIT_MISSION, "Can't edit an active mission"),
        (M.COMPLETED, Action.CANCEL, "Can't cancel a mission that's completed"),
        (M.ACTIVE, Action.PREVIEW_MATCH, "Can't suggest crew for an active mission"),
        (
            M.PENDING_APPROVAL,
            Action.PREVIEW_MATCH,
            "Can't suggest crew for a mission pending approval",
        ),
        (M.CANCELLED, Action.PREVIEW_MATCH, "Can't suggest crew for a mission that's cancelled"),
        (M.ACTIVE, Action.APPLY_MATCH, "Can't apply suggested crew to an active mission"),
    ],
)
def test_mission_refusal_wording(status, action, message):
    assert state_problem(status, action).message == message


@pytest.mark.parametrize(
    "action, current, mission, message",
    [
        (Action.WITHDRAW, A.ACCEPTED, M.ACTIVE, "Can't withdraw from an active mission"),
        (
            Action.ACCEPT,
            A.PROPOSED,
            M.PENDING_APPROVAL,
            "Can't accept a proposal on a mission pending approval",
        ),
        (
            Action.PROPOSE_CREW,
            None,
            M.COMPLETED,
            "Can't propose crew for a mission that's completed",
        ),
        (
            Action.REMOVE_CREW,
            A.ACCEPTED,
            M.CANCELLED,
            "Can't remove crew from a mission that's cancelled",
        ),
        (
            Action.DECLINE,
            A.PROPOSED,
            M.ACTIVE,
            "Can't decline a proposal on an active mission",
        ),
    ],
)
def test_assignment_refusal_wording(action, current, mission, message):
    assert assignment_problem(action, current, mission).message == message


# One action enum: lifecycle and permissions agree on what each action is


def test_mission_table_covers_exactly_the_mission_actions():
    assert set(MISSION_ALLOWED_FROM) == set(MISSION_ACTIONS)


def test_lifecycle_and_permissions_share_one_action_enum():
    lifecycle_keys = set(MISSION_ALLOWED_FROM) | set(lifecycle._ASSIGNMENT_RULES)
    assert lifecycle_keys == set(MISSION_ACTIONS) | set(ASSIGNMENT_ACTIONS)
    assert lifecycle_keys <= set(Action)
    assert all(type(key) is Action for key in lifecycle_keys)
    assert all(type(key) is Action for key in permissions.ROLES)
    # The member lifecycle uses is the very member permissions checks.
    assert set(permissions.ROLES) == set(Action)
    assert lifecycle_keys <= set(permissions.ROLES)
    assert not hasattr(lifecycle, "MissionAction")
    assert not hasattr(lifecycle, "AssignmentAction")
    assert permissions.Action is Action


@pytest.mark.parametrize("action", sorted(set(Action) - set(MISSION_ACTIONS)))
def test_mission_functions_refuse_a_non_mission_action_as_a_programming_error(action):
    with pytest.raises(ValueError, match="not a mission action"):
        state_problem(M.DRAFT, action)
    with pytest.raises(ValueError, match="not a mission action"):
        mission_status_after(M.DRAFT, action)


@pytest.mark.parametrize("action", sorted(set(Action) - set(ASSIGNMENT_ACTIONS)))
def test_assignment_functions_refuse_a_non_assignment_action_as_a_programming_error(action):
    with pytest.raises(ValueError, match="not an assignment action"):
        assignment_problem(action, A.PROPOSED, M.DRAFT)
    with pytest.raises(ValueError, match="not an assignment action"):
        assignment_status_after(action)
    with pytest.raises(ValueError, match="not an assignment action"):
        mission_status_after_assignment_action(M.DRAFT, action)


@pytest.mark.parametrize(
    "action, current, message",
    [
        (Action.REMOVE_CREW, A.DECLINED, "Can't remove an assignment that is declined"),
        (Action.ACCEPT, A.WITHDRAWN, "Can't accept an assignment that is withdrawn"),
        (Action.WITHDRAW, None, "Can't withdraw an assignment that is missing"),
    ],
)
def test_wrong_assignment_status_wording(action, current, message):
    assert assignment_problem(action, current, M.DRAFT).message == message


def test_status_after_refusal_names_the_action_in_words():
    with pytest.raises(ValueError, match="^edit is not allowed from active$"):
        mission_status_after(M.ACTIVE, Action.EDIT_MISSION)
