"""Missions: create and edit them, crew them (by hand or with the matcher), and take them
through submission, approval, completion or cancellation."""

import shlex
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from typing import Annotated, Any

import typer

from mission_control.cli.client import Api
from mission_control.cli.commands.common import (
    Json,
    MissionId,
    Yes,
    command,
    group,
    iso_date,
    start,
)
from mission_control.cli.env import Env
from mission_control.cli.errors import Refused, UsageProblem
from mission_control.cli.prompts import confirm
from mission_control.cli.refusals import refusals
from mission_control.cli.render import Span, Terminal, format_timestamp, join_names, plural
from mission_control.cli.resolve import (
    SLOT_EXAMPLE,
    crew_by_email,
    parse_requirements,
    parse_slot_spec,
    requirement_body,
    skill_ids,
    slot_in,
    user_by_email,
)
from mission_control.cli.views import (
    assignment_status,
    mission_heading,
    mission_row,
    requirements_text,
)

app = group("Create, crew and run missions.")
slot_app = group("Add, change or remove a mission's slots.")
app.add_typer(slot_app, name="slot")

SlotRef = Annotated[
    str, typer.Argument(metavar="SLOT", help="The slot's name, or its position (1 for the first)")
]
Reason = Annotated[
    str, typer.Option("--reason", metavar="TEXT", help="Why (recorded in the history)")
]
StartDate = Annotated[
    str, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="First day")
]
EndDate = Annotated[
    str, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="Last day")
]
NewName = Annotated[str | None, typer.Option("--name", metavar="NAME", help="A new name")]
NewStart = Annotated[
    str | None,
    typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="A new first day"),
]
NewEnd = Annotated[
    str | None,
    typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="A new last day"),
]
Headcount = Annotated[
    int | None, typer.Option("--headcount", metavar="N", help="How many people it needs")
]
Requires = Annotated[
    str | None,
    typer.Option("--requires", metavar="SKILL>=LEVEL,...", help="Replace its required skills"),
]
SlotSpec = Annotated[
    str,
    typer.Option(
        "--slot", metavar="SPEC", help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}"
    ),
]
SlotSpecs = Annotated[
    list[str],
    typer.Option(
        "--slot", metavar="SPEC", help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}"
    ),
]


def _refusals(mission_id: int, **hints: str) -> AbstractContextManager[None]:
    return refusals(
        f"Mission {mission_id}",
        name_state=True,
        not_found="See your missions: mc missions list",
        not_owner=f"See who owns it: mc missions show {mission_id}",
        **hints,
    )


def _invalidated_hints(mission_id: int) -> dict[str, str]:
    """Hints for an edit refused because it would invalidate crew's assignments."""
    return {
        "slot_has_open_assignments": (
            f"Remove crew first: mc missions remove-crew {mission_id} {{assignment_id}}"
        ),
        "headcount_below_open_assignments": f"See who is assigned: mc missions show {mission_id}",
        "skill_below_minimum": f"See who is assigned: mc missions show {mission_id}",
        "unavailable": f"See who is assigned: mc missions show {mission_id}",
        "overlap": f"See who is assigned: mc missions show {mission_id}",
    }


def _is_owner(me: dict[str, Any], mission: dict[str, Any]) -> bool:
    return me["id"] == mission["owner_id"]


def _is_director(me: dict[str, Any], mission: dict[str, Any]) -> bool:
    return me["role"] == "director"


def _is_owner_or_director(me: dict[str, Any], mission: dict[str, Any]) -> bool:
    return _is_owner(me, mission) or _is_director(me, mission)


Allowed = Callable[[dict[str, Any], dict[str, Any]], bool]


def _confirm(
    env: Env,
    api: Api,
    mission: dict[str, Any],
    warning: str,
    yes: bool,
    allowed: Allowed,
    question: str = "Continue?",
) -> None:
    """Ask before a change that can't easily be undone, but only someone the server will let make
    it: anyone else just sends the request and sees the server's refusal."""
    if yes or not allowed(api.get("/me"), mission):
        return
    confirm(env, warning, yes=False, question=question)


def _confirm_if_pending(
    env: Env,
    api: Api,
    mission: dict[str, Any],
    doing: str,
    yes: bool,
    allowed: Allowed = _is_owner,
) -> bool:
    """Ask before a change that sends a pending mission back to Draft. True if it was pending."""
    if mission["status"] != "pending_approval":
        return False
    warning = (
        f"{mission['name']} is pending approval. {doing} sends it back to Draft and clears its "
        "approvals."
    )
    _confirm(env, api, mission, warning, yes, allowed)
    return True


def _back(was_pending: bool) -> str:
    return " It's back in Draft." if was_pending else ""


def _done(env: Env, json_output: bool, body: Any, message: str) -> None:
    if json_output:
        env.term.json(body)
    else:
        env.term.ok(message)


def _slot_body(api: Api, specs: Sequence[str]) -> list[dict[str, Any]]:
    parsed = [parse_slot_spec(s) for s in specs]
    ids = skill_ids(api, [name for spec in parsed for name, _ in spec.requirements])
    return [
        {
            "name": s.name,
            "headcount": s.headcount,
            "requirements": requirement_body(s.requirements, ids),
        }
        for s in parsed
    ]


# Create, list, show, history


@command(
    app,
    "create",
    example=(
        'mc missions create --name "Europa Flyby" --start 2027-09-01 --end 2027-09-20 '
        f'--slot "{SLOT_EXAMPLE}"'
    ),
)
def create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", metavar="NAME", help="The mission's name")],
    start_date: StartDate,
    end_date: EndDate,
    slots: SlotSpecs,
    owner: Annotated[
        str | None,
        typer.Option(
            "--owner", metavar="EMAIL", help="The owning Lead (Directors create for a Lead)"
        ),
    ] = None,
    json_output: Json = False,
) -> None:
    """Create a draft mission with one or more slots. Repeat --slot for each."""
    for spec in slots:
        parse_slot_spec(spec)  # report a malformed spec before anything is sent
    env = start(ctx, json_output)
    api = env.api()
    body: dict[str, Any] = {
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "slots": _slot_body(api, slots),
    }
    if owner is not None:
        body["owner_id"] = user_by_email(api, owner)["id"]
    with refusals():
        mission = api.post("/missions", body)
    if json_output:
        env.term.json(mission)
        return
    env.term.ok(f"Created mission {mission['id']}: {mission_heading(env.term, mission)}")
    env.term.next_steps([f"mc missions match {mission['id']}"])


@command(app, "list", example="mc missions list")
def list_missions(ctx: typer.Context, json_output: Json = False) -> None:
    """List the missions you can see."""
    env = start(ctx, json_output)
    missions = env.api().get("/missions")
    if json_output:
        env.term.json(missions)
        return
    if not missions:
        env.term.line("No missions to show.")
        return
    with_owner = any(m.get("owner_name") for m in missions)
    headers = ["ID", "Mission", "Dates", "Status"] + (["Owner"] if with_owner else [])
    env.term.table(
        headers,
        [
            mission_row(env.term, m) + ([m.get("owner_name") or ""] if with_owner else [])
            for m in missions
        ],
    )


@command(app, "show", example="mc missions show 1")
def show(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Show a mission: its slots, crew and approvals."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        mission = env.api().get(f"/missions/{mission_id}")
    if json_output:
        env.term.json(mission)
        return
    _show_mission(env.term, mission)


def _show_mission(term: Terminal, mission: dict[str, Any]) -> None:
    term.line(mission_heading(term, mission))
    owner = f"Owner {mission.get('owner_name') or mission['owner_id']}"
    if mission.get("created_by_name") and mission.get("created_by_id") != mission.get("owner_id"):
        owner = term.heading(owner, f"created by {mission['created_by_name']}")
    term.line(owner)
    rejection = mission.get("rejection")
    if rejection:
        term.line(f"Rejected by {rejection['director_name']}: {rejection['reason']}")
    term.line()
    term.table(
        ["#", "Slot", "Requires", "Places"],
        [
            [
                str(s["position"]),
                s["name"],
                requirements_text(s["requirements"]),
                "full" if s["open_places"] <= 0 else f"{s['open_places']} of {s['headcount']} open",
            ]
            for s in mission["slots"]
        ],
    )
    term.line()
    crew = mission.get("assignments") or []
    if crew:
        term.table(
            ["Assignment", "Crew", "Slot", "Status"],
            [[str(a["id"]), a["crew_name"], a["slot_name"], assignment_status(a)] for a in crew],
        )
    else:
        term.line("No crew proposed yet.")
    required = mission.get("approvals_required")
    if mission["status"] in ("pending_approval", "active", "completed") and required:
        approvers = [
            a["director_name"] for a in mission.get("approvals") or [] if a["decision"] == "approve"
        ]
        names = f" ({join_names(approvers)})" if approvers else ""
        term.line()
        term.line(f"Approvals: {len(approvers)} of {required}{names}")


_EVENTS: dict[str, tuple[str, str]] = {
    # event: (with the names from its data, without them)
    "mission.created": ("Created the mission", "Created the mission"),
    "mission.updated": ("Edited the mission", "Edited the mission"),
    "mission.submitted": ("Submitted for approval", "Submitted for approval"),
    "mission.approved": ("Approved", "Approved"),
    "mission.rejected": ("Rejected", "Rejected"),
    "mission.activated": ("Mission became active", "Mission became active"),
    "mission.completed": ("Completed", "Completed"),
    "mission.cancelled": ("Cancelled", "Cancelled"),
    "mission.transferred": ("Handed the mission to {changes[owner_name][1]}", "Changed the owner"),
    "mission.returned_to_draft": ("Mission went back to Draft", "Mission went back to Draft"),
    "slot.added": ("Added slot {slot_name}", "Added a slot"),
    "slot.updated": ("Changed slot {slot_name}", "Changed a slot"),
    "slot.requirements_changed": ("Changed the skills for {slot_name}", "Changed a slot's skills"),
    "slot.removed": ("Removed slot {slot_name}", "Removed a slot"),
    "assignment.proposed": ("Proposed {crew_name} for {slot_name}", "Proposed crew"),
    "assignment.accepted": ("Accepted {slot_name}", "Accepted a proposal"),
    "assignment.declined": ("Declined {slot_name}", "Declined a proposal"),
    "assignment.withdrawn": ("Withdrew from {slot_name}", "Withdrew"),
    "assignment.removed": ("Removed {crew_name} from {slot_name}", "Removed crew"),
    "assignment.completed": ("{crew_name}'s assignment completed", "Assignment completed"),
    "assignment.cancelled": ("{crew_name}'s assignment cancelled", "Assignment cancelled"),
}


def _event_text(entry: dict[str, Any]) -> str:
    named, plain = _EVENTS.get(entry["event"], (entry["event"], entry["event"]))
    try:
        return named.format_map(entry.get("data") or {})
    except (KeyError, IndexError, TypeError, ValueError):
        return plain


@command(app, "history", example="mc missions history 1")
def history(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Show who changed a mission, what they did and when."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        entries = env.api().get(f"/missions/{mission_id}/history")
    if json_output:
        env.term.json(entries)
        return
    if not entries:
        env.term.line("Nothing has happened to this mission yet.")
        return
    with_reasons = any(e.get("reason") for e in entries)
    env.term.table(
        ["When (UTC)", "Who", "What"] + (["Reason"] if with_reasons else []),
        [
            [
                format_timestamp(e["created_at"]),
                e.get("actor_name") or str(e.get("actor_id")),
                _event_text(e),
            ]
            + ([e.get("reason") or ""] if with_reasons else [])
            for e in entries
        ],
    )


# Edit and slots


@command(app, "edit", example="mc missions edit 1 --end 2027-03-12")
def edit(
    ctx: typer.Context,
    mission_id: MissionId,
    name: NewName = None,
    start_date: NewStart = None,
    end_date: NewEnd = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Change a mission's name or dates. Owner only.

    A mission pending approval goes back to Draft, so you're asked first.
    """
    body = {"name": name, "start_date": start_date, "end_date": end_date}
    body = {k: v for k, v in body.items() if v is not None}
    if not body:
        raise UsageProblem("Nothing to change. Pass --name, --start or --end.")
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id, **_invalidated_hints(mission_id)):
        mission = api.get(f"/missions/{mission_id}")
        was_pending = _confirm_if_pending(env, api, mission, "Editing it", yes)
        updated = api.patch(f"/missions/{mission_id}", body)
    _done(env, json_output, updated, f"Updated {updated['name']}.{_back(was_pending)}")


@command(slot_app, "add", example='mc missions slot add 1 --slot "Geologist:1:Geology>=4"')
def add_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    spec: SlotSpec,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Add a slot to a mission. Owner only."""
    parse_slot_spec(spec)
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id):
        mission = api.get(f"/missions/{mission_id}")
        body = _slot_body(api, [spec])[0]
        was_pending = _confirm_if_pending(env, api, mission, "Adding a slot", yes)
        updated = api.post(f"/missions/{mission_id}/slots", body)
    _done(
        env, json_output, updated, f"Added {body['name']} to {mission['name']}.{_back(was_pending)}"
    )


@command(
    slot_app,
    "edit",
    example='mc missions slot edit 1 Commander --headcount 2 --requires "Piloting>=5"',
)
def edit_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    slot: SlotRef,
    name: NewName = None,
    headcount: Headcount = None,
    requires: Requires = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Rename a slot, change its headcount or replace its required skills. Owner only."""
    requirements = parse_requirements(requires) if requires is not None else None
    if name is None and headcount is None and requirements is None:
        raise UsageProblem("Nothing to change. Pass --name, --headcount or --requires.")
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id, **_invalidated_hints(mission_id)):
        mission = api.get(f"/missions/{mission_id}")
        target = slot_in(mission, slot)
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if headcount is not None:
            body["headcount"] = headcount
        if requirements is not None:
            ids = skill_ids(api, [n for n, _ in requirements])
            body["requirements"] = requirement_body(requirements, ids)
        was_pending = _confirm_if_pending(env, api, mission, "Changing a slot", yes)
        updated = api.patch(f"/missions/{mission_id}/slots/{target['id']}", body)
    _done(
        env,
        json_output,
        updated,
        f"Updated {target['name']} on {mission['name']}.{_back(was_pending)}",
    )


@command(slot_app, "remove", example='mc missions slot remove 1 "Mission Specialist"')
def remove_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    slot: SlotRef,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Remove a slot. Owner only. Refused while anyone is assigned to it."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id, **_invalidated_hints(mission_id)):
        mission = api.get(f"/missions/{mission_id}")
        target = slot_in(mission, slot)
        was_pending = _confirm_if_pending(env, api, mission, "Removing a slot", yes)
        updated = api.delete(f"/missions/{mission_id}/slots/{target['id']}")
    _done(
        env,
        json_output,
        updated,
        f"Removed {target['name']} from {mission['name']}.{_back(was_pending)}",
    )


# Crew


@command(app, "match", example="mc missions match 1")
def match(
    ctx: typer.Context,
    mission_id: MissionId,
    apply: Annotated[
        bool, typer.Option("--apply", help="Propose the suggested crew (owner only)")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print the suggestion as JSON")
    ] = False,
) -> None:
    """Suggest crew for a draft mission's open places. Nothing is changed.

    Owner or Director.
    """
    env = start(ctx, json_output)
    api = env.api()
    hints = {
        "mission_frozen": (
            f"Only draft missions can be matched. See its crew: mc missions show {mission_id}"
        ),
        "invalid_transition": (
            "Only draft missions can be matched. Its places are already filled: "
            f"mc missions show {mission_id}"
        ),
        "mission_final": (
            f"Only draft missions can be matched. See it: mc missions show {mission_id}"
        ),
    }
    with _refusals(mission_id, **hints):
        if apply:
            _apply(env, api, mission_id, json_output)
            return
        preview = api.get(f"/missions/{mission_id}/match")
    if json_output:
        env.term.json(preview)
        return
    _show_preview(env.term, mission_id, preview)


def _show_preview(term: Terminal, mission_id: int, preview: dict[str, Any]) -> None:
    mission = preview["mission"]
    term.line(
        term.heading(
            mission["name"], term.dates(mission["start_date"], mission["end_date"]), "Draft"
        )
    )
    slots = [s for s in preview["slots"] if s["open_places"] > 0]
    open_places = preview["open_places"]
    unfilled = [s for s in slots if s["unfilled"] > 0]
    suggested = sorted(
        ((p, s) for s in slots for p in s["suggested"]), key=lambda pair: pair[0]["pick"]
    )
    if open_places == 0:
        term.ok("Every place already has someone proposed or accepted. Nothing to suggest.")
        return
    if not unfilled:
        places = "the 1 open place" if open_places == 1 else f"all {open_places} open places"
        term.ok(f"Crew suggested for {places}. Nothing has been proposed yet.")
    else:
        names = join_names([s["name"] for s in unfilled])
        verb = "has" if len(unfilled) == 1 else "have"
        filled = open_places - preview["unfilled_places"]
        term.note(
            f"Crew suggested for {filled} of {plural(open_places, 'open place')}. "
            f"{names} {verb} no eligible crew left."
        )
    term.line()
    rows: list[list[str] | Span] = []
    for slot in slots:
        for person in slot["suggested"]:
            rows.append(
                [
                    slot["name"],
                    person["name"],
                    plural(person["workload"], "day"),
                    str(person["proficiency"]),
                    str(person["pick"]),
                ]
            )
        if slot["unfilled"]:
            rows.append(Span(slot["name"], f"unfilled ({plural(slot['unfilled'], 'place')})"))
    term.table(["Slot", "Suggested", "Workload", "Proficiency", "Pick"], rows)
    term.line()
    if unfilled:
        term.line("  The mission can't be submitted until every place is filled.")
    else:
        term.line(
            "  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload"
        )
        term.line("  wins, then highest proficiency (sum of the required skill levels).")

    if not preview.get("can_apply"):
        return
    steps = []
    if suggested:
        if len(suggested) == 1:
            person, slot = suggested[0]
            who = f"{person['name']} for {slot['name']}"
        else:
            who = join_names([p["name"] for p, _ in suggested])
        steps.append(f"mc missions match {mission_id} --apply    proposes {who}")
    for slot in unfilled:
        steps.append(
            f"mc missions propose {mission_id} --slot {shlex.quote(slot['name'])} --crew EMAIL    "
            f"fill {slot['name']} by hand"
        )
    term.next_steps(steps)


def _apply(env: Env, api: Api, mission_id: int, json_output: bool) -> None:
    proposed = api.post(f"/missions/{mission_id}/match/apply")
    if json_output:
        env.term.json(proposed)
        return
    if not proposed:
        env.term.note("No crew could be proposed: no eligible crew for the open places.")
        return
    mission = api.get(f"/missions/{mission_id}")
    by_id = {a["id"]: a for a in mission.get("assignments") or []}
    env.term.ok(
        f"Proposed {len(proposed)} crew for {mission['name']}. "
        f"{'They need' if len(proposed) == 1 else 'Each of them needs'} to accept."
    )
    env.term.line()
    rows = []
    for item in proposed:
        known = by_id.get(item["id"], {})
        rows.append([str(item["id"]), known.get("crew_name", ""), known.get("slot_name", "")])
    env.term.table(["Assignment", "Crew", "Slot"], rows)
    env.term.next_steps([f"mc missions show {mission_id}"])


@command(
    app,
    "propose",
    example='mc missions propose 1 --slot "Flight Engineer" --crew chen@aurora.example',
)
def propose(
    ctx: typer.Context,
    mission_id: MissionId,
    slot: Annotated[
        str, typer.Option("--slot", metavar="SLOT", help="The slot's name or position")
    ],
    crew: Annotated[str, typer.Option("--crew", metavar="EMAIL", help="The crew member's email")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Propose a crew member for a slot. Owner only. They still need to accept."""
    env = start(ctx, json_output)
    api = env.api()
    free = f"See who is free: mc missions match {mission_id}"
    hints = {
        "overlap": free,
        "unavailable": free,
        "skill_below_minimum": free,
        "inactive": free,
        "slot_full": f"See the open places: mc missions show {mission_id}",
    }
    with _refusals(mission_id, **hints):
        mission = api.get(f"/missions/{mission_id}")
        target = slot_in(mission, slot)
        person = crew_by_email(api, crew)
        was_pending = _confirm_if_pending(env, api, mission, "Proposing crew", yes)
        assignment = api.post(
            f"/missions/{mission_id}/assignments",
            {"slot_id": target["id"], "crew_profile_id": person["crew_profile_id"]},
        )
    _done(
        env,
        json_output,
        assignment,
        f"Proposed {person['name']} for {target['name']} on {mission['name']} "
        f"(assignment {assignment['id']}). They need to accept.{_back(was_pending)}",
    )


@command(app, "remove-crew", example="mc missions remove-crew 1 21")
def remove_crew(
    ctx: typer.Context,
    mission_id: MissionId,
    assignment_id: Annotated[
        int, typer.Argument(metavar="ASSIGNMENT_ID", help="From mc missions show")
    ],
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Remove someone from a mission, or take back a proposal. Owner only."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id):
        mission = api.get(f"/missions/{mission_id}")
        held = next((a for a in mission.get("assignments") or [] if a["id"] == assignment_id), None)
        if held is None:
            raise Refused(
                f"Assignment {assignment_id} isn't on {mission['name']}",
                hint=f"See its crew: mc missions show {mission_id}",
            )
        was_pending = _confirm_if_pending(env, api, mission, "Removing crew", yes)
        result = api.post(f"/assignments/{assignment_id}/remove")
    _done(
        env,
        json_output,
        result,
        f"Removed {held['crew_name']} from {held['slot_name']} on {mission['name']}."
        f"{_back(was_pending)}",
    )


# Lifecycle


@command(app, "submit", example="mc missions submit 1")
def submit(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Submit a fully crewed draft for approval. Owner only."""
    env = start(ctx, json_output)
    hints = {
        "slot_unfilled": f"Fill the open places: mc missions match {mission_id}",
        "proposal_unanswered": f"See who hasn't answered: mc missions show {mission_id}",
    }
    with _refusals(mission_id, **hints):
        mission = env.api().post(f"/missions/{mission_id}/submit")
    needs = mission.get("approvals_required")
    after = f" It needs {plural(needs, 'approval')}." if needs else ""
    _done(env, json_output, mission, f"Submitted {mission['name']} for approval.{after}")


@command(app, "approve", example="mc missions approve 1")
def approve(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Approve a mission pending approval. Directors who didn't create it and aren't on it."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        mission = env.api().post(f"/missions/{mission_id}/approve")
    if mission["status"] == "active":
        state = "It's now active."
    else:
        given = sum(1 for a in mission.get("approvals") or [] if a["decision"] == "approve")
        needed = plural(mission["approvals_required"], "approval")
        state = f"It's pending approval ({given} of {needed})."
    _done(env, json_output, mission, f"Approved {mission['name']}. {state}")


@command(app, "reject", example='mc missions reject 6 --reason "Roster too thin"')
def reject(
    ctx: typer.Context, mission_id: MissionId, reason: Reason, json_output: Json = False
) -> None:
    """Reject a mission pending approval. It goes back to Draft. Directors only."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        mission = env.api().post(f"/missions/{mission_id}/reject", {"reason": reason})
    _done(env, json_output, mission, f"Rejected {mission['name']}. It's back in Draft.")


@command(app, "transfer", example="mc missions transfer 1 --owner nora@aurora.example")
def transfer(
    ctx: typer.Context,
    mission_id: MissionId,
    owner: Annotated[str, typer.Option("--owner", metavar="EMAIL", help="The new owning Lead")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Hand a mission to another Lead. Directors only."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id):
        new_owner = user_by_email(api, owner)
        mission = api.get(f"/missions/{mission_id}")
        was_pending = _confirm_if_pending(
            env, api, mission, "Changing the owner", yes, _is_director
        )
        updated = api.post(f"/missions/{mission_id}/owner", {"owner_id": new_owner["id"]})
    _done(
        env,
        json_output,
        updated,
        f"{updated['name']} now belongs to {new_owner['name']}.{_back(was_pending)}",
    )


@command(app, "complete", example="mc missions complete 5")
def complete(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Mark an active mission completed. Owner or Director."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        mission = env.api().post(f"/missions/{mission_id}/complete")
    _done(
        env,
        json_output,
        mission,
        f"Completed {mission['name']}. Its accepted assignments are completed too.",
    )


@command(app, "cancel", example='mc missions cancel 1 --reason "Budget cut"')
def cancel(
    ctx: typer.Context,
    mission_id: MissionId,
    reason: Reason,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Cancel a mission that isn't finished. Owner or Director. Asks first."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id):
        mission = api.get(f"/missions/{mission_id}")
        _confirm(
            env,
            api,
            mission,
            f"Cancelling {mission['name']} can't be undone. Its open assignments will be "
            "cancelled too.",
            yes,
            _is_owner_or_director,
            question=f"Cancel {mission['name']}?",
        )
        cancelled = api.post(f"/missions/{mission_id}/cancel", {"reason": reason})
    # A mission is cancelled once, so every cancelled assignment was cancelled just now.
    ended = sum(1 for a in cancelled.get("assignments") or [] if a["status"] == "cancelled")
    also = f" and its {plural(ended, 'open assignment')}" if ended else ""
    _done(env, json_output, cancelled, f"Cancelled {cancelled['name']}{also}.")
