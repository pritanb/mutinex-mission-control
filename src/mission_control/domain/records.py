"""Plain facts the domain rules work on. Services build these from the database."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus


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


@dataclass(frozen=True)
class RosterEntry:
    """A proposed or accepted assignment on the mission being checked, edited or submitted.
    `crew.accepted_elsewhere` must exclude this mission."""

    assignment_id: int
    slot: SlotSpec
    crew: CandidateFacts
    status: AssignmentStatus


@dataclass(frozen=True)
class AssignmentFact:
    """One of a person's assignments, as counted towards their workload."""

    mission_id: int
    mission_status: MissionStatus
    assignment_status: AssignmentStatus
    window: DateRange


@dataclass(frozen=True)
class ActiveAssignment:
    """An accepted assignment on an Active mission."""

    mission_id: int
    mission_name: str
    slot_name: str
    requirements: tuple[Requirement, ...]
