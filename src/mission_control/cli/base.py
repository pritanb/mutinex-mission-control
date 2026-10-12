"""What both command-line tools, `mc` and `mc-admin`, share: a bare group prints its help, and
`--version` prints the installed version."""

from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import typer
from typer.core import TyperGroup


class HelpWhenBare(TyperGroup):
    """A bare group prints its help and exits 0."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)


def version_flag(program: str) -> Any:
    """The `--version` option for a tool's root callback, as `Annotated[bool, version_flag(...)]`:
    prints `<program> <version>`, then exits."""
    return typer.Option(
        "--version",
        help="Show the version and exit",
        callback=_show_version(program),
        is_eager=True,
    )


def _show_version(program: str) -> Callable[[bool], None]:
    def show(value: bool) -> None:
        if value:
            try:
                number = version("mission-control")
            except PackageNotFoundError:
                number = "unknown"
            typer.echo(f"{program} {number}")
            raise typer.Exit()

    return show
