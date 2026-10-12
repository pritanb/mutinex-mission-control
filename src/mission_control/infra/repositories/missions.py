"""Missions and who can see them.

`MissionRepo` is reached as `repos.missions`. It also carries a mission's slots
(`mission_slots.py`) and its crew and assignments (`mission_crew.py`), so every mission query is
one attribute away.

Visibility for crew is decided here: Directors and Leads see every mission in their organisation,
while crew see only the missions they're on. A mission a crew member isn't on is reported as
missing, exactly like an unknown id, so callers answer 404. Permissions' VIEW_MISSION is the
matching rule for services that have already loaded the mission.
"""

from __future__ import annotations

import sqlite3

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import MissionStatus, Role
from mission_control.domain.permissions import Actor
from mission_control.infra.repositories.base import FINAL, NOW, in_list, window
from mission_control.infra.repositories.mission_crew import MissionCrew, crew_is_on_mission
from mission_control.infra.repositories.mission_slots import MissionSlots
from mission_control.infra.repositories.models import Mission

_ORDER = "ORDER BY start_date, id"


class MissionRepo(MissionSlots, MissionCrew):
    # Reading

    def get(self, mission_id: int) -> Mission | None:
        r = self._one("SELECT * FROM missions WHERE org_id = :org AND id = :id", id=mission_id)
        return _mission(r) if r else None

    def list(self) -> list[Mission]:
        return [
            _mission(r) for r in self._all(f"SELECT * FROM missions WHERE org_id = :org {_ORDER}")
        ]

    def non_final_owned_by(self, user_id: int) -> list[Mission]:
        """Missions this user owns that aren't completed or cancelled."""
        placeholders, params = in_list("f", FINAL)
        rows = self._all(
            f"SELECT * FROM missions WHERE org_id = :org AND owner_id = :owner"
            f" AND status NOT IN ({placeholders}) {_ORDER}",
            owner=user_id,
            **params,
        )
        return [_mission(r) for r in rows]

    # Visibility

    def list_visible(self, actor: Actor) -> list[Mission]:
        """Directors and Leads see every mission; crew see only the missions they're on."""
        self._check_actor(actor)
        if actor.role != Role.CREW:
            return self.list()
        if actor.crew_profile_id is None:
            return []
        on_mission, params = crew_is_on_mission(actor.crew_profile_id)
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
        on_mission, params = crew_is_on_mission(actor.crew_profile_id)
        r = self._one(
            f"SELECT * FROM missions m WHERE m.org_id = :org AND m.id = :id AND {on_mission}",
            id=mission_id,
            **params,
        )
        return _mission(r) if r else None

    def _check_actor(self, actor: Actor) -> None:
        if actor.org_id != self._org:
            raise ValueError(
                f"actor belongs to org {actor.org_id}, but these repositories are for {self._org}"
            )

    # Writing

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
        return self._changed(
            f"UPDATE missions SET name = :name, start_date = :start, end_date = :end,"
            f" updated_at = {NOW} WHERE org_id = :org AND id = :id",
            name=name,
            start=window.start.isoformat(),
            end=window.end.isoformat(),
            id=mission_id,
        )

    def set_status(self, mission_id: int, status: MissionStatus) -> bool:
        return self._changed(
            f"UPDATE missions SET status = :status, updated_at = {NOW}"
            " WHERE org_id = :org AND id = :id",
            status=status,
            id=mission_id,
        )

    def start_round(self, mission_id: int, approvals_required: int) -> bool:
        """Submit: the mission goes to pending approval in a new round, needing
        `approvals_required` approvals however the organisation's setting changes later."""
        return self._changed(
            f"UPDATE missions SET status = 'pending_approval', approval_round = approval_round + 1,"
            f" approvals_required = :required, updated_at = {NOW}"
            " WHERE org_id = :org AND id = :id",
            required=approvals_required,
            id=mission_id,
        )

    def set_owner(self, mission_id: int, owner_id: int) -> bool:
        return self._changed(
            f"UPDATE missions SET owner_id = :owner, updated_at = {NOW}"
            " WHERE org_id = :org AND id = :id",
            owner=owner_id,
            id=mission_id,
        )


def _mission(r: sqlite3.Row) -> Mission:
    return Mission(
        r["id"],
        r["org_id"],
        r["name"],
        window(r),
        MissionStatus(r["status"]),
        r["owner_id"],
        r["created_by_id"],
        r["approval_round"],
        r["approvals_required"],
    )
