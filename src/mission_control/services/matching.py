"""Matching: suggest crew for a draft mission's open places. Advisory only, so a preview writes
nothing.

The owner or a Director may preview; only the owner may apply. Candidates are the
organisation's crew, minus anyone holding an open assignment on the mission and anyone who
declined, withdrew or was removed from it. The suggestion carries each person's workload and
proficiency, which are what decided the pick.
"""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Action, AssignmentStatus
from mission_control.domain.lifecycle import StateConflict, state_problem
from mission_control.domain.matching import proficiency, suggest_roster
from mission_control.domain.permissions import can
from mission_control.domain.records import CandidateFacts, SlotSpec
from mission_control.services.context import ServiceContext, mission_context, visible_mission

# Anyone holding one of these on the mission is never suggested for it again.
_LEFT_OUT = (
    AssignmentStatus.PROPOSED,
    AssignmentStatus.ACCEPTED,
    AssignmentStatus.DECLINED,
    AssignmentStatus.WITHDRAWN,
    AssignmentStatus.REMOVED,
)


@dataclass(frozen=True)
class SuggestedCrew:
    """One person suggested for one place, with the numbers that decided the pick."""

    crew_profile_id: int
    name: str
    workload: int  # mission-days of accepted assignments elsewhere; lower wins
    proficiency: int  # sum of their levels in the slot's required skills; breaks workload ties
    pick: int  # 1 for the matcher's first pick; the most constrained slot is filled first


@dataclass(frozen=True)
class SlotSuggestion:
    slot_id: int
    name: str
    open_places: int  # headcount minus open assignments; 0 means nothing to suggest
    suggested: tuple[SuggestedCrew, ...]  # in pick order
    unfilled: int  # open places left with no eligible candidate


@dataclass(frozen=True)
class MatchPreview:
    mission_id: int
    mission_name: str
    window: DateRange
    slots: tuple[SlotSuggestion, ...]  # every slot, in listed order
    can_apply: bool  # whether this actor may turn the suggestion into proposals (owner only)

    @property
    def open_places(self) -> int:
        return sum(s.open_places for s in self.slots)

    @property
    def unfilled_places(self) -> int:
        return sum(s.unfilled for s in self.slots)


def preview(ctx: ServiceContext, mission_id: int) -> MatchPreview:
    """The suggested crew for a draft mission's open places. Changes nothing."""
    with ctx.read() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        about = mission_context(repos, mission)
        ctx.authorize(Action.PREVIEW_MATCH, about)
        if problem := state_problem(mission.status, Action.PREVIEW_MATCH):
            raise StateConflict(problem)

        left_out = {a.crew_profile_id for a in repos.missions.assignments(mission.id, _LEFT_OUT)}
        candidates = [
            c
            for c in repos.facts.candidates(excluding_mission_id=mission.id)
            if c.crew_profile_id not in left_out
        ]
        slots = repos.facts.slot_specs(mission.id)

    suggestion = suggest_roster(slots, candidates, mission.window)
    by_id = {c.crew_profile_id: c for c in candidates}
    chosen: dict[int, list[SuggestedCrew]] = {s.id: [] for s in slots}
    specs = {s.id: s for s in slots}
    for pick, placement in enumerate(suggestion.placements, start=1):
        person = by_id[placement.crew_profile_id]
        chosen[placement.slot_id].append(_suggested(person, specs[placement.slot_id], pick))
    unfilled = {u.slot_id: u.count for u in suggestion.unfilled}

    return MatchPreview(
        mission_id=mission.id,
        mission_name=mission.name,
        window=mission.window,
        slots=tuple(
            SlotSuggestion(
                slot_id=s.id,
                name=s.name,
                open_places=s.open_places,
                suggested=tuple(chosen[s.id]),
                unfilled=unfilled.get(s.id, 0),
            )
            for s in slots
        ),
        can_apply=can(ctx.actor, Action.APPLY_MATCH, about),
    )


def _suggested(person: CandidateFacts, slot: SlotSpec, pick: int) -> SuggestedCrew:
    return SuggestedCrew(
        crew_profile_id=person.crew_profile_id,
        name=person.name,
        workload=person.workload,
        proficiency=proficiency(person, slot),
        pick=pick,
    )
