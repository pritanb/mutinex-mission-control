"""How API records read on screen, shared by the command groups."""

from collections.abc import Mapping, Sequence
from typing import Any

from mission_control.cli.render import MISSION_STATUS, ROLE, Terminal


def mission_status(mission: Mapping[str, Any]) -> str:
    return MISSION_STATUS.get(mission["status"], mission["status"])


def mission_heading(term: Terminal, mission: Mapping[str, Any]) -> str:
    """`Lunar Gateway Resupply · 1–10 Mar 2027 · Draft`."""
    dates = term.dates(mission["start_date"], mission["end_date"])
    return term.heading(mission["name"], dates, mission_status(mission))


def mission_row(term: Terminal, mission: Mapping[str, Any]) -> list[str]:
    return [
        str(mission["id"]),
        mission["name"],
        term.dates(mission["start_date"], mission["end_date"]),
        mission_status(mission),
    ]


def org_name(me: Mapping[str, Any]) -> str | None:
    org = me.get("organisation")
    return org.get("name") if isinstance(org, Mapping) else None


def identity(me: Mapping[str, Any], name: str | None = None) -> list[tuple[str, str]]:
    pairs = [
        ("Name", name or me["name"]),
        ("Email", me["email"]),
        ("Role", ROLE.get(me["role"], me["role"])),
    ]
    if org := org_name(me):
        pairs.append(("Organisation", org))
    return pairs


def requirements_text(requirements: Sequence[Mapping[str, Any]]) -> str:
    """`Piloting>=4, Leadership>=3`, the same form `--slot` takes."""
    return ", ".join(f"{r['skill_name']}>={r['min_level']}" for r in requirements)


def skills_text(skills: Sequence[Mapping[str, Any]]) -> str:
    return ", ".join(f"{s['skill_name']} {s['level']}" for s in skills)


def assignment_summary_rows(term: Terminal, rows: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    return [
        [
            str(a["assignment_id"]),
            a["mission_name"],
            a["slot_name"],
            term.dates(a["start_date"], a["end_date"]),
            a["status"],
        ]
        for a in rows
    ]


def show_profile(
    term: Terminal,
    pairs: list[tuple[str, str]],
    profile: Mapping[str, Any],
    *,
    own: bool,
) -> None:
    """A crew profile: details, skills, and unavailability. Reasons appear only when the
    server sent them; IDs only on your own, since you need them to remove an entry."""
    term.fields(pairs + [("Bio", profile.get("bio") or "none")])
    term.line()
    skills = profile.get("skills") or []
    if skills:
        term.table(["Skill", "Level"], [[s["skill_name"], str(s["level"])] for s in skills])
    else:
        term.line("No skills recorded yet.")
    term.line()
    unavailable = profile.get("unavailability") or []
    if not unavailable:
        term.line("No unavailability recorded.")
        return
    with_reasons = any(u.get("reason") for u in unavailable)
    headers = (["ID"] if own else []) + ["Unavailable"] + (["Reason"] if with_reasons else [])
    rows = []
    for u in unavailable:
        row = ([str(u["id"])] if own else []) + [term.dates(u["start_date"], u["end_date"])]
        rows.append(row + ([u.get("reason") or ""] if with_reasons else []))
    term.table(headers, rows)
