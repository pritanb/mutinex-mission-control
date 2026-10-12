from pydantic import BaseModel, field_validator, model_validator

from mission_control.api.schemas.common import Int, RequestBody
from mission_control.domain.enums import Role
from mission_control.infra.repositories.models import Organisation, Skill, User

# Organisation


class OrgOut(BaseModel):
    id: int
    name: str
    slug: str
    required_approvals: int

    @classmethod
    def of(cls, org: Organisation) -> "OrgOut":
        return cls(
            id=org.id, name=org.name, slug=org.slug, required_approvals=org.required_approvals
        )


class OrgUpdate(RequestBody):
    required_approvals: Int


# Users


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: Role
    active: bool

    @classmethod
    def of(cls, user: User) -> "UserOut":
        return cls(
            id=user.id, email=user.email, name=user.name, role=user.role, active=user.is_active
        )


class UserCreate(RequestBody):
    email: str
    name: str
    role: Role
    password: str


class UserUpdate(RequestBody):
    """A new role, or `active: false` to deactivate. Both are separate use cases, each in its
    own transaction, so one request makes only one of them."""

    role: Role | None = None
    active: bool | None = None

    @field_validator("active")
    @classmethod
    def _only_deactivate(cls, active: bool | None) -> bool | None:
        if active is True:
            raise ValueError("can only be false: deactivated users can't be reactivated")
        return active

    @model_validator(mode="after")
    def _one_change(self) -> "UserUpdate":
        if self.role is not None and self.active is not None:
            raise ValueError("Change a user's role and deactivate them in separate requests")
        return self


class CrewProfileCreate(RequestBody):
    display_name: str | None = None


# Skills


class SkillOut(BaseModel):
    id: int
    name: str
    category: str | None

    @classmethod
    def of(cls, skill: Skill) -> "SkillOut":
        return cls(id=skill.id, name=skill.name, category=skill.category)


class SkillCreate(RequestBody):
    name: str
    category: str | None = None


class SkillUpdate(RequestBody):
    """A field left out stays as it is; `category: null` clears the category."""

    name: str | None = None
    category: str | None = None
