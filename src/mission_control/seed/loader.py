"""Load the demo data into an empty database, in one transaction.

Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them.
"""

import json
import sqlite3

from mission_control.infra.db import write_tx
from mission_control.seed import data


def load_seed(conn: sqlite3.Connection, password_hash: str) -> None:
    """`password_hash` is stored for every user; the caller hashes `data.DEMO_PASSWORD`."""
    with write_tx(conn):
        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:
            raise RuntimeError("the database is not empty; reset it before seeding")
        _load_aurora(conn, password_hash)
        _load_helix(conn, password_hash)


def _load_aurora(conn: sqlite3.Connection, password_hash: str) -> None:
    _load_org(conn, 1, password_hash)


def _load_helix(conn: sqlite3.Connection, password_hash: str) -> None:
    _load_org(conn, 2, password_hash)


def _load_org(conn: sqlite3.Connection, org: int, password_hash: str) -> None:
    q = conn.execute
    for org_id, name, slug, required in data.ORGANISATIONS:
        if org_id == org:
            q(
                "INSERT INTO organisations(id, name, slug, required_approvals) VALUES (?, ?, ?, ?)",
                (org_id, name, slug, required),
            )

    users = [u for u in data.USERS if u[1] == org]
    for user_id, _, name, role, _ in users:
        email = f"{name.split()[0].lower()}@{_slug(org)}.example"
        q(
            "INSERT INTO users(id, org_id, email, name, role, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, org, email, name, role, password_hash),
        )
    for user_id, _, name, _, has_profile in users:
        if has_profile:
            q(
                "INSERT INTO crew_profiles(id, org_id, user_id, display_name) VALUES (?, ?, ?, ?)",
                (user_id, org, user_id, name.split()[0]),
            )

    for skill_id, skill_org, name in data.SKILLS:
        if skill_org == org:
            q("INSERT INTO skills(id, org_id, name) VALUES (?, ?, ?)", (skill_id, org, name))

    director = next(u[0] for u in users if u[3] == "director")
    profile_ids = {u[0] for u in users if u[4]}
    for crew_id, levels in data.CREW_SKILLS.items():
        if crew_id in profile_ids:
            for skill_id, level in levels.items():
                q(
                    "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
                    " updated_by_id) VALUES (?, ?, ?, ?, ?)",
                    (org, crew_id, skill_id, level, director),
                )

    for crew_id, start, end, reason in data.UNAVAILABILITY:
        if crew_id in profile_ids:
            q(
                "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
                " VALUES (?, ?, ?, ?, ?)",
                (org, crew_id, start, end, reason),
            )

    for mission in data.MISSIONS:
        if mission[1] == org:
            _load_mission(conn, *mission)


def _load_mission(
    conn, mission_id, org, name, owner, creator, start, end, status, approvers, slots
) -> None:
    q = conn.execute
    submitted = status != "draft"
    required = data.ORGANISATIONS[org - 1][3] if submitted else None
    q(
        "INSERT INTO missions(id, org_id, name, start_date, end_date, status, owner_id,"
        " created_by_id, approval_round, approvals_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            mission_id,
            org,
            name,
            start,
            end,
            status,
            owner,
            creator,
            1 if submitted else 0,
            required,
        ),
    )
    _audit(conn, org, creator, "mission.created", mission_id, None, "draft", name)

    for position, (slot_name, headcount, requirements, crew) in enumerate(slots, start=1):
        slot_id = q(
            "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
            " VALUES (?, ?, ?, ?, ?)",
            (org, mission_id, slot_name, headcount, position),
        ).lastrowid
        for skill_id, min_level in requirements.items():
            q(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (?, ?, ?, ?)",
                (org, slot_id, skill_id, min_level),
            )
        for crew_id, assignment_status in crew:
            q(
                "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
                " proposed_by_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                (org, mission_id, slot_id, crew_id, owner, assignment_status),
            )

    # Audit events in the order they would really have happened: submit, each approval, then
    # activation (made by the final approval) and completion (by the owner).
    if submitted:
        _audit(conn, org, owner, "mission.submitted", mission_id, "draft", "pending_approval", name)
    for director_id in approvers:
        q(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
            " VALUES (?, ?, 1, ?, 'approve')",
            (org, mission_id, director_id),
        )
        _audit(conn, org, director_id, "mission.approved", mission_id, None, None, name)
    if status in ("active", "completed"):
        _audit(
            conn,
            org,
            approvers[-1],
            "mission.activated",
            mission_id,
            "pending_approval",
            "active",
            name,
        )
    if status == "completed":
        _audit(conn, org, owner, "mission.completed", mission_id, "active", "completed", name)


def _audit(conn, org, actor, event, mission_id, before, after, mission_name) -> None:
    conn.execute(
        "INSERT INTO audit_events(org_id, actor_id, event, mission_id, from_status, to_status,"
        " data) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            org,
            actor,
            event,
            mission_id,
            before,
            after,
            json.dumps({"mission_name": mission_name, "seeded": True}),
        ),
    )


def _slug(org: int) -> str:
    return next(slug for org_id, _, slug, _ in data.ORGANISATIONS if org_id == org)
