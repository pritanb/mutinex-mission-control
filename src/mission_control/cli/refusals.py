"""Turning a refusal into what the user reads: the message, one bullet per problem that adds
something, and a next step for the codes we know."""

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass

from mission_control.cli.client import ApiError, Unreachable
from mission_control.cli.env import Env
from mission_control.cli.errors import INTERRUPTED, UNAVAILABLE, CliError
from mission_control.cli.render import sentence

# A mission's state stopped the action. The message says "a mission", so the CLI adds which one.
STATE_CODES = frozenset({"mission_frozen", "mission_final", "invalid_transition"})

GENERIC_HINTS = {
    "unauthenticated": "Log in: mc login",
    "busy": "Try again in a moment.",
    "unexpected_response": "Try again. If it keeps happening, check the server's log.",
}


@dataclass(frozen=True)
class Shown:
    message: str
    bullets: tuple[str, ...]
    hints: tuple[str, ...]


@contextmanager
def refusals(
    subject: str | None = None, *, name_state: bool = False, **hints: str
) -> Generator[None]:
    """Give refusals raised inside the block the context only the command knows: the `subject`
    (e.g. "Mission 5") for a not-found message, whether a state refusal should name it, and a
    hint per code. A hint may use `{name}` placeholders filled from the problem's refs."""
    try:
        yield
    except ApiError as error:
        if error.subject is None:
            error.subject = subject
            error.name_state = name_state
        error.hints = hints | error.hints
        raise


def present(error: ApiError) -> Shown:
    message = error.message
    subject = error.subject
    if subject:
        kind = subject.split()[0]
        if error.code == "not_found" and message.lower() == f"{kind} not found".lower():
            message = f"{subject} not found"
        elif error.code in STATE_CODES and error.name_state:
            message = f"{subject}: {message}"

    bullets = tuple(p.message for p in error.problems if p.message and p.message != error.message)

    hints: list[str] = []
    for code, refs in ((error.code, {}), *((p.code, p.refs) for p in error.problems)):
        hint = _fill(error.hints.get(code) or GENERIC_HINTS.get(code), refs)
        if hint and hint not in hints:
            hints.append(hint)
    return Shown(sentence(message), bullets, tuple(hints))


def _fill(template: str | None, refs: Mapping[str, object]) -> str | None:
    """A hint may name a record from the problem's refs, e.g. `{assignment_id}`. Without that
    ref the hint is skipped rather than shown half-filled."""
    if template is None:
        return None
    try:
        return template.format_map(dict(refs))
    except (KeyError, IndexError, ValueError):
        return None


def report(env: Env, failure: BaseException) -> int:
    """Show a failure on stderr (or a refusal's error body on stdout, with `--json`) and return
    the exit code to use."""
    term = env.term
    if isinstance(failure, KeyboardInterrupt):
        term.say()
        term.say("Cancelled.")
        return INTERRUPTED
    if isinstance(failure, Unreachable):
        term.error(
            f"Can't reach the Mission Control server at {failure.url}.",
            hint="Is it running? Start it with: uv run mc-server",
        )
        return UNAVAILABLE
    if isinstance(failure, ApiError):
        if env.json_output and failure.has_error_body:
            term.json(failure.body)
        else:
            shown = present(failure)
            term.error(shown.message, shown.bullets, shown.hints)
        return failure.exit_code
    if isinstance(failure, CliError):
        term.error(sentence(failure.message), failure.bullets, failure.hint)
        return failure.exit_code
    raise failure
