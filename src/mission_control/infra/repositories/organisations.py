"""The caller's own organisation and its settings."""

from __future__ import annotations

from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Organisation


class OrganisationRepo(Scoped):
    def get(self) -> Organisation:
        r = self._one("SELECT * FROM organisations WHERE id = :org")
        assert r is not None, "repositories are only built for an existing organisation"
        return Organisation(r["id"], r["name"], r["slug"], r["required_approvals"])

    def set_required_approvals(self, n: int) -> None:
        self._exec("UPDATE organisations SET required_approvals = :n WHERE id = :org", n=n)
