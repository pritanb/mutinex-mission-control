"""M7: tenant-scoped repositories and visibility (design §4 tenant isolation, PRD V2)."""

from datetime import date

import pytest

from builders import make_assignment, make_crew_profile, make_mission, make_slot, make_user
from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.permissions import Actor
from mission_control.infra.repositories import Repos

AURORA, HELIX = 1, 2
GATEWAY, TELESCOPE, COMMS, MARS, PAYLOAD = 1, 5, 6, 7, 8
LEE, BEN, CHEN, KAI_USER = 4, 7, 8, 16


@pytest.fixture
def aurora(seeded_db):
    return Repos(seeded_db, AURORA)


@pytest.fixture
def helix(seeded_db):
    return Repos(seeded_db, HELIX)


# --- Scoping: another organisation's id behaves exactly like a missing one ----------------


def test_get_returns_the_record_for_its_own_org(aurora):
    m = aurora.missions.get(GATEWAY)
    assert m.name == "Lunar Gateway Resupply"
    assert m.window == DateRange(date(2027, 3, 1), date(2027, 3, 10))
    assert m.status == MissionStatus.DRAFT
    assert (m.owner_id, m.created_by_id) == (LEE, 1)


@pytest.mark.parametrize(
    "repo, foreign_id",
    [
        ("missions", PAYLOAD),
        ("users", KAI_USER),
        ("crew", 16),
        ("skills", 7),
        ("assignments", 9),
        ("approvals", 1),
    ],
)
def test_get_returns_none_for_another_orgs_id(helix, aurora, repo, foreign_id):
    own = helix if repo != "approvals" else aurora
    other = aurora if repo != "approvals" else helix
    assert getattr(own, repo).get(foreign_id) is not None
    assert getattr(other, repo).get(foreign_id) is None


def test_get_returns_none_for_a_missing_id(aurora):
    assert aurora.missions.get(9999) is None


@pytest.mark.parametrize("repo", ["missions", "users", "crew", "skills"])
def test_lists_only_contain_the_callers_org(aurora, helix, repo):
    assert {r.org_id for r in getattr(aurora, repo).list()} == {AURORA}
    assert {r.org_id for r in getattr(helix, repo).list()} == {HELIX}


def test_organisation_is_always_the_callers_own(aurora, helix):
    assert aurora.organisation.get().slug == "aurora"
    assert helix.organisation.get().required_approvals == 1


def test_mission_children_from_another_org_are_empty(helix):
    assert helix.missions.slots(GATEWAY) == []
    assert helix.missions.assignments(GATEWAY) == []


def test_skill_lookup_by_name_is_scoped_and_case_insensitive(aurora, helix):
    assert aurora.skills.by_name("piloting").id == 1
    assert helix.skills.by_name("Piloting").id == 7
    assert aurora.skills.by_name("Payload Integration") is None


# --- Reading a mission's parts ------------------------------------------------------------


def test_slots_come_in_listed_order_with_named_requirements(aurora):
    slots = aurora.missions.slots(GATEWAY)
    assert [s.name for s in slots] == ["Flight Engineer", "Mission Specialist", "Commander"]
    commander = slots[2]
    assert {(r.skill_name, r.min_level) for r in commander.requirements} == {
        ("Piloting", 4),
        ("Leadership", 3),
    }


def test_removed_slots_are_not_listed(seeded_db, aurora):
    seeded_db.execute(
        "UPDATE slots SET removed_at = '2027-01-01T00:00:00Z'"
        " WHERE mission_id = ? AND name = 'Commander'",
        (GATEWAY,),
    )
    assert [s.name for s in aurora.missions.slots(GATEWAY)] == [
        "Flight Engineer",
        "Mission Specialist",
    ]


def test_assignments_can_be_filtered_by_status(aurora):
    all_ = aurora.missions.assignments(TELESCOPE)
    assert len(all_) == 4
    assert {a.status for a in all_} == {AssignmentStatus.ACCEPTED}
    assert aurora.missions.assignments(TELESCOPE, statuses={AssignmentStatus.PROPOSED}) == []


def test_approvals_for_a_round(aurora):
    assert [a.director_id for a in aurora.approvals.for_round(TELESCOPE, 1)] == [2, 3]
    assert aurora.approvals.for_round(TELESCOPE, 2) == []


def test_crew_skills_and_unavailability(aurora):
    fay = aurora.crew.by_user(11)
    assert aurora.crew.skills(fay.id) == {1: 4, 2: 4}
    [leave] = aurora.crew.unavailability(fay.id)
    assert leave.window == DateRange(date(2027, 3, 5), date(2027, 3, 8))
    assert leave.reason == "Medical"


def test_user_has_role_and_active_flag_but_no_password_hash(aurora):
    lee = aurora.users.get(LEE)
    assert (lee.email, lee.role, lee.is_active) == ("lee@aurora.example", Role.LEAD, True)
    assert not hasattr(lee, "password_hash")


# --- Visibility (PRD §5.7, V2) ------------------------------------------------------------


def actor(user_id, role, crew_profile_id=None, org=AURORA):
    return Actor(user_id=user_id, org_id=org, role=role, crew_profile_id=crew_profile_id)


def test_directors_and_leads_see_every_mission_in_their_org(aurora):
    all_ids = {m.id for m in aurora.missions.list()}
    assert {m.id for m in aurora.missions.list_visible(actor(1, Role.DIRECTOR))} == all_ids
    assert {m.id for m in aurora.missions.list_visible(actor(LEE, Role.LEAD))} == all_ids


def test_crew_see_only_missions_they_are_on_including_completed(aurora):
    chen = actor(CHEN, Role.CREW, crew_profile_id=CHEN)
    assert {m.id for m in aurora.missions.list_visible(chen)} == {TELESCOPE, MARS}
    ben = actor(BEN, Role.CREW, crew_profile_id=BEN)
    assert {m.id for m in aurora.missions.list_visible(ben)} == {COMMS}


def test_crew_without_assignments_see_no_missions(aurora):
    assert aurora.missions.list_visible(actor(11, Role.CREW, crew_profile_id=11)) == []


def test_get_visible_hides_missions_the_crew_member_is_not_on(aurora):
    ben = actor(BEN, Role.CREW, crew_profile_id=BEN)
    assert aurora.missions.get_visible(ben, COMMS).name == "Deep Space Comms Upgrade"
    assert aurora.missions.get_visible(ben, GATEWAY) is None


@pytest.mark.parametrize("status", ["proposed", "accepted"])
def test_an_open_assignment_makes_the_mission_visible(seeded_db, aurora, status):
    slot = make_slot(seeded_db, AURORA, GATEWAY, name="Extra", position=9)
    make_assignment(seeded_db, AURORA, GATEWAY, slot, 11, LEE, status=status)
    fay = actor(11, Role.CREW, crew_profile_id=11)
    assert aurora.missions.get_visible(fay, GATEWAY) is not None


@pytest.mark.parametrize(
    "status, reason",
    [("declined", None), ("withdrawn", "family"), ("removed", None), ("cancelled", None)],
)
def test_v2_former_assignees_lose_the_mission_but_keep_a_summary(seeded_db, aurora, status, reason):
    slot = make_slot(seeded_db, AURORA, GATEWAY, name="Extra", position=9)
    make_assignment(seeded_db, AURORA, GATEWAY, slot, 11, LEE, status=status, reason=reason)
    fay = actor(11, Role.CREW, crew_profile_id=11)
    assert aurora.missions.get_visible(fay, GATEWAY) is None
    assert GATEWAY not in {m.id for m in aurora.missions.list_visible(fay)}
    [summary] = aurora.crew.history(11)
    assert (summary.mission_id, summary.mission_name, summary.slot_name) == (
        GATEWAY,
        "Lunar Gateway Resupply",
        "Extra",
    )
    assert summary.status == AssignmentStatus(status)
    assert summary.reason == reason
    assert summary.window == DateRange(date(2027, 3, 1), date(2027, 3, 10))


def test_history_lists_every_assignment_newest_mission_first(aurora):
    history = aurora.crew.history(CHEN)
    assert [(h.mission_name, h.status) for h in history] == [
        ("Orbital Telescope Service", AssignmentStatus.ACCEPTED),
        ("Mars Analog Habitat", AssignmentStatus.COMPLETED),
    ]


def test_history_of_another_orgs_crew_is_empty(helix):
    assert helix.crew.history(CHEN) == []


def test_a_crew_member_in_another_org_sees_nothing_here(seeded_db):
    # Same numeric crew_profile_id cannot leak across orgs: repos are built from the actor's org.
    other_org = 2
    org_user = make_user(seeded_db, other_org, name="Visitor")
    profile = make_crew_profile(seeded_db, other_org, org_user, display_name="Visitor")
    visitor = actor(org_user, Role.CREW, crew_profile_id=profile, org=other_org)
    assert Repos(seeded_db, other_org).missions.list_visible(visitor) == []
    mission = make_mission(seeded_db, other_org, owner_id=15)
    assert Repos(seeded_db, AURORA).missions.get(mission) is None
