"""The rules mission changes must keep, and how a change is recorded.

- Only an active Mission Lead can own a mission.
- A mission's live slots have different names.
- An edit can't break an open assignment: anyone it would make no longer eligible must be removed
  first, and crew are never removed automatically.
- A change to a Pending mission sends it back to Draft, audited with its cause.
"""

from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.eligibility import MissionEditKind, invalidated_by
from mission_control.domain.enums import MissionStatus, Role
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission, Slot, User
from mission_control.services.context import ServiceContext, return_to_draft
from mission_control.services.missions.inputs import SlotInput

# Owners and slot names


def require_owner(user: User) -> None:
    """Only an active Mission Lead can own a mission."""
    for problem in owner_problems(user):
        raise RuleViolation.of(problem)


def owner_problems(user: User) -> list[Problem]:
    """Why the user can't own a mission, if they can't: only an active Mission Lead can."""
    if user.role != Role.LEAD:
        message = f"{user.name} can't own a mission: only Mission Leads can"
    elif not user.is_active:
        message = f"{user.name} can't own a mission because they're deactivated"
    else:
        return []
    return [Problem("owner_not_active_lead", message, {"user_id": user.id})]


def refuse_taken_name(
    mission: Mission, slots: Sequence[Slot], name: str, slot_id: int | None = None
) -> None:
    """A mission's live slots have different names, ignoring case. `slot_id` is the slot being
    renamed, which may keep its own name."""
    taken = next(
        (s for s in slots if s.id != slot_id and _name_key(s.name) == _name_key(name)), None
    )
    if taken is not None:
        raise RuleViolation.of(
            Problem(
                "already_exists",
                f"{mission.name} already has a slot called {taken.name}",
                {"slot_id": taken.id},
            )
        )


def repeated_name_problems(slots: Sequence[SlotInput]) -> list[Problem]:
    """A new mission's slots have different names, ignoring case. One problem per repeated
    name."""
    first_spelling: dict[str, str] = {}
    repeated: list[str] = []
    for s in slots:
        key = _name_key(s.name)
        if key not in first_spelling:
            first_spelling[key] = s.name.strip()
        elif first_spelling[key] not in repeated:
            repeated.append(first_spelling[key])
    return [Problem("already_exists", f"More than one slot is called {name}") for name in repeated]


def _name_key(name: str) -> str:
    """Slot names are compared ignoring case and surrounding spaces."""
    return name.strip().casefold()


# Edits that would break open assignments


def refuse_if_invalidated(
    repos: Repos,
    mission: Mission,
    edit: MissionEditKind,
    message: Callable[[list[str]], str],
    *,
    before: MissionEditKind | None = None,
) -> None:
    """Refuse an edit that would break open assignments. `message` gets the names of everyone
    affected, in roster order.

    `before` describes the mission as it is now, in the same terms as `edit`. Conflicts it
    already has don't count, so the edit is refused only for people it would make no longer
    eligible."""
    problems, names = invalidated(repos, mission, edit, before=before)
    if problems:
        raise RuleViolation(message(names), problems)


def invalidated(
    repos: Repos,
    mission: Mission,
    edit: MissionEditKind,
    *,
    before: MissionEditKind | None = None,
) -> tuple[list[Problem], list[str]]:
    """The open assignments the edit would break, and the names of everyone affected in roster
    order. Both are empty if the edit is safe. `before` is as for `refuse_if_invalidated`."""
    roster = repos.facts.roster(mission.id)
    problems = invalidated_by(edit, roster)
    if before is not None and problems:
        existing = {_conflict(p) for p in invalidated_by(before, roster)}
        problems = [p for p in problems if _conflict(p) not in existing]
    names = {e.crew.crew_profile_id: e.crew.name for e in roster}
    affected: list[int] = []
    for p in problems:
        ids = p.refs.get("crew_profile_ids") or [p.refs["crew_profile_id"]]
        affected += [i for i in ids if isinstance(i, int) and i not in affected]
    return problems, [names[i] for i in affected]


# What identifies a conflict's cause, so the same conflict is recognised before and after an
# edit: an overlap by the other mission and a shortfall by the skill, since the overlapping days
# and the level needed can move. An unavailability's message names its own period, which no
# mission edit changes.
_CAUSE_REF = MappingProxyType({"overlap": "mission_id", "skill_below_minimum": "skill_id"})


def _conflict(p: Problem) -> tuple[object, ...]:
    """Who, in which slot, and why."""
    cause = _CAUSE_REF.get(p.code)
    return (
        p.code,
        p.refs.get("crew_profile_id"),
        p.refs.get("slot_id"),
        p.refs[cause] if cause is not None else p.message,
    )


# Recording a change


def record_change(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    status: MissionStatus,
    event: Event,
    mission_name: str,
    data: Mapping[str, object],
) -> None:
    """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
    and, if a Pending mission went back to Draft, that return with its cause. `mission_name` is
    the mission's name once the change is made; the audit `data` starts with it."""
    ctx.audit(event, mission_id=mission.id, data={"mission_name": mission_name, **data})
    if status != mission.status:
        return_to_draft(ctx, repos, mission, event, mission_name)
