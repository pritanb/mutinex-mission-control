"""Matching: suggest crew for a draft mission's open places, and turn a suggestion into
proposals. A preview writes nothing; applying creates Proposed assignments, which crew still have
to accept.

The owner or a Director may preview; only the owner may apply. Applying works the suggestion out
again inside its own write transaction, so it's never stale, and each proposal goes through the
same checks as one made by hand. Candidates are the
organisation's crew, minus anyone holding an open assignment on the mission and anyone who
declined, withdrew or was removed from it. The suggestion carries each person's workload and
proficiency, which are what decided the pick.
"""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Action, AssignmentStatus
from mission_control.domain.lifecycle import StateConflict, state_problem
from mission_control.domain.matching import Suggestion, proficiency, suggest_roster
from mission_control.domain.permissions import Context, can
from mission_control.domain.records import CandidateFacts, SlotSpec
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Assignment, Mission
from mission_control.services.assignments import make_proposal
from mission_control.services.context import (
    ServiceContext,
    found,
    mission_context,
    visible_mission,
)

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
        mission, about = _open(ctx, repos, mission_id, Action.PREVIEW_MATCH)
        slots, candidates, suggestion = _suggest(repos, mission)

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


def apply(ctx: ServiceContext, mission_id: int) -> list[Assignment]:
    """Propose the suggested crew for a draft mission's open places, in pick order. Only the
    owner may. Places with no candidate stay empty; with nothing to suggest, nothing changes."""
    with ctx.write() as repos:
        mission, _ = _open(ctx, repos, mission_id, Action.APPLY_MATCH)
        _, _, suggestion = _suggest(repos, mission)
        made = []
        for placement in suggestion.placements:
            # Fresh slots each time, so a proposal sees the places the previous ones took.
            slots = {s.id: s for s in repos.facts.slot_specs(mission.id)}
            profile = found(repos.crew.get(placement.crew_profile_id), "Crew member")
            made.append(
                make_proposal(ctx, repos, mission, slots, slots[placement.slot_id], profile)
            )
        return made


def _open(
    ctx: ServiceContext, repos: Repos, mission_id: int, action: Action
) -> tuple[Mission, Context]:
    """Find the mission, check the actor may preview or apply, then that it's a draft."""
    mission = visible_mission(ctx, repos, mission_id)
    about = mission_context(repos, mission)
    ctx.authorize(action, about)
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)
    return mission, about


def _suggest(
    repos: Repos, mission: Mission
) -> tuple[list[SlotSpec], list[CandidateFacts], Suggestion]:
    """The mission's slots, the candidates for it, and the matcher's suggestion from them."""
    left_out = {a.crew_profile_id for a in repos.missions.assignments(mission.id, _LEFT_OUT)}
    candidates = [
        c
        for c in repos.facts.candidates(excluding_mission_id=mission.id)
        if c.crew_profile_id not in left_out
    ]
    slots = repos.facts.slot_specs(mission.id)
    return slots, candidates, suggest_roster(slots, candidates, mission.window)
