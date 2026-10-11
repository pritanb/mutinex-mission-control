"""What the repositories return. Plain frozen records; no database types leak out."""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.records import Requirement


@dataclass(frozen=True)
class Organisation:
    id: int
    name: str
    slug: str
    required_approvals: int


@dataclass(frozen=True)
class User:
    """Never carries the password hash; only the security module reads that."""

    id: int
    org_id: int
    email: str
    name: str
    role: Role
    is_active: bool


@dataclass(frozen=True)
class CrewProfile:
    id: int
    org_id: int
    user_id: int
    display_name: str
    bio: str | None


@dataclass(frozen=True)
class Skill:
    id: int
    org_id: int
    name: str
    category: str | None


@dataclass(frozen=True)
class Unavailability:
    id: int
    crew_profile_id: int
    window: DateRange
    reason: str


@dataclass(frozen=True)
class Mission:
    id: int
    org_id: int
    name: str
    window: DateRange
    status: MissionStatus
    owner_id: int
    created_by_id: int
    approval_round: int
    approvals_required: int | None


@dataclass(frozen=True)
class Slot:
    id: int
    mission_id: int
    name: str
    headcount: int
    position: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class Assignment:
    id: int
    mission_id: int
    slot_id: int
    crew_profile_id: int
    status: AssignmentStatus
    reason: str | None


@dataclass(frozen=True)
class Approval:
    id: int
    mission_id: int
    round: int
    director_id: int
    decision: str
    reason: str | None


@dataclass(frozen=True)
class AssignmentSummary:
    """One line of a crew member's history, readable even after they've left the mission."""

    assignment_id: int
    mission_id: int
    mission_name: str
    window: DateRange
    mission_status: MissionStatus
    slot_name: str
    status: AssignmentStatus
    reason: str | None
