"""Who is on a mission: its assignments, and the crew a mission's roster is made of.

A crew member is "on" a mission while they hold an open or completed assignment on it. That one
definition drives both who counts as rostered and which missions crew can see.
"""

from __future__ import annotations

from collections.abc import Iterable

from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories.assignments import assignment_from_row
from mission_control.infra.repositories.base import ON_MISSION, Scoped, in_list
from mission_control.infra.repositories.models import Assignment


class MissionCrew(Scoped):
    """Part of MissionRepo: reach these as `repos.missions.<method>`."""

    def assignments(
        self, mission_id: int, statuses: Iterable[AssignmentStatus] | None = None
    ) -> list[Assignment]:
        """The mission's assignments, optionally only those in the given statuses."""
        wanted = tuple(AssignmentStatus) if statuses is None else tuple(statuses)
        if not wanted:
            return []
        placeholders, params = in_list("s", wanted)
        rows = self._all(
            f"SELECT * FROM assignments WHERE org_id = :org AND mission_id = :mission_id"
            f" AND status IN ({placeholders}) ORDER BY id",
            mission_id=mission_id,
            **params,
        )
        return [assignment_from_row(r) for r in rows]

    def rostered_user_ids(self, mission_id: int) -> frozenset[int]:
        """User ids of the crew on the mission: those holding an open or completed assignment."""
        placeholders, params = in_list("s", ON_MISSION)
        rows = self._all(
            f"""SELECT DISTINCT u.id FROM assignments a
                JOIN crew_profiles c ON c.org_id = a.org_id AND c.id = a.crew_profile_id
                JOIN users u ON u.org_id = c.org_id AND u.id = c.user_id
                WHERE a.org_id = :org AND a.mission_id = :mission_id
                AND a.status IN ({placeholders})""",
            mission_id=mission_id,
            **params,
        )
        return frozenset(r["id"] for r in rows)

    def assignee_names(self, mission_id: int) -> dict[int, str]:
        """Display names of everyone who has held an assignment on the mission, by crew profile
        id, so a mission's assignments can be shown with names."""
        rows = self._all(
            """SELECT DISTINCT c.id, c.display_name FROM assignments a
               JOIN crew_profiles c ON c.org_id = a.org_id AND c.id = a.crew_profile_id
               WHERE a.org_id = :org AND a.mission_id = :mission_id""",
            mission_id=mission_id,
        )
        return {r["id"]: r["display_name"] for r in rows}


def crew_is_on_mission(crew_profile_id: int) -> tuple[str, dict[str, object]]:
    """A SQL condition on a mission aliased `m`: this crew member is on it. It joins on
    m.org_id, so the enclosing query's `m.org_id = :org` scopes it too."""
    placeholders, params = in_list("s", ON_MISSION)
    clause = (
        "EXISTS (SELECT 1 FROM assignments a WHERE a.org_id = m.org_id"
        " AND a.mission_id = m.id AND a.crew_profile_id = :crew_profile_id"
        f" AND a.status IN ({placeholders}))"
    )
    return clause, {"crew_profile_id": crew_profile_id, **params}
