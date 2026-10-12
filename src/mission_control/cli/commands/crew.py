"""Crew profiles: list and view them, see someone's assignment history, and set skill levels."""

from typing import Annotated, Any

import typer

from mission_control.cli.client import Api, ApiError
from mission_control.cli.commands.common import Email, Json, command, group, start
from mission_control.cli.errors import Refused
from mission_control.cli.refusals import refusals
from mission_control.cli.resolve import crew_by_email, skill_named
from mission_control.cli.views import assignment_summary_rows, show_profile, skills_text

app = group("Crew profiles, skill levels and assignment history.")

Skill = Annotated[str, typer.Argument(metavar="SKILL", help="The skill's name")]


@command(app, "list", example="mc crew list")
def list_crew(ctx: typer.Context, json_output: Json = False) -> None:
    """List the crew you can see."""
    env = start(ctx, json_output)
    crew = env.api().get("/crew")
    if json_output:
        env.term.json(crew)
        return
    if not crew:
        env.term.line("No crew to show.")
        return
    env.term.table(
        ["Name", "Email", "Skills"],
        [
            [
                c["name"] + ("" if c.get("active", True) else " (deactivated)"),
                c["email"],
                skills_text(c.get("skills") or []),
            ]
            for c in crew
        ],
    )


@command(app, "show", example="mc crew show fay@aurora.example")
def show(ctx: typer.Context, email: Email, json_output: Json = False) -> None:
    """Show someone's profile, skills and unavailable dates."""
    env = start(ctx, json_output)
    api = env.api()
    person = crew_by_email(api, email)
    profile = api.get(f"/crew/{person['crew_profile_id']}")
    if json_output:
        env.term.json(profile)
        return
    pairs = [("Name", profile["name"]), ("Email", profile["email"])]
    if not profile.get("active", True):
        pairs.append(("Status", "deactivated"))
    show_profile(env.term, pairs, profile, own=False)


@command(app, "history", example="mc crew history chen@aurora.example")
def history(ctx: typer.Context, email: Email, json_output: Json = False) -> None:
    """Show someone's assignment history, including missions they've left."""
    env = start(ctx, json_output)
    api = env.api()
    person = crew_by_email(api, email)
    rows = api.get(f"/crew/{person['crew_profile_id']}/assignments")
    if json_output:
        env.term.json(rows)
        return
    if not rows:
        env.term.line(f"{person['name']} has no assignments yet.")
        return
    env.term.table(
        ["Assignment", "Mission", "Slot", "Dates", "Status"],
        assignment_summary_rows(env.term, rows),
    )


def _skill(api: Api, name: str) -> dict[str, Any]:
    """The skill, from the catalogue. Only Leads and Directors can read the catalogue, and only
    they can change skill levels, so a refusal to read it is really a refusal to change them."""
    try:
        return skill_named(api, name)
    except ApiError as error:
        if error.code == "role_forbidden":
            raise Refused("Only Mission Leads and Directors can change skill levels") from None
        raise


@command(app, "set-skill", example="mc crew set-skill ana@aurora.example Piloting 5")
def set_skill(
    ctx: typer.Context,
    email: Email,
    skill: Skill,
    level: Annotated[int, typer.Argument(metavar="LEVEL", help="1 to 5")],
    json_output: Json = False,
) -> None:
    """Set someone's level in a skill. Leads and Directors, never for themselves."""
    env = start(ctx, json_output)
    api = env.api()
    found = _skill(api, skill)
    person = crew_by_email(api, email)
    with refusals():
        result = api.put(
            f"/crew/{person['crew_profile_id']}/skills/{found['id']}", {"level": level}
        )
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Set {person['name']}'s {found['name']} to {level}.")


@command(app, "unset-skill", example="mc crew unset-skill ana@aurora.example Leadership")
def unset_skill(ctx: typer.Context, email: Email, skill: Skill) -> None:
    """Remove a skill from someone's profile. Leads and Directors, never for themselves."""
    env = start(ctx)
    api = env.api()
    found = _skill(api, skill)
    person = crew_by_email(api, email)
    api.delete(f"/crew/{person['crew_profile_id']}/skills/{found['id']}")
    env.term.ok(f"Removed {found['name']} from {person['name']}'s skills.")
