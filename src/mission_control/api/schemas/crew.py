from datetime import date

from pydantic import BaseModel

from mission_control.api.schemas.common import Int, RequestBody
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.infra.repositories.models import AssignmentSummary, CrewProfile, Unavailability
from mission_control.services.crew import CrewView, SkillLevel, UnavailabilityView


class SkillLevelOut(BaseModel):
    skill_id: int
    skill_name: str
    level: int

    @classmethod
    def of(cls, s: SkillLevel) -> "SkillLevelOut":
        return cls(skill_id=s.skill_id, skill_name=s.skill_name, level=s.level)


class UnavailabilityOut(BaseModel):
    id: int
    start_date: date
    end_date: date
    reason: str | None  # null when the caller may not see it

    @classmethod
    def of(cls, u: UnavailabilityView | Unavailability) -> "UnavailabilityOut":
        return cls(id=u.id, start_date=u.window.start, end_date=u.window.end, reason=u.reason)


class CrewOut(BaseModel):
    crew_profile_id: int
    user_id: int
    name: str
    email: str
    active: bool
    bio: str | None
    skills: list[SkillLevelOut]
    unavailability: list[UnavailabilityOut]

    @classmethod
    def of(cls, v: CrewView) -> "CrewOut":
        return cls(
            crew_profile_id=v.crew_profile_id,
            user_id=v.user_id,
            name=v.name,
            email=v.email,
            active=v.active,
            bio=v.bio,
            skills=[SkillLevelOut.of(s) for s in v.skills],
            unavailability=[UnavailabilityOut.of(u) for u in v.unavailability],
        )


class CrewProfileOut(BaseModel):
    crew_profile_id: int
    user_id: int
    name: str
    bio: str | None

    @classmethod
    def of(cls, p: CrewProfile) -> "CrewProfileOut":
        return cls(crew_profile_id=p.id, user_id=p.user_id, name=p.display_name, bio=p.bio)


class CrewUpdate(RequestBody):
    """A field left out (or null) stays as it is; a blank bio clears it."""

    display_name: str | None = None
    bio: str | None = None


class SkillLevelSet(RequestBody):
    level: Int


class UnavailabilityAdd(RequestBody):
    start_date: date
    end_date: date
    reason: str


class AssignmentSummaryOut(BaseModel):
    """One line of someone's assignment history. It doesn't give access to the mission."""

    assignment_id: int
    mission_id: int
    mission_name: str
    start_date: date
    end_date: date
    mission_status: MissionStatus
    slot_name: str
    status: AssignmentStatus
    reason: str | None

    @classmethod
    def of(cls, a: AssignmentSummary) -> "AssignmentSummaryOut":
        return cls(
            assignment_id=a.assignment_id,
            mission_id=a.mission_id,
            mission_name=a.mission_name,
            start_date=a.window.start,
            end_date=a.window.end,
            mission_status=a.mission_status,
            slot_name=a.slot_name,
            status=a.status,
            reason=a.reason,
        )
