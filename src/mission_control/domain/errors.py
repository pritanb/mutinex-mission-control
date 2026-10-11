from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Problem:
    """One reason an action can't go ahead. `refs` names the records involved."""

    code: str
    message: str
    refs: Mapping[str, int | str | list[int]] = field(default_factory=dict)


class Forbidden(Exception):
    """The actor can see the resource but isn't allowed to do this."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
