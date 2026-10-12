"""Guard test (design §4): every SQL statement in infra/repositories filters on the caller's org,
bound by name as `org_id = :org`, and no statement uses positional `?` placeholders.

infra/platform.py, infra/security.py and seed/loader.py are scanned by the same rules. Each may
skip the org filter only for the statements listed for it in EXEMPT, which are cross-organisation
by nature; they must still bind by name:
- platform: the organisation statements that run before any tenant exists (mc-admin create-org);
- security: login by email alone, and the session statements on auth_tokens, which isn't owned
  by an organisation (reached by token hash, or by the user it belongs to);
- seed: checking the database is empty, and creating each organisation with its fixed id.
admin_cli.py holds no SQL at all."""

import ast
import re
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "src/mission_control"
REPOS = PACKAGE / "infra/repositories"
PLATFORM = PACKAGE / "infra/platform.py"
SECURITY = PACKAGE / "infra/security.py"
SEED = PACKAGE / "seed/loader.py"
ADMIN_CLI = PACKAGE / "admin_cli.py"
SQL = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH)\b", re.I)

# The org filter, written exactly as `org_id = :org`, optionally alias-qualified (`m.org_id`).
ORG_FILTER = re.compile(r"(?<![\w.])(?:\w+\.)?org_id = :org\b")
# The organisations table is the tenant itself: its own id is the caller's org, so a statement
# on it must be scoped by `WHERE id = :org` (reads and the settings update alike).
TENANT_LOOKUP = re.compile(r"\borganisations\b[^;]*\bWHERE id = :org\b")
# An INSERT has no WHERE: it must write the org as its first column, from the named :org value.
ORG_INSERT = re.compile(r"^\s*INSERT INTO \w+\s*\(\s*org_id\s*,[^)]*\)\s*VALUES\s*\(\s*:org\s*,")
POSITIONAL = re.compile(r"\?")

# The platform statements that may skip the org filter, written out in full: finding an
# organisation by slug across every tenant, and creating one.
PLATFORM_EXEMPT = frozenset(
    {
        "SELECT name FROM organisations WHERE slug = :slug",
        "INSERT INTO organisations(name, slug) VALUES (:name, :slug)",
    }
)
# Login by email, before the organisation is known, and the session statements on auth_tokens.
SECURITY_EXEMPT = frozenset(
    {
        "SELECT id, org_id, password_hash, is_active FROM users WHERE email = :email",
        "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at)"
        " VALUES (:user_id, :token_hash, :created, :expires)",
        "SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id FROM auth_tokens t"
        " JOIN users u ON u.id = t.user_id"
        " LEFT JOIN crew_profiles p ON p.org_id = u.org_id AND p.user_id = u.id"
        " WHERE t.token_hash = :token_hash AND t.revoked_at IS NULL AND t.expires_at > :now"
        " AND u.is_active = 1",
        "UPDATE auth_tokens SET revoked_at = :now"
        " WHERE token_hash = :token_hash AND revoked_at IS NULL",
        "UPDATE auth_tokens SET revoked_at = :now WHERE user_id = :user_id AND revoked_at IS NULL",
    }
)
# Checking the database is empty, and creating each demo organisation with its fixed id. Its
# other rows are written with that id bound as :org, like the repositories'.
SEED_EXEMPT = frozenset(
    {
        "SELECT count(*) FROM organisations",
        "INSERT INTO organisations(id, name, slug, required_approvals)"
        " VALUES (:org, :name, :slug, :required_approvals)",
    }
)
# Nothing else is exempt.
EXEMPT = {
    PLATFORM.name: PLATFORM_EXEMPT,
    SECURITY.name: SECURITY_EXEMPT,
    SEED.name: SEED_EXEMPT,
}
SCANNED_MODULES = (PLATFORM, SECURITY, SEED)


def _normal(sql: str) -> str:
    return " ".join(sql.split())


def problems(sql: str, exempt: frozenset[str] = frozenset()) -> list[str]:
    """Why a statement is unsafe; empty when it is scoped and bound by name. A statement in
    `exempt` needs no org filter, but must still bind by name."""
    found = []
    if POSITIONAL.search(sql):
        found.append("positional ? placeholder")
    scoped = ORG_FILTER.search(sql) or TENANT_LOOKUP.search(sql) or ORG_INSERT.search(sql)
    if not (scoped or _normal(sql) in exempt):
        found.append("no `org_id = :org` filter")
    return found


def exemptions_for(name: str) -> frozenset[str]:
    return EXEMPT.get(name, frozenset())


def sql_strings(paths=None):
    """Every SQL literal in the repositories and the other modules scanned. An f-string is read
    as one statement: its literal parts are joined and each interpolation is shown as {...}.
    Adjacent string literals are one constant, so a statement split over lines is read whole."""
    for path in paths or [*sorted(REPOS.glob("*.py")), *SCANNED_MODULES]:
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
    bad = {
        f"{name}:{line}": found
        for name, line, sql in sql_strings()
        if (found := problems(sql, exemptions_for(name)))
    }
    assert bad == {}, f"unsafe repository SQL: {bad}"


def test_the_scanned_module_names_dont_clash_with_a_repository():
    names = [p.name for p in REPOS.glob("*.py")] + [p.name for p in SCANNED_MODULES]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("module", SCANNED_MODULES, ids=lambda p: p.name)
def test_each_scanned_module_has_sql_and_every_exemption_is_in_use(module):
    module_sql = {_normal(sql) for name, _, sql in sql_strings() if name == module.name}
    assert module_sql, f"no SQL found in {module.name}: has it moved?"
    unused = EXEMPT[module.name] - module_sql
    assert not unused, f"an exemption no longer matches {module.name}: {unused}"


def test_admin_cli_has_no_sql():
    # Upper case only, so help text such as "Delete the database file" isn't taken for SQL.
    statement = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH|PRAGMA)\b")
    found = [sql for _, _, sql in sql_strings([ADMIN_CLI]) if statement.match(sql)]
    assert found == [], "mc-admin's SQL belongs in infra/"


@pytest.mark.parametrize(
    "sql, reason",
    [
        ("SELECT name FROM organisations WHERE slug = ?", "positional ? placeholder"),
        ("SELECT name FROM organisations", "no `org_id = :org` filter"),
        ("SELECT id FROM users WHERE email = :email", "no `org_id = :org` filter"),
        ("DELETE FROM organisations WHERE slug = :slug", "no `org_id = :org` filter"),
    ],
)
def test_the_platform_exemption_covers_only_its_listed_statements(sql, reason):
    assert reason in problems(sql, PLATFORM_EXEMPT)


@pytest.mark.parametrize(
    "sql, reason, exempt",
    [
        ("SELECT id FROM users WHERE email = ?", "positional ? placeholder", SECURITY_EXEMPT),
        (
            "SELECT password_hash FROM users WHERE id = :id",
            "no `org_id = :org` filter",
            SECURITY_EXEMPT,
        ),
        ("DELETE FROM auth_tokens WHERE user_id = :user_id", "no `org_id = :org` filter",
         SECURITY_EXEMPT),
        ("SELECT count(*) FROM users", "no `org_id = :org` filter", SEED_EXEMPT),
        ("INSERT INTO users(id, org_id) VALUES (:id, :org)", "no `org_id = :org` filter",
         SEED_EXEMPT),
    ],
)  # fmt: skip
def test_the_security_and_seed_exemptions_cover_only_their_listed_statements(sql, reason, exempt):
    assert reason in problems(sql, exempt)


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
