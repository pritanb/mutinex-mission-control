"""Shared plumbing for the tenant-scoped repositories. The caller's org is always bound by
name as `:org`, so a statement reads `org_id = :org` wherever the filter sits."""

import sqlite3
from collections.abc import Iterable
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus

# A crew member is "on" a mission while they hold an open or completed assignment on it.
ON_MISSION = (AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED, AssignmentStatus.COMPLETED)
OPEN = (AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED)
FINAL = (MissionStatus.COMPLETED, MissionStatus.CANCELLED)


def in_list(prefix: str, values: Iterable[object]) -> tuple[str, dict[str, object]]:
    """Named placeholders for an IN list: (":s0, :s1", {"s0": ..., "s1": ...})."""
    params = {f"{prefix}{i}": v for i, v in enumerate(values)}
    return ", ".join(f":{name}" for name in params), params


def window(row: sqlite3.Row) -> DateRange:
    return DateRange(date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"]))


class Scoped:
    def __init__(self, conn: sqlite3.Connection, org_id: int) -> None:
        self._conn = conn
        self._org = org_id

    def _params(self, params: dict[str, object]) -> dict[str, object]:
        if "org" in params:
            raise ValueError("`org` is bound from the repository, not passed in")
        return {"org": self._org, **params}

    def _one(self, sql: str, **params: object) -> sqlite3.Row | None:
        return self._conn.execute(sql, self._params(params)).fetchone()

    def _all(self, sql: str, **params: object) -> list[sqlite3.Row]:
        return self._conn.execute(sql, self._params(params)).fetchall()

    def _exec(self, sql: str, **params: object) -> sqlite3.Cursor:
        return self._conn.execute(sql, self._params(params))
