"""The approval round: the owner submits a Draft mission, then Directors approve or reject it.

Each use case runs in one write transaction, in this order: load (anything missing, hidden or
another organisation's is not found), authorize, check the mission's state, check input, check
the rules, then write and audit. A refusal writes nothing.

Submitting starts a new round and saves the number of approvals it needs, so later changes to
the organisation's setting don't affect it. Approvals are counted per round: a rejection, or a
change that sends the mission back to Draft, ends the round, and resubmitting starts a fresh
one. An approval already given still counts if its Director is later deactivated or demoted.
"""

from mission_control.domain.approvals import (
    Approver,
    count_eligible_approvers,
    decision_problems,
    reaches_quorum,
)
from mission_control.domain.enums import Action, MissionStatus, Role
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import (
    StateConflict,
    check_submit,
    mission_status_after,
    require_state,
    roster_problems,
)
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission
from mission_control.services.context import (
    ServiceContext,
    check,
    mission_context,
    visible_mission,
)
from mission_control.services.inputs import required_reason
from mission_control.services.missions.loading import reload
from mission_control.services.missions.views import MissionView, mission_view

_APPROVE = "approve"
_REJECT = "reject"


def submit(ctx: ServiceContext, mission_id: int) -> MissionView:
    """Send a Draft mission for approval. Refused, listing every problem at once, unless every
    place is filled, every proposal has been accepted, the accepted crew are still eligible, and
    enough Directors could approve it."""
    with ctx.write() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        about = mission_context(repos, mission)
        ctx.authorize(Action.SUBMIT, about)
        require_state(mission.status, Action.SUBMIT)

        required = repos.organisation.get().required_approvals
        approvers = [
            Approver(u.id, u.role == Role.DIRECTOR, u.is_active) for u in repos.users.list()
        ]
        eligible = count_eligible_approvers(
            approvers, mission.created_by_id, about.rostered_user_ids
        )
        problems = check_submit(
            repos.facts.slot_specs(mission.id),
            repos.facts.roster(mission.id),
            mission.window,
            eligible,
            required,
        )
        check(problems, f"{mission.name} can't be submitted")

        repos.missions.start_round(mission.id, required)
        ctx.audit(
            Event.MISSION_SUBMITTED,
            mission_id=mission.id,
            from_status=mission.status,
            to_status=MissionStatus.PENDING_APPROVAL,
            data={
                "mission_name": mission.name,
                "round": mission.approval_round + 1,
                "approvals_required": required,
            },
        )
        return _view(repos, mission)


def approve(ctx: ServiceContext, mission_id: int) -> MissionView:
    """Approve a pending mission's current round. The roster is checked again first; if anyone
    is no longer eligible the approval is refused and nothing changes. The approval that brings
    the round to the number saved at submit makes the mission Active."""
    with ctx.write() as repos:
        mission = _open_round(ctx, repos, mission_id, Action.APPROVE)
        check(
            roster_problems(repos.facts.roster(mission.id), mission.window),
            f"{mission.name} can't be approved",
        )

        repos.approvals.record(
            mission.id, mission.approval_round, ctx.actor.user_id, _APPROVE, None
        )
        approved = sum(
            1
            for a in repos.approvals.for_round(mission.id, mission.approval_round)
            if a.decision == _APPROVE
        )
        required = mission.approvals_required
        if required is None:
            raise RuntimeError("a pending mission always has its required approvals saved")
        ctx.audit(
            Event.MISSION_APPROVED,
            mission_id=mission.id,
            data={
                "mission_name": mission.name,
                "round": mission.approval_round,
                "approvals": approved,
                "required": required,
            },
        )
        after = mission_status_after(
            mission.status, Action.APPROVE, reaches_quorum=reaches_quorum(approved, required)
        )
        if after != mission.status:
            repos.missions.set_status(mission.id, after)
            ctx.audit(
                Event.MISSION_ACTIVATED,
                mission_id=mission.id,
                from_status=mission.status,
                to_status=after,
                data={"mission_name": mission.name},
            )
        return _view(repos, mission)


def reject(ctx: ServiceContext, mission_id: int, reason: str | None) -> MissionView:
    """Reject a pending mission, giving a reason. The round ends and the mission goes back to
    Draft; its accepted crew stay accepted."""
    with ctx.write() as repos:
        mission = _open_round(ctx, repos, mission_id, Action.REJECT)
        given = required_reason(reason, f"Rejecting {mission.name}")

        repos.approvals.record(
            mission.id, mission.approval_round, ctx.actor.user_id, _REJECT, given
        )
        after = mission_status_after(mission.status, Action.REJECT)
        repos.missions.set_status(mission.id, after)
        ctx.audit(
            Event.MISSION_REJECTED,
            mission_id=mission.id,
            from_status=mission.status,
            to_status=after,
            reason=given,
            data={"mission_name": mission.name, "round": mission.approval_round},
        )
        return _view(repos, mission)


def _open_round(ctx: ServiceContext, repos: Repos, mission_id: int, action: Action) -> Mission:
    """The opening steps of a decision: find the mission, check the Director may decide it
    (not its creator, not on it), check it's pending, then that they haven't decided this round
    already."""
    mission = visible_mission(ctx, repos, mission_id)
    about = mission_context(repos, mission)
    ctx.authorize(action, about)
    require_state(mission.status, action)
    decided = {a.director_id for a in repos.approvals.for_round(mission.id, mission.approval_round)}
    # Creator and roster were settled by authorize, so only "already decided" can be left.
    if problems := decision_problems(
        ctx.actor.user_id, mission.created_by_id, about.rostered_user_ids, decided
    ):
        raise StateConflict(problems[0])
    return mission


def _view(repos: Repos, mission: Mission) -> MissionView:
    return mission_view(repos, reload(repos, mission))
