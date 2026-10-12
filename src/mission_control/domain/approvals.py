"""Who may approve a mission, and when enough of them have."""

from collections.abc import Iterable, Set
from dataclasses import dataclass

from mission_control.domain.errors import Problem


@dataclass(frozen=True)
class Approver:
    user_id: int
    is_director: bool
    active: bool


def conflict_problems(
    user_id: int, created_by_id: int | None, rostered_user_ids: Set[int]
) -> list[Problem]:
    """Why this person is too close to the mission to approve it: they created it or are on it."""
    problems = []
    if user_id == created_by_id:
        problems.append(Problem("approver_is_creator", "You can't approve a mission you created"))
    if user_id in rostered_user_ids:
        problems.append(Problem("approver_is_rostered", "You can't approve a mission you're on"))
    return problems


def decision_problems(
    user_id: int,
    created_by_id: int | None,
    rostered_user_ids: Set[int],
    decided_this_round: Set[int],
) -> list[Problem]:
    """Why this Director can't decide this round: they created the mission, are on it, or have
    already decided. Empty means they still can."""
    problems = conflict_problems(user_id, created_by_id, rostered_user_ids)
    if user_id in decided_this_round:
        # A rejection ends the round, so anyone who has decided an open round approved it.
        problems.append(Problem("already_decided", "You've already approved this round"))
    return problems


def count_eligible_approvers(
    people: Iterable[Approver], created_by_id: int | None, rostered_user_ids: Set[int]
) -> int:
    """Active Directors who didn't create the mission and aren't on it."""
    return sum(
        1
        for p in people
        if p.is_director
        and p.active
        and not conflict_problems(p.user_id, created_by_id, rostered_user_ids)
    )


def reaches_quorum(approvals_in_round: int, approvals_required: int) -> bool:
    """`approvals_in_round` counts approvals recorded this round, including the new one.
    `approvals_required` is the N saved at submit, not the organisation's current setting."""
    return approvals_in_round >= approvals_required
