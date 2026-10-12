from datetime import datetime

from pydantic import BaseModel

from mission_control.api.schemas.admin import UserOut
from mission_control.api.schemas.common import RequestBody
from mission_control.services.auth import Me, Session


class Login(RequestBody):
    email: str
    password: str


class SessionOut(BaseModel):
    token: str  # shown once; send it as `Authorization: Bearer <token>`
    expires_at: datetime
    user: UserOut

    @classmethod
    def of(cls, session: Session) -> "SessionOut":
        return cls(
            token=session.token, expires_at=session.expires_at, user=UserOut.of(session.user)
        )


class OrganisationRef(BaseModel):
    id: int
    name: str
    slug: str


class MeOut(UserOut):
    """The caller's own account, organisation and crew profile."""

    crew_profile_id: int | None
    organisation: OrganisationRef

    @classmethod
    def of_me(cls, me: Me) -> "MeOut":
        org = me.organisation
        return cls(
            **UserOut.of(me.user).model_dump(),
            crew_profile_id=me.crew_profile_id,
            organisation=OrganisationRef(id=org.id, name=org.name, slug=org.slug),
        )


class PasswordChange(RequestBody):
    current_password: str
    new_password: str
