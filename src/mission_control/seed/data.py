"""Demo data for two organisations. Shared by `mc-admin seed` and the tests.

Ids are fixed, and a crew profile's id equals its user's id, so the demo and the tests can name
people and missions by number. The matcher's final tie-break is the crew profile id.
"""

from collections.abc import Mapping
from types import MappingProxyType as _ro
from typing import NamedTuple

DEMO_PASSWORD = "orbital launch window"  # every seeded user; at least 15 characters


class Organisation(NamedTuple):
    id: int
    name: str
    slug: str
    required_approvals: int


class User(NamedTuple):
    id: int
    org_id: int
    name: str
    role: str
    has_crew_profile: bool


class Skill(NamedTuple):
    id: int
    org_id: int
    name: str


class Unavailability(NamedTuple):
    crew_id: int
    start: str
    end: str
    reason: str


class Slot(NamedTuple):
    name: str
    headcount: int
    requirements: Mapping[int, int]  # skill id: min level
    crew: tuple[tuple[int, str], ...]  # (crew id, assignment status)


class Mission(NamedTuple):
    id: int
    org_id: int
    name: str
    owner_id: int
    creator_id: int
    start: str
    end: str
    status: str
    approvers: tuple[int, ...]  # director ids, round 1
    slots: tuple[Slot, ...]


ORGANISATIONS = (
    Organisation(1, "Aurora Space Agency", "aurora", 2),
    Organisation(2, "Helix Orbital", "helix", 1),
)

USERS = (
    # id, org, name, role, has crew profile
    User(1, 1, "Ruth Adeyemi", "director", False),
    User(2, 1, "Marco Bianchi", "director", True),
    User(3, 1, "Ingrid Holm", "director", False),
    User(4, 1, "Lee Park", "lead", False),
    User(5, 1, "Nora Quinn", "lead", False),
    User(6, 1, "Ana Okafor", "lead", True),
    User(7, 1, "Ben Ito", "crew", True),
    User(8, 1, "Chen Wu", "crew", True),
    User(9, 1, "Dana Reyes", "crew", True),
    User(10, 1, "Eli Novak", "crew", True),
    User(11, 1, "Fay Moreau", "crew", True),
    User(12, 1, "Gus Patel", "crew", True),
    User(13, 1, "Hana Sato", "crew", True),
    User(14, 2, "Sam Rivera", "director", False),
    User(15, 2, "Priya Nair", "lead", False),
    User(16, 2, "Kai Tanaka", "crew", True),
    User(17, 2, "Lena Fischer", "crew", True),
    User(18, 2, "Omar Haddad", "crew", True),
    User(19, 2, "Tess Moreno", "crew", True),
)

SKILLS = (
    # id, org, name
    Skill(1, 1, "Piloting"),
    Skill(2, 1, "Leadership"),
    Skill(3, 1, "Systems Engineering"),
    Skill(4, 1, "EVA"),
    Skill(5, 1, "Geology"),
    Skill(6, 1, "Flight Medicine"),
    Skill(7, 2, "Piloting"),
    Skill(8, 2, "Payload Integration"),
    Skill(9, 2, "Life Support"),
    Skill(10, 2, "Field Medicine"),
)

CREW_SKILLS = _ro(
    {
        # crew profile (= user) id: {skill id: level}
        2: _ro({6: 4}),
        6: _ro({1: 5, 2: 4, 3: 4}),
        7: _ro({3: 4, 4: 3}),
        8: _ro({3: 3}),
        9: _ro({4: 4}),
        10: _ro({4: 4, 1: 4, 2: 2}),
        11: _ro({1: 4, 2: 4}),
        12: _ro({3: 5}),
        13: _ro({4: 3, 5: 2}),
        16: _ro({7: 5}),
        17: _ro({8: 4}),
        18: _ro({10: 4}),
        19: _ro({9: 3}),
    }
)

UNAVAILABILITY = (Unavailability(11, "2027-03-05", "2027-03-08", "Medical"),)

# Each mission: id, org, name, owner, creator, start, end, status, approvals (director ids,
# round 1), and slots with their requirements and (crew id, assignment status) pairs.
MISSIONS = (
    Mission(
        1,
        1,
        "Lunar Gateway Resupply",
        4,
        1,
        "2027-03-01",
        "2027-03-10",
        "draft",
        (),
        (
            Slot("Flight Engineer", 1, _ro({3: 3}), ()),
            Slot("Mission Specialist", 1, _ro({4: 3}), ()),
            Slot("Commander", 1, _ro({1: 4, 2: 3}), ()),
        ),
    ),
    Mission(
        2,
        1,
        "Asteroid Survey",
        5,
        5,
        "2027-03-05",
        "2027-03-12",
        "draft",
        (),
        (
            Slot("Pilot", 1, _ro({1: 4}), ()),
            Slot("Geologist", 1, _ro({5: 4}), ()),
        ),
    ),
    Mission(
        3,
        1,
        "Station Reboost",
        5,
        5,
        "2027-02-25",
        "2027-03-02",
        "draft",
        (),
        (Slot("Engineer", 2, _ro({3: 3}), ((12, "accepted"),)),),
    ),
    Mission(
        4,
        1,
        "Lunar Surface Medical Study",
        5,
        1,
        "2027-03-15",
        "2027-03-18",
        "draft",
        (),
        (Slot("Flight Surgeon", 1, _ro({6: 4}), ((2, "accepted"),)),),
    ),
    Mission(
        5,
        1,
        "Orbital Telescope Service",
        4,
        4,
        "2027-01-10",
        "2027-01-14",
        "active",
        (2, 3),
        (
            Slot("Engineer", 1, _ro({3: 3}), ((8, "accepted"),)),
            Slot(
                "EVA Specialist",
                3,
                _ro({4: 3}),
                ((9, "accepted"), (10, "accepted"), (13, "accepted")),
            ),
        ),
    ),
    Mission(
        6,
        1,
        "Deep Space Comms Upgrade",
        5,
        5,
        "2027-04-01",
        "2027-04-20",
        "pending_approval",
        (2,),
        (Slot("Engineer", 1, _ro({3: 3}), ((7, "accepted"),)),),
    ),
    Mission(
        7,
        1,
        "Mars Analog Habitat",
        4,
        4,
        "2026-05-01",
        "2026-05-30",
        "completed",
        (2, 3),
        (Slot("Engineer", 1, _ro({3: 3}), ((8, "completed"),)),),
    ),
    Mission(
        8,
        2,
        "Payload Demo 1",
        15,
        15,
        "2027-02-01",
        "2027-02-03",
        "draft",
        (),
        (
            Slot("Payload Specialist", 1, _ro({8: 3}), ((17, "accepted"),)),
            Slot("Medic", 1, _ro({10: 3}), ((18, "accepted"),)),
        ),
    ),
)
