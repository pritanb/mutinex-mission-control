"""The HTTP API: JSON under /api/v1, authenticated with `Authorization: Bearer <token>`."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mission_control.api import errors
from mission_control.api.routers import admin, assignments, auth, crew, missions
from mission_control.infra import security
from mission_control.infra.db import connect, init_db
from mission_control.infra.settings import Settings

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Settings come from the environment unless given."""
    config = settings if settings is not None else Settings.from_env(os.environ)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        conn = connect(config.database_path, busy_timeout_ms=config.busy_timeout_ms)
        try:
            init_db(conn)  # refuses an unsupported SQLite or schema; creates an empty schema
        finally:
            conn.close()
        # Login checks unknown emails against this hash, so it costs the same as a real check.
        # Making it now keeps the first such login as slow as every other.
        security.dummy_hash()
        yield

    app = FastAPI(title="Mission Control", lifespan=lifespan)
    app.state.settings = config
    errors.install(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (auth.router, admin.router, crew.router, missions.router, assignments.router):
        app.include_router(router, prefix=API_PREFIX)
    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
