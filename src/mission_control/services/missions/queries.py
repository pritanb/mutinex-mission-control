"""Viewing missions."""

from mission_control.domain.enums import Action
from mission_control.infra.repositories.models import Mission
from mission_control.services.context import ServiceContext, mission_context, visible_mission
from mission_control.services.missions.views import MissionView, mission_view


def list_missions(ctx: ServiceContext) -> list[Mission]:
    """Directors and Leads see every mission in their organisation; crew see the missions
    they're on."""
    return ctx.repos.missions.list_visible(ctx.actor)


def get_mission(ctx: ServiceContext, mission_id: int) -> MissionView:
    """A mission the actor can't see is reported as not found, exactly like a missing one."""
    with ctx.read() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        ctx.authorize_view(Action.VIEW_MISSION, mission_context(repos, mission), "Mission")
        return mission_view(repos, mission)
