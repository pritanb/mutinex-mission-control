"""The append-only audit trail."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType

from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import AuditEntry


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

    def for_mission(self, mission_id: int) -> list[AuditEntry]:
        """The mission's events in the order they happened, each with the actor's name."""
        rows = self._all(
            """SELECT e.*, u.name AS actor_name FROM audit_events e
               JOIN users u ON u.org_id = e.org_id AND u.id = e.actor_id
               WHERE e.org_id = :org AND e.mission_id = :mission_id ORDER BY e.id""",
            mission_id=mission_id,
        )
        return [
            AuditEntry(
                r["id"],
                datetime.fromisoformat(r["created_at"]),
                r["actor_id"],
                r["actor_name"],
                r["event"],
                r["assignment_id"],
                r["crew_profile_id"],
                r["from_status"],
                r["to_status"],
                r["reason"],
                MappingProxyType(json.loads(r["data"])),
            )
            for r in rows
        ]
