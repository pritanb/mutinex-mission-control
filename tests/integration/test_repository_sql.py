"""Guard test (design §4): every SQL statement in infra/repositories filters on org_id."""

import ast
import re
from pathlib import Path

REPOS = Path(__file__).resolve().parents[2] / "src/mission_control/infra/repositories"
SQL = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH)\b", re.I)

# Statements allowed without org_id, each with a reason. Keep this empty unless justified.
ALLOWLIST: dict[str, str] = {
    "SELECT * FROM organisations WHERE id = ?": (
        "organisations is the tenant itself; the parameter is the caller's org_id"
    ),
}


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


def test_every_repository_query_mentions_org_id():
    missing = [
        f"{name}:{line}"
        for name, line, sql in sql_strings()
        if "org_id" not in sql and sql.strip() not in ALLOWLIST
    ]
    assert missing == [], f"queries without org_id: {missing}"
