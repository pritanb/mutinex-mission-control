"""Small builders and PRD §9.1 Aurora seed records for focused domain tests.

Builders only fill in defaults. Records are frozen dataclasses, so the module-level
constants below can be shared between tests. Build variations with the builders or
`dataclasses.replace`, never by mutating a constant.
"""

from collections.abc import Iterable, Mapping
from datetime import date
from types import MappingProxyType

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus
from mission_control.domain.records import (
    CandidateFacts,
    Commitment,
    Requirement,
    RosterEntry,
    SlotSpec,
)

# --- Dates --------------------------------------------------------------------------------


def date_range(start: str, end: str) -> DateRange:
    """A DateRange from two ISO dates, both inclusive."""
    return DateRange(date.fromisoformat(start), date.fromisoformat(end))


# --- Aurora skill catalogue (PRD §9.1) ----------------------------------------------------

PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, FLIGHT_MEDICINE = 1, 2, 3, 4, 5, 6
SKILL_NAMES: Mapping[int, str] = MappingProxyType(
    {
        PILOTING: "Piloting",
        LEADERSHIP: "Leadership",
        SYS_ENG: "Systems Eng",
        EVA: "EVA",
        GEOLOGY: "Geology",
        FLIGHT_MEDICINE: "Flight Medicine",
    }
)


# --- Record builders ----------------------------------------------------------------------


def req(skill_id: int, min_level: int) -> Requirement:
    return Requirement(skill_id, SKILL_NAMES[skill_id], min_level)


def slot(
    *requirements: Requirement,
    id: int = 10,
    position: int = 1,
    name: str = "Commander",
    open_places: int = 1,
) -> SlotSpec:
    return SlotSpec(
        id=id,
        position=position,
        name=name,
        open_places=open_places,
        requirements=tuple(requirements),
    )


def crew(
    name: str = "Test Crew",
    id: int = 1,
    active: bool = True,
    skills: Mapping[int, int] | None = None,
    unavailable: Iterable[DateRange] = (),
    accepted_elsewhere: Iterable[Commitment] = (),
    workload: int = 0,
) -> CandidateFacts:
    return CandidateFacts(
        crew_profile_id=id,
        name=name,
        active=active,
        skills=skills or {},
        unavailable=tuple(unavailable),
        accepted_elsewhere=tuple(accepted_elsewhere),
        workload=workload,
    )


def commitment(mission_id: int, mission_name: str, start: str, end: str) -> Commitment:
    return Commitment(mission_id, mission_name, date_range(start, end))


def roster_entry(
    crew: CandidateFacts,
    slot: SlotSpec,
    id: int = 100,
    status: AssignmentStatus = AssignmentStatus.ACCEPTED,
) -> RosterEntry:
    return RosterEntry(assignment_id=id, slot=slot, crew=crew, status=status)


# --- Aurora seed crew (PRD §9.1) ----------------------------------------------------------

STATION_REBOOST = commitment(3, "Station Reboost", "2027-02-25", "2027-03-02")

# IDs follow the PRD §9 table order (the stable identifier used for the last tie-break).
ANA = crew("Ana", 6, skills={PILOTING: 5, LEADERSHIP: 4, SYS_ENG: 4}, workload=0)
BEN = crew("Ben", 7, skills={SYS_ENG: 4, EVA: 3}, workload=20)
CHEN = crew("Chen", 8, skills={SYS_ENG: 3}, workload=5)
DANA = crew("Dana", 9, skills={EVA: 4}, workload=5)
ELI = crew("Eli", 10, skills={EVA: 4, PILOTING: 4, LEADERSHIP: 2}, workload=5)
FAY = crew(
    "Fay",
    11,
    skills={PILOTING: 4, LEADERSHIP: 4},
    unavailable=[date_range("2027-03-05", "2027-03-08")],
)
GUS = crew("Gus", 12, skills={SYS_ENG: 5}, workload=6, accepted_elsewhere=[STATION_REBOOST])
HANA = crew("Hana", 13, skills={EVA: 3, GEOLOGY: 2}, workload=5)
AURORA_CREW = (ANA, BEN, CHEN, DANA, ELI, FAY, GUS, HANA)

# --- Aurora seed missions (PRD §9.1) ------------------------------------------------------

# Lunar Gateway Resupply, 1–10 Mar 2027. Slots listed Flight Engineer first, as in the PRD.
GATEWAY_WINDOW = date_range("2027-03-01", "2027-03-10")
FLIGHT_ENGINEER = slot(req(SYS_ENG, 3), id=21, position=1, name="Flight Engineer")
SPECIALIST = slot(req(EVA, 3), id=22, position=2, name="Mission Specialist")
COMMANDER = slot(req(PILOTING, 4), req(LEADERSHIP, 3), id=23, position=3, name="Commander")
GATEWAY_SLOTS = (FLIGHT_ENGINEER, SPECIALIST, COMMANDER)

# Asteroid Survey, 5–12 Mar 2027.
ASTEROID_WINDOW = date_range("2027-03-05", "2027-03-12")
PILOT = slot(req(PILOTING, 4), id=31, position=1, name="Pilot")
GEOLOGIST = slot(req(GEOLOGY, 4), id=32, position=2, name="Geologist")
ASTEROID_SLOTS = (PILOT, GEOLOGIST)
