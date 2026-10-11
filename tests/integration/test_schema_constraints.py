"""M6: what the schema itself refuses (design §3 'Enforced by the database', Appendix A)."""

import sqlite3

import pytest


@pytest.fixture
def two_orgs(conn):
    """Org 1 (Aurora) and org 2 (Helix), each with a Director, a Lead, a crew member, a skill
    and a Draft mission with one slot. Returns the ids by name."""
    q = conn.execute
    q(
        "INSERT INTO organisations(id, name, slug, required_approvals) VALUES"
        " (1, 'Aurora', 'aurora', 2), (2, 'Helix', 'helix', 1)"
    )
    q(
        "INSERT INTO users(id, org_id, email, name, role, password_hash) VALUES"
        " (1, 1, 'ruth@aurora.example', 'Ruth', 'director', 'h'),"
        " (2, 1, 'lee@aurora.example', 'Lee', 'lead', 'h'),"
        " (3, 1, 'ben@aurora.example', 'Ben', 'crew', 'h'),"
        " (4, 2, 'sam@helix.example', 'Sam', 'director', 'h'),"
        " (5, 2, 'priya@helix.example', 'Priya', 'lead', 'h'),"
        " (6, 2, 'kai@helix.example', 'Kai', 'crew', 'h')"
    )
    q(
        "INSERT INTO crew_profiles(id, org_id, user_id, display_name) VALUES"
        " (1, 1, 3, 'Ben'), (2, 2, 6, 'Kai')"
    )
    q("INSERT INTO skills(id, org_id, name) VALUES (1, 1, 'Piloting'), (2, 2, 'Piloting')")
    q(
        "INSERT INTO missions(id, org_id, name, start_date, end_date, owner_id, created_by_id)"
        " VALUES (1, 1, 'Gateway', '2027-03-01', '2027-03-10', 2, 1),"
        " (2, 2, 'Payload Demo', '2027-02-01', '2027-02-03', 5, 5),"
        " (3, 1, 'Asteroid Survey', '2027-03-05', '2027-03-12', 2, 2)"
    )
    q(
        "INSERT INTO slots(id, org_id, mission_id, name, headcount, position) VALUES"
        " (1, 1, 1, 'Commander', 1, 1), (2, 2, 2, 'Pilot', 1, 1), (3, 1, 3, 'Pilot', 1, 1)"
    )
    return conn


def rejects(conn, sql, *args, match=""):
    with pytest.raises(sqlite3.IntegrityError, match=match):
        conn.execute(sql, args)


# --- Composite tenant foreign keys: no cross-organisation links ---------------------------


def test_crew_skill_cannot_use_another_orgs_skill(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
        " updated_by_id) VALUES (1, 1, 2, 3, 1)",
        match="FOREIGN KEY",
    )


def test_crew_skill_cannot_target_another_orgs_crew(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
        " updated_by_id) VALUES (1, 2, 1, 3, 1)",
        match="FOREIGN KEY",
    )


def test_mission_owner_must_be_in_the_same_org(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO missions(org_id, name, start_date, end_date, owner_id,"
        " created_by_id) VALUES (1, 'X', '2027-01-01', '2027-01-02', 5, 1)",
        match="FOREIGN KEY",
    )


def test_assignment_cannot_use_another_orgs_crew(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id) VALUES (1, 1, 1, 2, 2)",
        match="FOREIGN KEY",
    )


def test_assignment_slot_must_belong_to_its_mission(two_orgs):
    # slot 3 is Asteroid Survey's, not Gateway's
    rejects(
        two_orgs,
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id) VALUES (1, 1, 3, 1, 2)",
        match="FOREIGN KEY",
    )


def test_slot_requirement_cannot_use_another_orgs_skill(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level) VALUES (1, 1, 2, 3)",
        match="FOREIGN KEY",
    )


def test_approval_cannot_come_from_another_orgs_director(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
        " VALUES (1, 1, 1, 4, 'approve')",
        match="FOREIGN KEY",
    )


def test_same_org_links_are_accepted(two_orgs):
    two_orgs.execute(
        "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
        " updated_by_id) VALUES (1, 1, 1, 4, 1)"
    )
    two_orgs.execute(
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id) VALUES (1, 1, 1, 1, 2)"
    )


# --- Value checks -------------------------------------------------------------------------


@pytest.mark.parametrize("level", [0, 6])
def test_skill_level_must_be_1_to_5(two_orgs, level):
    rejects(
        two_orgs,
        "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
        " updated_by_id) VALUES (1, 1, 1, ?, 1)",
        level,
        match="CHECK",
    )


def test_strict_tables_reject_the_wrong_type(two_orgs):
    with pytest.raises(sqlite3.IntegrityError):
        two_orgs.execute("UPDATE organisations SET required_approvals = 'two' WHERE id = 1")


def test_required_approvals_must_be_at_least_1(two_orgs):
    rejects(two_orgs, "UPDATE organisations SET required_approvals = 0 WHERE id = 1", match="CHECK")


@pytest.mark.parametrize(
    "start, end",
    [
        ("2027-03-10", "2027-03-01"),
        ("2027-3-1", "2027-03-10"),
        ("2027-02-30", "2027-03-10"),
        ("not a date", "2027-03-10"),
    ],
)
def test_mission_dates_must_be_valid_and_ordered(two_orgs, start, end):
    rejects(
        two_orgs,
        "INSERT INTO missions(org_id, name, start_date, end_date, owner_id,"
        " created_by_id) VALUES (1, 'X', ?, ?, 2, 1)",
        start,
        end,
        match="CHECK",
    )


def test_past_dates_are_allowed(two_orgs):
    two_orgs.execute(
        "INSERT INTO missions(org_id, name, start_date, end_date, owner_id,"
        " created_by_id) VALUES (1, 'Mars Analog', '2026-05-01', '2026-05-30', 2, 1)"
    )


def test_unavailability_needs_a_reason_and_ordered_dates(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date,"
        " reason) VALUES (1, 1, '2027-03-05', '2027-03-08', '  ')",
        match="CHECK",
    )
    rejects(
        two_orgs,
        "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date,"
        " reason) VALUES (1, 1, '2027-03-08', '2027-03-05', 'Medical')",
        match="CHECK",
    )


def test_headcount_must_be_at_least_1(two_orgs):
    rejects(two_orgs, "UPDATE slots SET headcount = 0 WHERE id = 1", match="CHECK")


def test_mission_past_draft_must_have_its_approval_count_saved(two_orgs):
    rejects(two_orgs, "UPDATE missions SET status = 'pending_approval' WHERE id = 1", match="CHECK")
    two_orgs.execute(
        "UPDATE missions SET status = 'pending_approval', approvals_required = 2,"
        " approval_round = 1 WHERE id = 1"
    )


def test_unknown_status_and_role_values_are_rejected(two_orgs):
    rejects(two_orgs, "UPDATE missions SET status = 'approved' WHERE id = 1", match="CHECK")
    rejects(two_orgs, "UPDATE users SET role = 'admin' WHERE id = 1", match="CHECK")


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_withdrawal_needs_a_reason(two_orgs, reason):
    two_orgs.execute(
        "INSERT INTO assignments(id, org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id, status) VALUES (1, 1, 1, 1, 1, 2, 'accepted')"
    )
    rejects(
        two_orgs,
        "UPDATE assignments SET status = 'withdrawn', reason = ? WHERE id = 1",
        reason,
        match="CHECK",
    )


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_rejection_needs_a_reason(two_orgs, reason):
    rejects(
        two_orgs,
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision,"
        " reason) VALUES (1, 1, 1, 1, 'reject', ?)",
        reason,
        match="CHECK",
    )


def test_approval_needs_no_reason(two_orgs):
    two_orgs.execute(
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
        " VALUES (1, 1, 1, 1, 'approve')"
    )


# --- Uniqueness ---------------------------------------------------------------------------


def test_one_open_assignment_per_person_per_mission(two_orgs):
    two_orgs.execute(
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id) VALUES (1, 1, 1, 1, 2)"
    )
    rejects(
        two_orgs,
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id, status) VALUES (1, 1, 1, 1, 2, 'accepted')",
        match="UNIQUE",
    )


def test_closed_assignments_do_not_block_a_new_proposal(two_orgs):
    two_orgs.execute(
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id, status) VALUES (1, 1, 1, 1, 2, 'declined')"
    )
    two_orgs.execute(
        "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
        " proposed_by_id) VALUES (1, 1, 1, 1, 2)"
    )


def test_a_director_decides_each_round_once(two_orgs):
    two_orgs.execute(
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
        " VALUES (1, 1, 1, 1, 'approve')"
    )
    rejects(
        two_orgs,
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision,"
        " reason) VALUES (1, 1, 1, 1, 'reject', 'changed my mind')",
        match="UNIQUE",
    )
    two_orgs.execute(
        "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
        " VALUES (1, 1, 2, 1, 'approve')"
    )  # a new round is fine


def test_skill_names_are_unique_per_org_ignoring_case(two_orgs):
    rejects(two_orgs, "INSERT INTO skills(org_id, name) VALUES (1, 'piloting')", match="UNIQUE")
    # org 2 already has its own "Piloting" (fixture) — same name in another org is fine


def test_emails_are_unique_across_the_platform_ignoring_case(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO users(org_id, email, name, role, password_hash)"
        " VALUES (2, 'RUTH@aurora.example', 'Ruth 2', 'crew', 'h')",
        match="UNIQUE",
    )


def test_a_user_has_at_most_one_crew_profile(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO crew_profiles(org_id, user_id, display_name) VALUES (1, 3, 'Ben again')",
        match="UNIQUE",
    )


def test_removed_slots_free_their_position(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
        " VALUES (1, 1, 'Second Commander', 1, 1)",
        match="UNIQUE",
    )
    two_orgs.execute("UPDATE slots SET removed_at = '2027-01-01T00:00:00Z' WHERE id = 1")
    two_orgs.execute(
        "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
        " VALUES (1, 1, 'New Commander', 1, 1)"
    )


# --- Deletion rules and the audit log -----------------------------------------------------


def test_a_skill_in_use_cannot_be_deleted_but_an_unused_one_can(two_orgs):
    two_orgs.execute(
        "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level) VALUES (1, 1, 1, 4)"
    )
    rejects(two_orgs, "DELETE FROM skills WHERE id = 1", match="FOREIGN KEY")
    two_orgs.execute("INSERT INTO skills(id, org_id, name) VALUES (9, 1, 'Unused')")
    two_orgs.execute("DELETE FROM skills WHERE id = 9")


def test_deleting_a_slot_deletes_its_requirements(two_orgs):
    two_orgs.execute(
        "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level) VALUES (1, 3, 1, 4)"
    )
    two_orgs.execute("DELETE FROM slots WHERE id = 3")
    assert two_orgs.execute("SELECT count(*) FROM slot_requirements").fetchone()[0] == 0


def test_audit_events_are_append_only(two_orgs):
    two_orgs.execute(
        "INSERT INTO audit_events(id, org_id, actor_id, event, mission_id)"
        " VALUES (1, 1, 1, 'mission.submitted', 1)"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        two_orgs.execute("UPDATE audit_events SET event = 'x' WHERE id = 1")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        two_orgs.execute("DELETE FROM audit_events WHERE id = 1")


def test_audit_data_must_be_valid_json(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO audit_events(org_id, actor_id, event, data) VALUES (1, 1, 'x', 'not json')",
        match="CHECK",
    )


def test_audit_events_cannot_reference_another_orgs_mission(two_orgs):
    rejects(
        two_orgs,
        "INSERT INTO audit_events(org_id, actor_id, event, mission_id) VALUES (1, 1, 'x', 2)",
        match="FOREIGN KEY",
    )
