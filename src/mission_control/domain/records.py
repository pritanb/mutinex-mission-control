"""Plain facts the domain rules work on. Services build these from the database."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.dates import DateRange


@dataclass(frozen=True)
class Requirement:
    skill_id: int
    skill_name: str
    min_level: int


@dataclass(frozen=True)
class SlotSpec:
    id: int
    position: int
    name: str
    open_places: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class Commitment:
    """An accepted assignment on another non-final mission."""

    mission_id: int
    mission_name: str
    window: DateRange


@dataclass(frozen=True)
class CandidateFacts:
    crew_profile_id: int
    name: str
    active: bool
    skills: Mapping[int, int]  # skill_id -> level
    unavailable: tuple[DateRange, ...]
    accepted_elsewhere: tuple[Commitment, ...]
    workload: int
