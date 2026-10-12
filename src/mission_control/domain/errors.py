from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class Problem:
    """One reason an action can't go ahead. `refs` names the records involved. It is copied
    into a read-only mapping, so no two problems share it and it can't be changed later."""

    code: str
    message: str
    refs: Mapping[str, int | str | list[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "refs", MappingProxyType(dict(self.refs)))


class Forbidden(Exception):
    """The actor can see the resource but isn't allowed to do this."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Unauthenticated(Exception):
    """No valid identity: bad credentials, or a missing, expired or revoked session."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NotFound(Exception):
    """Missing, belonging to another organisation, or not visible to the actor. All three look
    the same, so a response never reveals that something exists."""

    code = "not_found"

    def __init__(self, what: str) -> None:
        self.message = f"{what} not found"
        super().__init__(self.message)


class RuleViolation(Exception):
    """A change conflicts with the rules or the current state. Carries every problem at once."""

    def __init__(self, message: str, problems: Sequence[Problem], code: str = "rule_violation"):
        if not problems:
            raise ValueError("a RuleViolation needs at least one problem")
        super().__init__(message)
        self.code = code
        self.message = message
        self.problems = tuple(problems)

    @classmethod
    def of(cls, problem: Problem) -> "RuleViolation":
        """A refusal with a single reason takes that reason's code and message."""
        return cls(problem.message, [problem], code=problem.code)


class InvalidInput(ValueError):
    """A value the caller supplied is malformed, e.g. a blank name or a level out of range.
    Answered as 422. Distinct from plain ValueError, which also signals programming errors."""

    code = "validation_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
