from datetime import date

import pytest

from mission_control.domain.dates import DateRange, InvalidDateRange


def r(start: str, end: str) -> DateRange:
    return DateRange(date.fromisoformat(start), date.fromisoformat(end))


# Overlap (PRD §5.1 "Overlap", AC-17)


def test_ac17_ranges_sharing_only_a_boundary_day_overlap():
    assert r("2027-02-25", "2027-03-01").overlaps(r("2027-03-01", "2027-03-10"))
    assert r("2027-03-01", "2027-03-10").overlaps(r("2027-02-25", "2027-03-01"))


def test_overlap_when_one_range_contains_the_other():
    assert r("2027-03-01", "2027-03-31").overlaps(r("2027-03-05", "2027-03-08"))
    assert r("2027-03-05", "2027-03-08").overlaps(r("2027-03-01", "2027-03-31"))


def test_overlap_with_identical_single_day_ranges():
    assert r("2027-03-05", "2027-03-05").overlaps(r("2027-03-05", "2027-03-05"))


def test_adjacent_ranges_do_not_overlap():
    assert not r("2027-02-25", "2027-02-28").overlaps(r("2027-03-01", "2027-03-10"))
    assert not r("2027-03-01", "2027-03-10").overlaps(r("2027-02-25", "2027-02-28"))


def test_separate_ranges_do_not_overlap():
    assert not r("2027-01-10", "2027-01-14").overlaps(r("2027-03-01", "2027-03-10"))


# Mission-days (PRD §5.1 "Mission-days")


def test_mission_days_counts_both_start_and_end():
    # PRD §9: Lunar Gateway Resupply, 1–10 Mar = 10 mission-days
    assert r("2027-03-01", "2027-03-10").mission_days == 10


def test_mission_days_single_day_range_is_one():
    assert r("2027-03-05", "2027-03-05").mission_days == 1


def test_mission_days_across_month_boundary():
    # PRD §9: Station Reboost, 25 Feb – 2 Mar 2027 = 6 mission-days (Gus's workload)
    assert r("2027-02-25", "2027-03-02").mission_days == 6


# Validity (PRD M2)


def test_m2_end_before_start_is_rejected():
    with pytest.raises(InvalidDateRange):
        r("2027-03-10", "2027-03-01")


def test_m2_invalid_date_range_is_a_value_error():
    with pytest.raises(ValueError):
        r("2027-03-10", "2027-03-01")


def test_m2_past_dates_are_allowed():
    # PRD §9: Mars Analog Habitat, May 2026 (in the past) is a valid range
    past = r("2026-05-01", "2026-05-30")
    assert past.mission_days == 30


def test_date_range_is_immutable():
    rng = r("2027-03-01", "2027-03-10")
    with pytest.raises(AttributeError):
        rng.start = date(2027, 1, 1)  # type: ignore[misc]
