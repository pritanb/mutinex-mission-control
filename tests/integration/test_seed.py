"""M7: the seed reproduces PRD §9 exactly (people, skills, missions, states, id order)."""

import pytest

from mission_control.seed.data import DEMO_PASSWORD
from mission_control.seed.loader import load_seed


def rows(conn, sql, *args):
    return [tuple(r) for r in conn.execute(sql, args)]


def one(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


def test_two_organisations_with_their_approval_counts(seeded_db):
    assert rows(seeded_db, "SELECT slug, required_approvals FROM organisations ORDER BY id") == [
        ("aurora", 2),
        ("helix", 1),
    ]


def test_people_and_roles_in_prd_table_order(seeded_db):
    aurora = rows(seeded_db, "SELECT id, name, role FROM users WHERE org_id = 1 ORDER BY id")
    assert [(i, n.split()[0], r) for i, n, r in aurora] == [
        (1, "Ruth", "director"),
        (2, "Marco", "director"),
        (3, "Ingrid", "director"),
        (4, "Lee", "lead"),
        (5, "Nora", "lead"),
        (6, "Ana", "lead"),
        (7, "Ben", "crew"),
        (8, "Chen", "crew"),
        (9, "Dana", "crew"),
        (10, "Eli", "crew"),
        (11, "Fay", "crew"),
        (12, "Gus", "crew"),
        (13, "Hana", "crew"),
    ]
    helix = rows(seeded_db, "SELECT name, role FROM users WHERE org_id = 2 ORDER BY id")
    assert [(n.split()[0], r) for n, r in helix] == [
        ("Sam", "director"),
        ("Priya", "lead"),
        ("Kai", "crew"),
        ("Lena", "crew"),
        ("Omar", "crew"),
        ("Tess", "crew"),
    ]


def test_emails_follow_firstname_at_org_example(seeded_db):
    assert one(seeded_db, "SELECT email FROM users WHERE id = 4") == "lee@aurora.example"
    assert one(seeded_db, "SELECT email FROM users WHERE name LIKE 'Sam%'") == "sam@helix.example"


def test_crew_profiles_use_their_users_id_so_the_tie_break_follows_table_order(seeded_db):
    # The matcher's last tie-break is crew_profiles.id; tests/builders.py uses the same ids.
    profiles = rows(
        seeded_db,
        "SELECT id, user_id, display_name FROM crew_profiles WHERE org_id = 1 ORDER BY id",
    )
    assert [(i, u) for i, u, _ in profiles] == [(u, u) for u in (2, 6, 7, 8, 9, 10, 11, 12, 13)]
    assert [n for *_, n in profiles] == [
        "Marco",
        "Ana",
        "Ben",
        "Chen",
        "Dana",
        "Eli",
        "Fay",
        "Gus",
        "Hana",
    ]


def test_every_crew_member_has_a_profile_and_some_others_do_too(seeded_db):
    assert (
        one(
            seeded_db,
            "SELECT count(*) FROM users u WHERE role = 'crew' AND NOT EXISTS"
            " (SELECT 1 FROM crew_profiles p WHERE p.user_id = u.id)",
        )
        == 0
    )
    others = rows(
        seeded_db,
        "SELECT u.name FROM users u JOIN crew_profiles p ON p.user_id = u.id"
        " WHERE u.role != 'crew' ORDER BY u.id",
    )
    assert [n.split()[0] for (n,) in others] == ["Marco", "Ana"]


def test_skill_catalogues_are_separate_per_organisation(seeded_db):
    assert rows(seeded_db, "SELECT id, name FROM skills WHERE org_id = 1 ORDER BY id") == [
        (1, "Piloting"),
        (2, "Leadership"),
        (3, "Systems Engineering"),
        (4, "EVA"),
        (5, "Geology"),
        (6, "Flight Medicine"),
    ]
    assert [
        n for (n,) in rows(seeded_db, "SELECT name FROM skills WHERE org_id = 2 ORDER BY id")
    ] == ["Piloting", "Payload Integration", "Life Support", "Field Medicine"]


@pytest.mark.parametrize(
    "person, skills",
    [
        ("Marco", {"Flight Medicine": 4}),
        ("Ana", {"Piloting": 5, "Leadership": 4, "Systems Engineering": 4}),
        ("Ben", {"Systems Engineering": 4, "EVA": 3}),
        ("Chen", {"Systems Engineering": 3}),
        ("Dana", {"EVA": 4}),
        ("Eli", {"EVA": 4, "Piloting": 4, "Leadership": 2}),
        ("Fay", {"Piloting": 4, "Leadership": 4}),
        ("Gus", {"Systems Engineering": 5}),
        ("Hana", {"EVA": 3, "Geology": 2}),
        ("Kai", {"Piloting": 5}),
        ("Lena", {"Payload Integration": 4}),
        ("Omar", {"Field Medicine": 4}),
        ("Tess", {"Life Support": 3}),
    ],
)
def test_crew_skill_levels_match_the_prd(seeded_db, person, skills):
    got = dict(
        rows(
            seeded_db,
            "SELECT s.name, cs.level FROM crew_skills cs"
            " JOIN skills s ON s.id = cs.skill_id"
            " JOIN crew_profiles p ON p.id = cs.crew_profile_id"
            " WHERE p.display_name = ?",
            person,
        )
    )
    assert got == skills


def test_fay_is_unavailable_5_to_8_march_for_medical_reasons(seeded_db):
    assert rows(seeded_db, "SELECT start_date, end_date, reason FROM unavailability") == [
        ("2027-03-05", "2027-03-08", "Medical")
    ]


MISSIONS = [
    # name, owner, creator, start, end, status, approval_round, approvals_required
    ("Lunar Gateway Resupply", "Lee", "Ruth", "2027-03-01", "2027-03-10", "draft", 0, None),
    ("Asteroid Survey", "Nora", "Nora", "2027-03-05", "2027-03-12", "draft", 0, None),
    ("Station Reboost", "Nora", "Nora", "2027-02-25", "2027-03-02", "draft", 0, None),
    ("Lunar Surface Medical Study", "Nora", "Ruth", "2027-03-15", "2027-03-18", "draft", 0, None),
    ("Orbital Telescope Service", "Lee", "Lee", "2027-01-10", "2027-01-14", "active", 1, 2),
    (
        "Deep Space Comms Upgrade",
        "Nora",
        "Nora",
        "2027-04-01",
        "2027-04-20",
        "pending_approval",
        1,
        2,
    ),
    ("Mars Analog Habitat", "Lee", "Lee", "2026-05-01", "2026-05-30", "completed", 1, 2),
    ("Payload Demo 1", "Priya", "Priya", "2027-02-01", "2027-02-03", "draft", 0, None),
]


def test_missions_owners_dates_and_states_match_the_prd(seeded_db):
    got = rows(
        seeded_db,
        """
        SELECT m.name, o.name, c.name, m.start_date, m.end_date, m.status, m.approval_round,
               m.approvals_required
        FROM missions m JOIN users o ON o.id = m.owner_id JOIN users c ON c.id = m.created_by_id
        ORDER BY m.id""",
    )
    assert [(n, o.split()[0], c.split()[0], *rest) for n, o, c, *rest in got] == MISSIONS


SLOTS = {
    "Lunar Gateway Resupply": [
        ("Flight Engineer", 1, "Systems Engineering>=3"),
        ("Mission Specialist", 1, "EVA>=3"),
        ("Commander", 1, "Leadership>=3,Piloting>=4"),
    ],
    "Asteroid Survey": [("Pilot", 1, "Piloting>=4"), ("Geologist", 1, "Geology>=4")],
    "Station Reboost": [("Engineer", 2, "Systems Engineering>=3")],
    "Lunar Surface Medical Study": [("Flight Surgeon", 1, "Flight Medicine>=4")],
    "Orbital Telescope Service": [
        ("Engineer", 1, "Systems Engineering>=3"),
        ("EVA Specialist", 3, "EVA>=3"),
    ],
    "Deep Space Comms Upgrade": [("Engineer", 1, "Systems Engineering>=3")],
    "Mars Analog Habitat": [("Engineer", 1, "Systems Engineering>=3")],
    "Payload Demo 1": [
        ("Payload Specialist", 1, "Payload Integration>=3"),
        ("Medic", 1, "Field Medicine>=3"),
    ],
}


def test_slots_are_in_listed_order_with_their_requirements(seeded_db):
    got: dict[str, list] = {}
    for mission, slot, headcount, reqs in rows(
        seeded_db,
        """
            SELECT m.name, s.name, s.headcount,
                   (SELECT group_concat(k.name || '>=' || r.min_level, ',')
                    FROM (SELECT * FROM slot_requirements r JOIN skills k ON k.id = r.skill_id
                          WHERE r.slot_id = s.id ORDER BY k.name) r JOIN skills k
                         ON k.id = r.skill_id)
            FROM slots s JOIN missions m ON m.id = s.mission_id ORDER BY m.id, s.position""",
    ):
        got.setdefault(mission, []).append((slot, headcount, reqs))
    assert got == SLOTS


ASSIGNMENTS = [
    ("Station Reboost", "Engineer", "Gus", "accepted"),
    ("Lunar Surface Medical Study", "Flight Surgeon", "Marco", "accepted"),
    ("Orbital Telescope Service", "Engineer", "Chen", "accepted"),
    ("Orbital Telescope Service", "EVA Specialist", "Dana", "accepted"),
    ("Orbital Telescope Service", "EVA Specialist", "Eli", "accepted"),
    ("Orbital Telescope Service", "EVA Specialist", "Hana", "accepted"),
    ("Deep Space Comms Upgrade", "Engineer", "Ben", "accepted"),
    ("Mars Analog Habitat", "Engineer", "Chen", "completed"),
    ("Payload Demo 1", "Payload Specialist", "Lena", "accepted"),
    ("Payload Demo 1", "Medic", "Omar", "accepted"),
]


def test_assignments_match_the_prd(seeded_db):
    assert (
        rows(
            seeded_db,
            """
        SELECT m.name, s.name, p.display_name, a.status FROM assignments a
        JOIN missions m ON m.id = a.mission_id JOIN slots s ON s.id = a.slot_id
        JOIN crew_profiles p ON p.id = a.crew_profile_id ORDER BY a.id""",
        )
        == ASSIGNMENTS
    )


def test_approvals_match_the_seeded_states(seeded_db):
    assert rows(
        seeded_db,
        """
        SELECT m.name, a.round, u.name, a.decision FROM approvals a
        JOIN missions m ON m.id = a.mission_id JOIN users u ON u.id = a.director_id
        ORDER BY a.id""",
    ) == [
        ("Orbital Telescope Service", 1, "Marco Bianchi", "approve"),
        ("Orbital Telescope Service", 1, "Ingrid Holm", "approve"),
        ("Deep Space Comms Upgrade", 1, "Marco Bianchi", "approve"),
        ("Mars Analog Habitat", 1, "Marco Bianchi", "approve"),
        ("Mars Analog Habitat", 1, "Ingrid Holm", "approve"),
    ]


def test_workloads_from_the_seed_match_the_prd(seeded_db):
    # Mission-days of accepted assignments on missions that aren't completed (AC-20).
    got = dict(
        rows(
            seeded_db,
            """
        SELECT p.display_name, coalesce(sum(CASE WHEN a.status = 'accepted'
               AND m.status != 'completed'
               THEN julianday(m.end_date) - julianday(m.start_date) + 1 END), 0)
        FROM crew_profiles p LEFT JOIN assignments a ON a.crew_profile_id = p.id
        LEFT JOIN missions m ON m.id = a.mission_id WHERE p.org_id = 1 GROUP BY p.id""",
        )
    )
    assert got == {
        "Marco": 4,
        "Ana": 0,
        "Ben": 20,
        "Chen": 5,
        "Dana": 5,
        "Eli": 5,
        "Fay": 0,
        "Gus": 6,
        "Hana": 5,
    }


def test_every_seeded_mission_has_an_audit_trail(seeded_db):
    missing = rows(
        seeded_db,
        "SELECT name FROM missions m WHERE NOT EXISTS"
        " (SELECT 1 FROM audit_events e WHERE e.mission_id = m.id)",
    )
    assert missing == []


def test_seed_uses_the_given_password_hash_and_documents_a_valid_demo_passphrase(seeded_db):
    from mission_control.domain.passwords import validate_password

    assert rows(seeded_db, "SELECT DISTINCT password_hash FROM users") == [("test-hash",)]
    validate_password(DEMO_PASSWORD)


def test_loading_the_seed_twice_is_refused(seeded_db):
    with pytest.raises(RuntimeError, match="not empty"):
        load_seed(seeded_db, password_hash="x")


def test_seed_loads_in_one_transaction(conn, monkeypatch):
    # If loading fails part-way, nothing is left behind.
    from mission_control.seed import loader

    monkeypatch.setattr(loader, "_load_helix", lambda *a, **k: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        load_seed(conn, password_hash="x")
    assert one(conn, "SELECT count(*) FROM organisations") == 0


# Regression: the seeded audit trail is in the order the events would really have happened


def audit_trail(conn, mission):
    return rows(
        conn,
        """
        SELECT e.event, u.name, e.from_status, e.to_status FROM audit_events e
        JOIN missions m ON m.id = e.mission_id JOIN users u ON u.id = e.actor_id
        WHERE m.name = ? ORDER BY e.id""",
        mission,
    )


def test_active_mission_trail_is_created_submitted_approved_then_activated(seeded_db):
    assert audit_trail(seeded_db, "Orbital Telescope Service") == [
        ("mission.created", "Lee Park", None, "draft"),
        ("mission.submitted", "Lee Park", "draft", "pending_approval"),
        ("mission.approved", "Marco Bianchi", None, None),
        ("mission.approved", "Ingrid Holm", None, None),
        ("mission.activated", "Ingrid Holm", "pending_approval", "active"),
    ]


def test_pending_mission_trail_has_its_partial_approval_after_submission(seeded_db):
    assert audit_trail(seeded_db, "Deep Space Comms Upgrade") == [
        ("mission.created", "Nora Quinn", None, "draft"),
        ("mission.submitted", "Nora Quinn", "draft", "pending_approval"),
        ("mission.approved", "Marco Bianchi", None, None),
    ]


def test_completed_mission_trail_ends_with_completion_by_its_owner(seeded_db):
    assert audit_trail(seeded_db, "Mars Analog Habitat") == [
        ("mission.created", "Lee Park", None, "draft"),
        ("mission.submitted", "Lee Park", "draft", "pending_approval"),
        ("mission.approved", "Marco Bianchi", None, None),
        ("mission.approved", "Ingrid Holm", None, None),
        ("mission.activated", "Ingrid Holm", "pending_approval", "active"),
        ("mission.completed", "Lee Park", "active", "completed"),
    ]


def test_draft_mission_trail_records_its_creator(seeded_db):
    assert audit_trail(seeded_db, "Lunar Gateway Resupply") == [
        ("mission.created", "Ruth Adeyemi", None, "draft"),
    ]


def test_no_mission_is_approved_before_it_is_submitted(seeded_db):
    out_of_order = rows(
        seeded_db,
        """
        SELECT m.name FROM missions m
        WHERE EXISTS (SELECT 1 FROM audit_events a WHERE a.mission_id = m.id
                      AND a.event = 'mission.approved'
                      AND a.id < (SELECT min(s.id) FROM audit_events s
                                  WHERE s.mission_id = m.id AND s.event = 'mission.submitted'))""",
    )
    assert out_of_order == []
