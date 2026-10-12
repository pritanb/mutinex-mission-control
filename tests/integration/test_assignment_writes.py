"""M12: the assignment repository writes. Every write is scoped to the caller's organisation
(T1, AC-29) and the database still enforces one open assignment per person per mission (S1)
and a reason on every withdrawal (S3)."""

import sqlite3

import pytest

from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories import Repos

GATEWAY, REBOOST, PAYLOAD = 1, 3, 8
FLIGHT_ENGINEER, SPECIALIST, PAYLOAD_SPECIALIST = 1, 2, 12
LEE, CHEN, GUS, KAI, PRIYA = 4, 8, 12, 16, 15
BEN_ON_COMMS = 7


@pytest.fixture
def aurora(seeded_db):
    return Repos(seeded_db, 1)


@pytest.fixture
def helix(seeded_db):
    return Repos(seeded_db, 2)


def test_s1_create_a_proposal(seeded_db, aurora):
    made = aurora.assignments.create(GATEWAY, FLIGHT_ENGINEER, CHEN, proposed_by_id=LEE)
    assert (made.mission_id, made.slot_id, made.crew_profile_id, made.status, made.reason) == (
        GATEWAY,
        FLIGHT_ENGINEER,
        CHEN,
        AssignmentStatus.PROPOSED,
        None,
    )
    row = seeded_db.execute(
        "SELECT org_id, proposed_by_id FROM assignments WHERE id = ?", (made.id,)
    ).fetchone()
    assert tuple(row) == (1, LEE)


def test_s1_database_refuses_a_second_open_assignment_on_a_mission(aurora):
    aurora.assignments.create(GATEWAY, FLIGHT_ENGINEER, CHEN, proposed_by_id=LEE)
    with pytest.raises(sqlite3.IntegrityError):
        aurora.assignments.create(GATEWAY, SPECIALIST, CHEN, proposed_by_id=LEE)


@pytest.mark.parametrize(
    "mission, slot, crew, proposer",
    [
        (PAYLOAD, PAYLOAD_SPECIALIST, CHEN, LEE),  # Helix mission and slot
        (GATEWAY, FLIGHT_ENGINEER, KAI, LEE),  # Helix crew member
        (GATEWAY, FLIGHT_ENGINEER, CHEN, PRIYA),  # Helix proposer
        (GATEWAY, PAYLOAD_SPECIALIST, CHEN, LEE),  # slot of another mission
    ],
)
def test_ac29_create_refuses_links_across_organisations_or_missions(
    aurora, mission, slot, crew, proposer
):
    with pytest.raises(sqlite3.IntegrityError):
        aurora.assignments.create(mission, slot, crew, proposed_by_id=proposer)


def test_set_status_changes_status_and_reason(aurora):
    assert aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.WITHDRAWN, "Moving")
    got = aurora.assignments.get(BEN_ON_COMMS)
    assert (got.status, got.reason) == (AssignmentStatus.WITHDRAWN, "Moving")


def test_set_status_stamps_updated_at(seeded_db, aurora):
    seeded_db.execute("UPDATE assignments SET updated_at = '2000-01-01T00:00:00.000Z'")
    aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.REMOVED)
    stamp = seeded_db.execute(
        "SELECT updated_at FROM assignments WHERE id = ?", (BEN_ON_COMMS,)
    ).fetchone()[0]
    assert stamp > "2000-01-01T00:00:00.000Z"


def test_ac29_set_status_cannot_reach_another_organisations_assignment(aurora, helix):
    assert not helix.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.REMOVED)
    assert aurora.assignments.get(BEN_ON_COMMS).status == AssignmentStatus.ACCEPTED


def test_s3_database_refuses_a_withdrawal_without_a_reason(aurora):
    with pytest.raises(sqlite3.IntegrityError):
        aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.WITHDRAWN, "  ")
