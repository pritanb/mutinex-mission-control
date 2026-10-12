from fastapi import APIRouter, status

from mission_control.api.deps import Ctx
from mission_control.api.schemas.assignments import AssignmentOut
from mission_control.api.schemas.common import PathId
from mission_control.api.schemas.matching import MatchPreviewOut
from mission_control.api.schemas.missions import (
    HistoryEntryOut,
    MissionCreate,
    MissionOut,
    MissionSummaryOut,
    MissionUpdate,
    OwnerChange,
    ReasonIn,
    SlotIn,
    SlotUpdate,
)
from mission_control.services import approvals, audit, matching, missions

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("")
def list_missions(ctx: Ctx) -> list[MissionSummaryOut]:
    return [MissionSummaryOut.of(m) for m in missions.list_missions(ctx)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_mission(body: MissionCreate, ctx: Ctx) -> MissionOut:
    view = missions.create_mission(
        ctx,
        name=body.name,
        start=body.start_date,
        end=body.end_date,
        slots=[s.to_input() for s in body.slots],
        owner_id=body.owner_id,
    )
    return MissionOut.of_view(view)


@router.get("/{mission_id}")
def view_mission(mission_id: PathId, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(missions.get_mission(ctx, mission_id))


@router.patch("/{mission_id}")
def update_mission(mission_id: PathId, body: MissionUpdate, ctx: Ctx) -> MissionOut:
    view = missions.update_mission(
        ctx, mission_id, name=body.name, start=body.start_date, end=body.end_date
    )
    return MissionOut.of_view(view)


@router.post("/{mission_id}/slots", status_code=status.HTTP_201_CREATED)
def add_slot(mission_id: PathId, body: SlotIn, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(missions.add_slot(ctx, mission_id, body.to_input()))


@router.patch("/{mission_id}/slots/{slot_id}")
def update_slot(mission_id: PathId, slot_id: PathId, body: SlotUpdate, ctx: Ctx) -> MissionOut:
    """Rename or change the headcount, or replace the required skills."""
    levels = body.levels()
    if levels is not None:
        view = missions.replace_requirements(ctx, mission_id, slot_id, levels)
    else:
        view = missions.update_slot(
            ctx, mission_id, slot_id, name=body.name, headcount=body.headcount
        )
    return MissionOut.of_view(view)


@router.delete("/{mission_id}/slots/{slot_id}")
def remove_slot(mission_id: PathId, slot_id: PathId, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(missions.remove_slot(ctx, mission_id, slot_id))


@router.post("/{mission_id}/owner")
def transfer_ownership(mission_id: PathId, body: OwnerChange, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(missions.transfer_ownership(ctx, mission_id, body.owner_id))


@router.get("/{mission_id}/match")
def preview_match(mission_id: PathId, ctx: Ctx) -> MatchPreviewOut:
    return MatchPreviewOut.of(matching.preview(ctx, mission_id))


@router.post("/{mission_id}/match/apply", status_code=status.HTTP_201_CREATED)
def apply_match(mission_id: PathId, ctx: Ctx) -> list[AssignmentOut]:
    """Propose the suggested crew; they still have to accept."""
    return [AssignmentOut.of(a) for a in matching.apply(ctx, mission_id)]


# Lifecycle


@router.post("/{mission_id}/submit")
def submit(mission_id: PathId, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(approvals.submit(ctx, mission_id))


@router.post("/{mission_id}/approve")
def approve(mission_id: PathId, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(approvals.approve(ctx, mission_id))


@router.post("/{mission_id}/reject")
def reject(mission_id: PathId, ctx: Ctx, body: ReasonIn | None = None) -> MissionOut:
    reason = body.reason if body is not None else None
    return MissionOut.of_view(approvals.reject(ctx, mission_id, reason))


@router.post("/{mission_id}/complete")
def complete(mission_id: PathId, ctx: Ctx) -> MissionOut:
    return MissionOut.of_view(missions.complete_mission(ctx, mission_id))


@router.post("/{mission_id}/cancel")
def cancel(mission_id: PathId, ctx: Ctx, body: ReasonIn | None = None) -> MissionOut:
    reason = body.reason if body is not None else None
    return MissionOut.of_view(missions.cancel_mission(ctx, mission_id, reason))


@router.get("/{mission_id}/history")
def history(mission_id: PathId, ctx: Ctx) -> list[HistoryEntryOut]:
    return [HistoryEntryOut.of(e) for e in audit.mission_history(ctx, mission_id)]
