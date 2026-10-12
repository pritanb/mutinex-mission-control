"""Assignments by id, and the shared row mapping for them."""

from __future__ import annotations

import sqlite3

from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Assignment


class AssignmentRepo(Scoped):
    def get(self, assignment_id: int) -> Assignment | None:
        r = self._one(
            "SELECT * FROM assignments WHERE org_id = :org AND id = :id", id=assignment_id
        )
        return assignment_from_row(r) if r else None


def assignment_from_row(r: sqlite3.Row) -> Assignment:
    return Assignment(
        r["id"],
        r["mission_id"],
        r["slot_id"],
        r["crew_profile_id"],
        AssignmentStatus(r["status"]),
        r["reason"],
    )
