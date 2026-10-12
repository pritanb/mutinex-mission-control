from fastapi import APIRouter, status

from mission_control.api.deps import Ctx
from mission_control.api.schemas.common import PathId
from mission_control.api.schemas.crew import (
    AssignmentSummaryOut,
    CrewOut,
    CrewProfileOut,
    CrewUpdate,
    SkillLevelOut,
    SkillLevelSet,
    UnavailabilityAdd,
    UnavailabilityOut,
)
from mission_control.services import crew

router = APIRouter(prefix="/crew", tags=["crew"])


@router.get("")
def list_crew(ctx: Ctx) -> list[CrewOut]:
    return [CrewOut.of(v) for v in crew.list_crew(ctx)]


@router.get("/{crew_id}")
def view_crew(crew_id: PathId, ctx: Ctx) -> CrewOut:
    return CrewOut.of(crew.view_crew(ctx, crew_id))


@router.patch("/{crew_id}")
def update_details(crew_id: PathId, body: CrewUpdate, ctx: Ctx) -> CrewProfileOut:
    profile = crew.update_details(ctx, crew_id, display_name=body.display_name, bio=body.bio)
    return CrewProfileOut.of(profile)


@router.put("/{crew_id}/skills/{skill_id}")
def set_skill_level(
    crew_id: PathId, skill_id: PathId, body: SkillLevelSet, ctx: Ctx
) -> SkillLevelOut:
    return SkillLevelOut.of(crew.set_skill_level(ctx, crew_id, skill_id, body.level))


@router.delete("/{crew_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill_level(crew_id: PathId, skill_id: PathId, ctx: Ctx) -> None:
    crew.remove_skill_level(ctx, crew_id, skill_id)


@router.get("/{crew_id}/unavailability")
def list_unavailability(crew_id: PathId, ctx: Ctx) -> list[UnavailabilityOut]:
    return [UnavailabilityOut.of(u) for u in crew.list_unavailability(ctx, crew_id)]


@router.post("/{crew_id}/unavailability", status_code=status.HTTP_201_CREATED)
def add_unavailability(crew_id: PathId, body: UnavailabilityAdd, ctx: Ctx) -> UnavailabilityOut:
    added = crew.add_unavailability(ctx, crew_id, body.start_date, body.end_date, body.reason)
    return UnavailabilityOut.of(added)


@router.delete(
    "/{crew_id}/unavailability/{unavailability_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_unavailability(crew_id: PathId, unavailability_id: PathId, ctx: Ctx) -> None:
    crew.remove_unavailability(ctx, crew_id, unavailability_id)


@router.get("/{crew_id}/assignments")
def assignment_history(crew_id: PathId, ctx: Ctx) -> list[AssignmentSummaryOut]:
    return [AssignmentSummaryOut.of(a) for a in crew.assignment_history(ctx, crew_id)]
