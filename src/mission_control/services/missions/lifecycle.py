"""Ending a mission: completing an Active one, or cancelling one that isn't finished. Either way
its assignments follow in the same transaction: completing it completes the accepted crew, and
cancelling it cancels every proposal and acceptance."""

from mission_control.domain.enums import Action
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import mission_status_after, require_state
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission
from mission_control.services.assignments import cascade_mission_end
from mission_control.services.context import ServiceContext, mission_context, visible_mission
from mission_control.services.inputs import required_reason
from mission_control.services.missions.loading import reload
from mission_control.services.missions.views import MissionView, mission_view


def complete_mission(ctx: ServiceContext, mission_id: int) -> MissionView:
    """The owner or a Director completes an Active mission."""
    with ctx.write() as repos:
        mission = _open_to_end(ctx, repos, mission_id, Action.COMPLETE)
        return _end(ctx, repos, mission, Action.COMPLETE, Event.MISSION_COMPLETED, None)


def cancel_mission(ctx: ServiceContext, mission_id: int, reason: str | None) -> MissionView:
    """The owner or a Director cancels a mission that isn't finished, giving a reason."""
    with ctx.write() as repos:
        mission = _open_to_end(ctx, repos, mission_id, Action.CANCEL)
        given = required_reason(reason, f"Cancelling {mission.name}")
        return _end(ctx, repos, mission, Action.CANCEL, Event.MISSION_CANCELLED, given)


def _open_to_end(ctx: ServiceContext, repos: Repos, mission_id: int, action: Action) -> Mission:
    mission = visible_mission(ctx, repos, mission_id)
    ctx.authorize(action, mission_context(repos, mission))
    require_state(mission.status, action)
    return mission


def _end(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    action: Action,
    event: Event,
    reason: str | None,
) -> MissionView:
    """Move the mission to its final state, audit it, then carry its assignments along."""
    after = mission_status_after(mission.status, action)
    repos.missions.set_status(mission.id, after)
    ctx.audit(
        event,
        mission_id=mission.id,
        from_status=mission.status,
        to_status=after,
        reason=reason,
        data={"mission_name": mission.name},
    )
    cascade_mission_end(ctx, repos, mission, after)
    return mission_view(repos, reload(repos, mission))
