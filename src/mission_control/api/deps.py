"""What each request runs with: one database connection, the caller resolved from their bearer
token, and the service context built from both.

The organisation always comes from the token, never from the request. Nothing about the caller
is cached, so a role change or deactivation applies to their very next request.
"""

import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mission_control.domain.permissions import Actor
from mission_control.infra.db import connect
from mission_control.infra.settings import Settings
from mission_control.services import auth
from mission_control.services.context import ServiceContext

_bearer = HTTPBearer(auto_error=False)


def settings(request: Request) -> Settings:
    return request.app.state.settings


def db(config: Annotated[Settings, Depends(settings)]) -> Generator[sqlite3.Connection]:
    """One connection per request, closed when the response is done."""
    conn = connect(config.database_path, busy_timeout_ms=config.busy_timeout_ms)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(db)]


def bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str | None:
    return credentials.credentials if credentials is not None else None


Token = Annotated[str | None, Depends(bearer_token)]


def current_actor(conn: Conn, token: Token) -> Actor:
    return auth.authenticate(conn, token)


def service_context(conn: Conn, actor: Annotated[Actor, Depends(current_actor)]) -> ServiceContext:
    return ServiceContext(conn, actor)


Ctx = Annotated[ServiceContext, Depends(service_context)]
