"""Who may approve a mission, and when enough of them have."""

from collections.abc import Iterable, Set
from dataclasses import dataclass

from mission_control.domain.errors import Problem


@dataclass(frozen=True)
class Approver:
    user_id: int
    is_director: bool
    active: bool


def approver_problems(
    approver: Approver,
    created_by_id: int,
    rostered_user_ids: Set[int],
    decided_this_round: Set[int],
) -> list[Problem]:
    """Every reason `approver` can't approve or reject this round. Empty means they can."""
    if not approver.is_director:
        return [Problem("role_forbidden", "Only Directors can approve or reject missions")]
    problems = []
    if approver.user_id == created_by_id:
        problems.append(Problem("approver_is_creator", "You can't approve a mission you created"))
    if approver.user_id in rostered_user_ids:
        problems.append(Problem("approver_is_rostered", "You can't approve a mission you're on"))
    if approver.user_id in decided_this_round:
        problems.append(Problem("already_decided", "You've already decided this round of approval"))
    return problems


def count_eligible_approvers(
    people: Iterable[Approver], created_by_id: int, rostered_user_ids: Set[int]
) -> int:
    """Active Directors who didn't create the mission and aren't on it."""
    return sum(
        1
        for p in people
        if p.is_director
        and p.active
        and p.user_id != created_by_id
        and p.user_id not in rostered_user_ids
    )


def reaches_quorum(approvals_in_round: int, approvals_required: int) -> bool:
    """`approvals_in_round` counts approvals recorded this round, including the new one.
    `approvals_required` is the N saved at submit, not the organisation's current setting."""
    return approvals_in_round >= approvals_required
