"""Your own crew profile: details, skills and unavailability."""

from typing import Annotated, Any

import typer

from mission_control.cli.client import Api
from mission_control.cli.commands.common import Json, command, group, iso_date, start
from mission_control.cli.errors import Refused, UsageProblem
from mission_control.cli.render import Terminal
from mission_control.cli.views import identity, show_profile

app = group("Your profile and availability.")
unavailable_app = group("Dates you can't fly.")
app.add_typer(unavailable_app, name="unavailable")

AwayFrom = Annotated[
    str,
    typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="First day you're away"),
]
AwayTo = Annotated[
    str,
    typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="Last day you're away"),
]
AwayReason = Annotated[
    str, typer.Option("--reason", metavar="TEXT", help="Why (only Directors and you see it)")
]


def _profile_id(api: Api) -> tuple[dict[str, Any], int]:
    me = api.get("/me")
    profile_id = me.get("crew_profile_id")
    if not profile_id:
        raise Refused(
            "You don't have a crew profile",
            hint="A Director can give you one: mc users enable-crew EMAIL",
        )
    return me, profile_id


@command(app, "show", example="mc me show")
def show(ctx: typer.Context, json_output: Json = False) -> None:
    """Show your details, skills and unavailability."""
    env = start(ctx, json_output)
    api = env.api()
    me = api.get("/me")
    profile = api.get(f"/crew/{me['crew_profile_id']}") if me.get("crew_profile_id") else None
    if json_output:
        env.term.json({"user": me, "crew_profile": profile})
        return
    if profile is None:
        env.term.fields(identity(me) + [("Crew profile", "none")])
        return
    show_profile(env.term, identity(me, profile["name"]), profile, own=True)


@command(app, "update", example='mc me update --name "Ben Ito" --bio "EVA and systems"')
def update(
    ctx: typer.Context,
    name: Annotated[
        str | None, typer.Option("--name", metavar="NAME", help="Your display name")
    ] = None,
    bio: Annotated[str | None, typer.Option("--bio", metavar="TEXT", help="A short bio")] = None,
    json_output: Json = False,
) -> None:
    """Change your display name or bio."""
    if name is None and bio is None:
        raise UsageProblem("Nothing to change. Pass --name or --bio.")
    env = start(ctx, json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    body = {"display_name": name, "bio": bio}
    profile = api.patch(f"/crew/{profile_id}", {k: v for k, v in body.items() if v is not None})
    if json_output:
        env.term.json(profile)
        return
    env.term.ok("Updated your profile.")


@command(
    unavailable_app,
    "add",
    example="mc me unavailable add --start 2027-06-01 --end 2027-06-03 --reason Leave",
)
def add_unavailability(
    ctx: typer.Context,
    start_date: AwayFrom,
    end_date: AwayTo,
    reason: AwayReason,
    json_output: Json = False,
) -> None:
    """Record dates you're unavailable. Both days count."""
    env = start(ctx, json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    added = api.post(
        f"/crew/{profile_id}/unavailability",
        {"start_date": start_date, "end_date": end_date, "reason": reason},
    )
    if json_output:
        env.term.json(added)
        return
    dates = env.term.dates(added["start_date"], added["end_date"])
    env.term.ok(f"Added unavailability {added['id']}: {dates} ({added['reason']}).")


@command(unavailable_app, "list", example="mc me unavailable list")
def list_unavailability(ctx: typer.Context, json_output: Json = False) -> None:
    """List the dates you've said you're unavailable."""
    env = start(ctx, json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    entries = api.get(f"/crew/{profile_id}/unavailability")
    if json_output:
        env.term.json(entries)
        return
    _unavailability_table(env.term, entries)


@command(unavailable_app, "remove", example="mc me unavailable remove 4")
def remove_unavailability(
    ctx: typer.Context,
    unavailability_id: Annotated[
        int, typer.Argument(metavar="ID", help="From mc me unavailable list")
    ],
) -> None:
    """Remove one of your unavailability entries."""
    env = start(ctx)
    api = env.api()
    _, profile_id = _profile_id(api)
    api.delete(f"/crew/{profile_id}/unavailability/{unavailability_id}")
    env.term.ok(f"Removed unavailability {unavailability_id}.")


def _unavailability_table(term: Terminal, entries: list[dict[str, Any]]) -> None:
    if not entries:
        term.line("No unavailability recorded.")
        return
    term.table(
        ["ID", "Unavailable", "Reason"],
        [
            [str(u["id"]), term.dates(u["start_date"], u["end_date"]), u.get("reason") or ""]
            for u in entries
        ],
    )
