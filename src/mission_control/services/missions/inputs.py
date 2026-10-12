"""What callers pass in to the mission use cases, and the checks on it. Malformed values are
refused as InvalidInput (422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from mission_control.domain.errors import Problem
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL, Requirement
from mission_control.services.inputs import invalid


@dataclass(frozen=True)
class SlotInput:
    """A slot as given by the caller. `requirements` maps skill id to minimum level."""

    name: str
    headcount: int
    requirements: Mapping[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", MappingProxyType(dict(self.requirements)))


def name_problems(name: str) -> list[Problem]:
    return [] if name.strip() else [invalid("The mission needs a name")]


def slot_problems(
    label: str,
    name: str | None,
    headcount: int | None,
    requirements: Mapping[int, int] | None,
    refs: Mapping[str, int] | None = None,
) -> list[Problem]:
    """What's wrong with a slot's given values. None means the value isn't being set. `refs`
    names the slot, if it already exists."""
    problems = []
    if name is not None and not name.strip():
        problems.append(invalid("Every slot needs a name", refs))
    if headcount is not None and headcount < 1:
        problems.append(invalid(f"{label} needs a headcount of at least 1", refs))
    if requirements is not None:
        if not requirements:
            problems.append(invalid(f"{label} needs at least one required skill", refs))
        for level in requirements.values():
            if not MIN_LEVEL <= level <= MAX_LEVEL:
                problems.append(
                    invalid(
                        f"{label}: a minimum skill level must be from {MIN_LEVEL} to "
                        f"{MAX_LEVEL}, not {level}",
                        refs,
                    )
                )
    return problems


def slot_label(name: str) -> str:
    """How a slot is named in a message, even if its name is blank."""
    return name.strip() or "A slot"


def levels(requirements: Sequence[Requirement]) -> dict[int, int]:
    return {r.skill_id: r.min_level for r in requirements}


def requirement_data(requirements: Sequence[Requirement]) -> list[dict[str, object]]:
    """Requirements for an audit event, with the skill names at the time."""
    return [
        {"skill_id": r.skill_id, "skill_name": r.skill_name, "min_level": r.min_level}
        for r in requirements
    ]
