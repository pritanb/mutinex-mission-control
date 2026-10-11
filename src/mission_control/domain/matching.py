"""Suggest crew for a mission's open places. Advisory only: nothing is written.

1. Filter: find the eligible candidates for each slot.
2. Pick the open slot with the fewest candidates (ties: position, then id).
3. Pick the person with the lowest workload, then highest proficiency, then lowest id.
4. Place them and remove them from every other slot's candidates.
5. Repeat, recounting each time. Places with no candidates left are reported as unfilled.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import is_eligible
from mission_control.domain.records import CandidateFacts, SlotSpec


@dataclass(frozen=True)
class Placement:
    """One suggested person for one place in a slot."""

    slot_id: int
    crew_profile_id: int


@dataclass(frozen=True)
class Unfilled:
    """Places in a slot that no eligible candidate was left to fill."""

    slot_id: int
    count: int


@dataclass(frozen=True)
class Suggestion:
    placements: tuple[Placement, ...]  # in the order they were picked
    unfilled: tuple[Unfilled, ...]  # in the order the gaps were found


def suggest_roster(
    slots: Sequence[SlotSpec], candidates: Sequence[CandidateFacts], window: DateRange
) -> Suggestion:
    by_id = {c.crew_profile_id: c for c in candidates}

    # Step 1: who could fill each slot. Computed once, then shrunk as people are placed.
    # Eligibility doesn't change during a run, only who is still free.
    eligible: dict[int, set[int]] = {
        s.id: {c.crew_profile_id for c in candidates if is_eligible(c, s, window)} for s in slots
    }
    # Places still to fill per slot. Slots that are already full start at 0 and are never picked.
    remaining: dict[int, int] = {s.id: s.open_places for s in slots}

    placements: list[Placement] = []
    unfilled: list[Unfilled] = []

    while open_slots := [s for s in slots if remaining[s.id] > 0]:
        # Step 2: most constrained slot first. Recounted on every pass, because each placement
        # can shrink other slots' candidate lists.
        slot = min(open_slots, key=lambda s: (len(eligible[s.id]), s.position, s.id))

        if not eligible[slot.id]:
            # Nobody left who can fill this slot: report every remaining place as a gap and stop
            # considering the slot.
            unfilled.append(Unfilled(slot.id, remaining[slot.id]))
            remaining[slot.id] = 0
            continue

        # Step 3: best person for this slot. Negating proficiency makes "higher is better" work
        # with min(); the id at the end makes the ordering total.
        person = min(
            (by_id[i] for i in eligible[slot.id]),
            key=lambda c: (c.workload, -proficiency(c, slot), c.crew_profile_id),
        )

        # Step 4: place them, and make sure they can't be picked for any other slot or place.
        placements.append(Placement(slot.id, person.crew_profile_id))
        remaining[slot.id] -= 1
        for ids in eligible.values():
            ids.discard(person.crew_profile_id)

    return Suggestion(tuple(placements), tuple(unfilled))


def proficiency(person: CandidateFacts, slot: SlotSpec) -> int:
    """Sum of the person's levels in the slot's required skills. Other skills don't count."""
    return sum(person.skills.get(r.skill_id, 0) for r in slot.requirements)
