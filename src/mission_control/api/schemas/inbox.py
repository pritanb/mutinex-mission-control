from datetime import date

from pydantic import BaseModel

from mission_control.api.schemas.crew import AssignmentSummaryOut
from mission_control.services.inbox import ApprovalItem, Inbox, MissionItem, UnfilledSlot


class ApprovalItemOut(BaseModel):
    mission_id: int
    mission_name: str
    start_date: date
    end_date: date
    approvals: int
    required: int

    @classmethod
    def of(cls, a: ApprovalItem) -> "ApprovalItemOut":
        return cls(
            mission_id=a.mission_id,
            mission_name=a.mission_name,
            start_date=a.window.start,
            end_date=a.window.end,
            approvals=a.approvals,
            required=a.required,
        )


class UnfilledSlotOut(BaseModel):
    slot_id: int
    slot_name: str
    open_places: int

    @classmethod
    def of(cls, u: UnfilledSlot) -> "UnfilledSlotOut":
        return cls(slot_id=u.slot_id, slot_name=u.slot_name, open_places=u.open_places)


class MissionItemOut(BaseModel):
    mission_id: int
    mission_name: str
    start_date: date
    end_date: date
    unfilled: list[UnfilledSlotOut]
    unanswered: int
    ready: bool  # every place filled and every proposal accepted

    @classmethod
    def of(cls, m: MissionItem) -> "MissionItemOut":
        return cls(
            mission_id=m.mission_id,
            mission_name=m.mission_name,
            start_date=m.window.start,
            end_date=m.window.end,
            unfilled=[UnfilledSlotOut.of(u) for u in m.unfilled],
            unanswered=m.unanswered,
            ready=m.ready,
        )


class InboxOut(BaseModel):
    """What is waiting on the caller: proposals to answer, missions to approve, and their own
    draft missions to staff or submit."""

    proposals: list[AssignmentSummaryOut]
    approvals: list[ApprovalItemOut]
    missions: list[MissionItemOut]

    @classmethod
    def of(cls, box: Inbox) -> "InboxOut":
        return cls(
            proposals=[AssignmentSummaryOut.of(p) for p in box.proposals],
            approvals=[ApprovalItemOut.of(a) for a in box.approvals],
            missions=[MissionItemOut.of(m) for m in box.missions],
        )
