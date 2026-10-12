"""The inbox: what is waiting on the caller to act, worked out from current data on each request.

Nothing is stored or marked as read; an item disappears once it's dealt with. Everyone has one
inbox, showing whichever sections apply to them:
- proposals waiting for their reply (anyone with a crew profile);
- pending missions they could still approve (Directors who didn't create the mission, aren't
  on it, and haven't approved this round);
- their own Draft missions, with the places still to fill and the proposals awaiting replies.

The missions section counts places and replies only. Whether the crew are still eligible, and
whether enough Directors could approve, is checked when the mission is submitted.
"""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import AssignmentSummary
from mission_control.services.context import ServiceContext


@dataclass(frozen=True)
class ApprovalItem:
    """A pending mission waiting on this Director's decision."""

    mission_id: int
    mission_name: str
    window: DateRange
    approvals: int  # given so far this round
    required: int  # saved when the mission was submitted


@dataclass(frozen=True)
class UnfilledSlot:
    slot_id: int
    slot_name: str
    open_places: int


@dataclass(frozen=True)
class MissionItem:
    """One of the caller's Draft missions, with what it's waiting on."""

    mission_id: int
    mission_name: str
    window: DateRange
    unfilled: tuple[UnfilledSlot, ...]  # slots with open places, in listed order
    unanswered: int  # proposals the crew haven't replied to yet

    @property
    def ready(self) -> bool:
        """Every place is filled and every proposal accepted, so the owner can submit."""
        return not self.unfilled and self.unanswered == 0


@dataclass(frozen=True)
class Inbox:
    proposals: tuple[AssignmentSummary, ...]  # soonest mission first
    approvals: tuple[ApprovalItem, ...]  # soonest mission first
    missions: tuple[MissionItem, ...]  # soonest mission first


def inbox(ctx: ServiceContext) -> Inbox:
    """Everything waiting on the caller, read in one consistent snapshot."""
    with ctx.read() as repos:
        return Inbox(
            proposals=_proposals(ctx, repos),
            approvals=_approvals(ctx, repos),
            missions=_missions(ctx, repos),
        )


def _proposals(ctx: ServiceContext, repos: Repos) -> tuple[AssignmentSummary, ...]:
    if ctx.actor.crew_profile_id is None:
        return ()
    waiting = [
        a
        for a in repos.crew.history(ctx.actor.crew_profile_id)
        if a.status == AssignmentStatus.PROPOSED
    ]
    return tuple(sorted(waiting, key=lambda a: (a.window.start, a.assignment_id)))


def _approvals(ctx: ServiceContext, repos: Repos) -> tuple[ApprovalItem, ...]:
    if ctx.actor.role != Role.DIRECTOR:
        return ()
    me = ctx.actor.user_id
    items = []
    for m in repos.missions.with_status(MissionStatus.PENDING_APPROVAL):
        if me == m.created_by_id or me in repos.missions.rostered_user_ids(m.id):
            continue
        decisions = repos.approvals.for_round(m.id, m.approval_round)
        if any(d.director_id == me for d in decisions):
            continue
        approved = sum(1 for d in decisions if d.decision == "approve")
        items.append(ApprovalItem(m.id, m.name, m.window, approved, m.approvals_required or 0))
    return tuple(items)


def _missions(ctx: ServiceContext, repos: Repos) -> tuple[MissionItem, ...]:
    items = []
    for m in repos.missions.non_final_owned_by(ctx.actor.user_id):
        if m.status != MissionStatus.DRAFT:
            continue
        unfilled = tuple(
            UnfilledSlot(s.id, s.name, s.open_places)
            for s in repos.facts.slot_specs(m.id)
            if s.open_places > 0
        )
        unanswered = len(repos.missions.assignments(m.id, (AssignmentStatus.PROPOSED,)))
        items.append(MissionItem(m.id, m.name, m.window, unfilled, unanswered))
    return tuple(items)
