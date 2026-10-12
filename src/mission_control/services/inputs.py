"""Checks on what callers pass in, shared by every use case. Malformed values are refused as
InvalidInput (422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from datetime import date

from mission_control.domain.errors import InvalidInput, Problem


def refuse_input(problems: Sequence[Problem]) -> None:
    if problems:
        raise invalid_input(problems)


def invalid_input(problems: Sequence[Problem]) -> InvalidInput:
    """Every mistake at once; the message is the only one's, or a summary of several."""
    message = problems[0].message if len(problems) == 1 else "Some values aren't valid"
    return InvalidInput(message, problems)


def invalid(message: str, refs: Mapping[str, int] | None = None) -> Problem:
    return Problem("validation_error", message, refs or {})


def date_problems(start: date, end: date) -> list[Problem]:
    if end >= start:
        return []
    return [invalid(f"The end date {end.isoformat()} is before the start date {start.isoformat()}")]


def required_reason(reason: str | None, doing: str) -> str:
    """The reason, without surrounding spaces. A missing or blank one is refused, e.g. "Cancelling
    Lunar Relay needs a reason" for `doing="Cancelling Lunar Relay"`."""
    given = (reason or "").strip()
    if not given:
        raise InvalidInput(f"{doing} needs a reason")
    return given
