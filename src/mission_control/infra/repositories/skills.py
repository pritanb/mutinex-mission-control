"""The organisation's skill catalogue."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Skill


@dataclass(frozen=True)
class SkillHolder:
    """A crew member who has a level in the skill."""

    crew_profile_id: int
    name: str


@dataclass(frozen=True)
class SkillRequirement:
    """A slot that requires the skill. Removed slots count too: they keep their requirements."""

    mission_id: int
    mission_name: str
    slot_id: int
    slot_name: str


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

    def holders(self, skill_id: int) -> list[SkillHolder]:
        """Crew with a level in the skill, by crew profile id, named as their user."""
        rows = self._all(
            """SELECT c.id, u.name FROM crew_skills k
               JOIN crew_profiles c ON c.org_id = k.org_id AND c.id = k.crew_profile_id
               JOIN users u ON u.org_id = c.org_id AND u.id = c.user_id
               WHERE k.org_id = :org AND k.skill_id = :id ORDER BY c.id""",
            id=skill_id,
        )
        return [SkillHolder(r["id"], r["name"]) for r in rows]

    def required_by(self, skill_id: int) -> list[SkillRequirement]:
        """Slots requiring the skill, removed ones included, by mission date then position."""
        rows = self._all(
            """SELECT m.id AS mission_id, m.name AS mission_name, s.id AS slot_id,
                      s.name AS slot_name
               FROM slot_requirements r
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               JOIN missions m ON m.org_id = s.org_id AND m.id = s.mission_id
               WHERE r.org_id = :org AND r.skill_id = :id
               ORDER BY m.start_date, m.id, s.position, s.id""",
            id=skill_id,
        )
        return [
            SkillRequirement(r["mission_id"], r["mission_name"], r["slot_id"], r["slot_name"])
            for r in rows
        ]

    def delete(self, skill_id: int) -> bool:
        return (
            self._exec("DELETE FROM skills WHERE org_id = :org AND id = :id", id=skill_id).rowcount
            == 1
        )


def _skill(r: sqlite3.Row) -> Skill:
    return Skill(r["id"], r["org_id"], r["name"], r["category"])
