"""M16: parsing what the user types. The `--slot` spec, requirement lists and dates (design §8).

Only syntax is checked here. Rules such as a headcount of at least 1 or a level from 1 to 5 belong
to the server, so values that parse are passed through for it to judge.
"""

import pytest

from mission_control.cli.resolve import SpecError, parse_requirements, parse_slot_spec


def test_m16_slot_spec_parses_name_headcount_and_requirements():
    spec = parse_slot_spec("Commander:1:Piloting>=4,Leadership>=3")

    assert spec.name == "Commander"
    assert spec.headcount == 1
    assert spec.requirements == (("Piloting", 4), ("Leadership", 3))


def test_m16_slot_spec_trims_spaces_and_keeps_multi_word_names():
    spec = parse_slot_spec(" Flight Engineer : 2 : Systems Engineering >= 3 , EVA>=2 ")

    assert spec.name == "Flight Engineer"
    assert spec.headcount == 2
    assert spec.requirements == (("Systems Engineering", 3), ("EVA", 2))


def test_m16_slot_spec_allows_a_colon_in_the_slot_name():
    spec = parse_slot_spec("Ops: Night:1:EVA>=3")

    assert spec.name == "Ops: Night"
    assert spec.requirements == (("EVA", 3),)


def test_m2_slot_spec_passes_rule_breaking_numbers_through_to_the_server():
    """Headcount 0 and level 9 parse; the server refuses them with every mistake listed."""
    spec = parse_slot_spec("Commander:0:Piloting>=9")

    assert spec.headcount == 0
    assert spec.requirements == (("Piloting", 9),)


def test_m2_slot_spec_with_no_requirements_is_left_for_the_server_to_refuse():
    assert parse_slot_spec("Commander:1:").requirements == ()


@pytest.mark.parametrize(
    "text",
    ["Commander", "Commander:1", "Commander:one:Piloting>=4", ":1:Piloting>=4"],
)
def test_m16_slot_spec_rejects_malformed_text_with_the_expected_format(text):
    with pytest.raises(SpecError) as raised:
        parse_slot_spec(text)

    assert "NAME:HEADCOUNT:SKILL>=LEVEL" in str(raised.value)
    assert "Commander:1:Piloting>=4,Leadership>=3" in str(raised.value)


@pytest.mark.parametrize("text", ["Piloting", "Piloting>=", ">=4", "Piloting=4", "Piloting>=x"])
def test_m16_requirements_reject_an_entry_without_skill_and_level(text):
    with pytest.raises(SpecError) as raised:
        parse_requirements(text)

    assert "SKILL>=LEVEL" in str(raised.value)
