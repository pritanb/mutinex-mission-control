"""Load the demo data into an empty database, in one transaction.

Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them.
"""

import sqlite3

from mission_control.domain.events import Event
from mission_control.infra.db import write_tx
from mission_control.infra.repositories import Repos
from mission_control.seed import data


def load_seed(conn: sqlite3.Connection, password_hash: str) -> None:
    """`password_hash` is stored for every user; the caller hashes `data.DEMO_PASSWORD`."""
    with write_tx(conn):
        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:
            raise RuntimeError("the database is not empty; reset it before seeding")
        for org in data.ORGANISATIONS:
            _load_org(conn, org, password_hash)


def _load_org(conn: sqlite3.Connection, org: data.Organisation, password_hash: str) -> None:
    q = conn.execute
    q(
        "INSERT INTO organisations(id, name, slug, required_approvals) VALUES (?, ?, ?, ?)",
        (org.id, org.name, org.slug, org.required_approvals),
    )

    users = [u for u in data.USERS if u.org_id == org.id]
    for user in users:
        email = f"{user.name.split()[0].lower()}@{org.slug}.example"
        q(
            "INSERT INTO users(id, org_id, email, name, role, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, org.id, email, user.name, user.role, password_hash),
        )
    for user in users:
        if user.has_crew_profile:
            q(
                "INSERT INTO crew_profiles(id, org_id, user_id, display_name) VALUES (?, ?, ?, ?)",
                (user.id, org.id, user.id, user.name.split()[0]),
            )

    for skill in data.SKILLS:
        if skill.org_id == org.id:
            q(
                "INSERT INTO skills(id, org_id, name) VALUES (?, ?, ?)",
                (skill.id, org.id, skill.name),
            )

    director = next(u.id for u in users if u.role == "director")
    profile_ids = {u.id for u in users if u.has_crew_profile}
    for crew_id, levels in data.CREW_SKILLS.items():
        if crew_id in profile_ids:
            for skill_id, level in levels.items():
                q(
                    "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
                    " updated_by_id) VALUES (?, ?, ?, ?, ?)",
                    (org.id, crew_id, skill_id, level, director),
                )

    for absence in data.UNAVAILABILITY:
        if absence.crew_id in profile_ids:
            q(
                "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
                " VALUES (?, ?, ?, ?, ?)",
                (org.id, absence.crew_id, absence.start, absence.end, absence.reason),
            )

    for mission in data.MISSIONS:
        if mission.org_id == org.id:
            _load_mission(conn, org, mission)


def _load_mission(conn: sqlite3.Connection, org: data.Organisation, m: data.Mission) -> None:
    q = conn.execute
    audit = Repos(conn, org.id).audit
    seeded = {"mission_name": m.name, "seeded": True}
    submitted = m.status != "draft"
    q(
        "INSERT INTO missions(id, org_id, name, start_date, end_date, status, owner_id,"
        " created_by_id, approval_round, approvals_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            m.id,
            org.id,
            m.name,
            m.start,
            m.end,
            m.status,
            m.owner_id,
            m.creator_id,
            1 if submitted else 0,
            org.required_approvals if submitted else None,
        ),
    )
    audit.record(
        m.creator_id, Event.MISSION_CREATED, mission_id=m.id, to_status="draft", data=seeded
    )

    for position, slot in enumerate(m.slots, start=1):
        slot_id = q(
            "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
            " VALUES (?, ?, ?, ?, ?)",
            (org.id, m.id, slot.name, slot.headcount, position),
        ).lastrowid
        for skill_id, min_level in slot.requirements.items():
            q(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (?, ?, ?, ?)",
                (org.id, slot_id, skill_id, min_level),
            )
        for crew_id, assignment_status in slot.crew:
            q(
                "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
                " proposed_by_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                (org.id, m.id, slot_id, crew_id, m.owner_id, assignment_status),
            )

    # Audit events in the order they would really have happened: submit, each approval, then
    # activation (made by the final approval) and completion (by the owner).
    if submitted:
        audit.record(
            m.owner_id,
            Event.MISSION_SUBMITTED,
            mission_id=m.id,
            from_status="draft",
            to_status="pending_approval",
            data=seeded,
        )
    for director_id in m.approvers:
        q(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
            " VALUES (?, ?, 1, ?, 'approve')",
            (org.id, m.id, director_id),
        )
        audit.record(director_id, Event.MISSION_APPROVED, mission_id=m.id, data=seeded)
    if m.status in ("active", "completed"):
        audit.record(
            m.approvers[-1],
            Event.MISSION_ACTIVATED,
            mission_id=m.id,
            from_status="pending_approval",
            to_status="active",
            data=seeded,
        )
    if m.status == "completed":
        audit.record(
            m.owner_id,
            Event.MISSION_COMPLETED,
            mission_id=m.id,
            from_status="active",
            to_status="completed",
            data=seeded,
        )
