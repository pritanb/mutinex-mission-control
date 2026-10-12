"""Turning what the user types into what the API expects. Missions and assignments are IDs;
people are found by email, skills by name and slots by name or position. Also parses the
`--slot` spec, e.g. `Commander:1:Piloting>=4,Leadership>=3`.

Only syntax is checked here. Whether a headcount or level is allowed is the server's call."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from mission_control.cli.client import Api
from mission_control.cli.errors import Refused, UsageProblem

SLOT_FORMAT = "NAME:HEADCOUNT:SKILL>=LEVEL[,SKILL>=LEVEL...]"
SLOT_EXAMPLE = "Commander:1:Piloting>=4,Leadership>=3"
REQUIREMENTS_FORMAT = "SKILL>=LEVEL[,SKILL>=LEVEL...]"


class SpecError(UsageProblem):
    pass


@dataclass(frozen=True)
class SlotSpec:
    name: str
    headcount: int
    requirements: tuple[tuple[str, int], ...]  # (skill name, minimum level), as typed


def parse_slot_spec(text: str) -> SlotSpec:
    parts = text.rsplit(":", 2)
    if len(parts) != 3 or not parts[0].strip():
        raise _slot_error(text)
    name, headcount, requirements = (p.strip() for p in parts)
    try:
        count = int(headcount)
    except ValueError:
        raise _slot_error(text) from None
    try:
        parsed = parse_requirements(requirements) if requirements else ()
    except SpecError:
        raise _slot_error(text) from None
    return SlotSpec(name, count, parsed)


def parse_requirements(text: str) -> tuple[tuple[str, int], ...]:
    requirements = []
    for entry in text.split(","):
        skill, sep, level = entry.partition(">=")
        skill, level = skill.strip(), level.strip()
        if not sep or not skill or not level.lstrip("-").isdigit():
            raise SpecError(
                f"'{entry.strip()}' isn't a requirement. Use {REQUIREMENTS_FORMAT}, "
                "e.g. Piloting>=4,Leadership>=3."
            )
        requirements.append((skill, int(level)))
    return tuple(requirements)


def _slot_error(text: str) -> SpecError:
    return SpecError(f"'{text}' isn't a slot. Use {SLOT_FORMAT}, e.g. {SLOT_EXAMPLE}.")


# References


def skill_ids(api: Api, names: Sequence[str]) -> dict[str, int]:
    """Skill names (any case) to IDs, from the organisation's catalogue."""
    catalogue = _catalogue(api)
    return {name: _skill_in(catalogue, name)["id"] for name in names}


def skill_named(api: Api, name: str) -> dict[str, Any]:
    """A skill from the organisation's catalogue, by name in any case."""
    return _skill_in(_catalogue(api), name)


def _catalogue(api: Api) -> dict[str, dict[str, Any]]:
    """The organisation's skills by name, ignoring case. Names are unique ignoring case."""
    return {s["name"].casefold(): s for s in api.get("/skills")}


def _skill_in(catalogue: Mapping[str, dict[str, Any]], name: str) -> dict[str, Any]:
    skill = catalogue.get(name.casefold())
    if skill is None:
        raise Refused(f"There's no skill called '{name}'", hint="See the skills: mc skills list")
    return skill


def requirement_body(
    requirements: Sequence[tuple[str, int]], ids: Mapping[str, int]
) -> list[dict[str, int]]:
    return [{"skill_id": ids[name], "min_level": level} for name, level in requirements]


def crew_by_email(api: Api, email: str) -> dict[str, Any]:
    for person in api.get("/crew"):
        if person["email"].casefold() == email.strip().casefold():
            return person
    raise Refused(
        f"There's no crew member with the email {email}", hint="See the crew: mc crew list"
    )


def user_by_email(api: Api, email: str) -> dict[str, Any]:
    for user in api.get("/users"):
        if user["email"].casefold() == email.strip().casefold():
            return user
    raise Refused(f"There's no user with the email {email}", hint="See the users: mc users list")


def slot_in(mission: Mapping[str, Any], ref: str) -> dict[str, Any]:
    """A live slot by position (`2`) or by name, ignoring case (`Flight Engineer`)."""
    slots = mission["slots"]
    ref = ref.strip()
    if ref.isdigit():
        match = [s for s in slots if s["position"] == int(ref)]
        missing = f"{mission['name']} has no slot {ref}"
    else:
        match = [s for s in slots if s["name"].casefold() == ref.casefold()]
        missing = f"{mission['name']} has no slot called '{ref}'"
    if not match:
        listed = ", ".join(f"{s['position']} {s['name']}" for s in slots)
        raise Refused(missing, hint=f"Its slots: {listed}")
    return match[0]
