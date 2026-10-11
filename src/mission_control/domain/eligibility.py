"""Who can fill a slot, how loaded they are, and which edits would break existing assignments."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem
from mission_control.domain.records import (
    ActiveAssignment,
    AssignmentFact,
    CandidateFacts,
    Requirement,
    RosterEntry,
    SlotSpec,
)


def _span(window: DateRange) -> str:
    return f"{window.start.isoformat()} to {window.end.isoformat()}"


def ineligibility_reasons(
    person: CandidateFacts, slot: SlotSpec, window: DateRange
) -> list[Problem]:
    """Every reason `person` can't fill `slot` for `window`. Empty means eligible."""
    problems: list[Problem] = []
    ref = {"crew_profile_id": person.crew_profile_id, "slot_id": slot.id}

    if not person.active:
        problems.append(Problem("inactive", f"{person.name} is deactivated", ref))

    problems.extend(_skill_shortfalls(person, slot.requirements, ref))
    problems.extend(_availability_conflicts(person, window, ref))
    return problems


def is_eligible(person: CandidateFacts, slot: SlotSpec, window: DateRange) -> bool:
    return not ineligibility_reasons(person, slot, window)


def _availability_conflicts(
    person: CandidateFacts, window: DateRange, ref: dict[str, int | str]
) -> list[Problem]:
    """Unavailability or accepted assignments elsewhere that overlap `window`."""
    problems = []
    for blocked in person.unavailable:
        if blocked.overlaps(window):
            problems.append(
                Problem("unavailable", f"{person.name} is unavailable {_span(blocked)}", ref)
            )
    for other in person.accepted_elsewhere:
        if other.window.overlaps(window):
            shared = DateRange(
                max(other.window.start, window.start), min(other.window.end, window.end)
            )
            problems.append(
                Problem(
                    "overlap",
                    f"{person.name} has an accepted assignment on {other.mission_name} "
                    f"overlapping {_span(shared)}",
                    {**ref, "mission_id": other.mission_id, "mission_name": other.mission_name},
                )
            )
    return problems


def _skill_shortfalls(
    person: CandidateFacts, requirements: Iterable[Requirement], ref: dict[str, int | str]
) -> list[Problem]:
    problems = []
    for r in requirements:
        level = person.skills.get(r.skill_id)
        if level is None or level < r.min_level:
            have = (
                f"doesn't have {r.skill_name}" if level is None else (f"has {r.skill_name} {level}")
            )
            problems.append(
                Problem(
                    "skill_below_minimum",
                    f"{person.name} {have} (needs {r.min_level})",
                    {**ref, "skill_id": r.skill_id},
                )
            )
    return problems


# Workload


def workload(assignments: Iterable[AssignmentFact], excluding_mission_id: int) -> int:
    """Mission-days of accepted assignments on missions that aren't completed."""
    return sum(
        a.window.mission_days
        for a in assignments
        if a.assignment_status == AssignmentStatus.ACCEPTED
        and a.mission_status != MissionStatus.COMPLETED
        and a.mission_id != excluding_mission_id
    )


# Edits that would invalidate open assignments


@dataclass(frozen=True)
class SlotRemoval:
    slot_id: int


@dataclass(frozen=True)
class SlotEdit:
    slot_id: int
    headcount: int | None = None
    requirements: tuple[Requirement, ...] | None = None


@dataclass(frozen=True)
class DatesEdit:
    window: DateRange


MissionEditKind = SlotRemoval | SlotEdit | DatesEdit


def invalidated_by(edit: MissionEditKind, roster: Sequence[RosterEntry]) -> list[Problem]:
    """Every open assignment the edit would break. Empty means the edit is safe."""
    if isinstance(edit, DatesEdit):
        return [
            _in_slot(e, p)
            for e in roster
            for p in _availability_conflicts(e.crew, edit.window, _refs(e))
        ]

    in_slot = [e for e in roster if e.slot.id == edit.slot_id]

    if isinstance(edit, SlotRemoval):
        return [
            Problem(
                "slot_has_open_assignments",
                f"{e.slot.name}: {e.crew.name} is still assigned",
                _refs(e),
            )
            for e in in_slot
        ]

    problems: list[Problem] = []
    if edit.headcount is not None and edit.headcount < len(in_slot):
        names = _join_names([e.crew.name for e in in_slot])
        problems.append(
            Problem(
                "headcount_below_open_assignments",
                f"{in_slot[0].slot.name}: {names} are assigned, more than the new headcount "
                f"of {edit.headcount}",
                {
                    "slot_id": edit.slot_id,
                    "crew_profile_ids": [e.crew.crew_profile_id for e in in_slot],
                },
            )
        )
    if edit.requirements is not None:
        for e in in_slot:
            problems.extend(
                _in_slot(e, p) for p in _skill_shortfalls(e.crew, edit.requirements, _refs(e))
            )
    return problems


def _join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _refs(e: RosterEntry) -> dict[str, int | str]:
    """The records every problem about this assignment names."""
    return {
        "assignment_id": e.assignment_id,
        "crew_profile_id": e.crew.crew_profile_id,
        "slot_id": e.slot.id,
    }


def _in_slot(e: RosterEntry, p: Problem) -> Problem:
    """`p` with the slot's name in front of its message."""
    return Problem(p.code, f"{e.slot.name}: {p.message}", p.refs)


# Skill changes against Active assignments


def invalidated_by_skill_change(
    person_name: str,
    skill_id: int,
    new_level: int | None,
    active_assignments: Sequence[ActiveAssignment],
) -> list[Problem]:
    """A skill change is refused only if it breaks an assignment on an Active mission.
    `new_level=None` means the skill is being removed."""
    problems = []
    for a in active_assignments:
        for r in a.requirements:
            if r.skill_id == skill_id and (new_level or 0) < r.min_level:
                problems.append(
                    Problem(
                        "invalidates_active_assignment",
                        f"{person_name} needs {r.skill_name} {r.min_level} as {a.slot_name} "
                        f"on active mission {a.mission_name}",
                        {"mission_id": a.mission_id, "skill_id": skill_id},
                    )
                )
    return problems
