"""Assignments: the owner proposing crew for a mission's slots, the crew member's answer (accept,
decline, withdraw), the owner removing someone, each person's own list, and what happens to
assignments when their mission is completed or cancelled.

Each use case runs in one write transaction, in this order: load (anything missing, hidden or
another organisation's is not found), authorize, check the mission's and the assignment's state,
check input, check the rules, then write and audit with the names involved. A refusal writes
nothing.

Who sees what: crew see only their own assignments, so anyone else's is not found. Leads and
Directors see every assignment in their organisation, so acting on one that isn't theirs is
forbidden.

A roster change (propose, withdraw, remove) on a mission pending approval sends it back to Draft,
so its approval round stops counting. That return is audited straight after the change that
caused it.
"""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import Action, AssignmentStatus, MissionStatus
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import (
    StateConflict,
    assignment_problem,
    assignment_status_after,
    cascade,
    mission_status_after_assignment_action,
)
from mission_control.domain.permissions import Context
from mission_control.domain.records import SlotSpec
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    Assignment,
    AssignmentSummary,
    CrewProfile,
    Mission,
)
from mission_control.services.context import (
    ServiceContext,
    found,
    mission_context,
    return_to_draft,
    visible_mission,
)

A = AssignmentStatus

_ASSIGNMENT = "Assignment"
_SLOT = "Slot"
_CREW_MEMBER = "Crew member"

_EVENT: Mapping[Action, Event] = MappingProxyType(
    {
        Action.PROPOSE_CREW: Event.ASSIGNMENT_PROPOSED,
        Action.ACCEPT: Event.ASSIGNMENT_ACCEPTED,
        Action.DECLINE: Event.ASSIGNMENT_DECLINED,
        Action.WITHDRAW: Event.ASSIGNMENT_WITHDRAWN,
        Action.REMOVE_CREW: Event.ASSIGNMENT_REMOVED,
    }
)

_CASCADE_EVENT: Mapping[AssignmentStatus, Event] = MappingProxyType(
    {A.COMPLETED: Event.ASSIGNMENT_COMPLETED, A.CANCELLED: Event.ASSIGNMENT_CANCELLED}
)

_MISSION_ENDS = frozenset({MissionStatus.COMPLETED, MissionStatus.CANCELLED})


# The owner proposes


def propose(ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int) -> Assignment:
    """Propose someone for a place in one of the mission's slots. Only the mission's owner may,
    while it's in Draft or pending approval; a pending mission goes back to Draft.

    Refused, with every reason at once, if the slot has no open place, the person already holds
    an open assignment on this mission, or they aren't eligible (deactivated, short of a
    required skill, unavailable, or accepted on another mission with overlapping dates).
    Proposals elsewhere don't count: they block nothing. An owner may propose themselves, and
    must then accept like anyone else."""
    with ctx.write() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        slots = _slot_specs(repos, mission)
        slot = found(slots.get(slot_id), _SLOT)
        ctx.authorize(Action.PROPOSE_CREW, mission_context(repos, mission))
        _check_state(Action.PROPOSE_CREW, None, mission)
        # The person is looked up only once the actor may propose, so a refusal never
        # reveals whether a crew id exists.
        profile = found(repos.crew.get(crew_profile_id), _CREW_MEMBER)
        ctx.authorize_view(Action.VIEW_CREW, _about(profile), _CREW_MEMBER)

        problems = [
            *_already_on_mission(repos, mission, slots, profile),
            *_slot_full(mission, slot),
            *_ineligibility(repos, mission, slot, profile),
        ]
        _refuse(
            problems, f"{profile.display_name} can't be proposed as {slot.name} on {mission.name}"
        )

        made = repos.assignments.create(mission.id, slot.id, profile.id, ctx.actor.user_id)
        _audit(ctx, Event.ASSIGNMENT_PROPOSED, made, None, A.PROPOSED, mission, slot, profile)
        _after_roster_change(ctx, repos, mission, Action.PROPOSE_CREW)
        return made


# The crew member answers


def accept(ctx: ServiceContext, assignment_id: int) -> Assignment:
    """Accept your own proposal while the mission is in Draft. Eligibility is checked again
    now, so an accepted assignment elsewhere with overlapping dates refuses it, naming that
    mission."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.ACCEPT, _about(profile))
        _check_state(Action.ACCEPT, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        _refuse(
            _ineligibility(repos, mission, slot, profile),
            f"{profile.display_name} can't accept {slot.name} on {mission.name}",
        )
        return _change(ctx, repos, Action.ACCEPT, assignment, mission, slot, profile)


def decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:
    """Decline your own proposal while the mission is in Draft. The reason is optional; a blank
    one is stored as none."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.DECLINE, _about(profile))
        _check_state(Action.DECLINE, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        given = (reason or "").strip() or None
        return _change(ctx, repos, Action.DECLINE, assignment, mission, slot, profile, given)


def withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:
    """Withdraw from your own accepted assignment, giving a reason. Allowed while the mission is
    in Draft or pending approval; a pending mission goes back to Draft. An active mission's
    roster is frozen."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.WITHDRAW, _about(profile))
        _check_state(Action.WITHDRAW, assignment.status, mission)
        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Withdrawing from {mission.name} needs a reason")
        slot = _slot_of(repos, mission, assignment)
        return _change(ctx, repos, Action.WITHDRAW, assignment, mission, slot, profile, given)


# The owner removes


def remove(ctx: ServiceContext, assignment_id: int) -> Assignment:
    """Retract a proposal or remove accepted crew. Only the mission's owner may, while it's in
    Draft or pending approval; a pending mission goes back to Draft."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.REMOVE_CREW, mission_context(repos, mission))
        _check_state(Action.REMOVE_CREW, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        return _change(ctx, repos, Action.REMOVE_CREW, assignment, mission, slot, profile)


# Your own assignments


def my_assignments(ctx: ServiceContext, pending: bool = False) -> list[AssignmentSummary]:
    """The caller's own assignments, newest first; with `pending`, only proposals still waiting
    for their reply. Someone without a crew profile has none."""
    if ctx.actor.crew_profile_id is None:
        return []
    with ctx.read() as repos:
        mine = repos.crew.history(ctx.actor.crew_profile_id)
    return [a for a in mine if a.status == A.PROPOSED] if pending else mine


# When a mission ends


def cascade_mission_end(
    ctx: ServiceContext, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:
    """Apply a mission's completion or cancellation to its assignments: completing it completes
    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything
    else is left as it is. Each change is written and audited as the acting user.

    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked
    the mission's own transition, so the assignments change in the same transaction as the
    mission and roll back with it. It does no permission or state checks of its own. Returns the
    changed assignments, in id order."""
    if final_status not in _MISSION_ENDS:
        raise ValueError(f"a mission ends completed or cancelled, not {final_status.value}")
    if not ctx.conn.in_transaction:
        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
    repos = ctx.repos
    slots = _slot_specs(repos, mission)
    changed = []
    for assignment in repos.missions.assignments(mission.id):
        to = cascade(final_status, assignment.status)
        if to == assignment.status:
            continue
        profile = found(repos.crew.get(assignment.crew_profile_id), _CREW_MEMBER)
        slot = found(slots.get(assignment.slot_id), _SLOT)
        repos.assignments.set_status(assignment.id, to, assignment.reason)
        _audit(ctx, _CASCADE_EVENT[to], assignment, assignment.status, to, mission, slot, profile)
        changed.append(found(repos.assignments.get(assignment.id), _ASSIGNMENT))
    return changed


# Loading


def _load(
    ctx: ServiceContext, repos: Repos, assignment_id: int
) -> tuple[Assignment, Mission, CrewProfile]:
    """The assignment, its mission and its crew member. Not found if it's missing, another
    organisation's, or a crew member's who isn't the caller."""
    assignment = found(repos.assignments.get(assignment_id), _ASSIGNMENT)
    profile = found(repos.crew.get(assignment.crew_profile_id), _ASSIGNMENT)
    ctx.authorize_view(Action.VIEW_ASSIGNMENT_HISTORY, _about(profile), _ASSIGNMENT)
    # Seeing the assignment is enough to see its mission's name and state, as in the crew
    # member's assignment history.
    mission = found(repos.missions.get(assignment.mission_id), _ASSIGNMENT)
    return assignment, mission, profile


def _slot_specs(repos: Repos, mission: Mission) -> dict[int, SlotSpec]:
    """The mission's live slots by id, with their open places."""
    return {s.id: s for s in repos.facts.slot_specs(mission.id)}


def _slot_of(repos: Repos, mission: Mission, assignment: Assignment) -> SlotSpec:
    """The slot of an open assignment. A slot can't be removed while it has open assignments,
    so it's always live once the state check has passed."""
    return found(_slot_specs(repos, mission).get(assignment.slot_id), _SLOT)


def _about(profile: CrewProfile) -> Context:
    """Permission context for someone's assignment: the person is the profile's user."""
    return Context(target_user_id=profile.user_id)


# Checks


def _check_state(action: Action, current: AssignmentStatus | None, mission: Mission) -> None:
    problem = assignment_problem(action, current, mission.status)
    if problem is not None:
        raise StateConflict(problem)


def _already_on_mission(
    repos: Repos, mission: Mission, slots: Mapping[int, SlotSpec], profile: CrewProfile
) -> list[Problem]:
    held = [
        a
        for a in repos.missions.assignments(mission.id, (A.PROPOSED, A.ACCEPTED))
        if a.crew_profile_id == profile.id
    ]
    if not held:
        return []
    existing = held[0]
    slot = slots.get(existing.slot_id)
    where = f" as {slot.name}" if slot else ""
    return [
        Problem(
            "already_assigned",
            f"{profile.display_name} is already {existing.status.value}{where} on {mission.name}",
            {"assignment_id": existing.id, "crew_profile_id": profile.id, "mission_id": mission.id},
        )
    ]


def _slot_full(mission: Mission, slot: SlotSpec) -> list[Problem]:
    if slot.open_places > 0:
        return []
    return [
        Problem(
            "slot_full", f"{slot.name} on {mission.name} has no open places", {"slot_id": slot.id}
        )
    ]


def _ineligibility(
    repos: Repos, mission: Mission, slot: SlotSpec, profile: CrewProfile
) -> list[Problem]:
    """Every reason the person can't fill the slot, with commitments on this mission left out."""
    person = found(repos.facts.candidate(profile.id, excluding_mission_id=mission.id), _CREW_MEMBER)
    return ineligibility_reasons(person, slot, mission.window)


def _refuse(problems: Sequence[Problem], message: str) -> None:
    """A single reason is raised under its own code; several are listed together."""
    if len(problems) == 1:
        raise RuleViolation.of(problems[0])
    if problems:
        raise RuleViolation(message, problems)


# Writing


def _change(
    ctx: ServiceContext,
    repos: Repos,
    action: Action,
    assignment: Assignment,
    mission: Mission,
    slot: SlotSpec,
    profile: CrewProfile,
    reason: str | None = None,
) -> Assignment:
    """Move the assignment on by `action`, audit it, and send a pending mission back to Draft
    if the roster changed."""
    to = assignment_status_after(action)
    repos.assignments.set_status(assignment.id, to, reason)
    _audit(ctx, _EVENT[action], assignment, assignment.status, to, mission, slot, profile, reason)
    _after_roster_change(ctx, repos, mission, action)
    return found(repos.assignments.get(assignment.id), _ASSIGNMENT)


def _after_roster_change(
    ctx: ServiceContext, repos: Repos, mission: Mission, action: Action
) -> None:
    if mission_status_after_assignment_action(mission.status, action) != mission.status:
        return_to_draft(ctx, repos, mission, _EVENT[action], mission.name)


def _audit(
    ctx: ServiceContext,
    event: Event,
    assignment: Assignment,
    from_status: AssignmentStatus | None,
    to_status: AssignmentStatus,
    mission: Mission,
    slot: SlotSpec,
    profile: CrewProfile,
    reason: str | None = None,
) -> None:
    ctx.audit(
        event,
        mission_id=mission.id,
        assignment_id=assignment.id,
        crew_profile_id=profile.id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        data={
            "mission_name": mission.name,
            "slot_name": slot.name,
            "crew_name": profile.display_name,
        },
    )
