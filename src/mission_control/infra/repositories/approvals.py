"""Approval decisions, by round."""

from __future__ import annotations

import sqlite3

from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Approval


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

    def record(
        self, mission_id: int, round_: int, director_id: int, decision: str, reason: str | None
    ) -> Approval:
        """A Director's decision for this round. The database refuses a second decision by the
        same Director in the same round, and a rejection without a reason."""
        cur = self._exec(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision, reason)"
            " VALUES (:org, :mission_id, :round, :director_id, :decision, :reason)",
            mission_id=mission_id,
            round=round_,
            director_id=director_id,
            decision=decision,
            reason=reason,
        )
        made = self.get(cur.lastrowid)
        assert made is not None
        return made


def _approval(r: sqlite3.Row) -> Approval:
    return Approval(
        r["id"], r["mission_id"], r["round"], r["director_id"], r["decision"], r["reason"]
    )
