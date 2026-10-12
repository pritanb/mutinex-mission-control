from collections.abc import Mapping
from datetime import date, datetime

from pydantic import BaseModel, field_validator, model_validator

from mission_control.api.schemas.common import Int, RequestBody
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.records import Requirement
from mission_control.infra.repositories.models import AuditEntry, Mission
from mission_control.services.missions import (
    ApprovalView,
    AssignmentView,
    MissionView,
    SlotInput,
    SlotView,
)

# Requests


class RequirementIn(RequestBody):
    skill_id: Int
    min_level: Int


def _levels(requirements: list[RequirementIn]) -> dict[int, int]:
    return {r.skill_id: r.min_level for r in requirements}


def _no_repeats(requirements: list[RequirementIn] | None) -> list[RequirementIn] | None:
    seen: set[int] = set()
    for r in requirements or ():
        if r.skill_id in seen:
            raise ValueError(f"lists skill {r.skill_id} more than once")
        seen.add(r.skill_id)
    return requirements


class SlotIn(RequestBody):
    name: str
    headcount: Int
    requirements: list[RequirementIn]

    _unique = field_validator("requirements")(_no_repeats)

    def to_input(self) -> SlotInput:
        return SlotInput(self.name, self.headcount, _levels(self.requirements))


class MissionCreate(RequestBody):
    name: str
    start_date: date
    end_date: date
    slots: list[SlotIn]
    owner_id: Int | None = None  # Directors name the Lead; Leads own what they create


class MissionUpdate(RequestBody):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SlotUpdate(RequestBody):
    """Rename or change headcount, or replace the required skills. Each is its own use case and
    transaction, so one request makes only one kind of change."""

    name: str | None = None
    headcount: Int | None = None
    requirements: list[RequirementIn] | None = None

    _unique = field_validator("requirements")(_no_repeats)

    @model_validator(mode="after")
    def _one_kind(self) -> "SlotUpdate":
        if self.requirements is not None and (self.name is not None or self.headcount is not None):
            raise ValueError(
                "Change a slot's required skills separately from its name and headcount"
            )
        return self

    def levels(self) -> dict[int, int] | None:
        return None if self.requirements is None else _levels(self.requirements)


class OwnerChange(RequestBody):
    owner_id: Int


class ReasonIn(RequestBody):
    reason: str | None = None  # required to reject or cancel; the service says so if it's missing


# Responses


class RequirementOut(BaseModel):
    skill_id: int
    skill_name: str
    min_level: int

    @classmethod
    def of(cls, r: Requirement) -> "RequirementOut":
        return cls(skill_id=r.skill_id, skill_name=r.skill_name, min_level=r.min_level)


class SlotOut(BaseModel):
    id: int
    position: int
    name: str
    headcount: int
    open_places: int
    requirements: list[RequirementOut]

    @classmethod
    def of(cls, s: SlotView) -> "SlotOut":
        return cls(
            id=s.id,
            position=s.position,
            name=s.name,
            headcount=s.headcount,
            open_places=s.open_places,
            requirements=[RequirementOut.of(r) for r in s.requirements],
        )


class RosterAssignmentOut(BaseModel):
    id: int
    slot_id: int
    slot_name: str
    crew_profile_id: int
    crew_name: str
    status: AssignmentStatus
    reason: str | None

    @classmethod
    def of(cls, a: AssignmentView) -> "RosterAssignmentOut":
        return cls(
            id=a.id,
            slot_id=a.slot_id,
            slot_name=a.slot_name,
            crew_profile_id=a.crew_profile_id,
            crew_name=a.crew_name,
            status=a.status,
            reason=a.reason,
        )


class ApprovalOut(BaseModel):
    director_id: int
    director_name: str
    decision: str
    reason: str | None

    @classmethod
    def of(cls, a: ApprovalView) -> "ApprovalOut":
        return cls(
            director_id=a.director_id,
            director_name=a.director_name,
            decision=a.decision,
            reason=a.reason,
        )


class MissionSummaryOut(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    status: MissionStatus
    owner_id: int
    created_by_id: int
    approval_round: int
    approvals_required: int | None  # fixed when the mission is submitted

    @classmethod
    def of(cls, m: Mission) -> "MissionSummaryOut":
        return cls(**_summary(m))


class MissionOut(MissionSummaryOut):
    """A mission with its live slots in listed order, every assignment it has had, and the
    approvals of its current round."""

    owner_name: str
    created_by_name: str
    slots: list[SlotOut]
    assignments: list[RosterAssignmentOut]
    approvals: list[ApprovalOut]

    @classmethod
    def of_view(cls, v: MissionView) -> "MissionOut":
        return cls(
            **_summary(v.mission),
            owner_name=v.owner_name,
            created_by_name=v.created_by_name,
            slots=[SlotOut.of(s) for s in v.slots],
            assignments=[RosterAssignmentOut.of(a) for a in v.assignments],
            approvals=[ApprovalOut.of(a) for a in v.approvals],
        )


def _summary(m: Mission) -> dict[str, object]:
    return {
        "id": m.id,
        "name": m.name,
        "start_date": m.window.start,
        "end_date": m.window.end,
        "status": m.status,
        "owner_id": m.owner_id,
        "created_by_id": m.created_by_id,
        "approval_round": m.approval_round,
        "approvals_required": m.approvals_required,
    }


class HistoryEntryOut(BaseModel):
    """One event in a mission's history: who did what, when, and the names at the time."""

    id: int
    created_at: datetime
    actor_id: int
    actor_name: str
    event: str
    assignment_id: int | None
    crew_profile_id: int | None
    from_status: str | None
    to_status: str | None
    reason: str | None
    data: Mapping[str, object]

    @classmethod
    def of(cls, e: AuditEntry) -> "HistoryEntryOut":
        return cls(
            id=e.id,
            created_at=e.at,
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            event=e.event,
            assignment_id=e.assignment_id,
            crew_profile_id=e.crew_profile_id,
            from_status=e.from_status,
            to_status=e.to_status,
            reason=e.reason,
            data=dict(e.data),
        )
