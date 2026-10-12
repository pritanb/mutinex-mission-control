"""Creating a mission, renaming or moving it, and handing it to another Lead."""

from collections.abc import Sequence
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import DatesEdit
from mission_control.domain.enums import Action, MissionStatus, Role
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
from mission_control.domain.permissions import Context
from mission_control.services.context import ServiceContext, found
from mission_control.services.missions.inputs import (
    SlotInput,
    date_problems,
    invalid,
    invalid_input,
    levels,
    name_problems,
    refuse_input,
    requirement_data,
    slot_label,
    slot_problems,
)
from mission_control.services.missions.loading import (
    mission_context,
    open_for_edit,
    reload,
    resolve_skills,
    visible,
)
from mission_control.services.missions.rules import (
    join_names,
    record_change,
    refuse_if_invalidated,
    refuse_repeated_names,
    require_owner,
)
from mission_control.services.missions.views import MissionView, mission_view


def create_mission(
    ctx: ServiceContext,
    *,
    name: str,
    start: date,
    end: date,
    slots: Sequence[SlotInput],
    owner_id: int | None = None,
) -> MissionView:
    """A new Draft mission with its slots. A Lead creates missions for themselves; a Director
    names the Lead who will own it. The creator is recorded separately."""
    if owner_id is None and ctx.actor.role != Role.DIRECTOR:
        owner_id = ctx.actor.user_id
    with ctx.write() as repos:
        # The id as given: the permission rules compare it with the actor before anyone is looked
        # up. A Director who names nobody passes this check and is asked to name a Lead below.
        ctx.authorize(
            Action.CREATE_MISSION,
            Context(owner_id=ctx.actor.user_id if owner_id is None else owner_id),
        )
        owner = None if owner_id is None else found(repos.users.get(owner_id), "User")
        requirements = [resolve_skills(repos, s.requirements) for s in slots]

        problems = name_problems(name) + date_problems(start, end)
        if owner is None:
            problems.append(invalid("Name the Lead who will own the mission"))
        if not slots:
            problems.append(invalid("The mission needs at least one slot"))
        for s in slots:
            problems += slot_problems(slot_label(s.name), s.name, s.headcount, s.requirements)
        if problems or owner is None:
            raise invalid_input(problems)
        window = DateRange(start, end)
        refuse_repeated_names(slots)
        require_owner(owner)

        mission = repos.missions.create(name.strip(), window, owner.id, ctx.actor.user_id)
        for s, reqs in zip(slots, requirements, strict=True):
            repos.missions.add_slot(mission.id, s.name.strip(), s.headcount, levels(reqs))
        ctx.audit(
            Event.MISSION_CREATED,
            mission_id=mission.id,
            to_status=MissionStatus.DRAFT,
            data={
                "mission_name": mission.name,
                "owner_id": owner.id,
                "owner_name": owner.name,
                "start_date": window.start.isoformat(),
                "end_date": window.end.isoformat(),
                "slots": [
                    {
                        "slot_name": s.name.strip(),
                        "headcount": s.headcount,
                        "requirements": requirement_data(reqs),
                    }
                    for s, reqs in zip(slots, requirements, strict=True)
                ],
            },
        )
        return mission_view(repos, mission)


def update_mission(
    ctx: ServiceContext,
    mission_id: int,
    *,
    name: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> MissionView:
    """Rename or move the mission. Only its owner can. New dates are refused if they would make
    anyone on the roster no longer eligible. A Pending mission goes back to Draft if its dates
    change, but not for a new name alone."""
    with ctx.write() as repos:
        target = open_for_edit(ctx, repos, mission_id)
        mission, status = target.mission, target.status
        new_start = mission.window.start if start is None else start
        new_end = mission.window.end if end is None else end
        refuse_input(
            (name_problems(name) if name is not None else []) + date_problems(new_start, new_end)
        )
        window = DateRange(new_start, new_end)
        new_name = name.strip() if name is not None else mission.name

        changes: dict[str, list[str]] = {}
        if new_name != mission.name:
            changes["name"] = [mission.name, new_name]
        for key, old, new in (
            ("start_date", mission.window.start, window.start),
            ("end_date", mission.window.end, window.end),
        ):
            if old != new:
                changes[key] = [old.isoformat(), new.isoformat()]
        if not changes:
            return mission_view(repos, mission)

        if window == mission.window:
            status = mission.status  # a new name alone keeps the approval round going
        else:
            refuse_if_invalidated(
                repos,
                mission,
                DatesEdit(window),
                lambda names: (
                    f"Can't change the dates of {mission.name}: {join_names(names)} would no "
                    "longer be eligible. Remove them from the mission first."
                ),
                before=DatesEdit(mission.window),
            )

        repos.missions.update(mission.id, new_name, window)
        record_change(
            ctx,
            repos,
            mission,
            status,
            Event.MISSION_UPDATED,
            {"mission_name": new_name, "changes": changes},
        )
        return mission_view(repos, reload(repos, mission))


def transfer_ownership(ctx: ServiceContext, mission_id: int, new_owner_id: int) -> MissionView:
    """Directors hand a mission that isn't finished to another active Lead. A Pending mission
    goes back to Draft; an Active one stays Active, since its roster doesn't change."""
    with ctx.write() as repos:
        mission = visible(ctx, repos, mission_id)
        ctx.authorize(Action.TRANSFER, mission_context(repos, mission))
        problem = state_problem(mission.status, Action.TRANSFER)
        if problem is not None:
            raise StateConflict(problem)
        new_owner = found(repos.users.get(new_owner_id), "User")
        if new_owner.id == mission.owner_id:
            raise RuleViolation.of(
                Problem(
                    "already_owner",
                    f"{new_owner.name} already owns {mission.name}",
                    {"user_id": new_owner.id},
                )
            )
        require_owner(new_owner)
        status = mission_status_after(mission.status, Action.TRANSFER)
        old_owner = found(repos.users.get(mission.owner_id), "User")

        repos.missions.set_owner(mission.id, new_owner.id)
        record_change(
            ctx,
            repos,
            mission,
            status,
            Event.MISSION_TRANSFERRED,
            {
                "mission_name": mission.name,
                "from_owner_id": old_owner.id,
                "from_owner_name": old_owner.name,
                "to_owner_id": new_owner.id,
                "to_owner_name": new_owner.name,
            },
        )
        return mission_view(repos, reload(repos, mission))
