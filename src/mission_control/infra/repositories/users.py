"""Users of one organisation. Records never carry the password hash."""

from __future__ import annotations

import sqlite3

from mission_control.domain.enums import Role
from mission_control.infra.repositories.base import NOW, Scoped
from mission_control.infra.repositories.models import User


class UserRepo(Scoped):
    _COLUMNS = "id, org_id, email, name, role, is_active"

    def get(self, user_id: int) -> User | None:
        r = self._one(
            f"SELECT {self._COLUMNS} FROM users WHERE org_id = :org AND id = :id", id=user_id
        )
        return _user(r) if r else None

    def list(self) -> list[User]:
        rows = self._all(f"SELECT {self._COLUMNS} FROM users WHERE org_id = :org ORDER BY id")
        return [_user(r) for r in rows]

    def create(self, email: str, name: str, role: Role, password_hash: str) -> User:
        cur = self._exec(
            "INSERT INTO users(org_id, email, name, role, password_hash)"
            " VALUES (:org, :email, :name, :role, :password_hash)",
            email=email,
            name=name,
            role=role,
            password_hash=password_hash,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def set_role(self, user_id: int, role: Role) -> bool:
        return (
            self._exec(
                f"UPDATE users SET role = :role, updated_at = {NOW}"
                " WHERE org_id = :org AND id = :id",
                role=role,
                id=user_id,
            ).rowcount
            == 1
        )

    def set_active(self, user_id: int, active: bool) -> bool:
        return (
            self._exec(
                f"UPDATE users SET is_active = :active, updated_at = {NOW}"
                " WHERE org_id = :org AND id = :id",
                active=int(active),
                id=user_id,
            ).rowcount
            == 1
        )

    def count_active_directors(self) -> int:
        r = self._one(
            "SELECT count(*) FROM users WHERE org_id = :org AND role = :director AND is_active = 1",
            director=Role.DIRECTOR,
        )
        return r[0]


def _user(r: sqlite3.Row) -> User:
    return User(r["id"], r["org_id"], r["email"], r["name"], Role(r["role"]), bool(r["is_active"]))
