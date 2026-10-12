from pydantic import BaseModel

from mission_control.api.schemas.common import Int, RequestBody
from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories.models import Assignment


class Proposal(RequestBody):
    slot_id: Int
    crew_profile_id: Int


class Reason(RequestBody):
    reason: str | None = None


class AssignmentOut(BaseModel):
    id: int
    mission_id: int
    slot_id: int
    crew_profile_id: int
    status: AssignmentStatus
    reason: str | None

    @classmethod
    def of(cls, a: Assignment) -> "AssignmentOut":
        return cls(
            id=a.id,
            mission_id=a.mission_id,
            slot_id=a.slot_id,
            crew_profile_id=a.crew_profile_id,
            status=a.status,
            reason=a.reason,
        )
