import pytest

from mission_control.domain.enums import MissionStatus
from mission_control.domain.errors import NotFound, Problem, RuleViolation
from mission_control.domain.lifecycle import StateConflict, touch_for_change


def test_rule_violation_carries_every_problem():
    problems = [
        Problem("slot_unfilled", "Commander: 1 place unfilled"),
        Problem("proposal_unanswered", "Specialist: Dana hasn't responded"),
    ]
    err = RuleViolation("Mission can't be submitted", problems)
    assert err.code == "rule_violation"
    assert err.message == "Mission can't be submitted"
    assert err.problems == tuple(problems)


def test_rule_violation_needs_at_least_one_problem():
    with pytest.raises(ValueError):
        RuleViolation("Nothing wrong", [])


def test_a_single_problem_becomes_a_rule_violation_with_its_own_code():
    p = Problem("overlap", "Gus has an accepted assignment on Station Reboost")
    err = RuleViolation.of(p)
    assert (err.code, err.message, err.problems) == ("overlap", p.message, (p,))


def test_state_conflict_is_a_rule_violation_that_keeps_its_problem():
    with pytest.raises(RuleViolation) as err:
        touch_for_change(MissionStatus.ACTIVE)
    assert isinstance(err.value, StateConflict)
    assert err.value.code == "mission_frozen"
    assert err.value.problem.message == "Can't edit an active mission"
    assert err.value.problems == (err.value.problem,)


def test_not_found_has_one_code_and_a_message_naming_the_thing():
    err = NotFound("Mission")
    assert (err.code, err.message) == ("not_found", "Mission not found")


def test_invalid_input_is_a_value_error_with_the_validation_code():
    from mission_control.domain.errors import InvalidInput

    err = InvalidInput("Skill level must be between 1 and 5")
    assert isinstance(err, ValueError)
    assert (err.code, err.message) == ("validation_error", "Skill level must be between 1 and 5")


def test_invalid_input_with_only_a_message_has_that_message_as_its_one_problem():
    from mission_control.domain.errors import InvalidInput

    err = InvalidInput("The mission needs a name")
    assert err.problems == (Problem("validation_error", "The mission needs a name"),)


def test_invalid_input_can_list_every_mistake_at_once():
    from mission_control.domain.errors import InvalidInput

    problems = [
        Problem("validation_error", "The mission needs a name"),
        Problem("validation_error", "Engineer needs a headcount of at least 1", {"slot_id": 3}),
    ]
    err = InvalidInput("Some values aren't valid", problems)
    assert (err.code, err.message, str(err)) == (
        "validation_error",
        "Some values aren't valid",
        "Some values aren't valid",
    )
    assert err.problems == tuple(problems)
    assert isinstance(err.problems, tuple)
