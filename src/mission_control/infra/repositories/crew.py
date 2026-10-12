"""Crew profiles: details, skills, unavailability and assignment history."""

from __future__ import annotations

import sqlite3

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.infra.repositories.assignments import assignment_from_row
from mission_control.infra.repositories.base import NOW, OPEN, Scoped, in_list, window
from mission_control.infra.repositories.models import (
    Assignment,
    AssignmentSummary,
    CrewProfile,
    Unavailability,
)


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
        return [Unavailability(r["id"], r["crew_profile_id"], window(r), r["reason"]) for r in rows]

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
                f" updated_at = {NOW} WHERE org_id = :org AND id = :id",
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
        return [assignment_from_row(r) for r in rows]

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
                updated_at = {NOW} WHERE crew_skills.org_id = :org""",
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
                window(r),
                MissionStatus(r["mission_status"]),
                r["slot_name"],
                AssignmentStatus(r["status"]),
                r["reason"],
            )
            for r in rows
        ]


def _crew(r: sqlite3.Row) -> CrewProfile:
    return CrewProfile(r["id"], r["org_id"], r["user_id"], r["display_name"], r["bio"])
