"""A mission's history: every state change, approval, rejection and assignment response, with
who did it, when, and any reason. Anyone who can see the mission can see its history."""

from mission_control.domain.enums import Action
from mission_control.infra.repositories.models import AuditEntry
from mission_control.services.context import ServiceContext, mission_context, visible_mission


def mission_history(ctx: ServiceContext, mission_id: int) -> list[AuditEntry]:
    """The mission's events, oldest first. A mission the actor can't see is not found."""
    with ctx.read() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        ctx.authorize_view(Action.VIEW_MISSION, mission_context(repos, mission), "Mission")
        return repos.audit.for_mission(mission.id)
