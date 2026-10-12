"""Failures the CLI reports itself, before or instead of asking the server, and the exit codes
every command uses."""

from collections.abc import Sequence

OK = 0
REFUSED = 1
USAGE = 2
AUTHENTICATION = 3
UNAVAILABLE = 4
INTERRUPTED = 130


class CliError(Exception):
    """Something to tell the user, with an optional next step, and the exit code to use."""

    exit_code = REFUSED

    def __init__(self, message: str, *, hint: str | None = None, bullets: Sequence[str] = ()):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.bullets = tuple(bullets)


class Refused(CliError):
    """A reference that doesn't match anything, e.g. an email nobody has."""


class Declined(CliError):
    """The user answered no to a confirmation."""

    def __init__(self) -> None:
        super().__init__("Nothing was changed.")


class UsageProblem(CliError):
    """Input the CLI can't use, found before anything was sent."""

    exit_code = USAGE


class NotLoggedIn(CliError):
    exit_code = AUTHENTICATION

    def __init__(self) -> None:
        super().__init__("You're not logged in.", hint="Log in: mc login")
