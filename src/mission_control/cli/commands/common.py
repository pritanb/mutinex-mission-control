"""Plumbing every command shares: the group and command classes (help layout, error handling),
the current `Env`, and common options."""

from datetime import date
from typing import Annotated, Any

import typer
from typer.core import TyperCommand, TyperGroup

from mission_control.cli.client import ApiError, Unreachable
from mission_control.cli.env import Env
from mission_control.cli.errors import CliError
from mission_control.cli.refusals import report


class Command(TyperCommand):
    """Usage lines that spell out the options (`mc missions match MISSION_ID [--apply]`), and
    the epilog shown as an example block."""

    def collect_usage_pieces(self, ctx: typer.Context) -> list[str]:
        pieces: list[str] = []
        options: list[str] = []
        for param in self.get_params(ctx):
            if param.param_type_name == "argument":
                pieces.append(param.make_metavar(ctx))
            elif param.param_type_name == "option" and param.name != "help" and not param.hidden:
                flag = max(param.opts, key=len)
                text = flag if param.is_flag else f"{flag} {param.make_metavar(ctx)}"
                options.append(text if param.required else f"[{text}]")
        return pieces + options

    def format_epilog(self, ctx: typer.Context, formatter: Any) -> None:
        if not self.epilog:
            return
        examples = [line.strip() for line in self.epilog.strip().splitlines() if line.strip()]
        formatter.write_paragraph()
        formatter.write_text("Example:" if len(examples) == 1 else "Examples:")
        with formatter.indentation():
            for line in examples:
                formatter.write(f"{' ' * formatter.current_indent}{line}\n")


class Group(TyperGroup):
    """A bare group prints its help and exits 0. Failures raised by commands are reported here
    with their exit code, so tests and real runs behave the same."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except (CliError, ApiError, Unreachable, KeyboardInterrupt) as failure:
            env = ctx.find_object(Env) or Env()
            raise typer.Exit(report(env, failure)) from None


def group(help: str | None = None, name: str | None = None) -> typer.Typer:
    """A command group. Without `help`, its callback's docstring is the help."""
    named: dict[str, str] = {"help": help} if help else {}
    if name:
        named["name"] = name
    return typer.Typer(
        cls=Group,
        rich_markup_mode=None,
        add_completion=False,
        pretty_exceptions_enable=False,
        **named,
    )


def start(ctx: typer.Context, json_output: bool = False) -> Env:
    """The command's Env, remembering whether output is JSON so refusals print as JSON too."""
    env = ctx.ensure_object(Env)
    env.json_output = json_output
    return env


def iso_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise typer.BadParameter(
            f"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2027-03-01."
        ) from None


Json = Annotated[bool, typer.Option("--json", help="Print the result as JSON")]
Yes = Annotated[bool, typer.Option("--yes", "-y", help="Don't ask for confirmation")]
MissionId = Annotated[int, typer.Argument(metavar="MISSION_ID", help="The mission's ID")]
Email = Annotated[str, typer.Argument(metavar="EMAIL", help="The person's email address")]


def command(app: typer.Typer, name: str, example: str | None = None, **settings: Any) -> Any:
    """Register a command with the shared help layout. `example` lines appear under Example."""
    return app.command(name, cls=Command, epilog=example, **settings)
