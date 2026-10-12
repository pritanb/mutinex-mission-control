"""SF: the repository writes Wave 1 (admin, crew, missions) needs. Every write is scoped."""

import sqlite3
from datetime import date

import pytest

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.infra.repositories import Repos

GATEWAY, REBOOST, TELESCOPE, PAYLOAD = 1, 3, 5, 8


@pytest.fixture
def aurora(seeded_db):
    return Repos(seeded_db, 1)


@pytest.fixture
def helix(seeded_db):
    return Repos(seeded_db, 2)


def window(a, b):
    return DateRange(date.fromisoformat(a), date.fromisoformat(b))


# --- Organisation and users (admin) -------------------------------------------------------


def test_set_required_approvals_changes_only_this_org(aurora, helix):
    aurora.organisation.set_required_approvals(3)
    assert aurora.organisation.get().required_approvals == 3
    assert helix.organisation.get().required_approvals == 1


def test_create_user_in_this_org(seeded_db, aurora):
    user = aurora.users.create("zoe@aurora.example", "Zoe Lane", Role.CREW, "hash")
    assert (user.org_id, user.email, user.role, user.is_active) == (
        1,
        "zoe@aurora.example",
        Role.CREW,
        True,
    )
    assert (
        seeded_db.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,)).fetchone()[0]
        == "hash"
    )


def test_duplicate_email_anywhere_is_refused_by_the_database(aurora):
    with pytest.raises(sqlite3.IntegrityError):
        aurora.users.create("SAM@helix.example", "Sam Again", Role.CREW, "hash")


def test_role_and_active_changes_are_scoped(aurora, helix):
    assert aurora.users.set_role(7, Role.LEAD) is True
    assert aurora.users.get(7).role == Role.LEAD
    assert helix.users.set_role(7, Role.DIRECTOR) is False  # Ben is Aurora's
    assert aurora.users.set_active(7, False) is True
    assert aurora.users.get(7).is_active is False
    assert helix.users.set_active(7, True) is False


def test_count_active_directors(aurora, helix):
    assert aurora.users.count_active_directors() == 3
    aurora.users.set_active(3, False)
    assert aurora.users.count_active_directors() == 2
    assert helix.users.count_active_directors() == 1


def test_missions_a_lead_owns_that_are_not_finished(aurora, helix):
    assert [m.name for m in aurora.missions.non_final_owned_by(4)] == [
        "Orbital Telescope Service",
        "Lunar Gateway Resupply",
    ]  # Mars Analog is completed
    assert helix.missions.non_final_owned_by(4) == []


# --- Crew profiles, skills and unavailability (admin + crew) ------------------------------


def test_create_crew_profile(aurora):
    lee = aurora.crew.create(4, "Lee")
    assert (lee.org_id, lee.user_id, lee.display_name, lee.bio) == (1, 4, "Lee", None)
    assert aurora.crew.by_user(4) == lee


def test_update_crew_profile_details_is_scoped(aurora, helix):
    assert aurora.crew.update(7, display_name="Benjamin", bio="EVA nerd") is True
    assert (aurora.crew.get(7).display_name, aurora.crew.get(7).bio) == ("Benjamin", "EVA nerd")
    assert helix.crew.update(7, display_name="Hijack", bio=None) is False


def test_open_assignments_of_a_crew_member(aurora):
    assert [(a.mission_id, a.status) for a in aurora.crew.open_assignments(8)] == [
        (TELESCOPE, AssignmentStatus.ACCEPTED)
    ]  # Mars Analog's is completed, not open
    assert aurora.crew.open_assignments(11) == []


def test_add_and_remove_unavailability(aurora, helix):
    added = aurora.crew.add_unavailability(7, window("2027-05-01", "2027-05-03"), "Training")
    assert (added.window, added.reason) == (window("2027-05-01", "2027-05-03"), "Training")
    assert added in aurora.crew.unavailability(7)
    assert helix.crew.remove_unavailability(7, added.id) is False
    assert aurora.crew.remove_unavailability(8, added.id) is False  # not Chen's
    assert aurora.crew.remove_unavailability(7, added.id) is True
    assert aurora.crew.unavailability(7) == []


def test_set_skill_inserts_then_updates_and_records_who(seeded_db, aurora):
    aurora.crew.set_skill(7, skill_id=5, level=2, updated_by=4)
    assert aurora.crew.skills(7)[5] == 2
    aurora.crew.set_skill(7, skill_id=5, level=4, updated_by=1)
    assert aurora.crew.skills(7)[5] == 4
    assert (
        seeded_db.execute(
            "SELECT updated_by_id FROM crew_skills WHERE crew_profile_id = 7 AND skill_id = 5"
        ).fetchone()[0]
        == 1
    )


def test_set_skill_cannot_use_another_orgs_skill_or_crew(aurora):
    with pytest.raises(sqlite3.IntegrityError):
        aurora.crew.set_skill(7, skill_id=7, level=3, updated_by=4)  # Helix's Piloting
    with pytest.raises(sqlite3.IntegrityError):
        aurora.crew.set_skill(17, skill_id=1, level=3, updated_by=4)  # Helix's Lena


def test_remove_skill(aurora, helix):
    assert helix.crew.remove_skill(7, 3) is False
    assert aurora.crew.remove_skill(7, 3) is True
    assert 3 not in aurora.crew.skills(7)
    assert aurora.crew.remove_skill(7, 3) is False


# --- Skill catalogue (admin) --------------------------------------------------------------


def test_create_rename_and_categorise_skills(aurora, helix):
    eva2 = aurora.skills.create("Robotics", category="Engineering")
    assert (eva2.org_id, eva2.name, eva2.category) == (1, "Robotics", "Engineering")
    assert aurora.skills.update(eva2.id, name="Robotic Arm", category=None) is True
    assert aurora.skills.get(eva2.id).name == "Robotic Arm"
    assert helix.skills.update(eva2.id, name="Stolen", category=None) is False


def test_skill_in_use_and_delete(aurora, helix):
    assert aurora.skills.is_in_use(1) is True  # Piloting has levels and requirements
    unused = aurora.skills.create("Cartography")
    assert aurora.skills.is_in_use(unused.id) is False
    assert helix.skills.delete(unused.id) is False
    assert aurora.skills.delete(unused.id) is True
    assert aurora.skills.get(unused.id) is None


# --- Missions and slots (missions) --------------------------------------------------------


def test_create_mission_starts_as_draft(aurora):
    m = aurora.missions.create(
        "Europa Flyby", window("2027-09-01", "2027-09-20"), owner_id=4, created_by_id=1
    )
    assert (
        m.org_id,
        m.status,
        m.owner_id,
        m.created_by_id,
        m.approval_round,
        m.approvals_required,
    ) == (1, MissionStatus.DRAFT, 4, 1, 0, None)


def test_update_mission_name_and_dates_is_scoped(aurora, helix):
    assert (
        aurora.missions.update(
            GATEWAY, name="Gateway II", window=window("2027-03-02", "2027-03-11")
        )
        is True
    )
    m = aurora.missions.get(GATEWAY)
    assert (m.name, m.window) == ("Gateway II", window("2027-03-02", "2027-03-11"))
    assert helix.missions.update(GATEWAY, name="X", window=m.window) is False


def test_set_status_and_owner(aurora, helix):
    assert aurora.missions.set_status(GATEWAY, MissionStatus.CANCELLED) is True
    assert aurora.missions.get(GATEWAY).status == MissionStatus.CANCELLED
    assert aurora.missions.set_owner(TELESCOPE, 5) is True
    assert aurora.missions.get(TELESCOPE).owner_id == 5
    assert helix.missions.set_owner(TELESCOPE, 14) is False


def test_owner_from_another_org_is_refused_by_the_database(aurora):
    with pytest.raises(sqlite3.IntegrityError):
        aurora.missions.set_owner(GATEWAY, 15)  # Priya is Helix's


def test_add_slot_goes_to_the_end_with_its_requirements(aurora):
    slot = aurora.missions.add_slot(GATEWAY, "Medic", 1, {6: 3})
    assert (slot.name, slot.headcount, slot.position) == ("Medic", 1, 4)
    assert [(r.skill_name, r.min_level) for r in slot.requirements] == [("Flight Medicine", 3)]
    assert [s.name for s in aurora.missions.slots(GATEWAY)][-1] == "Medic"


def test_add_slot_to_another_orgs_mission_is_refused(helix):
    with pytest.raises(sqlite3.IntegrityError):
        helix.missions.add_slot(GATEWAY, "Intruder", 1, {7: 1})


def test_update_slot_and_replace_requirements(aurora, helix):
    commander = aurora.missions.slots(GATEWAY)[2]
    assert aurora.missions.update_slot(commander.id, name="Captain", headcount=2) is True
    assert aurora.missions.replace_requirements(commander.id, {1: 5}) is True
    captain = aurora.missions.get_slot(commander.id)
    assert (captain.name, captain.headcount) == ("Captain", 2)
    assert [(r.skill_id, r.min_level) for r in captain.requirements] == [(1, 5)]
    assert helix.missions.update_slot(commander.id, name="X", headcount=1) is False
    assert helix.missions.replace_requirements(commander.id, {7: 1}) is False


def test_remove_slot_hides_it_but_keeps_its_history(seeded_db, aurora):
    commander = aurora.missions.slots(GATEWAY)[2]
    assert aurora.missions.remove_slot(commander.id) is True
    assert commander.id not in {s.id for s in aurora.missions.slots(GATEWAY)}
    assert aurora.missions.get_slot(commander.id) is None
    assert (
        seeded_db.execute("SELECT removed_at FROM slots WHERE id = ?", (commander.id,)).fetchone()[
            0
        ]
        is not None
    )
    assert aurora.missions.remove_slot(commander.id) is False  # already removed


def test_get_slot_is_scoped(aurora, helix):
    slot_id = aurora.missions.slots(GATEWAY)[0].id
    assert aurora.missions.get_slot(slot_id).name == "Flight Engineer"
    assert helix.missions.get_slot(slot_id) is None


def test_updates_stamp_updated_at(seeded_db, aurora):
    seeded_db.execute("UPDATE missions SET updated_at = '2000-01-01T00:00:00.000Z' WHERE id = 1")
    aurora.missions.update(GATEWAY, name="Gateway", window=window("2027-03-01", "2027-03-10"))
    assert seeded_db.execute("SELECT updated_at FROM missions WHERE id = 1").fetchone()[0] > (
        "2000-01-01T00:00:00.000Z"
    )
