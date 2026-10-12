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
    if user.role != Role.LEAD:
        message = f"{user.name} can't own a mission: only Mission Leads can"
    elif not user.is_active:
        message = f"{user.name} can't own a mission because they're deactivated"
    else:
        return
    raise RuleViolation(message, [Problem("owner_not_active_lead", message, {"user_id": user.id})])


def refuse_taken_name(
    mission: Mission, slots: Sequence[Slot], name: str, slot_id: int | None = None
) -> None:
    """A mission's live slots have different names, ignoring case. `slot_id` is the slot being
    renamed, which may keep its own name."""
    taken = next(
        (s for s in slots if s.id != slot_id and _name_key(s.name) == _name_key(name)), None
    )
    if taken is not None:
        message = f"{mission.name} already has a slot called {taken.name}"
        raise RuleViolation(message, [Problem("already_exists", message, {"slot_id": taken.id})])


def refuse_repeated_names(slots: Sequence[SlotInput]) -> None:
    """A new mission's slots have different names, ignoring case. Every repeated name is listed."""
    first_spelling: dict[str, str] = {}
    repeated: list[str] = []
    for s in slots:
        key = _name_key(s.name)
        if key not in first_spelling:
            first_spelling[key] = s.name.strip()
        elif first_spelling[key] not in repeated:
            repeated.append(first_spelling[key])
    problems = [
        Problem("already_exists", f"More than one slot is called {name}") for name in repeated
    ]
    if problems:
        message = problems[0].message if len(problems) == 1 else "Some slots share a name"
        raise RuleViolation(message, problems)


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
    roster = repos.facts.roster(mission.id)
    problems = invalidated_by(edit, roster)
    if before is not None and problems:
        existing = {_conflict(p) for p in invalidated_by(before, roster)}
        problems = [p for p in problems if _conflict(p) not in existing]
    if not problems:
        return
    names = {e.crew.crew_profile_id: e.crew.name for e in roster}
    affected: list[int] = []
    for p in problems:
        ids = p.refs.get("crew_profile_ids") or [p.refs["crew_profile_id"]]
        affected += [i for i in ids if isinstance(i, int) and i not in affected]
    raise RuleViolation(message([names[i] for i in affected]), problems)


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
    data: Mapping[str, object],
) -> None:
    """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
    and, if a Pending mission went back to Draft, that return with its cause."""
    ctx.audit(event, mission_id=mission.id, data=data)
    if status != mission.status:
        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))


# Wording


def join_names(names: Sequence[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def is_are(names: Sequence[str]) -> str:
    return "is" if len(names) == 1 else "are"
