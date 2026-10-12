"""The `mc` entry point: every command group, the global options, and a quiet exit when the
reader of a pipe goes away."""

import os
import sys
from typing import Annotated

import typer

from mission_control.cli.base import version_flag
from mission_control.cli.commands import account, admin, assignments, crew, me, missions
from mission_control.cli.commands.common import group
from mission_control.cli.env import Env

app = group(name="mc")
account.register(app)
app.add_typer(me.app, name="me")
app.add_typer(assignments.app, name="assignments")
app.add_typer(missions.app, name="missions")
app.add_typer(crew.app, name="crew")
app.add_typer(admin.users_app, name="users")
app.add_typer(admin.skills_app, name="skills")
app.add_typer(admin.org_app, name="org")

Version = Annotated[bool, version_flag("mc")]


@app.callback()
def root(ctx: typer.Context, show_version: Version = False) -> None:
    """Mission Control: plan missions, crew them and get them approved.

    Start with mc login, then mc inbox. Every command has --help.

    Exit codes: 0 OK, 1 refused, 2 usage, 3 not logged in, 4 server unreachable or busy,
    130 interrupted.
    """
    if ctx.obj is None:
        ctx.obj = Env()


def main() -> None:
    try:
        app(prog_name="mc")
    finally:
        _flush_quietly()


def _flush_quietly() -> None:
    """`mc ... | head` closes the pipe early; don't end with a broken-pipe traceback."""
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
