"""Tenant-scoped data access. All SQL lives here, and every statement filters on org_id.

Parameters are bound by name and the caller's org is always `:org`, so a statement reads
`org_id = :org` wherever the filter sits; placeholder order can't bind another tenant's id.

Build one `Repos(conn, org_id)` per request from the authenticated actor's organisation.
Looking up another organisation's id returns None, exactly like a missing id.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.permissions import Actor
from mission_control.domain.records import Requirement
from mission_control.infra.repositories.base import FINAL, ON_MISSION, OPEN, Scoped, in_list
from mission_control.infra.repositories.base import window as _window
from mission_control.infra.repositories.facts import FactsRepo
from mission_control.infra.repositories.models import (
    Approval,
    Assignment,
    AssignmentSummary,
    CrewProfile,
    Mission,
    Organisation,
    Skill,
    Slot,
    Unavailability,
    User,
)

_NOW = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


class OrganisationRepo(Scoped):
    def get(self) -> Organisation:
        r = self._one("SELECT * FROM organisations WHERE id = :org")
        assert r is not None, "repositories are only built for an existing organisation"
        return Organisation(r["id"], r["name"], r["slug"], r["required_approvals"])

    def set_required_approvals(self, n: int) -> None:
        self._exec("UPDATE organisations SET required_approvals = :n WHERE id = :org", n=n)


class UserRepo(Scoped):
    _COLUMNS = "id, org_id, email, name, role, is_active"

    def get(self, user_id: int) -> User | None:
        r = self._one(
            f"SELECT {self._COLUMNS} FROM users WHERE org_id = :org AND id = :id", id=user_id
        )
        return _user(r) if r else None

    def list(self) -> list[User]:
        rows = self._all(f"SELECT {self._COLUMNS} FROM users WHERE org_id = :org ORDER BY id")
        return [_user(r) for r in rows]

    def create(self, email: str, name: str, role: Role, password_hash: str) -> User:
        cur = self._exec(
            "INSERT INTO users(org_id, email, name, role, password_hash)"
            " VALUES (:org, :email, :name, :role, :password_hash)",
            email=email,
            name=name,
            role=role,
            password_hash=password_hash,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def set_role(self, user_id: int, role: Role) -> bool:
        return (
            self._exec(
                f"UPDATE users SET role = :role, updated_at = {_NOW}"
                " WHERE org_id = :org AND id = :id",
                role=role,
                id=user_id,
            ).rowcount
            == 1
        )

    def set_active(self, user_id: int, active: bool) -> bool:
        return (
            self._exec(
                f"UPDATE users SET is_active = :active, updated_at = {_NOW}"
                " WHERE org_id = :org AND id = :id",
                active=int(active),
                id=user_id,
            ).rowcount
            == 1
        )

    def count_active_directors(self) -> int:
        r = self._one(
            "SELECT count(*) FROM users WHERE org_id = :org AND role = :director AND is_active = 1",
            director=Role.DIRECTOR,
        )
        return r[0]


def _user(r: sqlite3.Row) -> User:
    return User(r["id"], r["org_id"], r["email"], r["name"], Role(r["role"]), bool(r["is_active"]))


class CrewRepo(Scoped):
    def get(self, crew_profile_id: int) -> CrewProfile | None:
        r = self._one(
            "SELECT * FROM crew_profiles WHERE org_id = :org AND id = :id", id=crew_profile_id
        )
        return _crew(r) if r else None

    def by_user(self, user_id: int) -> CrewProfile | None:
        r = self._one(
            "SELECT * FROM crew_profiles WHERE org_id = :org AND user_id = :user_id",
            user_id=user_id,
        )
        return _crew(r) if r else None

    def list(self) -> list[CrewProfile]:
        return [
            _crew(r)
            for r in self._all("SELECT * FROM crew_profiles WHERE org_id = :org ORDER BY id")
        ]

    def skills(self, crew_profile_id: int) -> dict[int, int]:
        rows = self._all(
            "SELECT skill_id, level FROM crew_skills"
            " WHERE org_id = :org AND crew_profile_id = :crew_profile_id",
            crew_profile_id=crew_profile_id,
        )
        return {r["skill_id"]: r["level"] for r in rows}

    def unavailability(self, crew_profile_id: int) -> list[Unavailability]:
        rows = self._all(
            "SELECT * FROM unavailability"
            " WHERE org_id = :org AND crew_profile_id = :crew_profile_id ORDER BY start_date, id",
            crew_profile_id=crew_profile_id,
        )
        return [
            Unavailability(r["id"], r["crew_profile_id"], _window(r), r["reason"]) for r in rows
        ]

    def create(self, user_id: int, display_name: str, bio: str | None = None) -> CrewProfile:
        cur = self._exec(
            "INSERT INTO crew_profiles(org_id, user_id, display_name, bio)"
            " VALUES (:org, :user_id, :display_name, :bio)",
            user_id=user_id,
            display_name=display_name,
            bio=bio,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def update(self, crew_profile_id: int, display_name: str, bio: str | None) -> bool:
        return (
            self._exec(
                f"UPDATE crew_profiles SET display_name = :display_name, bio = :bio,"
                f" updated_at = {_NOW} WHERE org_id = :org AND id = :id",
                display_name=display_name,
                bio=bio,
                id=crew_profile_id,
            ).rowcount
            == 1
        )

    def open_assignments(self, crew_profile_id: int) -> list[Assignment]:
        statuses, params = in_list("s", OPEN)
        rows = self._all(
            f"SELECT * FROM assignments WHERE org_id = :org AND crew_profile_id = :crew_profile_id"
            f" AND status IN ({statuses}) ORDER BY id",
            crew_profile_id=crew_profile_id,
            **params,
        )
        return [_assignment(r) for r in rows]

    def add_unavailability(
        self, crew_profile_id: int, window: DateRange, reason: str
    ) -> Unavailability:
        cur = self._exec(
            "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
            " VALUES (:org, :crew_profile_id, :start, :end, :reason)",
            crew_profile_id=crew_profile_id,
            start=window.start.isoformat(),
            end=window.end.isoformat(),
            reason=reason,
        )
        return Unavailability(cur.lastrowid, crew_profile_id, window, reason)

    def remove_unavailability(self, crew_profile_id: int, unavailability_id: int) -> bool:
        return (
            self._exec(
                "DELETE FROM unavailability WHERE org_id = :org AND id = :id"
                " AND crew_profile_id = :crew_profile_id",
                id=unavailability_id,
                crew_profile_id=crew_profile_id,
            ).rowcount
            == 1
        )

    def set_skill(self, crew_profile_id: int, skill_id: int, level: int, updated_by: int) -> None:
        """Set a skill level, adding it or changing it, and record who set it."""
        self._exec(
            f"""INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level, updated_by_id)
                VALUES (:org, :crew_profile_id, :skill_id, :level, :updated_by)
                ON CONFLICT (crew_profile_id, skill_id) DO UPDATE SET
                level = excluded.level, updated_by_id = excluded.updated_by_id,
                updated_at = {_NOW} WHERE crew_skills.org_id = :org""",
            crew_profile_id=crew_profile_id,
            skill_id=skill_id,
            level=level,
            updated_by=updated_by,
        )

    def remove_skill(self, crew_profile_id: int, skill_id: int) -> bool:
        return (
            self._exec(
                "DELETE FROM crew_skills WHERE org_id = :org AND crew_profile_id = :crew_profile_id"
                " AND skill_id = :skill_id",
                crew_profile_id=crew_profile_id,
                skill_id=skill_id,
            ).rowcount
            == 1
        )

    def history(self, crew_profile_id: int) -> list[AssignmentSummary]:
        """Every assignment the person has held, including ones they've left. Newest first."""
        rows = self._all(
            """SELECT a.id, a.mission_id, m.name AS mission_name, m.start_date, m.end_date,
                      m.status AS mission_status, s.name AS slot_name, a.status, a.reason
               FROM assignments a
               JOIN missions m ON m.org_id = a.org_id AND m.id = a.mission_id
               JOIN slots s ON s.org_id = a.org_id AND s.id = a.slot_id
               WHERE a.org_id = :org AND a.crew_profile_id = :crew_profile_id
               ORDER BY m.start_date DESC, a.id DESC""",
            crew_profile_id=crew_profile_id,
        )
        return [
            AssignmentSummary(
                r["id"],
                r["mission_id"],
                r["mission_name"],
                _window(r),
                MissionStatus(r["mission_status"]),
                r["slot_name"],
                AssignmentStatus(r["status"]),
                r["reason"],
            )
            for r in rows
        ]


def _crew(r: sqlite3.Row) -> CrewProfile:
    return CrewProfile(r["id"], r["org_id"], r["user_id"], r["display_name"], r["bio"])


class SkillRepo(Scoped):
    def get(self, skill_id: int) -> Skill | None:
        r = self._one("SELECT * FROM skills WHERE org_id = :org AND id = :id", id=skill_id)
        return _skill(r) if r else None

    def by_name(self, name: str) -> Skill | None:
        r = self._one(
            "SELECT * FROM skills WHERE org_id = :org AND name = :name COLLATE NOCASE", name=name
        )
        return _skill(r) if r else None

    def list(self) -> list[Skill]:
        return [
            _skill(r)
            for r in self._all(
                "SELECT * FROM skills WHERE org_id = :org ORDER BY name COLLATE NOCASE"
            )
        ]

    def create(self, name: str, category: str | None = None) -> Skill:
        cur = self._exec(
            "INSERT INTO skills(org_id, name, category) VALUES (:org, :name, :category)",
            name=name,
            category=category,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def update(self, skill_id: int, name: str, category: str | None) -> bool:
        """Rename or recategorise. The id stays the same, so levels and requirements follow."""
        return (
            self._exec(
                "UPDATE skills SET name = :name, category = :category"
                " WHERE org_id = :org AND id = :id",
                name=name,
                category=category,
                id=skill_id,
            ).rowcount
            == 1
        )

    def is_in_use(self, skill_id: int) -> bool:
        r = self._one(
            """SELECT EXISTS (SELECT 1 FROM crew_skills WHERE org_id = :org AND skill_id = :id)
                   OR EXISTS (SELECT 1 FROM slot_requirements WHERE org_id = :org
                              AND skill_id = :id)""",
            id=skill_id,
        )
        return bool(r[0])

    def delete(self, skill_id: int) -> bool:
        return (
            self._exec("DELETE FROM skills WHERE org_id = :org AND id = :id", id=skill_id).rowcount
            == 1
        )


def _skill(r: sqlite3.Row) -> Skill:
    return Skill(r["id"], r["org_id"], r["name"], r["category"])


class MissionRepo(Scoped):
    """Missions and their parts.

    Mission visibility for crew is decided here: Directors and Leads see every mission in their
    organisation, while crew see only the missions they're on (see `rostered_user_ids`). A
    mission a crew member isn't on is reported as missing, exactly like an unknown id, so callers
    answer 404. Permissions' VIEW_MISSION is the matching rule for services that have already
    loaded the mission.
    """

    def get(self, mission_id: int) -> Mission | None:
        r = self._one("SELECT * FROM missions WHERE org_id = :org AND id = :id", id=mission_id)
        return _mission(r) if r else None

    def list(self) -> list[Mission]:
        return [
            _mission(r)
            for r in self._all("SELECT * FROM missions WHERE org_id = :org ORDER BY start_date, id")
        ]

    def rostered_user_ids(self, mission_id: int) -> frozenset[int]:
        """User ids of the crew on the mission: those holding an open or completed assignment."""
        statuses, params = in_list("s", ON_MISSION)
        rows = self._all(
            f"""SELECT DISTINCT u.id FROM assignments a
                JOIN crew_profiles c ON c.org_id = a.org_id AND c.id = a.crew_profile_id
                JOIN users u ON u.org_id = c.org_id AND u.id = c.user_id
                WHERE a.org_id = :org AND a.mission_id = :mission_id
                AND a.status IN ({statuses})""",
            mission_id=mission_id,
            **params,
        )
        return frozenset(r["id"] for r in rows)

    def list_visible(self, actor: Actor) -> list[Mission]:
        """Directors and Leads see every mission; crew see only the missions they're on."""
        self._check_actor(actor)
        if actor.role != Role.CREW:
            return self.list()
        if actor.crew_profile_id is None:
            return []
        on_mission, params = _crew_on_mission(actor.crew_profile_id)
        rows = self._all(
            f"SELECT * FROM missions m WHERE m.org_id = :org AND {on_mission}"
            " ORDER BY m.start_date, m.id",
            **params,
        )
        return [_mission(r) for r in rows]

    def get_visible(self, actor: Actor, mission_id: int) -> Mission | None:
        """The mission if the actor may see it; None if it's missing or hidden from them."""
        self._check_actor(actor)
        if actor.role != Role.CREW:
            return self.get(mission_id)
        if actor.crew_profile_id is None:
            return None
        on_mission, params = _crew_on_mission(actor.crew_profile_id)
        r = self._one(
            f"SELECT * FROM missions m WHERE m.org_id = :org AND m.id = :id AND {on_mission}",
            id=mission_id,
            **params,
        )
        return _mission(r) if r else None

    def non_final_owned_by(self, user_id: int) -> list[Mission]:
        finals, params = in_list("f", FINAL)
        rows = self._all(
            f"SELECT * FROM missions WHERE org_id = :org AND owner_id = :owner"
            f" AND status NOT IN ({finals}) ORDER BY start_date, id",
            owner=user_id,
            **params,
        )
        return [_mission(r) for r in rows]

    def create(self, name: str, window: DateRange, owner_id: int, created_by_id: int) -> Mission:
        cur = self._exec(
            "INSERT INTO missions(org_id, name, start_date, end_date, owner_id, created_by_id)"
            " VALUES (:org, :name, :start, :end, :owner, :creator)",
            name=name,
            start=window.start.isoformat(),
            end=window.end.isoformat(),
            owner=owner_id,
            creator=created_by_id,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def update(self, mission_id: int, name: str, window: DateRange) -> bool:
        return (
            self._exec(
                f"UPDATE missions SET name = :name, start_date = :start, end_date = :end,"
                f" updated_at = {_NOW} WHERE org_id = :org AND id = :id",
                name=name,
                start=window.start.isoformat(),
                end=window.end.isoformat(),
                id=mission_id,
            ).rowcount
            == 1
        )

    def set_status(self, mission_id: int, status: MissionStatus) -> bool:
        return (
            self._exec(
                f"UPDATE missions SET status = :status, updated_at = {_NOW}"
                " WHERE org_id = :org AND id = :id",
                status=status,
                id=mission_id,
            ).rowcount
            == 1
        )

    def set_owner(self, mission_id: int, owner_id: int) -> bool:
        return (
            self._exec(
                f"UPDATE missions SET owner_id = :owner, updated_at = {_NOW}"
                " WHERE org_id = :org AND id = :id",
                owner=owner_id,
                id=mission_id,
            ).rowcount
            == 1
        )

    def get_slot(self, slot_id: int) -> Slot | None:
        """A live slot by id, with its requirements."""
        r = self._one(
            "SELECT mission_id FROM slots WHERE org_id = :org AND id = :id AND removed_at IS NULL",
            id=slot_id,
        )
        if r is None:
            return None
        return next(s for s in self.slots(r["mission_id"]) if s.id == slot_id)

    def add_slot(
        self, mission_id: int, name: str, headcount: int, requirements: Mapping[int, int]
    ) -> Slot:
        """Append a slot after the last live one, with its {skill_id: min_level}."""
        cur = self._exec(
            """INSERT INTO slots(org_id, mission_id, name, headcount, position)
               VALUES (:org, :mission_id, :name, :headcount,
                       (SELECT coalesce(max(position), 0) + 1 FROM slots
                        WHERE org_id = :org AND mission_id = :mission_id
                        AND removed_at IS NULL))""",
            mission_id=mission_id,
            name=name,
            headcount=headcount,
        )
        self._insert_requirements(cur.lastrowid, requirements)
        created = self.get_slot(cur.lastrowid)
        assert created is not None
        return created

    def update_slot(self, slot_id: int, name: str, headcount: int) -> bool:
        return (
            self._exec(
                "UPDATE slots SET name = :name, headcount = :headcount"
                " WHERE org_id = :org AND id = :id AND removed_at IS NULL",
                name=name,
                headcount=headcount,
                id=slot_id,
            ).rowcount
            == 1
        )

    def replace_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> bool:
        if self.get_slot(slot_id) is None:
            return False
        self._exec(
            "DELETE FROM slot_requirements WHERE org_id = :org AND slot_id = :slot_id",
            slot_id=slot_id,
        )
        self._insert_requirements(slot_id, requirements)
        return True

    def _insert_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> None:
        for skill_id, min_level in requirements.items():
            self._exec(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (:org, :slot_id, :skill_id, :min_level)",
                slot_id=slot_id,
                skill_id=skill_id,
                min_level=min_level,
            )

    def remove_slot(self, slot_id: int) -> bool:
        """Soft delete: the slot disappears but its past assignments keep their history."""
        return (
            self._exec(
                f"UPDATE slots SET removed_at = {_NOW}"
                " WHERE org_id = :org AND id = :id AND removed_at IS NULL",
                id=slot_id,
            ).rowcount
            == 1
        )

    def _check_actor(self, actor: Actor) -> None:
        if actor.org_id != self._org:
            raise ValueError(
                f"actor belongs to org {actor.org_id}, but these repositories are for {self._org}"
            )

    def slots(self, mission_id: int) -> list[Slot]:
        """Live slots in listed order, each with its requirements."""
        slot_rows = self._all(
            "SELECT * FROM slots WHERE org_id = :org AND mission_id = :mission_id"
            " AND removed_at IS NULL ORDER BY position",
            mission_id=mission_id,
        )
        req_rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        reqs: dict[int, list[Requirement]] = {}
        for r in req_rows:
            reqs.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return [
            Slot(
                s["id"],
                s["mission_id"],
                s["name"],
                s["headcount"],
                s["position"],
                tuple(reqs.get(s["id"], ())),
            )
            for s in slot_rows
        ]

    def assignments(
        self, mission_id: int, statuses: Iterable[AssignmentStatus] | None = None
    ) -> list[Assignment]:
        wanted = tuple(statuses) if statuses is not None else tuple(AssignmentStatus)
        if not wanted:
            return []
        statuses, params = in_list("s", wanted)
        rows = self._all(
            f"SELECT * FROM assignments WHERE org_id = :org AND mission_id = :mission_id"
            f" AND status IN ({statuses}) ORDER BY id",
            mission_id=mission_id,
            **params,
        )
        return [_assignment(r) for r in rows]


def _crew_on_mission(crew_profile_id: int) -> tuple[str, dict[str, object]]:
    """A condition on mission `m`: the crew member holds an open or completed assignment on it.
    It joins on m.org_id, so the enclosing query's `m.org_id = :org` scopes it too."""
    statuses, params = in_list("s", ON_MISSION)
    clause = (
        "EXISTS (SELECT 1 FROM assignments a WHERE a.org_id = m.org_id"
        " AND a.mission_id = m.id AND a.crew_profile_id = :crew_profile_id"
        f" AND a.status IN ({statuses}))"
    )
    return clause, {"crew_profile_id": crew_profile_id, **params}


def _mission(r: sqlite3.Row) -> Mission:
    return Mission(
        r["id"],
        r["org_id"],
        r["name"],
        _window(r),
        MissionStatus(r["status"]),
        r["owner_id"],
        r["created_by_id"],
        r["approval_round"],
        r["approvals_required"],
    )


class AssignmentRepo(Scoped):
    def get(self, assignment_id: int) -> Assignment | None:
        r = self._one(
            "SELECT * FROM assignments WHERE org_id = :org AND id = :id", id=assignment_id
        )
        return _assignment(r) if r else None


def _assignment(r: sqlite3.Row) -> Assignment:
    return Assignment(
        r["id"],
        r["mission_id"],
        r["slot_id"],
        r["crew_profile_id"],
        AssignmentStatus(r["status"]),
        r["reason"],
    )


class ApprovalRepo(Scoped):
    def get(self, approval_id: int) -> Approval | None:
        r = self._one("SELECT * FROM approvals WHERE org_id = :org AND id = :id", id=approval_id)
        return _approval(r) if r else None

    def for_round(self, mission_id: int, round_: int) -> list[Approval]:
        rows = self._all(
            "SELECT * FROM approvals WHERE org_id = :org AND mission_id = :mission_id"
            " AND round = :round ORDER BY id",
            mission_id=mission_id,
            round=round_,
        )
        return [_approval(r) for r in rows]


def _approval(r: sqlite3.Row) -> Approval:
    return Approval(
        r["id"], r["mission_id"], r["round"], r["director_id"], r["decision"], r["reason"]
    )


class AuditRepo(Scoped):
    def record(
        self,
        actor_id: int,
        event: str,
        *,
        mission_id: int | None = None,
        assignment_id: int | None = None,
        crew_profile_id: int | None = None,
        from_status: str | None = None,
        to_status: str | None = None,
        reason: str | None = None,
        data: Mapping[str, object] | None = None,
    ) -> None:
        """Append one event. `data` should hold the names involved at the time."""
        self._exec(
            "INSERT INTO audit_events(org_id, actor_id, event, mission_id, assignment_id,"
            " crew_profile_id, from_status, to_status, reason, data)"
            " VALUES (:org, :actor_id, :event, :mission_id, :assignment_id,"
            " :crew_profile_id, :from_status, :to_status, :reason, :data)",
            actor_id=actor_id,
            event=event,
            mission_id=mission_id,
            assignment_id=assignment_id,
            crew_profile_id=crew_profile_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            data=json.dumps(dict(data or {})),
        )


class Repos:
    """All repositories for one organisation, built from the authenticated actor."""

    def __init__(self, conn: sqlite3.Connection, org_id: int) -> None:
        self.org_id = org_id
        self.organisation = OrganisationRepo(conn, org_id)
        self.users = UserRepo(conn, org_id)
        self.crew = CrewRepo(conn, org_id)
        self.skills = SkillRepo(conn, org_id)
        self.missions = MissionRepo(conn, org_id)
        self.assignments = AssignmentRepo(conn, org_id)
        self.approvals = ApprovalRepo(conn, org_id)
        self.audit = AuditRepo(conn, org_id)
        self.facts = FactsRepo(conn, org_id)
