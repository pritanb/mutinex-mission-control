"""Guard test (design §4): every SQL statement in infra/repositories filters on the caller's org,
bound by name as `org_id = :org`, and no statement uses positional `?` placeholders."""

import ast
import re
from pathlib import Path

import pytest

REPOS = Path(__file__).resolve().parents[2] / "src/mission_control/infra/repositories"
SQL = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH)\b", re.I)

# The org filter, written exactly as `org_id = :org`, optionally alias-qualified (`m.org_id`).
ORG_FILTER = re.compile(r"(?<![\w.])(?:\w+\.)?org_id = :org\b")
# The organisations table is the tenant itself: its own id is the caller's org, so a statement
# on it must be scoped by `WHERE id = :org` (reads and the settings update alike).
TENANT_LOOKUP = re.compile(r"\borganisations\b[^;]*\bWHERE id = :org\b")
# An INSERT has no WHERE: it must write the org as its first column, from the named :org value.
ORG_INSERT = re.compile(r"^\s*INSERT INTO \w+\s*\(\s*org_id\s*,[^)]*\)\s*VALUES\s*\(\s*:org\s*,")
POSITIONAL = re.compile(r"\?")


def problems(sql: str) -> list[str]:
    """Why a repository statement is unsafe; empty when it is scoped and bound by name."""
    found = []
    if POSITIONAL.search(sql):
        found.append("positional ? placeholder")
    if not (ORG_FILTER.search(sql) or TENANT_LOOKUP.search(sql) or ORG_INSERT.search(sql)):
        found.append("no `org_id = :org` filter")
    return found


def sql_strings():
    """Every SQL literal in the package. An f-string is read as one statement: its literal
    parts are joined and each interpolation is shown as {...}."""
    for path in sorted(REPOS.glob("*.py")):
        tree = ast.parse(path.read_text())
        inside_fstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                parts = []
                for value in node.values:
                    inside_fstrings.add(id(value))
                    is_text = isinstance(value, ast.Constant)
                    parts.append(value.value if is_text else "{...}")
                text = "".join(parts)
                if SQL.match(text):
                    yield path.name, node.lineno, text
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in inside_fstrings
                and SQL.match(node.value)
            ):
                yield path.name, node.lineno, node.value


def test_repositories_contain_sql():
    found = list(sql_strings())
    assert found, "no SQL found: has the repositories package moved?"
    # f-string queries are read whole, so their org_id filter is seen
    assert any("{...}" in sql for _, _, sql in found)


def test_every_repository_query_filters_on_the_named_org():
    bad = {f"{name}:{line}": problems(sql) for name, line, sql in sql_strings() if problems(sql)}
    assert bad == {}, f"unsafe repository SQL: {bad}"


@pytest.mark.parametrize(
    "sql, reason",
    [
        ("SELECT * FROM missions WHERE id = ? AND org_id = ?", "positional ? placeholder"),
        ("SELECT * FROM missions WHERE id = :id", "no `org_id = :org` filter"),
        ("SELECT * FROM missions WHERE org_id = :id", "no `org_id = :org` filter"),
        ("SELECT * FROM missions WHERE org_id = :organisation", "no `org_id = :org` filter"),
        ("SELECT * FROM missions WHERE parent_org_id = :org", "no `org_id = :org` filter"),
        ("SELECT * FROM organisations WHERE id = ?", "positional ? placeholder"),
        ("SELECT * FROM organisations WHERE id = :id", "no `org_id = :org` filter"),
        (
            "UPDATE organisations SET required_approvals = :n WHERE id = :id",
            "no `org_id = :org` filter",
        ),
        ("UPDATE organisations SET required_approvals = :n", "no `org_id = :org` filter"),
        (
            "INSERT INTO audit_events(org_id, event) VALUES (:other, :org)",
            "no `org_id = :org` filter",
        ),
        (
            "INSERT INTO audit_events(event, org_id) VALUES (:org, :event)",
            "no `org_id = :org` filter",
        ),
    ],
)
def test_the_guard_flags_unsafe_statements(sql, reason):
    assert reason in problems(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM missions WHERE org_id = :org AND id = :id",
        "SELECT * FROM missions m WHERE m.org_id = :org AND m.id = :id",
        "SELECT * FROM organisations WHERE id = :org",
        "UPDATE organisations SET required_approvals = :n WHERE id = :org",
        "INSERT INTO audit_events(org_id, event) VALUES (:org, :event)",
    ],
)
def test_the_guard_accepts_scoped_named_statements(sql):
    assert problems(sql) == []
