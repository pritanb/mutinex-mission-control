"""Demo data for two organisations. Shared by `mc-admin seed` and the tests.

Ids are fixed and follow the people and mission tables in the PRD, so a crew profile's id
equals its user's id. The matcher's final tie-break is the crew profile id.
"""

DEMO_PASSWORD = "orbital launch window"  # every seeded user; at least 15 characters

ORGANISATIONS = [
    # id, name, slug, required approvals
    (1, "Aurora Space Agency", "aurora", 2),
    (2, "Helix Orbital", "helix", 1),
]

USERS = [
    # id, org, name, role, has crew profile
    (1, 1, "Ruth Adeyemi", "director", False),
    (2, 1, "Marco Bianchi", "director", True),
    (3, 1, "Ingrid Holm", "director", False),
    (4, 1, "Lee Park", "lead", False),
    (5, 1, "Nora Quinn", "lead", False),
    (6, 1, "Ana Okafor", "lead", True),
    (7, 1, "Ben Ito", "crew", True),
    (8, 1, "Chen Wu", "crew", True),
    (9, 1, "Dana Reyes", "crew", True),
    (10, 1, "Eli Novak", "crew", True),
    (11, 1, "Fay Moreau", "crew", True),
    (12, 1, "Gus Patel", "crew", True),
    (13, 1, "Hana Sato", "crew", True),
    (14, 2, "Sam Rivera", "director", False),
    (15, 2, "Priya Nair", "lead", False),
    (16, 2, "Kai Tanaka", "crew", True),
    (17, 2, "Lena Fischer", "crew", True),
    (18, 2, "Omar Haddad", "crew", True),
    (19, 2, "Tess Moreno", "crew", True),
]

SKILLS = [
    # id, org, name
    (1, 1, "Piloting"),
    (2, 1, "Leadership"),
    (3, 1, "Systems Engineering"),
    (4, 1, "EVA"),
    (5, 1, "Geology"),
    (6, 1, "Flight Medicine"),
    (7, 2, "Piloting"),
    (8, 2, "Payload Integration"),
    (9, 2, "Life Support"),
    (10, 2, "Field Medicine"),
]

CREW_SKILLS = {
    # crew profile (= user) id: {skill id: level}
    2: {6: 4},
    6: {1: 5, 2: 4, 3: 4},
    7: {3: 4, 4: 3},
    8: {3: 3},
    9: {4: 4},
    10: {4: 4, 1: 4, 2: 2},
    11: {1: 4, 2: 4},
    12: {3: 5},
    13: {4: 3, 5: 2},
    16: {7: 5},
    17: {8: 4},
    18: {10: 4},
    19: {9: 3},
}

UNAVAILABILITY = [
    # crew profile, start, end, reason
    (11, "2027-03-05", "2027-03-08", "Medical"),
]

# Each mission: id, org, name, owner, creator, start, end, status, approvals (director ids,
# round 1), and slots as (name, headcount, {skill id: min level}, [(crew id, status)]).
MISSIONS = [
    (
        1,
        1,
        "Lunar Gateway Resupply",
        4,
        1,
        "2027-03-01",
        "2027-03-10",
        "draft",
        [],
        [
            ("Flight Engineer", 1, {3: 3}, []),
            ("Mission Specialist", 1, {4: 3}, []),
            ("Commander", 1, {1: 4, 2: 3}, []),
        ],
    ),
    (
        2,
        1,
        "Asteroid Survey",
        5,
        5,
        "2027-03-05",
        "2027-03-12",
        "draft",
        [],
        [
            ("Pilot", 1, {1: 4}, []),
            ("Geologist", 1, {5: 4}, []),
        ],
    ),
    (
        3,
        1,
        "Station Reboost",
        5,
        5,
        "2027-02-25",
        "2027-03-02",
        "draft",
        [],
        [
            ("Engineer", 2, {3: 3}, [(12, "accepted")]),
        ],
    ),
    (
        4,
        1,
        "Lunar Surface Medical Study",
        5,
        1,
        "2027-03-15",
        "2027-03-18",
        "draft",
        [],
        [
            ("Flight Surgeon", 1, {6: 4}, [(2, "accepted")]),
        ],
    ),
    (
        5,
        1,
        "Orbital Telescope Service",
        4,
        4,
        "2027-01-10",
        "2027-01-14",
        "active",
        [2, 3],
        [
            ("Engineer", 1, {3: 3}, [(8, "accepted")]),
            ("EVA Specialist", 3, {4: 3}, [(9, "accepted"), (10, "accepted"), (13, "accepted")]),
        ],
    ),
    (
        6,
        1,
        "Deep Space Comms Upgrade",
        5,
        5,
        "2027-04-01",
        "2027-04-20",
        "pending_approval",
        [2],
        [
            ("Engineer", 1, {3: 3}, [(7, "accepted")]),
        ],
    ),
    (
        7,
        1,
        "Mars Analog Habitat",
        4,
        4,
        "2026-05-01",
        "2026-05-30",
        "completed",
        [2, 3],
        [
            ("Engineer", 1, {3: 3}, [(8, "completed")]),
        ],
    ),
    (
        8,
        2,
        "Payload Demo 1",
        15,
        15,
        "2027-02-01",
        "2027-02-03",
        "draft",
        [],
        [
            ("Payload Specialist", 1, {8: 3}, [(17, "accepted")]),
            ("Medic", 1, {10: 3}, [(18, "accepted")]),
        ],
    ),
]
