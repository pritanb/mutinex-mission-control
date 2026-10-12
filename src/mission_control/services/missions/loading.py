"""Finding the records a mission use case works on, and the opening steps every edit shares."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.enums import Action, MissionStatus
from mission_control.domain.lifecycle import touch_for_change
from mission_control.domain.records import Requirement
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission, Slot
from mission_control.services.context import (
    ServiceContext,
    found,
    mission_context,
    visible_mission,
)


@dataclass(frozen=True)
class EditTarget:
    """What an edit works on, once it may go ahead. `status` is where the mission goes if the
    edit is made: Draft for a Pending mission, otherwise unchanged."""

    mission: Mission
    status: MissionStatus


@dataclass(frozen=True)
class SlotEditTarget(EditTarget):
    slot: Slot


def open_for_edit(ctx: ServiceContext, repos: Repos, mission_id: int) -> EditTarget:
    """The opening steps of every mission edit: find the mission, check the actor may edit it,
    then check its state."""
    mission = visible_mission(ctx, repos, mission_id)
    ctx.authorize(Action.EDIT_MISSION, mission_context(repos, mission))
    return EditTarget(mission, touch_for_change(mission.status))


def open_slot_for_edit(
    ctx: ServiceContext, repos: Repos, mission_id: int, slot_id: int
) -> SlotEditTarget:
    """The same, for an edit to one of the mission's slots. The slot is found before the
    permission check, like the mission: anyone who can see a mission can see its slots."""
    mission = visible_mission(ctx, repos, mission_id)
    slot = slot_of(repos, mission, slot_id)
    ctx.authorize(Action.EDIT_MISSION, mission_context(repos, mission))
    return SlotEditTarget(mission, touch_for_change(mission.status), slot)


def reload(repos: Repos, mission: Mission) -> Mission:
    return found(repos.missions.get(mission.id), "Mission")


def slot_of(repos: Repos, mission: Mission, slot_id: int) -> Slot:
    """A live slot of this mission; any other slot id is not found."""
    slot = repos.missions.get_slot(slot_id)
    if slot is None or slot.mission_id != mission.id:
        return found(None, "Slot")
    return slot


def resolve_skills(repos: Repos, levels: Mapping[int, int]) -> tuple[Requirement, ...]:
    """Requirements with their skill names. A skill outside the catalogue is not found."""
    return tuple(
        Requirement(skill_id, found(repos.skills.get(skill_id), "Skill").name, level)
        for skill_id, level in levels.items()
    )


def user_name(repos: Repos, user_id: int) -> str:
    return found(repos.users.get(user_id), "User").name
