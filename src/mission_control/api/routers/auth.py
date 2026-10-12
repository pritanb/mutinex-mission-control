from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status

from mission_control.api.deps import Conn, Ctx, Token, current_actor, settings
from mission_control.api.schemas.auth import Login, MeOut, PasswordChange, SessionOut
from mission_control.api.schemas.inbox import InboxOut
from mission_control.domain.permissions import Actor
from mission_control.infra.settings import Settings
from mission_control.services import auth, inbox

router = APIRouter(tags=["auth"])

Me = Annotated[Actor, Depends(current_actor)]


@router.post("/auth/login")
def login(body: Login, conn: Conn, config: Annotated[Settings, Depends(settings)]) -> SessionOut:
    lifetime = timedelta(hours=config.token_ttl_hours)
    return SessionOut.of(auth.login(conn, body.email, body.password, lifetime=lifetime))


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(conn: Conn, token: Token, _: Me) -> None:
    assert token is not None  # a valid session was required to get here
    auth.logout(conn, token)


@router.get("/me")
def me(conn: Conn, actor: Me) -> MeOut:
    return MeOut.of_me(auth.whoami(conn, actor))


@router.get("/me/inbox")
def my_inbox(ctx: Ctx) -> InboxOut:
    """What is waiting on you to act."""
    return InboxOut.of(inbox.inbox(ctx))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: PasswordChange, conn: Conn, actor: Me) -> None:
    auth.change_password(conn, actor, body.current_password, body.new_password)
