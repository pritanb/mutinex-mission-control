"""Running the organisation (Directors): users and roles, the skill catalogue, and how many
approvals a mission needs."""

from enum import StrEnum
from typing import Annotated

import typer

from mission_control.cli.commands.common import Email, Json, Yes, command, group, start
from mission_control.cli.prompts import ask_new_secret, confirm
from mission_control.cli.render import ROLE, plural
from mission_control.cli.resolve import skill_named, user_by_email

users_app = group("Users and roles (Directors).")
skills_app = group("The skill catalogue (Directors manage it; Leads can list it).")
org_app = group("Organisation settings (Directors).")


class RoleName(StrEnum):
    director = "director"
    lead = "lead"
    crew = "crew"


RoleArg = Annotated[RoleName, typer.Argument(metavar="ROLE", help="director, lead or crew")]
SkillName = Annotated[str, typer.Argument(metavar="NAME", help="The skill's name")]


def _a(role: str) -> str:
    label = ROLE.get(role, role)
    return f"an {label}" if label[0] in "AEIOU" else f"a {label}"


# Users


@command(users_app, "list", example="mc users list")
def list_users(ctx: typer.Context, json_output: Json = False) -> None:
    """List everyone in your organisation."""
    env = start(ctx, json_output)
    users = env.api().get("/users")
    if json_output:
        env.term.json(users)
        return
    env.term.table(
        ["ID", "Name", "Email", "Role", "Status"],
        [
            [
                str(u["id"]),
                u["name"],
                u["email"],
                ROLE.get(u["role"], u["role"]),
                "active" if u["active"] else "deactivated",
            ]
            for u in users
        ],
    )


@command(
    users_app,
    "add",
    example='mc users add --email zoe@aurora.example --name "Zoe Lin" --role crew',
)
def add_user(
    ctx: typer.Context,
    email: Annotated[
        str, typer.Option("--email", metavar="EMAIL", help="Their email; they log in with it")
    ],
    name: Annotated[str, typer.Option("--name", metavar="NAME", help="Their full name")],
    role: Annotated[
        RoleName, typer.Option("--role", metavar="ROLE", help="director, lead or crew")
    ],
    json_output: Json = False,
) -> None:
    """Add a user. You set their initial password, asked for twice with the input hidden.

    Without a terminal, pipe the password on stdin.
    """
    env = start(ctx, json_output)
    api = env.api()
    secret = ask_new_secret(
        env,
        "Initial password",
        "Repeat initial password",
        mismatch="The passwords don't match. Nothing was changed.",
    )
    user = api.post(
        "/users", {"email": email, "name": name, "role": role.value, "password": secret}
    )
    if json_output:
        env.term.json(user)
        return
    env.term.ok(f"Added {user['name']} ({user['email']}) as {_a(user['role'])}.")
    first_name = (user["name"].split() or [user["name"]])[0]
    env.term.next_steps([f"mc login --email {user['email']}    (for {first_name})"])


@command(users_app, "set-role", example="mc users set-role nora@aurora.example director")
def set_role(ctx: typer.Context, email: Email, role: RoleArg, json_output: Json = False) -> None:
    """Change someone's role."""
    env = start(ctx, json_output)
    api = env.api()
    user = user_by_email(api, email)
    updated = api.patch(f"/users/{user['id']}", {"role": role.value})
    if json_output:
        env.term.json(updated)
        return
    env.term.ok(f"{user['name']} is now {_a(role.value)}.")


@command(users_app, "deactivate", example="mc users deactivate chen@aurora.example")
def deactivate(
    ctx: typer.Context, email: Email, yes: Yes = False, json_output: Json = False
) -> None:
    """Deactivate someone. They can't log in any more, and their history stays.

    It can't be undone, so you're asked first. --yes skips the question.
    """
    env = start(ctx, json_output)
    api = env.api()
    user = user_by_email(api, email)
    confirm(
        env,
        f"Deactivating {user['name']} can't be undone: they won't be able to log in.",
        yes=yes,
        question=f"Deactivate {user['name']}?",
    )
    updated = api.patch(f"/users/{user['id']}", {"active": False})
    if json_output:
        env.term.json(updated)
        return
    env.term.ok(f"Deactivated {user['name']}. They can no longer log in.")


@command(users_app, "enable-crew", example="mc users enable-crew lee@aurora.example")
def enable_crew(ctx: typer.Context, email: Email, json_output: Json = False) -> None:
    """Give someone a crew profile, so they can be put on missions."""
    env = start(ctx, json_output)
    api = env.api()
    user = user_by_email(api, email)
    profile = api.post(f"/users/{user['id']}/crew-profile")
    if json_output:
        env.term.json(profile)
        return
    env.term.ok(f"{user['name']} now has a crew profile.")


# Skills


@command(skills_app, "list", example="mc skills list")
def list_skills(ctx: typer.Context, json_output: Json = False) -> None:
    """List the skill catalogue."""
    env = start(ctx, json_output)
    skills = env.api().get("/skills")
    if json_output:
        env.term.json(skills)
        return
    if not skills:
        env.term.line("No skills yet.")
        return
    if any(s.get("category") for s in skills):
        env.term.table(
            ["Skill", "Category"], [[s["name"], s.get("category") or ""] for s in skills]
        )
    else:
        env.term.lines(s["name"] for s in skills)


@command(skills_app, "add", example='mc skills add "Robotics"')
def add_skill(ctx: typer.Context, name: SkillName, json_output: Json = False) -> None:
    """Add a skill to the catalogue."""
    env = start(ctx, json_output)
    skill = env.api().post("/skills", {"name": name})
    if json_output:
        env.term.json(skill)
        return
    env.term.ok(f"Added skill {skill['name']}.")


@command(skills_app, "rename", example='mc skills rename Geology "Planetary Geology"')
def rename_skill(
    ctx: typer.Context,
    name: SkillName,
    new_name: Annotated[str, typer.Argument(metavar="NEW_NAME", help="What to call it")],
    json_output: Json = False,
) -> None:
    """Rename a skill. Everyone who has it keeps it."""
    env = start(ctx, json_output)
    api = env.api()
    skill = skill_named(api, name)
    renamed = api.patch(f"/skills/{skill['id']}", {"name": new_name})
    if json_output:
        env.term.json(renamed)
        return
    env.term.ok(f"Renamed {skill['name']} to {renamed['name']}.")


@command(skills_app, "remove", example="mc skills remove Robotics")
def remove_skill(ctx: typer.Context, name: SkillName) -> None:
    """Remove a skill nobody has and no slot requires."""
    env = start(ctx)
    api = env.api()
    skill = skill_named(api, name)
    api.delete(f"/skills/{skill['id']}")
    env.term.ok(f"Removed skill {skill['name']}.")


# Organisation


@command(org_app, "show", example="mc org show")
def show_org(ctx: typer.Context, json_output: Json = False) -> None:
    """Show your organisation's settings."""
    env = start(ctx, json_output)
    org = env.api().get("/org")
    if json_output:
        env.term.json(org)
        return
    env.term.fields(
        [("Organisation", org["name"]), ("Approvals required", str(org["required_approvals"]))]
    )


@command(org_app, "set-approvals", example="mc org set-approvals 2")
def set_approvals(
    ctx: typer.Context,
    count: Annotated[
        int, typer.Argument(metavar="N", help="Approvals a mission needs to go active")
    ],
    json_output: Json = False,
) -> None:
    """Set how many Directors must approve a mission."""
    env = start(ctx, json_output)
    org = env.api().patch("/org", {"required_approvals": count})
    if json_output:
        env.term.json(org)
        return
    env.term.ok(
        f"Missions now need {plural(org['required_approvals'], 'approval')}. Missions already "
        "pending keep the number they were submitted with."
    )
