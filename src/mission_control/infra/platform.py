"""Platform statements: the organisation lookups and writes that come before any tenant exists to
scope by. Only `mc-admin create-org` uses them; everything inside an organisation goes through the
tenant-scoped repositories."""

import sqlite3


def organisation_with_slug(conn: sqlite3.Connection, slug: str) -> str | None:
    """The name of the organisation with this slug, in any tenant, or None."""
    row = conn.execute(
        "SELECT name FROM organisations WHERE slug = :slug", {"slug": slug}
    ).fetchone()
    return row[0] if row else None


def create_organisation(conn: sqlite3.Connection, name: str, slug: str) -> int:
    """A new organisation with the default settings. Returns its id."""
    cursor = conn.execute(
        "INSERT INTO organisations(name, slug) VALUES (:name, :slug)",
        {"name": name, "slug": slug},
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid
