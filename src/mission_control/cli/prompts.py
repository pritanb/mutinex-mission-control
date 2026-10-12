"""Asking the user things. Prompts go to the terminal (stderr, or the tty for passwords), never to
stdout. Passwords are read with the input hidden, or from stdin, one line per password, when
there's no terminal."""

import getpass
import sys
from typing import TYPE_CHECKING, Protocol

from mission_control.cli.errors import Declined, UsageProblem

if TYPE_CHECKING:
    from mission_control.cli.env import Env


class Prompter(Protocol):
    def ask(self, label: str) -> str: ...

    def ask_hidden(self, label: str) -> str: ...


class TerminalPrompter:
    """Reads answers from the keyboard. Ctrl+C raises KeyboardInterrupt; Ctrl+D is treated the
    same, as a way out."""

    def ask(self, label: str) -> str:
        sys.stderr.write(f"{label}: ")
        sys.stderr.flush()
        line = sys.stdin.readline()
        if not line:
            raise KeyboardInterrupt
        return line.rstrip("\r\n")

    def ask_hidden(self, label: str) -> str:
        try:
            return getpass.getpass(f"{label}: ")
        except EOFError:
            raise KeyboardInterrupt from None


def ask(env: "Env", label: str, *, missing: str) -> str:
    """A visible answer. Without a terminal, fail with `missing` instead of waiting."""
    if not env.is_interactive:
        raise UsageProblem(missing)
    while not (answer := env.prompter.ask(label).strip()):
        pass
    return answer


def ask_secret(env: "Env", label: str) -> str:
    if env.is_interactive:
        return env.prompter.ask_hidden(label)
    line = sys.stdin.readline()
    if not line:
        raise UsageProblem(
            "No password given, and there's no terminal to ask on.",
            hint="Run this in a terminal, or pipe it on stdin.",
        )
    return line.rstrip("\r\n")


def ask_new_secret(env: "Env", label: str, repeat: str, *, mismatch: str) -> str:
    """A password being set. On a terminal it's asked twice, and both answers must match, to catch
    a typo nobody could see. Piped, it's read once."""
    first = ask_secret(env, label)
    if env.is_interactive and first != ask_secret(env, repeat):
        raise UsageProblem(mismatch)
    return first


def confirm(env: "Env", warning: str, *, yes: bool, question: str = "Continue?") -> None:
    """Show `warning` and ask before going ahead. `--yes` skips the question. Without a terminal
    the change needs `--yes`, so a script never waits on a prompt."""
    if yes:
        return
    env.term.warn(warning)
    if not env.is_interactive:
        raise UsageProblem(
            "There's no terminal to confirm on.", hint="Re-run with --yes to go ahead."
        )
    if env.prompter.ask(f"{question} [y/N]").strip().lower() not in ("y", "yes"):
        raise Declined()
