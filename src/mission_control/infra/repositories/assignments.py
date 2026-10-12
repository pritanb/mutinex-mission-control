"""Assignments by id, the writes that create and change them, and the shared row mapping."""

from __future__ import annotations

import sqlite3

from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories.base import NOW, Scoped
from mission_control.infra.repositories.models import Assignment


class AssignmentRepo(Scoped):
    def get(self, assignment_id: int) -> Assignment | None:
        r = self._one(
            "SELECT * FROM assignments WHERE org_id = :org AND id = :id", id=assignment_id
        )
        return assignment_from_row(r) if r else None

    def create(
        self, mission_id: int, slot_id: int, crew_profile_id: int, proposed_by_id: int
    ) -> Assignment:
        """A new proposal. The database refuses a second open assignment for the same person on
        the same mission, and links to another organisation's records."""
        cur = self._exec(
            "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id, proposed_by_id)"
            " VALUES (:org, :mission_id, :slot_id, :crew_profile_id, :proposed_by_id)",
            mission_id=mission_id,
            slot_id=slot_id,
            crew_profile_id=crew_profile_id,
            proposed_by_id=proposed_by_id,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def set_status(
        self, assignment_id: int, status: AssignmentStatus, reason: str | None = None
    ) -> bool:
        """Move an assignment to `status`, recording `reason` (None clears it)."""
        return self._changed(
            f"UPDATE assignments SET status = :status, reason = :reason, updated_at = {NOW}"
            " WHERE org_id = :org AND id = :id",
            status=status,
            reason=reason,
            id=assignment_id,
        )


def assignment_from_row(r: sqlite3.Row) -> Assignment:
    return Assignment(
        r["id"],
        r["mission_id"],
        r["slot_id"],
        r["crew_profile_id"],
        AssignmentStatus(r["status"]),
        r["reason"],
    )
