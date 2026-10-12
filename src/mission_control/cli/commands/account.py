"""Signing in and out, who am I, changing my password, and what's waiting on me."""

from datetime import UTC, datetime
from typing import Annotated

import typer

from mission_control.cli.client import ApiError
from mission_control.cli.commands.common import Json, command, start
from mission_control.cli.config import Credentials
from mission_control.cli.prompts import ask, ask_new_secret, ask_secret
from mission_control.cli.refusals import refusals
from mission_control.cli.render import ROLE, Terminal, plural
from mission_control.cli.views import identity, org_name


def register(app: typer.Typer) -> None:
    command(app, "login", example="mc login --email lee@aurora.example")(login)
    command(app, "logout", example="mc logout")(logout)
    command(app, "whoami", example="mc whoami")(whoami)
    command(app, "password", example="mc password")(password)
    command(app, "inbox", example="mc inbox")(inbox)


def login(
    ctx: typer.Context,
    email: Annotated[
        str | None,
        typer.Option(
            "--email", "-e", metavar="EMAIL", help="Your email address (asked if left out)"
        ),
    ] = None,
) -> None:
    """Log in. Your password is asked for with the input hidden.

    Without a terminal, pass --email and pipe the password on stdin.
    """
    env = start(ctx)
    if email is None:
        email = ask(
            env,
            "Email",
            missing="No email given, and there's no terminal to ask on. Pass --email, and pipe "
            "the password on stdin.",
        )
    secret = ask_secret(env, "Password")
    with refusals():
        session = env.anonymous_api().post("/auth/login", {"email": email, "password": secret})
    env.store.save(Credentials(session["token"], email, session.get("expires_at")))
    me = env.api().get("/me")

    about = ROLE.get(me["role"], me["role"])
    if org := org_name(me):
        about = f"{about}, {org}"
    lasts = _session_length(session.get("expires_at"))
    env.term.ok(f"Logged in as {me['name']} ({about}).{lasts}")
    env.term.next_steps(["mc inbox"])


def logout(ctx: typer.Context) -> None:
    """Log out and end this session on the server."""
    env = start(ctx)
    if env.store.load() is None:
        env.term.ok("You're not logged in.")
        return
    try:
        env.api().post("/auth/logout")
    except ApiError as error:
        if error.status != 401:  # a session that already ended is as good as logged out
            raise
    env.store.clear()
    env.term.ok("Logged out.")


def whoami(ctx: typer.Context, json_output: Json = False) -> None:
    """Show who you're logged in as."""
    env = start(ctx, json_output)
    me = env.api().get("/me")
    if json_output:
        env.term.json(me)
        return
    env.term.fields(
        identity(me) + [("Crew profile", "yes" if me.get("crew_profile_id") else "none")]
    )


def password(ctx: typer.Context) -> None:
    """Change your password. Asks for your current one, then the new one twice.

    Every session ends afterwards, including this one, so log in again.
    """
    env = start(ctx)
    api = env.api()
    current = ask_secret(env, "Current password")
    new = ask_new_secret(
        env,
        "New password",
        "Repeat new password",
        mismatch="The new passwords don't match. Nothing was changed.",
    )
    api.post("/me/password", {"current_password": current, "new_password": new})
    env.store.clear()
    env.term.ok("Password changed. All your sessions have ended, including this one.")
    env.term.next_steps(["mc login"])


def inbox(ctx: typer.Context, json_output: Json = False) -> None:
    """Show what's waiting on you.

    Proposals to answer, missions waiting for your approval, and your missions.
    """
    env = start(ctx, json_output)
    data = env.api().get("/me/inbox")
    if json_output:
        env.term.json(data)
        return
    term = env.term
    proposals = data.get("proposals") or []
    approvals = data.get("approvals") or []
    missions = data.get("missions") or []
    if not (proposals or approvals or missions):
        term.ok("Nothing needs your attention.")
        return

    sections = 0
    if proposals:
        sections = _section(term, sections, "Proposals waiting for your answer")
        term.table(
            ["Assignment", "Mission", "Slot", "Dates"],
            [
                [
                    str(a["assignment_id"]),
                    a["mission_name"],
                    a["slot_name"],
                    term.dates(a["start_date"], a["end_date"]),
                ]
                for a in proposals
            ],
        )
    if approvals:
        sections = _section(term, sections, "Missions waiting for your approval")
        term.table(
            ["ID", "Mission", "Dates", "Approvals"],
            [
                [
                    str(m["mission_id"]),
                    m["mission_name"],
                    term.dates(m["start_date"], m["end_date"]),
                    f"{m['approvals']} of {m['required']}",
                ]
                for m in approvals
            ],
        )
    if missions:
        sections = _section(term, sections, "Your draft missions")
        term.table(
            ["ID", "Mission", "Dates", "Waiting on"],
            [
                [
                    str(m["mission_id"]),
                    m["mission_name"],
                    term.dates(m["start_date"], m["end_date"]),
                    _waiting_on(m),
                ]
                for m in missions
            ],
        )

    steps = []
    if proposals:
        first = proposals[0]["assignment_id"]
        steps += [f"mc assignments accept {first}", f"mc assignments decline {first}"]
    if approvals:
        steps.append(f"mc missions approve {approvals[0]['mission_id']}")
    ready = [m for m in missions if m["ready"]]
    unfilled = [m for m in missions if m["unfilled"]]
    if ready:
        steps.append(f"mc missions submit {ready[0]['mission_id']}")
    elif unfilled:
        steps.append(f"mc missions match {unfilled[0]['mission_id']}")
    term.next_steps(steps)


def _waiting_on(mission: dict) -> str:
    """What one of your draft missions needs before it can be submitted."""
    if mission["ready"]:
        return "Ready to submit"
    parts = [
        f"{s['slot_name']}: {plural(s['open_places'], 'place')} unfilled"
        for s in mission["unfilled"]
    ]
    if mission["unanswered"]:
        parts.append(f"{plural(mission['unanswered'], 'reply', 'replies')} awaited")
    return "; ".join(parts)


def _section(term: Terminal, shown: int, title: str) -> int:
    if shown:
        term.line()
    term.line(title)
    return shown + 1


def _session_length(expires_at: str | None) -> str:
    if not expires_at:
        return ""
    try:
        expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return ""
    hours = round((expires - datetime.now(UTC)).total_seconds() / 3600)
    return f" Session lasts {plural(hours, 'hour')}." if hours >= 1 else ""
