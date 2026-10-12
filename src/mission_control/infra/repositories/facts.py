"""Build the domain's input records from the database: slot specs, candidate facts, rosters,
workload facts and active assignments. Each loader uses one query per kind of fact."""

from __future__ import annotations

from collections.abc import Iterable

from mission_control.domain.eligibility import workload
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.records import (
    ActiveAssignment,
    AssignmentFact,
    CandidateFacts,
    Commitment,
    Requirement,
    RosterEntry,
    SlotSpec,
)
from mission_control.infra.repositories.base import FINAL, OPEN, Scoped, in_list, window


class FactsRepo(Scoped):
    def slot_specs(self, mission_id: int) -> list[SlotSpec]:
        """Live slots in listed order. open_places = headcount minus open assignments."""
        open_statuses, open_params = in_list("o", OPEN)
        rows = self._all(
            f"""SELECT s.id, s.position, s.name, s.headcount,
                       (SELECT count(*) FROM assignments a
                        WHERE a.org_id = s.org_id AND a.slot_id = s.id
                        AND a.status IN ({open_statuses})) AS open_count
                FROM slots s WHERE s.org_id = :org AND s.mission_id = :mission_id
                AND s.removed_at IS NULL ORDER BY s.position""",
            mission_id=mission_id,
            **open_params,
        )
        reqs = self._requirements(mission_id)
        return [
            SlotSpec(
                r["id"],
                r["position"],
                r["name"],
                r["headcount"] - r["open_count"],
                tuple(reqs.get(r["id"], ())),
            )
            for r in rows
        ]

    def _requirements(self, mission_id: int) -> dict[int, list[Requirement]]:
        rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        reqs: dict[int, list[Requirement]] = {}
        for r in rows:
            reqs.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return reqs

    def candidates(
        self, excluding_mission_id: int | None, crew_profile_ids: Iterable[int] | None = None
    ) -> list[CandidateFacts]:
        """Facts for every crew profile in the org (or just those listed), as seen from one
        mission: commitments and workload leave that mission out."""
        ids = None if crew_profile_ids is None else tuple(crew_profile_ids)
        if ids == ():
            return []
        id_filter, id_params = "", {}
        if ids is not None:
            placeholders, id_params = in_list("p", ids)
            id_filter = f" AND p.id IN ({placeholders})"

        profiles = self._all(
            f"""SELECT p.id, p.display_name, u.is_active FROM crew_profiles p
                JOIN users u ON u.org_id = p.org_id AND u.id = p.user_id
                WHERE p.org_id = :org{id_filter} ORDER BY p.id""",
            **id_params,
        )
        if not profiles:
            return []
        wanted = [r["id"] for r in profiles]
        skills = self._by_profile(
            "SELECT crew_profile_id, skill_id, level FROM crew_skills WHERE org_id = :org", wanted
        )
        blocked = self._by_profile(
            "SELECT crew_profile_id, start_date, end_date FROM unavailability WHERE org_id = :org",
            wanted,
            order="start_date, id",
        )
        accepted = self._accepted(wanted)

        facts = []
        for p in profiles:
            mine = accepted.get(p["id"], [])
            facts.append(
                CandidateFacts(
                    crew_profile_id=p["id"],
                    name=p["display_name"],
                    active=bool(p["is_active"]),
                    skills={r["skill_id"]: r["level"] for r in skills.get(p["id"], [])},
                    unavailable=tuple(window(r) for r in blocked.get(p["id"], [])),
                    accepted_elsewhere=tuple(
                        Commitment(r["mission_id"], r["mission_name"], window(r))
                        for r in mine
                        if r["mission_status"] not in FINAL
                        and r["mission_id"] != excluding_mission_id
                    ),
                    workload=workload([_fact(r) for r in mine], excluding_mission_id),
                )
            )
        return facts

    def candidate(
        self, crew_profile_id: int, excluding_mission_id: int | None
    ) -> CandidateFacts | None:
        found = self.candidates(excluding_mission_id, crew_profile_ids=[crew_profile_id])
        return found[0] if found else None

    def _by_profile(self, sql: str, profile_ids: list[int], order: str = "rowid") -> dict:
        ids, params = in_list("p", profile_ids)
        rows = self._all(f"{sql} AND crew_profile_id IN ({ids}) ORDER BY {order}", **params)
        grouped: dict[int, list] = {}
        for r in rows:
            grouped.setdefault(r["crew_profile_id"], []).append(r)
        return grouped

    def _accepted(self, profile_ids: list[int]) -> dict:
        """Accepted assignments of these crew, with their missions, oldest mission first."""
        ids, params = in_list("p", profile_ids)
        rows = self._all(
            f"""SELECT a.crew_profile_id, a.status, m.id AS mission_id, m.name AS mission_name,
                       m.status AS mission_status, m.start_date, m.end_date
                FROM assignments a JOIN missions m ON m.org_id = a.org_id AND m.id = a.mission_id
                WHERE a.org_id = :org AND a.status = :accepted AND a.crew_profile_id IN ({ids})
                ORDER BY m.start_date, m.id""",
            accepted=AssignmentStatus.ACCEPTED,
            **params,
        )
        grouped: dict[int, list] = {}
        for r in rows:
            grouped.setdefault(r["crew_profile_id"], []).append(r)
        return grouped

    def commitments(self, crew_profile_id: int) -> list[Commitment]:
        """Accepted assignments on missions that aren't finished, e.g. to check new
        unavailability against."""
        facts = self.candidate(crew_profile_id, excluding_mission_id=None)
        return list(facts.accepted_elsewhere) if facts else []

    def roster(self, mission_id: int) -> list[RosterEntry]:
        """Open assignments on the mission, each with its slot spec and the crew member's facts
        as seen from this mission."""
        open_statuses, params = in_list("o", OPEN)
        rows = self._all(
            f"SELECT id, slot_id, crew_profile_id, status FROM assignments"
            f" WHERE org_id = :org AND mission_id = :mission_id AND status IN ({open_statuses})"
            f" ORDER BY id",
            mission_id=mission_id,
            **params,
        )
        if not rows:
            return []
        specs = {s.id: s for s in self.slot_specs(mission_id)}
        crew = {
            c.crew_profile_id: c
            for c in self.candidates(
                mission_id, crew_profile_ids={r["crew_profile_id"] for r in rows}
            )
        }
        return [
            RosterEntry(
                r["id"],
                specs[r["slot_id"]],
                crew[r["crew_profile_id"]],
                AssignmentStatus(r["status"]),
            )
            for r in rows
            if r["slot_id"] in specs
        ]

    def assignment_facts(self, crew_profile_id: int) -> list[AssignmentFact]:
        rows = self._all(
            """SELECT a.status, m.id AS mission_id, m.status AS mission_status, m.start_date,
                      m.end_date
               FROM assignments a JOIN missions m ON m.org_id = a.org_id AND m.id = a.mission_id
               WHERE a.org_id = :org AND a.crew_profile_id = :crew_profile_id ORDER BY a.id""",
            crew_profile_id=crew_profile_id,
        )
        return [_fact(r) for r in rows]

    def active_assignments(self, crew_profile_id: int) -> list[ActiveAssignment]:
        """Accepted assignments on Active missions, with their slot's requirements."""
        rows = self._all(
            """SELECT m.id AS mission_id, m.name AS mission_name, s.id AS slot_id,
                      s.name AS slot_name
               FROM assignments a
               JOIN missions m ON m.org_id = a.org_id AND m.id = a.mission_id
               JOIN slots s ON s.org_id = a.org_id AND s.id = a.slot_id
               WHERE a.org_id = :org AND a.crew_profile_id = :crew_profile_id
               AND a.status = :accepted AND m.status = :active ORDER BY a.id""",
            crew_profile_id=crew_profile_id,
            accepted=AssignmentStatus.ACCEPTED,
            active=MissionStatus.ACTIVE,
        )
        result = []
        for r in rows:
            reqs = self._requirements(r["mission_id"]).get(r["slot_id"], [])
            result.append(
                ActiveAssignment(r["mission_id"], r["mission_name"], r["slot_name"], tuple(reqs))
            )
        return result


def _fact(r) -> AssignmentFact:
    return AssignmentFact(
        r["mission_id"],
        MissionStatus(r["mission_status"]),
        AssignmentStatus(r["status"]),
        window(r),
    )
