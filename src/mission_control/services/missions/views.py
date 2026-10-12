"""How a mission is shown to its viewers."""

from dataclasses import dataclass

from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.records import Requirement
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Approval, Mission
from mission_control.services.missions.loading import user_name

# States reached through the current approval round, so its approvals are the live ones. A Draft
# mission's round was rejected or voided by a change, so its approvals no longer count.
_ROUND_IS_LIVE = frozenset(
    {MissionStatus.PENDING_APPROVAL, MissionStatus.ACTIVE, MissionStatus.COMPLETED}
)


@dataclass(frozen=True)
class SlotView:
    id: int
    position: int
    name: str
    headcount: int
    open_places: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class AssignmentView:
    id: int
    slot_id: int
    slot_name: str
    crew_profile_id: int
    crew_name: str
    status: AssignmentStatus
    reason: str | None


@dataclass(frozen=True)
class ApprovalView:
    director_id: int
    director_name: str
    decision: str
    reason: str | None


@dataclass(frozen=True)
class MissionListItem:
    """A mission as it appears in a list: the mission and its owner's name."""

    mission: Mission
    owner_name: str


@dataclass(frozen=True)
class MissionView:
    """A mission as its viewers see it: live slots in listed order, every assignment it has had,
    the approvals of its current round (none while it's in Draft or cancelled), and, while a
    rejected mission is back in Draft, who rejected it and why."""

    mission: Mission
    owner_name: str
    created_by_name: str
    slots: tuple[SlotView, ...]
    assignments: tuple[AssignmentView, ...]
    approvals: tuple[ApprovalView, ...]
    rejection: ApprovalView | None = None


def mission_view(repos: Repos, mission: Mission) -> MissionView:
    assignments = repos.missions.assignments(mission.id)
    crew_names = repos.missions.assignee_names(mission.id)
    slot_names = repos.missions.slot_names(mission.id)
    decisions = (
        repos.approvals.for_round(mission.id, mission.approval_round)
        if mission.approval_round
        else []
    )
    approvals = decisions if mission.status in _ROUND_IS_LIVE else []
    # A rejection ends its round and sends the mission to Draft; resubmitting starts a new round.
    rejected = (
        next((d for d in decisions if d.decision == "reject"), None)
        if mission.status == MissionStatus.DRAFT
        else None
    )
    open_places = {s.id: s.open_places for s in repos.facts.slot_specs(mission.id)}

    return MissionView(
        mission=mission,
        owner_name=user_name(repos, mission.owner_id),
        created_by_name=user_name(repos, mission.created_by_id),
        slots=tuple(
            SlotView(
                s.id,
                s.position,
                s.name,
                s.headcount,
                open_places[s.id],
                s.requirements,
            )
            for s in repos.missions.slots(mission.id)
        ),
        assignments=tuple(
            AssignmentView(
                a.id,
                a.slot_id,
                slot_names[a.slot_id],
                a.crew_profile_id,
                crew_names[a.crew_profile_id],
                a.status,
                a.reason,
            )
            for a in assignments
        ),
        approvals=tuple(_approval(repos, a) for a in approvals),
        rejection=_approval(repos, rejected) if rejected else None,
    )


def _approval(repos: Repos, a: Approval) -> ApprovalView:
    return ApprovalView(a.director_id, user_name(repos, a.director_id), a.decision, a.reason)
