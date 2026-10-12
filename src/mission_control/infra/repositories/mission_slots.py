"""A mission's slots and their skill requirements.

Slots are soft-deleted: a removed slot disappears from every list and lookup, but keeps its row,
so past assignments still show the slot they were in.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping

from mission_control.domain.records import Requirement
from mission_control.infra.repositories.base import NOW, Scoped
from mission_control.infra.repositories.models import Slot

_LIVE = "removed_at IS NULL"


class SlotRequirements(Scoped):
    """Reading a mission's slot requirements, shared by the mission and fact repositories."""

    def _requirements_by_slot(self, mission_id: int) -> dict[int, tuple[Requirement, ...]]:
        """Every slot's requirements, removed slots included, by slot id and then skill id."""
        rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        grouped: dict[int, list[Requirement]] = {}
        for r in rows:
            grouped.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return {slot_id: tuple(reqs) for slot_id, reqs in grouped.items()}


class MissionSlots(SlotRequirements):
    """Part of MissionRepo: reach these as `repos.missions.<method>`."""

    # Reading

    def slots(self, mission_id: int) -> list[Slot]:
        """Live slots in listed order, each with its requirements."""
        rows = self._all(
            f"SELECT * FROM slots WHERE org_id = :org AND mission_id = :mission_id AND {_LIVE}"
            " ORDER BY position",
            mission_id=mission_id,
        )
        requirements = self._requirements_by_slot(mission_id)
        return [_slot(r, requirements.get(r["id"], ())) for r in rows]

    def get_slot(self, slot_id: int) -> Slot | None:
        """A live slot by id, with its requirements."""
        r = self._one(
            f"SELECT * FROM slots WHERE org_id = :org AND id = :id AND {_LIVE}", id=slot_id
        )
        if r is None:
            return None
        return _slot(r, self._requirements_by_slot(r["mission_id"]).get(slot_id, ()))

    def slot_names(self, mission_id: int) -> dict[int, str]:
        """Names of every slot the mission has had, removed ones included, so past assignments
        still show the slot they were in."""
        rows = self._all(
            "SELECT id, name FROM slots WHERE org_id = :org AND mission_id = :mission_id",
            mission_id=mission_id,
        )
        return {r["id"]: r["name"] for r in rows}

    # Writing

    def add_slot(
        self, mission_id: int, name: str, headcount: int, requirements: Mapping[int, int]
    ) -> Slot:
        """Append a slot after the last live one, with its {skill_id: min_level}."""
        cur = self._exec(
            f"""INSERT INTO slots(org_id, mission_id, name, headcount, position)
                VALUES (:org, :mission_id, :name, :headcount,
                        (SELECT coalesce(max(position), 0) + 1 FROM slots
                         WHERE org_id = :org AND mission_id = :mission_id AND {_LIVE}))""",
            mission_id=mission_id,
            name=name,
            headcount=headcount,
        )
        self._insert_requirements(cur.lastrowid, requirements)
        created = self.get_slot(cur.lastrowid)
        assert created is not None
        return created

    def update_slot(self, slot_id: int, name: str, headcount: int) -> bool:
        return self._changed(
            f"UPDATE slots SET name = :name, headcount = :headcount"
            f" WHERE org_id = :org AND id = :id AND {_LIVE}",
            name=name,
            headcount=headcount,
            id=slot_id,
        )

    def replace_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> bool:
        """Swap a live slot's requirements for {skill_id: min_level}. False if no such slot."""
        if self.get_slot(slot_id) is None:
            return False
        self._exec(
            "DELETE FROM slot_requirements WHERE org_id = :org AND slot_id = :slot_id",
            slot_id=slot_id,
        )
        self._insert_requirements(slot_id, requirements)
        return True

    def remove_slot(self, slot_id: int) -> bool:
        """Soft delete: the slot disappears but its past assignments keep their history."""
        return self._changed(
            f"UPDATE slots SET removed_at = {NOW} WHERE org_id = :org AND id = :id AND {_LIVE}",
            id=slot_id,
        )

    def _insert_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> None:
        for skill_id, min_level in requirements.items():
            self._exec(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (:org, :slot_id, :skill_id, :min_level)",
                slot_id=slot_id,
                skill_id=skill_id,
                min_level=min_level,
            )


def _slot(r: sqlite3.Row, requirements: tuple[Requirement, ...]) -> Slot:
    return Slot(r["id"], r["mission_id"], r["name"], r["headcount"], r["position"], requirements)
