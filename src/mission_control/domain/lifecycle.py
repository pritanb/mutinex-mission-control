"""Mission and assignment state machines, and the checks a mission must pass to be submitted."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem
from mission_control.domain.records import CandidateFacts, SlotSpec

M = MissionStatus
A = AssignmentStatus

FINAL = frozenset({M.COMPLETED, M.CANCELLED})


class MissionAction(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    TRANSFER = "transfer"
    COMPLETE = "complete"
    CANCEL = "cancel"
    EDIT = "edit"  # any change to dates, slots or requirements


# The states each mission action may start from.
MISSION_ALLOWED_FROM: dict[MissionAction, frozenset[MissionStatus]] = {
    MissionAction.SUBMIT: frozenset({M.DRAFT}),
    MissionAction.APPROVE: frozenset({M.PENDING_APPROVAL}),
    MissionAction.REJECT: frozenset({M.PENDING_APPROVAL}),
    MissionAction.TRANSFER: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
    MissionAction.COMPLETE: frozenset({M.ACTIVE}),
    MissionAction.CANCEL: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
    MissionAction.EDIT: frozenset({M.DRAFT, M.PENDING_APPROVAL}),
}


# How each state reads after "a mission ...", e.g. "Can't approve a mission in draft".
_STATE_PHRASE = {
    M.DRAFT: "in draft",
    M.PENDING_APPROVAL: "pending approval",
    M.COMPLETED: "that's completed",
    M.CANCELLED: "that's cancelled",
}


def _wrong_state(status: MissionStatus, doing: str) -> Problem:
    """`doing` is the start of the sentence, e.g. "approve" or "withdraw from"."""
    if status == M.ACTIVE:
        return Problem("mission_frozen", f"Can't {doing} an active mission")
    code = "mission_final" if status in FINAL else "invalid_transition"
    return Problem(code, f"Can't {doing} a mission {_STATE_PHRASE[status]}")


def state_problem(status: MissionStatus, action: MissionAction) -> Problem | None:
    """Why `action` isn't allowed from `status`, or None if it is."""
    if status in MISSION_ALLOWED_FROM[action]:
        return None
    return _wrong_state(status, action.value)


def mission_status_after(
    status: MissionStatus, action: MissionAction, *, reaches_quorum: bool = False
) -> MissionStatus:
    """The mission's status once `action` succeeds. Check `state_problem` first."""
    if state_problem(status, action) is not None:
        raise ValueError(f"{action.value} is not allowed from {status.value}")
    match action:
        case MissionAction.SUBMIT:
            return M.PENDING_APPROVAL
        case MissionAction.APPROVE:
            return M.ACTIVE if reaches_quorum else M.PENDING_APPROVAL
        case MissionAction.REJECT:
            return M.DRAFT
        case MissionAction.COMPLETE:
            return M.COMPLETED
        case MissionAction.CANCEL:
            return M.CANCELLED
        case MissionAction.EDIT | MissionAction.TRANSFER:
            # A change to a pending mission voids its approval round; otherwise status holds.
            return M.DRAFT if status == M.PENDING_APPROVAL else status


# Assignments


class AssignmentAction(StrEnum):
    PROPOSE = "propose"
    ACCEPT = "accept"
    DECLINE = "decline"
    WITHDRAW = "withdraw"
    REMOVE = "remove"


# action -> (assignment states it may start from, mission states it's allowed in).
# PROPOSE creates the assignment, so it has no starting state.
_ASSIGNMENT_RULES: dict[
    AssignmentAction, tuple[frozenset[AssignmentStatus] | None, frozenset[MissionStatus]]
] = {
    AssignmentAction.PROPOSE: (None, frozenset({M.DRAFT, M.PENDING_APPROVAL})),
    AssignmentAction.ACCEPT: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
    AssignmentAction.DECLINE: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
    AssignmentAction.WITHDRAW: (frozenset({A.ACCEPTED}), frozenset({M.DRAFT, M.PENDING_APPROVAL})),
    AssignmentAction.REMOVE: (
        frozenset({A.PROPOSED, A.ACCEPTED}),
        frozenset({M.DRAFT, M.PENDING_APPROVAL}),
    ),
}

_ASSIGNMENT_RESULT = {
    AssignmentAction.PROPOSE: A.PROPOSED,
    AssignmentAction.ACCEPT: A.ACCEPTED,
    AssignmentAction.DECLINE: A.DECLINED,
    AssignmentAction.WITHDRAW: A.WITHDRAWN,
    AssignmentAction.REMOVE: A.REMOVED,
}

# How each assignment action reads before "a mission ...".
_ASSIGNMENT_PHRASE = {
    AssignmentAction.PROPOSE: "propose crew for",
    AssignmentAction.ACCEPT: "accept a proposal on",
    AssignmentAction.DECLINE: "decline a proposal on",
    AssignmentAction.WITHDRAW: "withdraw from",
    AssignmentAction.REMOVE: "remove crew from",
}

# Actions that change the roster, and so send a pending mission back to Draft.
_ROSTER_CHANGES = frozenset(
    {AssignmentAction.PROPOSE, AssignmentAction.WITHDRAW, AssignmentAction.REMOVE}
)


def assignment_problem(
    action: AssignmentAction, current: AssignmentStatus | None, mission: MissionStatus
) -> Problem | None:
    """Why `action` isn't allowed, or None. Mission state is checked before assignment state."""
    from_states, mission_states = _ASSIGNMENT_RULES[action]
    if mission not in mission_states:
        return _wrong_state(mission, _ASSIGNMENT_PHRASE[action])
    if from_states is not None and current not in from_states:
        label = current.value if current else "missing"
        return Problem("invalid_transition", f"Can't {action.value} an assignment that is {label}")
    return None


def assignment_status_after(action: AssignmentAction) -> AssignmentStatus:
    return _ASSIGNMENT_RESULT[action]


def mission_status_after_assignment_action(
    mission: MissionStatus, action: AssignmentAction
) -> MissionStatus:
    if action in _ROSTER_CHANGES and mission == M.PENDING_APPROVAL:
        return M.DRAFT
    return mission


def cascade(mission_final_status: MissionStatus, assignment: AssignmentStatus) -> AssignmentStatus:
    """What an assignment becomes when its mission completes or is cancelled."""
    if mission_final_status == M.COMPLETED and assignment == A.ACCEPTED:
        return A.COMPLETED
    if mission_final_status == M.CANCELLED and assignment in (A.PROPOSED, A.ACCEPTED):
        return A.CANCELLED
    return assignment


# Submit guard


@dataclass(frozen=True)
class RosterEntry:
    """An open assignment on the mission being submitted."""

    assignment_id: int
    slot: SlotSpec
    crew: CandidateFacts  # accepted_elsewhere must exclude this mission
    status: AssignmentStatus  # proposed or accepted


def roster_problems(roster: Sequence[RosterEntry], window: DateRange) -> list[Problem]:
    """Accepted crew who are no longer eligible, e.g. after a skill change. Checked at submit
    and again at every approval."""
    return [
        p
        for e in roster
        if e.status == A.ACCEPTED
        for p in ineligibility_reasons(e.crew, e.slot, window)
    ]


def submit_problems(
    slots: Sequence[SlotSpec],
    roster: Sequence[RosterEntry],
    window: DateRange,
    eligible_approvers: int,
    approvals_required: int,
) -> list[Problem]:
    """Everything stopping a Draft mission being submitted, all at once. `slots[i].open_places`
    is headcount minus open assignments."""
    problems: list[Problem] = []
    for s in slots:
        if s.open_places > 0:
            problems.append(
                Problem(
                    "slot_unfilled",
                    f"{s.name}: {s.open_places} place{'s' if s.open_places > 1 else ''} unfilled",
                    {"slot_id": s.id},
                )
            )
    for e in roster:
        if e.status == A.PROPOSED:
            problems.append(
                Problem(
                    "proposal_unanswered",
                    f"{e.slot.name}: {e.crew.name} hasn't responded to the proposal",
                    {
                        "assignment_id": e.assignment_id,
                        "slot_id": e.slot.id,
                        "crew_profile_id": e.crew.crew_profile_id,
                    },
                )
            )
    problems.extend(roster_problems(roster, window))
    if eligible_approvers < approvals_required:
        problems.append(
            Problem(
                "insufficient_approvers",
                f"{eligible_approvers} eligible approver{'s' if eligible_approvers != 1 else ''}, "
                f"{approvals_required} required",
            )
        )
    return problems
