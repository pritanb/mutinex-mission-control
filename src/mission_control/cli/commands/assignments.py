"""Your assignments: list them, and accept, decline or withdraw."""

from contextlib import AbstractContextManager
from typing import Annotated, Any

import typer

from mission_control.cli.client import Api
from mission_control.cli.commands.common import Json, Yes, command, group, start
from mission_control.cli.prompts import confirm
from mission_control.cli.refusals import refusals
from mission_control.cli.views import assignment_summary_rows

app = group("Your assignments: accept, decline or withdraw.")

AssignmentId = Annotated[
    int, typer.Argument(metavar="ASSIGNMENT_ID", help="From mc assignments list or mc inbox")
]


def _refusals(assignment_id: int) -> AbstractContextManager[None]:
    return refusals(
        f"Assignment {assignment_id}", not_found="See your assignments: mc assignments list"
    )


def _mine(api: Api, assignment_id: int) -> dict[str, Any] | None:
    """Your summary of the assignment (mission, slot, mission status), if it's yours."""
    for row in api.get("/assignments"):
        if row["assignment_id"] == assignment_id:
            return row
    return None


def _what(summary: dict[str, Any] | None, assignment_id: int) -> str:
    if summary is None:
        return f"assignment {assignment_id}"
    return f"{summary['slot_name']} on {summary['mission_name']}"


@command(app, "list", example="mc assignments list --pending")
def list_assignments(
    ctx: typer.Context,
    pending: Annotated[
        bool, typer.Option("--pending", help="Only proposals waiting for your answer")
    ] = False,
    json_output: Json = False,
) -> None:
    """List your assignments."""
    env = start(ctx, json_output)
    rows = env.api().get("/assignments", {"pending": "true"} if pending else None)
    if json_output:
        env.term.json(rows)
        return
    if not rows:
        env.term.line(
            "No proposals are waiting for you." if pending else "You have no assignments."
        )
        return
    env.term.table(
        ["ID", "Mission", "Slot", "Dates", "Status"], assignment_summary_rows(env.term, rows)
    )


@command(app, "accept", example="mc assignments accept 21")
def accept(ctx: typer.Context, assignment_id: AssignmentId, json_output: Json = False) -> None:
    """Accept a proposal. Only while the mission is a draft."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        result = api.post(f"/assignments/{assignment_id}/accept")
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Accepted {_what(summary, assignment_id)}.")


@command(app, "decline", example='mc assignments decline 21 --reason "On leave"')
def decline(
    ctx: typer.Context,
    assignment_id: AssignmentId,
    reason: Annotated[
        str | None, typer.Option("--reason", metavar="TEXT", help="Why (optional)")
    ] = None,
    json_output: Json = False,
) -> None:
    """Decline a proposal."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        body = {"reason": reason} if reason is not None else None
        result = api.post(f"/assignments/{assignment_id}/decline", body)
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Declined {_what(summary, assignment_id)}.")


@command(app, "withdraw", example='mc assignments withdraw 31 --reason "Family matter"')
def withdraw(
    ctx: typer.Context,
    assignment_id: AssignmentId,
    reason: Annotated[str, typer.Option("--reason", metavar="TEXT", help="Why you're withdrawing")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Withdraw from an accepted assignment. A mission pending approval goes back to Draft."""
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        pending = summary is not None and summary["mission_status"] == "pending_approval"
        if pending:
            confirm(
                env,
                f"{summary['mission_name']} is pending approval. Withdrawing sends it back to "
                "Draft and clears its approvals.",
                yes=yes,
            )
        result = api.post(f"/assignments/{assignment_id}/withdraw", {"reason": reason})
    if json_output:
        env.term.json(result)
        return
    back = " It's back in Draft." if pending else ""
    env.term.ok(f"Withdrew from {_what(summary, assignment_id)}.{back}")
