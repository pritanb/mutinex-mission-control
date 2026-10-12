"""Mission and assignment state machines, and the checks a mission must pass to be submitted."""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import Action, AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.records import RosterEntry, SlotSpec

M = MissionStatus
A = AssignmentStatus

FINAL = frozenset({M.COMPLETED, M.CANCELLED})


# The states each mission action may start from. Its keys are the mission actions. Previewing a
# match is listed so its refusals share these codes, though it never changes the status.
MISSION_ALLOWED_FROM: Mapping[Action, frozenset[MissionStatus]] = MappingProxyType(
    {
        Action.SUBMIT: frozenset({M.DRAFT}),
        Action.APPROVE: frozenset({M.PENDING_APPROVAL}),
        Action.REJECT: frozenset({M.PENDING_APPROVAL}),
        Action.TRANSFER: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.COMPLETE: frozenset({M.ACTIVE}),
        Action.CANCEL: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.EDIT_MISSION: frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        Action.PREVIEW_MATCH: frozenset({M.DRAFT}),
    }
)

# How each mission action reads after "Can't ...", e.g. "Can't approve a mission in draft".
_MISSION_VERB: Mapping[Action, str] = MappingProxyType(
    {
        Action.SUBMIT: "submit",
        Action.APPROVE: "approve",
        Action.REJECT: "reject",
        Action.TRANSFER: "transfer",
        Action.COMPLETE: "complete",
        Action.CANCEL: "cancel",
        Action.EDIT_MISSION: "edit",
        Action.PREVIEW_MATCH: "suggest crew for",
    }
)


# How each state reads after "a mission ...", e.g. "Can't approve a mission in draft".
_STATE_PHRASE: Mapping[MissionStatus, str] = MappingProxyType(
    {
        M.DRAFT: "in draft",
        M.PENDING_APPROVAL: "pending approval",
        M.COMPLETED: "that's completed",
        M.CANCELLED: "that's cancelled",
    }
)


def _wrong_state(status: MissionStatus, doing: str) -> Problem:
    """`doing` is the start of the sentence, e.g. "approve" or "withdraw from"."""
    if status == M.ACTIVE:
        return Problem("mission_frozen", f"Can't {doing} an active mission")
    code = "mission_final" if status in FINAL else "invalid_transition"
    return Problem(code, f"Can't {doing} a mission {_STATE_PHRASE[status]}")


class StateConflict(RuleViolation):
    """The mission's state doesn't allow the change. `problem` says why; its code and message
    become the refusal's own."""

    def __init__(self, problem: Problem) -> None:
        super().__init__(problem.message, [problem], code=problem.code)
        self.problem = problem


def _after_change(status: MissionStatus) -> MissionStatus:
    """A change to a pending mission voids its approval round; otherwise status holds."""
    return M.DRAFT if status == M.PENDING_APPROVAL else status


def touch_for_change(status: MissionStatus) -> MissionStatus:
    """The mission's status once a change to it is made. Every mutating service calls this
    first. Draft stays Draft and Pending goes back to Draft; an Active or finished mission
    can't be changed, so this raises `StateConflict`."""
    if status not in MISSION_ALLOWED_FROM[Action.EDIT_MISSION]:
        raise StateConflict(_wrong_state(status, _MISSION_VERB[Action.EDIT_MISSION]))
    return _after_change(status)


def _require_mission_action(action: Action) -> None:
    if action not in MISSION_ALLOWED_FROM:
        raise ValueError(f"{action!r} is not a mission action; use the assignment functions")


def state_problem(status: MissionStatus, action: Action) -> Problem | None:
    """Why mission `action` isn't allowed from `status`, or None if it is. Raises ValueError
    for an action that isn't a mission action."""
    _require_mission_action(action)
    if status in MISSION_ALLOWED_FROM[action]:
        return None
    return _wrong_state(status, _MISSION_VERB[action])


def mission_status_after(
    status: MissionStatus, action: Action, *, reaches_quorum: bool = False
) -> MissionStatus:
    """The mission's status once `action` succeeds. Check `state_problem` first. Previewing a
    match changes nothing, so the status stays as it is."""
    if state_problem(status, action) is not None:
        raise ValueError(f"{_MISSION_VERB[action]} is not allowed from {status.value}")
    match action:
        case Action.SUBMIT:
            return M.PENDING_APPROVAL
        case Action.APPROVE:
            return M.ACTIVE if reaches_quorum else M.PENDING_APPROVAL
        case Action.REJECT:
            return M.DRAFT
        case Action.COMPLETE:
            return M.COMPLETED
        case Action.CANCEL:
            return M.CANCELLED
        case Action.EDIT_MISSION | Action.TRANSFER:
            return _after_change(status)
        case Action.PREVIEW_MATCH:
            return status


# Assignments


# action -> (assignment states it may start from, mission states it's allowed in). Its keys
# are the assignment actions. PROPOSE_CREW creates the assignment, so it has no starting state.
_ASSIGNMENT_RULES: Mapping[
    Action, tuple[frozenset[AssignmentStatus] | None, frozenset[MissionStatus]]
] = MappingProxyType(
    {
        Action.PROPOSE_CREW: (None, frozenset({M.DRAFT, M.PENDING_APPROVAL})),
        Action.ACCEPT: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
        Action.DECLINE: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
        Action.WITHDRAW: (
            frozenset({A.ACCEPTED}),
            frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        ),
        Action.REMOVE_CREW: (
            frozenset({A.PROPOSED, A.ACCEPTED}),
            frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        ),
    }
)

_ASSIGNMENT_RESULT: Mapping[Action, AssignmentStatus] = MappingProxyType(
    {
        Action.PROPOSE_CREW: A.PROPOSED,
        Action.ACCEPT: A.ACCEPTED,
        Action.DECLINE: A.DECLINED,
        Action.WITHDRAW: A.WITHDRAWN,
        Action.REMOVE_CREW: A.REMOVED,
    }
)

# How each assignment action reads before "a mission ...".
_ASSIGNMENT_PHRASE: Mapping[Action, str] = MappingProxyType(
    {
        Action.PROPOSE_CREW: "propose crew for",
        Action.ACCEPT: "accept a proposal on",
        Action.DECLINE: "decline a proposal on",
        Action.WITHDRAW: "withdraw from",
        Action.REMOVE_CREW: "remove crew from",
    }
)

# Actions that change the roster, and so send a pending mission back to Draft.
_ROSTER_CHANGES = frozenset({Action.PROPOSE_CREW, Action.WITHDRAW, Action.REMOVE_CREW})

# How each assignment action reads before "an assignment ...".
_ASSIGNMENT_VERB: Mapping[Action, str] = MappingProxyType(
    {
        Action.PROPOSE_CREW: "propose",
        Action.ACCEPT: "accept",
        Action.DECLINE: "decline",
        Action.WITHDRAW: "withdraw",
        Action.REMOVE_CREW: "remove",
    }
)


def _require_assignment_action(action: Action) -> None:
    if action not in _ASSIGNMENT_RULES:
        raise ValueError(f"{action!r} is not an assignment action; use the mission functions")


def assignment_problem(
    action: Action, current: AssignmentStatus | None, mission: MissionStatus
) -> Problem | None:
    """Why assignment `action` isn't allowed, or None. Mission state is checked before
    assignment state. Raises ValueError for an action that isn't an assignment action."""
    _require_assignment_action(action)
    from_states, mission_states = _ASSIGNMENT_RULES[action]
    if mission not in mission_states:
        return _wrong_state(mission, _ASSIGNMENT_PHRASE[action])
    if from_states is not None and current not in from_states:
        label = current.value if current else "missing"
        return Problem(
            "invalid_transition", f"Can't {_ASSIGNMENT_VERB[action]} an assignment that is {label}"
        )
    return None


def assignment_status_after(action: Action) -> AssignmentStatus:
    _require_assignment_action(action)
    return _ASSIGNMENT_RESULT[action]


def mission_status_after_assignment_action(mission: MissionStatus, action: Action) -> MissionStatus:
    _require_assignment_action(action)
    return _after_change(mission) if action in _ROSTER_CHANGES else mission


def cascade(mission_final_status: MissionStatus, assignment: AssignmentStatus) -> AssignmentStatus:
    """What an assignment becomes when its mission completes or is cancelled."""
    if mission_final_status == M.COMPLETED and assignment == A.ACCEPTED:
        return A.COMPLETED
    if mission_final_status == M.CANCELLED and assignment in (A.PROPOSED, A.ACCEPTED):
        return A.CANCELLED
    return assignment


# Submit guard


def roster_problems(roster: Sequence[RosterEntry], window: DateRange) -> list[Problem]:
    """Accepted crew who are no longer eligible, e.g. after a skill change. Checked at submit
    and again at every approval."""
    return [
        p
        for e in roster
        if e.status == A.ACCEPTED
        for p in ineligibility_reasons(e.crew, e.slot, window)
    ]


def check_submit(
    slots: Sequence[SlotSpec],
    roster: Sequence[RosterEntry],
    window: DateRange,
    eligible_approvers: int,
    approvals_required: int,
) -> list[Problem]:
    """Everything stopping a Draft mission being submitted, all at once. `slots[i].open_places`
    is headcount minus open assignments.

    The order is part of the contract, and callers show problems in it: unfilled places (in
    slot order), then unanswered proposals, then accepted crew who are no longer eligible (in
    roster order), then too few eligible approvers."""
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
