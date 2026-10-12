from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

# SQLite stores 64-bit integers. Anything larger is malformed input, refused as 422 rather than
# failing in the database.
_MIN_INT, _MAX_INT = -(2**63), 2**63 - 1

Int = Annotated[int, Field(ge=_MIN_INT, le=_MAX_INT)]
PathId = Annotated[int, Path(ge=_MIN_INT, le=_MAX_INT)]


class RequestBody(BaseModel):
    """A request body. Unknown fields are refused, so a misspelt field isn't silently ignored."""

    model_config = ConfigDict(extra="forbid")
