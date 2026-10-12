from datetime import date

from pydantic import BaseModel

from mission_control.services.matching import MatchPreview, SlotSuggestion, SuggestedCrew


class MatchMissionOut(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date


class SuggestedCrewOut(BaseModel):
    crew_profile_id: int
    name: str
    workload: int  # mission-days
    proficiency: int
    pick: int

    @classmethod
    def of(cls, s: SuggestedCrew) -> "SuggestedCrewOut":
        return cls(
            crew_profile_id=s.crew_profile_id,
            name=s.name,
            workload=s.workload,
            proficiency=s.proficiency,
            pick=s.pick,
        )


class SlotSuggestionOut(BaseModel):
    slot_id: int
    name: str
    open_places: int
    unfilled: int
    suggested: list[SuggestedCrewOut]  # in pick order

    @classmethod
    def of(cls, s: SlotSuggestion) -> "SlotSuggestionOut":
        return cls(
            slot_id=s.slot_id,
            name=s.name,
            open_places=s.open_places,
            unfilled=s.unfilled,
            suggested=[SuggestedCrewOut.of(p) for p in s.suggested],
        )


class MatchPreviewOut(BaseModel):
    mission: MatchMissionOut
    can_apply: bool  # only the mission's owner may turn the suggestion into proposals
    open_places: int
    unfilled_places: int
    slots: list[SlotSuggestionOut]  # every slot, in listed order

    @classmethod
    def of(cls, p: MatchPreview) -> "MatchPreviewOut":
        return cls(
            mission=MatchMissionOut(
                id=p.mission_id,
                name=p.mission_name,
                start_date=p.window.start,
                end_date=p.window.end,
            ),
            can_apply=p.can_apply,
            open_places=p.open_places,
            unfilled_places=p.unfilled_places,
            slots=[SlotSuggestionOut.of(s) for s in p.slots],
        )
