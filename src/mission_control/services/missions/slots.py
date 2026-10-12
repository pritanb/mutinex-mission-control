"""Changing a mission's slots: adding one, renaming it or changing its headcount, replacing its
required skills, and removing it. Only the mission's owner can."""

from collections.abc import Mapping

from mission_control.domain.eligibility import SlotEdit, SlotRemoval
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.services.context import ServiceContext
from mission_control.services.missions.inputs import (
    SlotInput,
    levels,
    refuse_input,
    requirement_data,
    slot_label,
    slot_problems,
)
from mission_control.services.missions.loading import (
    open_for_edit,
    open_slot_for_edit,
    reload,
    resolve_skills,
)
from mission_control.services.missions.rules import (
    is_are,
    join_names,
    record_change,
    refuse_if_invalidated,
    refuse_taken_name,
)
from mission_control.services.missions.views import MissionView, mission_view


def add_slot(ctx: ServiceContext, mission_id: int, slot: SlotInput) -> MissionView:
    """A new slot after the mission's last one."""
    with ctx.write() as repos:
        target = open_for_edit(ctx, repos, mission_id)
        mission = target.mission
        requirements = resolve_skills(repos, slot.requirements)
        refuse_input(
            slot_problems(slot_label(slot.name), slot.name, slot.headcount, slot.requirements)
        )
        refuse_taken_name(mission, repos.missions.slots(mission.id), slot.name)

        added = repos.missions.add_slot(
            mission.id, slot.name.strip(), slot.headcount, levels(requirements)
        )
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_ADDED,
            {
                "mission_name": mission.name,
                "slot_id": added.id,
                "slot_name": added.name,
                "headcount": added.headcount,
                "requirements": requirement_data(requirements),
            },
        )
        return mission_view(repos, reload(repos, mission))


def update_slot(
    ctx: ServiceContext,
    mission_id: int,
    slot_id: int,
    *,
    name: str | None = None,
    headcount: int | None = None,
) -> MissionView:
    """Rename a slot or change its headcount. A headcount below the crew already assigned to the
    slot is refused, naming them."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        label = name.strip() if name is not None and name.strip() else slot.name
        refuse_input(slot_problems(label, name, headcount, None, {"slot_id": slot.id}))
        new_name = name.strip() if name is not None else slot.name
        new_headcount = headcount if headcount is not None else slot.headcount

        changes: dict[str, list[object]] = {}
        if new_name != slot.name:
            changes["name"] = [slot.name, new_name]
        if new_headcount != slot.headcount:
            changes["headcount"] = [slot.headcount, new_headcount]
        if not changes:
            return mission_view(repos, mission)
        refuse_taken_name(mission, repos.missions.slots(mission.id), new_name, slot.id)
        refuse_if_invalidated(
            repos,
            mission,
            SlotEdit(slot.id, headcount=new_headcount),
            lambda names: (
                f"Can't lower the headcount of {slot.name} on {mission.name}: "
                f"{join_names(names)} {is_are(names)} assigned. Remove crew from the slot first."
            ),
        )

        repos.missions.update_slot(slot.id, new_name, new_headcount)
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_UPDATED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,
                "slot_name": new_name,
                "changes": changes,
            },
        )
        return mission_view(repos, reload(repos, mission))


def replace_requirements(
    ctx: ServiceContext, mission_id: int, slot_id: int, requirements: Mapping[int, int]
) -> MissionView:
    """Replace every required skill of a slot ({skill id: minimum level}). Refused if anyone
    assigned to the slot would no longer meet them; a shortfall they already had doesn't count."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        new = resolve_skills(repos, requirements)
        refuse_input(slot_problems(slot.name, None, None, requirements, {"slot_id": slot.id}))

        if levels(new) == levels(slot.requirements):
            return mission_view(repos, mission)
        refuse_if_invalidated(
            repos,
            mission,
            SlotEdit(slot.id, requirements=new),
            lambda names: (
                f"Can't change the requirements of {slot.name} on {mission.name}: "
                f"{join_names(names)} would no longer be eligible. Remove them from the "
                "mission first."
            ),
            before=SlotEdit(slot.id, requirements=slot.requirements),
        )

        repos.missions.replace_requirements(slot.id, levels(new))
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_REQUIREMENTS_CHANGED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,
                "slot_name": slot.name,
                "requirements": requirement_data(new),
                "previous_requirements": requirement_data(slot.requirements),
            },
        )
        return mission_view(repos, reload(repos, mission))


def remove_slot(ctx: ServiceContext, mission_id: int, slot_id: int) -> MissionView:
    """Remove a slot. Its past assignments keep their history. Refused while anyone is assigned
    to it, or if it's the mission's only slot."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        if len(repos.missions.slots(mission.id)) == 1:
            raise RuleViolation.of(
                Problem(
                    "mission_needs_a_slot",
                    f"Can't remove {slot.name}: {mission.name} needs at least one slot",
                    {"slot_id": slot.id},
                )
            )
        refuse_if_invalidated(
            repos,
            mission,
            SlotRemoval(slot.id),
            lambda names: (
                f"Can't remove {slot.name} from {mission.name} while {join_names(names)} "
                f"{is_are(names)} assigned to it. Remove them from the mission first."
            ),
        )

        repos.missions.remove_slot(slot.id)
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_REMOVED,
            {"mission_name": mission.name, "slot_id": slot.id, "slot_name": slot.name},
        )
        return mission_view(repos, reload(repos, mission))
