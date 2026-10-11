from mission_control.domain.approvals import (
    Approver,
    approver_problems,
    conflict_problems,
    count_eligible_approvers,
    reaches_quorum,
)

RUTH, MARCO, INGRID, LEE = 1, 2, 3, 4  # PRD §9.1 Aurora


def director(user_id, active=True):
    return Approver(user_id=user_id, is_director=True, active=active)


DIRECTORS = [director(RUTH), director(MARCO), director(INGRID)]


# --- Who may approve (A2, A3) -------------------------------------------------------------


def test_eligible_director_has_no_problems():
    assert (
        approver_problems(
            director(MARCO), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
        )
        == []
    )


def test_ac8_creator_cannot_approve():
    [p] = approver_problems(
        director(RUTH), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
    )
    assert p.code == "approver_is_creator"


def test_ac11_rostered_director_cannot_approve():
    [p] = approver_problems(
        director(MARCO), created_by_id=RUTH, rostered_user_ids={MARCO}, decided_this_round=set()
    )
    assert p.code == "approver_is_rostered"


def test_ac9_a_lead_cannot_approve():
    lead = Approver(user_id=LEE, is_director=False, active=True)
    [p] = approver_problems(
        lead, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
    )
    assert p.code == "role_forbidden"


def test_ac10_a_director_cannot_decide_the_same_round_twice():
    [p] = approver_problems(
        director(MARCO), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round={MARCO}
    )
    assert p.code == "already_decided"


def test_every_approver_problem_is_reported_together():
    codes = {
        p.code
        for p in approver_problems(
            director(RUTH), created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
        )
    }
    assert codes == {"approver_is_creator", "approver_is_rostered", "already_decided"}


def test_conflict_problems_lists_creator_then_roster():
    problems = conflict_problems(RUTH, created_by_id=RUTH, rostered_user_ids={RUTH})
    assert [(p.code, p.message) for p in problems] == [
        ("approver_is_creator", "You can't approve a mission you created"),
        ("approver_is_rostered", "You can't approve a mission you're on"),
    ]


def test_conflict_problems_is_empty_for_an_unrelated_director():
    assert conflict_problems(MARCO, created_by_id=RUTH, rostered_user_ids={INGRID}) == []
    assert conflict_problems(MARCO, created_by_id=None, rostered_user_ids=set()) == []


def test_approver_problems_keeps_its_order_and_messages():
    problems = approver_problems(
        director(RUTH), created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
    )
    assert [p.message for p in problems] == [
        "You can't approve a mission you created",
        "You can't approve a mission you're on",
        "You've already decided this round of approval",
    ]


# --- Counting eligible approvers at submit (AC-12) ----------------------------------------


def test_ac12_s7_creator_and_rostered_director_leave_one_eligible_approver():
    # S7: Ruth created Lunar Surface Medical Study and Marco is rostered, leaving Ingrid only
    assert count_eligible_approvers(DIRECTORS, created_by_id=RUTH, rostered_user_ids={MARCO}) == 1


def test_inactive_directors_are_not_eligible_approvers():
    directors = [director(RUTH), director(MARCO, active=False), director(INGRID)]
    assert count_eligible_approvers(directors, created_by_id=99, rostered_user_ids=set()) == 2


def test_non_directors_are_never_counted():
    people = DIRECTORS + [Approver(user_id=LEE, is_director=False, active=True)]
    assert count_eligible_approvers(people, created_by_id=99, rostered_user_ids=set()) == 3


# --- Quorum (A1, AC-3) --------------------------------------------------------------------


def test_ac3_quorum_reached_only_at_the_saved_n():
    assert not reaches_quorum(approvals_in_round=1, approvals_required=2)
    assert reaches_quorum(approvals_in_round=2, approvals_required=2)


def test_ac13_single_approval_is_enough_when_n_is_one():
    assert reaches_quorum(approvals_in_round=1, approvals_required=1)


def test_a1_quorum_uses_only_the_recorded_approval_count():
    # reaches_quorum sees only the number of approvals recorded this round. Whether a Director who
    # approved earlier has since left is a service-level concern, covered in M13.
    assert reaches_quorum(approvals_in_round=2, approvals_required=2)
