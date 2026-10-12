from fastapi import APIRouter, status

from mission_control.api.deps import Ctx
from mission_control.api.schemas.assignments import AssignmentOut, Proposal, Reason
from mission_control.api.schemas.common import PathId
from mission_control.api.schemas.crew import AssignmentSummaryOut
from mission_control.services import assignments

router = APIRouter(tags=["assignments"])


@router.post("/missions/{mission_id}/assignments", status_code=status.HTTP_201_CREATED)
def propose(mission_id: PathId, body: Proposal, ctx: Ctx) -> AssignmentOut:
    made = assignments.propose(ctx, mission_id, body.slot_id, body.crew_profile_id)
    return AssignmentOut.of(made)


@router.get("/assignments")
def my_assignments(ctx: Ctx, pending: bool = False) -> list[AssignmentSummaryOut]:
    """Your own assignments, newest first; `pending=true` for proposals awaiting your reply."""
    return [AssignmentSummaryOut.of(a) for a in assignments.my_assignments(ctx, pending)]


@router.post("/assignments/{assignment_id}/accept")
def accept(assignment_id: PathId, ctx: Ctx) -> AssignmentOut:
    return AssignmentOut.of(assignments.accept(ctx, assignment_id))


@router.post("/assignments/{assignment_id}/decline")
def decline(assignment_id: PathId, ctx: Ctx, body: Reason | None = None) -> AssignmentOut:
    reason = body.reason if body is not None else None
    return AssignmentOut.of(assignments.decline(ctx, assignment_id, reason))


@router.post("/assignments/{assignment_id}/withdraw")
def withdraw(assignment_id: PathId, ctx: Ctx, body: Reason | None = None) -> AssignmentOut:
    """A reason is required; leaving it out is refused with the service's own message."""
    reason = body.reason if body is not None else None
    return AssignmentOut.of(assignments.withdraw(ctx, assignment_id, reason))


@router.post("/assignments/{assignment_id}/remove")
def remove(assignment_id: PathId, ctx: Ctx) -> AssignmentOut:
    return AssignmentOut.of(assignments.remove(ctx, assignment_id))
