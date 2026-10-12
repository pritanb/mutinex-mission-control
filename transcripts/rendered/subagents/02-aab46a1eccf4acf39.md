# Subagent (02): Wave 2: helpers and audit clean-up

Source: `agent-aab46a1eccf4acf39.jsonl` · 2026-10-12 05:19:36 UTC → 2026-10-12 05:37:28 UTC

Rendered from the raw JSONL without editing message content. Tool results and thinking are collapsed; expand them to read.


---

### 👤 User · 2026-10-12 05:19:36 UTC

You are doing the consistency clean-up from the Mission Control phase reviews. Work ONLY in `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup` (branch `fix-cleanup`, from 37c7293, which already contains every other review fix). **Don't commit, push or run bare `git stash`. Don't add dependencies (httpx banned; httpx2 only). Behaviour must not change** except where a fix below says so: every refusal code, message, status and HTTP/CLI output stays the same unless listed. Read `CLAUDE.md` and `docs/technical-design.md` §2, §7, §10 as needed. Conventions: no PRD/AC/§ refs in `src/` (tests may); `@contextmanager` → `-> Generator[T]`; match the surrounding style.

## Fixes
1. **One shape for before/after values in audit `data`.** Today: `changes{field: [old, new]}` (`services/missions/changes.py`, `slots.py`), `from_x`/`to_x` (`admin.py`, `changes.py` transfer), bare `from`/`to` (`admin.py` ~56), `previous_x` (`crew.py`, `slots.py`). Pick one convention (recommended: `changes: {field: [old, new]}` for edited fields, keeping the existing name keys like `mission_name`, `crew_name`, `slot_name` as "names at the time"), apply it everywhere, document it in the `domain/events.py` module docstring, and update the CLI history renderer (`src/mission_control/cli/commands/missions.py` history / wherever it reads `data`, e.g. `to_owner_name`) and every test that asserts audit data. The rendered `mc missions history` text should stay the same or read better; show before/after in your hand-off.
2. **Single-reason refusals built one way:** replace `RuleViolation(msg, [Problem(code, msg, refs)])` with `RuleViolation.of(Problem(...))` (e.g. `admin.py` ~86, 110–119, 334; `missions/rules.py` `refuse_taken_name` etc.).
3. **Shared helpers instead of copies** (put service-level ones in `services/context.py` or a new `services/common.py`; domain-level ones in the domain):
   - joining names ("A, B and C"): `domain/eligibility.py`, `services/missions/rules.py join_names`, `admin.py _join` → one domain helper;
   - `_about(profile)` in `crew.py` and `assignments.py`;
   - "state check or raise `StateConflict`" in `approvals.py`, `matching.py`, `missions/lifecycle.py`, inline in `missions/changes.py` → one helper (e.g. `require_state(mission, action)`);
   - "strip the reason or `InvalidInput(f"{Doing} {name} needs a reason")`" in `assignments.py`, `approvals.py`, `missions/lifecycle.py`;
   - the slot-requirements SQL duplicated in `infra/repositories/mission_slots.py` and `facts.py`;
   - open places computed in `services/missions/views.py` and in `facts.slot_specs`;
   - the overlap problem built in `crew.py` and `domain/eligibility.py`;
   - `services/crew.py` and `admin.py` now import `date_problems`/`invalid`/`refuse_input` from `services/missions/inputs.py`; move the generic ones somewhere shared.
   - CLI: `_show_version` and the bare-group argument handling duplicated in `cli/main.py` and `admin_cli.py`; `resolve.py` `skill_ids`/`skill_named` each fetching `/skills` with repeated lookup logic.
4. **Dead code:** `domain/approvals.approver_problems` is now used only by tests (the services use `decision_problems`). Remove it if nothing in `src/` needs it, and move its unit tests onto `decision_problems` plus the role check in `permissions`.
5. **Module refs in `src/`:** `domain/events.py` has `# M9 admin`, `# M10 crew`, `# M11 …`, `# M12 …`, `# M13 …` section comments; replace with plain topic headings (e.g. `# Crew`, `# Organisation and users`). Grep `src/` for any other `M\d+`/`AC-`/`§`/`PRD` references and fix them.
6. **Small coupling:** `services/missions/rules.py record_change` reads the mission name back out of the audit `data` dict (`str(data["mission_name"])`) — pass it explicitly. `services/assignments.cascade_mission_end` uses `ctx.repos` while every other helper takes `repos` — make it take `repos`.
7. **SQL lint coverage:** `src/mission_control/seed/loader.py` and `src/mission_control/infra/security.py` use positional `?` SQL and aren't scanned by `tests/integration/test_repository_sql.py`. Convert them to named parameters and bring both into the lint, with documented exemptions only for their inherently cross-organisation statements (seed inserts with explicit org ids; login/session lookups by email/token hash), the same way `infra/platform.py` is handled.
8. **Test gaps:** (a) AC-7 after a transfer: test that the new owner can, and the previous owner can't, propose, apply the match, and submit (service level; edit is already tested). (b) `tests/integration/test_assignments_service.py` (~line 213) proves "propose on a Pending mission sends it back to Draft" by adding a slot through the repository, which users can't do; keep it if useful but add the realistic case: on a seeded Pending mission every slot is full, so a proposal is refused with `slot_full` and the mission stays Pending.

## Verify, then hand off
- `uv run pytest -W error -q -o addopts=''`, `uv run ruff check`, `uv run ruff format --check` — all pass, no skips in `tests/cli/test_readme_smoke.py`.
- **Prove behaviour is unchanged:** before you start, run a behaviour snapshot — a script under `/tmp/fixcleanup/` that, on a fresh seeded DB, calls a broad set of service use cases (successes and refusals across admin, crew, missions, slots, assignments, approvals, matching, inbox, history) and prints each result's codes/messages/status; save its output, rerun after your changes, and diff. The only differences allowed are the audit `data` shape (fix 1). Also run the real `mc missions history 1` after the S1 golden path (seed with `MC_DATABASE_PATH=/tmp/fixcleanup/x.db uv run mc-admin seed --reset`, uvicorn on a free port, `mc` with `HOME=/tmp/fixcleanup/home_<who> MC_API_URL=...`) before vs after. Stop servers; keep everything under /tmp.
- Final message: per fix — what changed, files, tests, evidence, "resolved: yes/no"; the snapshot diff; test count. Don't commit.

<details>
<summary>⚙️ System/meta message · 2026-10-12 05:19:36 UTC</summary>

```
<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered.
</system-reminder>
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && git status && git log --oneline -3 && find src -name '*.py' | xargs wc -l | sort -n | tail -60
```

<details>
<summary>↳ Result</summary>

```
On branch fix-cleanup
nothing to commit, working tree clean
37c7293 wip: phase 3/4 review fixes, wave 1 merged (local only)
5526869 wip: phase 4 reconciliation snapshot (local only; split into reviewed commits before main)
2b279fa docs: 409 convention and the inbox in design §7
      68 src/mission_control/api/routers/crew.py
      68 src/mission_control/infra/repositories/audit.py
      69 src/mission_control/infra/repositories/users.py
      70 src/mission_control/cli/main.py
      71 src/mission_control/api/schemas/matching.py
      71 src/mission_control/domain/approvals.py
      71 src/mission_control/infra/repositories/mission_crew.py
      73 src/mission_control/cli/config.py
      73 src/mission_control/services/missions/loading.py
      77 src/mission_control/domain/records.py
      79 src/mission_control/api/schemas/inbox.py
      80 src/mission_control/domain/errors.py
      81 src/mission_control/cli/prompts.py
      86 src/mission_control/domain/matching.py
      91 src/mission_control/api/routers/admin.py
      93 src/mission_control/services/missions/inputs.py
      97 src/mission_control/cli/views.py
      98 src/mission_control/api/schemas/admin.py
     101 src/mission_control/cli/commands/common.py
     102 src/mission_control/cli/refusals.py
     105 src/mission_control/services/context.py
     109 src/mission_control/api/schemas/crew.py
     110 src/mission_control/infra/security.py
     114 src/mission_control/services/missions/views.py
     115 src/mission_control/infra/db.py
     117 src/mission_control/infra/repositories/skills.py
     120 src/mission_control/cli/commands/crew.py
     123 src/mission_control/cli/resolve.py
     125 src/mission_control/api/routers/missions.py
     127 src/mission_control/cli/commands/assignments.py
     127 src/mission_control/infra/repositories/mission_slots.py
     128 src/mission_control/infra/repositories/models.py
     136 src/mission_control/services/inbox.py
     145 src/mission_control/cli/commands/me.py
     156 src/mission_control/seed/loader.py
     158 src/mission_control/cli/client.py
     160 src/mission_control/services/matching.py
     162 src/mission_control/infra/repositories/missions.py
     162 src/mission_control/services/missions/rules.py
     164 src/mission_control/services/auth.py
     166 src/mission_control/infra/repositories/crew.py
     173 src/mission_control/api/errors.py
     180 src/mission_control/services/approvals.py
     202 src/mission_control/services/missions/slots.py
     209 src/mission_control/domain/eligibility.py
     210 src/mission_control/services/missions/changes.py
     224 src/mission_control/infra/repositories/facts.py
     232 src/mission_control/domain/permissions.py
     236 src/mission_control/cli/render.py
     239 src/mission_control/cli/commands/account.py
     242 src/mission_control/seed/data.py
     243 src/mission_control/cli/commands/admin.py
     247 src/mission_control/api/schemas/missions.py
     290 src/mission_control/domain/lifecycle.py
     329 src/mission_control/services/crew.py
     363 src/mission_control/services/admin.py
     364 src/mission_control/services/assignments.py
     379 src/mission_control/admin_cli.py
     804 src/mission_control/cli/commands/missions.py
   10616 total
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && ls -R src/mission_control | head -100 && ls tests tests/* && cat src/mission_control/domain/events.py src/mission_control/domain/errors.py
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/services/admin.py src/mission_control/services/context.py src/mission_control/services/missions/inputs.py
```

<details>
<summary>↳ Result</summary>

```
"""Director administration: organisation settings, users and roles, crew profiles and the skill
catalogue.

Each use case authorizes first, then loads, checks, writes and audits inside one write
transaction, so the checks see the same data the write changes. Audit `data` keeps the names
that applied at the time.
"""

from collections.abc import Iterable
from enum import Enum

from mission_control.domain.enums import Action, Role
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.passwords import validate_password
from mission_control.infra import security
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    CrewProfile,
    Mission,
    Organisation,
    Skill,
    User,
)
from mission_control.services.context import ServiceContext, check, found
from mission_control.services.missions.inputs import invalid, refuse_input


class _Keep(Enum):
    KEEP = "keep"


KEEP = _Keep.KEEP  # update_skill: leave the category as it is


# --- Organisation settings ----------------------------------------------------------------


def view_organisation(ctx: ServiceContext) -> Organisation:
    ctx.authorize(Action.MANAGE_ORG)
    return ctx.repos.organisation.get()


def set_required_approvals(ctx: ServiceContext, n: int) -> Organisation:
    """Only missions submitted from now on use the new number: a submitted mission keeps the
    number it was submitted with."""
    ctx.authorize(Action.MANAGE_ORG)
    if n < 1:
        raise InvalidInput("At least one approval must be required")
    with ctx.write() as repos:
        current = repos.organisation.get()
        if current.required_approvals == n:
            return current
        repos.organisation.set_required_approvals(n)
        ctx.audit(
            Event.ORG_REQUIRED_APPROVALS_CHANGED,
            data={"from": current.required_approvals, "to": n},
        )
        return repos.organisation.get()


# --- Users --------------------------------------------------------------------------------


def list_users(ctx: ServiceContext) -> list[User]:
    ctx.authorize(Action.MANAGE_ORG)
    return ctx.repos.users.list()


def view_user(ctx: ServiceContext, user_id: int) -> User:
    ctx.authorize(Action.MANAGE_ORG)
    return found(ctx.repos.users.get(user_id), "User")


def create_user(ctx: ServiceContext, email: str, name: str, role: Role, password: str) -> User:
    """A Director sets the initial password. A new Crew Member gets a crew profile straight
    away; Leads and Directors get one only on request."""
    ctx.authorize(Action.MANAGE_ORG)
    email, name = email.strip(), name.strip()
    refuse_input(_blank(email, "email address") + _blank(name, "name"))
    validate_password(password)
    password_hash = security.hash_password(password)  # slow, so before the write lock
    with ctx.write() as repos:
        # Emails are unique across every organisation, because login is by email alone.
        if security.find_login(ctx.conn, email) is not None:
            message = f"The email address {email} is already in use"
            raise RuleViolation(message, [Problem("already_exists", message, {"email": email})])
        user = repos.users.create(email, name, role, password_hash)
        ctx.audit(
            Event.USER_CREATED,
            data={"user_id": user.id, "user_name": user.name, "email": user.email, "role": role},
        )
        if role == Role.CREW:
            _give_crew_profile(ctx, repos, user)
    return user


def create_crew_profile(
    ctx: ServiceContext, user_id: int, display_name: str | None = None
) -> CrewProfile:
    """Give a Lead or Director a crew profile so they can take part in missions. The display
    name defaults to their first name. Profiles are never deleted."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if display_name is not None:
            display_name = _required(display_name, "display name")
        existing = repos.crew.by_user(user.id)
        if existing is not None:
            message = f"{user.name} already has a crew profile"
            raise RuleViolation(
                message,
                [
                    Problem(
                        "already_exists",
                        message,
                        {"user_id": user.id, "crew_profile_id": existing.id},
                    )
                ],
            )
        return _give_crew_profile(ctx, repos, user, display_name)


def change_role(ctx: ServiceContext, user_id: int, role: Role) -> User:
    """A crew profile survives any role change, and becoming a Crew Member gives one to anyone
    who lacks it. A Lead who owns unfinished missions keeps the role until they're reassigned,
    and the organisation always keeps an active Director."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if user.role == role:
            return user
        problems: list[Problem] = []
        if user.role == Role.LEAD:
            problems += _owns_open_missions(repos, user)
        if user.role == Role.DIRECTOR:
            problems += _last_director(repos, user)
        check(problems, f"{user.name}'s role can't be changed")

        repos.users.set_role(user.id, role)
        ctx.audit(
            Event.USER_ROLE_CHANGED,
            data={
                "user_id": user.id,
                "user_name": user.name,
                "from_role": user.role,
                "to_role": role,
            },
        )
        if role == Role.CREW and repos.crew.by_user(user.id) is None:
            _give_crew_profile(ctx, repos, user)
        return found(repos.users.get(user.id), "User")


def deactivate_user(ctx: ServiceContext, user_id: int) -> User:
    """Deactivated users keep their history but can't sign in, and every session they have
    ends at once. Refused while they hold open assignments, own unfinished missions, or are the
    last active Director; every reason is listed together."""
    ctx.authorize(Action.MANAGE_ORG)
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
        if not user.is_active:
            return user
        profile = repos.crew.by_user(user.id)
        problems: list[Problem] = []
        if profile is not None:
            problems += _has_open_assignments(repos, user, profile)
        problems += _owns_open_missions(repos, user)
        if user.role == Role.DIRECTOR:
            problems += _last_director(repos, user)
        check(problems, f"{user.name} can't be deactivated")

        repos.users.set_active(user.id, False)
        security.revoke_user_tokens(ctx.conn, user.id, ctx.now)
        ctx.audit(
            Event.USER_DEACTIVATED,
            crew_profile_id=profile.id if profile else None,
            data={"user_id": user.id, "user_name": user.name},
        )
        return found(repos.users.get(user.id), "User")


def _give_crew_profile(
    ctx: ServiceContext, repos: Repos, user: User, display_name: str | None = None
) -> CrewProfile:
    profile = repos.crew.create(user.id, display_name or user.name.split()[0])
    ctx.audit(
        Event.CREW_PROFILE_CREATED,
        crew_profile_id=profile.id,
        data={"user_id": user.id, "user_name": user.name, "display_name": profile.display_name},
    )
    return profile


def _has_open_assignments(repos: Repos, user: User, profile: CrewProfile) -> list[Problem]:
    mission_ids = {a.mission_id for a in repos.crew.open_assignments(profile.id)}
    missions = _by_date([found(repos.missions.get(i), "Mission") for i in mission_ids])
    if not missions:
        return []
    on = (
        f"an open assignment on {missions[0].name}"
        if len(missions) == 1
        else f"open assignments on {_join(m.name for m in missions)}"
    )
    return [
        Problem(
            "has_open_assignments",
            f"{user.name} has {on}; they must withdraw or be removed first",
            {"user_id": user.id, "mission_ids": [m.id for m in missions]},
        )
    ]


def _owns_open_missions(repos: Repos, user: User) -> list[Problem]:
    missions = repos.missions.non_final_owned_by(user.id)
    if not missions:
        return []
    them = "it" if len(missions) == 1 else "them"
    return [
        Problem(
            "owns_open_missions",
            f"{user.name} still owns {_join(m.name for m in missions)};"
            f" reassign {them} to another Lead first",
            {"user_id": user.id, "mission_ids": [m.id for m in missions]},
        )
    ]


def _last_director(repos: Repos, user: User) -> list[Problem]:
    if not user.is_active or repos.users.count_active_directors() > 1:
        return []
    return [
        Problem(
            "last_director",
            f"{user.name} is the only active Director, and the organisation must always have"
            " one; make someone else a Director first",
            {"user_id": user.id},
        )
    ]


# --- Skill catalogue ----------------------------------------------------------------------


def list_skills(ctx: ServiceContext) -> list[Skill]:
    ctx.authorize(Action.LIST_SKILLS)
    return ctx.repos.skills.list()


def add_skill(ctx: ServiceContext, name: str, category: str | None = None) -> Skill:
    """Names are unique within the organisation, ignoring case."""
    ctx.authorize(Action.MANAGE_SKILLS)
    name = _required(name, "skill name")
    category = _optional(category)
    with ctx.write() as repos:
        existing = repos.skills.by_name(name)
        if existing is not None:
            raise _name_taken(existing)
        skill = repos.skills.create(name, category)
        ctx.audit(
            Event.SKILL_CREATED,
            data={"skill_id": skill.id, "skill_name": skill.name, "category": skill.category},
        )
        return skill


def update_skill(
    ctx: ServiceContext,
    skill_id: int,
    *,
    name: str | None = None,
    category: str | None | _Keep = KEEP,
) -> Skill:
    """Rename or recategorise. The skill keeps its id, so crew levels and slot requirements
    follow it. A name left out stays as it is; so does the category unless one is given (None
    clears it)."""
    ctx.authorize(Action.MANAGE_SKILLS)
    with ctx.write() as repos:
        skill = found(repos.skills.get(skill_id), "Skill")
        to_name = _required(name, "skill name") if name is not None else skill.name
        to_category = skill.category if isinstance(category, _Keep) else _optional(category)
        if (to_name, to_category) == (skill.name, skill.category):
            return skill
        clash = repos.skills.by_name(to_name)
        if clash is not None and clash.id != skill.id:
            raise _name_taken(clash)
        repos.skills.update(skill.id, to_name, to_category)
        ctx.audit(
            Event.SKILL_UPDATED,
            data={
                "skill_id": skill.id,
                "from_name": skill.name,
                "to_name": to_name,
                "from_category": skill.category,
                "to_category": to_category,
            },
        )
        return found(repos.skills.get(skill.id), "Skill")


def delete_skill(ctx: ServiceContext, skill_id: int) -> None:
    """Only a skill that no crew member has and no slot requires can be deleted."""
    ctx.authorize(Action.MANAGE_SKILLS)
    with ctx.write() as repos:
        skill = found(repos.skills.get(skill_id), "Skill")
        holders = repos.skills.holders(skill.id)
        slots = repos.skills.required_by(skill.id)
        if holders or slots:
            reasons = []
            if holders:
                has = "has" if len(holders) == 1 else "have"
                reasons.append(f"{_join(h.name for h in holders)} {has} it")
            if slots:
                requires = "requires" if len(slots) == 1 else "require"
                uses = _join(f"{s.mission_name} ({s.slot_name})" for s in slots)
                reasons.append(f"{uses} {requires} it")
            raise RuleViolation.of(
                Problem(
                    "skill_in_use",
                    f"{skill.name} can't be deleted because {' and '.join(reasons)}",
                    {
                        "skill_id": skill.id,
                        "crew_profile_ids": [h.crew_profile_id for h in holders],
                        "mission_ids": list(dict.fromkeys(s.mission_id for s in slots)),
                    },
                )
            )
        repos.skills.delete(skill.id)
        ctx.audit(Event.SKILL_DELETED, data={"skill_id": skill.id, "skill_name": skill.name})


def _name_taken(existing: Skill) -> RuleViolation:
    message = f"The catalogue already has a skill called {existing.name}"
    return RuleViolation(message, [Problem("already_exists", message, {"skill_id": existing.id})])


# --- Helpers ------------------------------------------------------------------------------


def _required(value: str, what: str) -> str:
    stripped = value.strip()
    refuse_input(_blank(stripped, what))
    return stripped


def _blank(value: str, what: str) -> list[Problem]:
    return [] if value.strip() else [invalid(f"The {what} can't be blank")]


def _optional(value: str | None) -> str | None:
    return (value.strip() or None) if value is not None else None


def _by_date(missions: list[Mission]) -> list[Mission]:
    return sorted(missions, key=lambda m: (m.window.start, m.id))


def _join(names: Iterable[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    items = list(names)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"
"""What every use case runs with: who is acting, their organisation's repositories, the time,
one transaction and its audit trail.

A use case follows one shape: load through `ctx.repos`, check with domain rules, then write and
audit inside `with ctx.write():`. Refusals raise `Forbidden`, `NotFound` or `RuleViolation`.
"""

import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control.domain.enums import MissionStatus
from mission_control.domain.errors import Forbidden, NotFound, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import NO_CONTEXT, Action, Actor, Context, authorize
from mission_control.infra.db import read_tx, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission


class ServiceContext:
    def __init__(self, conn: sqlite3.Connection, actor: Actor, now: datetime | None = None):
        if now is not None and now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        self.conn = conn
        self.actor = actor
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.repos = Repos(conn, actor.org_id)

    @contextmanager
    def write(self) -> Generator[Repos]:
        """One write transaction: the lock is taken before any check inside the block, and
        everything, audit included, commits together or not at all."""
        with write_tx(self.conn):
            yield self.repos

    @contextmanager
    def read(self) -> Generator[Repos]:
        """Several reads against one consistent snapshot."""
        with read_tx(self.conn):
            yield self.repos

    def audit(self, event: Event, **fields: object) -> None:
        """Record an event as the acting user. Only inside `write()`, so it commits with the
        change it describes."""
        if not self.conn.in_transaction:
            raise RuntimeError("audit events are written inside ctx.write()")
        self.repos.audit.record(self.actor.user_id, event, **fields)  # type: ignore[arg-type]

    def authorize(self, action: Action, context: Context = NO_CONTEXT) -> None:
        """For a resource the actor can see: refusal is Forbidden (403)."""
        authorize(self.actor, action, context)

    def authorize_view(self, action: Action, context: Context, what: str) -> None:
        """For looking at something: a refusal is reported as NotFound (404), so the response
        never reveals that it exists."""
        try:
            authorize(self.actor, action, context)
        except Forbidden as refused:
            raise NotFound(what) from refused


def found[T](value: T | None, what: str) -> T:
    """The loaded record, or NotFound if the repository returned None."""
    if value is None:
        raise NotFound(what)
    return value


def visible_mission(ctx: ServiceContext, repos: Repos, mission_id: int) -> Mission:
    """The mission if the actor may see it; NotFound if it's missing or hidden from them."""
    return found(repos.missions.get_visible(ctx.actor, mission_id), "Mission")


def mission_context(repos: Repos, mission: Mission) -> Context:
    """Everything the permission rules may ask about a mission."""
    return Context(
        owner_id=mission.owner_id,
        created_by_id=mission.created_by_id,
        rostered_user_ids=repos.missions.rostered_user_ids(mission.id),
    )


def return_to_draft(
    ctx: ServiceContext, repos: Repos, mission: Mission, cause: Event, mission_name: str
) -> None:
    """Send a Pending mission back to Draft after a change to it, so its approval round stops
    counting, and audit the return with the event that caused it. Call it inside `ctx.write()`,
    after auditing the change itself."""
    if not repos.missions.set_status(mission.id, MissionStatus.DRAFT):
        raise NotFound("Mission")
    ctx.audit(
        Event.MISSION_RETURNED_TO_DRAFT,
        mission_id=mission.id,
        from_status=mission.status,
        to_status=MissionStatus.DRAFT,
        data={"mission_name": mission_name, "cause": cause.value},
    )


def check(problems: Sequence[Problem], message: str) -> None:
    """Raise every problem at once as a RuleViolation; do nothing if there are none."""
    if problems:
        raise RuleViolation(message, problems)
"""What callers pass in, and the checks on it. Malformed values are refused as InvalidInput
(422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

from mission_control.domain.errors import InvalidInput, Problem
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL, Requirement


@dataclass(frozen=True)
class SlotInput:
    """A slot as given by the caller. `requirements` maps skill id to minimum level."""

    name: str
    headcount: int
    requirements: Mapping[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", MappingProxyType(dict(self.requirements)))


def refuse_input(problems: Sequence[Problem]) -> None:
    if problems:
        raise invalid_input(problems)


def invalid_input(problems: Sequence[Problem]) -> InvalidInput:
    """Every mistake at once; the message is the only one's, or a summary of several."""
    message = problems[0].message if len(problems) == 1 else "Some values aren't valid"
    return InvalidInput(message, problems)


def invalid(message: str, refs: Mapping[str, int] | None = None) -> Problem:
    return Problem("validation_error", message, refs or {})


def name_problems(name: str) -> list[Problem]:
    return [] if name.strip() else [invalid("The mission needs a name")]


def date_problems(start: date, end: date) -> list[Problem]:
    if end >= start:
        return []
    return [invalid(f"The end date {end.isoformat()} is before the start date {start.isoformat()}")]


def slot_problems(
    label: str,
    name: str | None,
    headcount: int | None,
    requirements: Mapping[int, int] | None,
    refs: Mapping[str, int] | None = None,
) -> list[Problem]:
    """What's wrong with a slot's given values. None means the value isn't being set. `refs`
    names the slot, if it already exists."""
    problems = []
    if name is not None and not name.strip():
        problems.append(invalid("Every slot needs a name", refs))
    if headcount is not None and headcount < 1:
        problems.append(invalid(f"{label} needs a headcount of at least 1", refs))
    if requirements is not None:
        if not requirements:
            problems.append(invalid(f"{label} needs at least one required skill", refs))
        for level in requirements.values():
            if not MIN_LEVEL <= level <= MAX_LEVEL:
                problems.append(
                    invalid(
                        f"{label}: a minimum skill level must be from {MIN_LEVEL} to "
                        f"{MAX_LEVEL}, not {level}",
                        refs,
                    )
                )
    return problems


def slot_label(name: str) -> str:
    """How a slot is named in a message, even if its name is blank."""
    return name.strip() or "A slot"


def levels(requirements: Sequence[Requirement]) -> dict[int, int]:
    return {r.skill_id: r.min_level for r in requirements}


def requirement_data(requirements: Sequence[Requirement]) -> list[dict[str, object]]:
    """Requirements for an audit event, with the skill names at the time."""
    return [
        {"skill_id": r.skill_id, "skill_name": r.skill_name, "min_level": r.min_level}
        for r in requirements
    ]
```

</details>

<details>
<summary>↳ Result</summary>

```
__init__.py
admin_cli.py
api
cli
domain
infra
seed
services

src/mission_control/api:
__init__.py
app.py
deps.py
errors.py
routers
schemas

src/mission_control/api/routers:
__init__.py
admin.py
assignments.py
auth.py
crew.py
missions.py

src/mission_control/api/schemas:
__init__.py
admin.py
assignments.py
auth.py
common.py
crew.py
inbox.py
matching.py
missions.py

src/mission_control/cli:
__init__.py
client.py
commands
config.py
env.py
errors.py
main.py
prompts.py
refusals.py
render.py
resolve.py
views.py

src/mission_control/cli/commands:
__init__.py
account.py
admin.py
assignments.py
common.py
crew.py
me.py
missions.py

src/mission_control/domain:
__init__.py
approvals.py
dates.py
eligibility.py
enums.py
errors.py
events.py
lifecycle.py
matching.py
passwords.py
permissions.py
records.py

src/mission_control/infra:
__init__.py
db.py
platform.py
repositories
schema.sql
security.py
settings.py

src/mission_control/infra/repositories:
__init__.py
approvals.py
assignments.py
audit.py
base.py
crew.py
facts.py
mission_crew.py
mission_slots.py
missions.py
models.py
organisations.py
skills.py
users.py

src/mission_control/seed:
tests/builders.py
tests/conftest.py

tests:
api
builders.py
cli
conftest.py
integration
unit

tests/api:
conftest.py
test_api_auth.py
test_api_errors.py
test_api_isolation.py
test_api_lifecycle.py
test_api_permissions.py
test_api_resources.py
test_api_scenarios.py
test_health.py

tests/cli:
api_contract.py
cli_fakes.py
conftest.py
test_admin_cli.py
test_api_contract.py
test_cli_auth.py
test_cli_config.py
test_cli_errors.py
test_cli_match.py
test_cli_missions.py
test_cli_parsing.py
test_cli_people.py
test_cli_real_api.py
test_cli_render.py
test_cli_scenarios.py
test_readme_smoke.py

tests/integration:
conftest.py
test_admin_service.py
test_approvals_service.py
test_assignment_writes.py
test_assignments_service.py
test_auth.py
test_crew_service.py
test_db.py
test_facts.py
test_inbox_service.py
test_matching_service.py
test_mission_end_service.py
test_mission_history.py
test_missions_service.py
test_platform.py
test_repositories.py
test_repository_sql.py
test_repository_writes.py
test_schema_constraints.py
test_seed.py
test_service_context.py

tests/unit:
domain
"""Audit event names. Every audit event is recorded under one of these names, so a mission's
history reads the same whichever code path wrote it."""

from enum import StrEnum


class Event(StrEnum):
    MISSION_CREATED = "mission.created"
    MISSION_SUBMITTED = "mission.submitted"
    MISSION_APPROVED = "mission.approved"
    MISSION_ACTIVATED = "mission.activated"
    MISSION_COMPLETED = "mission.completed"
    USER_PASSWORD_CHANGED = "user.password_changed"
    # M10 crew
    CREW_DETAILS_UPDATED = "crew.details_updated"
    CREW_UNAVAILABILITY_ADDED = "crew.unavailability_added"
    CREW_UNAVAILABILITY_REMOVED = "crew.unavailability_removed"
    CREW_SKILL_SET = "crew.skill_set"
    CREW_SKILL_REMOVED = "crew.skill_removed"
    # M9 admin
    ORG_REQUIRED_APPROVALS_CHANGED = "org.required_approvals_changed"
    USER_CREATED = "user.created"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    CREW_PROFILE_CREATED = "crew_profile.created"
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_DELETED = "skill.deleted"
    # M11 missions
    MISSION_UPDATED = "mission.updated"
    MISSION_TRANSFERRED = "mission.transferred"
    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
    SLOT_ADDED = "slot.added"
    SLOT_UPDATED = "slot.updated"
    SLOT_REQUIREMENTS_CHANGED = "slot.requirements_changed"
    SLOT_REMOVED = "slot.removed"
    # M12 assignments
    ASSIGNMENT_PROPOSED = "assignment.proposed"
    ASSIGNMENT_ACCEPTED = "assignment.accepted"
    ASSIGNMENT_DECLINED = "assignment.declined"
    ASSIGNMENT_WITHDRAWN = "assignment.withdrawn"
    ASSIGNMENT_REMOVED = "assignment.removed"
    ASSIGNMENT_COMPLETED = "assignment.completed"
    ASSIGNMENT_CANCELLED = "assignment.cancelled"
    # M13 approvals and ending a mission
    MISSION_REJECTED = "mission.rejected"
    MISSION_CANCELLED = "mission.cancelled"
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class Problem:
    """One reason an action can't go ahead. `refs` names the records involved. It is copied
    into a read-only mapping, so no two problems share it and it can't be changed later."""

    code: str
    message: str
    refs: Mapping[str, int | str | list[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "refs", MappingProxyType(dict(self.refs)))


class Forbidden(Exception):
    """The actor can see the resource but isn't allowed to do this."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Unauthenticated(Exception):
    """No valid identity: bad credentials, or a missing, expired or revoked session."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class NotFound(Exception):
    """Missing, belonging to another organisation, or not visible to the actor. All three look
    the same, so a response never reveals that something exists."""

    code = "not_found"

    def __init__(self, what: str) -> None:
        self.message = f"{what} not found"
        super().__init__(self.message)


class RuleViolation(Exception):
    """A change conflicts with the rules or the current state. Carries every problem at once.

    A rule refusal's code is always `rule_violation`, with a summary message; each reason is a
    problem with its own code. Only state conflicts (`StateConflict`) set a code of their own."""

    def __init__(self, message: str, problems: Sequence[Problem], code: str = "rule_violation"):
        if not problems:
            raise ValueError("a RuleViolation needs at least one problem")
        super().__init__(message)
        self.code = code
        self.message = message
        self.problems = tuple(problems)

    @classmethod
    def of(cls, problem: Problem) -> "RuleViolation":
        """A refusal with a single reason, which also serves as its message. The code stays
        `rule_violation`; the reason's own code is in `problems`."""
        return cls(problem.message, [problem])


class InvalidInput(ValueError):
    """A value the caller supplied is malformed, e.g. a blank name or a level out of range.
    Answered as 422. Distinct from plain ValueError, which also signals programming errors.

    `problems` lists every mistake at once; given none, the message is the only one."""

    code = "validation_error"

    def __init__(self, message: str, problems: Sequence[Problem] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.problems = tuple(problems) or (Problem(self.code, message),)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/services/crew.py src/mission_control/services/missions/rules.py src/mission_control/services/missions/changes.py
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && ls src/mission_control/services src/mission_control/services/missions && cat src/mission_control/services/missions/slots.py src/mission_control/services/missions/lifecycle.py src/mission_control/services/missions/__init__.py
```

<details>
<summary>↳ Result</summary>

```
"""Crew profiles: viewing people, their skills, availability and assignment history; editing
your own personal details and unavailability; and setting other people's skill levels.

Who sees what:
- Directors and Leads see every profile; crew see only their own. A profile the caller can't
  see is reported as not found.
- Unavailability dates are visible with the profile, but the reasons only to Directors and to
  the person themselves.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import invalidated_by_skill_change
from mission_control.domain.errors import InvalidInput, Problem
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, Context, can
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    AssignmentSummary,
    CrewProfile,
    Unavailability,
    User,
)
from mission_control.services.context import ServiceContext, check, found
from mission_control.services.missions.inputs import date_problems, invalid, refuse_input

_CREW_MEMBER = "Crew member"


@dataclass(frozen=True)
class SkillLevel:
    skill_id: int
    skill_name: str
    level: int


@dataclass(frozen=True)
class UnavailabilityView:
    """A period someone is unavailable. `reason` is None when the viewer may not see it."""

    id: int
    window: DateRange
    reason: str | None


@dataclass(frozen=True)
class CrewView:
    """A crew profile as the caller may see it."""

    crew_profile_id: int
    user_id: int
    name: str
    email: str
    active: bool
    bio: str | None
    skills: tuple[SkillLevel, ...]  # by skill name
    unavailability: tuple[UnavailabilityView, ...]  # by start date


# Viewing


def list_crew(ctx: ServiceContext) -> list[CrewView]:
    """Every profile the caller may see: all of them for Directors and Leads, only their own
    for crew."""
    with ctx.read() as repos:
        users = {u.id: u for u in repos.users.list()}
        skill_names = _skill_names(repos)
        return [
            _view(ctx, repos, profile, users[profile.user_id], skill_names)
            for profile in repos.crew.list()
            if can(ctx.actor, Action.VIEW_CREW, _about(profile))
        ]


def view_crew(ctx: ServiceContext, crew_profile_id: int) -> CrewView:
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
        user = found(repos.users.get(profile.user_id), _CREW_MEMBER)
        return _view(ctx, repos, profile, user, _skill_names(repos))


def list_unavailability(ctx: ServiceContext, crew_profile_id: int) -> list[UnavailabilityView]:
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
        return list(_unavailability(ctx, repos, profile))


def assignment_history(ctx: ServiceContext, crew_profile_id: int) -> list[AssignmentSummary]:
    """Every assignment the person has held, newest first, including missions they've left.
    Each is a summary: it doesn't give access to the mission itself."""
    with ctx.read() as repos:
        profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_ASSIGNMENT_HISTORY)
        return repos.crew.history(profile.id)


# Personal details and unavailability: the person themselves only


def update_details(
    ctx: ServiceContext,
    crew_profile_id: int,
    *,
    display_name: str | None = None,
    bio: str | None = None,
) -> CrewProfile:
    """Change your display name and bio. A value left as None stays as it is; a blank bio
    clears it."""
    if display_name is None and bio is None:
        with ctx.read():  # nothing to change: still check access, but write nothing
            return _own_profile(ctx, crew_profile_id)
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        new_name = None if display_name is None else display_name.strip()
        if new_name == "":
            raise InvalidInput("Display name can't be blank")
        name = profile.display_name if new_name is None else new_name
        new_bio = profile.bio if bio is None else (bio.strip() or None)
        repos.crew.update(profile.id, name, new_bio)
        ctx.audit(
            Event.CREW_DETAILS_UPDATED,
            crew_profile_id=profile.id,
            data={"crew_name": name, "previous_name": profile.display_name},
        )
        return found(repos.crew.get(profile.id), _CREW_MEMBER)


def add_unavailability(
    ctx: ServiceContext, crew_profile_id: int, start: date, end: date, reason: str
) -> Unavailability:
    """Record a period you're unavailable. Past dates are allowed. Refused if it overlaps one
    of your accepted assignments on a mission that isn't finished."""
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        reason = reason.strip()
        problems = date_problems(start, end)
        if not reason:
            problems.append(invalid("Unavailability needs a reason"))
        refuse_input(problems)
        window = DateRange(start, end)
        clashes = [
            _overlap(profile, c.mission_id, c.mission_name, c.window, window)
            for c in repos.facts.commitments(profile.id)
            if c.window.overlaps(window)
        ]
        assignments = "an accepted assignment" if len(clashes) == 1 else "accepted assignments"
        check(clashes, f"{profile.display_name} has {assignments} overlapping those dates")
        added = repos.crew.add_unavailability(profile.id, window, reason)
        ctx.audit(
            Event.CREW_UNAVAILABILITY_ADDED,
            crew_profile_id=profile.id,
            data=_period(profile, window),  # the reason stays private: not in the audit log
        )
        return added


def remove_unavailability(
    ctx: ServiceContext, crew_profile_id: int, unavailability_id: int
) -> None:
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        entry = found(
            next(
                (u for u in repos.crew.unavailability(profile.id) if u.id == unavailability_id),
                None,
            ),
            "Unavailability",
        )
        repos.crew.remove_unavailability(profile.id, entry.id)
        ctx.audit(
            Event.CREW_UNAVAILABILITY_REMOVED,
            crew_profile_id=profile.id,
            data=_period(profile, entry.window),
        )


# Skill levels: Leads and Directors, never on themselves


def set_skill_level(
    ctx: ServiceContext, crew_profile_id: int, skill_id: int, level: int
) -> SkillLevel:
    """Add or change someone's level in one of the organisation's skills. Refused if it would
    leave them short of a requirement on an Active mission they're on."""
    with ctx.write() as repos:
        profile, skill_name, previous = _skill_target(ctx, repos, crew_profile_id, skill_id)
        if not MIN_LEVEL <= level <= MAX_LEVEL:
            raise InvalidInput(f"Skill level must be between {MIN_LEVEL} and {MAX_LEVEL}")
        _refuse_if_active_assignment_breaks(repos, profile, skill_id, skill_name, level)
        repos.crew.set_skill(profile.id, skill_id, level, updated_by=ctx.actor.user_id)
        ctx.audit(
            Event.CREW_SKILL_SET,
            crew_profile_id=profile.id,
            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "level": level,
                "previous_level": previous,
            },
        )
        return SkillLevel(skill_id, skill_name, level)


def remove_skill_level(ctx: ServiceContext, crew_profile_id: int, skill_id: int) -> None:
    with ctx.write() as repos:
        profile, skill_name, previous = _skill_target(ctx, repos, crew_profile_id, skill_id)
        found(previous, "Skill level")
        _refuse_if_active_assignment_breaks(repos, profile, skill_id, skill_name, None)
        repos.crew.remove_skill(profile.id, skill_id)
        ctx.audit(
            Event.CREW_SKILL_REMOVED,
            crew_profile_id=profile.id,
            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "previous_level": previous,
            },
        )


# Helpers


def _about(profile: CrewProfile) -> Context:
    """Permission context for a profile: the person is its user, not the profile id."""
    return Context(target_user_id=profile.user_id)


def _visible_profile(ctx: ServiceContext, crew_profile_id: int, action: Action) -> CrewProfile:
    """The profile, or NotFound if it's missing, another organisation's, or hidden from the
    caller."""
    profile = found(ctx.repos.crew.get(crew_profile_id), _CREW_MEMBER)
    ctx.authorize_view(action, _about(profile), _CREW_MEMBER)
    return profile


def _own_profile(ctx: ServiceContext, crew_profile_id: int) -> CrewProfile:
    """The caller's own profile. Someone else's they can see is Forbidden."""
    profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
    ctx.authorize(Action.EDIT_OWN_PROFILE, _about(profile))
    return profile


def _skill_target(
    ctx: ServiceContext, repos: Repos, crew_profile_id: int, skill_id: int
) -> tuple[CrewProfile, str, int | None]:
    """The profile whose level is changing, the skill's name, and the current level."""
    profile = _visible_profile(ctx, crew_profile_id, Action.VIEW_CREW)
    ctx.authorize(Action.SET_SKILL_LEVEL, _about(profile))
    skill = found(repos.skills.get(skill_id), "Skill")
    return profile, skill.name, repos.crew.skills(profile.id).get(skill_id)


def _refuse_if_active_assignment_breaks(
    repos: Repos, profile: CrewProfile, skill_id: int, skill_name: str, level: int | None
) -> None:
    broken = invalidated_by_skill_change(
        profile.display_name, skill_id, level, repos.facts.active_assignments(profile.id)
    )
    check(
        broken,
        f"Changing {profile.display_name}'s {skill_name} level would break their assignments "
        f"on active missions",
    )


def _overlap(
    profile: CrewProfile, mission_id: int, mission_name: str, busy: DateRange, wanted: DateRange
) -> Problem:
    shared = DateRange(max(busy.start, wanted.start), min(busy.end, wanted.end))
    return Problem(
        "overlap",
        f"{profile.display_name} has an accepted assignment on {mission_name} overlapping "
        f"{shared.start.isoformat()} to {shared.end.isoformat()}",
        {"crew_profile_id": profile.id, "mission_id": mission_id, "mission_name": mission_name},
    )


def _period(profile: CrewProfile, window: DateRange) -> dict[str, str]:
    return {
        "crew_name": profile.display_name,
        "start_date": window.start.isoformat(),
        "end_date": window.end.isoformat(),
    }


def _skill_names(repos: Repos) -> dict[int, str]:
    return {s.id: s.name for s in repos.skills.list()}


def _view(
    ctx: ServiceContext,
    repos: Repos,
    profile: CrewProfile,
    user: User,
    skill_names: Mapping[int, str],
) -> CrewView:
    skills = sorted(
        (
            SkillLevel(skill_id, skill_names[skill_id], level)
            for skill_id, level in repos.crew.skills(profile.id).items()
        ),
        key=lambda s: (s.skill_name.casefold(), s.skill_id),
    )
    return CrewView(
        crew_profile_id=profile.id,
        user_id=profile.user_id,
        name=profile.display_name,
        email=user.email,
        active=user.is_active,
        bio=profile.bio,
        skills=tuple(skills),
        unavailability=_unavailability(ctx, repos, profile),
    )


def _unavailability(
    ctx: ServiceContext, repos: Repos, profile: CrewProfile
) -> tuple[UnavailabilityView, ...]:
    """Dates for anyone who can see the profile; reasons only for Directors and the person."""
    show_reason = can(ctx.actor, Action.VIEW_UNAVAILABILITY_REASON, _about(profile))
    return tuple(
        UnavailabilityView(u.id, u.window, u.reason if show_reason else None)
        for u in repos.crew.unavailability(profile.id)
    )
"""The rules mission changes must keep, and how a change is recorded.

- Only an active Mission Lead can own a mission.
- A mission's live slots have different names.
- An edit can't break an open assignment: anyone it would make no longer eligible must be removed
  first, and crew are never removed automatically.
- A change to a Pending mission sends it back to Draft, audited with its cause.
"""

from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.eligibility import MissionEditKind, invalidated_by
from mission_control.domain.enums import MissionStatus, Role
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission, Slot, User
from mission_control.services.context import ServiceContext, return_to_draft
from mission_control.services.missions.inputs import SlotInput

# Owners and slot names


def require_owner(user: User) -> None:
    """Only an active Mission Lead can own a mission."""
    for problem in owner_problems(user):
        raise RuleViolation.of(problem)


def owner_problems(user: User) -> list[Problem]:
    """Why the user can't own a mission, if they can't: only an active Mission Lead can."""
    if user.role != Role.LEAD:
        message = f"{user.name} can't own a mission: only Mission Leads can"
    elif not user.is_active:
        message = f"{user.name} can't own a mission because they're deactivated"
    else:
        return []
    return [Problem("owner_not_active_lead", message, {"user_id": user.id})]


def refuse_taken_name(
    mission: Mission, slots: Sequence[Slot], name: str, slot_id: int | None = None
) -> None:
    """A mission's live slots have different names, ignoring case. `slot_id` is the slot being
    renamed, which may keep its own name."""
    taken = next(
        (s for s in slots if s.id != slot_id and _name_key(s.name) == _name_key(name)), None
    )
    if taken is not None:
        message = f"{mission.name} already has a slot called {taken.name}"
        raise RuleViolation(message, [Problem("already_exists", message, {"slot_id": taken.id})])


def repeated_name_problems(slots: Sequence[SlotInput]) -> list[Problem]:
    """A new mission's slots have different names, ignoring case. One problem per repeated
    name."""
    first_spelling: dict[str, str] = {}
    repeated: list[str] = []
    for s in slots:
        key = _name_key(s.name)
        if key not in first_spelling:
            first_spelling[key] = s.name.strip()
        elif first_spelling[key] not in repeated:
            repeated.append(first_spelling[key])
    return [Problem("already_exists", f"More than one slot is called {name}") for name in repeated]


def _name_key(name: str) -> str:
    """Slot names are compared ignoring case and surrounding spaces."""
    return name.strip().casefold()


# Edits that would break open assignments


def refuse_if_invalidated(
    repos: Repos,
    mission: Mission,
    edit: MissionEditKind,
    message: Callable[[list[str]], str],
    *,
    before: MissionEditKind | None = None,
) -> None:
    """Refuse an edit that would break open assignments. `message` gets the names of everyone
    affected, in roster order.

    `before` describes the mission as it is now, in the same terms as `edit`. Conflicts it
    already has don't count, so the edit is refused only for people it would make no longer
    eligible."""
    problems, names = invalidated(repos, mission, edit, before=before)
    if problems:
        raise RuleViolation(message(names), problems)


def invalidated(
    repos: Repos,
    mission: Mission,
    edit: MissionEditKind,
    *,
    before: MissionEditKind | None = None,
) -> tuple[list[Problem], list[str]]:
    """The open assignments the edit would break, and the names of everyone affected in roster
    order. Both are empty if the edit is safe. `before` is as for `refuse_if_invalidated`."""
    roster = repos.facts.roster(mission.id)
    problems = invalidated_by(edit, roster)
    if before is not None and problems:
        existing = {_conflict(p) for p in invalidated_by(before, roster)}
        problems = [p for p in problems if _conflict(p) not in existing]
    names = {e.crew.crew_profile_id: e.crew.name for e in roster}
    affected: list[int] = []
    for p in problems:
        ids = p.refs.get("crew_profile_ids") or [p.refs["crew_profile_id"]]
        affected += [i for i in ids if isinstance(i, int) and i not in affected]
    return problems, [names[i] for i in affected]


# What identifies a conflict's cause, so the same conflict is recognised before and after an
# edit: an overlap by the other mission and a shortfall by the skill, since the overlapping days
# and the level needed can move. An unavailability's message names its own period, which no
# mission edit changes.
_CAUSE_REF = MappingProxyType({"overlap": "mission_id", "skill_below_minimum": "skill_id"})


def _conflict(p: Problem) -> tuple[object, ...]:
    """Who, in which slot, and why."""
    cause = _CAUSE_REF.get(p.code)
    return (
        p.code,
        p.refs.get("crew_profile_id"),
        p.refs.get("slot_id"),
        p.refs[cause] if cause is not None else p.message,
    )


# Recording a change


def record_change(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    status: MissionStatus,
    event: Event,
    data: Mapping[str, object],
) -> None:
    """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
    and, if a Pending mission went back to Draft, that return with its cause."""
    ctx.audit(event, mission_id=mission.id, data=data)
    if status != mission.status:
        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))


# Wording


def join_names(names: Sequence[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def is_are(names: Sequence[str]) -> str:
    return "is" if len(names) == 1 else "are"
"""Creating a mission, renaming or moving it, and handing it to another Lead."""

from collections.abc import Sequence
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import DatesEdit
from mission_control.domain.enums import Action, MissionStatus, Role
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
from mission_control.domain.permissions import Context
from mission_control.services.context import (
    ServiceContext,
    check,
    found,
    mission_context,
    visible_mission,
)
from mission_control.services.missions.inputs import (
    SlotInput,
    date_problems,
    invalid,
    invalid_input,
    levels,
    name_problems,
    refuse_input,
    requirement_data,
    slot_label,
    slot_problems,
)
from mission_control.services.missions.loading import open_for_edit, reload, resolve_skills
from mission_control.services.missions.rules import (
    join_names,
    owner_problems,
    record_change,
    refuse_if_invalidated,
    repeated_name_problems,
    require_owner,
)
from mission_control.services.missions.views import MissionView, mission_view


def create_mission(
    ctx: ServiceContext,
    *,
    name: str,
    start: date,
    end: date,
    slots: Sequence[SlotInput],
    owner_id: int | None = None,
) -> MissionView:
    """A new Draft mission with its slots. A Lead creates missions for themselves; a Director
    names the Lead who will own it. The creator is recorded separately."""
    if owner_id is None and ctx.actor.role != Role.DIRECTOR:
        owner_id = ctx.actor.user_id
    with ctx.write() as repos:
        # The id as given: the permission rules compare it with the actor before anyone is looked
        # up. A Director who names nobody passes this check and is asked to name a Lead below.
        ctx.authorize(
            Action.CREATE_MISSION,
            Context(owner_id=ctx.actor.user_id if owner_id is None else owner_id),
        )
        owner = None if owner_id is None else found(repos.users.get(owner_id), "User")
        requirements = [resolve_skills(repos, s.requirements) for s in slots]

        problems = name_problems(name) + date_problems(start, end)
        if owner is None:
            problems.append(invalid("Name the Lead who will own the mission"))
        if not slots:
            problems.append(invalid("The mission needs at least one slot"))
        for s in slots:
            problems += slot_problems(slot_label(s.name), s.name, s.headcount, s.requirements)
        if problems or owner is None:
            raise invalid_input(problems)
        window = DateRange(start, end)
        repeated = repeated_name_problems(slots)
        problems = repeated + owner_problems(owner)
        if len(problems) == 1:
            message = problems[0].message
        elif problems == repeated:
            message = "Some slots share a name"
        else:
            message = f"{name.strip()} can't be created"
        check(problems, message)

        mission = repos.missions.create(name.strip(), window, owner.id, ctx.actor.user_id)
        for s, reqs in zip(slots, requirements, strict=True):
            repos.missions.add_slot(mission.id, s.name.strip(), s.headcount, levels(reqs))
        ctx.audit(
            Event.MISSION_CREATED,
            mission_id=mission.id,
            to_status=MissionStatus.DRAFT,
            data={
                "mission_name": mission.name,
                "owner_id": owner.id,
                "owner_name": owner.name,
                "start_date": window.start.isoformat(),
                "end_date": window.end.isoformat(),
                "slots": [
                    {
                        "slot_name": s.name.strip(),
                        "headcount": s.headcount,
                        "requirements": requirement_data(reqs),
                    }
                    for s, reqs in zip(slots, requirements, strict=True)
                ],
            },
        )
        return mission_view(repos, mission)


def update_mission(
    ctx: ServiceContext,
    mission_id: int,
    *,
    name: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> MissionView:
    """Rename or move the mission. Only its owner can. New dates are refused if they would make
    anyone on the roster no longer eligible. A Pending mission goes back to Draft if its dates
    change, but not for a new name alone."""
    with ctx.write() as repos:
        target = open_for_edit(ctx, repos, mission_id)
        mission, status = target.mission, target.status
        new_start = mission.window.start if start is None else start
        new_end = mission.window.end if end is None else end
        refuse_input(
            (name_problems(name) if name is not None else []) + date_problems(new_start, new_end)
        )
        window = DateRange(new_start, new_end)
        new_name = name.strip() if name is not None else mission.name

        changes: dict[str, list[str]] = {}
        if new_name != mission.name:
            changes["name"] = [mission.name, new_name]
        for key, old, new in (
            ("start_date", mission.window.start, window.start),
            ("end_date", mission.window.end, window.end),
        ):
            if old != new:
                changes[key] = [old.isoformat(), new.isoformat()]
        if not changes:
            return mission_view(repos, mission)

        if window == mission.window:
            status = mission.status  # a new name alone keeps the approval round going
        else:
            refuse_if_invalidated(
                repos,
                mission,
                DatesEdit(window),
                lambda names: (
                    f"Can't change the dates of {mission.name}: {join_names(names)} would no "
                    "longer be eligible. Remove them from the mission first."
                ),
                before=DatesEdit(mission.window),
            )

        repos.missions.update(mission.id, new_name, window)
        record_change(
            ctx,
            repos,
            mission,
            status,
            Event.MISSION_UPDATED,
            {"mission_name": new_name, "changes": changes},
        )
        return mission_view(repos, reload(repos, mission))


def transfer_ownership(ctx: ServiceContext, mission_id: int, new_owner_id: int) -> MissionView:
    """Directors hand a mission that isn't finished to another active Lead. A Pending mission
    goes back to Draft; an Active one stays Active, since its roster doesn't change."""
    with ctx.write() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        ctx.authorize(Action.TRANSFER, mission_context(repos, mission))
        problem = state_problem(mission.status, Action.TRANSFER)
        if problem is not None:
            raise StateConflict(problem)
        new_owner = found(repos.users.get(new_owner_id), "User")
        if new_owner.id == mission.owner_id:
            raise RuleViolation.of(
                Problem(
                    "already_owner",
                    f"{new_owner.name} already owns {mission.name}",
                    {"user_id": new_owner.id},
                )
            )
        require_owner(new_owner)
        status = mission_status_after(mission.status, Action.TRANSFER)
        old_owner = found(repos.users.get(mission.owner_id), "User")

        repos.missions.set_owner(mission.id, new_owner.id)
        record_change(
            ctx,
            repos,
            mission,
            status,
            Event.MISSION_TRANSFERRED,
            {
                "mission_name": mission.name,
                "from_owner_id": old_owner.id,
                "from_owner_name": old_owner.name,
                "to_owner_id": new_owner.id,
                "to_owner_name": new_owner.name,
            },
        )
        return mission_view(repos, reload(repos, mission))
```

</details>

<details>
<summary>↳ Result</summary>

```
src/mission_control/services:
__init__.py
admin.py
approvals.py
assignments.py
audit.py
auth.py
context.py
crew.py
inbox.py
matching.py
missions

src/mission_control/services/missions:
__init__.py
changes.py
inputs.py
lifecycle.py
loading.py
queries.py
rules.py
slots.py
views.py
"""Changing a mission's slots: adding one, renaming it or changing its headcount, replacing its
required skills, and removing it. Only the mission's owner can."""

from collections.abc import Mapping

from mission_control.domain.eligibility import SlotEdit, SlotRemoval
from mission_control.domain.errors import Problem
from mission_control.domain.events import Event
from mission_control.services.context import ServiceContext, check
from mission_control.services.missions.inputs import (
    SlotInput,
    levels,
    refuse_input,
    requirement_data,
    slot_label,
    slot_problems,
)
from mission_control.services.missions.loading import (
    open_for_edit,
    open_slot_for_edit,
    reload,
    resolve_skills,
)
from mission_control.services.missions.rules import (
    invalidated,
    is_are,
    join_names,
    record_change,
    refuse_if_invalidated,
    refuse_taken_name,
)
from mission_control.services.missions.views import MissionView, mission_view


def add_slot(ctx: ServiceContext, mission_id: int, slot: SlotInput) -> MissionView:
    """A new slot after the mission's last one."""
    with ctx.write() as repos:
        target = open_for_edit(ctx, repos, mission_id)
        mission = target.mission
        requirements = resolve_skills(repos, slot.requirements)
        refuse_input(
            slot_problems(slot_label(slot.name), slot.name, slot.headcount, slot.requirements)
        )
        refuse_taken_name(mission, repos.missions.slots(mission.id), slot.name)

        added = repos.missions.add_slot(
            mission.id, slot.name.strip(), slot.headcount, levels(requirements)
        )
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_ADDED,
            {
                "mission_name": mission.name,
                "slot_id": added.id,
                "slot_name": added.name,
                "headcount": added.headcount,
                "requirements": requirement_data(requirements),
            },
        )
        return mission_view(repos, reload(repos, mission))


def update_slot(
    ctx: ServiceContext,
    mission_id: int,
    slot_id: int,
    *,
    name: str | None = None,
    headcount: int | None = None,
) -> MissionView:
    """Rename a slot or change its headcount. A headcount below the crew already assigned to the
    slot is refused, naming them."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        label = name.strip() if name is not None and name.strip() else slot.name
        refuse_input(slot_problems(label, name, headcount, None, {"slot_id": slot.id}))
        new_name = name.strip() if name is not None else slot.name
        new_headcount = headcount if headcount is not None else slot.headcount

        changes: dict[str, list[object]] = {}
        if new_name != slot.name:
            changes["name"] = [slot.name, new_name]
        if new_headcount != slot.headcount:
            changes["headcount"] = [slot.headcount, new_headcount]
        if not changes:
            return mission_view(repos, mission)
        refuse_taken_name(mission, repos.missions.slots(mission.id), new_name, slot.id)
        refuse_if_invalidated(
            repos,
            mission,
            SlotEdit(slot.id, headcount=new_headcount),
            lambda names: (
                f"Can't lower the headcount of {slot.name} on {mission.name}: "
                f"{join_names(names)} {is_are(names)} assigned. Remove crew from the slot first."
            ),
        )

        repos.missions.update_slot(slot.id, new_name, new_headcount)
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_UPDATED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,
                "slot_name": new_name,
                "changes": changes,
            },
        )
        return mission_view(repos, reload(repos, mission))


def replace_requirements(
    ctx: ServiceContext, mission_id: int, slot_id: int, requirements: Mapping[int, int]
) -> MissionView:
    """Replace every required skill of a slot ({skill id: minimum level}). Refused if anyone
    assigned to the slot would no longer meet them; a shortfall they already had doesn't count."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        new = resolve_skills(repos, requirements)
        refuse_input(slot_problems(slot.name, None, None, requirements, {"slot_id": slot.id}))

        if levels(new) == levels(slot.requirements):
            return mission_view(repos, mission)
        refuse_if_invalidated(
            repos,
            mission,
            SlotEdit(slot.id, requirements=new),
            lambda names: (
                f"Can't change the requirements of {slot.name} on {mission.name}: "
                f"{join_names(names)} would no longer be eligible. Remove them from the "
                "mission first."
            ),
            before=SlotEdit(slot.id, requirements=slot.requirements),
        )

        repos.missions.replace_requirements(slot.id, levels(new))
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_REQUIREMENTS_CHANGED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,
                "slot_name": slot.name,
                "requirements": requirement_data(new),
                "previous_requirements": requirement_data(slot.requirements),
            },
        )
        return mission_view(repos, reload(repos, mission))


def remove_slot(ctx: ServiceContext, mission_id: int, slot_id: int) -> MissionView:
    """Remove a slot. Its past assignments keep their history. Refused while anyone is assigned
    to it, or if it's the mission's only slot."""
    with ctx.write() as repos:
        target = open_slot_for_edit(ctx, repos, mission_id, slot_id)
        mission, slot = target.mission, target.slot
        assigned, names = invalidated(repos, mission, SlotRemoval(slot.id))
        problems: list[Problem] = []
        if len(repos.missions.slots(mission.id)) == 1:
            problems.append(
                Problem(
                    "mission_needs_a_slot",
                    f"Can't remove {slot.name}: {mission.name} needs at least one slot",
                    {"slot_id": slot.id},
                )
            )
        problems += assigned
        if not assigned:
            message = problems[0].message if problems else ""
        elif len(problems) > len(assigned):  # the only slot, and occupied
            message = (
                f"Can't remove {slot.name} from {mission.name}: it's the mission's only slot, "
                f"and {join_names(names)} {is_are(names)} assigned to it"
            )
        else:
            message = (
                f"Can't remove {slot.name} from {mission.name} while {join_names(names)} "
                f"{is_are(names)} assigned to it. Remove them from the mission first."
            )
        check(problems, message)

        repos.missions.remove_slot(slot.id)
        record_change(
            ctx,
            repos,
            mission,
            target.status,
            Event.SLOT_REMOVED,
            {"mission_name": mission.name, "slot_id": slot.id, "slot_name": slot.name},
        )
        return mission_view(repos, reload(repos, mission))
"""Ending a mission: completing an Active one, or cancelling one that isn't finished. Either way
its assignments follow in the same transaction: completing it completes the accepted crew, and
cancelling it cancels every proposal and acceptance."""

from mission_control.domain.enums import Action
from mission_control.domain.errors import InvalidInput
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission
from mission_control.services.assignments import cascade_mission_end
from mission_control.services.context import ServiceContext, mission_context, visible_mission
from mission_control.services.missions.loading import reload
from mission_control.services.missions.views import MissionView, mission_view


def complete_mission(ctx: ServiceContext, mission_id: int) -> MissionView:
    """The owner or a Director completes an Active mission."""
    with ctx.write() as repos:
        mission = _open_to_end(ctx, repos, mission_id, Action.COMPLETE)
        return _end(ctx, repos, mission, Action.COMPLETE, Event.MISSION_COMPLETED, None)


def cancel_mission(ctx: ServiceContext, mission_id: int, reason: str | None) -> MissionView:
    """The owner or a Director cancels a mission that isn't finished, giving a reason."""
    with ctx.write() as repos:
        mission = _open_to_end(ctx, repos, mission_id, Action.CANCEL)
        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Cancelling {mission.name} needs a reason")
        return _end(ctx, repos, mission, Action.CANCEL, Event.MISSION_CANCELLED, given)


def _open_to_end(ctx: ServiceContext, repos: Repos, mission_id: int, action: Action) -> Mission:
    mission = visible_mission(ctx, repos, mission_id)
    ctx.authorize(action, mission_context(repos, mission))
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)
    return mission


def _end(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    action: Action,
    event: Event,
    reason: str | None,
) -> MissionView:
    """Move the mission to its final state, audit it, then carry its assignments along."""
    after = mission_status_after(mission.status, action)
    repos.missions.set_status(mission.id, after)
    ctx.audit(
        event,
        mission_id=mission.id,
        from_status=mission.status,
        to_status=after,
        reason=reason,
        data={"mission_name": mission.name},
    )
    cascade_mission_end(ctx, mission, after)
    return mission_view(repos, reload(repos, mission))
"""Missions: viewing them, creating them, editing their name, dates and slots, handing them to
another Lead, and completing or cancelling them.

Every change runs inside one write transaction, in this order:
1. find the mission and its slot (missing, hidden or another organisation's is NotFound);
2. check permission (Forbidden);
3. check the mission's state with `touch_for_change` (StateConflict);
4. find the other records named, such as the owner or the skills (NotFound);
5. check the input (InvalidInput, listing every mistake);
6. check the rules (RuleViolation);
7. write and audit.

Permission comes before the lookups in step 4, so a refused caller can't learn whether a user or
skill exists. A Pending mission whose dates, slots or owner change goes back to Draft and its
approval round stops counting; that return is audited with the change that caused it. A new name
alone leaves it Pending.

Modules: `queries` (list, view), `changes` (create, rename or move, transfer), `slots` (add,
edit, replace requirements, remove), `lifecycle` (complete, cancel), with `inputs`, `rules`,
`views` and `loading` behind them. Completing and cancelling don't go through `touch_for_change`:
they're allowed on an Active mission, and check their own state.
"""

from mission_control.services.missions.changes import (
    create_mission,
    transfer_ownership,
    update_mission,
)
from mission_control.services.missions.inputs import SlotInput
from mission_control.services.missions.lifecycle import cancel_mission, complete_mission
from mission_control.services.missions.queries import get_mission, list_missions
from mission_control.services.missions.slots import (
    add_slot,
    remove_slot,
    replace_requirements,
    update_slot,
)
from mission_control.services.missions.views import (
    ApprovalView,
    AssignmentView,
    MissionListItem,
    MissionView,
    SlotView,
)

__all__ = [
    "ApprovalView",
    "AssignmentView",
    "MissionListItem",
    "MissionView",
    "SlotInput",
    "SlotView",
    "add_slot",
    "cancel_mission",
    "complete_mission",
    "create_mission",
    "get_mission",
    "list_missions",
    "remove_slot",
    "replace_requirements",
    "transfer_ownership",
    "update_mission",
    "update_slot",
]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/services/assignments.py src/mission_control/services/approvals.py src/mission_control/services/matching.py
```

<details>
<summary>↳ Result</summary>

```
"""Assignments: the owner proposing crew for a mission's slots, the crew member's answer (accept,
decline, withdraw), the owner removing someone, each person's own list, and what happens to
assignments when their mission is completed or cancelled.

Each use case runs in one write transaction, in this order: load (anything missing, hidden or
another organisation's is not found), authorize, check the mission's and the assignment's state,
check input, check the rules, then write and audit with the names involved. A refusal writes
nothing.

Who sees what: crew see only their own assignments, so anyone else's is not found. Leads and
Directors see every assignment in their organisation, so acting on one that isn't theirs is
forbidden.

A roster change (propose, withdraw, remove) on a mission pending approval sends it back to Draft,
so its approval round stops counting. That return is audited straight after the change that
caused it.
"""

from collections.abc import Mapping
from types import MappingProxyType

from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import Action, AssignmentStatus, MissionStatus
from mission_control.domain.errors import InvalidInput, Problem
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import (
    StateConflict,
    assignment_problem,
    assignment_status_after,
    cascade,
    mission_status_after_assignment_action,
)
from mission_control.domain.permissions import Context
from mission_control.domain.records import SlotSpec
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    Assignment,
    AssignmentSummary,
    CrewProfile,
    Mission,
)
from mission_control.services.context import (
    ServiceContext,
    check,
    found,
    mission_context,
    return_to_draft,
    visible_mission,
)

A = AssignmentStatus

_ASSIGNMENT = "Assignment"
_SLOT = "Slot"
_CREW_MEMBER = "Crew member"

_EVENT: Mapping[Action, Event] = MappingProxyType(
    {
        Action.PROPOSE_CREW: Event.ASSIGNMENT_PROPOSED,
        Action.ACCEPT: Event.ASSIGNMENT_ACCEPTED,
        Action.DECLINE: Event.ASSIGNMENT_DECLINED,
        Action.WITHDRAW: Event.ASSIGNMENT_WITHDRAWN,
        Action.REMOVE_CREW: Event.ASSIGNMENT_REMOVED,
    }
)

_CASCADE_EVENT: Mapping[AssignmentStatus, Event] = MappingProxyType(
    {A.COMPLETED: Event.ASSIGNMENT_COMPLETED, A.CANCELLED: Event.ASSIGNMENT_CANCELLED}
)

_MISSION_ENDS = frozenset({MissionStatus.COMPLETED, MissionStatus.CANCELLED})


# The owner proposes


def propose(ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int) -> Assignment:
    """Propose someone for a place in one of the mission's slots. Only the mission's owner may,
    while it's in Draft or pending approval; a pending mission goes back to Draft.

    Refused, with every reason at once, if the slot has no open place, the person already holds
    an open assignment on this mission, or they aren't eligible (deactivated, short of a
    required skill, unavailable, or accepted on another mission with overlapping dates).
    Proposals elsewhere don't count: they block nothing. An owner may propose themselves, and
    must then accept like anyone else."""
    with ctx.write() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        slots = _slot_specs(repos, mission)
        slot = found(slots.get(slot_id), _SLOT)
        ctx.authorize(Action.PROPOSE_CREW, mission_context(repos, mission))
        _check_state(Action.PROPOSE_CREW, None, mission)
        # The person is looked up only once the actor may propose, so a refusal never
        # reveals whether a crew id exists.
        profile = found(repos.crew.get(crew_profile_id), _CREW_MEMBER)
        ctx.authorize_view(Action.VIEW_CREW, _about(profile), _CREW_MEMBER)
        return make_proposal(ctx, repos, mission, slots, slot, profile)


def make_proposal(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    slots: Mapping[int, SlotSpec],
    slot: SlotSpec,
    profile: CrewProfile,
) -> Assignment:
    """The checks and writes every proposal goes through, by hand or from the matcher. Call it
    inside `ctx.write()` once the caller has authorized the owner and checked the mission's
    state. `slots` are the mission's live slots with their current open places."""
    problems = [
        *_already_on_mission(repos, mission, slots, profile),
        *_slot_full(mission, slot),
        *_ineligibility(repos, mission, slot, profile),
    ]
    check(problems, f"{profile.display_name} can't be proposed as {slot.name} on {mission.name}")

    made = repos.assignments.create(mission.id, slot.id, profile.id, ctx.actor.user_id)
    _audit(ctx, Event.ASSIGNMENT_PROPOSED, made, None, A.PROPOSED, mission, slot, profile)
    _after_roster_change(ctx, repos, mission, Action.PROPOSE_CREW)
    return made


# The crew member answers


def accept(ctx: ServiceContext, assignment_id: int) -> Assignment:
    """Accept your own proposal while the mission is in Draft. Eligibility is checked again
    now, so an accepted assignment elsewhere with overlapping dates refuses it, naming that
    mission."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.ACCEPT, _about(profile))
        _check_state(Action.ACCEPT, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        check(
            _ineligibility(repos, mission, slot, profile),
            f"{profile.display_name} can't accept {slot.name} on {mission.name}",
        )
        return _change(ctx, repos, Action.ACCEPT, assignment, mission, slot, profile)


def decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:
    """Decline your own proposal while the mission is in Draft. The reason is optional; a blank
    one is stored as none."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.DECLINE, _about(profile))
        _check_state(Action.DECLINE, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        given = (reason or "").strip() or None
        return _change(ctx, repos, Action.DECLINE, assignment, mission, slot, profile, given)


def withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:
    """Withdraw from your own accepted assignment, giving a reason. Allowed while the mission is
    in Draft or pending approval; a pending mission goes back to Draft. An active mission's
    roster is frozen."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.WITHDRAW, _about(profile))
        _check_state(Action.WITHDRAW, assignment.status, mission)
        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Withdrawing from {mission.name} needs a reason")
        slot = _slot_of(repos, mission, assignment)
        return _change(ctx, repos, Action.WITHDRAW, assignment, mission, slot, profile, given)


# The owner removes


def remove(ctx: ServiceContext, assignment_id: int) -> Assignment:
    """Retract a proposal or remove accepted crew. Only the mission's owner may, while it's in
    Draft or pending approval; a pending mission goes back to Draft."""
    with ctx.write() as repos:
        assignment, mission, profile = _load(ctx, repos, assignment_id)
        ctx.authorize(Action.REMOVE_CREW, mission_context(repos, mission))
        _check_state(Action.REMOVE_CREW, assignment.status, mission)
        slot = _slot_of(repos, mission, assignment)
        return _change(ctx, repos, Action.REMOVE_CREW, assignment, mission, slot, profile)


# Your own assignments


def my_assignments(ctx: ServiceContext, pending: bool = False) -> list[AssignmentSummary]:
    """The caller's own assignments, newest first; with `pending`, only proposals still waiting
    for their reply. Someone without a crew profile has none."""
    if ctx.actor.crew_profile_id is None:
        return []
    with ctx.read() as repos:
        mine = repos.crew.history(ctx.actor.crew_profile_id)
    return [a for a in mine if a.status == A.PROPOSED] if pending else mine


# When a mission ends


def cascade_mission_end(
    ctx: ServiceContext, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:
    """Apply a mission's completion or cancellation to its assignments: completing it completes
    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything
    else is left as it is. Each change is written and audited as the acting user.

    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked
    the mission's own transition, so the assignments change in the same transaction as the
    mission and roll back with it. It does no permission or state checks of its own. Returns the
    changed assignments, in id order."""
    if final_status not in _MISSION_ENDS:
        raise ValueError(f"a mission ends completed or cancelled, not {final_status.value}")
    if not ctx.conn.in_transaction:
        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
    repos = ctx.repos
    slots = _slot_specs(repos, mission)
    changed = []
    for assignment in repos.missions.assignments(mission.id):
        to = cascade(final_status, assignment.status)
        if to == assignment.status:
            continue
        profile = found(repos.crew.get(assignment.crew_profile_id), _CREW_MEMBER)
        slot = found(slots.get(assignment.slot_id), _SLOT)
        repos.assignments.set_status(assignment.id, to, assignment.reason)
        _audit(ctx, _CASCADE_EVENT[to], assignment, assignment.status, to, mission, slot, profile)
        changed.append(found(repos.assignments.get(assignment.id), _ASSIGNMENT))
    return changed


# Loading


def _load(
    ctx: ServiceContext, repos: Repos, assignment_id: int
) -> tuple[Assignment, Mission, CrewProfile]:
    """The assignment, its mission and its crew member. Not found if it's missing, another
    organisation's, or a crew member's who isn't the caller."""
    assignment = found(repos.assignments.get(assignment_id), _ASSIGNMENT)
    profile = found(repos.crew.get(assignment.crew_profile_id), _ASSIGNMENT)
    ctx.authorize_view(Action.VIEW_ASSIGNMENT_HISTORY, _about(profile), _ASSIGNMENT)
    # Seeing the assignment is enough to see its mission's name and state, as in the crew
    # member's assignment history.
    mission = found(repos.missions.get(assignment.mission_id), _ASSIGNMENT)
    return assignment, mission, profile


def _slot_specs(repos: Repos, mission: Mission) -> dict[int, SlotSpec]:
    """The mission's live slots by id, with their open places."""
    return {s.id: s for s in repos.facts.slot_specs(mission.id)}


def _slot_of(repos: Repos, mission: Mission, assignment: Assignment) -> SlotSpec:
    """The slot of an open assignment. A slot can't be removed while it has open assignments,
    so it's always live once the state check has passed."""
    return found(_slot_specs(repos, mission).get(assignment.slot_id), _SLOT)


def _about(profile: CrewProfile) -> Context:
    """Permission context for someone's assignment: the person is the profile's user."""
    return Context(target_user_id=profile.user_id)


# Checks


def _check_state(action: Action, current: AssignmentStatus | None, mission: Mission) -> None:
    problem = assignment_problem(action, current, mission.status)
    if problem is not None:
        raise StateConflict(problem)


def _already_on_mission(
    repos: Repos, mission: Mission, slots: Mapping[int, SlotSpec], profile: CrewProfile
) -> list[Problem]:
    held = [
        a
        for a in repos.missions.assignments(mission.id, (A.PROPOSED, A.ACCEPTED))
        if a.crew_profile_id == profile.id
    ]
    if not held:
        return []
    existing = held[0]
    slot = slots.get(existing.slot_id)
    where = f" as {slot.name}" if slot else ""
    return [
        Problem(
            "already_assigned",
            f"{profile.display_name} is already {existing.status.value}{where} on {mission.name}",
            {"assignment_id": existing.id, "crew_profile_id": profile.id, "mission_id": mission.id},
        )
    ]


def _slot_full(mission: Mission, slot: SlotSpec) -> list[Problem]:
    if slot.open_places > 0:
        return []
    return [
        Problem(
            "slot_full", f"{slot.name} on {mission.name} has no open places", {"slot_id": slot.id}
        )
    ]


def _ineligibility(
    repos: Repos, mission: Mission, slot: SlotSpec, profile: CrewProfile
) -> list[Problem]:
    """Every reason the person can't fill the slot, with commitments on this mission left out."""
    person = found(repos.facts.candidate(profile.id, excluding_mission_id=mission.id), _CREW_MEMBER)
    return ineligibility_reasons(person, slot, mission.window)


# Writing


def _change(
    ctx: ServiceContext,
    repos: Repos,
    action: Action,
    assignment: Assignment,
    mission: Mission,
    slot: SlotSpec,
    profile: CrewProfile,
    reason: str | None = None,
) -> Assignment:
    """Move the assignment on by `action`, audit it, and send a pending mission back to Draft
    if the roster changed."""
    to = assignment_status_after(action)
    repos.assignments.set_status(assignment.id, to, reason)
    _audit(ctx, _EVENT[action], assignment, assignment.status, to, mission, slot, profile, reason)
    _after_roster_change(ctx, repos, mission, action)
    return found(repos.assignments.get(assignment.id), _ASSIGNMENT)


def _after_roster_change(
    ctx: ServiceContext, repos: Repos, mission: Mission, action: Action
) -> None:
    if mission_status_after_assignment_action(mission.status, action) != mission.status:
        return_to_draft(ctx, repos, mission, _EVENT[action], mission.name)


def _audit(
    ctx: ServiceContext,
    event: Event,
    assignment: Assignment,
    from_status: AssignmentStatus | None,
    to_status: AssignmentStatus,
    mission: Mission,
    slot: SlotSpec,
    profile: CrewProfile,
    reason: str | None = None,
) -> None:
    ctx.audit(
        event,
        mission_id=mission.id,
        assignment_id=assignment.id,
        crew_profile_id=profile.id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        data={
            "mission_name": mission.name,
            "slot_name": slot.name,
            "crew_name": profile.display_name,
        },
    )
"""The approval round: the owner submits a Draft mission, then Directors approve or reject it.

Each use case runs in one write transaction, in this order: load (anything missing, hidden or
another organisation's is not found), authorize, check the mission's state, check input, check
the rules, then write and audit. A refusal writes nothing.

Submitting starts a new round and saves the number of approvals it needs, so later changes to
the organisation's setting don't affect it. Approvals are counted per round: a rejection, or a
change that sends the mission back to Draft, ends the round, and resubmitting starts a fresh
one. An approval already given still counts if its Director is later deactivated or demoted.
"""

from mission_control.domain.approvals import (
    Approver,
    count_eligible_approvers,
    decision_problems,
    reaches_quorum,
)
from mission_control.domain.enums import Action, MissionStatus, Role
from mission_control.domain.errors import InvalidInput
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import (
    StateConflict,
    check_submit,
    mission_status_after,
    roster_problems,
    state_problem,
)
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission
from mission_control.services.context import (
    ServiceContext,
    check,
    mission_context,
    visible_mission,
)
from mission_control.services.missions.loading import reload
from mission_control.services.missions.views import MissionView, mission_view

_APPROVE = "approve"
_REJECT = "reject"


def submit(ctx: ServiceContext, mission_id: int) -> MissionView:
    """Send a Draft mission for approval. Refused, listing every problem at once, unless every
    place is filled, every proposal has been accepted, the accepted crew are still eligible, and
    enough Directors could approve it."""
    with ctx.write() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        about = mission_context(repos, mission)
        ctx.authorize(Action.SUBMIT, about)
        _check_state(mission, Action.SUBMIT)

        required = repos.organisation.get().required_approvals
        approvers = [
            Approver(u.id, u.role == Role.DIRECTOR, u.is_active) for u in repos.users.list()
        ]
        eligible = count_eligible_approvers(
            approvers, mission.created_by_id, about.rostered_user_ids
        )
        problems = check_submit(
            repos.facts.slot_specs(mission.id),
            repos.facts.roster(mission.id),
            mission.window,
            eligible,
            required,
        )
        check(problems, f"{mission.name} can't be submitted")

        repos.missions.start_round(mission.id, required)
        ctx.audit(
            Event.MISSION_SUBMITTED,
            mission_id=mission.id,
            from_status=mission.status,
            to_status=MissionStatus.PENDING_APPROVAL,
            data={
                "mission_name": mission.name,
                "round": mission.approval_round + 1,
                "approvals_required": required,
            },
        )
        return _view(repos, mission)


def approve(ctx: ServiceContext, mission_id: int) -> MissionView:
    """Approve a pending mission's current round. The roster is checked again first; if anyone
    is no longer eligible the approval is refused and nothing changes. The approval that brings
    the round to the number saved at submit makes the mission Active."""
    with ctx.write() as repos:
        mission = _open_round(ctx, repos, mission_id, Action.APPROVE)
        check(
            roster_problems(repos.facts.roster(mission.id), mission.window),
            f"{mission.name} can't be approved",
        )

        repos.approvals.record(
            mission.id, mission.approval_round, ctx.actor.user_id, _APPROVE, None
        )
        approved = sum(
            1
            for a in repos.approvals.for_round(mission.id, mission.approval_round)
            if a.decision == _APPROVE
        )
        required = mission.approvals_required
        if required is None:
            raise RuntimeError("a pending mission always has its required approvals saved")
        ctx.audit(
            Event.MISSION_APPROVED,
            mission_id=mission.id,
            data={
                "mission_name": mission.name,
                "round": mission.approval_round,
                "approvals": approved,
                "required": required,
            },
        )
        after = mission_status_after(
            mission.status, Action.APPROVE, reaches_quorum=reaches_quorum(approved, required)
        )
        if after != mission.status:
            repos.missions.set_status(mission.id, after)
            ctx.audit(
                Event.MISSION_ACTIVATED,
                mission_id=mission.id,
                from_status=mission.status,
                to_status=after,
                data={"mission_name": mission.name},
            )
        return _view(repos, mission)


def reject(ctx: ServiceContext, mission_id: int, reason: str | None) -> MissionView:
    """Reject a pending mission, giving a reason. The round ends and the mission goes back to
    Draft; its accepted crew stay accepted."""
    with ctx.write() as repos:
        mission = _open_round(ctx, repos, mission_id, Action.REJECT)
        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Rejecting {mission.name} needs a reason")

        repos.approvals.record(
            mission.id, mission.approval_round, ctx.actor.user_id, _REJECT, given
        )
        after = mission_status_after(mission.status, Action.REJECT)
        repos.missions.set_status(mission.id, after)
        ctx.audit(
            Event.MISSION_REJECTED,
            mission_id=mission.id,
            from_status=mission.status,
            to_status=after,
            reason=given,
            data={"mission_name": mission.name, "round": mission.approval_round},
        )
        return _view(repos, mission)


def _open_round(ctx: ServiceContext, repos: Repos, mission_id: int, action: Action) -> Mission:
    """The opening steps of a decision: find the mission, check the Director may decide it
    (not its creator, not on it), check it's pending, then that they haven't decided this round
    already."""
    mission = visible_mission(ctx, repos, mission_id)
    about = mission_context(repos, mission)
    ctx.authorize(action, about)
    _check_state(mission, action)
    decided = {a.director_id for a in repos.approvals.for_round(mission.id, mission.approval_round)}
    # Creator and roster were settled by authorize, so only "already decided" can be left.
    if problems := decision_problems(
        ctx.actor.user_id, mission.created_by_id, about.rostered_user_ids, decided
    ):
        raise StateConflict(problems[0])
    return mission


def _check_state(mission: Mission, action: Action) -> None:
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)


def _view(repos: Repos, mission: Mission) -> MissionView:
    return mission_view(repos, reload(repos, mission))
"""Matching: suggest crew for a draft mission's open places, and turn a suggestion into
proposals. A preview writes nothing; applying creates Proposed assignments, which crew still have
to accept.

The owner or a Director may preview; only the owner may apply. Applying works the suggestion out
again inside its own write transaction, so it's never stale, and each proposal goes through the
same checks as one made by hand. Candidates are the
organisation's crew, minus anyone holding an open assignment on the mission and anyone who
declined, withdrew or was removed from it. The suggestion carries each person's workload and
proficiency, which are what decided the pick.
"""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Action, AssignmentStatus
from mission_control.domain.lifecycle import StateConflict, state_problem
from mission_control.domain.matching import Suggestion, proficiency, suggest_roster
from mission_control.domain.permissions import Context, can
from mission_control.domain.records import CandidateFacts, SlotSpec
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Assignment, Mission
from mission_control.services.assignments import make_proposal
from mission_control.services.context import (
    ServiceContext,
    found,
    mission_context,
    visible_mission,
)

# Anyone holding one of these on the mission is never suggested for it again.
_LEFT_OUT = (
    AssignmentStatus.PROPOSED,
    AssignmentStatus.ACCEPTED,
    AssignmentStatus.DECLINED,
    AssignmentStatus.WITHDRAWN,
    AssignmentStatus.REMOVED,
)


@dataclass(frozen=True)
class SuggestedCrew:
    """One person suggested for one place, with the numbers that decided the pick."""

    crew_profile_id: int
    name: str
    workload: int  # mission-days of accepted assignments elsewhere; lower wins
    proficiency: int  # sum of their levels in the slot's required skills; breaks workload ties
    pick: int  # 1 for the matcher's first pick; the most constrained slot is filled first


@dataclass(frozen=True)
class SlotSuggestion:
    slot_id: int
    name: str
    open_places: int  # headcount minus open assignments; 0 means nothing to suggest
    suggested: tuple[SuggestedCrew, ...]  # in pick order
    unfilled: int  # open places left with no eligible candidate


@dataclass(frozen=True)
class MatchPreview:
    mission_id: int
    mission_name: str
    window: DateRange
    slots: tuple[SlotSuggestion, ...]  # every slot, in listed order
    can_apply: bool  # whether this actor may turn the suggestion into proposals (owner only)

    @property
    def open_places(self) -> int:
        return sum(s.open_places for s in self.slots)

    @property
    def unfilled_places(self) -> int:
        return sum(s.unfilled for s in self.slots)


def preview(ctx: ServiceContext, mission_id: int) -> MatchPreview:
    """The suggested crew for a draft mission's open places. Changes nothing."""
    with ctx.read() as repos:
        mission, about = _open(ctx, repos, mission_id, Action.PREVIEW_MATCH)
        slots, candidates, suggestion = _suggest(repos, mission)

    by_id = {c.crew_profile_id: c for c in candidates}
    chosen: dict[int, list[SuggestedCrew]] = {s.id: [] for s in slots}
    specs = {s.id: s for s in slots}
    for pick, placement in enumerate(suggestion.placements, start=1):
        person = by_id[placement.crew_profile_id]
        chosen[placement.slot_id].append(_suggested(person, specs[placement.slot_id], pick))
    unfilled = {u.slot_id: u.count for u in suggestion.unfilled}

    return MatchPreview(
        mission_id=mission.id,
        mission_name=mission.name,
        window=mission.window,
        slots=tuple(
            SlotSuggestion(
                slot_id=s.id,
                name=s.name,
                open_places=s.open_places,
                suggested=tuple(chosen[s.id]),
                unfilled=unfilled.get(s.id, 0),
            )
            for s in slots
        ),
        can_apply=can(ctx.actor, Action.APPLY_MATCH, about),
    )


def _suggested(person: CandidateFacts, slot: SlotSpec, pick: int) -> SuggestedCrew:
    return SuggestedCrew(
        crew_profile_id=person.crew_profile_id,
        name=person.name,
        workload=person.workload,
        proficiency=proficiency(person, slot),
        pick=pick,
    )


def apply(ctx: ServiceContext, mission_id: int) -> list[Assignment]:
    """Propose the suggested crew for a draft mission's open places, in pick order. Only the
    owner may. Places with no candidate stay empty; with nothing to suggest, nothing changes."""
    with ctx.write() as repos:
        mission, _ = _open(ctx, repos, mission_id, Action.APPLY_MATCH)
        _, _, suggestion = _suggest(repos, mission)
        made = []
        for placement in suggestion.placements:
            # Fresh slots each time, so a proposal sees the places the previous ones took.
            slots = {s.id: s for s in repos.facts.slot_specs(mission.id)}
            profile = found(repos.crew.get(placement.crew_profile_id), "Crew member")
            made.append(
                make_proposal(ctx, repos, mission, slots, slots[placement.slot_id], profile)
            )
        return made


def _open(
    ctx: ServiceContext, repos: Repos, mission_id: int, action: Action
) -> tuple[Mission, Context]:
    """Find the mission, check the actor may preview or apply, then that it's a draft."""
    mission = visible_mission(ctx, repos, mission_id)
    about = mission_context(repos, mission)
    ctx.authorize(action, about)
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)
    return mission, about


def _suggest(
    repos: Repos, mission: Mission
) -> tuple[list[SlotSpec], list[CandidateFacts], Suggestion]:
    """The mission's slots, the candidates for it, and the matcher's suggestion from them."""
    left_out = {a.crew_profile_id for a in repos.missions.assignments(mission.id, _LEFT_OUT)}
    candidates = [
        c
        for c in repos.facts.candidates(excluding_mission_id=mission.id)
        if c.crew_profile_id not in left_out
    ]
    slots = repos.facts.slot_specs(mission.id)
    return slots, candidates, suggest_roster(slots, candidates, mission.window)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/domain/eligibility.py src/mission_control/domain/approvals.py && grep -n "def \|StateConflict" src/mission_control/domain/lifecycle.py
```

<details>
<summary>↳ Result</summary>

```
"""Who can fill a slot, how loaded they are, and which edits would break existing assignments."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem
from mission_control.domain.records import (
    ActiveAssignment,
    AssignmentFact,
    CandidateFacts,
    Requirement,
    RosterEntry,
    SlotSpec,
)


def _span(window: DateRange) -> str:
    return f"{window.start.isoformat()} to {window.end.isoformat()}"


def ineligibility_reasons(
    person: CandidateFacts, slot: SlotSpec, window: DateRange
) -> list[Problem]:
    """Every reason `person` can't fill `slot` for `window`. Empty means eligible."""
    problems: list[Problem] = []
    ref = {"crew_profile_id": person.crew_profile_id, "slot_id": slot.id}

    if not person.active:
        problems.append(Problem("inactive", f"{person.name} is deactivated", ref))

    problems.extend(_skill_shortfalls(person, slot.requirements, ref))
    problems.extend(_availability_conflicts(person, window, ref))
    return problems


def is_eligible(person: CandidateFacts, slot: SlotSpec, window: DateRange) -> bool:
    return not ineligibility_reasons(person, slot, window)


def _availability_conflicts(
    person: CandidateFacts, window: DateRange, ref: dict[str, int | str]
) -> list[Problem]:
    """Unavailability or accepted assignments elsewhere that overlap `window`."""
    problems = []
    for blocked in person.unavailable:
        if blocked.overlaps(window):
            problems.append(
                Problem("unavailable", f"{person.name} is unavailable {_span(blocked)}", ref)
            )
    for other in person.accepted_elsewhere:
        if other.window.overlaps(window):
            shared = DateRange(
                max(other.window.start, window.start), min(other.window.end, window.end)
            )
            problems.append(
                Problem(
                    "overlap",
                    f"{person.name} has an accepted assignment on {other.mission_name} "
                    f"overlapping {_span(shared)}",
                    {**ref, "mission_id": other.mission_id, "mission_name": other.mission_name},
                )
            )
    return problems


def _skill_shortfalls(
    person: CandidateFacts, requirements: Iterable[Requirement], ref: dict[str, int | str]
) -> list[Problem]:
    problems = []
    for r in requirements:
        level = person.skills.get(r.skill_id)
        if level is None or level < r.min_level:
            have = (
                f"doesn't have {r.skill_name}" if level is None else (f"has {r.skill_name} {level}")
            )
            problems.append(
                Problem(
                    "skill_below_minimum",
                    f"{person.name} {have} (needs {r.min_level})",
                    {**ref, "skill_id": r.skill_id},
                )
            )
    return problems


# Workload


def workload(assignments: Iterable[AssignmentFact], excluding_mission_id: int | None) -> int:
    """Mission-days of accepted assignments on missions that aren't completed."""
    return sum(
        a.window.mission_days
        for a in assignments
        if a.assignment_status == AssignmentStatus.ACCEPTED
        and a.mission_status != MissionStatus.COMPLETED
        and a.mission_id != excluding_mission_id
    )


# Edits that would invalidate open assignments


@dataclass(frozen=True)
class SlotRemoval:
    slot_id: int


@dataclass(frozen=True)
class SlotEdit:
    slot_id: int
    headcount: int | None = None
    requirements: tuple[Requirement, ...] | None = None


@dataclass(frozen=True)
class DatesEdit:
    window: DateRange


MissionEditKind = SlotRemoval | SlotEdit | DatesEdit


def invalidated_by(edit: MissionEditKind, roster: Sequence[RosterEntry]) -> list[Problem]:
    """Every open assignment the edit would break. Empty means the edit is safe."""
    if isinstance(edit, DatesEdit):
        return [
            _in_slot(e, p)
            for e in roster
            for p in _availability_conflicts(e.crew, edit.window, _refs(e))
        ]

    in_slot = [e for e in roster if e.slot.id == edit.slot_id]

    if isinstance(edit, SlotRemoval):
        return [
            Problem(
                "slot_has_open_assignments",
                f"{e.slot.name}: {e.crew.name} is still assigned",
                _refs(e),
            )
            for e in in_slot
        ]

    problems: list[Problem] = []
    if edit.headcount is not None and edit.headcount < len(in_slot):
        names = _join_names([e.crew.name for e in in_slot])
        problems.append(
            Problem(
                "headcount_below_open_assignments",
                f"{in_slot[0].slot.name}: {names} are assigned, more than the new headcount "
                f"of {edit.headcount}",
                {
                    "slot_id": edit.slot_id,
                    "crew_profile_ids": [e.crew.crew_profile_id for e in in_slot],
                },
            )
        )
    if edit.requirements is not None:
        for e in in_slot:
            problems.extend(
                _in_slot(e, p) for p in _skill_shortfalls(e.crew, edit.requirements, _refs(e))
            )
    return problems


def _join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _refs(e: RosterEntry) -> dict[str, int | str]:
    """The records every problem about this assignment names."""
    return {
        "assignment_id": e.assignment_id,
        "crew_profile_id": e.crew.crew_profile_id,
        "slot_id": e.slot.id,
    }


def _in_slot(e: RosterEntry, p: Problem) -> Problem:
    """`p` with the slot's name in front of its message."""
    return Problem(p.code, f"{e.slot.name}: {p.message}", p.refs)


# Skill changes against Active assignments


def invalidated_by_skill_change(
    person_name: str,
    skill_id: int,
    new_level: int | None,
    active_assignments: Sequence[ActiveAssignment],
) -> list[Problem]:
    """A skill change is refused only if it breaks an assignment on an Active mission.
    `new_level=None` means the skill is being removed."""
    problems = []
    for a in active_assignments:
        for r in a.requirements:
            if r.skill_id == skill_id and (new_level or 0) < r.min_level:
                problems.append(
                    Problem(
                        "invalidates_active_assignment",
                        f"{person_name} needs {r.skill_name} {r.min_level} as {a.slot_name} "
                        f"on active mission {a.mission_name}",
                        {"mission_id": a.mission_id, "skill_id": skill_id},
                    )
                )
    return problems
"""Who may approve a mission, and when enough of them have."""

from collections.abc import Iterable, Set
from dataclasses import dataclass

from mission_control.domain.errors import Problem


@dataclass(frozen=True)
class Approver:
    user_id: int
    is_director: bool
    active: bool


def conflict_problems(
    user_id: int, created_by_id: int | None, rostered_user_ids: Set[int]
) -> list[Problem]:
    """Why this person is too close to the mission to approve it: they created it or are on it."""
    problems = []
    if user_id == created_by_id:
        problems.append(Problem("approver_is_creator", "You can't approve a mission you created"))
    if user_id in rostered_user_ids:
        problems.append(Problem("approver_is_rostered", "You can't approve a mission you're on"))
    return problems


def decision_problems(
    user_id: int,
    created_by_id: int | None,
    rostered_user_ids: Set[int],
    decided_this_round: Set[int],
) -> list[Problem]:
    """Why this Director can't decide this round: they created the mission, are on it, or have
    already decided. Empty means they still can."""
    problems = conflict_problems(user_id, created_by_id, rostered_user_ids)
    if user_id in decided_this_round:
        # A rejection ends the round, so anyone who has decided an open round approved it.
        problems.append(Problem("already_decided", "You've already approved this round"))
    return problems


def approver_problems(
    approver: Approver,
    created_by_id: int | None,
    rostered_user_ids: Set[int],
    decided_this_round: Set[int],
) -> list[Problem]:
    """Every reason `approver` can't approve or reject this round. Empty means they can."""
    if not approver.is_director:
        return [Problem("role_forbidden", "Only Directors can approve or reject missions")]
    return decision_problems(approver.user_id, created_by_id, rostered_user_ids, decided_this_round)


def count_eligible_approvers(
    people: Iterable[Approver], created_by_id: int | None, rostered_user_ids: Set[int]
) -> int:
    """Active Directors who didn't create the mission and aren't on it."""
    return sum(
        1
        for p in people
        if p.is_director
        and p.active
        and not conflict_problems(p.user_id, created_by_id, rostered_user_ids)
    )


def reaches_quorum(approvals_in_round: int, approvals_required: int) -> bool:
    """`approvals_in_round` counts approvals recorded this round, including the new one.
    `approvals_required` is the N saved at submit, not the organisation's current setting."""
    return approvals_in_round >= approvals_required
62:def _wrong_state(status: MissionStatus, doing: str) -> Problem:
70:class StateConflict(RuleViolation):
74:    def __init__(self, problem: Problem) -> None:
79:def _after_change(status: MissionStatus) -> MissionStatus:
84:def touch_for_change(status: MissionStatus) -> MissionStatus:
87:    can't be changed, so this raises `StateConflict`."""
89:        raise StateConflict(_wrong_state(status, _MISSION_VERB[Action.EDIT_MISSION]))
93:def _require_mission_action(action: Action) -> None:
98:def state_problem(status: MissionStatus, action: Action) -> Problem | None:
107:def mission_status_after(
190:def _require_assignment_action(action: Action) -> None:
195:def assignment_problem(
212:def assignment_status_after(action: Action) -> AssignmentStatus:
217:def mission_status_after_assignment_action(mission: MissionStatus, action: Action) -> MissionStatus:
222:def cascade(mission_final_status: MissionStatus, assignment: AssignmentStatus) -> AssignmentStatus:
234:def roster_problems(roster: Sequence[RosterEntry], window: DateRange) -> list[Problem]:
245:def check_submit(
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 1,130p src/mission_control/domain/lifecycle.py && cat src/mission_control/services/missions/loading.py src/mission_control/services/missions/views.py
```

<details>
<summary>↳ Result</summary>

```
"""Mission and assignment state machines, and the checks a mission must pass to be submitted."""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import Action, AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.records import RosterEntry, SlotSpec

M = MissionStatus
A = AssignmentStatus

FINAL = frozenset({M.COMPLETED, M.CANCELLED})


# The states each mission action may start from. Its keys are the mission actions. Previewing and
# applying a match are listed so their refusals share these codes, though neither changes the
# mission's status.
MISSION_ALLOWED_FROM: Mapping[Action, frozenset[MissionStatus]] = MappingProxyType(
    {
        Action.SUBMIT: frozenset({M.DRAFT}),
        Action.APPROVE: frozenset({M.PENDING_APPROVAL}),
        Action.REJECT: frozenset({M.PENDING_APPROVAL}),
        Action.TRANSFER: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.COMPLETE: frozenset({M.ACTIVE}),
        Action.CANCEL: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.EDIT_MISSION: frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        Action.PREVIEW_MATCH: frozenset({M.DRAFT}),
        Action.APPLY_MATCH: frozenset({M.DRAFT}),
    }
)

# How each mission action reads after "Can't ...", e.g. "Can't approve a mission in draft".
_MISSION_VERB: Mapping[Action, str] = MappingProxyType(
    {
        Action.SUBMIT: "submit",
        Action.APPROVE: "approve",
        Action.REJECT: "reject",
        Action.TRANSFER: "transfer",
        Action.COMPLETE: "complete",
        Action.CANCEL: "cancel",
        Action.EDIT_MISSION: "edit",
        Action.PREVIEW_MATCH: "suggest crew for",
        Action.APPLY_MATCH: "apply suggested crew to",
    }
)


# How each state reads after "a mission ...", e.g. "Can't approve a mission in draft".
_STATE_PHRASE: Mapping[MissionStatus, str] = MappingProxyType(
    {
        M.DRAFT: "in draft",
        M.PENDING_APPROVAL: "pending approval",
        M.COMPLETED: "that's completed",
        M.CANCELLED: "that's cancelled",
    }
)


def _wrong_state(status: MissionStatus, doing: str) -> Problem:
    """`doing` is the start of the sentence, e.g. "approve" or "withdraw from"."""
    if status == M.ACTIVE:
        return Problem("mission_frozen", f"Can't {doing} an active mission")
    code = "mission_final" if status in FINAL else "invalid_transition"
    return Problem(code, f"Can't {doing} a mission {_STATE_PHRASE[status]}")


class StateConflict(RuleViolation):
    """The mission's state doesn't allow the change. `problem` says why; its code and message
    become the refusal's own."""

    def __init__(self, problem: Problem) -> None:
        super().__init__(problem.message, [problem], code=problem.code)
        self.problem = problem


def _after_change(status: MissionStatus) -> MissionStatus:
    """A change to a pending mission voids its approval round; otherwise status holds."""
    return M.DRAFT if status == M.PENDING_APPROVAL else status


def touch_for_change(status: MissionStatus) -> MissionStatus:
    """The mission's status once a change to it is made. Every mutating service calls this
    first. Draft stays Draft and Pending goes back to Draft; an Active or finished mission
    can't be changed, so this raises `StateConflict`."""
    if status not in MISSION_ALLOWED_FROM[Action.EDIT_MISSION]:
        raise StateConflict(_wrong_state(status, _MISSION_VERB[Action.EDIT_MISSION]))
    return _after_change(status)


def _require_mission_action(action: Action) -> None:
    if action not in MISSION_ALLOWED_FROM:
        raise ValueError(f"{action!r} is not a mission action; use the assignment functions")


def state_problem(status: MissionStatus, action: Action) -> Problem | None:
    """Why mission `action` isn't allowed from `status`, or None if it is. Raises ValueError
    for an action that isn't a mission action."""
    _require_mission_action(action)
    if status in MISSION_ALLOWED_FROM[action]:
        return None
    return _wrong_state(status, _MISSION_VERB[action])


def mission_status_after(
    status: MissionStatus, action: Action, *, reaches_quorum: bool = False
) -> MissionStatus:
    """The mission's status once `action` succeeds. Check `state_problem` first. Previewing or
    applying a match leaves the status as it is."""
    if state_problem(status, action) is not None:
        raise ValueError(f"{_MISSION_VERB[action]} is not allowed from {status.value}")
    match action:
        case Action.SUBMIT:
            return M.PENDING_APPROVAL
        case Action.APPROVE:
            return M.ACTIVE if reaches_quorum else M.PENDING_APPROVAL
        case Action.REJECT:
            return M.DRAFT
        case Action.COMPLETE:
            return M.COMPLETED
        case Action.CANCEL:
            return M.CANCELLED
        case Action.EDIT_MISSION | Action.TRANSFER:
            return _after_change(status)
        case Action.PREVIEW_MATCH | Action.APPLY_MATCH:
            return status


"""Finding the records a mission use case works on, and the opening steps every edit shares."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.enums import Action, MissionStatus
from mission_control.domain.lifecycle import touch_for_change
from mission_control.domain.records import Requirement
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission, Slot
from mission_control.services.context import (
    ServiceContext,
    found,
    mission_context,
    visible_mission,
)


@dataclass(frozen=True)
class EditTarget:
    """What an edit works on, once it may go ahead. `status` is where the mission goes if the
    edit is made: Draft for a Pending mission, otherwise unchanged."""

    mission: Mission
    status: MissionStatus


@dataclass(frozen=True)
class SlotEditTarget(EditTarget):
    slot: Slot


def open_for_edit(ctx: ServiceContext, repos: Repos, mission_id: int) -> EditTarget:
    """The opening steps of every mission edit: find the mission, check the actor may edit it,
    then check its state."""
    mission = visible_mission(ctx, repos, mission_id)
    ctx.authorize(Action.EDIT_MISSION, mission_context(repos, mission))
    return EditTarget(mission, touch_for_change(mission.status))


def open_slot_for_edit(
    ctx: ServiceContext, repos: Repos, mission_id: int, slot_id: int
) -> SlotEditTarget:
    """The same, for an edit to one of the mission's slots. The slot is found before the
    permission check, like the mission: anyone who can see a mission can see its slots."""
    mission = visible_mission(ctx, repos, mission_id)
    slot = slot_of(repos, mission, slot_id)
    ctx.authorize(Action.EDIT_MISSION, mission_context(repos, mission))
    return SlotEditTarget(mission, touch_for_change(mission.status), slot)


def reload(repos: Repos, mission: Mission) -> Mission:
    return found(repos.missions.get(mission.id), "Mission")


def slot_of(repos: Repos, mission: Mission, slot_id: int) -> Slot:
    """A live slot of this mission; any other slot id is not found."""
    slot = repos.missions.get_slot(slot_id)
    if slot is None or slot.mission_id != mission.id:
        return found(None, "Slot")
    return slot


def resolve_skills(repos: Repos, levels: Mapping[int, int]) -> tuple[Requirement, ...]:
    """Requirements with their skill names. A skill outside the catalogue is not found."""
    return tuple(
        Requirement(skill_id, found(repos.skills.get(skill_id), "Skill").name, level)
        for skill_id, level in levels.items()
    )


def user_name(repos: Repos, user_id: int) -> str:
    return found(repos.users.get(user_id), "User").name
"""How a mission is shown to its viewers."""

from dataclasses import dataclass

from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.records import Requirement
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import Mission
from mission_control.services.missions.loading import user_name

_OPEN = frozenset({AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED})
# States reached through the current approval round, so its approvals are the live ones. A Draft
# mission's round was rejected or voided by a change, so its approvals no longer count.
_ROUND_IS_LIVE = frozenset(
    {MissionStatus.PENDING_APPROVAL, MissionStatus.ACTIVE, MissionStatus.COMPLETED}
)


@dataclass(frozen=True)
class SlotView:
    id: int
    position: int
    name: str
    headcount: int
    open_places: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class AssignmentView:
    id: int
    slot_id: int
    slot_name: str
    crew_profile_id: int
    crew_name: str
    status: AssignmentStatus
    reason: str | None


@dataclass(frozen=True)
class ApprovalView:
    director_id: int
    director_name: str
    decision: str
    reason: str | None


@dataclass(frozen=True)
class MissionListItem:
    """A mission as it appears in a list: the mission and its owner's name."""

    mission: Mission
    owner_name: str


@dataclass(frozen=True)
class MissionView:
    """A mission as its viewers see it: live slots in listed order, every assignment it has had,
    and the approvals of its current round (none while it's in Draft or cancelled)."""

    mission: Mission
    owner_name: str
    created_by_name: str
    slots: tuple[SlotView, ...]
    assignments: tuple[AssignmentView, ...]
    approvals: tuple[ApprovalView, ...]


def mission_view(repos: Repos, mission: Mission) -> MissionView:
    assignments = repos.missions.assignments(mission.id)
    crew_names = repos.missions.assignee_names(mission.id)
    slot_names = repos.missions.slot_names(mission.id)
    approvals = (
        repos.approvals.for_round(mission.id, mission.approval_round)
        if mission.status in _ROUND_IS_LIVE
        else []
    )

    def open_places(slot_id: int, headcount: int) -> int:
        taken = sum(1 for a in assignments if a.slot_id == slot_id and a.status in _OPEN)
        return headcount - taken

    return MissionView(
        mission=mission,
        owner_name=user_name(repos, mission.owner_id),
        created_by_name=user_name(repos, mission.created_by_id),
        slots=tuple(
            SlotView(
                s.id,
                s.position,
                s.name,
                s.headcount,
                open_places(s.id, s.headcount),
                s.requirements,
            )
            for s in repos.missions.slots(mission.id)
        ),
        assignments=tuple(
            AssignmentView(
                a.id,
                a.slot_id,
                slot_names[a.slot_id],
                a.crew_profile_id,
                crew_names[a.crew_profile_id],
                a.status,
                a.reason,
            )
            for a in assignments
        ),
        approvals=tuple(
            ApprovalView(a.director_id, user_name(repos, a.director_id), a.decision, a.reason)
            for a in approvals
        ),
    )
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/infra/repositories/facts.py src/mission_control/infra/repositories/mission_slots.py && cat src/mission_control/domain/records.py
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 1,60p src/mission_control/infra/repositories/missions.py && cat src/mission_control/infra/repositories/base.py src/mission_control/infra/repositories/__init__.py
```

<details>
<summary>↳ Result</summary>

```
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
"""A mission's slots and their skill requirements.

Slots are soft-deleted: a removed slot disappears from every list and lookup, but keeps its row,
so past assignments still show the slot they were in.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping

from mission_control.domain.records import Requirement
from mission_control.infra.repositories.base import NOW, Scoped
from mission_control.infra.repositories.models import Slot

_LIVE = "removed_at IS NULL"


class MissionSlots(Scoped):
    """Part of MissionRepo: reach these as `repos.missions.<method>`."""

    # Reading

    def slots(self, mission_id: int) -> list[Slot]:
        """Live slots in listed order, each with its requirements."""
        rows = self._all(
            f"SELECT * FROM slots WHERE org_id = :org AND mission_id = :mission_id AND {_LIVE}"
            " ORDER BY position",
            mission_id=mission_id,
        )
        requirements = self._requirements_by_slot(mission_id)
        return [_slot(r, requirements.get(r["id"], ())) for r in rows]

    def get_slot(self, slot_id: int) -> Slot | None:
        """A live slot by id, with its requirements."""
        r = self._one(
            f"SELECT * FROM slots WHERE org_id = :org AND id = :id AND {_LIVE}", id=slot_id
        )
        if r is None:
            return None
        return _slot(r, self._requirements_by_slot(r["mission_id"]).get(slot_id, ()))

    def slot_names(self, mission_id: int) -> dict[int, str]:
        """Names of every slot the mission has had, removed ones included, so past assignments
        still show the slot they were in."""
        rows = self._all(
            "SELECT id, name FROM slots WHERE org_id = :org AND mission_id = :mission_id",
            mission_id=mission_id,
        )
        return {r["id"]: r["name"] for r in rows}

    def _requirements_by_slot(self, mission_id: int) -> dict[int, tuple[Requirement, ...]]:
        rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        grouped: dict[int, list[Requirement]] = {}
        for r in rows:
            grouped.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return {slot_id: tuple(reqs) for slot_id, reqs in grouped.items()}

    # Writing

    def add_slot(
        self, mission_id: int, name: str, headcount: int, requirements: Mapping[int, int]
    ) -> Slot:
        """Append a slot after the last live one, with its {skill_id: min_level}."""
        cur = self._exec(
            f"""INSERT INTO slots(org_id, mission_id, name, headcount, position)
                VALUES (:org, :mission_id, :name, :headcount,
                        (SELECT coalesce(max(position), 0) + 1 FROM slots
                         WHERE org_id = :org AND mission_id = :mission_id AND {_LIVE}))""",
            mission_id=mission_id,
            name=name,
            headcount=headcount,
        )
        self._insert_requirements(cur.lastrowid, requirements)
        created = self.get_slot(cur.lastrowid)
        assert created is not None
        return created

    def update_slot(self, slot_id: int, name: str, headcount: int) -> bool:
        return self._changed(
            f"UPDATE slots SET name = :name, headcount = :headcount"
            f" WHERE org_id = :org AND id = :id AND {_LIVE}",
            name=name,
            headcount=headcount,
            id=slot_id,
        )

    def replace_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> bool:
        """Swap a live slot's requirements for {skill_id: min_level}. False if no such slot."""
        if self.get_slot(slot_id) is None:
            return False
        self._exec(
            "DELETE FROM slot_requirements WHERE org_id = :org AND slot_id = :slot_id",
            slot_id=slot_id,
        )
        self._insert_requirements(slot_id, requirements)
        return True

    def remove_slot(self, slot_id: int) -> bool:
        """Soft delete: the slot disappears but its past assignments keep their history."""
        return self._changed(
            f"UPDATE slots SET removed_at = {NOW} WHERE org_id = :org AND id = :id AND {_LIVE}",
            id=slot_id,
        )

    def _insert_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> None:
        for skill_id, min_level in requirements.items():
            self._exec(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (:org, :slot_id, :skill_id, :min_level)",
                slot_id=slot_id,
                skill_id=skill_id,
                min_level=min_level,
            )


def _slot(r: sqlite3.Row, requirements: tuple[Requirement, ...]) -> Slot:
    return Slot(r["id"], r["mission_id"], r["name"], r["headcount"], r["position"], requirements)
"""Plain facts the domain rules work on. Services build these from the database."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus

# The range of a skill level, whether held by a person or required by a slot.
MIN_LEVEL, MAX_LEVEL = 1, 5


@dataclass(frozen=True)
class Requirement:
    skill_id: int
    skill_name: str
    min_level: int


@dataclass(frozen=True)
class SlotSpec:
    id: int
    position: int
    name: str
    open_places: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class Commitment:
    """An accepted assignment on another non-final mission."""

    mission_id: int
    mission_name: str
    window: DateRange


@dataclass(frozen=True)
class CandidateFacts:
    crew_profile_id: int
    name: str
    active: bool
    skills: Mapping[int, int]  # skill_id -> level
    unavailable: tuple[DateRange, ...]
    accepted_elsewhere: tuple[Commitment, ...]
    workload: int


@dataclass(frozen=True)
class RosterEntry:
    """A proposed or accepted assignment on the mission being checked, edited or submitted.
    `crew.accepted_elsewhere` must exclude this mission."""

    assignment_id: int
    slot: SlotSpec
    crew: CandidateFacts
    status: AssignmentStatus


@dataclass(frozen=True)
class AssignmentFact:
    """One of a person's assignments, as counted towards their workload."""

    mission_id: int
    mission_status: MissionStatus
    assignment_status: AssignmentStatus
    window: DateRange


@dataclass(frozen=True)
class ActiveAssignment:
    """An accepted assignment on an Active mission."""

    mission_id: int
    mission_name: str
    slot_name: str
    requirements: tuple[Requirement, ...]
```

</details>

<details>
<summary>↳ Result</summary>

```
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

    def with_status(self, status: MissionStatus) -> list[Mission]:
        """The organisation's missions in one status, soonest first."""
        rows = self._all(
            f"SELECT * FROM missions WHERE org_id = :org AND status = :status {_ORDER}",
            status=status,
        )
        return [_mission(r) for r in rows]

    # Visibility

"""Shared plumbing for the tenant-scoped repositories. The caller's org is always bound by
name as `:org`, so a statement reads `org_id = :org` wherever the filter sits."""

import sqlite3
from collections.abc import Iterable
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus

# A crew member is "on" a mission while they hold an open or completed assignment on it.
ON_MISSION = (AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED, AssignmentStatus.COMPLETED)
OPEN = (AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED)
FINAL = (MissionStatus.COMPLETED, MissionStatus.CANCELLED)
# The current UTC time in the same format as the schema's column defaults.
NOW = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def in_list(prefix: str, values: Iterable[object]) -> tuple[str, dict[str, object]]:
    """Named placeholders for an IN list: (":s0, :s1", {"s0": ..., "s1": ...})."""
    params = {f"{prefix}{i}": v for i, v in enumerate(values)}
    return ", ".join(f":{name}" for name in params), params


def window(row: sqlite3.Row) -> DateRange:
    return DateRange(date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"]))


class Scoped:
    def __init__(self, conn: sqlite3.Connection, org_id: int) -> None:
        self._conn = conn
        self._org = org_id

    def _params(self, params: dict[str, object]) -> dict[str, object]:
        if "org" in params:
            raise ValueError("`org` is bound from the repository, not passed in")
        return {"org": self._org, **params}

    def _one(self, sql: str, **params: object) -> sqlite3.Row | None:
        return self._conn.execute(sql, self._params(params)).fetchone()

    def _all(self, sql: str, **params: object) -> list[sqlite3.Row]:
        return self._conn.execute(sql, self._params(params)).fetchall()

    def _exec(self, sql: str, **params: object) -> sqlite3.Cursor:
        return self._conn.execute(sql, self._params(params))

    def _changed(self, sql: str, **params: object) -> bool:
        """Run an UPDATE or DELETE aimed at one row; True if it changed that row. False means
        the row is missing or belongs to another organisation."""
        return self._exec(sql, **params).rowcount == 1
"""Tenant-scoped data access. All SQL lives here, and every statement filters on org_id.

Parameters are bound by name and the caller's org is always `:org`, so a statement reads
`org_id = :org` wherever the filter sits; placeholder order can't bind another tenant's id.

Build one `Repos(conn, org_id)` per request from the authenticated actor's organisation.
Looking up another organisation's id returns None, exactly like a missing id.
"""

import sqlite3

from mission_control.infra.repositories.approvals import ApprovalRepo
from mission_control.infra.repositories.assignments import AssignmentRepo
from mission_control.infra.repositories.audit import AuditRepo
from mission_control.infra.repositories.crew import CrewRepo
from mission_control.infra.repositories.facts import FactsRepo
from mission_control.infra.repositories.missions import MissionRepo
from mission_control.infra.repositories.organisations import OrganisationRepo
from mission_control.infra.repositories.skills import SkillRepo
from mission_control.infra.repositories.users import UserRepo

__all__ = [
    "ApprovalRepo",
    "AssignmentRepo",
    "AuditRepo",
    "CrewRepo",
    "FactsRepo",
    "MissionRepo",
    "OrganisationRepo",
    "Repos",
    "SkillRepo",
    "UserRepo",
]


class Repos:
    """All repositories for one organisation, built from the authenticated actor."""

    def __init__(self, conn: sqlite3.Connection, org_id: int) -> None:
        self.org_id = org_id
        self.organisation = OrganisationRepo(conn, org_id)
        self.users = UserRepo(conn, org_id)
        self.crew = CrewRepo(conn, org_id)
        self.skills = SkillRepo(conn, org_id)
        self.missions = MissionRepo(conn, org_id)
        self.assignments = AssignmentRepo(conn, org_id)
        self.approvals = ApprovalRepo(conn, org_id)
        self.audit = AuditRepo(conn, org_id)
        self.facts = FactsRepo(conn, org_id)
```

</details>

### 🤖 Claude · 2026-10-12 05:20:06 UTC

Now the CLI side and the history renderer.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "data\b\|data\[\|data.get\|\"data\"" src/mission_control/cli/ | head -40; grep -rn "from_\|to_owner\|previous\|changes" src/mission_control/cli/ src/mission_control/api | head -40
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/cli/config.py:43:            data = json.loads(self.path.read_text(encoding="utf-8"))
src/mission_control/cli/config.py:46:        if not isinstance(data, dict):
src/mission_control/cli/config.py:48:        token = data.get("token")
src/mission_control/cli/config.py:51:        expires_at = data.get("expires_at")
src/mission_control/cli/config.py:54:            email=str(data.get("email") or ""),
src/mission_control/cli/render.py:155:    """Writes data to stdout and messages to stderr, each styled for its own stream."""
src/mission_control/cli/render.py:198:    def json(self, data: Any) -> None:
src/mission_control/cli/render.py:199:        self.line(json.dumps(data, indent=2, ensure_ascii=False))
src/mission_control/cli/render.py:210:        self.out.flush()  # keep data and messages in order when stdout is a pipe
src/mission_control/cli/main.py:6:from importlib.metadata import PackageNotFoundError, version
src/mission_control/cli/commands/missions.py:306:    # event: (with the names from its data, without them)
src/mission_control/cli/commands/missions.py:334:        return named.format_map(entry.get("data") or {})
src/mission_control/cli/commands/account.py:138:    data = env.api().get("/me/inbox")
src/mission_control/cli/commands/account.py:140:        env.term.json(data)
src/mission_control/cli/commands/account.py:143:    proposals = data.get("proposals") or []
src/mission_control/cli/commands/account.py:144:    approvals = data.get("approvals") or []
src/mission_control/cli/commands/account.py:145:    missions = data.get("missions") or []
src/mission_control/cli/commands/account.py:51:    _end_previous_session(env)
src/mission_control/cli/commands/account.py:63:def _end_previous_session(env: Env) -> None:
src/mission_control/cli/commands/missions.py:315:    "mission.transferred": ("Handed the mission to {to_owner_name}", "Changed the owner"),
src/mission_control/api/app.py:20:    config = settings if settings is not None else Settings.from_env(os.environ)
src/mission_control/api/errors.py:124:    "int_from_float": "{field} must be a whole number",
src/mission_control/api/errors.py:129:    "date_from_datetime_parsing": "{field} must be a date (YYYY-MM-DD)",
src/mission_control/api/errors.py:130:    "date_from_datetime_inexact": "{field} must be a date (YYYY-MM-DD)",
src/mission_control/api/schemas/missions.py:228:    from_status: str | None
src/mission_control/api/schemas/missions.py:243:            from_status=e.from_status,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 280,380p src/mission_control/cli/commands/missions.py; sed -n 215,247p src/mission_control/api/schemas/missions.py; cat src/mission_control/services/audit.py
```

<details>
<summary>↳ Result</summary>

```
                requirements_text(s["requirements"]),
                "full" if s["open_places"] <= 0 else f"{s['open_places']} of {s['headcount']} open",
            ]
            for s in mission["slots"]
        ],
    )
    term.line()
    crew = mission.get("assignments") or []
    if crew:
        term.table(
            ["Assignment", "Crew", "Slot", "Status"],
            [[str(a["id"]), a["crew_name"], a["slot_name"], assignment_status(a)] for a in crew],
        )
    else:
        term.line("No crew proposed yet.")
    required = mission.get("approvals_required")
    if mission["status"] in ("pending_approval", "active", "completed") and required:
        approvers = [
            a["director_name"] for a in mission.get("approvals") or [] if a["decision"] == "approve"
        ]
        names = f" ({join_names(approvers)})" if approvers else ""
        term.line()
        term.line(f"Approvals: {len(approvers)} of {required}{names}")


_EVENTS: dict[str, tuple[str, str]] = {
    # event: (with the names from its data, without them)
    "mission.created": ("Created the mission", "Created the mission"),
    "mission.updated": ("Edited the mission", "Edited the mission"),
    "mission.submitted": ("Submitted for approval", "Submitted for approval"),
    "mission.approved": ("Approved", "Approved"),
    "mission.rejected": ("Rejected", "Rejected"),
    "mission.activated": ("Mission became active", "Mission became active"),
    "mission.completed": ("Completed", "Completed"),
    "mission.cancelled": ("Cancelled", "Cancelled"),
    "mission.transferred": ("Handed the mission to {to_owner_name}", "Changed the owner"),
    "mission.returned_to_draft": ("Mission went back to Draft", "Mission went back to Draft"),
    "slot.added": ("Added slot {slot_name}", "Added a slot"),
    "slot.updated": ("Changed slot {slot_name}", "Changed a slot"),
    "slot.requirements_changed": ("Changed the skills for {slot_name}", "Changed a slot's skills"),
    "slot.removed": ("Removed slot {slot_name}", "Removed a slot"),
    "assignment.proposed": ("Proposed {crew_name} for {slot_name}", "Proposed crew"),
    "assignment.accepted": ("Accepted {slot_name}", "Accepted a proposal"),
    "assignment.declined": ("Declined {slot_name}", "Declined a proposal"),
    "assignment.withdrawn": ("Withdrew from {slot_name}", "Withdrew"),
    "assignment.removed": ("Removed {crew_name} from {slot_name}", "Removed crew"),
    "assignment.completed": ("{crew_name}'s assignment completed", "Assignment completed"),
    "assignment.cancelled": ("{crew_name}'s assignment cancelled", "Assignment cancelled"),
}


def _event_text(entry: dict[str, Any]) -> str:
    named, plain = _EVENTS.get(entry["event"], (entry["event"], entry["event"]))
    try:
        return named.format_map(entry.get("data") or {})
    except (KeyError, IndexError, ValueError):
        return plain


@command(app, "history", example="mc missions history 1")
def history(ctx: typer.Context, mission_id: MissionId, json_output: Json = False) -> None:
    """Show who changed a mission, what they did and when."""
    env = start(ctx, json_output)
    with _refusals(mission_id):
        entries = env.api().get(f"/missions/{mission_id}/history")
    if json_output:
        env.term.json(entries)
        return
    if not entries:
        env.term.line("Nothing has happened to this mission yet.")
        return
    with_reasons = any(e.get("reason") for e in entries)
    env.term.table(
        ["When (UTC)", "Who", "What"] + (["Reason"] if with_reasons else []),
        [
            [
                format_timestamp(e["created_at"]),
                e.get("actor_name") or str(e.get("actor_id")),
                _event_text(e),
            ]
            + ([e.get("reason") or ""] if with_reasons else [])
            for e in entries
        ],
    )


# Edit and slots


@command(app, "edit", example="mc missions edit 1 --end 2027-03-12")
def edit(
    ctx: typer.Context,
    mission_id: MissionId,
    name: NewName = None,
    start_date: NewStart = None,
    end_date: NewEnd = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Change a mission's name or dates. Owner only.

    }


class HistoryEntryOut(BaseModel):
    """One event in a mission's history: who did what, when, and the names at the time."""

    id: int
    created_at: datetime
    actor_id: int
    actor_name: str
    event: str
    assignment_id: int | None
    crew_profile_id: int | None
    from_status: str | None
    to_status: str | None
    reason: str | None
    data: Mapping[str, object]

    @classmethod
    def of(cls, e: AuditEntry) -> "HistoryEntryOut":
        return cls(
            id=e.id,
            created_at=e.at,
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            event=e.event,
            assignment_id=e.assignment_id,
            crew_profile_id=e.crew_profile_id,
            from_status=e.from_status,
            to_status=e.to_status,
            reason=e.reason,
            data=dict(e.data),
        )
"""A mission's history: every state change, approval, rejection and assignment response, with
who did it, when, and any reason. Anyone who can see the mission can see its history."""

from mission_control.domain.enums import Action
from mission_control.infra.repositories.models import AuditEntry
from mission_control.services.context import ServiceContext, mission_context, visible_mission


def mission_history(ctx: ServiceContext, mission_id: int) -> list[AuditEntry]:
    """The mission's events, oldest first. A mission the actor can't see is not found."""
    with ctx.read() as repos:
        mission = visible_mission(ctx, repos, mission_id)
        ctx.authorize_view(Action.VIEW_MISSION, mission_context(repos, mission), "Mission")
        return repos.audit.for_mission(mission.id)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "\.data\b\|data\[\|\.data\.get\|previous_\|from_name\|to_name\|from_role\|to_role\|from_owner\|to_owner\|\"from\"\|\"to\"" src tests docs --include=*.py --include=*.md | grep -v "from_status\|to_status" | head -80
```

<details>
<summary>↳ Result</summary>

```
(eval):1: no matches found: --include=*.py
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn '\.data\b\|data\[\|\.data\.get\|previous_\|from_name\|to_name\|from_role\|to_role\|from_owner\|to_owner\|"from"\|"to"\|"changes"' src tests docs README.md | grep -v "from_status\|to_status" | head -80
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/cli/commands/account.py:51:    _end_previous_session(env)
src/mission_control/cli/commands/account.py:63:def _end_previous_session(env: Env) -> None:
src/mission_control/cli/commands/missions.py:315:    "mission.transferred": ("Handed the mission to {to_owner_name}", "Changed the owner"),
src/mission_control/api/schemas/missions.py:246:            data=dict(e.data),
src/mission_control/services/admin.py:57:            data={"from": current.required_approvals, "to": n},
src/mission_control/services/admin.py:146:                "from_role": user.role,
src/mission_control/services/admin.py:147:                "to_role": role,
src/mission_control/services/admin.py:280:        to_name = _required(name, "skill name") if name is not None else skill.name
src/mission_control/services/admin.py:282:        if (to_name, to_category) == (skill.name, skill.category):
src/mission_control/services/admin.py:284:        clash = repos.skills.by_name(to_name)
src/mission_control/services/admin.py:287:        repos.skills.update(skill.id, to_name, to_category)
src/mission_control/services/admin.py:292:                "from_name": skill.name,
src/mission_control/services/admin.py:293:                "to_name": to_name,
src/mission_control/services/crew.py:127:            data={"crew_name": name, "previous_name": profile.display_name},
src/mission_control/services/crew.py:202:                "previous_level": previous,
src/mission_control/services/crew.py:220:                "previous_level": previous,
src/mission_control/services/missions/changes.py:168:            {"mission_name": new_name, "changes": changes},
src/mission_control/services/missions/changes.py:204:                "from_owner_id": old_owner.id,
src/mission_control/services/missions/changes.py:205:                "from_owner_name": old_owner.name,
src/mission_control/services/missions/changes.py:206:                "to_owner_id": new_owner.id,
src/mission_control/services/missions/changes.py:207:                "to_owner_name": new_owner.name,
src/mission_control/services/missions/slots.py:113:                "changes": changes,
src/mission_control/services/missions/slots.py:156:                "previous_requirements": requirement_data(slot.requirements),
src/mission_control/services/missions/rules.py:151:        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))
tests/unit/domain/test_permissions.py:118:def test_ac7_after_transfer_the_new_owner_can_edit_and_the_previous_owner_cannot():
tests/integration/test_auth.py:12:from mission_control.seed.data import DEMO_PASSWORD
tests/integration/test_missions_service.py:214:    assert data["mission_name"] == "Lunar Relay"
tests/integration/test_missions_service.py:215:    assert data["owner_name"] == "Lee Park"
tests/integration/test_missions_service.py:216:    assert [s["slot_name"] for s in data["slots"]] == ["Commander", "Engineer"]
tests/integration/test_missions_service.py:547:    assert data["mission_name"] == "Gateway Resupply II"
tests/integration/test_missions_service.py:548:    assert data["changes"] == {
tests/integration/test_missions_service.py:620:        "changes": {"name": ["Deep Space Comms Upgrade", "Deep Space Comms Upgrade II"]},
tests/integration/test_missions_service.py:764:    assert data["mission_name"] == "Lunar Gateway Resupply"
tests/integration/test_missions_service.py:765:    assert data["slot_name"] == "Medic"
tests/integration/test_missions_service.py:766:    assert data["headcount"] == 1
tests/integration/test_missions_service.py:767:    assert data["requirements"] == [
tests/integration/test_missions_service.py:866:    assert data["slot_id"] == COMMANDER
tests/integration/test_missions_service.py:867:    assert data["changes"] == {"name": ["Commander", "Mission Commander"], "headcount": [1, 2]}
tests/integration/test_missions_service.py:958:    assert data["slot_name"] == "Commander"
tests/integration/test_missions_service.py:959:    assert data["requirements"] == [
tests/integration/test_missions_service.py:963:    assert data["previous_requirements"] == [
tests/integration/test_missions_service.py:1097:    assert (event, data["slot_name"], data["slot_id"]) == ("slot.removed", "Commander", COMMANDER)
tests/integration/test_missions_service.py:1251:        "from_owner_id": LEE.user_id,
tests/integration/test_missions_service.py:1252:        "from_owner_name": "Lee Park",
tests/integration/test_missions_service.py:1253:        "to_owner_id": NORA.user_id,
tests/integration/test_missions_service.py:1254:        "to_owner_name": "Nora Quinn",
tests/integration/test_mission_history.py:81:    assert [h.data["crew_name"] for h in history[1:4]] == ["Ana", "Chen", "Dana"]
tests/cli/test_readme_smoke.py:29:from mission_control.seed.data import DEMO_PASSWORD
tests/integration/test_crew_service.py:202:    assert data == {"crew_name": "Benji", "previous_name": "Ben"}
tests/integration/test_crew_service.py:465:    assert data == {"crew_name": "Ana", "skill_name": "Piloting", "level": 3, "previous_level": 5}
tests/integration/test_crew_service.py:497:    assert last_audit(seeded_db)[4]["previous_level"] is None
tests/integration/test_crew_service.py:505:    assert data == {"crew_name": "Ben", "skill_name": "EVA", "previous_level": 3}
tests/cli/test_cli_auth.py:80:def test_m16_login_again_ends_the_previous_session_on_the_server(mc, api):
tests/cli/test_cli_auth.py:97:def test_m16_login_again_ignores_a_previous_session_the_server_already_ended(mc, api):
tests/cli/test_cli_auth.py:110:def test_m16_a_failed_login_keeps_the_previous_session(mc, api):
tests/integration/test_seed.py:5:from mission_control.seed.data import DEMO_PASSWORD
tests/api/conftest.py:15:from mission_control.seed.data import DEMO_PASSWORD
tests/integration/test_admin_service.py:82:        (1, "org.required_approvals_changed", None, {"from": 2, "to": 3}),
tests/integration/test_admin_service.py:380:                "from_role": "director",
tests/integration/test_admin_service.py:381:                "to_role": "crew",
tests/integration/test_admin_service.py:408:@pytest.mark.parametrize("to_role", [Role.CREW, Role.DIRECTOR])
tests/integration/test_admin_service.py:409:def test_p7_a_lead_who_owns_unfinished_missions_cant_change_role(seeded_db, to_role):
tests/integration/test_admin_service.py:412:        admin.change_role(ctx(seeded_db), NORA, to_role)
tests/integration/test_admin_service.py:500:            {"user_id": FAY, "user_name": "Fay Moreau", "from_role": "crew", "to_role": "lead"},
tests/integration/test_admin_service.py:727:                "from_name": "Systems Engineering",
tests/integration/test_admin_service.py:728:                "to_name": "Systems Eng",
tests/cli/test_cli_real_api.py:16:from mission_control.seed.data import DEMO_PASSWORD
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -n -i "audit\|names at the time\|data_json\|\bdata\b" docs/technical-design.md | head -40; grep -n -i "audit" docs/prd.md | head -20
```

<details>
<summary>↳ Result</summary>

```
10:3. [Data model](#3-data-model)
66:| Services | `services/` | One use case = one transaction + audit | domain, infra |
75:4. `domain.lifecycle.check_submit(...)` returns a list of problems. If the list is empty, the service writes the new status and an audit event, then commits.
84:  services/  auth  admin  crew  missions  assignments  approvals  matching  audit  inbox
87:  seed/      data  loader
97:## 3. Data model
99:The core entities are below. Skills, unavailability, approvals, tokens and the audit log hang off these. All 13 tables are in [Appendix A](#appendix-a-schema-sql).
120:| Append-only audit log; used skills can't be deleted | |
127:- **History survives renames.** Audit `data` keeps the names that applied at the time.
237:| **Audit** | Written in the same transaction as the change. Refused actions write nothing. |
306:| Data | Loaded with one query per fact type | Recomputed inside the write transaction, so it's never stale |
315:- Lifecycle changes are explicit `POST` commands, for example `/submit`. They are never `PATCH status`, because each one has its own guards and audit event ([TR-8](#tr-8)).
325:| GET | `/me/inbox` | Things waiting on me: a to-do list computed from current data (see below) |
354:| GET | `/missions/{id}/history` | Audit trail |
369:`GET /me/inbox` (`mc inbox`) lists only what is waiting on the caller to act. It's computed from current data on each request, so nothing is stored, nothing is marked as read, and an item disappears once it's dealt with. Every role has one inbox, showing whichever sections apply:
510:| SF | service foundation | Service context (actor + `Repos` + transaction + audit) · `RuleViolation` carrying problems · refused view becomes not-found · fact loaders building `CandidateFacts` / `RosterEntry` / `AssignmentFact` / `ActiveAssignment` from the database · the repository writes Wave 1 needs |
515:| M13 | approvals | S1, S6, S7, S8 · audit trail (AC-1) |
573:- Every change decides the mission's next status through `domain.lifecycle` (`touch_for_change()` for edits, `mission_status_after()` / `mission_status_after_assignment_action()` for transfers and roster changes), so a Pending mission returns to Draft in one place. It writes an audit event in the same transaction.
600:uv run mc-admin seed --reset      # load PRD §9 data
613:| Integration | temporary file | Services, rollback, constraints, audit, SQL lint |
617:- **Shared seed.** `seed/data.py` drives both the demo and the tests, so they can't drift apart.
780:### Assignments, approvals and audit
823:CREATE TABLE audit_events (                                      -- append-only (V1)
834:  data            TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(data)),   -- names at the time of the event
841:CREATE INDEX audit_events_mission ON audit_events(mission_id, created_at);
842:CREATE INDEX audit_events_profile ON audit_events(crew_profile_id, created_at);
843:CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events
844:  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
845:CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events
846:  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
849:Composite foreign keys are only checked when every column in them is non-NULL, so the optional references on `audit_events` work as expected.
867:| <a id="tr-7"></a>TR-7 | **Compute, don't store** (workload, eligibility) | Cached columns | Can never go stale; small data | More reads per request. Add caching only if profiling shows a need. |
868:| <a id="tr-8"></a>TR-8 | **Command endpoints** (`/submit`) | `PATCH {status}` | Each transition has its own guards, audit event and CLI command | More routes |
870:| <a id="tr-10"></a>TR-10 | **404 for anything not visible** | 403 | Never reveals that another tenant's data exists | Slightly harder to debug. Logs record the real reason. |
879:| A new endpoint leaks data across tenants | Scoped repositories, composite foreign keys, a route inventory test that fails CI, and the isolation sweep |
155:### 5.7 Visibility and audit
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat tests/integration/conftest.py tests/conftest.py | head -150; sed -n 1,80p tests/builders.py
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/seed/data.py | sed -n 1,242p
```

<details>
<summary>↳ Result</summary>

```
"""Demo data for two organisations. Shared by `mc-admin seed` and the tests.

Ids are fixed and follow the people and mission tables in the PRD, so a crew profile's id
equals its user's id. The matcher's final tie-break is the crew profile id.
"""

from collections.abc import Mapping
from types import MappingProxyType as _ro
from typing import NamedTuple

DEMO_PASSWORD = "orbital launch window"  # every seeded user; at least 15 characters


class Organisation(NamedTuple):
    id: int
    name: str
    slug: str
    required_approvals: int


class User(NamedTuple):
    id: int
    org_id: int
    name: str
    role: str
    has_crew_profile: bool


class Skill(NamedTuple):
    id: int
    org_id: int
    name: str


class Unavailability(NamedTuple):
    crew_id: int
    start: str
    end: str
    reason: str


class Slot(NamedTuple):
    name: str
    headcount: int
    requirements: Mapping[int, int]  # skill id: min level
    crew: tuple[tuple[int, str], ...]  # (crew id, assignment status)


class Mission(NamedTuple):
    id: int
    org_id: int
    name: str
    owner_id: int
    creator_id: int
    start: str
    end: str
    status: str
    approvers: tuple[int, ...]  # director ids, round 1
    slots: tuple[Slot, ...]


ORGANISATIONS = (
    Organisation(1, "Aurora Space Agency", "aurora", 2),
    Organisation(2, "Helix Orbital", "helix", 1),
)

USERS = (
    # id, org, name, role, has crew profile
    User(1, 1, "Ruth Adeyemi", "director", False),
    User(2, 1, "Marco Bianchi", "director", True),
    User(3, 1, "Ingrid Holm", "director", False),
    User(4, 1, "Lee Park", "lead", False),
    User(5, 1, "Nora Quinn", "lead", False),
    User(6, 1, "Ana Okafor", "lead", True),
    User(7, 1, "Ben Ito", "crew", True),
    User(8, 1, "Chen Wu", "crew", True),
    User(9, 1, "Dana Reyes", "crew", True),
    User(10, 1, "Eli Novak", "crew", True),
    User(11, 1, "Fay Moreau", "crew", True),
    User(12, 1, "Gus Patel", "crew", True),
    User(13, 1, "Hana Sato", "crew", True),
    User(14, 2, "Sam Rivera", "director", False),
    User(15, 2, "Priya Nair", "lead", False),
    User(16, 2, "Kai Tanaka", "crew", True),
    User(17, 2, "Lena Fischer", "crew", True),
    User(18, 2, "Omar Haddad", "crew", True),
    User(19, 2, "Tess Moreno", "crew", True),
)

SKILLS = (
    # id, org, name
    Skill(1, 1, "Piloting"),
    Skill(2, 1, "Leadership"),
    Skill(3, 1, "Systems Engineering"),
    Skill(4, 1, "EVA"),
    Skill(5, 1, "Geology"),
    Skill(6, 1, "Flight Medicine"),
    Skill(7, 2, "Piloting"),
    Skill(8, 2, "Payload Integration"),
    Skill(9, 2, "Life Support"),
    Skill(10, 2, "Field Medicine"),
)

CREW_SKILLS = _ro(
    {
        # crew profile (= user) id: {skill id: level}
        2: _ro({6: 4}),
        6: _ro({1: 5, 2: 4, 3: 4}),
        7: _ro({3: 4, 4: 3}),
        8: _ro({3: 3}),
        9: _ro({4: 4}),
        10: _ro({4: 4, 1: 4, 2: 2}),
        11: _ro({1: 4, 2: 4}),
        12: _ro({3: 5}),
        13: _ro({4: 3, 5: 2}),
        16: _ro({7: 5}),
        17: _ro({8: 4}),
        18: _ro({10: 4}),
        19: _ro({9: 3}),
    }
)

UNAVAILABILITY = (Unavailability(11, "2027-03-05", "2027-03-08", "Medical"),)

# Each mission: id, org, name, owner, creator, start, end, status, approvals (director ids,
# round 1), and slots with their requirements and (crew id, assignment status) pairs.
MISSIONS = (
    Mission(
        1,
        1,
        "Lunar Gateway Resupply",
        4,
        1,
        "2027-03-01",
        "2027-03-10",
        "draft",
        (),
        (
            Slot("Flight Engineer", 1, _ro({3: 3}), ()),
            Slot("Mission Specialist", 1, _ro({4: 3}), ()),
            Slot("Commander", 1, _ro({1: 4, 2: 3}), ()),
        ),
    ),
    Mission(
        2,
        1,
        "Asteroid Survey",
        5,
        5,
        "2027-03-05",
        "2027-03-12",
        "draft",
        (),
        (
            Slot("Pilot", 1, _ro({1: 4}), ()),
            Slot("Geologist", 1, _ro({5: 4}), ()),
        ),
    ),
    Mission(
        3,
        1,
        "Station Reboost",
        5,
        5,
        "2027-02-25",
        "2027-03-02",
        "draft",
        (),
        (Slot("Engineer", 2, _ro({3: 3}), ((12, "accepted"),)),),
    ),
    Mission(
        4,
        1,
        "Lunar Surface Medical Study",
        5,
        1,
        "2027-03-15",
        "2027-03-18",
        "draft",
        (),
        (Slot("Flight Surgeon", 1, _ro({6: 4}), ((2, "accepted"),)),),
    ),
    Mission(
        5,
        1,
        "Orbital Telescope Service",
        4,
        4,
        "2027-01-10",
        "2027-01-14",
        "active",
        (2, 3),
        (
            Slot("Engineer", 1, _ro({3: 3}), ((8, "accepted"),)),
            Slot(
                "EVA Specialist",
                3,
                _ro({4: 3}),
                ((9, "accepted"), (10, "accepted"), (13, "accepted")),
            ),
        ),
    ),
    Mission(
        6,
        1,
        "Deep Space Comms Upgrade",
        5,
        5,
        "2027-04-01",
        "2027-04-20",
        "pending_approval",
        (2,),
        (Slot("Engineer", 1, _ro({3: 3}), ((7, "accepted"),)),),
    ),
    Mission(
        7,
        1,
        "Mars Analog Habitat",
        4,
        4,
        "2026-05-01",
        "2026-05-30",
        "completed",
        (2, 3),
        (Slot("Engineer", 1, _ro({3: 3}), ((8, "completed"),)),),
    ),
    Mission(
        8,
        2,
        "Payload Demo 1",
        15,
        15,
        "2027-02-01",
        "2027-02-03",
        "draft",
        (),
        (
            Slot("Payload Specialist", 1, _ro({8: 3}), ((17, "accepted"),)),
            Slot("Medic", 1, _ro({10: 3}), ((18, "accepted"),)),
        ),
    ),
)
```

</details>

<details>
<summary>↳ Result</summary>

```
import pytest

from mission_control.infra.db import connect, init_db


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "mission_control.db"


@pytest.fixture
def conn(db_path):
    """A fresh, initialised database file per test."""
    c = connect(db_path)
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def seeded_db(conn):
    """A fresh database loaded with the PRD §9 seed."""
    from mission_control.seed.loader import load_seed

    load_seed(conn, password_hash="test-hash")
    return conn
"""Shared test setup.

- Puts this directory on sys.path so tests can `import builders`.
- Swaps in cheap Argon2 settings for speed. Tests marked `real_argon2` keep the production
  settings, so those stay covered.
"""

import sys
from pathlib import Path

import pytest
from argon2 import PasswordHasher

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

_CHEAP_HASHER = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


def pytest_configure(config):
    config.addinivalue_line("markers", "real_argon2: use production Argon2 settings")


@pytest.fixture(autouse=True)
def _cheap_argon2(request, monkeypatch):
    if request.node.get_closest_marker("real_argon2") is None:
        from mission_control.infra import security

        monkeypatch.setattr(security, "_hasher", _CHEAP_HASHER)
"""Small builders and PRD §9.1 Aurora seed records for focused domain tests.

Builders only fill in defaults. Records are frozen dataclasses, so the module-level
constants below can be shared between tests. Build variations with the builders or
`dataclasses.replace`, never by mutating a constant.
"""

from collections.abc import Iterable, Mapping
from datetime import date
from types import MappingProxyType

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus
from mission_control.domain.records import (
    CandidateFacts,
    Commitment,
    Requirement,
    RosterEntry,
    SlotSpec,
)

# --- Dates --------------------------------------------------------------------------------


def date_range(start: str, end: str) -> DateRange:
    """A DateRange from two ISO dates, both inclusive."""
    return DateRange(date.fromisoformat(start), date.fromisoformat(end))


# --- Aurora skill catalogue (PRD §9.1) ----------------------------------------------------

PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, FLIGHT_MEDICINE = 1, 2, 3, 4, 5, 6
SKILL_NAMES: Mapping[int, str] = MappingProxyType(
    {
        PILOTING: "Piloting",
        LEADERSHIP: "Leadership",
        SYS_ENG: "Systems Eng",
        EVA: "EVA",
        GEOLOGY: "Geology",
        FLIGHT_MEDICINE: "Flight Medicine",
    }
)


# --- Record builders ----------------------------------------------------------------------


def req(skill_id: int, min_level: int) -> Requirement:
    return Requirement(skill_id, SKILL_NAMES[skill_id], min_level)


def slot(
    *requirements: Requirement,
    id: int = 10,
    position: int = 1,
    name: str = "Commander",
    open_places: int = 1,
) -> SlotSpec:
    return SlotSpec(
        id=id,
        position=position,
        name=name,
        open_places=open_places,
        requirements=tuple(requirements),
    )


def crew(
    name: str = "Test Crew",
    id: int = 1,
    active: bool = True,
    skills: Mapping[int, int] | None = None,
    unavailable: Iterable[DateRange] = (),
    accepted_elsewhere: Iterable[Commitment] = (),
    workload: int = 0,
) -> CandidateFacts:
    return CandidateFacts(
        crew_profile_id=id,
        name=name,
        active=active,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 1,80p tests/integration/test_assignments_service.py; sed -n 195,240p tests/integration/test_assignments_service.py; grep -n "def \|^class\|^[A-Z_]* =" src/mission_control/domain/permissions.py | head -50
```

<details>
<summary>↳ Result</summary>

```
"""M12: the assignments service. Propose, accept, decline, withdraw, remove, and the cascade a
completed or cancelled mission applies (PRD §5.1, §5.4, S1–S4, §5.7, V1; AC-4, AC-5, AC-14,
AC-15, AC-29; scenarios S1, S4, S5).

Seed ids (PRD §9): a crew profile's id equals its user's id.
Missions: Gateway 1 (Draft, Lee) · Station Reboost 3 (Nora, Gus accepted) · Telescope 5 (Active)
· Deep Space Comms 6 (Pending, Ben accepted, Marco approved) · Payload Demo 8 (Helix).
Slots: Gateway Flight Engineer 1, Mission Specialist 2, Commander 3 · Asteroid Pilot 4 ·
Station Reboost Engineer 6 · Telescope EVA Specialist 9 · Deep Space Comms Engineer 10 ·
Payload Specialist 12 (Helix).
"""

import json
from datetime import UTC, datetime

import pytest

from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import Actor
from mission_control.infra.repositories import Repos
from mission_control.services import assignments
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
MARCO = Actor(user_id=2, org_id=1, role=Role.DIRECTOR, crew_profile_id=2)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
CHEN = Actor(user_id=8, org_id=1, role=Role.CREW, crew_profile_id=8)
DANA = Actor(user_id=9, org_id=1, role=Role.CREW, crew_profile_id=9)
HANA = Actor(user_id=13, org_id=1, role=Role.CREW, crew_profile_id=13)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)
PRIYA = Actor(user_id=15, org_id=2, role=Role.LEAD, crew_profile_id=None)

ANA_ID, BEN_ID, CHEN_ID, DANA_ID, ELI_ID, FAY_ID, GUS_ID, HANA_ID = 6, 7, 8, 9, 10, 11, 12, 13
KAI_ID, LENA_ID = 16, 17
GATEWAY, ASTEROID, REBOOST, TELESCOPE, DEEP_SPACE, PAYLOAD = 1, 2, 3, 5, 6, 8
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT = 1, 2, 3, 4
REBOOST_ENGINEER, DEEP_SPACE_ENGINEER, PAYLOAD_SPECIALIST = 6, 10, 12
SYS_ENG = 3

A = AssignmentStatus


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def assignment_id(conn, mission_id, crew_id):
    return conn.execute(
        "SELECT id FROM assignments WHERE mission_id = ? AND crew_profile_id = ? ORDER BY id DESC",
        (mission_id, crew_id),
    ).fetchone()[0]


def status_of(conn, assignment):
    return conn.execute("SELECT status FROM assignments WHERE id = ?", (assignment,)).fetchone()[0]


def mission_status(conn, mission_id):
    return conn.execute("SELECT status FROM missions WHERE id = ?", (mission_id,)).fetchone()[0]


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]


def audit_since(conn, since_id):
    rows = conn.execute(
        "SELECT actor_id, event, mission_id, assignment_id, crew_profile_id, from_status,"
        " to_status, reason, data FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(*tuple(r)[:8], json.loads(r["data"])) for r in rows]



def test_s1_lead_can_propose_themselves_but_must_accept(seeded_db):
    Repos(seeded_db, 1).missions.set_owner(GATEWAY, ANA.user_id)
    made = assignments.propose(as_(seeded_db, ANA), GATEWAY, COMMANDER, ANA_ID)
    assert made.status == A.PROPOSED
    accepted = assignments.accept(as_(seeded_db, ANA), made.id)
    assert accepted.status == A.ACCEPTED


def test_s2_overlapping_proposals_on_different_missions_are_allowed(seeded_db):
    # Proposals block nothing: Chen can be proposed for two overlapping missions.
    assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)
    assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    assert status_of(seeded_db, assignment_id(seeded_db, REBOOST, CHEN_ID)) == "proposed"
    assert status_of(seeded_db, assignment_id(seeded_db, GATEWAY, CHEN_ID)) == "proposed"


def test_ac4_proposing_on_a_pending_mission_returns_it_to_draft(seeded_db):
    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, "Backup Engineer", 1, {SYS_ENG: 3})
    before = last_audit_id(seeded_db)
    made = assignments.propose(as_(seeded_db, NORA), DEEP_SPACE, backup.id, GUS_ID)
    assert made.status == A.PROPOSED
    assert mission_status(seeded_db, DEEP_SPACE) == "draft"
    events = audit_since(seeded_db, before)
    assert [e[1] for e in events] == [Event.ASSIGNMENT_PROPOSED, Event.MISSION_RETURNED_TO_DRAFT]
    assert events[1] == (
        NORA.user_id,
        Event.MISSION_RETURNED_TO_DRAFT,
        DEEP_SPACE,
        None,
        None,
        "pending_approval",
        "draft",
        None,
        {"mission_name": "Deep Space Comms Upgrade", "cause": "assignment.proposed"},
    )


def test_ac5_proposing_on_an_active_mission_is_refused(seeded_db):
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, LEE), TELESCOPE, 9, BEN_ID)
    assert error.code == "mission_frozen"
    assert snapshot(seeded_db) == before


17:class Actor:
25:class Context:
39:ALL = frozenset(Role)
72:_OWNER_ONLY = frozenset(
81:_OWNER_OR_DIRECTOR = frozenset({Action.PREVIEW_MATCH, Action.COMPLETE, Action.CANCEL})
83:_CREW_SELF_ONLY = frozenset({Action.VIEW_CREW, Action.VIEW_ASSIGNMENT_HISTORY})
85:_SELF_ONLY = frozenset({Action.EDIT_OWN_PROFILE, Action.ACCEPT, Action.DECLINE, Action.WITHDRAW})
87:_OWNER = ("owner_id",)
88:_TARGET = ("target_user_id",)
165:_RESPOND_ONLY_TO_OWN = "You can only respond to your own assignments"
178:NO_CONTEXT = Context()
181:def authorize(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> None:
227:def can(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> bool:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -n "^def \|^    def " src/mission_control/services/inbox.py src/mission_control/services/auth.py src/mission_control/services/missions/queries.py; sed -n 1,60p src/mission_control/services/inbox.py
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/inbox.py:60:    def ready(self) -> bool:
src/mission_control/services/inbox.py:77:def inbox(ctx: ServiceContext) -> Inbox:
src/mission_control/services/inbox.py:87:def _proposals(ctx: ServiceContext, repos: Repos) -> tuple[AssignmentSummary, ...]:
src/mission_control/services/inbox.py:98:def _approvals(ctx: ServiceContext, repos: Repos) -> tuple[ApprovalItem, ...]:
src/mission_control/services/inbox.py:114:def _missions(ctx: ServiceContext, repos: Repos) -> tuple[MissionItem, ...]:
src/mission_control/services/missions/queries.py:8:def list_missions(ctx: ServiceContext) -> list[MissionListItem]:
src/mission_control/services/missions/queries.py:17:def get_mission(ctx: ServiceContext, mission_id: int) -> MissionView:
src/mission_control/services/auth.py:36:def _now(now: datetime | None) -> datetime:
src/mission_control/services/auth.py:40:def login(
src/mission_control/services/auth.py:81:def authenticate(
src/mission_control/services/auth.py:100:def whoami(conn: sqlite3.Connection, actor: Actor) -> Me:
src/mission_control/services/auth.py:110:def logout(conn: sqlite3.Connection, token: str, *, now: datetime | None = None) -> None:
src/mission_control/services/auth.py:115:def revoke_all_sessions(
src/mission_control/services/auth.py:126:def change_password(
src/mission_control/services/auth.py:151:def _bad_login() -> Unauthenticated:
src/mission_control/services/auth.py:157:def _wrong_current_password() -> Forbidden:
src/mission_control/services/auth.py:161:def _session_error() -> Unauthenticated:
"""The inbox: what is waiting on the caller to act, worked out from current data on each request.

Nothing is stored or marked as read; an item disappears once it's dealt with. Everyone has one
inbox, showing whichever sections apply to them:
- proposals waiting for their reply (anyone with a crew profile);
- pending missions they could still approve (Directors who didn't create the mission, aren't
  on it, and haven't approved this round);
- their own Draft missions, with the places still to fill, the proposals awaiting replies, and
  how many Directors could approve against how many are required.

The missions section counts places, replies and eligible approvers only. Whether the accepted
crew are still eligible is checked when the mission is submitted.
"""

from dataclasses import dataclass

from mission_control.domain.approvals import (
    Approver,
    count_eligible_approvers,
    decision_problems,
)
from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import AssignmentSummary
from mission_control.services.context import ServiceContext


@dataclass(frozen=True)
class ApprovalItem:
    """A pending mission waiting on this Director's decision."""

    mission_id: int
    mission_name: str
    window: DateRange
    approvals: int  # given so far this round
    required: int  # saved when the mission was submitted


@dataclass(frozen=True)
class UnfilledSlot:
    slot_id: int
    slot_name: str
    open_places: int


@dataclass(frozen=True)
class MissionItem:
    """One of the caller's Draft missions, with what it's waiting on."""

    mission_id: int
    mission_name: str
    window: DateRange
    unfilled: tuple[UnfilledSlot, ...]  # slots with open places, in listed order
    unanswered: int  # proposals the crew haven't replied to yet
    eligible_approvers: int  # active Directors who didn't create the mission and aren't on it
    approvals_required: int  # the organisation's current setting, saved when it's submitted

    @property
    def ready(self) -> bool:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 1,80p src/mission_control/infra/repositories/models.py | grep -n "datetime\|class" ; grep -n "def " src/mission_control/seed/loader.py; cat src/mission_control/infra/security.py | head -60
```

<details>
<summary>↳ Result</summary>

```
4:from dataclasses import dataclass
5:from datetime import datetime
12:@dataclass(frozen=True)
13:class Organisation:
20:@dataclass(frozen=True)
21:class User:
32:@dataclass(frozen=True)
33:class CrewProfile:
41:@dataclass(frozen=True)
42:class Skill:
49:@dataclass(frozen=True)
50:class Unavailability:
57:@dataclass(frozen=True)
58:class Mission:
70:@dataclass(frozen=True)
71:class Slot:
80:@dataclass(frozen=True)
15:def load_seed(conn: sqlite3.Connection, password_hash: str) -> None:
24:def _load_org(conn: sqlite3.Connection, org: data.Organisation, password_hash: str) -> None:
77:def _load_mission(conn: sqlite3.Connection, org: data.Organisation, m: data.Mission) -> None:
"""Password hashing, session tokens, and the only lookups not scoped to an organisation.

Login and token resolution happen before the caller's organisation is known, so these queries
look users up by email or token hash. Everything else goes through tenant-scoped repositories.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from mission_control.infra.db import utc_timestamp

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


_dummy_hashes: dict[int, str] = {}


def dummy_hash() -> str:
    """A real Argon2 hash of a random secret, made with the current hasher. Verifying against
    it when an email doesn't exist makes that path cost the same as a real check, so response
    time doesn't reveal which accounts exist."""
    key = id(_hasher)
    if key not in _dummy_hashes:
        _dummy_hashes[key] = _hasher.hash(secrets.token_urlsafe(32))
    return _dummy_hashes[key]


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_token() -> str:
    """32 random bytes, URL-safe. Returned to the client once and never stored."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def find_login(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, org_id, password_hash, is_active FROM users WHERE email = ?", (email,)
    ).fetchone()
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/seed/loader.py; sed -n 60,110p src/mission_control/infra/security.py
```

<details>
<summary>↳ Result</summary>

```
"""Load the demo data into an empty database, in one transaction.

Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them.
"""

import sqlite3

from mission_control.domain.events import Event
from mission_control.infra.db import write_tx
from mission_control.infra.repositories import Repos
from mission_control.seed import data


def load_seed(conn: sqlite3.Connection, password_hash: str) -> None:
    """`password_hash` is stored for every user; the caller hashes `data.DEMO_PASSWORD`."""
    with write_tx(conn):
        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:
            raise RuntimeError("the database is not empty; reset it before seeding")
        for org in data.ORGANISATIONS:
            _load_org(conn, org, password_hash)


def _load_org(conn: sqlite3.Connection, org: data.Organisation, password_hash: str) -> None:
    q = conn.execute
    q(
        "INSERT INTO organisations(id, name, slug, required_approvals) VALUES (?, ?, ?, ?)",
        (org.id, org.name, org.slug, org.required_approvals),
    )

    users = [u for u in data.USERS if u.org_id == org.id]
    for user in users:
        email = f"{user.name.split()[0].lower()}@{org.slug}.example"
        q(
            "INSERT INTO users(id, org_id, email, name, role, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, org.id, email, user.name, user.role, password_hash),
        )
    for user in users:
        if user.has_crew_profile:
            q(
                "INSERT INTO crew_profiles(id, org_id, user_id, display_name) VALUES (?, ?, ?, ?)",
                (user.id, org.id, user.id, user.name.split()[0]),
            )

    for skill in data.SKILLS:
        if skill.org_id == org.id:
            q(
                "INSERT INTO skills(id, org_id, name) VALUES (?, ?, ?)",
                (skill.id, org.id, skill.name),
            )

    director = next(u.id for u in users if u.role == "director")
    profile_ids = {u.id for u in users if u.has_crew_profile}
    for crew_id, levels in data.CREW_SKILLS.items():
        if crew_id in profile_ids:
            for skill_id, level in levels.items():
                q(
                    "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
                    " updated_by_id) VALUES (?, ?, ?, ?, ?)",
                    (org.id, crew_id, skill_id, level, director),
                )

    for absence in data.UNAVAILABILITY:
        if absence.crew_id in profile_ids:
            q(
                "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
                " VALUES (?, ?, ?, ?, ?)",
                (org.id, absence.crew_id, absence.start, absence.end, absence.reason),
            )

    for mission in data.MISSIONS:
        if mission.org_id == org.id:
            _load_mission(conn, org, mission)


def _load_mission(conn: sqlite3.Connection, org: data.Organisation, m: data.Mission) -> None:
    q = conn.execute
    audit = Repos(conn, org.id).audit
    seeded = {"mission_name": m.name, "seeded": True}
    submitted = m.status != "draft"
    q(
        "INSERT INTO missions(id, org_id, name, start_date, end_date, status, owner_id,"
        " created_by_id, approval_round, approvals_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            m.id,
            org.id,
            m.name,
            m.start,
            m.end,
            m.status,
            m.owner_id,
            m.creator_id,
            1 if submitted else 0,
            org.required_approvals if submitted else None,
        ),
    )
    audit.record(
        m.creator_id, Event.MISSION_CREATED, mission_id=m.id, to_status="draft", data=seeded
    )

    for position, slot in enumerate(m.slots, start=1):
        slot_id = q(
            "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
            " VALUES (?, ?, ?, ?, ?)",
            (org.id, m.id, slot.name, slot.headcount, position),
        ).lastrowid
        for skill_id, min_level in slot.requirements.items():
            q(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (?, ?, ?, ?)",
                (org.id, slot_id, skill_id, min_level),
            )
        for crew_id, assignment_status in slot.crew:
            q(
                "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
                " proposed_by_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                (org.id, m.id, slot_id, crew_id, m.owner_id, assignment_status),
            )

    # Audit events in the order they would really have happened: submit, each approval, then
    # activation (made by the final approval) and completion (by the owner).
    if submitted:
        audit.record(
            m.owner_id,
            Event.MISSION_SUBMITTED,
            mission_id=m.id,
            from_status="draft",
            to_status="pending_approval",
            data=seeded,
        )
    for director_id in m.approvers:
        q(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
            " VALUES (?, ?, 1, ?, 'approve')",
            (org.id, m.id, director_id),
        )
        audit.record(director_id, Event.MISSION_APPROVED, mission_id=m.id, data=seeded)
    if m.status in ("active", "completed"):
        audit.record(
            m.approvers[-1],
            Event.MISSION_ACTIVATED,
            mission_id=m.id,
            from_status="pending_approval",
            to_status="active",
            data=seeded,
        )
    if m.status == "completed":
        audit.record(
            m.owner_id,
            Event.MISSION_COMPLETED,
            mission_id=m.id,
            from_status="active",
            to_status="completed",
            data=seeded,
        )
    ).fetchone()


def login_state(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT password_hash, is_active FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def password_hash_of(conn: sqlite3.Connection, user_id: int) -> str:
    return conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()[0]


def set_password_hash(conn: sqlite3.Connection, user_id: int, password_hash: str) -> None:
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def store_token(
    conn: sqlite3.Connection, user_id: int, token_hash: str, created: datetime, expires: datetime
) -> None:
    conn.execute(
        "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token_hash, utc_timestamp(created), utc_timestamp(expires)),
    )


def find_session(conn: sqlite3.Connection, token_hash: str, now: datetime) -> sqlite3.Row | None:
    """The user behind a live session: not revoked, not expired, and still active."""
    return conn.execute(
        """SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id
           FROM auth_tokens t
           JOIN users u ON u.id = t.user_id
           LEFT JOIN crew_profiles p ON p.org_id = u.org_id AND p.user_id = u.id
           WHERE t.token_hash = ? AND t.revoked_at IS NULL AND t.expires_at > ?
             AND u.is_active = 1""",
        (token_hash, utc_timestamp(now)),
    ).fetchone()


def revoke_token(conn: sqlite3.Connection, token_hash: str, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
        (utc_timestamp(now), token_hash),
    )


def revoke_user_tokens(conn: sqlite3.Connection, user_id: int, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
        (utc_timestamp(now), user_id),
    )
```

</details>

### 🤖 Claude · 2026-10-12 05:21:12 UTC

Now I'll write the behaviour snapshot script.

**🔧 Write**

```json
{
  "file_path": "/tmp/fixcleanup/snapshot.py",
  "content": "\"\"\"Behaviour snapshot: run a broad set of service use cases on fresh seeded DBs and print every\nresult's codes, messages, statuses and the audit trail. Run from the worktree with `uv run`.\"\"\"\n\nimport dataclasses\nimport enum\nimport json\nimport sys\nimport tempfile\nfrom datetime import UTC, date, datetime\nfrom pathlib import Path\n\nfrom mission_control.domain.enums import Role\nfrom mission_control.domain.permissions import Actor\nfrom mission_control.infra.db import connect, init_db\nfrom mission_control.seed.loader import load_seed\nfrom mission_control.services import (\n    admin,\n    approvals,\n    assignments,\n    audit,\n    crew,\n    inbox,\n    matching,\n    missions,\n)\nfrom mission_control.services.context import ServiceContext\nfrom mission_control.services.missions import SlotInput\n\nNOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)\n\nRUTH = Actor(1, 1, Role.DIRECTOR, None)\nMARCO = Actor(2, 1, Role.DIRECTOR, 2)\nINGRID = Actor(3, 1, Role.DIRECTOR, None)\nLEE = Actor(4, 1, Role.LEAD, None)\nNORA = Actor(5, 1, Role.LEAD, None)\nANA = Actor(6, 1, Role.LEAD, 6)\nBEN = Actor(7, 1, Role.CREW, 7)\nCHEN = Actor(8, 1, Role.CREW, 8)\nDANA = Actor(9, 1, Role.CREW, 9)\nELI = Actor(10, 1, Role.CREW, 10)\nFAY = Actor(11, 1, Role.CREW, 11)\nGUS = Actor(12, 1, Role.CREW, 12)\nSAM = Actor(14, 2, Role.DIRECTOR, None)\nPRIYA = Actor(15, 2, Role.LEAD, None)\n\nout: list[str] = []\n\n\ndef clean(v):\n    if dataclasses.is_dataclass(v) and not isinstance(v, type):\n        return {f.name: clean(getattr(v, f.name)) for f in dataclasses.fields(v)}\n    if isinstance(v, datetime):\n        return \"<datetime>\"\n    if isinstance(v, date):\n        return v.isoformat()\n    if isinstance(v, enum.Enum):\n        return v.value\n    if isinstance(v, dict) or hasattr(v, \"items\"):\n        return {str(k): clean(x) for k, x in v.items()}\n    if isinstance(v, (list, tuple, set, frozenset)):\n        return [clean(x) for x in v]\n    return v\n\n\ndef fresh():\n    d = tempfile.mkdtemp(dir=\"/tmp/fixcleanup\")\n    c = connect(Path(d) / \"s.db\")\n    init_db(c)\n    load_seed(c, password_hash=\"x\")\n    return c\n\n\ndef run(conn, label, actor, fn, *args, **kwargs):\n    ctx = ServiceContext(conn, actor, now=NOW)\n    try:\n        result = fn(ctx, *args, **kwargs)\n        out.append(f\"OK   {label}: {json.dumps(clean(result), sort_keys=True, default=str)}\")\n    except Exception as e:  # noqa: BLE001\n        problems = [\n            {\"code\": p.code, \"message\": p.message, \"refs\": clean(p.refs)}\n            for p in getattr(e, \"problems\", ())\n        ]\n        out.append(\n            f\"FAIL {label}: {type(e).__name__} code={getattr(e, 'code', None)!r} \"\n            f\"message={getattr(e, 'message', str(e))!r} problems={json.dumps(problems)}\"\n        )\n\n\ndef dump_audit(conn, title):\n    out.append(f\"--- audit {title}\")\n    for r in conn.execute(\n        \"SELECT actor_id, event, mission_id, assignment_id, crew_profile_id, from_status,\"\n        \" to_status, reason, data FROM audit_events ORDER BY id\"\n    ):\n        out.append(\"AUDIT \" + json.dumps([*tuple(r)[:8], json.loads(r[\"data\"])], sort_keys=True))\n\n\ndef dump_state(conn, title):\n    out.append(f\"--- state {title}\")\n    for t in (\"missions\", \"assignments\", \"users\", \"crew_profiles\", \"skills\", \"slots\",\n              \"crew_skills\", \"unavailability\", \"approvals\", \"organisations\", \"slot_requirements\"):\n        rows = conn.execute(f\"SELECT * FROM {t} ORDER BY rowid\").fetchall()\n        for r in rows:\n            d = {k: r[k] for k in r.keys() if not k.endswith(\"_at\") and k != \"password_hash\"}\n            out.append(f\"STATE {t} {json.dumps(d, sort_keys=True)}\")\n\n\n# --- 1. Admin ---------------------------------------------------------------------------\nc = fresh()\nrun(c, \"view_org\", RUTH, admin.view_organisation)\nrun(c, \"view_org lead\", LEE, admin.view_organisation)\nrun(c, \"set_approvals 0\", RUTH, admin.set_required_approvals, 0)\nrun(c, \"set_approvals same\", RUTH, admin.set_required_approvals, 2)\nrun(c, \"set_approvals 3\", RUTH, admin.set_required_approvals, 3)\nrun(c, \"set_approvals 2\", RUTH, admin.set_required_approvals, 2)\nrun(c, \"list_users\", RUTH, admin.list_users)\nrun(c, \"view_user other org\", RUTH, admin.view_user, 14)\nrun(c, \"create_user dup\", RUTH, admin.create_user, \"ben@aurora.example\", \"B\", Role.CREW,\n    \"a long enough password\")\nrun(c, \"create_user blank\", RUTH, admin.create_user, \" \", \" \", Role.CREW, \"a long enough password\")\nrun(c, \"create_user short pw\", RUTH, admin.create_user, \"z@a.example\", \"Zed\", Role.CREW, \"short\")\nrun(c, \"create_user ok crew\", RUTH, admin.create_user, \"zoe@aurora.example\", \"Zoe Lin\", Role.CREW,\n    \"a long enough password\")\nrun(c, \"create_user ok lead\", RUTH, admin.create_user, \"yan@aurora.example\", \"Yan Ma\", Role.LEAD,\n    \"a long enough password\")\nrun(c, \"create_crew_profile exists\", RUTH, admin.create_crew_profile, 7)\nrun(c, \"create_crew_profile blank\", RUTH, admin.create_crew_profile, 4, \" \")\nrun(c, \"create_crew_profile ok\", RUTH, admin.create_crew_profile, 4, \"Lee P\")\nrun(c, \"change_role nora owns\", RUTH, admin.change_role, 5, Role.CREW)\nrun(c, \"change_role same\", RUTH, admin.change_role, 7, Role.CREW)\nrun(c, \"change_role fay->lead\", RUTH, admin.change_role, 11, Role.LEAD)\nrun(c, \"change_role ingrid->crew\", RUTH, admin.change_role, 3, Role.CREW)\nrun(c, \"change_role by lead\", LEE, admin.change_role, 7, Role.LEAD)\nrun(c, \"deactivate ben (open)\", RUTH, admin.deactivate_user, 7)\nrun(c, \"deactivate lee (owns)\", RUTH, admin.deactivate_user, 4)\nrun(c, \"deactivate hana (open on active)\", RUTH, admin.deactivate_user, 13)\nrun(c, \"deactivate eli\", RUTH, admin.deactivate_user, 11)\nrun(c, \"deactivate yan\", RUTH, admin.deactivate_user, 21)\nrun(c, \"deactivate yan again\", RUTH, admin.deactivate_user, 21)\nrun(c, \"list_skills crew\", BEN, admin.list_skills)\nrun(c, \"add_skill dup\", RUTH, admin.add_skill, \"piloting\")\nrun(c, \"add_skill blank\", RUTH, admin.add_skill, \"  \")\nrun(c, \"add_skill ok\", RUTH, admin.add_skill, \"Robotics\", \" Tech \")\nrun(c, \"add_skill by lead\", LEE, admin.add_skill, \"Robotics2\")\nrun(c, \"update_skill rename\", RUTH, admin.update_skill, 3, name=\"Systems Eng\")\nrun(c, \"update_skill category\", RUTH, admin.update_skill, 3, category=\"Eng\")\nrun(c, \"update_skill both\", RUTH, admin.update_skill, 3, name=\"Sys Eng\", category=None)\nrun(c, \"update_skill nothing\", RUTH, admin.update_skill, 3)\nrun(c, \"update_skill clash\", RUTH, admin.update_skill, 3, name=\"EVA\")\nrun(c, \"update_skill blank\", RUTH, admin.update_skill, 3, name=\" \")\nrun(c, \"delete_skill in use\", RUTH, admin.delete_skill, 3)\nrun(c, \"delete_skill in use 2\", RUTH, admin.delete_skill, 6)\nrun(c, \"delete_skill ok\", RUTH, admin.delete_skill, 11)\nrun(c, \"delete_skill missing\", RUTH, admin.delete_skill, 99)\ndump_audit(c, \"admin\")\ndump_state(c, \"admin\")\n\n# --- 2. Crew ----------------------------------------------------------------------------\nc = fresh()\nrun(c, \"list_crew ben\", BEN, crew.list_crew)\nrun(c, \"list_crew lee\", LEE, crew.list_crew)\nrun(c, \"view_crew ana as ben\", BEN, crew.view_crew, 6)\nrun(c, \"view_crew fay as ruth\", RUTH, crew.view_crew, 11)\nrun(c, \"view_crew fay as lee\", LEE, crew.view_crew, 11)\nrun(c, \"list_unavailability fay as fay\", FAY, crew.list_unavailability, 11)\nrun(c, \"assignment_history chen\", CHEN, crew.assignment_history, 8)\nrun(c, \"assignment_history chen as ben\", BEN, crew.assignment_history, 8)\nrun(c, \"update_details nothing\", BEN, crew.update_details, 7)\nrun(c, \"update_details blank\", BEN, crew.update_details, 7, display_name=\" \")\nrun(c, \"update_details other\", BEN, crew.update_details, 8, display_name=\"X\")\nrun(c, \"update_details lee other\", LEE, crew.update_details, 8, display_name=\"X\")\nrun(c, \"update_details ok\", BEN, crew.update_details, 7, display_name=\"Benji\", bio=\" hi \")\nrun(c, \"update_details bio only\", BEN, crew.update_details, 7, bio=\"\")\nrun(c, \"add_unav bad dates\", BEN, crew.add_unavailability, 7, date(2027, 5, 2), date(2027, 5, 1),\n    \" \")\nrun(c, \"add_unav overlap\", BEN, crew.add_unavailability, 7, date(2027, 4, 5), date(2027, 4, 6),\n    \"Leave\")\nrun(c, \"add_unav overlap gus\", GUS, crew.add_unavailability, 12, date(2027, 2, 1),\n    date(2027, 3, 30), \"Leave\")\nrun(c, \"add_unav ok\", BEN, crew.add_unavailability, 7, date(2027, 6, 1), date(2027, 6, 3), \"Leave\")\nrun(c, \"remove_unav missing\", BEN, crew.remove_unavailability, 7, 99)\nrun(c, \"remove_unav fay's as ben\", BEN, crew.remove_unavailability, 11, 1)\nrun(c, \"remove_unav ok\", FAY, crew.remove_unavailability, 11, 1)\nrun(c, \"set_skill self\", ANA, crew.set_skill_level, 6, 1, 3)\nrun(c, \"set_skill crew\", BEN, crew.set_skill_level, 8, 3, 2)\nrun(c, \"set_skill bad level\", LEE, crew.set_skill_level, 8, 3, 9)\nrun(c, \"set_skill breaks active\", LEE, crew.set_skill_level, 8, 3, 2)\nrun(c, \"set_skill breaks active dana\", LEE, crew.set_skill_level, 9, 4, 1)\nrun(c, \"set_skill ok up\", LEE, crew.set_skill_level, 8, 3, 4)\nrun(c, \"set_skill ok new\", LEE, crew.set_skill_level, 8, 5, 2)\nrun(c, \"set_skill missing skill\", LEE, crew.set_skill_level, 8, 99, 2)\nrun(c, \"remove_skill missing level\", LEE, crew.remove_skill_level, 8, 1)\nrun(c, \"remove_skill breaks active\", LEE, crew.remove_skill_level, 13, 4)\nrun(c, \"remove_skill ok\", LEE, crew.remove_skill_level, 7, 4)\ndump_audit(c, \"crew\")\ndump_state(c, \"crew\")\n\n# --- 3. Missions ------------------------------------------------------------------------\nc = fresh()\nrun(c, \"list_missions ben\", BEN, missions.list_missions)\nrun(c, \"list_missions lee\", LEE, missions.list_missions)\nrun(c, \"get_mission 1 as ben\", BEN, missions.get_mission, 1)\nrun(c, \"get_mission 6\", RUTH, missions.get_mission, 6)\nrun(c, \"get_mission 7\", RUTH, missions.get_mission, 7)\nrun(c, \"get_mission helix\", RUTH, missions.get_mission, 8)\nslots_ok = [SlotInput(\"Pilot\", 1, {1: 3}), SlotInput(\"Engineer\", 2, {3: 2})]\nrun(c, \"create invalid\", LEE, missions.create_mission, name=\" \", start=date(2027, 5, 5),\n    end=date(2027, 5, 1), slots=[SlotInput(\" \", 0, {}), SlotInput(\"X\", 1, {1: 9})])\nrun(c, \"create no slots\", LEE, missions.create_mission, name=\"M\", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=[])\nrun(c, \"create director no owner\", RUTH, missions.create_mission, name=\"M\",\n    start=date(2027, 5, 1), end=date(2027, 5, 2), slots=slots_ok)\nrun(c, \"create repeated\", LEE, missions.create_mission, name=\"M\", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=[SlotInput(\"Pilot\", 1, {1: 3}), SlotInput(\"pilot \", 1, {1: 3})])\nrun(c, \"create owner crew\", RUTH, missions.create_mission, name=\"M\", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=slots_ok, owner_id=7)\nrun(c, \"create owner crew + repeated\", RUTH, missions.create_mission, name=\"M2\",\n    start=date(2027, 5, 1), end=date(2027, 5, 2),\n    slots=[SlotInput(\"Pilot\", 1, {1: 3}), SlotInput(\"Pilot\", 1, {1: 3})], owner_id=7)\nrun(c, \"create lee for nora\", LEE, missions.create_mission, name=\"M\", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=slots_ok, owner_id=5)\nrun(c, \"create unknown skill\", LEE, missions.create_mission, name=\"M\", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=[SlotInput(\"Pilot\", 1, {99: 3})])\nrun(c, \"create ok\", LEE, missions.create_mission, name=\" Lunar Relay \", start=date(2027, 5, 1),\n    end=date(2027, 5, 2), slots=slots_ok)\nrun(c, \"create ok director\", RUTH, missions.create_mission, name=\"Relay 2\",\n    start=date(2027, 5, 1), end=date(2027, 5, 2), slots=slots_ok, owner_id=5)\nrun(c, \"update not owner\", NORA, missions.update_mission, 1, name=\"X\")\nrun(c, \"update active\", LEE, missions.update_mission, 5, name=\"X\")\nrun(c, \"update completed\", LEE, missions.update_mission, 7, name=\"X\")\nrun(c, \"update bad dates\", LEE, missions.update_mission, 1, end=date(2027, 2, 1))\nrun(c, \"update blank\", LEE, missions.update_mission, 1, name=\" \")\nrun(c, \"update nothing\", LEE, missions.update_mission, 1, name=\"Lunar Gateway Resupply\")\nrun(c, \"update ok\", LEE, missions.update_mission, 1, name=\"Gateway II\", end=date(2027, 3, 11))\nrun(c, \"update pending name only\", NORA, missions.update_mission, 6, name=\"DSC II\")\nrun(c, \"update pending dates invalid (ben)\", NORA, missions.update_mission, 6,\n    start=date(2027, 4, 2))\nrun(c, \"update reboost dates gus\", NORA, missions.update_mission, 3, end=date(2027, 3, 3))\nrun(c, \"transfer by lead\", LEE, missions.transfer_ownership, 1, 5)\nrun(c, \"transfer already owner\", RUTH, missions.transfer_ownership, 1, 4)\nrun(c, \"transfer to crew\", RUTH, missions.transfer_ownership, 1, 7)\nrun(c, \"transfer completed\", RUTH, missions.transfer_ownership, 7, 5)\nrun(c, \"transfer missing user\", RUTH, missions.transfer_ownership, 1, 99)\nrun(c, \"transfer ok\", RUTH, missions.transfer_ownership, 1, 5)\nrun(c, \"transfer pending ok\", RUTH, missions.transfer_ownership, 6, 4)\nrun(c, \"transfer active ok\", RUTH, missions.transfer_ownership, 5, 5)\nrun(c, \"add_slot taken\", NORA, missions.add_slot, 1, SlotInput(\"commander\", 1, {1: 1}))\nrun(c, \"add_slot invalid\", NORA, missions.add_slot, 1, SlotInput(\"\", 0, {}))\nrun(c, \"add_slot old owner\", LEE, missions.add_slot, 1, SlotInput(\"Medic\", 1, {6: 2}))\nrun(c, \"add_slot ok\", NORA, missions.add_slot, 1, SlotInput(\"Medic\", 1, {6: 2}))\nrun(c, \"update_slot headcount below\", NORA, missions.update_slot, 3, 6, headcount=0)\nrun(c, \"update_slot taken\", NORA, missions.update_slot, 1, 1, name=\"Commander\")\nrun(c, \"update_slot wrong mission\", NORA, missions.update_slot, 1, 6, name=\"Y\")\nrun(c, \"update_slot ok\", NORA, missions.update_slot, 1, 3, name=\"Mission Commander\",\n    headcount=2)\nrun(c, \"update_slot nothing\", NORA, missions.update_slot, 1, 3, name=\"Mission Commander\")\nrun(c, \"replace_req invalid\", NORA, missions.replace_requirements, 1, 3, {})\nrun(c, \"replace_req breaks gus\", NORA, missions.replace_requirements, 3, 6, {3: 5, 1: 2})\nrun(c, \"replace_req same\", NORA, missions.replace_requirements, 1, 1, {3: 3})\nrun(c, \"replace_req ok\", NORA, missions.replace_requirements, 1, 1, {3: 4, 4: 1})\nrun(c, \"remove_slot only+occupied\", NORA, missions.remove_slot, 3, 6)\nrun(c, \"remove_slot ok\", NORA, missions.remove_slot, 1, 2)\nrun(c, \"complete draft\", NORA, missions.complete_mission, 1)\nrun(c, \"cancel no reason\", NORA, missions.cancel_mission, 1, \"  \")\nrun(c, \"cancel completed\", RUTH, missions.cancel_mission, 7, \"x\")\nrun(c, \"cancel by crew\", BEN, missions.cancel_mission, 6, \"x\")\nrun(c, \"complete active\", NORA, missions.complete_mission, 5)\nrun(c, \"cancel pending ok\", RUTH, missions.cancel_mission, 6, \" Budget \")\nrun(c, \"remove_slot only (empty) new\", LEE, missions.remove_slot, 9, 13)\ndump_audit(c, \"missions\")\ndump_state(c, \"missions\")\n\n# --- 4. Assignments ---------------------------------------------------------------------\nc = fresh()\nrun(c, \"propose not owner\", NORA, assignments.propose, 1, 3, 11)\nrun(c, \"propose crew\", BEN, assignments.propose, 1, 3, 11)\nrun(c, \"propose active\", LEE, assignments.propose, 5, 9, 7)\nrun(c, \"propose pending full\", NORA, assignments.propose, 6, 10, 12)\nrun(c, \"propose unknown crew\", LEE, assignments.propose, 1, 3, 99)\nrun(c, \"propose unknown slot\", LEE, assignments.propose, 1, 99, 11)\nrun(c, \"propose ineligible fay (unavailable)\", LEE, assignments.propose, 1, 3, 11)\nrun(c, \"propose ineligible chen (skill)\", LEE, assignments.propose, 1, 3, 8)\nrun(c, \"propose ben overlap? no\", LEE, assignments.propose, 1, 1, 7)\nrun(c, \"propose gus (reboost overlap)\", LEE, assignments.propose, 1, 1, 12)\nrun(c, \"propose again ben\", LEE, assignments.propose, 1, 2, 7)\nrun(c, \"propose full\", LEE, assignments.propose, 1, 1, 8)\nrun(c, \"propose eli commander\", LEE, assignments.propose, 1, 3, 10)\nrun(c, \"propose dana specialist\", LEE, assignments.propose, 1, 2, 9)\nrun(c, \"accept other's\", CHEN, assignments.accept, 9)\nrun(c, \"accept lee on ben's\", LEE, assignments.accept, 9)\nrun(c, \"accept ok\", BEN, assignments.accept, 9)\nrun(c, \"accept again\", BEN, assignments.accept, 9)\nrun(c, \"decline ok\", ELI, assignments.decline, 10, \"  \")\nrun(c, \"withdraw no reason\", BEN, assignments.withdraw, 9, \" \")\nrun(c, \"withdraw proposed\", DANA, assignments.withdraw, 11, \"x\")\nrun(c, \"withdraw ok\", BEN, assignments.withdraw, 9, \"Sick\")\nrun(c, \"remove by crew\", DANA, assignments.remove, 11)\nrun(c, \"remove ok\", LEE, assignments.remove, 11)\nrun(c, \"remove again\", LEE, assignments.remove, 11)\nrun(c, \"withdraw pending ben\", BEN, assignments.withdraw, 5, \"Family\")\nrun(c, \"remove active\", LEE, assignments.remove, 3)\nrun(c, \"my_assignments chen\", CHEN, assignments.my_assignments)\nrun(c, \"my_assignments pending eli\", ELI, assignments.my_assignments, True)\nrun(c, \"my_assignments lee\", LEE, assignments.my_assignments)\nrun(c, \"accept helix as other org\", SAM, assignments.accept, 9)\ndump_audit(c, \"assignments\")\ndump_state(c, \"assignments\")\n\n# --- 5. Approvals, matching, golden path ------------------------------------------------\nc = fresh()\nrun(c, \"submit gateway incomplete\", LEE, approvals.submit, 1)\nrun(c, \"submit by other\", NORA, approvals.submit, 1)\nrun(c, \"submit pending\", NORA, approvals.submit, 6)\nrun(c, \"approve draft\", RUTH, approvals.approve, 1)\nrun(c, \"approve marco already\", MARCO, approvals.approve, 6)\nrun(c, \"approve by lead\", LEE, approvals.approve, 6)\nrun(c, \"reject no reason\", RUTH, approvals.reject, 6, \" \")\nrun(c, \"preview gateway lee\", LEE, matching.preview, 1)\nrun(c, \"preview gateway ruth\", RUTH, matching.preview, 1)\nrun(c, \"preview active\", LEE, matching.preview, 5)\nrun(c, \"preview by crew\", BEN, matching.preview, 1)\nrun(c, \"apply by director\", RUTH, matching.apply, 1)\nrun(c, \"apply ok\", LEE, matching.apply, 1)\nrun(c, \"apply nothing\", LEE, matching.apply, 1)\nrun(c, \"inbox ben\", BEN, inbox.inbox)\nrun(c, \"inbox lee\", LEE, inbox.inbox)\nrun(c, \"inbox ruth\", RUTH, inbox.inbox)\nrun(c, \"inbox ingrid\", INGRID, inbox.inbox)\nrun(c, \"inbox marco\", MARCO, inbox.inbox)\nfor aid, who in ((9, CHEN), (10, BEN), (11, ELI)):\n    pass\nrows = c.execute(\"SELECT id, crew_profile_id FROM assignments WHERE mission_id = 1\").fetchall()\nactors = {a.crew_profile_id: a for a in (BEN, CHEN, DANA, ELI, FAY, GUS, ANA, MARCO)}\nfor r in rows:\n    run(c, f\"accept {r['id']}\", actors[r[\"crew_profile_id\"]], assignments.accept, r[\"id\"])\nrun(c, \"submit gateway ok\", LEE, approvals.submit, 1)\nrun(c, \"approve creator ruth\", RUTH, approvals.approve, 1)\nrun(c, \"approve ingrid\", INGRID, approvals.approve, 1)\nrun(c, \"approve ingrid again\", INGRID, approvals.approve, 1)\nrun(c, \"approve marco\", MARCO, approvals.approve, 1)\nrun(c, \"reject ok deep space\", INGRID, approvals.reject, 6, \"Too early\")\nrun(c, \"resubmit deep space\", NORA, approvals.submit, 6)\nrun(c, \"approve deep space marco\", MARCO, approvals.approve, 6)\nrun(c, \"approve deep space ingrid\", INGRID, approvals.approve, 6)\nrun(c, \"complete gateway\", LEE, missions.complete_mission, 1)\nrun(c, \"cancel medical\", RUTH, missions.cancel_mission, 4, \"Scrubbed\")\nfor m in range(1, 10):\n    run(c, f\"history {m} ruth\", RUTH, audit.mission_history, m)\nrun(c, \"history 1 as ben\", BEN, audit.mission_history, 1)\nrun(c, \"history 2 as ben\", BEN, audit.mission_history, 2)\ndump_audit(c, \"approvals\")\ndump_state(c, \"approvals\")\n\n# --- 6. Transfer then owner-only actions (AC-7 shape) -----------------------------------\nc = fresh()\nrun(c, \"transfer gateway to nora\", RUTH, missions.transfer_ownership, 1, 5)\nrun(c, \"lee propose after\", LEE, assignments.propose, 1, 1, 7)\nrun(c, \"lee apply after\", LEE, matching.apply, 1)\nrun(c, \"lee submit after\", LEE, approvals.submit, 1)\nrun(c, \"nora propose\", NORA, assignments.propose, 1, 1, 7)\nrun(c, \"nora apply\", NORA, matching.apply, 1)\nrun(c, \"nora submit\", NORA, approvals.submit, 1)\ndump_audit(c, \"transfer\")\n\nsys.stdout.write(\"\\n\".join(out) + \"\\n\")\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /tmp/fixcleanup/snapshot.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run python /tmp/fixcleanup/snapshot.py > /tmp/fixcleanup/before.txt 2>/tmp/fixcleanup/before.err; echo $?; wc -l /tmp/fixcleanup/before.txt; cat /tmp/fixcleanup/before.err | tail -5; grep -c "^FAIL" /tmp/fixcleanup/before.txt; grep "^FAIL" /tmp/fixcleanup/before.txt | grep -v "RuleViolation\|StateConflict\|InvalidInput\|Forbidden\|NotFound"
```

<details>
<summary>↳ Result</summary>

```
0
    1012 /tmp/fixcleanup/before.txt
119
FAIL create_user short pw: PasswordTooShort code=None message='password must be at least 15 characters' problems=[]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run python /tmp/fixcleanup/snapshot.py > /tmp/fixcleanup/before2.txt 2>&1; diff /tmp/fixcleanup/before.txt /tmp/fixcleanup/before2.txt && echo SAME; grep "^OK\|^FAIL" /tmp/fixcleanup/before.txt | cut -c1-230 | sed -n 1,400p | grep -v "^OK   history\|list_crew\|list_missions\|list_users\|get_mission" | head -150
```

<details>
<summary>↳ Result</summary>

```
SAME
OK   view_org: {"id": 1, "name": "Aurora Space Agency", "required_approvals": 2, "slug": "aurora"}
FAIL view_org lead: Forbidden code='role_forbidden' message="Leads can't manage the organisation" problems=[]
FAIL set_approvals 0: InvalidInput code='validation_error' message='At least one approval must be required' problems=[{"code": "validation_error", "message": "At least one approval must be required", "refs": {}}]
OK   set_approvals same: {"id": 1, "name": "Aurora Space Agency", "required_approvals": 2, "slug": "aurora"}
OK   set_approvals 3: {"id": 1, "name": "Aurora Space Agency", "required_approvals": 3, "slug": "aurora"}
OK   set_approvals 2: {"id": 1, "name": "Aurora Space Agency", "required_approvals": 2, "slug": "aurora"}
FAIL view_user other org: NotFound code='not_found' message='User not found' problems=[]
FAIL create_user dup: RuleViolation code='rule_violation' message='The email address ben@aurora.example is already in use' problems=[{"code": "already_exists", "message": "The email address ben@aurora.example is already in use", "
FAIL create_user blank: InvalidInput code='validation_error' message="Some values aren't valid" problems=[{"code": "validation_error", "message": "The email address can't be blank", "refs": {}}, {"code": "validation_error", "messa
FAIL create_user short pw: PasswordTooShort code=None message='password must be at least 15 characters' problems=[]
OK   create_user ok crew: {"email": "zoe@aurora.example", "id": 20, "is_active": true, "name": "Zoe Lin", "org_id": 1, "role": "crew"}
OK   create_user ok lead: {"email": "yan@aurora.example", "id": 21, "is_active": true, "name": "Yan Ma", "org_id": 1, "role": "lead"}
FAIL create_crew_profile exists: RuleViolation code='rule_violation' message='Ben Ito already has a crew profile' problems=[{"code": "already_exists", "message": "Ben Ito already has a crew profile", "refs": {"user_id": 7, "crew_p
FAIL create_crew_profile blank: InvalidInput code='validation_error' message="The display name can't be blank" problems=[{"code": "validation_error", "message": "The display name can't be blank", "refs": {}}]
OK   create_crew_profile ok: {"bio": null, "display_name": "Lee P", "id": 21, "org_id": 1, "user_id": 4}
FAIL change_role nora owns: RuleViolation code='rule_violation' message="Nora Quinn's role can't be changed" problems=[{"code": "owns_open_missions", "message": "Nora Quinn still owns Station Reboost, Asteroid Survey, Lunar Surfac
OK   change_role same: {"email": "ben@aurora.example", "id": 7, "is_active": true, "name": "Ben Ito", "org_id": 1, "role": "crew"}
OK   change_role fay->lead: {"email": "fay@aurora.example", "id": 11, "is_active": true, "name": "Fay Moreau", "org_id": 1, "role": "lead"}
OK   change_role ingrid->crew: {"email": "ingrid@aurora.example", "id": 3, "is_active": true, "name": "Ingrid Holm", "org_id": 1, "role": "crew"}
FAIL change_role by lead: Forbidden code='role_forbidden' message="Leads can't manage the organisation" problems=[]
FAIL deactivate ben (open): RuleViolation code='rule_violation' message="Ben Ito can't be deactivated" problems=[{"code": "has_open_assignments", "message": "Ben Ito has an open assignment on Deep Space Comms Upgrade; they must wi
FAIL deactivate lee (owns): RuleViolation code='rule_violation' message="Lee Park can't be deactivated" problems=[{"code": "owns_open_missions", "message": "Lee Park still owns Orbital Telescope Service and Lunar Gateway Resupply;
FAIL deactivate hana (open on active): RuleViolation code='rule_violation' message="Hana Sato can't be deactivated" problems=[{"code": "has_open_assignments", "message": "Hana Sato has an open assignment on Orbital Telescope Servi
OK   deactivate eli: {"email": "fay@aurora.example", "id": 11, "is_active": false, "name": "Fay Moreau", "org_id": 1, "role": "lead"}
OK   deactivate yan: {"email": "yan@aurora.example", "id": 21, "is_active": false, "name": "Yan Ma", "org_id": 1, "role": "lead"}
OK   deactivate yan again: {"email": "yan@aurora.example", "id": 21, "is_active": false, "name": "Yan Ma", "org_id": 1, "role": "lead"}
FAIL list_skills crew: Forbidden code='role_forbidden' message="Crew can't view the skill catalogue" problems=[]
FAIL add_skill dup: RuleViolation code='rule_violation' message='The catalogue already has a skill called Piloting' problems=[{"code": "already_exists", "message": "The catalogue already has a skill called Piloting", "refs": {"ski
FAIL add_skill blank: InvalidInput code='validation_error' message="The skill name can't be blank" problems=[{"code": "validation_error", "message": "The skill name can't be blank", "refs": {}}]
OK   add_skill ok: {"category": "Tech", "id": 11, "name": "Robotics", "org_id": 1}
FAIL add_skill by lead: Forbidden code='role_forbidden' message="Leads can't manage the skill catalogue" problems=[]
OK   update_skill rename: {"category": null, "id": 3, "name": "Systems Eng", "org_id": 1}
OK   update_skill category: {"category": "Eng", "id": 3, "name": "Systems Eng", "org_id": 1}
OK   update_skill both: {"category": null, "id": 3, "name": "Sys Eng", "org_id": 1}
OK   update_skill nothing: {"category": null, "id": 3, "name": "Sys Eng", "org_id": 1}
FAIL update_skill clash: RuleViolation code='rule_violation' message='The catalogue already has a skill called EVA' problems=[{"code": "already_exists", "message": "The catalogue already has a skill called EVA", "refs": {"skill_id
FAIL update_skill blank: InvalidInput code='validation_error' message="The skill name can't be blank" problems=[{"code": "validation_error", "message": "The skill name can't be blank", "refs": {}}]
FAIL delete_skill in use: RuleViolation code='rule_violation' message="Sys Eng can't be deleted because Ana Okafor, Ben Ito, Chen Wu and Gus Patel have it and Mars Analog Habitat (Engineer), Orbital Telescope Service (Engineer), S
FAIL delete_skill in use 2: RuleViolation code='rule_violation' message="Flight Medicine can't be deleted because Marco Bianchi has it and Lunar Surface Medical Study (Flight Surgeon) requires it" problems=[{"code": "skill_in_use"
OK   delete_skill ok: null
FAIL delete_skill missing: NotFound code='not_found' message='Skill not found' problems=[]
FAIL view_crew ana as ben: NotFound code='not_found' message='Crew member not found' problems=[]
OK   view_crew fay as ruth: {"active": true, "bio": null, "crew_profile_id": 11, "email": "fay@aurora.example", "name": "Fay", "skills": [{"level": 4, "skill_id": 2, "skill_name": "Leadership"}, {"level": 4, "skill_id": 1, "skill_
OK   view_crew fay as lee: {"active": true, "bio": null, "crew_profile_id": 11, "email": "fay@aurora.example", "name": "Fay", "skills": [{"level": 4, "skill_id": 2, "skill_name": "Leadership"}, {"level": 4, "skill_id": 1, "skill_n
OK   list_unavailability fay as fay: [{"id": 1, "reason": "Medical", "window": {"end": "2027-03-08", "start": "2027-03-05"}}]
OK   assignment_history chen: [{"assignment_id": 3, "mission_id": 5, "mission_name": "Orbital Telescope Service", "mission_status": "active", "reason": null, "slot_name": "Engineer", "status": "accepted", "window": {"end": "2027-0
FAIL assignment_history chen as ben: NotFound code='not_found' message='Crew member not found' problems=[]
OK   update_details nothing: {"bio": null, "display_name": "Ben", "id": 7, "org_id": 1, "user_id": 7}
FAIL update_details blank: InvalidInput code='validation_error' message="Display name can't be blank" problems=[{"code": "validation_error", "message": "Display name can't be blank", "refs": {}}]
FAIL update_details other: NotFound code='not_found' message='Crew member not found' problems=[]
FAIL update_details lee other: Forbidden code='not_owner' message='You can only edit your own profile and availability' problems=[]
OK   update_details ok: {"bio": "hi", "display_name": "Benji", "id": 7, "org_id": 1, "user_id": 7}
OK   update_details bio only: {"bio": null, "display_name": "Benji", "id": 7, "org_id": 1, "user_id": 7}
FAIL add_unav bad dates: InvalidInput code='validation_error' message="Some values aren't valid" problems=[{"code": "validation_error", "message": "The end date 2027-05-01 is before the start date 2027-05-02", "refs": {}}, {"code"
FAIL add_unav overlap: RuleViolation code='rule_violation' message='Benji has an accepted assignment overlapping those dates' problems=[{"code": "overlap", "message": "Benji has an accepted assignment on Deep Space Comms Upgrade o
FAIL add_unav overlap gus: RuleViolation code='rule_violation' message='Gus has an accepted assignment overlapping those dates' problems=[{"code": "overlap", "message": "Gus has an accepted assignment on Station Reboost overlappin
OK   add_unav ok: {"crew_profile_id": 7, "id": 2, "reason": "Leave", "window": {"end": "2027-06-03", "start": "2027-06-01"}}
FAIL remove_unav missing: NotFound code='not_found' message='Unavailability not found' problems=[]
FAIL remove_unav fay's as ben: NotFound code='not_found' message='Crew member not found' problems=[]
OK   remove_unav ok: null
FAIL set_skill self: Forbidden code='self_skill_edit' message="You can't change your own skill levels" problems=[]
FAIL set_skill crew: NotFound code='not_found' message='Crew member not found' problems=[]
FAIL set_skill bad level: InvalidInput code='validation_error' message='Skill level must be between 1 and 5' problems=[{"code": "validation_error", "message": "Skill level must be between 1 and 5", "refs": {}}]
FAIL set_skill breaks active: RuleViolation code='rule_violation' message="Changing Chen's Systems Engineering level would break their assignments on active missions" problems=[{"code": "invalidates_active_assignment", "message": 
FAIL set_skill breaks active dana: RuleViolation code='rule_violation' message="Changing Dana's EVA level would break their assignments on active missions" problems=[{"code": "invalidates_active_assignment", "message": "Dana needs
OK   set_skill ok up: {"level": 4, "skill_id": 3, "skill_name": "Systems Engineering"}
OK   set_skill ok new: {"level": 2, "skill_id": 5, "skill_name": "Geology"}
FAIL set_skill missing skill: NotFound code='not_found' message='Skill not found' problems=[]
FAIL remove_skill missing level: NotFound code='not_found' message='Skill level not found' problems=[]
FAIL remove_skill breaks active: RuleViolation code='rule_violation' message="Changing Hana's EVA level would break their assignments on active missions" problems=[{"code": "invalidates_active_assignment", "message": "Hana needs E
OK   remove_skill ok: null
FAIL create invalid: InvalidInput code='validation_error' message="Some values aren't valid" problems=[{"code": "validation_error", "message": "The mission needs a name", "refs": {}}, {"code": "validation_error", "message": "The e
FAIL create no slots: InvalidInput code='validation_error' message='The mission needs at least one slot' problems=[{"code": "validation_error", "message": "The mission needs at least one slot", "refs": {}}]
FAIL create director no owner: InvalidInput code='validation_error' message='Name the Lead who will own the mission' problems=[{"code": "validation_error", "message": "Name the Lead who will own the mission", "refs": {}}]
FAIL create repeated: RuleViolation code='rule_violation' message='More than one slot is called Pilot' problems=[{"code": "already_exists", "message": "More than one slot is called Pilot", "refs": {}}]
FAIL create owner crew: RuleViolation code='rule_violation' message="Ben Ito can't own a mission: only Mission Leads can" problems=[{"code": "owner_not_active_lead", "message": "Ben Ito can't own a mission: only Mission Leads can"
FAIL create owner crew + repeated: RuleViolation code='rule_violation' message="M2 can't be created" problems=[{"code": "already_exists", "message": "More than one slot is called Pilot", "refs": {}}, {"code": "owner_not_active_lea
FAIL create lee for nora: Forbidden code='not_owner' message='Leads can only create missions they own' problems=[]
FAIL create unknown skill: NotFound code='not_found' message='Skill not found' problems=[]
OK   create ok: {"approvals": [], "assignments": [], "created_by_name": "Lee Park", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 4, "id": 9, "name": "Lunar Relay", "org_id": 1, "owner_id": 4, "stat
OK   create ok director: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 10, "name": "Relay 2", "org_id": 1, "owner_id"
FAIL update not owner: Forbidden code='not_owner' message="Only the mission's owner can edit this mission" problems=[]
FAIL update active: StateConflict code='mission_frozen' message="Can't edit an active mission" problems=[{"code": "mission_frozen", "message": "Can't edit an active mission", "refs": {}}]
FAIL update completed: StateConflict code='mission_final' message="Can't edit a mission that's completed" problems=[{"code": "mission_final", "message": "Can't edit a mission that's completed", "refs": {}}]
FAIL update bad dates: InvalidInput code='validation_error' message='The end date 2027-02-01 is before the start date 2027-03-01' problems=[{"code": "validation_error", "message": "The end date 2027-02-01 is before the start date 
FAIL update blank: InvalidInput code='validation_error' message='The mission needs a name' problems=[{"code": "validation_error", "message": "The mission needs a name", "refs": {}}]
OK   update nothing: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Lunar Gateway Resupply", "org_id": 1, 
OK   update ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 4, "s
OK   update pending name only: {"approvals": [{"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_
OK   update pending dates invalid (ben): {"approvals": [], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "accepted"}], "created_by_name": "Nor
OK   update reboost dates gus: {"approvals": [], "assignments": [{"crew_name": "Gus", "crew_profile_id": 12, "id": 1, "reason": null, "slot_id": 6, "slot_name": "Engineer", "status": "accepted"}], "created_by_name": "Nora Quinn", 
FAIL transfer by lead: Forbidden code='role_forbidden' message="Leads can't transfer mission ownership" problems=[]
FAIL transfer already owner: RuleViolation code='rule_violation' message='Lee Park already owns Gateway II' problems=[{"code": "already_owner", "message": "Lee Park already owns Gateway II", "refs": {"user_id": 4}}]
FAIL transfer to crew: RuleViolation code='rule_violation' message="Ben Ito can't own a mission: only Mission Leads can" problems=[{"code": "owner_not_active_lead", "message": "Ben Ito can't own a mission: only Mission Leads can",
FAIL transfer completed: StateConflict code='mission_final' message="Can't transfer a mission that's completed" problems=[{"code": "mission_final", "message": "Can't transfer a mission that's completed", "refs": {}}]
FAIL transfer missing user: NotFound code='not_found' message='User not found' problems=[]
OK   transfer ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 5, 
OK   transfer pending ok: {"approvals": [], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "accepted"}], "created_by_name": "Nora Quinn", "miss
OK   transfer active ok: {"approvals": [{"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}, {"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}], "assi
FAIL add_slot taken: RuleViolation code='rule_violation' message='Gateway II already has a slot called Commander' problems=[{"code": "already_exists", "message": "Gateway II already has a slot called Commander", "refs": {"slot_id"
FAIL add_slot invalid: InvalidInput code='validation_error' message="Some values aren't valid" problems=[{"code": "validation_error", "message": "Every slot needs a name", "refs": {}}, {"code": "validation_error", "message": "A sl
FAIL add_slot old owner: Forbidden code='not_owner' message="Only the mission's owner can edit this mission" problems=[]
OK   add_slot ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 5, 
FAIL update_slot headcount below: InvalidInput code='validation_error' message='Engineer needs a headcount of at least 1' problems=[{"code": "validation_error", "message": "Engineer needs a headcount of at least 1", "refs": {"slot
FAIL update_slot taken: RuleViolation code='rule_violation' message='Gateway II already has a slot called Commander' problems=[{"code": "already_exists", "message": "Gateway II already has a slot called Commander", "refs": {"slot_
FAIL update_slot wrong mission: NotFound code='not_found' message='Slot not found' problems=[]
OK   update_slot ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 
OK   update_slot nothing: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_
FAIL replace_req invalid: InvalidInput code='validation_error' message='Mission Commander needs at least one required skill' problems=[{"code": "validation_error", "message": "Mission Commander needs at least one required skill", 
FAIL replace_req breaks gus: RuleViolation code='rule_violation' message="Can't change the requirements of Engineer on Station Reboost: Gus would no longer be eligible. Remove them from the mission first." problems=[{"code": "skil
OK   replace_req same: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id"
OK   replace_req ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 
FAIL remove_slot only+occupied: RuleViolation code='rule_violation' message="Can't remove Engineer from Station Reboost: it's the mission's only slot, and Gus is assigned to it" problems=[{"code": "mission_needs_a_slot", "message"
OK   remove_slot ok: {"approvals": [], "assignments": [], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_by_id": 1, "id": 1, "name": "Gateway II", "org_id": 1, "owner_id": 
FAIL complete draft: StateConflict code='invalid_transition' message="Can't complete a mission in draft" problems=[{"code": "invalid_transition", "message": "Can't complete a mission in draft", "refs": {}}]
FAIL cancel no reason: InvalidInput code='validation_error' message='Cancelling Gateway II needs a reason' problems=[{"code": "validation_error", "message": "Cancelling Gateway II needs a reason", "refs": {}}]
FAIL cancel completed: StateConflict code='mission_final' message="Can't cancel a mission that's completed" problems=[{"code": "mission_final", "message": "Can't cancel a mission that's completed", "refs": {}}]
FAIL cancel by crew: Forbidden code='role_forbidden' message="Crew can't cancel missions" problems=[]
OK   complete active: {"approvals": [{"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}, {"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}], "assignm
OK   cancel pending ok: {"approvals": [], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "cancelled"}], "created_by_name": "Nora Quinn", "missi
FAIL remove_slot only (empty) new: NotFound code='not_found' message='Slot not found' problems=[]
FAIL propose not owner: Forbidden code='not_owner' message="Only the mission's owner can propose crew for this mission" problems=[]
FAIL propose crew: NotFound code='not_found' message='Mission not found' problems=[]
FAIL propose active: StateConflict code='mission_frozen' message="Can't propose crew for an active mission" problems=[{"code": "mission_frozen", "message": "Can't propose crew for an active mission", "refs": {}}]
FAIL propose pending full: RuleViolation code='rule_violation' message="Gus can't be proposed as Engineer on Deep Space Comms Upgrade" problems=[{"code": "slot_full", "message": "Engineer on Deep Space Comms Upgrade has no open pl
FAIL propose unknown crew: NotFound code='not_found' message='Crew member not found' problems=[]
FAIL propose unknown slot: NotFound code='not_found' message='Slot not found' problems=[]
FAIL propose ineligible fay (unavailable): RuleViolation code='rule_violation' message="Fay can't be proposed as Commander on Lunar Gateway Resupply" problems=[{"code": "unavailable", "message": "Fay is unavailable 2027-03-05 to 2
FAIL propose ineligible chen (skill): RuleViolation code='rule_violation' message="Chen can't be proposed as Commander on Lunar Gateway Resupply" problems=[{"code": "skill_below_minimum", "message": "Chen doesn't have Piloting (ne
OK   propose ben overlap? no: {"crew_profile_id": 7, "id": 11, "mission_id": 1, "reason": null, "slot_id": 1, "status": "proposed"}
FAIL propose gus (reboost overlap): RuleViolation code='rule_violation' message="Gus can't be proposed as Flight Engineer on Lunar Gateway Resupply" problems=[{"code": "slot_full", "message": "Flight Engineer on Lunar Gateway Resu
FAIL propose again ben: RuleViolation code='rule_violation' message="Ben can't be proposed as Mission Specialist on Lunar Gateway Resupply" problems=[{"code": "already_assigned", "message": "Ben is already proposed as Flight Engin
FAIL propose full: RuleViolation code='rule_violation' message="Chen can't be proposed as Flight Engineer on Lunar Gateway Resupply" problems=[{"code": "slot_full", "message": "Flight Engineer on Lunar Gateway Resupply has no open
FAIL propose eli commander: RuleViolation code='rule_violation' message="Eli can't be proposed as Commander on Lunar Gateway Resupply" problems=[{"code": "skill_below_minimum", "message": "Eli has Leadership 2 (needs 3)", "refs": 
OK   propose dana specialist: {"crew_profile_id": 9, "id": 12, "mission_id": 1, "reason": null, "slot_id": 2, "status": "proposed"}
FAIL accept other's: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL accept lee on ben's: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL accept ok: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL accept again: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL decline ok: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL withdraw no reason: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL withdraw proposed: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL withdraw ok: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL remove by crew: NotFound code='not_found' message='Assignment not found' problems=[]
OK   remove ok: {"crew_profile_id": 7, "id": 11, "mission_id": 1, "reason": null, "slot_id": 1, "status": "removed"}
FAIL remove again: StateConflict code='invalid_transition' message="Can't remove an assignment that is removed" problems=[{"code": "invalid_transition", "message": "Can't remove an assignment that is removed", "refs": {}}]
FAIL withdraw pending ben: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL remove active: StateConflict code='mission_frozen' message="Can't remove crew from an active mission" problems=[{"code": "mission_frozen", "message": "Can't remove crew from an active mission", "refs": {}}]
OK   my_assignments chen: [{"assignment_id": 3, "mission_id": 5, "mission_name": "Orbital Telescope Service", "mission_status": "active", "reason": null, "slot_name": "Engineer", "status": "accepted", "window": {"end": "2027-01-14
OK   my_assignments pending eli: []
```

</details>

**🔧 Bash**

```bash
cd /tmp/fixcleanup && python3 - <<'EOF'
p='snapshot.py'
s=open(p).read()
old_start=s.index('run(c, "accept other\'s", CHEN, assignments.accept, 9)')
old_end=s.index('run(c, "my_assignments chen"')
new='''run(c, "propose ana commander", LEE, assignments.propose, 1, 3, 6)
run(c, "accept other's", CHEN, assignments.accept, 11)
run(c, "accept lee on ben's", LEE, assignments.accept, 11)
run(c, "accept ok", BEN, assignments.accept, 11)
run(c, "accept again", BEN, assignments.accept, 11)
run(c, "decline ok", ANA, assignments.decline, 13, "  ")
run(c, "withdraw no reason", BEN, assignments.withdraw, 11, " ")
run(c, "withdraw proposed", DANA, assignments.withdraw, 12, "x")
run(c, "withdraw ok", BEN, assignments.withdraw, 11, "Sick")
run(c, "remove by crew", DANA, assignments.remove, 12)
run(c, "remove ok", LEE, assignments.remove, 12)
run(c, "remove again", LEE, assignments.remove, 12)
run(c, "withdraw pending ben", BEN, assignments.withdraw, 7, "Family")
run(c, "remove active", LEE, assignments.remove, 3)
run(c, "decline after withdraw", BEN, assignments.decline, 11)
'''
s=s[:old_start]+new+s[old_end:]
s=s.replace('run(c, "accept helix as other org", SAM, assignments.accept, 9)','run(c, "accept as other org", SAM, assignments.accept, 11)')
open(p,'w').write(s)
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run python /tmp/fixcleanup/snapshot.py > /tmp/fixcleanup/before.txt 2>&1; echo $?; sed -n '/propose ana/,/accept as other/p' /tmp/fixcleanup/before.txt | cut -c1-250; grep -A40 "inbox ben" /tmp/fixcleanup/before.txt | grep "^OK\|^FAIL" | cut -c1-300
```

<details>
<summary>↳ Result</summary>

```
0
OK   propose ana commander: {"crew_profile_id": 6, "id": 13, "mission_id": 1, "reason": null, "slot_id": 3, "status": "proposed"}
FAIL accept other's: NotFound code='not_found' message='Assignment not found' problems=[]
FAIL accept lee on ben's: Forbidden code='not_owner' message='You can only respond to your own assignments' problems=[]
OK   accept ok: {"crew_profile_id": 7, "id": 11, "mission_id": 1, "reason": null, "slot_id": 1, "status": "accepted"}
FAIL accept again: StateConflict code='invalid_transition' message="Can't accept an assignment that is accepted" problems=[{"code": "invalid_transition", "message": "Can't accept an assignment that is accepted", "refs": {}}]
OK   decline ok: {"crew_profile_id": 6, "id": 13, "mission_id": 1, "reason": null, "slot_id": 3, "status": "declined"}
FAIL withdraw no reason: InvalidInput code='validation_error' message='Withdrawing from Lunar Gateway Resupply needs a reason' problems=[{"code": "validation_error", "message": "Withdrawing from Lunar Gateway Resupply needs a reason", "refs": {}}]
FAIL withdraw proposed: StateConflict code='invalid_transition' message="Can't withdraw an assignment that is proposed" problems=[{"code": "invalid_transition", "message": "Can't withdraw an assignment that is proposed", "refs": {}}]
OK   withdraw ok: {"crew_profile_id": 7, "id": 11, "mission_id": 1, "reason": "Sick", "slot_id": 1, "status": "withdrawn"}
FAIL remove by crew: Forbidden code='role_forbidden' message="Crew can't remove crew" problems=[]
OK   remove ok: {"crew_profile_id": 9, "id": 12, "mission_id": 1, "reason": null, "slot_id": 2, "status": "removed"}
FAIL remove again: StateConflict code='invalid_transition' message="Can't remove an assignment that is removed" problems=[{"code": "invalid_transition", "message": "Can't remove an assignment that is removed", "refs": {}}]
OK   withdraw pending ben: {"crew_profile_id": 7, "id": 7, "mission_id": 6, "reason": "Family", "slot_id": 10, "status": "withdrawn"}
FAIL remove active: StateConflict code='mission_frozen' message="Can't remove crew from an active mission" problems=[{"code": "mission_frozen", "message": "Can't remove crew from an active mission", "refs": {}}]
FAIL decline after withdraw: StateConflict code='invalid_transition' message="Can't decline an assignment that is withdrawn" problems=[{"code": "invalid_transition", "message": "Can't decline an assignment that is withdrawn", "refs": {}}]
OK   my_assignments chen: [{"assignment_id": 3, "mission_id": 5, "mission_name": "Orbital Telescope Service", "mission_status": "active", "reason": null, "slot_name": "Engineer", "status": "accepted", "window": {"end": "2027-01-14", "start": "2027-01
OK   my_assignments pending eli: []
OK   my_assignments lee: []
FAIL accept as other org: NotFound code='not_found' message='Assignment not found' problems=[]
OK   inbox ben: {"approvals": [], "missions": [], "proposals": []}
OK   inbox lee: {"approvals": [], "missions": [{"approvals_required": 2, "eligible_approvers": 2, "mission_id": 1, "mission_name": "Lunar Gateway Resupply", "unanswered": 3, "unfilled": [], "window": {"end": "2027-03-10", "start": "2027-03-01"}}], "proposals": []}
OK   inbox ruth: {"approvals": [{"approvals": 1, "mission_id": 6, "mission_name": "Deep Space Comms Upgrade", "required": 2, "window": {"end": "2027-04-20", "start": "2027-04-01"}}], "missions": [], "proposals": []}
OK   inbox ingrid: {"approvals": [{"approvals": 1, "mission_id": 6, "mission_name": "Deep Space Comms Upgrade", "required": 2, "window": {"end": "2027-04-20", "start": "2027-04-01"}}], "missions": [], "proposals": []}
OK   inbox marco: {"approvals": [], "missions": [], "proposals": []}
OK   accept 11: {"crew_profile_id": 6, "id": 11, "mission_id": 1, "reason": null, "slot_id": 3, "status": "accepted"}
OK   accept 12: {"crew_profile_id": 8, "id": 12, "mission_id": 1, "reason": null, "slot_id": 1, "status": "accepted"}
OK   accept 13: {"crew_profile_id": 9, "id": 13, "mission_id": 1, "reason": null, "slot_id": 2, "status": "accepted"}
OK   submit gateway ok: {"approvals": [], "assignments": [{"crew_name": "Ana", "crew_profile_id": 6, "id": 11, "reason": null, "slot_id": 3, "slot_name": "Commander", "status": "accepted"}, {"crew_name": "Chen", "crew_profile_id": 8, "id": 12, "reason": null, "slot_id": 1, "slot_name": "Flight Engin
FAIL approve creator ruth: Forbidden code='approver_is_creator' message="You can't approve a mission you created" problems=[]
OK   approve ingrid: {"approvals": [{"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}], "assignments": [{"crew_name": "Ana", "crew_profile_id": 6, "id": 11, "reason": null, "slot_id": 3, "slot_name": "Commander", "status": "accepted"}, {"crew_name": "Chen", "c
FAIL approve ingrid again: StateConflict code='already_decided' message="You've already approved this round" problems=[{"code": "already_decided", "message": "You've already approved this round", "refs": {}}]
OK   approve marco: {"approvals": [{"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}, {"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}], "assignments": [{"crew_name": "Ana", "crew_profile_id": 6, "id": 11, "reason": n
OK   reject ok deep space: {"approvals": [], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "accepted"}], "created_by_name": "Nora Quinn", "mission": {"approval_round": 1, "approvals_required": 2, "created_by_id":
OK   resubmit deep space: {"approvals": [], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "accepted"}], "created_by_name": "Nora Quinn", "mission": {"approval_round": 2, "approvals_required": 2, "created_by_id": 
OK   approve deep space marco: {"approvals": [{"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, "reason": null, "slot_id": 10, "slot_name": "Engineer", "status": "accepted"}], "created_by_
OK   approve deep space ingrid: {"approvals": [{"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}, {"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}], "assignments": [{"crew_name": "Ben", "crew_profile_id": 7, "id": 7, 
OK   complete gateway: {"approvals": [{"decision": "approve", "director_id": 3, "director_name": "Ingrid Holm", "reason": null}, {"decision": "approve", "director_id": 2, "director_name": "Marco Bianchi", "reason": null}], "assignments": [{"crew_name": "Ana", "crew_profile_id": 6, "id": 11, "reason"
OK   cancel medical: {"approvals": [], "assignments": [{"crew_name": "Marco", "crew_profile_id": 2, "id": 2, "reason": null, "slot_id": 7, "slot_name": "Flight Surgeon", "status": "cancelled"}], "created_by_name": "Ruth Adeyemi", "mission": {"approval_round": 0, "approvals_required": null, "created_
OK   history 1 ruth: [{"actor_id": 1, "actor_name": "Ruth Adeyemi", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Lunar Gateway Resupply", "seeded": true}, "event": "mission.created", "from_status": null, "id": 1, "reason": null, "to_status": "draft"},
OK   history 2 ruth: [{"actor_id": 5, "actor_name": "Nora Quinn", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Asteroid Survey", "seeded": true}, "event": "mission.created", "from_status": null, "id": 2, "reason": null, "to_status": "draft"}]
OK   history 3 ruth: [{"actor_id": 5, "actor_name": "Nora Quinn", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Station Reboost", "seeded": true}, "event": "mission.created", "from_status": null, "id": 3, "reason": null, "to_status": "draft"}]
OK   history 4 ruth: [{"actor_id": 1, "actor_name": "Ruth Adeyemi", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Lunar Surface Medical Study", "seeded": true}, "event": "mission.created", "from_status": null, "id": 4, "reason": null, "to_status": "dra
OK   history 5 ruth: [{"actor_id": 4, "actor_name": "Lee Park", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Orbital Telescope Service", "seeded": true}, "event": "mission.created", "from_status": null, "id": 5, "reason": null, "to_status": "draft"}, 
OK   history 6 ruth: [{"actor_id": 5, "actor_name": "Nora Quinn", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Deep Space Comms Upgrade", "seeded": true}, "event": "mission.created", "from_status": null, "id": 10, "reason": null, "to_status": "draft"}
OK   history 7 ruth: [{"actor_id": 4, "actor_name": "Lee Park", "assignment_id": null, "at": "<datetime>", "crew_profile_id": null, "data": {"mission_name": "Mars Analog Habitat", "seeded": true}, "event": "mission.created", "from_status": null, "id": 13, "reason": null, "to_status": "draft"}, {"act
FAIL history 8 ruth: NotFound code='not_found' message='Mission not found' problems=[]
FAIL history 9 ruth: NotFound code='not_found' message='Mission not found' problems=[]
FAIL history 1 as ben: NotFound code='not_found' message='Mission not found' problems=[]
FAIL history 2 as ben: NotFound code='not_found' message='Mission not found' problems=[]
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && tail -12 /tmp/fixcleanup/before.txt | cut -c1-250; grep -n "mc \|mc-admin" README.md | head -60
```

<details>
<summary>↳ Result</summary>

```
AUDIT [2, "mission.approved", 6, null, null, null, null, null, {"mission_name": "Deep Space Comms Upgrade", "seeded": true}]
AUDIT [4, "mission.created", 7, null, null, null, "draft", null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [4, "mission.submitted", 7, null, null, "draft", "pending_approval", null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [2, "mission.approved", 7, null, null, null, null, null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [3, "mission.approved", 7, null, null, null, null, null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [3, "mission.activated", 7, null, null, "pending_approval", "active", null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [4, "mission.completed", 7, null, null, "active", "completed", null, {"mission_name": "Mars Analog Habitat", "seeded": true}]
AUDIT [15, "mission.created", 8, null, null, null, "draft", null, {"mission_name": "Payload Demo 1", "seeded": true}]
AUDIT [1, "mission.transferred", 1, null, null, null, null, null, {"from_owner_id": 4, "from_owner_name": "Lee Park", "mission_name": "Lunar Gateway Resupply", "to_owner_id": 5, "to_owner_name": "Nora Quinn"}]
AUDIT [5, "assignment.proposed", 1, 11, 7, null, "proposed", null, {"crew_name": "Ben", "mission_name": "Lunar Gateway Resupply", "slot_name": "Flight Engineer"}]
AUDIT [5, "assignment.proposed", 1, 12, 6, null, "proposed", null, {"crew_name": "Ana", "mission_name": "Lunar Gateway Resupply", "slot_name": "Commander"}]
AUDIT [5, "assignment.proposed", 1, 13, 9, null, "proposed", null, {"crew_name": "Dana", "mission_name": "Lunar Gateway Resupply", "slot_name": "Mission Specialist"}]
14:uv run mc-admin seed --reset      # demo data in ./mission_control.db
21:uv run mc login --email lee@aurora.example    # password: orbital launch window
22:uv run mc missions list
25:Every demo account's password is `orbital launch window`. `mc login` asks for it with the input hidden.
29:Lunar Gateway Resupply (mission 1) is a draft with three empty slots. Take it all the way to Completed. Each `mc login` replaces the previous session, so one terminal is enough. Start from a fresh seed (`uv run mc-admin seed --reset`, with the server stopped).
34:uv run mc login --email lee@aurora.example
35:uv run mc inbox
36:uv run mc missions match 1                     # Commander → Ana, Flight Engineer → Chen, Mission Specialist → Dana
37:uv run mc missions match 1 --apply             # proposes them as assignments 11, 12 and 13
43:uv run mc login --email ana@aurora.example
44:uv run mc assignments list --pending
45:uv run mc assignments accept 11
46:uv run mc login --email chen@aurora.example
47:uv run mc assignments accept 12
48:uv run mc login --email dana@aurora.example
49:uv run mc assignments accept 13
55:uv run mc login --email lee@aurora.example
56:uv run mc missions submit 1
62:uv run mc login --email ruth@aurora.example
63:uv run mc missions approve 1                   # refused: Ruth created this mission
64:uv run mc login --email marco@aurora.example
65:uv run mc missions approve 1                   # pending approval, 1 of 2
66:uv run mc login --email ingrid@aurora.example
67:uv run mc missions approve 1                   # 2 of 2: the mission is active
73:uv run mc login --email lee@aurora.example
74:uv run mc missions complete 1
75:uv run mc missions history 1
81:uv run mc login --email sam@helix.example
82:uv run mc missions list                        # only Helix's Payload Demo 1
83:uv run mc missions show 1                      # refused: looks exactly like an unknown ID
116:## Operators: `mc-admin`
118:`mc-admin` works on the database file directly, so run it on the machine that runs `mc-server`. There's no self-service signup: organisations come from the seed or from `create-org`.
121:uv run mc-admin init-db                        # an empty database, if you don't want the demo data
122:uv run mc-admin create-org --name "Orion Labs" --director-email zoe@orion.example --director-name "Zoe Lin"
125:`create-org` asks for the Director's password twice with the input hidden (at least 15 characters). Without a terminal, pipe it on stdin. The new organisation needs 1 approval per mission and starts with an empty skill catalogue. Its Director logs in with `mc` and sets up the rest (`mc skills add`, `mc users add`, `mc org set-approvals`).
127:`mc-admin seed` refuses a database that already has data. `seed --reset` deletes the file and everything in it first. Stop the server before resetting.
135:| `MC_DATABASE_PATH` | `mission_control.db` in the current folder | `mc-server`, `mc-admin` |
137:| `MC_DB_BUSY_TIMEOUT_MS` | `5000` | `mc-server`, `mc-admin` |
150:Every test gets its own temporary SQLite file. `tests/cli/test_readme_smoke.py` runs this README's `mc-admin`, `mc-server` and `mc` commands for real, in order.
169:                and tokens, and the organisation statements mc-admin needs
172:  cli/          the mc command, a client of the HTTP API
173:  seed/         the demo data, shared by mc-admin and the tests
174:  admin_cli.py  mc-admin: init-db, seed, create-org
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -n '@command(app, "' src/mission_control/cli/commands/missions.py; grep -n "mc-server\|uvicorn" README.md pyproject.toml | head; grep -n "password\|getpass\|stdin" src/mission_control/cli/commands/account.py | head
```

<details>
<summary>↳ Result</summary>

```
233:@command(app, "list", example="mc missions list")
255:@command(app, "show", example="mc missions show 1")
339:@command(app, "history", example="mc missions history 1")
369:@command(app, "edit", example="mc missions edit 1 --end 2027-03-12")
487:@command(app, "match", example="mc missions match 1")
664:@command(app, "remove-crew", example="mc missions remove-crew 1 21")
699:@command(app, "submit", example="mc missions submit 1")
714:@command(app, "approve", example="mc missions approve 1")
729:@command(app, "reject", example='mc missions reject 6 --reason "Roster too thin"')
740:@command(app, "transfer", example="mc missions transfer 1 --owner nora@aurora.example")
766:@command(app, "complete", example="mc missions complete 5")
780:@command(app, "cancel", example='mc missions cancel 1 --reason "Budget cut"')
README.md:15:uv run mc-server                  # API on http://127.0.0.1:8000; leave it running
README.md:118:`mc-admin` works on the database file directly, so run it on the machine that runs `mc-server`. There's no self-service signup: organisations come from the seed or from `create-org`.
README.md:135:| `MC_DATABASE_PATH` | `mission_control.db` in the current folder | `mc-server`, `mc-admin` |
README.md:136:| `MC_TOKEN_TTL_HOURS` | `12` | `mc-server` |
README.md:137:| `MC_DB_BUSY_TIMEOUT_MS` | `5000` | `mc-server`, `mc-admin` |
README.md:140:`mc-server` listens on `127.0.0.1:8000`. `mc` keeps its session token in `~/.config/mission-control/credentials.json`, readable only by you.
README.md:150:Every test gets its own temporary SQLite file. `tests/cli/test_readme_smoke.py` runs this README's `mc-admin`, `mc-server` and `mc` commands for real, in order.
README.md:171:  api/          FastAPI app (mc-server): validates input, resolves the caller, maps errors
pyproject.toml:12:    "uvicorn>=0.30",
pyproject.toml:18:mc-server = "mission_control.api.app:main"
1:"""Signing in and out, who am I, changing my password, and what's waiting on me."""
23:    command(app, "password", example="mc password")(password)
36:    """Log in. Your password is asked for with the input hidden.
38:    Without a terminal, pass --email and pipe the password on stdin.
46:            "the password on stdin.",
50:        session = env.anonymous_api().post("/auth/login", {"email": email, "password": secret})
111:def password(ctx: typer.Context) -> None:
112:    """Change your password. Asks for your current one, then the new one twice.
114:    Without a terminal, pipe the current and new passwords on stdin, one per line. Every session
119:    current = ask_secret(env, "Current password")
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/api/app.py | head -50; sed -n 487,500p src/mission_control/cli/commands/missions.py; sed -n 369,390p src/mission_control/cli/commands/missions.py
```

<details>
<summary>↳ Result</summary>

```
"""The HTTP API: JSON under /api/v1, authenticated with `Authorization: Bearer <token>`."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mission_control.api import errors
from mission_control.api.routers import admin, assignments, auth, crew, missions
from mission_control.infra import security
from mission_control.infra.db import connect, init_db
from mission_control.infra.settings import Settings

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Settings come from the environment unless given."""
    config = settings if settings is not None else Settings.from_env(os.environ)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        conn = connect(config.database_path, busy_timeout_ms=config.busy_timeout_ms)
        try:
            init_db(conn)  # refuses an unsupported SQLite or schema; creates an empty schema
        finally:
            conn.close()
        # Login checks unknown emails against this hash, so it costs the same as a real check.
        # Making it now keeps the first such login as slow as every other.
        security.dummy_hash()
        yield

    app = FastAPI(title="Mission Control", lifespan=lifespan)
    app.state.settings = config
    errors.install(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (auth.router, admin.router, crew.router, missions.router, assignments.router):
        app.include_router(router, prefix=API_PREFIX)
    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
@command(app, "match", example="mc missions match 1")
def match(
    ctx: typer.Context,
    mission_id: MissionId,
    apply: Annotated[
        bool, typer.Option("--apply", help="Propose the suggested crew (owner only)")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print the suggestion as JSON")
    ] = False,
) -> None:
    """Suggest crew for a draft mission's open places. Nothing is changed.

    Owner or Director.
@command(app, "edit", example="mc missions edit 1 --end 2027-03-12")
def edit(
    ctx: typer.Context,
    mission_id: MissionId,
    name: NewName = None,
    start_date: NewStart = None,
    end_date: NewEnd = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Change a mission's name or dates. Owner only.

    A mission pending approval goes back to Draft, so you're asked first.
    """
    body = {"name": name, "start_date": start_date, "end_date": end_date}
    body = {k: v for k, v in body.items() if v is not None}
    if not body:
        raise UsageProblem("Nothing to change. Pass --name, --start or --end.")
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id, **_invalidated_hints(mission_id)):
        mission = api.get(f"/missions/{mission_id}")
```

</details>

**🔧 Bash**

```bash
mkdir -p /tmp/fixcleanup && cat > /tmp/fixcleanup/golden.sh <<'EOF'
#!/bin/bash
# Usage: golden.sh <worktree> <outfile>
set -u
WT=$1; OUT=$2
cd "$WT"
export MC_DATABASE_PATH=/tmp/fixcleanup/x.db
rm -rf /tmp/fixcleanup/home_*
uv run mc-admin seed --reset >/dev/null 2>&1 || { echo "seed failed"; exit 1; }
PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
uv run uvicorn --factory mission_control.api.app:create_app --host 127.0.0.1 --port $PORT >/tmp/fixcleanup/server.log 2>&1 &
SERVER=$!
for i in $(seq 1 50); do curl -s http://127.0.0.1:$PORT/health >/dev/null && break; sleep 0.2; done
export MC_API_URL=http://127.0.0.1:$PORT
as() { local who=$1; shift; mkdir -p /tmp/fixcleanup/home_$who
  if [ ! -f /tmp/fixcleanup/home_$who/.logged ]; then
    echo "orbital launch window" | HOME=/tmp/fixcleanup/home_$who uv run mc login --email $who@aurora.example >/dev/null 2>&1
    touch /tmp/fixcleanup/home_$who/.logged
  fi
  HOME=/tmp/fixcleanup/home_$who COLUMNS=200 uv run mc "$@" 2>&1; }
{
as lee missions match 1 --apply >/dev/null
as ana assignments accept 11 >/dev/null
as chen assignments accept 12 >/dev/null
as dana assignments accept 13 >/dev/null
as lee missions submit 1 >/dev/null
as ruth missions approve 1 >/dev/null
as marco missions approve 1 >/dev/null
as ingrid missions approve 1 >/dev/null
as lee missions complete 1 >/dev/null
echo "### mc missions history 1"
as lee missions history 1
echo "### extra: transfer 6 to lee, lee edits name and end date, history 6"
as ruth missions transfer 6 --owner lee@aurora.example --yes >/dev/null
as lee missions edit 6 --name "Deep Space Comms II" --end 2027-04-21 --yes >/dev/null
as lee missions history 6
} > "$OUT"
kill $SERVER; wait $SERVER 2>/dev/null
EOF
chmod +x /tmp/fixcleanup/golden.sh; /tmp/fixcleanup/golden.sh /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup /tmp/fixcleanup/golden_before.txt; cat /tmp/fixcleanup/golden_before.txt
```

<details>
<summary>↳ Result</summary>

```
### mc missions history 1
  When (UTC)          Who             What
  12 Oct 2026 05:23   Ruth Adeyemi    Created the mission
  12 Oct 2026 05:23   Lee Park        Proposed Ana for Commander
  12 Oct 2026 05:23   Lee Park        Proposed Chen for Flight Engineer
  12 Oct 2026 05:23   Lee Park        Proposed Dana for Mission Specialist
  12 Oct 2026 05:23   Ana Okafor      Accepted Commander
  12 Oct 2026 05:23   Chen Wu         Accepted Flight Engineer
  12 Oct 2026 05:23   Dana Reyes      Accepted Mission Specialist
  12 Oct 2026 05:23   Lee Park        Submitted for approval
  12 Oct 2026 05:23   Marco Bianchi   Approved
  12 Oct 2026 05:23   Ingrid Holm     Approved
  12 Oct 2026 05:23   Ingrid Holm     Mission became active
  12 Oct 2026 05:23   Lee Park        Completed
  12 Oct 2026 05:23   Lee Park        Ana's assignment completed
  12 Oct 2026 05:23   Lee Park        Chen's assignment completed
  12 Oct 2026 05:23   Lee Park        Dana's assignment completed
### extra: transfer 6 to lee, lee edits name and end date, history 6
  When (UTC)          Who             What
  12 Oct 2026 05:23   Nora Quinn      Created the mission
  12 Oct 2026 05:23   Nora Quinn      Submitted for approval
  12 Oct 2026 05:23   Marco Bianchi   Approved
  12 Oct 2026 05:23   Ruth Adeyemi    Handed the mission to Lee Park
  12 Oct 2026 05:23   Ruth Adeyemi    Mission went back to Draft
  12 Oct 2026 05:23   Lee Park        Edited the mission
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run pytest -W error -q -o addopts='' 2>&1 | tail -3; uv run ruff check | tail -1; uv run ruff format --check | tail -1
```

<details>
<summary>↳ Result</summary>

```
........................................................................ [ 97%]
.........................................                                [100%]
1697 passed in 23.58s
All checks passed!
152 files already formatted
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "def join_names\|def _join\|join_names\b" src | grep -v "^.*:.*join_names(" ; grep -rn "def .*join" src; grep -rn "from mission_control.domain" src/mission_control/cli | head
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/cli/commands/missions.py:25:from mission_control.cli.render import Span, Terminal, format_timestamp, join_names, plural
src/mission_control/services/missions/slots.py:27:    join_names,
src/mission_control/services/missions/changes.py:34:    join_names,
src/mission_control/services/admin.py:358:def _join(names: Iterable[str]) -> str:
src/mission_control/cli/render.py:137:def join_names(names: Sequence[str]) -> str:
src/mission_control/domain/eligibility.py:168:def _join_names(names: list[str]) -> str:
src/mission_control/services/missions/rules.py:157:def join_names(names: Sequence[str]) -> str:
src/mission_control/services/admin.py:358:def _join(names: Iterable[str]) -> str:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/domain/dates.py; sed -n 130,236p src/mission_control/domain/lifecycle.py
```

<details>
<summary>↳ Result</summary>

```
"""Calendar date ranges. Dates have no time or time zone; both ends are inclusive."""

from dataclasses import dataclass
from datetime import date


class InvalidDateRange(ValueError):
    """The end date is before the start date."""


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise InvalidDateRange(
                f"end date {self.end.isoformat()} is before start date {self.start.isoformat()}"
            )

    def overlaps(self, other: "DateRange") -> bool:
        """True if the ranges share at least one calendar day, including a boundary day."""
        return self.start <= other.end and other.start <= self.end

    @property
    def mission_days(self) -> int:
        """Days from start to end, counting both."""
        return (self.end - self.start).days + 1

# Assignments


# action -> (assignment states it may start from, mission states it's allowed in). Its keys
# are the assignment actions. PROPOSE_CREW creates the assignment, so it has no starting state.
_ASSIGNMENT_RULES: Mapping[
    Action, tuple[frozenset[AssignmentStatus] | None, frozenset[MissionStatus]]
] = MappingProxyType(
    {
        Action.PROPOSE_CREW: (None, frozenset({M.DRAFT, M.PENDING_APPROVAL})),
        Action.ACCEPT: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
        Action.DECLINE: (frozenset({A.PROPOSED}), frozenset({M.DRAFT})),
        Action.WITHDRAW: (
            frozenset({A.ACCEPTED}),
            frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        ),
        Action.REMOVE_CREW: (
            frozenset({A.PROPOSED, A.ACCEPTED}),
            frozenset({M.DRAFT, M.PENDING_APPROVAL}),
        ),
    }
)

_ASSIGNMENT_RESULT: Mapping[Action, AssignmentStatus] = MappingProxyType(
    {
        Action.PROPOSE_CREW: A.PROPOSED,
        Action.ACCEPT: A.ACCEPTED,
        Action.DECLINE: A.DECLINED,
        Action.WITHDRAW: A.WITHDRAWN,
        Action.REMOVE_CREW: A.REMOVED,
    }
)

# How each assignment action reads before "a mission ...".
_ASSIGNMENT_PHRASE: Mapping[Action, str] = MappingProxyType(
    {
        Action.PROPOSE_CREW: "propose crew for",
        Action.ACCEPT: "accept a proposal on",
        Action.DECLINE: "decline a proposal on",
        Action.WITHDRAW: "withdraw from",
        Action.REMOVE_CREW: "remove crew from",
    }
)

# Actions that change the roster, and so send a pending mission back to Draft.
_ROSTER_CHANGES = frozenset({Action.PROPOSE_CREW, Action.WITHDRAW, Action.REMOVE_CREW})

# How each assignment action reads before "an assignment ...".
_ASSIGNMENT_VERB: Mapping[Action, str] = MappingProxyType(
    {
        Action.PROPOSE_CREW: "propose",
        Action.ACCEPT: "accept",
        Action.DECLINE: "decline",
        Action.WITHDRAW: "withdraw",
        Action.REMOVE_CREW: "remove",
    }
)


def _require_assignment_action(action: Action) -> None:
    if action not in _ASSIGNMENT_RULES:
        raise ValueError(f"{action!r} is not an assignment action; use the mission functions")


def assignment_problem(
    action: Action, current: AssignmentStatus | None, mission: MissionStatus
) -> Problem | None:
    """Why assignment `action` isn't allowed, or None. Mission state is checked before
    assignment state. Raises ValueError for an action that isn't an assignment action."""
    _require_assignment_action(action)
    from_states, mission_states = _ASSIGNMENT_RULES[action]
    if mission not in mission_states:
        return _wrong_state(mission, _ASSIGNMENT_PHRASE[action])
    if from_states is not None and current not in from_states:
        label = current.value if current else "missing"
        return Problem(
            "invalid_transition", f"Can't {_ASSIGNMENT_VERB[action]} an assignment that is {label}"
        )
    return None


def assignment_status_after(action: Action) -> AssignmentStatus:
    _require_assignment_action(action)
    return _ASSIGNMENT_RESULT[action]


def mission_status_after_assignment_action(mission: MissionStatus, action: Action) -> MissionStatus:
    _require_assignment_action(action)
    return _after_change(mission) if action in _ROSTER_CHANGES else mission


def cascade(mission_final_status: MissionStatus, assignment: AssignmentStatus) -> AssignmentStatus:
    """What an assignment becomes when its mission completes or is cancelled."""
    if mission_final_status == M.COMPLETED and assignment == A.ACCEPTED:
        return A.COMPLETED
    if mission_final_status == M.CANCELLED and assignment in (A.PROPOSED, A.ACCEPTED):
        return A.CANCELLED
    return assignment


# Submit guard


def roster_problems(roster: Sequence[RosterEntry], window: DateRange) -> list[Problem]:
    """Accepted crew who are no longer eligible, e.g. after a skill change. Checked at submit
    and again at every approval."""
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/cli/main.py; sed -n 1,90p src/mission_control/admin_cli.py; cat src/mission_control/cli/resolve.py
```

<details>
<summary>↳ Result</summary>

```
"""The `mc` entry point: every command group, the global options, and a quiet exit when the
reader of a pipe goes away."""

import os
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Annotated

import typer

from mission_control.cli.commands import account, admin, assignments, crew, me, missions
from mission_control.cli.commands.common import group
from mission_control.cli.env import Env

app = group(name="mc")
account.register(app)
app.add_typer(me.app, name="me")
app.add_typer(assignments.app, name="assignments")
app.add_typer(missions.app, name="missions")
app.add_typer(crew.app, name="crew")
app.add_typer(admin.users_app, name="users")
app.add_typer(admin.skills_app, name="skills")
app.add_typer(admin.org_app, name="org")


def _show_version(value: bool) -> None:
    if value:
        try:
            number = version("mission-control")
        except PackageNotFoundError:
            number = "unknown"
        typer.echo(f"mc {number}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    show_version: Annotated[
        bool,
        typer.Option(
            "--version", help="Show the version and exit", callback=_show_version, is_eager=True
        ),
    ] = False,
) -> None:
    """Mission Control: plan missions, crew them and get them approved.

    Start with mc login, then mc inbox. Every command has --help.

    Exit codes: 0 OK, 1 refused, 2 usage, 3 not logged in, 4 server unreachable or busy,
    130 interrupted.
    """
    if ctx.obj is None:
        ctx.obj = Env()


def main() -> None:
    try:
        app(prog_name="mc")
    finally:
        _flush_quietly()


def _flush_quietly() -> None:
    """`mc ... | head` closes the pipe early; don't end with a broken-pipe traceback."""
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
"""`mc-admin`: operator commands for the machine that runs the server. They work on the database
file directly rather than through the API: set up the schema, load the demo data, and create an
organisation with its first Director (there is no self-service signup)."""

import getpass
import os
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Generator
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any

import typer
from typer.core import TyperGroup

from mission_control.domain.enums import Role
from mission_control.domain.passwords import (
    MIN_PASSWORD_LENGTH,
    PasswordTooShort,
    validate_password,
)
from mission_control.infra import platform, security
from mission_control.infra.db import DatabaseBusy, UnsupportedSQLite, connect, init_db, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.settings import Settings
from mission_control.seed import data
from mission_control.seed.loader import load_seed

OK, FAILED, USAGE, INTERRUPTED = 0, 1, 2, 130
_RESET = "uv run mc-admin seed --reset (deletes everything in it)"


class Failure(Exception):
    """Something to tell the operator, with an optional next step, and the exit code to use."""

    def __init__(self, message: str, *, hint: str | None = None, exit_code: int = FAILED):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.exit_code = exit_code


class _Group(TyperGroup):
    """A bare `mc-admin` prints its help and exits 0. Failures are reported in words with their
    exit code, never as a traceback."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(OK)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except Failure as failure:
            _error(failure.message, failure.hint)
            raise typer.Exit(failure.exit_code) from None
        except KeyboardInterrupt:
            _error("Interrupted. Nothing was changed.")
            raise typer.Exit(INTERRUPTED) from None


app = typer.Typer(
    cls=_Group,
    name="mc-admin",
    rich_markup_mode=None,
    add_completion=False,
    pretty_exceptions_enable=False,
)


def _example(*lines: str) -> str:
    heading = "Example:" if len(lines) == 1 else "Examples:"
    # \b stops the help formatter from re-wrapping the lines.
    return "\b\n" + heading + "\n" + "\n".join(f"  {line}" for line in lines)


def _show_version(value: bool) -> None:
    if value:
        try:
            number = version("mission-control")
        except PackageNotFoundError:
            number = "unknown"
        typer.echo(f"mc-admin {number}")
        raise typer.Exit()
"""Turning what the user types into what the API expects. Missions and assignments are IDs;
people are found by email, skills by name and slots by name or position. Also parses the
`--slot` spec, e.g. `Commander:1:Piloting>=4,Leadership>=3`.

Only syntax is checked here. Whether a headcount or level is allowed is the server's call."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from mission_control.cli.client import Api
from mission_control.cli.errors import Refused, UsageProblem

SLOT_FORMAT = "NAME:HEADCOUNT:SKILL>=LEVEL[,SKILL>=LEVEL...]"
SLOT_EXAMPLE = "Commander:1:Piloting>=4,Leadership>=3"
REQUIREMENTS_FORMAT = "SKILL>=LEVEL[,SKILL>=LEVEL...]"


class SpecError(UsageProblem):
    pass


@dataclass(frozen=True)
class SlotSpec:
    name: str
    headcount: int
    requirements: tuple[tuple[str, int], ...]  # (skill name, minimum level), as typed


def parse_slot_spec(text: str) -> SlotSpec:
    parts = text.rsplit(":", 2)
    if len(parts) != 3 or not parts[0].strip():
        raise _slot_error(text)
    name, headcount, requirements = (p.strip() for p in parts)
    try:
        count = int(headcount)
    except ValueError:
        raise _slot_error(text) from None
    try:
        parsed = parse_requirements(requirements) if requirements else ()
    except SpecError:
        raise _slot_error(text) from None
    return SlotSpec(name, count, parsed)


def parse_requirements(text: str) -> tuple[tuple[str, int], ...]:
    requirements = []
    for entry in text.split(","):
        skill, sep, level = entry.partition(">=")
        skill, level = skill.strip(), level.strip()
        if not sep or not skill or not level.lstrip("-").isdigit():
            raise SpecError(
                f"'{entry.strip()}' isn't a requirement. Use {REQUIREMENTS_FORMAT}, "
                "e.g. Piloting>=4,Leadership>=3."
            )
        requirements.append((skill, int(level)))
    return tuple(requirements)


def _slot_error(text: str) -> SpecError:
    return SpecError(f"'{text}' isn't a slot. Use {SLOT_FORMAT}, e.g. {SLOT_EXAMPLE}.")


# References


def skill_ids(api: Api, names: Sequence[str]) -> dict[str, int]:
    """Skill names (any case) to IDs, from the organisation's catalogue."""
    catalogue = {s["name"].casefold(): s for s in api.get("/skills")}
    found: dict[str, int] = {}
    for name in names:
        skill = catalogue.get(name.casefold())
        if skill is None:
            raise Refused(
                f"There's no skill called '{name}'", hint="See the skills: mc skills list"
            )
        found[name] = skill["id"]
    return found


def skill_named(api: Api, name: str) -> dict[str, Any]:
    for skill in api.get("/skills"):
        if skill["name"].casefold() == name.casefold():
            return skill
    raise Refused(f"There's no skill called '{name}'", hint="See the skills: mc skills list")


def requirement_body(
    requirements: Sequence[tuple[str, int]], ids: Mapping[str, int]
) -> list[dict[str, int]]:
    return [{"skill_id": ids[name], "min_level": level} for name, level in requirements]


def crew_by_email(api: Api, email: str) -> dict[str, Any]:
    for person in api.get("/crew"):
        if person["email"].casefold() == email.strip().casefold():
            return person
    raise Refused(
        f"There's no crew member with the email {email}", hint="See the crew: mc crew list"
    )


def user_by_email(api: Api, email: str) -> dict[str, Any]:
    for user in api.get("/users"):
        if user["email"].casefold() == email.strip().casefold():
            return user
    raise Refused(f"There's no user with the email {email}", hint="See the users: mc users list")


def slot_in(mission: Mapping[str, Any], ref: str) -> dict[str, Any]:
    """A live slot by position (`2`) or by name, ignoring case (`Flight Engineer`)."""
    slots = mission["slots"]
    ref = ref.strip()
    if ref.isdigit():
        match = [s for s in slots if s["position"] == int(ref)]
        missing = f"{mission['name']} has no slot {ref}"
    else:
        match = [s for s in slots if s["name"].casefold() == ref.casefold()]
        missing = f"{mission['name']} has no slot called '{ref}'"
    if not match:
        listed = ", ".join(f"{s['position']} {s['name']}" for s in slots)
        raise Refused(missing, hint=f"Its slots: {listed}")
    return match[0]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 90,140p src/mission_control/admin_cli.py; cat src/mission_control/cli/commands/common.py; grep -rn "skill_named\|skill_ids" src | grep -v "def "
```

<details>
<summary>↳ Result</summary>

```
        raise typer.Exit()


@app.callback()
def root(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version", help="Show the version and exit", callback=_show_version, is_eager=True
        ),
    ] = False,
) -> None:
    """Operator commands for Mission Control.

    They work on the database file directly, so run them on the machine that runs mc-server.
    The file is MC_DATABASE_PATH, or mission_control.db in the current folder.

    Exit codes: 0 OK, 1 refused or failed, 2 usage, 130 interrupted.
    """


# --- Commands -----------------------------------------------------------------------------


@app.command("init-db", epilog=_example("mc-admin init-db"))
def init_database() -> None:
    """Create an empty database with the current schema. Safe to run again."""
    settings = _settings()
    path = _shown(settings.database_path)
    with _database(settings) as conn:
        created = _prepare(conn, path)
    if created:
        typer.echo(f"Created an empty database at {path}.")
        _next_steps(["uv run mc-admin seed", "uv run mc-admin create-org --help"])
    else:
        typer.echo(f"The database at {path} is already set up.")


@app.command("seed", epilog=_example("mc-admin seed", "mc-admin seed --reset"))
def seed(
    reset: Annotated[
        bool,
        typer.Option("--reset", help="Delete the database file first, and everything in it"),
    ] = False,
) -> None:
    """Load the demo organisations, people and missions.

    Every demo user's password is the demo passphrase. Without --reset, a database that already
    has data is left as it is. Stop mc-server before using --reset.
    """
    settings = _settings()
"""Plumbing every command shares: the group and command classes (help layout, error handling),
the current `Env`, and common options."""

from datetime import date
from typing import Annotated, Any

import typer
from typer.core import TyperCommand, TyperGroup

from mission_control.cli.client import ApiError, Unreachable
from mission_control.cli.env import Env
from mission_control.cli.errors import CliError
from mission_control.cli.refusals import report


class Command(TyperCommand):
    """Usage lines that spell out the options (`mc missions match MISSION_ID [--apply]`), and
    the epilog shown as an example block."""

    def collect_usage_pieces(self, ctx: typer.Context) -> list[str]:
        pieces: list[str] = []
        options: list[str] = []
        for param in self.get_params(ctx):
            if param.param_type_name == "argument":
                pieces.append(param.make_metavar(ctx))
            elif param.param_type_name == "option" and param.name != "help" and not param.hidden:
                flag = max(param.opts, key=len)
                text = flag if param.is_flag else f"{flag} {param.make_metavar(ctx)}"
                options.append(text if param.required else f"[{text}]")
        return pieces + options

    def format_epilog(self, ctx: typer.Context, formatter: Any) -> None:
        if not self.epilog:
            return
        examples = [line.strip() for line in self.epilog.strip().splitlines() if line.strip()]
        formatter.write_paragraph()
        formatter.write_text("Example:" if len(examples) == 1 else "Examples:")
        with formatter.indentation():
            for line in examples:
                formatter.write(f"{' ' * formatter.current_indent}{line}\n")


class Group(TyperGroup):
    """A bare group prints its help and exits 0. Failures raised by commands are reported here
    with their exit code, so tests and real runs behave the same."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except (CliError, ApiError, Unreachable, KeyboardInterrupt) as failure:
            env = ctx.find_object(Env) or Env()
            raise typer.Exit(report(env, failure)) from None


def group(help: str | None = None, name: str | None = None) -> typer.Typer:
    """A command group. Without `help`, its callback's docstring is the help."""
    named: dict[str, str] = {"help": help} if help else {}
    if name:
        named["name"] = name
    return typer.Typer(
        cls=Group,
        rich_markup_mode=None,
        add_completion=False,
        pretty_exceptions_enable=False,
        **named,
    )


def start(ctx: typer.Context, json_output: bool = False) -> Env:
    """The command's Env, remembering whether output is JSON so refusals print as JSON too."""
    env = ctx.ensure_object(Env)
    env.json_output = json_output
    return env


def iso_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise typer.BadParameter(
            f"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2027-03-01."
        ) from None


Json = Annotated[bool, typer.Option("--json", help="Print the result as JSON")]
Yes = Annotated[bool, typer.Option("--yes", "-y", help="Don't ask for confirmation")]
MissionId = Annotated[int, typer.Argument(metavar="MISSION_ID", help="The mission's ID")]
Email = Annotated[str, typer.Argument(metavar="EMAIL", help="The person's email address")]


def command(app: typer.Typer, name: str, example: str | None = None, **settings: Any) -> Any:
    """Register a command with the shared help layout. `example` lines appear under Example."""
    return app.command(name, cls=Command, epilog=example, **settings)
src/mission_control/cli/commands/missions.py:32:    skill_ids,
src/mission_control/cli/commands/missions.py:175:    ids = skill_ids(api, [name for spec in parsed for name, _ in spec.requirements])
src/mission_control/cli/commands/missions.py:448:            ids = skill_ids(api, [n for n, _ in requirements])
src/mission_control/cli/commands/admin.py:12:from mission_control.cli.resolve import skill_named, user_by_email
src/mission_control/cli/commands/admin.py:192:    skill = skill_named(api, name)
src/mission_control/cli/commands/admin.py:205:    skill = skill_named(api, name)
src/mission_control/cli/commands/crew.py:11:from mission_control.cli.resolve import crew_by_email, skill_named
src/mission_control/cli/commands/crew.py:82:        return skill_named(api, name)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat src/mission_control/cli/__init__.py; grep -rn "_show_version\|_Group\|parse_args" tests | head; cat pyproject.toml | sed -n '/ruff/,$p'
```

<details>
<summary>↳ Result</summary>

```
"""`mc`, the Mission Control command-line client. It reaches the system only through the HTTP
API."""
    "ruff>=0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mission_control"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["docs", ".claude"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat tests/integration/test_repository_sql.py; grep -n "execute\|EXEMPT\|noqa\|cross" src/mission_control/infra/platform.py | head -30
```

<details>
<summary>↳ Result</summary>

```
"""Guard test (design §4): every SQL statement in infra/repositories filters on the caller's org,
bound by name as `org_id = :org`, and no statement uses positional `?` placeholders.

infra/platform.py is scanned by the same rules. Its only exemption is the organisation statements
listed in PLATFORM_EXEMPT, which run before any tenant exists to scope by (mc-admin create-org);
they must still bind by name. admin_cli.py holds no SQL at all."""

import ast
import re
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "src/mission_control"
REPOS = PACKAGE / "infra/repositories"
PLATFORM = PACKAGE / "infra/platform.py"
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
# organisation by slug across every tenant, and creating one. Nothing else is exempt.
PLATFORM_EXEMPT = frozenset(
    {
        "SELECT name FROM organisations WHERE slug = :slug",
        "INSERT INTO organisations(name, slug) VALUES (:name, :slug)",
    }
)


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
    return PLATFORM_EXEMPT if name == PLATFORM.name else frozenset()


def sql_strings(paths=None):
    """Every SQL literal in the repositories and the platform module. An f-string is read as
    one statement: its literal parts are joined and each interpolation is shown as {...}."""
    for path in paths or [*sorted(REPOS.glob("*.py")), PLATFORM]:
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


def test_the_platform_module_is_scanned_and_every_exemption_is_in_use():
    platform_sql = {_normal(sql) for name, _, sql in sql_strings() if name == PLATFORM.name}
    assert PLATFORM_EXEMPT <= platform_sql, "an exemption no longer matches platform.py"


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
10:    row = conn.execute(
18:    cursor = conn.execute(
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "security\.\(find_login\|login_state\|password_hash_of\|set_password_hash\|store_token\|find_session\|revoke_token\|revoke_user_tokens\)" src tests | grep -v "^tests.*monkeypatch" ; grep -n -A12 "CREATE TABLE auth_tokens\|CREATE TABLE users" src/mission_control/infra/schema.sql; cat src/mission_control/infra/platform.py
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/admin_cli.py:315:    if security.find_login(conn, email) is not None:
src/mission_control/services/admin.py:85:        if security.find_login(ctx.conn, email) is not None:
src/mission_control/services/admin.py:174:        security.revoke_user_tokens(ctx.conn, user.id, ctx.now)
src/mission_control/services/auth.py:53:    found = security.find_login(conn, email)
src/mission_control/services/auth.py:68:        current = security.login_state(conn, found["id"])
src/mission_control/services/auth.py:74:            security.set_password_hash(conn, found["id"], upgraded_hash)
src/mission_control/services/auth.py:75:        security.store_token(conn, found["id"], security.hash_token(token), now, expires)
src/mission_control/services/auth.py:89:        row = security.find_session(conn, security.hash_token(token), _now(now))
src/mission_control/services/auth.py:112:        security.revoke_token(conn, security.hash_token(token), _now(now))
src/mission_control/services/auth.py:121:    security.revoke_user_tokens inside its own write_tx, next to its audit write."""
src/mission_control/services/auth.py:123:        security.revoke_user_tokens(conn, user_id, _now(now))
src/mission_control/services/auth.py:139:    verified_hash = security.password_hash_of(conn, actor.user_id)
src/mission_control/services/auth.py:144:        if security.password_hash_of(conn, actor.user_id) != verified_hash:
src/mission_control/services/auth.py:146:        security.set_password_hash(conn, actor.user_id, new_hash)
src/mission_control/services/auth.py:147:        security.revoke_user_tokens(conn, actor.user_id, now)
tests/integration/test_admin_service.py:226:    stored = security.password_hash_of(seeded_db, user.id)
tests/integration/test_admin_service.py:624:    real = security.revoke_user_tokens
tests/integration/test_admin_service.py:636:    security.store_token(seeded_db, BEN_ID, "ben-session", NOW, datetime(2027, 1, 6, tzinfo=UTC))
14:CREATE TABLE users (
15-  id            INTEGER PRIMARY KEY,
16-  org_id        INTEGER NOT NULL REFERENCES organisations(id),
17-  email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,   -- login is by email only
18-  name          TEXT    NOT NULL CHECK (length(trim(name)) > 0),
19-  role          TEXT    NOT NULL CHECK (role IN ('director','lead','crew')),
20-  password_hash TEXT    NOT NULL,   -- Argon2id encoded hash
21-  is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
22-  created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
23-  updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
24-  UNIQUE (org_id, id)
25-) STRICT;
26-CREATE INDEX users_org_role ON users(org_id, role, is_active);
--
28:CREATE TABLE auth_tokens (   -- not tenant-owned; reached only via token hash
29-  id         INTEGER PRIMARY KEY,
30-  user_id    INTEGER NOT NULL REFERENCES users(id),
31-  token_hash TEXT    NOT NULL UNIQUE,   -- SHA-256 hex; raw token never stored
32-  created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
33-  expires_at TEXT    NOT NULL,
34-  revoked_at TEXT
35-) STRICT;
36-CREATE INDEX auth_tokens_user ON auth_tokens(user_id) WHERE revoked_at IS NULL;
37-
38-CREATE TABLE crew_profiles (
39-  id           INTEGER PRIMARY KEY,   -- stable identifier for matcher ties
40-  org_id       INTEGER NOT NULL,
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
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "approver_problems\|decision_problems\|conflict_problems" src tests | grep -v "^src/mission_control/domain/approvals.py"; ls tests/unit/domain
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/domain/permissions.py:11:from mission_control.domain.approvals import conflict_problems
src/mission_control/domain/permissions.py:222:        problems = conflict_problems(actor.user_id, ctx.created_by_id, rostered)
src/mission_control/services/approvals.py:16:    decision_problems,
src/mission_control/services/approvals.py:167:    if problems := decision_problems(
src/mission_control/services/inbox.py:20:    decision_problems,
src/mission_control/services/inbox.py:107:        if decision_problems(me, m.created_by_id, rostered, decided):
tests/unit/domain/test_approvals.py:3:    approver_problems,
tests/unit/domain/test_approvals.py:4:    conflict_problems,
tests/unit/domain/test_approvals.py:6:    decision_problems,
tests/unit/domain/test_approvals.py:25:        approver_problems(
tests/unit/domain/test_approvals.py:33:    [p] = approver_problems(
tests/unit/domain/test_approvals.py:40:    [p] = approver_problems(
tests/unit/domain/test_approvals.py:48:    [p] = approver_problems(
tests/unit/domain/test_approvals.py:55:    [p] = approver_problems(
tests/unit/domain/test_approvals.py:64:        for p in approver_problems(
tests/unit/domain/test_approvals.py:71:def test_conflict_problems_lists_creator_then_roster():
tests/unit/domain/test_approvals.py:72:    problems = conflict_problems(RUTH, created_by_id=RUTH, rostered_user_ids={RUTH})
tests/unit/domain/test_approvals.py:79:def test_conflict_problems_is_empty_for_an_unrelated_director():
tests/unit/domain/test_approvals.py:80:    assert conflict_problems(MARCO, created_by_id=RUTH, rostered_user_ids={INGRID}) == []
tests/unit/domain/test_approvals.py:81:    assert conflict_problems(MARCO, created_by_id=None, rostered_user_ids=set()) == []
tests/unit/domain/test_approvals.py:84:def test_approver_problems_keeps_its_order_and_messages():
tests/unit/domain/test_approvals.py:85:    problems = approver_problems(
tests/unit/domain/test_approvals.py:99:    problems = decision_problems(
tests/unit/domain/test_approvals.py:105:def test_decision_problems_cover_creator_roster_and_already_decided_in_order():
tests/unit/domain/test_approvals.py:106:    problems = decision_problems(
tests/unit/domain/test_approvals.py:117:    [p] = decision_problems(
tests/unit/domain/test_approvals.py:123:def test_approver_problems_is_the_role_check_plus_decision_problems():
tests/unit/domain/test_approvals.py:126:        assert approver_problems(director(user_id), **args) == decision_problems(user_id, **args)
__pycache__
test_approvals.py
test_dates.py
test_eligibility.py
test_errors.py
test_events.py
test_lifecycle.py
test_matching.py
test_passwords.py
test_permissions.py
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat tests/unit/domain/test_approvals.py; sed -n 150,232p src/mission_control/domain/permissions.py; grep -n "APPROVE\|REJECT" src/mission_control/domain/permissions.py
```

<details>
<summary>↳ Result</summary>

```
from mission_control.domain.approvals import (
    Approver,
    approver_problems,
    conflict_problems,
    count_eligible_approvers,
    decision_problems,
    reaches_quorum,
)

RUTH, MARCO, INGRID, LEE = 1, 2, 3, 4  # PRD §9.1 Aurora


def director(user_id, active=True):
    return Approver(user_id=user_id, is_director=True, active=active)


DIRECTORS = [director(RUTH), director(MARCO), director(INGRID)]


# --- Who may approve (A2, A3) -------------------------------------------------------------


def test_eligible_director_has_no_problems():
    assert (
        approver_problems(
            director(MARCO), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
        )
        == []
    )


def test_ac8_creator_cannot_approve():
    [p] = approver_problems(
        director(RUTH), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
    )
    assert p.code == "approver_is_creator"


def test_ac11_rostered_director_cannot_approve():
    [p] = approver_problems(
        director(MARCO), created_by_id=RUTH, rostered_user_ids={MARCO}, decided_this_round=set()
    )
    assert p.code == "approver_is_rostered"


def test_ac9_a_lead_cannot_approve():
    lead = Approver(user_id=LEE, is_director=False, active=True)
    [p] = approver_problems(
        lead, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
    )
    assert p.code == "role_forbidden"


def test_ac10_a_director_cannot_decide_the_same_round_twice():
    [p] = approver_problems(
        director(MARCO), created_by_id=RUTH, rostered_user_ids=set(), decided_this_round={MARCO}
    )
    assert p.code == "already_decided"


def test_every_approver_problem_is_reported_together():
    codes = {
        p.code
        for p in approver_problems(
            director(RUTH), created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
        )
    }
    assert codes == {"approver_is_creator", "approver_is_rostered", "already_decided"}


def test_conflict_problems_lists_creator_then_roster():
    problems = conflict_problems(RUTH, created_by_id=RUTH, rostered_user_ids={RUTH})
    assert [(p.code, p.message) for p in problems] == [
        ("approver_is_creator", "You can't approve a mission you created"),
        ("approver_is_rostered", "You can't approve a mission you're on"),
    ]


def test_conflict_problems_is_empty_for_an_unrelated_director():
    assert conflict_problems(MARCO, created_by_id=RUTH, rostered_user_ids={INGRID}) == []
    assert conflict_problems(MARCO, created_by_id=None, rostered_user_ids=set()) == []


def test_approver_problems_keeps_its_order_and_messages():
    problems = approver_problems(
        director(RUTH), created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
    )
    assert [p.message for p in problems] == [
        "You can't approve a mission you created",
        "You can't approve a mission you're on",
        "You've already approved this round",
    ]


# --- Whether a Director can still decide this round (A2, A3; inbox and approve/reject) ------


def test_an_unrelated_director_who_has_not_decided_can_still_decide():
    problems = decision_problems(
        MARCO, created_by_id=RUTH, rostered_user_ids={INGRID}, decided_this_round={INGRID}
    )
    assert problems == []


def test_decision_problems_cover_creator_roster_and_already_decided_in_order():
    problems = decision_problems(
        RUTH, created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
    )
    assert [(p.code, p.message) for p in problems] == [
        ("approver_is_creator", "You can't approve a mission you created"),
        ("approver_is_rostered", "You can't approve a mission you're on"),
        ("already_decided", "You've already approved this round"),
    ]


def test_a_director_who_already_approved_this_round_cannot_decide_again():
    [p] = decision_problems(
        MARCO, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round={MARCO}
    )
    assert p.code == "already_decided"


def test_approver_problems_is_the_role_check_plus_decision_problems():
    for user_id in (RUTH, MARCO, INGRID):
        args = dict(created_by_id=RUTH, rostered_user_ids={MARCO}, decided_this_round={INGRID})
        assert approver_problems(director(user_id), **args) == decision_problems(user_id, **args)


# --- Counting eligible approvers at submit (AC-12) ----------------------------------------


def test_ac12_s7_creator_and_rostered_director_leave_one_eligible_approver():
    # S7: Ruth created Lunar Surface Medical Study and Marco is rostered, leaving Ingrid only
    assert count_eligible_approvers(DIRECTORS, created_by_id=RUTH, rostered_user_ids={MARCO}) == 1


def test_inactive_directors_are_not_eligible_approvers():
    directors = [director(RUTH), director(MARCO, active=False), director(INGRID)]
    assert count_eligible_approvers(directors, created_by_id=99, rostered_user_ids=set()) == 2


def test_non_directors_are_never_counted():
    people = DIRECTORS + [Approver(user_id=LEE, is_director=False, active=True)]
    assert count_eligible_approvers(people, created_by_id=99, rostered_user_ids=set()) == 3


# --- Quorum (A1, AC-3) --------------------------------------------------------------------


def test_ac3_quorum_reached_only_at_the_saved_n():
    assert not reaches_quorum(approvals_in_round=1, approvals_required=2)
    assert reaches_quorum(approvals_in_round=2, approvals_required=2)


def test_ac13_single_approval_is_enough_when_n_is_one():
    assert reaches_quorum(approvals_in_round=1, approvals_required=1)


def test_a1_quorum_uses_only_the_recorded_approval_count():
    # reaches_quorum sees only the number of approvals recorded this round. Whether a Director who
    # approved earlier has since left is a service-level concern, covered in M13.
    assert reaches_quorum(approvals_in_round=2, approvals_required=2)

# Completes "Only the mission's owner can ..." / "Only the owner or a Director can ...".
_MISSION_PHRASE: Mapping[Action, str] = MappingProxyType(
    {
        Action.EDIT_MISSION: "edit this mission",
        Action.PROPOSE_CREW: "propose crew for this mission",
        Action.REMOVE_CREW: "remove crew from this mission",
        Action.APPLY_MATCH: "apply suggested crew to this mission",
        Action.SUBMIT: "submit this mission",
        Action.PREVIEW_MATCH: "see suggested crew for this mission",
        Action.COMPLETE: "complete this mission",
        Action.CANCEL: "cancel this mission",
    }
)

_RESPOND_ONLY_TO_OWN = "You can only respond to your own assignments"
_SELF_ONLY_MESSAGE: Mapping[Action, str] = MappingProxyType(
    {
        Action.VIEW_CREW: "Crew can only view their own profile",
        Action.VIEW_ASSIGNMENT_HISTORY: "Crew can only view their own assignment history",
        Action.EDIT_OWN_PROFILE: "You can only edit your own profile and availability",
        Action.ACCEPT: _RESPOND_ONLY_TO_OWN,
        Action.DECLINE: _RESPOND_ONLY_TO_OWN,
        Action.WITHDRAW: _RESPOND_ONLY_TO_OWN,
    }
)


NO_CONTEXT = Context()


def authorize(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> None:
    if actor.role not in ROLES[action]:
        raise Forbidden("role_forbidden", f"{_ROLE_PLURAL[actor.role]} can't {ROLE_PHRASE[action]}")

    missing = [name for name in _REQUIRED_CONTEXT.get(action, ()) if getattr(ctx, name) is None]
    if missing:
        raise ValueError(f"{action.value} needs context field(s): {', '.join(missing)}")

    rostered = ctx.rostered_user_ids or frozenset()
    is_self = ctx.target_user_id == actor.user_id
    is_owner = ctx.owner_id == actor.user_id

    if action in _OWNER_ONLY and not is_owner:
        raise Forbidden("not_owner", f"Only the mission's owner can {_MISSION_PHRASE[action]}")

    if action in _OWNER_OR_DIRECTOR and actor.role != D and not is_owner:
        raise Forbidden("not_owner", f"Only the owner or a Director can {_MISSION_PHRASE[action]}")

    if action == Action.CREATE_MISSION and actor.role == L and not is_owner:
        raise Forbidden("not_owner", "Leads can only create missions they own")

    if action in _CREW_SELF_ONLY and actor.role == C and not is_self:
        raise Forbidden("role_forbidden", _SELF_ONLY_MESSAGE[action])

    if action == Action.VIEW_UNAVAILABILITY_REASON and actor.role != D and not is_self:
        raise Forbidden(
            "role_forbidden", "Only Directors can see other people's unavailability reasons"
        )

    if action == Action.VIEW_MISSION and actor.role == C and actor.user_id not in rostered:
        raise Forbidden("role_forbidden", "Crew can only view missions they're on")

    if action in _SELF_ONLY and not is_self:
        raise Forbidden("not_owner", _SELF_ONLY_MESSAGE[action])

    if action == Action.SET_SKILL_LEVEL and is_self:
        raise Forbidden("self_skill_edit", "You can't change your own skill levels")

    if action in (Action.APPROVE, Action.REJECT):
        # Creator and roster rules are shared with the approval module. "Already decided" is a
        # state conflict, not a permission, so it's checked by the service, not here.
        problems = conflict_problems(actor.user_id, ctx.created_by_id, rostered)
        if problems:
            raise Forbidden(problems[0].code, problems[0].message)


def can(actor: Actor, action: Action, ctx: Context = NO_CONTEXT) -> bool:
    try:
        authorize(actor, action, ctx)
    except Forbidden:
        return False
    return True
64:        Action.APPROVE: frozenset({D}),
65:        Action.REJECT: frozenset({D}),
109:        Action.APPROVE: ("created_by_id", "rostered_user_ids"),
110:        Action.REJECT: ("created_by_id", "rostered_user_ids"),
143:        Action.APPROVE: "approve missions",
144:        Action.REJECT: "reject missions",
219:    if action in (Action.APPROVE, Action.REJECT):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat > src/mission_control/domain/wording.py <<'EOF'
"""How messages put names together, so every refusal lists people and records the same way."""

from collections.abc import Iterable, Sequence


def join_names(names: Iterable[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    items = list(names)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def is_are(names: Sequence[str]) -> str:
    return "is" if len(names) == 1 else "are"
EOF
grep -rn "is_are\|join_names\|_join(" src/mission_control/services src/mission_control/domain | grep -v wording.py
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/admin.py:203:        else f"open assignments on {_join(m.name for m in missions)}"
src/mission_control/services/admin.py:222:            f"{user.name} still owns {_join(m.name for m in missions)};"
src/mission_control/services/admin.py:312:                reasons.append(f"{_join(h.name for h in holders)} {has} it")
src/mission_control/services/admin.py:315:                uses = _join(f"{s.mission_name} ({s.slot_name})" for s in slots)
src/mission_control/services/admin.py:358:def _join(names: Iterable[str]) -> str:
src/mission_control/services/missions/changes.py:34:    join_names,
src/mission_control/services/missions/changes.py:155:                    f"Can't change the dates of {mission.name}: {join_names(names)} would no "
src/mission_control/services/missions/slots.py:26:    is_are,
src/mission_control/services/missions/slots.py:27:    join_names,
src/mission_control/services/missions/slots.py:98:                f"{join_names(names)} {is_are(names)} assigned. Remove crew from the slot first."
src/mission_control/services/missions/slots.py:138:                f"{join_names(names)} would no longer be eligible. Remove them from the "
src/mission_control/services/missions/slots.py:184:                f"and {join_names(names)} {is_are(names)} assigned to it"
src/mission_control/services/missions/slots.py:188:                f"Can't remove {slot.name} from {mission.name} while {join_names(names)} "
src/mission_control/services/missions/slots.py:189:                f"{is_are(names)} assigned to it. Remove them from the mission first."
src/mission_control/services/missions/rules.py:157:def join_names(names: Sequence[str]) -> str:
src/mission_control/services/missions/rules.py:161:def is_are(names: Sequence[str]) -> str:
src/mission_control/domain/eligibility.py:148:        names = _join_names([e.crew.name for e in in_slot])
src/mission_control/domain/eligibility.py:168:def _join_names(names: list[str]) -> str:
```

</details>

### 🤖 Claude · 2026-10-12 05:25:32 UTC

Now edit eligibility.py (join + overlap helper).

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/domain/eligibility.py'
s=open(p).read()
s=s.replace('''from collections.abc import Iterable, Sequence
from dataclasses import dataclass
''','''from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
''')
s=s.replace('''from mission_control.domain.records import (
    ActiveAssignment,
    AssignmentFact,
    CandidateFacts,
    Requirement,
    RosterEntry,
    SlotSpec,
)
''','''from mission_control.domain.records import (
    ActiveAssignment,
    AssignmentFact,
    CandidateFacts,
    Commitment,
    Requirement,
    RosterEntry,
    SlotSpec,
)
from mission_control.domain.wording import join_names
''')
s=s.replace('''    for other in person.accepted_elsewhere:
        if other.window.overlaps(window):
            shared = DateRange(
                max(other.window.start, window.start), min(other.window.end, window.end)
            )
            problems.append(
                Problem(
                    "overlap",
                    f"{person.name} has an accepted assignment on {other.mission_name} "
                    f"overlapping {_span(shared)}",
                    {**ref, "mission_id": other.mission_id, "mission_name": other.mission_name},
                )
            )
    return problems
''','''    for other in person.accepted_elsewhere:
        if other.window.overlaps(window):
            problems.append(overlap_problem(person.name, other, window, ref))
    return problems


def overlap_problem(
    name: str, other: Commitment, window: DateRange, refs: Mapping[str, int | str]
) -> Problem:
    """`name` has an accepted assignment on another mission whose dates overlap `window`. The
    message names the days they share; `refs` gain the other mission."""
    shared = DateRange(max(other.window.start, window.start), min(other.window.end, window.end))
    return Problem(
        "overlap",
        f"{name} has an accepted assignment on {other.mission_name} overlapping {_span(shared)}",
        {**refs, "mission_id": other.mission_id, "mission_name": other.mission_name},
    )
''')
s=s.replace('''        names = _join_names([e.crew.name for e in in_slot])''','''        names = join_names(e.crew.name for e in in_slot)''')
s=s.replace('''def _join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


''','')
open(p,'w').write(s)
EOF
grep -n "_join_names\|overlap_problem" src/mission_control/domain/eligibility.py
```

<details>
<summary>↳ Result</summary>

```
56:            problems.append(overlap_problem(person.name, other, window, ref))
60:def overlap_problem(
```

</details>

**🔧 Edit**

```json
{
  "replace_all": false,
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/src/mission_control/domain/lifecycle.py",
  "old_string": "    return _wrong_state(status, _MISSION_VERB[action])\n\n\ndef mission_status_after(",
  "new_string": "    return _wrong_state(status, _MISSION_VERB[action])\n\n\ndef require_state(status: MissionStatus, action: Action) -> None:\n    \"\"\"Raise `StateConflict` unless mission `action` is allowed from `status`.\"\"\"\n    if problem := state_problem(status, action):\n        raise StateConflict(problem)\n\n\ndef mission_status_after("
}
```

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/src/mission_control/domain/lifecycle.py",
  "limit": 5
}
```

<details>
<summary>↳ Result</summary>

```
The file /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/src/mission_control/domain/lifecycle.py has been updated successfully.
```

</details>

<details>
<summary>↳ Result</summary>

```
1	"""Mission and assignment state machines, and the checks a mission must pass to be submitted."""
2	
3	from collections.abc import Mapping, Sequence
4	from types import MappingProxyType
5
```

</details>

<details>
<summary>📎 File attached: .worktrees/fix-cleanup/CLAUDE.md</summary>

```
{
  "path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/CLAUDE.md",
  "type": "Project",
  "content": "# Mission Control\n\nMulti-tenant mission planning API and CLI. Read these before doing any work. They are the source of truth, so don't copy their content here.\n\n- [`docs/brief.md`](docs/brief.md): the assessment brief\n- [`docs/prd.md`](docs/prd.md): **behaviour**. What the system does, its rules, acceptance criteria and seed scenarios.\n- [`docs/technical-design.md`](docs/technical-design.md): **structure**. Architecture, schema, API, CLI, the delivery plan (§9) and the implementation guidelines (§10).\n\nIf the PRD and the design conflict, or are silent on something, stop and ask. Never invent behaviour.\n\n## Workflow (every module)\n\n1. **One approved module at a time.** Work only on the module from design §9 that I have approved. Don't start anything else.\n2. **Tests first.** Write failing tests that reference the PRD IDs, then implement. Run the full suite and lint: `uv run pytest` and `uv run ruff check`.\n3. **Real verification.** Exercise the behaviour for real, for example with a REPL call, an HTTP request or a CLI command. Show the actual output. A passing test run alone isn't verification.\n4. **Read-only review.** Review the full diff against the PRD and design §10 without editing. Report findings, and fix them only once I agree.\n5. **Stop for approval.** Summarise what changed, the test and verification results, and the review findings, and propose a commit message. **Don't commit, and don't start the next module, until I approve.**\n\n## Waves (parallel modules in worktrees)\n\nWhen I approve a wave of independent modules (design §9), build them in parallel and keep reviews small:\n\n1. **One worktree per module.** Run `git worktree add .worktrees/<module> -b <module> main`, then `uv sync` inside it. Each agent edits only its own worktree and doesn't commit.\n2. **Same workflow per module.** Steps 2 to 4 above still apply, inside the worktree.\n3. **Review one branch at a time.** Show me only that module's diff against `main` (`git -C .worktrees/<module> diff main`, including new files), with its results.\n4. **After I approve that module:**\n   - commit on its branch;\n   - rebase onto `main` if `main` has moved, and re-run its tests;\n   - fast-forward `main`;\n   - run the full suite on `main`;\n   - remove the worktree and branch.\n\n   Only then present the next branch.\n\nNever push, add dependencies, change the schema, or add endpoints, error codes or CLI commands outside the design without asking first.\n",
  "contentDiffersFromDisk": false
}
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/domain/approvals.py'
s=open(p).read()
a=s.index('def approver_problems(')
b=s.index('def count_eligible_approvers(')
s=s[:a]+s[b:]
open(p,'w').write(s)
EOF
sed -n 25,50p src/mission_control/domain/approvals.py
```

<details>
<summary>↳ Result</summary>

```
    return problems


def decision_problems(
    user_id: int,
    created_by_id: int | None,
    rostered_user_ids: Set[int],
    decided_this_round: Set[int],
) -> list[Problem]:
    """Why this Director can't decide this round: they created the mission, are on it, or have
    already decided. Empty means they still can."""
    problems = conflict_problems(user_id, created_by_id, rostered_user_ids)
    if user_id in decided_this_round:
        # A rejection ends the round, so anyone who has decided an open round approved it.
        problems.append(Problem("already_decided", "You've already approved this round"))
    return problems


def count_eligible_approvers(
    people: Iterable[Approver], created_by_id: int | None, rostered_user_ids: Set[int]
) -> int:
    """Active Directors who didn't create the mission and aren't on it."""
    return sum(
        1
        for p in people
        if p.is_director
```

</details>

### 🤖 Claude · 2026-10-12 05:25:51 UTC

Now update the approvals unit tests.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='tests/unit/domain/test_approvals.py'
s=open(p).read()
a=s.index('# --- Who may approve (A2, A3)')
b=s.index('def test_conflict_problems_lists_creator_then_roster')
new='''# --- Who may approve (A2, A3) -------------------------------------------------------------


def test_eligible_director_has_no_problems():
    assert (
        decision_problems(MARCO, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set())
        == []
    )


def test_ac8_creator_cannot_approve():
    [p] = decision_problems(
        RUTH, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round=set()
    )
    assert p.code == "approver_is_creator"


def test_ac11_rostered_director_cannot_approve():
    [p] = decision_problems(
        MARCO, created_by_id=RUTH, rostered_user_ids={MARCO}, decided_this_round=set()
    )
    assert p.code == "approver_is_rostered"


@pytest.mark.parametrize("action", [Action.APPROVE, Action.REJECT])
@pytest.mark.parametrize("role", [Role.LEAD, Role.CREW])
def test_ac9_only_directors_can_approve_or_reject(action, role):
    # The role is a permission, checked before any of the decision problems.
    actor = Actor(user_id=LEE, org_id=1, role=role, crew_profile_id=None)
    about = Context(created_by_id=RUTH, rostered_user_ids=frozenset())
    with pytest.raises(Forbidden) as refused:
        authorize(actor, action, about)
    assert refused.value.code == "role_forbidden"


def test_ac10_a_director_cannot_decide_the_same_round_twice():
    [p] = decision_problems(
        MARCO, created_by_id=RUTH, rostered_user_ids=set(), decided_this_round={MARCO}
    )
    assert p.code == "already_decided"


def test_every_decision_problem_is_reported_together():
    codes = {
        p.code
        for p in decision_problems(
            RUTH, created_by_id=RUTH, rostered_user_ids={RUTH}, decided_this_round={RUTH}
        )
    }
    assert codes == {"approver_is_creator", "approver_is_rostered", "already_decided"}


'''
s=s[:a]+new+s[b:]
# remove the approver_problems order test and equivalence test
a=s.index('def test_approver_problems_keeps_its_order_and_messages')
b=s.index('# --- Whether a Director can still decide')
s=s[:a]+s[b:]
a=s.index('def test_approver_problems_is_the_role_check_plus_decision_problems')
b=s.index('# --- Counting eligible approvers')
s=s[:a]+s[b:]
s=s.replace('''from mission_control.domain.approvals import (
    Approver,
    approver_problems,
    conflict_problems,''','''import pytest

from mission_control.domain.approvals import (
    Approver,
    conflict_problems,''')
s=s.replace('''    reaches_quorum,
)
''','''    reaches_quorum,
)
from mission_control.domain.enums import Action, Role
from mission_control.domain.errors import Forbidden
from mission_control.domain.permissions import Actor, Context, authorize
''',1)
open(p,'w').write(s)
EOF
uv run ruff format tests/unit/domain/test_approvals.py >/dev/null; uv run pytest -q -o addopts='' tests/unit/domain/test_approvals.py 2>&1 | tail -2
```

<details>
<summary>↳ Result</summary>

```
....................                                                     [100%]
20 passed in 0.04s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "missions.inputs import\|missions import inputs\|inputs\.\(invalid\|refuse_input\|date_problems\|invalid_input\)" src tests | grep -v "^src/mission_control/services/missions/" ; grep -rn -A12 "missions.inputs import" src/mission_control/services/missions/*.py | grep -v "^--$" | head -60
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/crew.py:29:from mission_control.services.missions.inputs import date_problems, invalid, refuse_input
src/mission_control/services/admin.py:26:from mission_control.services.missions.inputs import invalid, refuse_input
src/mission_control/services/missions/__init__.py:29:from mission_control.services.missions.inputs import SlotInput
src/mission_control/services/missions/__init__.py-30-from mission_control.services.missions.lifecycle import cancel_mission, complete_mission
src/mission_control/services/missions/__init__.py-31-from mission_control.services.missions.queries import get_mission, list_missions
src/mission_control/services/missions/__init__.py-32-from mission_control.services.missions.slots import (
src/mission_control/services/missions/__init__.py-33-    add_slot,
src/mission_control/services/missions/__init__.py-34-    remove_slot,
src/mission_control/services/missions/__init__.py-35-    replace_requirements,
src/mission_control/services/missions/__init__.py-36-    update_slot,
src/mission_control/services/missions/__init__.py-37-)
src/mission_control/services/missions/__init__.py-38-from mission_control.services.missions.views import (
src/mission_control/services/missions/__init__.py-39-    ApprovalView,
src/mission_control/services/missions/__init__.py-40-    AssignmentView,
src/mission_control/services/missions/__init__.py-41-    MissionListItem,
src/mission_control/services/missions/changes.py:20:from mission_control.services.missions.inputs import (
src/mission_control/services/missions/changes.py-21-    SlotInput,
src/mission_control/services/missions/changes.py-22-    date_problems,
src/mission_control/services/missions/changes.py-23-    invalid,
src/mission_control/services/missions/changes.py-24-    invalid_input,
src/mission_control/services/missions/changes.py-25-    levels,
src/mission_control/services/missions/changes.py-26-    name_problems,
src/mission_control/services/missions/changes.py-27-    refuse_input,
src/mission_control/services/missions/changes.py-28-    requirement_data,
src/mission_control/services/missions/changes.py-29-    slot_label,
src/mission_control/services/missions/changes.py-30-    slot_problems,
src/mission_control/services/missions/changes.py-31-)
src/mission_control/services/missions/changes.py-32-from mission_control.services.missions.loading import open_for_edit, reload, resolve_skills
src/mission_control/services/missions/rules.py:20:from mission_control.services.missions.inputs import SlotInput
src/mission_control/services/missions/rules.py-21-
src/mission_control/services/missions/rules.py-22-# Owners and slot names
src/mission_control/services/missions/rules.py-23-
src/mission_control/services/missions/rules.py-24-
src/mission_control/services/missions/rules.py-25-def require_owner(user: User) -> None:
src/mission_control/services/missions/rules.py-26-    """Only an active Mission Lead can own a mission."""
src/mission_control/services/missions/rules.py-27-    for problem in owner_problems(user):
src/mission_control/services/missions/rules.py-28-        raise RuleViolation.of(problem)
src/mission_control/services/missions/rules.py-29-
src/mission_control/services/missions/rules.py-30-
src/mission_control/services/missions/rules.py-31-def owner_problems(user: User) -> list[Problem]:
src/mission_control/services/missions/rules.py-32-    """Why the user can't own a mission, if they can't: only an active Mission Lead can."""
src/mission_control/services/missions/slots.py:10:from mission_control.services.missions.inputs import (
src/mission_control/services/missions/slots.py-11-    SlotInput,
src/mission_control/services/missions/slots.py-12-    levels,
src/mission_control/services/missions/slots.py-13-    refuse_input,
src/mission_control/services/missions/slots.py-14-    requirement_data,
src/mission_control/services/missions/slots.py-15-    slot_label,
src/mission_control/services/missions/slots.py-16-    slot_problems,
src/mission_control/services/missions/slots.py-17-)
src/mission_control/services/missions/slots.py-18-from mission_control.services.missions.loading import (
src/mission_control/services/missions/slots.py-19-    open_for_edit,
src/mission_control/services/missions/slots.py-20-    open_slot_for_edit,
src/mission_control/services/missions/slots.py-21-    reload,
src/mission_control/services/missions/slots.py-22-    resolve_skills,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat > src/mission_control/services/inputs.py <<'EOF'
"""Checks on what callers pass in, shared by every use case. Malformed values are refused as
InvalidInput (422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from datetime import date

from mission_control.domain.errors import InvalidInput, Problem


def refuse_input(problems: Sequence[Problem]) -> None:
    if problems:
        raise invalid_input(problems)


def invalid_input(problems: Sequence[Problem]) -> InvalidInput:
    """Every mistake at once; the message is the only one's, or a summary of several."""
    message = problems[0].message if len(problems) == 1 else "Some values aren't valid"
    return InvalidInput(message, problems)


def invalid(message: str, refs: Mapping[str, int] | None = None) -> Problem:
    return Problem("validation_error", message, refs or {})


def date_problems(start: date, end: date) -> list[Problem]:
    if end >= start:
        return []
    return [invalid(f"The end date {end.isoformat()} is before the start date {start.isoformat()}")]


def required_reason(reason: str | None, doing: str) -> str:
    """The reason, without surrounding spaces. A missing or blank one is refused, e.g. "Cancelling
    Lunar Relay needs a reason" for `doing="Cancelling Lunar Relay"`."""
    given = (reason or "").strip()
    if not given:
        raise InvalidInput(f"{doing} needs a reason")
    return given
EOF
python3 - <<'EOF'
p='src/mission_control/services/missions/inputs.py'
s=open(p).read()
s=s.replace('''"""What callers pass in, and the checks on it. Malformed values are refused as InvalidInput
(422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

from mission_control.domain.errors import InvalidInput, Problem
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL, Requirement
''','''"""What callers pass in to the mission use cases, and the checks on it. Malformed values are
refused as InvalidInput (422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from mission_control.domain.errors import Problem
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL, Requirement
from mission_control.services.inputs import invalid
''')
a=s.index('def refuse_input(')
b=s.index('def name_problems(')
s=s[:a]+s[b:]
a=s.index('def date_problems(')
b=s.index('def slot_problems(')
s=s[:a]+s[b:]
open(p,'w').write(s)
EOF
sed -n 1,40p src/mission_control/services/missions/inputs.py
```

<details>
<summary>↳ Result</summary>

```
"""What callers pass in to the mission use cases, and the checks on it. Malformed values are
refused as InvalidInput (422), listing every mistake at once."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from mission_control.domain.errors import Problem
from mission_control.domain.records import MAX_LEVEL, MIN_LEVEL, Requirement
from mission_control.services.inputs import invalid


@dataclass(frozen=True)
class SlotInput:
    """A slot as given by the caller. `requirements` maps skill id to minimum level."""

    name: str
    headcount: int
    requirements: Mapping[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", MappingProxyType(dict(self.requirements)))


def name_problems(name: str) -> list[Problem]:
    return [] if name.strip() else [invalid("The mission needs a name")]


def slot_problems(
    label: str,
    name: str | None,
    headcount: int | None,
    requirements: Mapping[int, int] | None,
    refs: Mapping[str, int] | None = None,
) -> list[Problem]:
    """What's wrong with a slot's given values. None means the value isn't being set. `refs`
    names the slot, if it already exists."""
    problems = []
    if name is not None and not name.strip():
        problems.append(invalid("Every slot needs a name", refs))
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/admin.py'
s=open(p).read()
def rep(old,new,count=1):
    global s
    assert s.count(old)==count, (old, s.count(old))
    s=s.replace(old,new)
rep('''from collections.abc import Iterable
from enum import Enum
''','''from enum import Enum
''')
rep('''from mission_control.domain.passwords import validate_password
''','''from mission_control.domain.passwords import validate_password
from mission_control.domain.wording import join_names
''')
rep('''from mission_control.services.missions.inputs import invalid, refuse_input
''','''from mission_control.services.inputs import invalid, refuse_input
''')
rep('''            data={"from": current.required_approvals, "to": n},''','''            data={"changes": {"required_approvals": [current.required_approvals, n]}},''')
rep('''            message = f"The email address {email} is already in use"
            raise RuleViolation(message, [Problem("already_exists", message, {"email": email})])''','''            raise RuleViolation.of(
                Problem(
                    "already_exists",
                    f"The email address {email} is already in use",
                    {"email": email},
                )
            )''')
rep('''            message = f"{user.name} already has a crew profile"
            raise RuleViolation(
                message,
                [
                    Problem(
                        "already_exists",
                        message,
                        {"user_id": user.id, "crew_profile_id": existing.id},
                    )
                ],
            )''','''            raise RuleViolation.of(
                Problem(
                    "already_exists",
                    f"{user.name} already has a crew profile",
                    {"user_id": user.id, "crew_profile_id": existing.id},
                )
            )''')
rep('''            data={
                "user_id": user.id,
                "user_name": user.name,
                "from_role": user.role,
                "to_role": role,
            },''','''            data={
                "user_id": user.id,
                "user_name": user.name,
                "changes": {"role": [user.role, role]},
            },''')
rep('''        repos.skills.update(skill.id, to_name, to_category)
        ctx.audit(
            Event.SKILL_UPDATED,
            data={
                "skill_id": skill.id,
                "from_name": skill.name,
                "to_name": to_name,
                "from_category": skill.category,
                "to_category": to_category,
            },
        )''','''        changes: dict[str, list[str | None]] = {}
        if to_name != skill.name:
            changes["name"] = [skill.name, to_name]
        if to_category != skill.category:
            changes["category"] = [skill.category, to_category]
        repos.skills.update(skill.id, to_name, to_category)
        ctx.audit(
            Event.SKILL_UPDATED,
            data={"skill_id": skill.id, "skill_name": to_name, "changes": changes},
        )''')
rep('''def _name_taken(existing: Skill) -> RuleViolation:
    message = f"The catalogue already has a skill called {existing.name}"
    return RuleViolation(message, [Problem("already_exists", message, {"skill_id": existing.id})])''','''def _name_taken(existing: Skill) -> RuleViolation:
    return RuleViolation.of(
        Problem(
            "already_exists",
            f"The catalogue already has a skill called {existing.name}",
            {"skill_id": existing.id},
        )
    )''')
rep('''

def _join(names: Iterable[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    items = list(names)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"
''','''
''')
s=s.replace('_join(','join_names(')
open(p,'w').write(s)
EOF
grep -n "join_names\|_join" src/mission_control/services/admin.py; tail -5 src/mission_control/services/admin.py
```

<details>
<summary>↳ Result</summary>

```
15:from mission_control.domain.wording import join_names
203:        else f"open assignments on {join_names(m.name for m in missions)}"
222:            f"{user.name} still owns {join_names(m.name for m in missions)};"
311:                reasons.append(f"{join_names(h.name for h in holders)} {has} it")
314:                uses = join_names(f"{s.mission_name} ({s.slot_name})" for s in slots)


def _by_date(missions: list[Mission]) -> list[Mission]:
    return sorted(missions, key=lambda m: (m.window.start, m.id))
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/context.py'
s=open(p).read()
s=s.replace('''from mission_control.infra.repositories.models import Mission
''','''from mission_control.infra.repositories.models import CrewProfile, Mission
''')
s=s.replace('''        rostered_user_ids=repos.missions.rostered_user_ids(mission.id),
    )
''','''        rostered_user_ids=repos.missions.rostered_user_ids(mission.id),
    )


def profile_context(profile: CrewProfile) -> Context:
    """Permission context for a crew profile, or for an assignment it holds: the person is the
    profile's user, not the profile id."""
    return Context(target_user_id=profile.user_id)
''')
open(p,'w').write(s)
EOF
grep -n "profile_context" src/mission_control/services/context.py
```

<details>
<summary>↳ Result</summary>

```
85:def profile_context(profile: CrewProfile) -> Context:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/crew.py'
s=open(p).read()
def rep(old,new,count=1):
    global s
    assert s.count(old)==count, (old, s.count(old))
    s=s.replace(old,new)
rep('''from mission_control.domain.eligibility import invalidated_by_skill_change
from mission_control.domain.errors import InvalidInput, Problem
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, Context, can
''','''from mission_control.domain.eligibility import invalidated_by_skill_change, overlap_problem
from mission_control.domain.errors import InvalidInput
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, can
''')
rep('''from mission_control.services.context import ServiceContext, check, found
from mission_control.services.missions.inputs import date_problems, invalid, refuse_input
''','''from mission_control.services.context import ServiceContext, check, found, profile_context
from mission_control.services.inputs import date_problems, invalid, refuse_input
''')
rep('''        name = profile.display_name if new_name is None else new_name
        new_bio = profile.bio if bio is None else (bio.strip() or None)
        repos.crew.update(profile.id, name, new_bio)
        ctx.audit(
            Event.CREW_DETAILS_UPDATED,
            crew_profile_id=profile.id,
            data={"crew_name": name, "previous_name": profile.display_name},
        )''','''        name = profile.display_name if new_name is None else new_name
        new_bio = profile.bio if bio is None else (bio.strip() or None)
        repos.crew.update(profile.id, name, new_bio)
        changes = {} if name == profile.display_name else {"display_name": [profile.display_name, name]}
        ctx.audit(
            Event.CREW_DETAILS_UPDATED,
            crew_profile_id=profile.id,
            data={"crew_name": name, "changes": changes},
        )''')
rep('''        clashes = [
            _overlap(profile, c.mission_id, c.mission_name, c.window, window)
            for c in repos.facts.commitments(profile.id)
            if c.window.overlaps(window)
        ]''','''        clashes = [
            overlap_problem(profile.display_name, c, window, {"crew_profile_id": profile.id})
            for c in repos.facts.commitments(profile.id)
            if c.window.overlaps(window)
        ]''')
rep('''            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "level": level,
                "previous_level": previous,
            },''','''            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "changes": {"level": [previous, level]},
            },''')
rep('''            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "previous_level": previous,
            },''','''            data={
                "crew_name": profile.display_name,
                "skill_name": skill_name,
                "changes": {"level": [previous, None]},
            },''')
rep('''def _about(profile: CrewProfile) -> Context:
    """Permission context for a profile: the person is its user, not the profile id."""
    return Context(target_user_id=profile.user_id)


''','')
a=s.index('def _overlap(')
b=s.index('def _period(')
s=s[:a]+s[b:]
s=s.replace('_about(profile)','profile_context(profile)')
open(p,'w').write(s)
EOF
uv run ruff format src/mission_control/services/crew.py; grep -n "_about\|Problem\b" src/mission_control/services/crew.py; sed -n '/repos.crew.update(profile.id/,/+12p' src/mission_control/services/crew.py
```

<details>
<summary>↳ Result (error)</summary>

```
Exit code 1
1 file reformatted
sed: 1: "/repos.crew.update(prof ...": unterminated regular expression
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -n -A12 "repos.crew.update(profile.id" src/mission_control/services/crew.py
```

<details>
<summary>↳ Result</summary>

```
123:        repos.crew.update(profile.id, name, new_bio)
124-        changes = (
125-            {} if name == profile.display_name else {"display_name": [profile.display_name, name]}
126-        )
127-        ctx.audit(
128-            Event.CREW_DETAILS_UPDATED,
129-            crew_profile_id=profile.id,
130-            data={"crew_name": name, "changes": changes},
131-        )
132-        return found(repos.crew.get(profile.id), _CREW_MEMBER)
133-
134-
135-def add_unavailability(
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "cascade_mission_end" src tests docs | grep -v "def cascade_mission_end"
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/assignments.py:213:        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
src/mission_control/services/missions/lifecycle.py:11:from mission_control.services.assignments import cascade_mission_end
src/mission_control/services/missions/lifecycle.py:61:    cascade_mission_end(ctx, mission, after)
tests/integration/test_assignments_service.py:629:        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
tests/integration/test_assignments_service.py:654:        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.CANCELLED)
tests/integration/test_assignments_service.py:674:        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
tests/integration/test_assignments_service.py:684:        assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
tests/integration/test_assignments_service.py:694:            assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
tests/integration/test_assignments_service.py:706:        assignments.cascade_mission_end(ctx, mission, status)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 615,710p tests/integration/test_assignments_service.py
```

<details>
<summary>↳ Result</summary>

```
    before = snapshot(seeded_db)
    with pytest.raises((RuleViolation, Forbidden, NotFound, InvalidInput)):
        call(as_(seeded_db, actor))
    assert snapshot(seeded_db) == before


# --- Cascades when a mission completes or is cancelled (§5.4) -----------------------------


def test_m4_completing_a_mission_completes_accepted_assignments(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = last_audit_id(seeded_db)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert sorted(a.crew_profile_id for a in changed) == [CHEN_ID, DANA_ID, ELI_ID, HANA_ID]
    assert {a.status for a in changed} == {A.COMPLETED}
    events = audit_since(seeded_db, before)
    assert [(e[1], e[5], e[6]) for e in events] == [
        (Event.ASSIGNMENT_COMPLETED, "accepted", "completed")
    ] * 4
    assert events[0][8] == {
        "mission_name": "Orbital Telescope Service",
        "slot_name": "Engineer",
        "crew_name": "Chen",
    }


def test_m4_cancelling_a_mission_cancels_open_assignments_only(seeded_db):
    proposed = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)
    accepted = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, DANA_ID)
    assignments.accept(as_(seeded_db, DANA), accepted.id)
    declined = assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)
    assignments.decline(as_(seeded_db, ANA), declined.id, "Busy")

    ctx = as_(seeded_db, RUTH)
    mission = Repos(seeded_db, 1).missions.get(GATEWAY)
    before = last_audit_id(seeded_db)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.CANCELLED)
    assert [(a.id, a.status) for a in changed] == [
        (proposed.id, A.CANCELLED),
        (accepted.id, A.CANCELLED),
    ]
    assert status_of(seeded_db, declined.id) == "declined"
    assert [(e[0], e[1], e[5], e[6]) for e in audit_since(seeded_db, before)] == [
        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, "proposed", "cancelled"),
        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, "accepted", "cancelled"),
    ]


def test_m4_completing_leaves_proposals_and_closed_assignments_alone(seeded_db):
    # Not reachable through the lifecycle (Active missions have only accepted crew), but the
    # cascade must not touch anything that isn't accepted.
    repos = Repos(seeded_db, 1)
    mission = repos.missions.get(REBOOST)
    proposal = repos.assignments.create(REBOOST, REBOOST_ENGINEER, CHEN_ID, proposed_by_id=5)
    ctx = as_(seeded_db, NORA)
    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert [a.crew_profile_id for a in changed] == [GUS_ID]
    assert status_of(seeded_db, proposal.id) == "proposed"


def test_cascade_runs_only_inside_the_callers_write(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = snapshot(seeded_db)
    with pytest.raises(RuntimeError):
        assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert snapshot(seeded_db) == before


def test_cascade_rolls_back_with_the_callers_transaction(seeded_db):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    before = snapshot(seeded_db)
    with pytest.raises(RuntimeError, match="caller failed"):
        with ctx.write():
            assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
            raise RuntimeError("caller failed")
    assert snapshot(seeded_db) == before


@pytest.mark.parametrize(
    "status", [MissionStatus.DRAFT, MissionStatus.PENDING_APPROVAL, MissionStatus.ACTIVE]
)
def test_cascade_needs_a_final_status(seeded_db, status):
    ctx = as_(seeded_db, LEE)
    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)
    with ctx.write(), pytest.raises(ValueError):
        assignments.cascade_mission_end(ctx, mission, status)


# --- Scenarios end to end -----------------------------------------------------------------
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/assignments.py'
s=open(p).read()
def rep(old,new,count=1):
    global s
    assert s.count(old)==count, (old, s.count(old))
    s=s.replace(old,new)
rep('''from mission_control.domain.errors import InvalidInput, Problem
''','''from mission_control.domain.errors import Problem
''')
rep('''from mission_control.domain.permissions import Context
''','')
rep('''    mission_context,
    return_to_draft,
    visible_mission,
)
''','''    mission_context,
    profile_context,
    return_to_draft,
    visible_mission,
)
from mission_control.services.inputs import required_reason
''')
rep('''        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Withdrawing from {mission.name} needs a reason")
        slot''','''        given = required_reason(reason, f"Withdrawing from {mission.name}")
        slot''')
rep('''def cascade_mission_end(
    ctx: ServiceContext, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:''','''def cascade_mission_end(
    ctx: ServiceContext, repos: Repos, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:''')
rep('''        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
    repos = ctx.repos
''','''        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
''')
rep('''def _about(profile: CrewProfile) -> Context:
    """Permission context for someone's assignment: the person is the profile's user."""
    return Context(target_user_id=profile.user_id)


''','')
s=s.replace('_about(profile)','profile_context(profile)')
open(p,'w').write(s)

p='tests/integration/test_assignments_service.py'
s=open(p).read()
s=s.replace('''    with ctx.write():
        changed = assignments.cascade_mission_end(ctx, mission,''','''    with ctx.write() as repos:
        changed = assignments.cascade_mission_end(ctx, repos, mission,''')
s=s.replace('''        assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)
    assert snapshot(seeded_db) == before


def test_cascade_rolls_back''','''        assignments.cascade_mission_end(ctx, ctx.repos, mission, MissionStatus.COMPLETED)
    assert snapshot(seeded_db) == before


def test_cascade_rolls_back''')
s=s.replace('''        with ctx.write():
            assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)''','''        with ctx.write() as repos:
            assignments.cascade_mission_end(ctx, repos, mission, MissionStatus.COMPLETED)''')
s=s.replace('''    with ctx.write(), pytest.raises(ValueError):
        assignments.cascade_mission_end(ctx, mission, status)''','''    with ctx.write() as repos, pytest.raises(ValueError):
        assignments.cascade_mission_end(ctx, repos, mission, status)''')
open(p,'w').write(s)
EOF
grep -n "cascade_mission_end" tests/integration/test_assignments_service.py; grep -n "_about\|Context" src/mission_control/services/assignments.py
```

<details>
<summary>↳ Result</summary>

```
629:        changed = assignments.cascade_mission_end(ctx, repos, mission, MissionStatus.COMPLETED)
654:        changed = assignments.cascade_mission_end(ctx, repos, mission, MissionStatus.CANCELLED)
674:        changed = assignments.cascade_mission_end(ctx, repos, mission, MissionStatus.COMPLETED)
684:        assignments.cascade_mission_end(ctx, ctx.repos, mission, MissionStatus.COMPLETED)
694:            assignments.cascade_mission_end(ctx, repos, mission, MissionStatus.COMPLETED)
706:        assignments.cascade_mission_end(ctx, repos, mission, status)
42:    ServiceContext,
78:def propose(ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int) -> Assignment:
101:    ctx: ServiceContext,
127:def accept(ctx: ServiceContext, assignment_id: int) -> Assignment:
143:def decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:
155:def withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:
171:def remove(ctx: ServiceContext, assignment_id: int) -> Assignment:
185:def my_assignments(ctx: ServiceContext, pending: bool = False) -> list[AssignmentSummary]:
199:    ctx: ServiceContext, repos: Repos, mission: Mission, final_status: MissionStatus
231:    ctx: ServiceContext, repos: Repos, assignment_id: int
308:    ctx: ServiceContext,
327:    ctx: ServiceContext, repos: Repos, mission: Mission, action: Action
334:    ctx: ServiceContext,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/approvals.py'
s=open(p).read()
def rep(old,new,count=1):
    global s
    assert s.count(old)==count, (old, s.count(old))
    s=s.replace(old,new)
rep('''from mission_control.domain.errors import InvalidInput
''','')
rep('''from mission_control.domain.lifecycle import (
    StateConflict,
    check_submit,
    mission_status_after,
    roster_problems,
    state_problem,
)''','''from mission_control.domain.lifecycle import (
    StateConflict,
    check_submit,
    mission_status_after,
    require_state,
    roster_problems,
)''')
rep('''    visible_mission,
)
''','''    visible_mission,
)
from mission_control.services.inputs import required_reason
''')
rep('''        _check_state(mission, Action.SUBMIT)''','''        require_state(mission.status, Action.SUBMIT)''')
rep('''    _check_state(mission, action)''','''    require_state(mission.status, action)''')
rep('''        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Rejecting {mission.name} needs a reason")
''','''        given = required_reason(reason, f"Rejecting {mission.name}")
''')
rep('''def _check_state(mission: Mission, action: Action) -> None:
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)


''','')
open(p,'w').write(s)

p='src/mission_control/services/matching.py'
s=open(p).read()
rep('''from mission_control.domain.lifecycle import StateConflict, state_problem
''','''from mission_control.domain.lifecycle import require_state
''')
rep('''    ctx.authorize(action, about)
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)
    return mission, about''','''    ctx.authorize(action, about)
    require_state(mission.status, action)
    return mission, about''')
open(p,'w').write(s)

p='src/mission_control/services/missions/lifecycle.py'
s=open(p).read()
rep('''from mission_control.domain.enums import Action
from mission_control.domain.errors import InvalidInput
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
''','''from mission_control.domain.enums import Action
from mission_control.domain.events import Event
from mission_control.domain.lifecycle import mission_status_after, require_state
''')
rep('''from mission_control.services.context import ServiceContext, mission_context, visible_mission
''','''from mission_control.services.context import ServiceContext, mission_context, visible_mission
from mission_control.services.inputs import required_reason
''')
rep('''        given = (reason or "").strip()
        if not given:
            raise InvalidInput(f"Cancelling {mission.name} needs a reason")
''','''        given = required_reason(reason, f"Cancelling {mission.name}")
''')
rep('''    ctx.authorize(action, mission_context(repos, mission))
    if problem := state_problem(mission.status, action):
        raise StateConflict(problem)
    return mission''','''    ctx.authorize(action, mission_context(repos, mission))
    require_state(mission.status, action)
    return mission''')
rep('''    cascade_mission_end(ctx, mission, after)''','''    cascade_mission_end(ctx, repos, mission, after)''')
open(p,'w').write(s)
EOF
grep -n "StateConflict" src/mission_control/services/approvals.py
```

<details>
<summary>↳ Result</summary>

```
22:    StateConflict,
168:        raise StateConflict(problems[0])
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
import re
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)

edit('src/mission_control/services/missions/rules.py', [
('''        message = f"{mission.name} already has a slot called {taken.name}"
        raise RuleViolation(message, [Problem("already_exists", message, {"slot_id": taken.id})])''',
'''        raise RuleViolation.of(
            Problem(
                "already_exists",
                f"{mission.name} already has a slot called {taken.name}",
                {"slot_id": taken.id},
            )
        )'''),
('''def record_change(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    status: MissionStatus,
    event: Event,
    data: Mapping[str, object],
) -> None:
    """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
    and, if a Pending mission went back to Draft, that return with its cause."""
    ctx.audit(event, mission_id=mission.id, data=data)
    if status != mission.status:
        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))


# Wording


def join_names(names: Sequence[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def is_are(names: Sequence[str]) -> str:
    return "is" if len(names) == 1 else "are"
''',
'''def record_change(
    ctx: ServiceContext,
    repos: Repos,
    mission: Mission,
    status: MissionStatus,
    event: Event,
    mission_name: str,
    data: Mapping[str, object],
) -> None:
    """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
    and, if a Pending mission went back to Draft, that return with its cause. `mission_name` is
    the mission's name once the change is made; the audit `data` starts with it."""
    ctx.audit(event, mission_id=mission.id, data={"mission_name": mission_name, **data})
    if status != mission.status:
        return_to_draft(ctx, repos, mission, event, mission_name)
'''),
])

edit('src/mission_control/services/missions/changes.py', [
('''from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
from mission_control.domain.permissions import Context
''','''from mission_control.domain.lifecycle import mission_status_after, require_state
from mission_control.domain.permissions import Context
from mission_control.domain.wording import join_names
'''),
('''from mission_control.services.missions.inputs import (
    SlotInput,
    date_problems,
    invalid,
    invalid_input,
    levels,
    name_problems,
    refuse_input,
    requirement_data,
    slot_label,
    slot_problems,
)''','''from mission_control.services.inputs import date_problems, invalid, invalid_input, refuse_input
from mission_control.services.missions.inputs import (
    SlotInput,
    levels,
    name_problems,
    requirement_data,
    slot_label,
    slot_problems,
)'''),
('''from mission_control.services.missions.rules import (
    join_names,
    owner_problems,''','''from mission_control.services.missions.rules import (
    owner_problems,'''),
('''            Event.MISSION_UPDATED,
            {"mission_name": new_name, "changes": changes},''','''            Event.MISSION_UPDATED,
            new_name,
            {"changes": changes},'''),
('''        problem = state_problem(mission.status, Action.TRANSFER)
        if problem is not None:
            raise StateConflict(problem)
''','''        require_state(mission.status, Action.TRANSFER)
'''),
('''            Event.MISSION_TRANSFERRED,
            {
                "mission_name": mission.name,
                "from_owner_id": old_owner.id,
                "from_owner_name": old_owner.name,
                "to_owner_id": new_owner.id,
                "to_owner_name": new_owner.name,
            },''','''            Event.MISSION_TRANSFERRED,
            mission.name,
            {
                "changes": {
                    "owner_id": [old_owner.id, new_owner.id],
                    "owner_name": [old_owner.name, new_owner.name],
                }
            },'''),
])

edit('src/mission_control/services/missions/slots.py', [
('''from mission_control.domain.events import Event
''','''from mission_control.domain.events import Event
from mission_control.domain.wording import is_are, join_names
'''),
('''from mission_control.services.context import ServiceContext, check
from mission_control.services.missions.inputs import (
    SlotInput,
    levels,
    refuse_input,
    requirement_data,''','''from mission_control.services.context import ServiceContext, check
from mission_control.services.inputs import refuse_input
from mission_control.services.missions.inputs import (
    SlotInput,
    levels,
    requirement_data,'''),
('''    invalidated,
    is_are,
    join_names,
    record_change,''','''    invalidated,
    record_change,'''),
('''            Event.SLOT_ADDED,
            {
                "mission_name": mission.name,
                "slot_id": added.id,''','''            Event.SLOT_ADDED,
            mission.name,
            {
                "slot_id": added.id,'''),
('''            Event.SLOT_UPDATED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,''','''            Event.SLOT_UPDATED,
            mission.name,
            {
                "slot_id": slot.id,'''),
('''            Event.SLOT_REQUIREMENTS_CHANGED,
            {
                "mission_name": mission.name,
                "slot_id": slot.id,
                "slot_name": slot.name,
                "requirements": requirement_data(new),
                "previous_requirements": requirement_data(slot.requirements),
            },''','''            Event.SLOT_REQUIREMENTS_CHANGED,
            mission.name,
            {
                "slot_id": slot.id,
                "slot_name": slot.name,
                "changes": {
                    "requirements": [requirement_data(slot.requirements), requirement_data(new)]
                },
            },'''),
('''            Event.SLOT_REMOVED,
            {"mission_name": mission.name, "slot_id": slot.id, "slot_name": slot.name},''','''            Event.SLOT_REMOVED,
            mission.name,
            {"slot_id": slot.id, "slot_name": slot.name},'''),
])
EOF
uv run ruff check src --fix 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/services/missions/views.py', [
('''_OPEN = frozenset({AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED})
''',''),
('''    approvals = (
        repos.approvals.for_round(mission.id, mission.approval_round)
        if mission.status in _ROUND_IS_LIVE
        else []
    )

    def open_places(slot_id: int, headcount: int) -> int:
        taken = sum(1 for a in assignments if a.slot_id == slot_id and a.status in _OPEN)
        return headcount - taken
''','''    approvals = (
        repos.approvals.for_round(mission.id, mission.approval_round)
        if mission.status in _ROUND_IS_LIVE
        else []
    )
    open_places = {s.id: s.open_places for s in repos.facts.slot_specs(mission.id)}
'''),
('''                open_places(s.id, s.headcount),''','''                open_places[s.id],'''),
])
EOF
uv run ruff check src/mission_control/services/missions/views.py
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/infra/repositories/mission_slots.py', [
('''_LIVE = "removed_at IS NULL"


class MissionSlots(Scoped):''','''_LIVE = "removed_at IS NULL"


class SlotRequirements(Scoped):
    """Reading a mission's slot requirements, shared by the mission and fact repositories."""

    def _requirements_by_slot(self, mission_id: int) -> dict[int, tuple[Requirement, ...]]:
        """Every slot's requirements, removed slots included, by slot id and then skill id."""
        rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        grouped: dict[int, list[Requirement]] = {}
        for r in rows:
            grouped.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return {slot_id: tuple(reqs) for slot_id, reqs in grouped.items()}


class MissionSlots(SlotRequirements):'''),
('''    def _requirements_by_slot(self, mission_id: int) -> dict[int, tuple[Requirement, ...]]:
        rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        grouped: dict[int, list[Requirement]] = {}
        for r in rows:
            grouped.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return {slot_id: tuple(reqs) for slot_id, reqs in grouped.items()}

''',''),
])
edit('src/mission_control/infra/repositories/facts.py', [
('''    Commitment,
    Requirement,
    RosterEntry,''','''    Commitment,
    RosterEntry,'''),
('''from mission_control.infra.repositories.base import FINAL, OPEN, Scoped, in_list, window


class FactsRepo(Scoped):''','''from mission_control.infra.repositories.base import FINAL, OPEN, in_list, window
from mission_control.infra.repositories.mission_slots import SlotRequirements


class FactsRepo(SlotRequirements):'''),
('''        reqs = self._requirements(mission_id)
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
''','''        reqs = self._requirements_by_slot(mission_id)
        return [
            SlotSpec(
                r["id"],
                r["position"],
                r["name"],
                r["headcount"] - r["open_count"],
                reqs.get(r["id"], ()),
            )
            for r in rows
        ]
'''),
('''            reqs = self._requirements(r["mission_id"]).get(r["slot_id"], [])
            result.append(
                ActiveAssignment(r["mission_id"], r["mission_name"], r["slot_name"], tuple(reqs))
            )''','''            reqs = self._requirements_by_slot(r["mission_id"]).get(r["slot_id"], ())
            result.append(ActiveAssignment(r["mission_id"], r["mission_name"], r["slot_name"], reqs))'''),
])
EOF
uv run ruff check src && uv run ruff format src | tail -1; grep -rn "_requirements(" src tests | head
```

<details>
<summary>↳ Result</summary>

```
E501 Line too long (101 > 100)
   --> src/mission_control/infra/repositories/facts.py:196:101
    |
194 |         for r in rows:
195 |             reqs = self._requirements_by_slot(r["mission_id"]).get(r["slot_id"], ())
196 |             result.append(ActiveAssignment(r["mission_id"], r["mission_name"], r["slot_name"], reqs))
    |                                                                                                     ^
197 |         return result
    |

Found 1 error.
src/mission_control/infra/schema.sql:134:CREATE INDEX slot_requirements_skill ON slot_requirements(skill_id);
src/mission_control/infra/repositories/mission_slots.py:88:        self._insert_requirements(cur.lastrowid, requirements)
src/mission_control/infra/repositories/mission_slots.py:102:    def replace_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> bool:
src/mission_control/infra/repositories/mission_slots.py:110:        self._insert_requirements(slot_id, requirements)
src/mission_control/infra/repositories/mission_slots.py:120:    def _insert_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> None:
src/mission_control/infra/repositories/mission_slots.py:123:                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
src/mission_control/seed/loader.py:110:                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
src/mission_control/cli/resolve.py:40:        parsed = parse_requirements(requirements) if requirements else ()
src/mission_control/cli/resolve.py:46:def parse_requirements(text: str) -> tuple[tuple[str, int], ...]:
src/mission_control/cli/commands/missions.py:434:    requirements = parse_requirements(requires) if requires is not None else None
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run ruff format src | tail -1 && uv run ruff check src | tail -1; grep -rn "_requirements_by_slot\|\._requirements\b" tests | head
```

<details>
<summary>↳ Result</summary>

```
2 files reformatted, 93 files left unchanged
All checks passed!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat > src/mission_control/domain/events.py <<'EOF'
"""Audit event names. Every audit event is recorded under one of these names, so a mission's
history reads the same whichever code path wrote it.

An event's `data` follows one shape:
- names at the time, under name keys such as `mission_name`, `crew_name`, `slot_name`,
  `skill_name` and `user_name`, so the history still reads correctly after a rename;
- what an edit changed, as `changes: {field: [old, new]}`, listing only the fields that changed
  (a value that didn't exist before, or no longer does, is null);
- anything else the event needs, such as a new slot's requirements or a rejection's round.
"""

from enum import StrEnum


class Event(StrEnum):
    # Missions
    MISSION_CREATED = "mission.created"
    MISSION_UPDATED = "mission.updated"
    MISSION_TRANSFERRED = "mission.transferred"
    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
    MISSION_SUBMITTED = "mission.submitted"
    MISSION_APPROVED = "mission.approved"
    MISSION_REJECTED = "mission.rejected"
    MISSION_ACTIVATED = "mission.activated"
    MISSION_COMPLETED = "mission.completed"
    MISSION_CANCELLED = "mission.cancelled"
    # Slots
    SLOT_ADDED = "slot.added"
    SLOT_UPDATED = "slot.updated"
    SLOT_REQUIREMENTS_CHANGED = "slot.requirements_changed"
    SLOT_REMOVED = "slot.removed"
    # Assignments
    ASSIGNMENT_PROPOSED = "assignment.proposed"
    ASSIGNMENT_ACCEPTED = "assignment.accepted"
    ASSIGNMENT_DECLINED = "assignment.declined"
    ASSIGNMENT_WITHDRAWN = "assignment.withdrawn"
    ASSIGNMENT_REMOVED = "assignment.removed"
    ASSIGNMENT_COMPLETED = "assignment.completed"
    ASSIGNMENT_CANCELLED = "assignment.cancelled"
    # Crew
    CREW_DETAILS_UPDATED = "crew.details_updated"
    CREW_UNAVAILABILITY_ADDED = "crew.unavailability_added"
    CREW_UNAVAILABILITY_REMOVED = "crew.unavailability_removed"
    CREW_SKILL_SET = "crew.skill_set"
    CREW_SKILL_REMOVED = "crew.skill_removed"
    # Organisation and users
    ORG_REQUIRED_APPROVALS_CHANGED = "org.required_approvals_changed"
    USER_CREATED = "user.created"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    USER_PASSWORD_CHANGED = "user.password_changed"
    CREW_PROFILE_CREATED = "crew_profile.created"
    # Skill catalogue
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_DELETED = "skill.deleted"
EOF
cat tests/unit/domain/test_events.py | head -30; grep -rnE "M[0-9]+\b|AC-[0-9]|§|PRD" src | grep -v "^src/mission_control/seed/data.py:.*PRD"
```

<details>
<summary>↳ Result</summary>

```
from mission_control.domain.events import Event


def test_event_names_are_the_stored_audit_strings():
    assert {e.name: e.value for e in Event} == {
        "MISSION_CREATED": "mission.created",
        "MISSION_SUBMITTED": "mission.submitted",
        "MISSION_APPROVED": "mission.approved",
        "MISSION_ACTIVATED": "mission.activated",
        "MISSION_COMPLETED": "mission.completed",
        "USER_PASSWORD_CHANGED": "user.password_changed",
        # M10 crew
        "CREW_DETAILS_UPDATED": "crew.details_updated",
        "CREW_UNAVAILABILITY_ADDED": "crew.unavailability_added",
        "CREW_UNAVAILABILITY_REMOVED": "crew.unavailability_removed",
        "CREW_SKILL_SET": "crew.skill_set",
        "CREW_SKILL_REMOVED": "crew.skill_removed",
        # M9 admin
        "ORG_REQUIRED_APPROVALS_CHANGED": "org.required_approvals_changed",
        "USER_CREATED": "user.created",
        "USER_ROLE_CHANGED": "user.role_changed",
        "USER_DEACTIVATED": "user.deactivated",
        "CREW_PROFILE_CREATED": "crew_profile.created",
        "SKILL_CREATED": "skill.created",
        "SKILL_UPDATED": "skill.updated",
        "SKILL_DELETED": "skill.deleted",
        # M11 missions
        "MISSION_UPDATED": "mission.updated",
        "MISSION_TRANSFERRED": "mission.transferred",
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "in Event\b\|list(Event)\|Event)\b" src tests | grep -v "import" | head; grep -rnE "M[0-9]+\b|AC-[0-9]+|§|\bPRD\b" src | head -20
```

<details>
<summary>↳ Result</summary>

```
tests/unit/domain/test_events.py:5:    assert {e.name: e.value for e in Event} == {
src/mission_control/seed/data.py:3:Ids are fixed and follow the people and mission tables in the PRD, so a crew profile's id
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rnE "\b(S|V|A|P|TR|R)[0-9]+\b|design doc|technical-design|prd\.md" src | grep -v "\.sql:" | head -20; sed -n 1,8p src/mission_control/seed/data.py
```

<details>
<summary>↳ Result</summary>

```
"""Demo data for two organisations. Shared by `mc-admin seed` and the tests.

Ids are fixed and follow the people and mission tables in the PRD, so a crew profile's id
equals its user's id. The matcher's final tie-break is the crew profile id.
"""

from collections.abc import Mapping
from types import MappingProxyType as _ro
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/seed/data.py'
s=open(p).read()
s=s.replace('''Ids are fixed and follow the people and mission tables in the PRD, so a crew profile's id
equals its user's id. The matcher's final tie-break is the crew profile id.''','''Ids are fixed, and a crew profile's id equals its user's id, so the demo and the tests can name
people and missions by number. The matcher's final tie-break is the crew profile id.''')
open(p,'w').write(s)
EOF
grep -n "schema.sql" /dev/null; grep -nE "M[0-9]+\b|AC-|§|PRD" src/mission_control/infra/schema.sql | head
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat tests/unit/domain/test_events.py | sed -n 30,80p
```

<details>
<summary>↳ Result</summary>

```
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",
        "SLOT_ADDED": "slot.added",
        "SLOT_UPDATED": "slot.updated",
        "SLOT_REQUIREMENTS_CHANGED": "slot.requirements_changed",
        "SLOT_REMOVED": "slot.removed",
        # M12 assignments
        "ASSIGNMENT_PROPOSED": "assignment.proposed",
        "ASSIGNMENT_ACCEPTED": "assignment.accepted",
        "ASSIGNMENT_DECLINED": "assignment.declined",
        "ASSIGNMENT_WITHDRAWN": "assignment.withdrawn",
        "ASSIGNMENT_REMOVED": "assignment.removed",
        "ASSIGNMENT_COMPLETED": "assignment.completed",
        "ASSIGNMENT_CANCELLED": "assignment.cancelled",
        # M13 approvals and ending a mission
        "MISSION_REJECTED": "mission.rejected",
        "MISSION_CANCELLED": "mission.cancelled",
    }
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
import re
src=open('src/mission_control/domain/events.py').read()
body=src[src.index('class Event(StrEnum):'):].splitlines()[1:]
lines=[]
for l in body:
    l=l.strip()
    if not l: continue
    if l.startswith('#'):
        lines.append('        '+l)
    else:
        m=re.match(r'(\w+) = "([^"]+)"',l)
        lines.append(f'        "{m.group(1)}": "{m.group(2)}",')
test='''from mission_control.domain.events import Event


def test_event_names_are_the_stored_audit_strings():
    assert {e.name: e.value for e in Event} == {
''' + "\n".join(lines) + '''
    }
'''
open('tests/unit/domain/test_events.py','w').write(test)
EOF
cat tests/unit/domain/test_events.py | head -12; uv run pytest -q -o addopts='' tests/unit/domain/test_events.py | tail -1
```

<details>
<summary>↳ Result</summary>

```
from mission_control.domain.events import Event


def test_event_names_are_the_stored_audit_strings():
    assert {e.name: e.value for e in Event} == {
        # Missions
        "MISSION_CREATED": "mission.created",
        "MISSION_UPDATED": "mission.updated",
        "MISSION_TRANSFERRED": "mission.transferred",
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",
        "MISSION_SUBMITTED": "mission.submitted",
        "MISSION_APPROVED": "mission.approved",
1 passed in 0.03s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/cli/commands/missions.py'
s=open(p).read()
old='''    "mission.transferred": ("Handed the mission to {to_owner_name}", "Changed the owner"),'''
new='''    "mission.transferred": ("Handed the mission to {changes[owner_name][1]}", "Changed the owner"),'''
assert s.count(old)==1
s=s.replace(old,new)
old='''    except (KeyError, IndexError, ValueError):
        return plain'''
assert s.count(old)==1
s=s.replace(old,'''    except (KeyError, IndexError, TypeError, ValueError):
        return plain''')
open(p,'w').write(s)
EOF
sed -n 300,310p src/mission_control/cli/commands/missions.py; grep -rn "to_owner_name\|Handed the mission" tests | head
```

<details>
<summary>↳ Result</summary>

```
        names = f" ({join_names(approvers)})" if approvers else ""
        term.line()
        term.line(f"Approvals: {len(approvers)} of {required}{names}")


_EVENTS: dict[str, tuple[str, str]] = {
    # event: (with the names from its data, without them)
    "mission.created": ("Created the mission", "Created the mission"),
    "mission.updated": ("Edited the mission", "Edited the mission"),
    "mission.submitted": ("Submitted for approval", "Submitted for approval"),
    "mission.approved": ("Approved", "Approved"),
tests/integration/test_missions_service.py:1254:        "to_owner_name": "Nora Quinn",
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "mission.transferred\|Changed the owner\|_event_text\|history" tests/cli/*.py | head -20
```

<details>
<summary>↳ Result</summary>

```
tests/cli/test_cli_missions.py:204:def test_v1_history_shows_who_did_what_and_when(mc, api):
tests/cli/test_cli_missions.py:208:        "/missions/6/history",
tests/cli/test_cli_missions.py:224:    result = mc("missions", "history", "6")
tests/cli/test_cli_people.py:478:def test_m16_crew_history(mc, api):
tests/cli/test_cli_people.py:483:    result = mc("crew", "history", "chen@aurora.example")
tests/cli/test_cli_real_api.py:65:        ("lee", "missions history 6"),
tests/cli/test_cli_real_api.py:68:        ("lee", "crew history chen@aurora.example"),
tests/cli/test_readme_smoke.py:90:    s1_actions = {"match", "accept", "submit", "approve", "complete", "history"}
tests/cli/test_readme_smoke.py:110:        ("lee", "missions history 1"),
tests/cli/test_cli_scenarios.py:37:    history: list[dict] = field(default_factory=list)
tests/cli/test_cli_scenarios.py:56:        on("GET", "/missions/1/history", self.authed(lambda r, u: ok(self.history)))
tests/cli/test_cli_scenarios.py:91:        self.history.append(
tests/cli/test_cli_scenarios.py:92:            {"id": len(self.history) + 1,
tests/cli/test_cli_scenarios.py:93:             "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",
tests/cli/test_cli_scenarios.py:243:    history = mc("missions", "history", "1").stdout.splitlines()  # AC-1: who did what, when
tests/cli/test_cli_scenarios.py:250:        assert any(who in line and what in line and "Jan 2027" in line for line in history)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 200,240p tests/cli/test_cli_missions.py
```

<details>
<summary>↳ Result</summary>

```
        "Approvals: 1 of 2 (Marco Bianchi)\n"
    )


def test_v1_history_shows_who_did_what_and_when(mc, api):
    mc.login_as()
    api.on(
        "GET",
        "/missions/6/history",
        ok(
            [
                {"id": 1, "created_at": "2027-01-02T10:00:00.000Z", "actor_id": 5,
                 "actor_name": "Nora Quinn", "event": "mission.submitted",
                 "assignment_id": None, "crew_profile_id": None, "from_status": "draft",
                 "to_status": "pending_approval", "reason": None, "data": {}},
                {"id": 2, "created_at": "2027-01-03T11:30:00.000Z", "actor_id": 7,
                 "actor_name": "Ben Ito", "event": "assignment.withdrawn",
                 "assignment_id": 31, "crew_profile_id": 7, "from_status": "accepted",
                 "to_status": "withdrawn", "reason": "Family matter",
                 "data": {"slot_name": "Engineer", "crew_name": "Ben Ito"}},
            ]
        ),
    )  # fmt: skip

    result = mc("missions", "history", "6")

    assert result.exit_code == 0
    assert result.stdout == (
        "  When (UTC)         Who          What                     Reason\n"
        "  2 Jan 2027 10:00   Nora Quinn   Submitted for approval\n"
        "  3 Jan 2027 11:30   Ben Ito      Withdrew from Engineer   Family matter\n"
    )


# Confirmations (C4)


def test_c4_editing_a_pending_mission_asks_first_and_yes_changes_it(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
```

</details>

**🔧 Edit**

```json
{
  "replace_all": false,
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/tests/cli/test_cli_missions.py",
  "old_string": "        \"  3 Jan 2027 11:30   Ben Ito      Withdrew from Engineer   Family matter\\n\"\n    )\n",
  "new_string": "        \"  3 Jan 2027 11:30   Ben Ito      Withdrew from Engineer   Family matter\\n\"\n    )\n\n\ndef test_v1_history_names_the_new_owner_from_the_changes_in_a_transfer(mc, api):\n    mc.login_as()\n\n    def entry(id, data):\n        return {\"id\": id, \"created_at\": \"2027-01-02T10:00:00.000Z\", \"actor_id\": 1,\n                \"actor_name\": \"Ruth Adeyemi\", \"event\": \"mission.transferred\",\n                \"assignment_id\": None, \"crew_profile_id\": None, \"from_status\": None,\n                \"to_status\": None, \"reason\": None, \"data\": data}  # fmt: skip\n\n    changes = {\"owner_id\": [4, 5], \"owner_name\": [\"Lee Park\", \"Nora Quinn\"]}\n    api.on(\n        \"GET\",\n        \"/missions/1/history\",\n        ok([entry(1, {\"mission_name\": \"Gateway\", \"changes\": changes}), entry(2, {})]),\n    )\n\n    result = mc(\"missions\", \"history\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"  When (UTC)         Who            What\\n\"\n        \"  2 Jan 2027 10:00   Ruth Adeyemi   Handed the mission to Nora Quinn\\n\"\n        \"  2 Jan 2027 10:00   Ruth Adeyemi   Changed the owner\\n\"\n    )\n"
}
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run pytest -q -o addopts='' tests/cli/test_cli_missions.py -k history 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
The file /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/tests/cli/test_cli_missions.py has been updated successfully.
```

</details>

<details>
<summary>↳ Result</summary>

```
..                                                                       [100%]
2 passed, 40 deselected in 0.15s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cat > src/mission_control/cli/base.py <<'EOF'
"""What both command-line tools, `mc` and `mc-admin`, share: a bare group prints its help, and
`--version` prints the installed version."""

from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, Any

import typer
from typer.core import TyperGroup


class HelpWhenBare(TyperGroup):
    """A bare group prints its help and exits 0."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)


def version_option(program: str) -> Any:
    """The `--version` option for a tool's root callback: prints `<program> <version>`, then
    exits."""
    return Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the version and exit",
            callback=_show_version(program),
            is_eager=True,
        ),
    ]


def _show_version(program: str) -> Callable[[bool], None]:
    def show(value: bool) -> None:
        if value:
            try:
                number = version("mission-control")
            except PackageNotFoundError:
                number = "unknown"
            typer.echo(f"{program} {number}")
            raise typer.Exit()

    return show
EOF
python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/cli/main.py', [
('''import os
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Annotated

import typer

from mission_control.cli.commands import''','''import os
import sys

import typer

from mission_control.cli.base import version_option
from mission_control.cli.commands import'''),
('''

def _show_version(value: bool) -> None:
    if value:
        try:
            number = version("mission-control")
        except PackageNotFoundError:
            number = "unknown"
        typer.echo(f"mc {number}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    show_version: Annotated[
        bool,
        typer.Option(
            "--version", help="Show the version and exit", callback=_show_version, is_eager=True
        ),
    ] = False,
) -> None:''','''
Version = version_option("mc")


@app.callback()
def root(ctx: typer.Context, show_version: Version = False) -> None:'''),
])
edit('src/mission_control/cli/commands/common.py', [
('''import typer
from typer.core import TyperCommand, TyperGroup

from mission_control.cli.client import ApiError, Unreachable''','''import typer
from typer.core import TyperCommand

from mission_control.cli.base import HelpWhenBare
from mission_control.cli.client import ApiError, Unreachable'''),
('''class Group(TyperGroup):
    """A bare group prints its help and exits 0. Failures raised by commands are reported here
    with their exit code, so tests and real runs behave the same."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)

    def invoke''','''class Group(HelpWhenBare):
    """A bare group prints its help and exits 0. Failures raised by commands are reported here
    with their exit code, so tests and real runs behave the same."""

    def invoke'''),
])
edit('src/mission_control/admin_cli.py', [
('''from importlib.metadata import PackageNotFoundError, version
''',''),
('''import typer
from typer.core import TyperGroup

''','''import typer

from mission_control.cli.base import HelpWhenBare, version_option
'''),
('''class _Group(TyperGroup):
    """A bare `mc-admin` prints its help and exits 0. Failures are reported in words with their
    exit code, never as a traceback."""

    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(OK)
        return super().parse_args(ctx, args)

    def invoke''','''class _Group(HelpWhenBare):
    """A bare `mc-admin` prints its help and exits 0. Failures are reported in words with their
    exit code, never as a traceback."""

    def invoke'''),
('''def _show_version(value: bool) -> None:
    if value:
        try:
            number = version("mission-control")
        except PackageNotFoundError:
            number = "unknown"
        typer.echo(f"mc-admin {number}")
        raise typer.Exit()


@app.callback()
def root(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version", help="Show the version and exit", callback=_show_version, is_eager=True
        ),
    ] = False,
) -> None:''','''Version = version_option("mc-admin")


@app.callback()
def root(show_version: Version = False) -> None:'''),
])
EOF
uv run ruff check src --fix | tail -3; uv run ruff format src | tail -1; grep -n "^from\|^import" src/mission_control/admin_cli.py
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
96 files left unchanged
5:import getpass
6:import os
7:import re
8:import sqlite3
9:import sys
10:import unicodedata
11:from collections.abc import Generator
12:from contextlib import contextmanager
13:from pathlib import Path
14:from typing import Annotated, Any
16:import typer
18:from mission_control.cli.base import HelpWhenBare, version_option
19:from mission_control.domain.enums import Role
20:from mission_control.domain.passwords import (
25:from mission_control.infra import platform, security
26:from mission_control.infra.db import DatabaseBusy, UnsupportedSQLite, connect, init_db, write_tx
27:from mission_control.infra.repositories import Repos
28:from mission_control.infra.settings import Settings
29:from mission_control.seed import data
30:from mission_control.seed.loader import load_seed
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/cli/base.py', [
('''from typing import Annotated, Any
''','''from typing import Any
'''),
('''def version_option(program: str) -> Any:
    """The `--version` option for a tool's root callback: prints `<program> <version>`, then
    exits."""
    return Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the version and exit",
            callback=_show_version(program),
            is_eager=True,
        ),
    ]
''','''def version_flag(program: str) -> Any:
    """The `--version` option for a tool's root callback, as `Annotated[bool, version_flag(...)]`:
    prints `<program> <version>`, then exits."""
    return typer.Option(
        "--version", help="Show the version and exit", callback=_show_version(program), is_eager=True
    )
'''),
])
edit('src/mission_control/cli/main.py', [
('''import os
import sys

import typer

from mission_control.cli.base import version_option''','''import os
import sys
from typing import Annotated

import typer

from mission_control.cli.base import version_flag'''),
('''Version = version_option("mc")''','''Version = Annotated[bool, version_flag("mc")]'''),
])
edit('src/mission_control/admin_cli.py', [
('''from mission_control.cli.base import HelpWhenBare, version_option''','''from mission_control.cli.base import HelpWhenBare, version_flag'''),
('''Version = version_option("mc-admin")''','''Version = Annotated[bool, version_flag("mc-admin")]'''),
])
EOF
uv run ruff check src | tail -3; uv run ruff format src | tail -1; HOME=/tmp/fixcleanup uv run mc --version; uv run mc-admin --version; uv run mc | head -3; uv run mc-admin | head -3; uv run mc missions | head -2
```

<details>
<summary>↳ Result</summary>

```
   |

Found 1 error.
1 file reformatted, 95 files left unchanged
mc 0.1.0
mc-admin 0.1.0
Usage: mc [OPTIONS] COMMAND [ARGS]...

  Mission Control: plan missions, crew them and get them approved.
Usage: mc-admin [OPTIONS] COMMAND [ARGS]...

  Operator commands for Mission Control.
Usage: mc missions [OPTIONS] COMMAND [ARGS]...
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run ruff check src
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/cli/resolve.py'
s=open(p).read()
old=s[s.index('def skill_ids('):s.index('def requirement_body(')]
new='''def skill_ids(api: Api, names: Sequence[str]) -> dict[str, int]:
    """Skill names (any case) to IDs, from the organisation's catalogue."""
    catalogue = _catalogue(api)
    return {name: _skill_in(catalogue, name)["id"] for name in names}


def skill_named(api: Api, name: str) -> dict[str, Any]:
    """A skill from the organisation's catalogue, by name in any case."""
    return _skill_in(_catalogue(api), name)


def _catalogue(api: Api) -> dict[str, dict[str, Any]]:
    """The organisation's skills by name, ignoring case. Names are unique ignoring case."""
    return {s["name"].casefold(): s for s in api.get("/skills")}


def _skill_in(catalogue: Mapping[str, dict[str, Any]], name: str) -> dict[str, Any]:
    skill = catalogue.get(name.casefold())
    if skill is None:
        raise Refused(f"There's no skill called '{name}'", hint="See the skills: mc skills list")
    return skill


'''
s=s.replace(old,new)
open(p,'w').write(s)
EOF
uv run ruff check src/mission_control/cli && uv run ruff format --check src | tail -1
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
96 files already formatted
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 36,150p src/mission_control/services/auth.py
```

<details>
<summary>↳ Result</summary>

```
def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


def login(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    *,
    now: datetime | None = None,
    lifetime: timedelta = SESSION_LIFETIME,
) -> Session:
    """Unknown email, wrong password and deactivated user all get the same refusal, so the
    response never reveals which accounts exist."""
    now = _now(now)
    # Argon2 is slow, so it runs before the write lock is taken; the transaction then checks
    # that nothing changed since the verify.
    found = security.find_login(conn, email)
    if found is None:
        security.verify_password(security.dummy_hash(), password)  # same cost as a real check
        raise _bad_login()
    verified_hash = found["password_hash"]
    if not security.verify_password(verified_hash, password):
        raise _bad_login()
    if not found["is_active"]:
        raise _bad_login()
    upgraded_hash = (
        security.hash_password(password) if security.needs_rehash(verified_hash) else None
    )
    token = security.new_token()
    expires = now + lifetime
    with write_tx(conn):
        current = security.login_state(conn, found["id"])
        if current is None or current["password_hash"] != verified_hash:
            raise _bad_login()
        if not current["is_active"]:
            raise _bad_login()
        if upgraded_hash is not None:
            security.set_password_hash(conn, found["id"], upgraded_hash)
        security.store_token(conn, found["id"], security.hash_token(token), now, expires)
        user = Repos(conn, found["org_id"]).users.get(found["id"])
    assert user is not None
    return Session(token=token, expires_at=expires, user=user)


def authenticate(
    conn: sqlite3.Connection, token: str | None, *, now: datetime | None = None
) -> Actor:
    """Resolve a bearer token to the current Actor. Nothing is cached: role and active status
    are read on every call, so changes apply to the very next request."""
    if not token:
        raise _session_error()
    with read_tx(conn):
        row = security.find_session(conn, security.hash_token(token), _now(now))
    if row is None:
        raise _session_error()
    return Actor(
        user_id=row["id"],
        org_id=row["org_id"],
        role=Role(row["role"]),
        crew_profile_id=row["crew_profile_id"],
    )


def whoami(conn: sqlite3.Connection, actor: Actor) -> Me:
    """The caller's own account and organisation. Anyone may see their own."""
    with read_tx(conn):
        repos = Repos(conn, actor.org_id)
        user = repos.users.get(actor.user_id)
        if user is None:  # authenticate() has just found them
            raise _session_error()
        return Me(user, repos.organisation.get(), actor.crew_profile_id)


def logout(conn: sqlite3.Connection, token: str, *, now: datetime | None = None) -> None:
    with write_tx(conn):
        security.revoke_token(conn, security.hash_token(token), _now(now))


def revoke_all_sessions(
    conn: sqlite3.Connection, user_id: int, *, now: datetime | None = None
) -> None:
    """End every session of a user, in its own write transaction.

    A service making a larger change (such as deactivating a user) doesn't call this: it calls
    security.revoke_user_tokens inside its own write_tx, next to its audit write."""
    with write_tx(conn):
        security.revoke_user_tokens(conn, user_id, _now(now))


def change_password(
    conn: sqlite3.Connection,
    actor: Actor,
    current_password: str,
    new_password: str,
    *,
    now: datetime | None = None,
) -> None:
    """Needs the current password. Every session ends, including the one used to change it."""
    validate_password(new_password)
    now = _now(now)
    # Argon2 runs before the write lock is taken; the transaction then checks that the stored
    # hash is still the one the current password was verified against.
    verified_hash = security.password_hash_of(conn, actor.user_id)
    if not security.verify_password(verified_hash, current_password):
        raise _wrong_current_password()
    new_hash = security.hash_password(new_password)
    with write_tx(conn):
        if security.password_hash_of(conn, actor.user_id) != verified_hash:
            raise _wrong_current_password()
        security.set_password_hash(conn, actor.user_id, new_hash)
        security.revoke_user_tokens(conn, actor.user_id, now)
        Repos(conn, actor.org_id).audit.record(actor.user_id, Event.USER_PASSWORD_CHANGED)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/infra/security.py'
s=open(p).read()
a=s.index('def find_login(')
new='''def find_login(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    """The account with this email, in any organisation: login is by email alone."""
    return conn.execute(
        "SELECT id, org_id, password_hash, is_active FROM users WHERE email = :email",
        {"email": email},
    ).fetchone()


def login_state(conn: sqlite3.Connection, org_id: int, user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT password_hash, is_active FROM users WHERE org_id = :org AND id = :id",
        {"org": org_id, "id": user_id},
    ).fetchone()


def password_hash_of(conn: sqlite3.Connection, org_id: int, user_id: int) -> str:
    return conn.execute(
        "SELECT password_hash FROM users WHERE org_id = :org AND id = :id",
        {"org": org_id, "id": user_id},
    ).fetchone()[0]


def set_password_hash(
    conn: sqlite3.Connection, org_id: int, user_id: int, password_hash: str
) -> None:
    conn.execute(
        "UPDATE users SET password_hash = :password_hash WHERE org_id = :org AND id = :id",
        {"password_hash": password_hash, "org": org_id, "id": user_id},
    )


# Sessions. auth_tokens isn't owned by an organisation: a token is reached by its hash, or by
# the id of the user it belongs to.


def store_token(
    conn: sqlite3.Connection, user_id: int, token_hash: str, created: datetime, expires: datetime
) -> None:
    conn.execute(
        "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at)"
        " VALUES (:user_id, :token_hash, :created, :expires)",
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "created": utc_timestamp(created),
            "expires": utc_timestamp(expires),
        },
    )


def find_session(conn: sqlite3.Connection, token_hash: str, now: datetime) -> sqlite3.Row | None:
    """The user behind a live session: not revoked, not expired, and still active."""
    return conn.execute(
        """SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id
           FROM auth_tokens t
           JOIN users u ON u.id = t.user_id
           LEFT JOIN crew_profiles p ON p.org_id = u.org_id AND p.user_id = u.id
           WHERE t.token_hash = :token_hash AND t.revoked_at IS NULL AND t.expires_at > :now
             AND u.is_active = 1""",
        {"token_hash": token_hash, "now": utc_timestamp(now)},
    ).fetchone()


def revoke_token(conn: sqlite3.Connection, token_hash: str, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = :now"
        " WHERE token_hash = :token_hash AND revoked_at IS NULL",
        {"now": utc_timestamp(now), "token_hash": token_hash},
    )


def revoke_user_tokens(conn: sqlite3.Connection, user_id: int, now: datetime) -> None:
    conn.execute(
        "UPDATE auth_tokens SET revoked_at = :now WHERE user_id = :user_id AND revoked_at IS NULL",
        {"now": utc_timestamp(now), "user_id": user_id},
    )
'''
s=s[:a]+new
s=s.replace('''"""Password hashing, session tokens, and the only lookups not scoped to an organisation.

Login and token resolution happen before the caller's organisation is known, so these queries
look users up by email or token hash. Everything else goes through tenant-scoped repositories.
"""''','''"""Password hashing, session tokens, and the only lookups not scoped to an organisation.

Login and token resolution happen before the caller's organisation is known, so those queries
look users up by email or token hash, and sessions aren't owned by an organisation at all. A
user's password hash is read and written within their organisation. Everything else goes
through tenant-scoped repositories.
"""''')
open(p,'w').write(s)

def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/services/auth.py', [
('''        current = security.login_state(conn, found["id"])''','''        current = security.login_state(conn, found["org_id"], found["id"])'''),
('''            security.set_password_hash(conn, found["id"], upgraded_hash)''','''            security.set_password_hash(conn, found["org_id"], found["id"], upgraded_hash)'''),
('''    verified_hash = security.password_hash_of(conn, actor.user_id)''','''    verified_hash = security.password_hash_of(conn, actor.org_id, actor.user_id)'''),
('''        if security.password_hash_of(conn, actor.user_id) != verified_hash:''','''        if security.password_hash_of(conn, actor.org_id, actor.user_id) != verified_hash:'''),
('''        security.set_password_hash(conn, actor.user_id, new_hash)''','''        security.set_password_hash(conn, actor.org_id, actor.user_id, new_hash)'''),
])
EOF
uv run ruff format src | tail -1; uv run ruff check src | tail -1; grep -rn "security\.\(login_state\|password_hash_of\|set_password_hash\)" tests src
```

<details>
<summary>↳ Result</summary>

```
96 files left unchanged
All checks passed!
tests/integration/test_admin_service.py:226:    stored = security.password_hash_of(seeded_db, user.id)
src/mission_control/services/auth.py:68:        current = security.login_state(conn, found["org_id"], found["id"])
src/mission_control/services/auth.py:74:            security.set_password_hash(conn, found["org_id"], found["id"], upgraded_hash)
src/mission_control/services/auth.py:139:    verified_hash = security.password_hash_of(conn, actor.org_id, actor.user_id)
src/mission_control/services/auth.py:144:        if security.password_hash_of(conn, actor.org_id, actor.user_id) != verified_hash:
src/mission_control/services/auth.py:146:        security.set_password_hash(conn, actor.org_id, actor.user_id, new_hash)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "setattr(.*security\|security, \"" tests | head; sed -i '' 's/security.password_hash_of(seeded_db, user.id)/security.password_hash_of(seeded_db, 1, user.id)/' tests/integration/test_admin_service.py; sed -n 220,230p tests/integration/test_admin_service.py
```

<details>
<summary>↳ Result</summary>

```
tests/conftest.py:30:        monkeypatch.setattr(security, "_hasher", _CHEAP_HASHER)
tests/integration/test_auth.py:129:    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
tests/integration/test_auth.py:269:    monkeypatch.setattr(security, "verify_password", counting_verify)
tests/integration/test_auth.py:313:    monkeypatch.setattr(security, "verify_password", verify)
tests/integration/test_auth.py:314:    monkeypatch.setattr(security, "hash_password", hash_password)
tests/integration/test_auth.py:338:    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
tests/integration/test_auth.py:365:    monkeypatch.setattr(security, "verify_password", verify)
tests/integration/test_auth.py:384:    monkeypatch.setattr(security, "verify_password", verify)
tests/integration/test_admin_service.py:131:    monkeypatch.setattr(security, "hash_password", lambda p: hashed.append(p) or "never")
tests/integration/test_admin_service.py:242:        security, "hash_password", lambda p: seen.append(seeded_db.in_transaction) or real_hash(p)
        "Zoe Lin",
        Role.LEAD,
        True,
    )
    session = auth.login(seeded_db, "zoe@aurora.example", PASSPHRASE, now=NOW)
    assert session.user == user
    stored = security.password_hash_of(seeded_db, 1, user.id)
    assert stored.startswith("$argon2id$") and PASSPHRASE not in stored


def test_p10_an_initial_password_under_15_characters_is_refused(seeded_db):
```

</details>

### 🤖 Claude · 2026-10-12 05:30:55 UTC

Now the seed loader with named parameters and `org_id` first.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('src/mission_control/seed/loader.py', [
('''Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them.
"""''','''Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them. Each organisation's rows are written with its id bound as `:org`,
the same way the tenant-scoped repositories write theirs.
"""'''),
('''        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:''','''        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:'''),
('''    q = conn.execute
    q(
        "INSERT INTO organisations(id, name, slug, required_approvals) VALUES (?, ?, ?, ?)",
        (org.id, org.name, org.slug, org.required_approvals),
    )

    users = [u for u in data.USERS if u.org_id == org.id]
    for user in users:
        email = f"{user.name.split()[0].lower()}@{org.slug}.example"
        q(
            "INSERT INTO users(id, org_id, email, name, role, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, org.id, email, user.name, user.role, password_hash),
        )
    for user in users:
        if user.has_crew_profile:
            q(
                "INSERT INTO crew_profiles(id, org_id, user_id, display_name) VALUES (?, ?, ?, ?)",
                (user.id, org.id, user.id, user.name.split()[0]),
            )

    for skill in data.SKILLS:
        if skill.org_id == org.id:
            q(
                "INSERT INTO skills(id, org_id, name) VALUES (?, ?, ?)",
                (skill.id, org.id, skill.name),
            )
''','''    conn.execute(
        "INSERT INTO organisations(id, name, slug, required_approvals)"
        " VALUES (:org, :name, :slug, :required_approvals)",
        {
            "org": org.id,
            "name": org.name,
            "slug": org.slug,
            "required_approvals": org.required_approvals,
        },
    )

    def q(sql: str, **params: object) -> sqlite3.Cursor:
        return conn.execute(sql, {"org": org.id, **params})

    users = [u for u in data.USERS if u.org_id == org.id]
    for user in users:
        q(
            "INSERT INTO users(org_id, id, email, name, role, password_hash)"
            " VALUES (:org, :id, :email, :name, :role, :password_hash)",
            id=user.id,
            email=f"{user.name.split()[0].lower()}@{org.slug}.example",
            name=user.name,
            role=user.role,
            password_hash=password_hash,
        )
    for user in users:
        if user.has_crew_profile:
            q(
                "INSERT INTO crew_profiles(org_id, id, user_id, display_name)"
                " VALUES (:org, :id, :user_id, :display_name)",
                id=user.id,
                user_id=user.id,
                display_name=user.name.split()[0],
            )

    for skill in data.SKILLS:
        if skill.org_id == org.id:
            q(
                "INSERT INTO skills(org_id, id, name) VALUES (:org, :id, :name)",
                id=skill.id,
                name=skill.name,
            )
'''),
('''                q(
                    "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
                    " updated_by_id) VALUES (?, ?, ?, ?, ?)",
                    (org.id, crew_id, skill_id, level, director),
                )''','''                q(
                    "INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level,"
                    " updated_by_id) VALUES (:org, :crew_id, :skill_id, :level, :director)",
                    crew_id=crew_id,
                    skill_id=skill_id,
                    level=level,
                    director=director,
                )'''),
('''            q(
                "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
                " VALUES (?, ?, ?, ?, ?)",
                (org.id, absence.crew_id, absence.start, absence.end, absence.reason),
            )''','''            q(
                "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
                " VALUES (:org, :crew_id, :start, :end, :reason)",
                crew_id=absence.crew_id,
                start=absence.start,
                end=absence.end,
                reason=absence.reason,
            )'''),
('''    q = conn.execute
    audit = Repos(conn, org.id).audit
    seeded = {"mission_name": m.name, "seeded": True}
    submitted = m.status != "draft"
    q(
        "INSERT INTO missions(id, org_id, name, start_date, end_date, status, owner_id,"
        " created_by_id, approval_round, approvals_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            m.id,
            org.id,
            m.name,
            m.start,
            m.end,
            m.status,
            m.owner_id,
            m.creator_id,
            1 if submitted else 0,
            org.required_approvals if submitted else None,
        ),
    )''','''    def q(sql: str, **params: object) -> sqlite3.Cursor:
        return conn.execute(sql, {"org": org.id, **params})

    audit = Repos(conn, org.id).audit
    seeded = {"mission_name": m.name, "seeded": True}
    submitted = m.status != "draft"
    q(
        "INSERT INTO missions(org_id, id, name, start_date, end_date, status, owner_id,"
        " created_by_id, approval_round, approvals_required)"
        " VALUES (:org, :id, :name, :start, :end, :status, :owner_id, :creator_id, :round,"
        " :approvals_required)",
        id=m.id,
        name=m.name,
        start=m.start,
        end=m.end,
        status=m.status,
        owner_id=m.owner_id,
        creator_id=m.creator_id,
        round=1 if submitted else 0,
        approvals_required=org.required_approvals if submitted else None,
    )'''),
('''        slot_id = q(
            "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
            " VALUES (?, ?, ?, ?, ?)",
            (org.id, m.id, slot.name, slot.headcount, position),
        ).lastrowid
        for skill_id, min_level in slot.requirements.items():
            q(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (?, ?, ?, ?)",
                (org.id, slot_id, skill_id, min_level),
            )
        for crew_id, assignment_status in slot.crew:
            q(
                "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
                " proposed_by_id, status) VALUES (?, ?, ?, ?, ?, ?)",
                (org.id, m.id, slot_id, crew_id, m.owner_id, assignment_status),
            )''','''        slot_id = q(
            "INSERT INTO slots(org_id, mission_id, name, headcount, position)"
            " VALUES (:org, :mission_id, :name, :headcount, :position)",
            mission_id=m.id,
            name=slot.name,
            headcount=slot.headcount,
            position=position,
        ).lastrowid
        for skill_id, min_level in slot.requirements.items():
            q(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (:org, :slot_id, :skill_id, :min_level)",
                slot_id=slot_id,
                skill_id=skill_id,
                min_level=min_level,
            )
        for crew_id, assignment_status in slot.crew:
            q(
                "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id,"
                " proposed_by_id, status) VALUES (:org, :mission_id, :slot_id, :crew_id,"
                " :owner_id, :status)",
                mission_id=m.id,
                slot_id=slot_id,
                crew_id=crew_id,
                owner_id=m.owner_id,
                status=assignment_status,
            )'''),
('''        q(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
            " VALUES (?, ?, 1, ?, 'approve')",
            (org.id, m.id, director_id),
        )''','''        q(
            "INSERT INTO approvals(org_id, mission_id, round, director_id, decision)"
            " VALUES (:org, :mission_id, 1, :director_id, 'approve')",
            mission_id=m.id,
            director_id=director_id,
        )'''),
])
EOF
uv run ruff format src | tail -1; uv run ruff check src | tail -3; grep -n "?" src/mission_control/seed/loader.py src/mission_control/infra/security.py
```

<details>
<summary>↳ Result</summary>

```
96 files left unchanged
All checks passed!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/seed/loader.py'
s=open(p).read()
old='''    def q(sql: str, **params: object) -> sqlite3.Cursor:
        return conn.execute(sql, {"org": org.id, **params})
'''
assert s.count(old)==2
s=s.replace(old,'''    q = _scoped(conn, org)
''')
s=s.replace('''import sqlite3

from mission_control''','''import sqlite3
from collections.abc import Callable

from mission_control''')
s=s.replace('''def _load_org(''','''def _scoped(conn: sqlite3.Connection, org: data.Organisation) -> Callable[..., sqlite3.Cursor]:
    """Run a statement with the organisation's id bound as `:org`."""

    def run(sql: str, **params: object) -> sqlite3.Cursor:
        return conn.execute(sql, {"org": org.id, **params})

    return run


def _load_org(''')
open(p,'w').write(s)
EOF
uv run ruff format src | tail -1; uv run ruff check src | tail -1; sed -n 1,75p src/mission_control/seed/loader.py
```

<details>
<summary>↳ Result</summary>

```
96 files left unchanged
All checks passed!
"""Load the demo data into an empty database, in one transaction.

Missions are written straight into their seeded states, with the approvals and audit events
that would have produced them. Each organisation's rows are written with its id bound as `:org`,
the same way the tenant-scoped repositories write theirs.
"""

import sqlite3
from collections.abc import Callable

from mission_control.domain.events import Event
from mission_control.infra.db import write_tx
from mission_control.infra.repositories import Repos
from mission_control.seed import data


def load_seed(conn: sqlite3.Connection, password_hash: str) -> None:
    """`password_hash` is stored for every user; the caller hashes `data.DEMO_PASSWORD`."""
    with write_tx(conn):
        if conn.execute("SELECT count(*) FROM organisations").fetchone()[0]:
            raise RuntimeError("the database is not empty; reset it before seeding")
        for org in data.ORGANISATIONS:
            _load_org(conn, org, password_hash)


def _scoped(conn: sqlite3.Connection, org: data.Organisation) -> Callable[..., sqlite3.Cursor]:
    """Run a statement with the organisation's id bound as `:org`."""

    def run(sql: str, **params: object) -> sqlite3.Cursor:
        return conn.execute(sql, {"org": org.id, **params})

    return run


def _load_org(conn: sqlite3.Connection, org: data.Organisation, password_hash: str) -> None:
    conn.execute(
        "INSERT INTO organisations(id, name, slug, required_approvals)"
        " VALUES (:org, :name, :slug, :required_approvals)",
        {
            "org": org.id,
            "name": org.name,
            "slug": org.slug,
            "required_approvals": org.required_approvals,
        },
    )

    q = _scoped(conn, org)

    users = [u for u in data.USERS if u.org_id == org.id]
    for user in users:
        q(
            "INSERT INTO users(org_id, id, email, name, role, password_hash)"
            " VALUES (:org, :id, :email, :name, :role, :password_hash)",
            id=user.id,
            email=f"{user.name.split()[0].lower()}@{org.slug}.example",
            name=user.name,
            role=user.role,
            password_hash=password_hash,
        )
    for user in users:
        if user.has_crew_profile:
            q(
                "INSERT INTO crew_profiles(org_id, id, user_id, display_name)"
                " VALUES (:org, :id, :user_id, :display_name)",
                id=user.id,
                user_id=user.id,
                display_name=user.name.split()[0],
            )

    for skill in data.SKILLS:
        if skill.org_id == org.id:
            q(
                "INSERT INTO skills(org_id, id, name) VALUES (:org, :id, :name)",
                id=skill.id,
                name=skill.name,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/seed/loader.py'
s=open(p).read()
old='''    conn.execute(
        "INSERT INTO organisations(id, name, slug, required_approvals)"
        " VALUES (:org, :name, :slug, :required_approvals)",
        {
            "org": org.id,
            "name": org.name,
            "slug": org.slug,
            "required_approvals": org.required_approvals,
        },
    )

    q = _scoped(conn, org)
'''
new='''    q = _scoped(conn, org)
    q(
        "INSERT INTO organisations(id, name, slug, required_approvals)"
        " VALUES (:org, :name, :slug, :required_approvals)",
        name=org.name,
        slug=org.slug,
        required_approvals=org.required_approvals,
    )
'''
assert s.count(old)==1
s=s.replace(old,new)
open(p,'w').write(s)
EOF
uv run ruff format src | tail -1
```

<details>
<summary>↳ Result</summary>

```
96 files left unchanged
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='tests/integration/test_repository_sql.py'
s=open(p).read()
def rep(old,new):
    global s
    assert s.count(old)==1, old
    s=s.replace(old,new)
rep('''"""Guard test (design §4): every SQL statement in infra/repositories filters on the caller's org,
bound by name as `org_id = :org`, and no statement uses positional `?` placeholders.

infra/platform.py is scanned by the same rules. Its only exemption is the organisation statements
listed in PLATFORM_EXEMPT, which run before any tenant exists to scope by (mc-admin create-org);
they must still bind by name. admin_cli.py holds no SQL at all."""''','''"""Guard test (design §4): every SQL statement in infra/repositories filters on the caller's org,
bound by name as `org_id = :org`, and no statement uses positional `?` placeholders.

infra/platform.py, infra/security.py and seed/loader.py are scanned by the same rules. Each may
skip the org filter only for the statements listed for it in EXEMPT, which are cross-organisation
by nature; they must still bind by name:
- platform: the organisation statements that run before any tenant exists (mc-admin create-org);
- security: login by email alone, and the session statements on auth_tokens, which isn't owned
  by an organisation (reached by token hash, or by the user it belongs to);
- seed: checking the database is empty, and creating each organisation with its fixed id.
admin_cli.py holds no SQL at all."""''')
rep('''PLATFORM = PACKAGE / "infra/platform.py"
''','''PLATFORM = PACKAGE / "infra/platform.py"
SECURITY = PACKAGE / "infra/security.py"
SEED = PACKAGE / "seed/loader.py"
''')
rep('''# The platform statements that may skip the org filter, written out in full: finding an
# organisation by slug across every tenant, and creating one. Nothing else is exempt.
PLATFORM_EXEMPT = frozenset(
    {
        "SELECT name FROM organisations WHERE slug = :slug",
        "INSERT INTO organisations(name, slug) VALUES (:name, :slug)",
    }
)
''','''# The platform statements that may skip the org filter, written out in full: finding an
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
''')
rep('''def exemptions_for(name: str) -> frozenset[str]:
    return PLATFORM_EXEMPT if name == PLATFORM.name else frozenset()
''','''def exemptions_for(name: str) -> frozenset[str]:
    return EXEMPT.get(name, frozenset())
''')
rep('''    """Every SQL literal in the repositories and the platform module. An f-string is read as
    one statement: its literal parts are joined and each interpolation is shown as {...}."""
    for path in paths or [*sorted(REPOS.glob("*.py")), PLATFORM]:''','''    """Every SQL literal in the repositories and the other modules scanned. An f-string is read
    as one statement: its literal parts are joined and each interpolation is shown as {...}.
    Adjacent string literals are one constant, so a statement split over lines is read whole."""
    for path in paths or [*sorted(REPOS.glob("*.py")), *SCANNED_MODULES]:''')
rep('''def test_the_platform_module_is_scanned_and_every_exemption_is_in_use():
    platform_sql = {_normal(sql) for name, _, sql in sql_strings() if name == PLATFORM.name}
    assert PLATFORM_EXEMPT <= platform_sql, "an exemption no longer matches platform.py"
''','''def test_the_scanned_module_names_dont_clash_with_a_repository():
    names = [p.name for p in REPOS.glob("*.py")] + [p.name for p in SCANNED_MODULES]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("module", SCANNED_MODULES, ids=lambda p: p.name)
def test_each_scanned_module_has_sql_and_every_exemption_is_in_use(module):
    module_sql = {_normal(sql) for name, _, sql in sql_strings() if name == module.name}
    assert module_sql, f"no SQL found in {module.name}: has it moved?"
    unused = EXEMPT[module.name] - module_sql
    assert not unused, f"an exemption no longer matches {module.name}: {unused}"
''')
rep('''def test_the_platform_exemption_covers_only_its_listed_statements(sql, reason):
    assert reason in problems(sql, PLATFORM_EXEMPT)
''','''def test_the_platform_exemption_covers_only_its_listed_statements(sql, reason):
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
def test_the_security_and_seed_exemptions_cover_only_their_listed_statements(
    sql, reason, exempt
):
    assert reason in problems(sql, exempt)
''')
open(p,'w').write(s)
EOF
uv run ruff format tests/integration/test_repository_sql.py | tail -1; uv run pytest -q -o addopts='' tests/integration/test_repository_sql.py 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
1 file reformatted
................................                                         [100%]
32 passed in 0.13s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && cd tests/integration && uv run python -c "
import test_repository_sql as t
for n,l,s in t.sql_strings([t.SEED,t.SECURITY]): print(n,l,t.problems(s, t.exemptions_for(n)), ' '.join(s.split())[:90])
"
```

<details>
<summary>↳ Result</summary>

```
loader.py 38 [] INSERT INTO organisations(id, name, slug, required_approvals) VALUES (:org, :name, :slug, 
loader.py 111 [] INSERT INTO missions(org_id, id, name, start_date, end_date, status, owner_id, created_by_
loader.py 48 [] INSERT INTO users(org_id, id, email, name, role, password_hash) VALUES (:org, :id, :email,
loader.py 171 [] INSERT INTO approvals(org_id, mission_id, round, director_id, decision) VALUES (:org, :mis
loader.py 59 [] INSERT INTO crew_profiles(org_id, id, user_id, display_name) VALUES (:org, :id, :user_id, 
loader.py 69 [] INSERT INTO skills(org_id, id, name) VALUES (:org, :id, :name)
loader.py 91 [] INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason) VALUES (
loader.py 131 [] INSERT INTO slots(org_id, mission_id, name, headcount, position) VALUES (:org, :mission_id
loader.py 140 [] INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level) VALUES (:org, :slot_id
loader.py 148 [] INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id, proposed_by_id, stat
loader.py 80 [] INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level, updated_by_id) VALUES (:
loader.py 20 [] SELECT count(*) FROM organisations
security.py 85 [] UPDATE users SET password_hash = :password_hash WHERE org_id = :org AND id = :id
security.py 98 [] INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at) VALUES (:user_id, :to
security.py 124 [] UPDATE auth_tokens SET revoked_at = :now WHERE token_hash = :token_hash AND revoked_at IS 
security.py 132 [] UPDATE auth_tokens SET revoked_at = :now WHERE user_id = :user_id AND revoked_at IS NULL
security.py 62 [] SELECT id, org_id, password_hash, is_active FROM users WHERE email = :email
security.py 69 [] SELECT password_hash, is_active FROM users WHERE org_id = :org AND id = :id
security.py 112 [] SELECT u.id, u.org_id, u.role, p.id AS crew_profile_id FROM auth_tokens t JOIN users u ON 
security.py 76 [] SELECT password_hash FROM users WHERE org_id = :org AND id = :id
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run pytest -W error -q -o addopts='' -x -q 2>&1 | tail -5; uv run pytest -W error -q -o addopts='' 2>&1 | grep -E "^FAILED|passed|failed"
```

<details>
<summary>↳ Result</summary>

```
tests/integration/test_admin_service.py:81: AssertionError
=========================== short test summary info ============================
FAILED tests/integration/test_admin_service.py::test_a1_director_sets_the_required_approvals_and_it_is_audited
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
FAILED tests/integration/test_admin_service.py::test_a1_director_sets_the_required_approvals_and_it_is_audited
FAILED tests/integration/test_admin_service.py::test_p9_changing_someone_to_crew_gives_them_a_profile_if_missing
FAILED tests/integration/test_admin_service.py::test_p9_a_role_change_is_audited_with_names
FAILED tests/integration/test_admin_service.py::test_p1_renaming_a_skill_keeps_its_identity
FAILED tests/integration/test_crew_service.py::test_ac23_ben_edits_his_personal_details
FAILED tests/integration/test_crew_service.py::test_ac23_lee_can_change_anas_skill_levels
FAILED tests/integration/test_crew_service.py::test_p3_director_adds_a_new_skill_level
FAILED tests/integration/test_crew_service.py::test_p3_lead_removes_a_skill_level
FAILED tests/integration/test_missions_service.py::test_m2_m3_the_owner_replaces_a_slots_requirements
FAILED tests/integration/test_missions_service.py::test_ac7_after_transfer_the_new_owner_can_edit_and_the_old_cannot
10 failed, 1697 passed in 24.00s
```

</details>

### 🤖 Claude · 2026-10-12 05:32:56 UTC

Exactly the audit-data assertions. Let me update them.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 72,86p tests/integration/test_admin_service.py; sed -n 370,385p tests/integration/test_admin_service.py; sed -n 490,505p tests/integration/test_admin_service.py; sed -n 710,735p tests/integration/test_admin_service.py
```

<details>
<summary>↳ Result</summary>

```
    org = admin.view_organisation(ctx(seeded_db))
    assert (org.id, org.name, org.required_approvals) == (1, "Aurora Space Agency", 2)


def test_a1_director_sets_the_required_approvals_and_it_is_audited(seeded_db):
    start = last_audit_id(seeded_db)
    org = admin.set_required_approvals(ctx(seeded_db), 3)
    assert org.required_approvals == 3
    assert admin.view_organisation(ctx(seeded_db)).required_approvals == 3
    assert audit_events(seeded_db, start) == [
        (1, "org.required_approvals_changed", None, {"from": 2, "to": 3}),
    ]


def test_a1_changing_the_setting_doesnt_affect_a_round_already_in_progress(seeded_db):
    profile = ctx(seeded_db).repos.crew.by_user(INGRID)
    assert profile.display_name == "Ingrid"
    assert audit_events(seeded_db, start) == [
        (
            1,
            "user.role_changed",
            None,
            {
                "user_id": INGRID,
                "user_name": "Ingrid Holm",
                "from_role": "director",
                "to_role": "crew",
            },
        ),
        (
            1,


def test_p9_a_role_change_is_audited_with_names(seeded_db):
    start = last_audit_id(seeded_db)
    admin.change_role(ctx(seeded_db), FAY, Role.LEAD)
    assert audit_events(seeded_db, start) == [
        (
            1,
            "user.role_changed",
            None,
            {"user_id": FAY, "user_name": "Fay Moreau", "from_role": "crew", "to_role": "lead"},
        ),
    ]


# --- Deactivation (P7, P8, AC-26) ---------------------------------------------------------
def test_p1_renaming_a_skill_keeps_its_identity(seeded_db):
    start = last_audit_id(seeded_db)
    skill = admin.update_skill(ctx(seeded_db), SYS_ENG, name="Systems Eng")
    assert (skill.id, skill.name) == (SYS_ENG, "Systems Eng")
    repos = ctx(seeded_db).repos
    assert repos.crew.skills(BEN_ID)[SYS_ENG] == 4
    flight_engineer = repos.missions.slots(GATEWAY)[0]
    assert [(r.skill_id, r.skill_name) for r in flight_engineer.requirements] == [
        (SYS_ENG, "Systems Eng")
    ]
    assert audit_events(seeded_db, start) == [
        (
            1,
            "skill.updated",
            None,
            {
                "skill_id": SYS_ENG,
                "from_name": "Systems Engineering",
                "to_name": "Systems Eng",
                "from_category": None,
                "to_category": None,
            },
        ),
    ]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('tests/integration/test_admin_service.py', [
('''        (1, "org.required_approvals_changed", None, {"from": 2, "to": 3}),''','''        (1, "org.required_approvals_changed", None, {"changes": {"required_approvals": [2, 3]}}),'''),
('''            {
                "user_id": INGRID,
                "user_name": "Ingrid Holm",
                "from_role": "director",
                "to_role": "crew",
            },''','''            {
                "user_id": INGRID,
                "user_name": "Ingrid Holm",
                "changes": {"role": ["director", "crew"]},
            },'''),
('''            {"user_id": FAY, "user_name": "Fay Moreau", "from_role": "crew", "to_role": "lead"},''','''            {
                "user_id": FAY,
                "user_name": "Fay Moreau",
                "changes": {"role": ["crew", "lead"]},
            },'''),
('''            {
                "skill_id": SYS_ENG,
                "from_name": "Systems Engineering",
                "to_name": "Systems Eng",
                "from_category": None,
                "to_category": None,
            },
        ),
    ]''','''            {
                "skill_id": SYS_ENG,
                "skill_name": "Systems Eng",
                "changes": {"name": ["Systems Engineering", "Systems Eng"]},
            },
        ),
    ]'''),
])
EOF
grep -n "category" tests/integration/test_admin_service.py | head -20
```

<details>
<summary>↳ Result</summary>

```
681:    skill = admin.add_skill(ctx(seeded_db), "  Robotics ", category="Engineering")
682:    assert (skill.org_id, skill.name, skill.category) == (1, "Robotics", "Engineering")
689:            {"skill_id": skill.id, "skill_name": "Robotics", "category": "Engineering"},
738:    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category="Science")
739:    assert (skill.name, skill.category) == ("Geology", "Science")
741:    assert (skill.name, skill.category) == ("Planetary Geology", "Science")
742:    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category=None)
743:    assert (skill.name, skill.category) == ("Planetary Geology", None)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 734,750p tests/integration/test_admin_service.py; grep -n "def audit_events" -A12 tests/integration/test_admin_service.py
```

<details>
<summary>↳ Result</summary>

```
    ]


def test_p1_recategorising_a_skill_keeps_its_name_unless_one_is_given(seeded_db):
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category="Science")
    assert (skill.name, skill.category) == ("Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, name="Planetary Geology")
    assert (skill.name, skill.category) == ("Planetary Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category=None)
    assert (skill.name, skill.category) == ("Planetary Geology", None)


def test_p1_renaming_to_another_skills_name_is_refused(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(RuleViolation) as err:
        admin.update_skill(ctx(seeded_db), GEOLOGY, name="eva")
    assert refused(err)[2] == ["already_exists"]
50:def audit_events(conn, since_id=0):
51-    rows = conn.execute(
52-        "SELECT actor_id, event, crew_profile_id, data FROM audit_events WHERE id > ? ORDER BY id",
53-        (since_id,),
54-    ).fetchall()
55-    return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]
56-
57-
58-def last_audit_id(conn):
59-    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]
60-
61-
62-def refused(exc_info):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('tests/integration/test_admin_service.py', [
('''def test_p1_recategorising_a_skill_keeps_its_name_unless_one_is_given(seeded_db):
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category="Science")
    assert (skill.name, skill.category) == ("Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, name="Planetary Geology")
    assert (skill.name, skill.category) == ("Planetary Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category=None)
    assert (skill.name, skill.category) == ("Planetary Geology", None)
''','''def test_p1_recategorising_a_skill_keeps_its_name_unless_one_is_given(seeded_db):
    start = last_audit_id(seeded_db)
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category="Science")
    assert (skill.name, skill.category) == ("Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, name="Planetary Geology")
    assert (skill.name, skill.category) == ("Planetary Geology", "Science")
    skill = admin.update_skill(ctx(seeded_db), GEOLOGY, category=None)
    assert (skill.name, skill.category) == ("Planetary Geology", None)
    # Each audit event lists only what changed, as [old, new].
    assert [data for _, _, _, data in audit_events(seeded_db, start)] == [
        {"skill_id": GEOLOGY, "skill_name": "Geology", "changes": {"category": [None, "Science"]}},
        {
            "skill_id": GEOLOGY,
            "skill_name": "Planetary Geology",
            "changes": {"name": ["Geology", "Planetary Geology"]},
        },
        {
            "skill_id": GEOLOGY,
            "skill_name": "Planetary Geology",
            "changes": {"category": ["Science", None]},
        },
    ]
'''),
])
EOF
sed -n 190,206p tests/integration/test_crew_service.py; sed -n 455,510p tests/integration/test_crew_service.py
```

<details>
<summary>↳ Result</summary>

```
        crew.assignment_history(as_(seeded_db, RUTH), 17)  # Lena, Helix


# --- Personal details (P4, AC-16, AC-23) --------------------------------------------------


def test_ac23_ben_edits_his_personal_details(seeded_db):
    updated = crew.update_details(as_(seeded_db, BEN), 7, display_name="Benji", bio="EVA nerd")
    assert (updated.display_name, updated.bio) == ("Benji", "EVA nerd")
    assert crew.view_crew(as_(seeded_db, LEE), 7).name == "Benji"
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (7, "crew.details_updated", 7)
    assert data == {"crew_name": "Benji", "previous_name": "Ben"}


def test_p4_display_name_is_kept_when_only_the_bio_changes_and_bio_can_be_cleared(seeded_db):
    ctx = as_(seeded_db, ANA)  # a Lead with a crew profile

def test_ac23_lee_can_change_anas_skill_levels(seeded_db):
    level = crew.set_skill_level(as_(seeded_db, LEE), 6, PILOTING, 3)
    assert (level.skill_id, level.skill_name, level.level) == (PILOTING, "Piloting", 3)
    stored = seeded_db.execute(
        "SELECT level, updated_by_id FROM crew_skills WHERE crew_profile_id = 6 AND skill_id = 1"
    ).fetchone()
    assert tuple(stored) == (3, 4)
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (4, "crew.skill_set", 6)
    assert data == {"crew_name": "Ana", "skill_name": "Piloting", "level": 3, "previous_level": 5}


def test_ac23_ben_cant_edit_skills(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.set_skill_level(as_(seeded_db, BEN), 7, EVA, 5)
    assert (err.value.code, err.value.message) == (
        "role_forbidden",
        "Crew can't change skill levels",
    )
    with pytest.raises(NotFound):  # Fay's profile isn't visible to him
        crew.set_skill_level(as_(seeded_db, BEN), 11, EVA, 5)
    assert unchanged(seeded_db, before)


def test_ac23_crew_setting_an_out_of_range_level_is_forbidden_not_invalid(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
        crew.set_skill_level(as_(seeded_db, BEN), 7, EVA, 9)
    assert err.value.code == "role_forbidden"
    assert unchanged(seeded_db, before)


def test_ac29_another_orgs_skill_level_is_not_found_before_the_level_is_checked(seeded_db):
    with pytest.raises(NotFound):
        crew.set_skill_level(as_(seeded_db, SAM), 7, EVA, 9)


def test_p3_director_adds_a_new_skill_level(seeded_db):
    crew.set_skill_level(as_(seeded_db, RUTH), 11, EVA, 2)
    assert crew.view_crew(as_(seeded_db, RUTH), 11).skills[0].skill_name == "EVA"
    assert last_audit(seeded_db)[4]["previous_level"] is None


def test_p3_lead_removes_a_skill_level(seeded_db):
    crew.remove_skill_level(as_(seeded_db, LEE), 7, EVA)
    assert [s.skill_id for s in crew.view_crew(as_(seeded_db, LEE), 7).skills] == [SYS_ENG]
    actor, event, profile, _, data = last_audit(seeded_db)
    assert (actor, event, profile) == (4, "crew.skill_removed", 7)
    assert data == {"crew_name": "Ben", "skill_name": "EVA", "previous_level": 3}


@pytest.mark.parametrize("level", [0, 6])
def test_p2_proficiency_is_from_1_to_5(seeded_db, level):
    with pytest.raises(crew.InvalidInput, match="between 1 and 5"):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 205,222p tests/integration/test_crew_service.py
```

<details>
<summary>↳ Result</summary>

```
def test_p4_display_name_is_kept_when_only_the_bio_changes_and_bio_can_be_cleared(seeded_db):
    ctx = as_(seeded_db, ANA)  # a Lead with a crew profile
    assert crew.update_details(ctx, 6, bio="Test pilot").display_name == "Ana"
    cleared = crew.update_details(ctx, 6, bio="")
    assert (cleared.display_name, cleared.bio) == ("Ana", None)


def test_p4_display_name_cant_be_blank(seeded_db):
    before = snapshot(seeded_db)
    with pytest.raises(crew.InvalidInput, match="Display name"):
        crew.update_details(as_(seeded_db, BEN), 7, display_name="   ")
    assert unchanged(seeded_db, before)


@pytest.mark.parametrize("actor", [LEE, RUTH], ids=["lead", "director"])
def test_p4_nobody_else_edits_personal_details(seeded_db, actor):
    before = snapshot(seeded_db)
    with pytest.raises(Forbidden) as err:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('tests/integration/test_crew_service.py', [
('''    assert data == {"crew_name": "Benji", "previous_name": "Ben"}''','''    assert data == {"crew_name": "Benji", "changes": {"display_name": ["Ben", "Benji"]}}'''),
('''    assert crew.update_details(ctx, 6, bio="Test pilot").display_name == "Ana"
    cleared = crew.update_details(ctx, 6, bio="")
    assert (cleared.display_name, cleared.bio) == ("Ana", None)
''','''    assert crew.update_details(ctx, 6, bio="Test pilot").display_name == "Ana"
    assert last_audit(seeded_db)[4] == {"crew_name": "Ana", "changes": {}}  # the bio isn't audited
    cleared = crew.update_details(ctx, 6, bio="")
    assert (cleared.display_name, cleared.bio) == ("Ana", None)
'''),
('''    assert data == {"crew_name": "Ana", "skill_name": "Piloting", "level": 3, "previous_level": 5}''','''    assert data == {"crew_name": "Ana", "skill_name": "Piloting", "changes": {"level": [5, 3]}}'''),
('''    assert last_audit(seeded_db)[4]["previous_level"] is None''','''    assert last_audit(seeded_db)[4]["changes"] == {"level": [None, 2]}'''),
('''    assert data == {"crew_name": "Ben", "skill_name": "EVA", "previous_level": 3}''','''    assert data == {"crew_name": "Ben", "skill_name": "EVA", "changes": {"level": [3, None]}}'''),
])
EOF
sed -n 950,970p tests/integration/test_missions_service.py; sed -n 1225,1262p tests/integration/test_missions_service.py
```

<details>
<summary>↳ Result</summary>

```
    )
    commander = next(s for s in view.slots if s.id == COMMANDER)
    assert [(r.skill_name, r.min_level) for r in commander.requirements] == [
        ("Piloting", 5),
        ("Leadership", 4),
    ]
    [(_, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert event == "slot.requirements_changed"
    assert data["slot_name"] == "Commander"
    assert data["requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 5},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 4},
    ]
    assert data["previous_requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 4},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 3},
    ]


def test_m7_a_requirement_change_that_breaks_an_assignee_is_refused(seeded_db):
    before = snapshot(seeded_db)
    [
        lambda c: missions.update_slot(c, TELESCOPE, TELESCOPE_ENGINEER, headcount=2),
        lambda c: missions.replace_requirements(c, TELESCOPE, TELESCOPE_ENGINEER, {SYS_ENG: 2}),
        lambda c: missions.remove_slot(c, TELESCOPE, TELESCOPE_ENGINEER),
    ],
)
def test_ac5_an_active_missions_slots_are_frozen(seeded_db, change):
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        change(svc(seeded_db, LEE))
    assert err.value.code == "mission_frozen"
    assert snapshot(seeded_db) == before


# --- Transfer ownership (M1, AC-7) --------------------------------------------------------


def test_ac7_after_transfer_the_new_owner_can_edit_and_the_old_cannot(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, RUTH), GATEWAY, NORA.user_id)
    assert (view.mission.owner_id, view.owner_name) == (NORA.user_id, "Nora Quinn")
    assert view.mission.created_by_id == RUTH.user_id  # the creator is unchanged
    assert view.mission.status == MissionStatus.DRAFT
    [(actor, event, _, _, data)] = last_events(seeded_db, GATEWAY, 1)
    assert (actor, event) == (RUTH.user_id, "mission.transferred")
    assert data == {
        "mission_name": "Lunar Gateway Resupply",
        "from_owner_id": LEE.user_id,
        "from_owner_name": "Lee Park",
        "to_owner_id": NORA.user_id,
        "to_owner_name": "Nora Quinn",
    }

    missions.update_mission(svc(seeded_db, NORA), GATEWAY, name="Gateway (Nora)")
    with pytest.raises(Forbidden) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, name="Gateway (Lee)")
    assert err.value.code == "not_owner"
    with pytest.raises(Forbidden):
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer())
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
def edit(p, pairs):
    s=open(p).read()
    for old,new in pairs:
        assert s.count(old)==1, (p, old, s.count(old))
        s=s.replace(old,new)
    open(p,'w').write(s)
edit('tests/integration/test_missions_service.py', [
('''    assert data["requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 5},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 4},
    ]
    assert data["previous_requirements"] == [
        {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 4},
        {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 3},
    ]''','''    assert data["changes"] == {
        "requirements": [
            [
                {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 4},
                {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 3},
            ],
            [
                {"skill_id": PILOTING, "skill_name": "Piloting", "min_level": 5},
                {"skill_id": LEADERSHIP, "skill_name": "Leadership", "min_level": 4},
            ],
        ]
    }'''),
('''    assert data == {
        "mission_name": "Lunar Gateway Resupply",
        "from_owner_id": LEE.user_id,
        "from_owner_name": "Lee Park",
        "to_owner_id": NORA.user_id,
        "to_owner_name": "Nora Quinn",
    }''','''    assert data == {
        "mission_name": "Lunar Gateway Resupply",
        "changes": {
            "owner_id": [LEE.user_id, NORA.user_id],
            "owner_name": ["Lee Park", "Nora Quinn"],
        },
    }'''),
])
EOF
uv run pytest -W error -q -o addopts='' 2>&1 | grep -E "^FAILED|passed|failed"
```

<details>
<summary>↳ Result</summary>

```
1707 passed in 26.18s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 1,75p tests/integration/test_missions_service.py; sed -n 1262,1300p tests/integration/test_missions_service.py
```

<details>
<summary>↳ Result</summary>

```
"""M11: the missions service. Viewing, creating and editing missions and their slots, and
transferring ownership (PRD M1–M3, M5, M7, §5.7, AC-4, AC-5, AC-7, AC-24, AC-27, AC-29)."""

import json
from datetime import UTC, date, datetime

import pytest

from builders import make_assignment
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import missions
from mission_control.services.context import ServiceContext
from mission_control.services.missions import SlotInput

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(1, 1, Role.DIRECTOR, None)
MARCO = Actor(2, 1, Role.DIRECTOR, 2)
INGRID = Actor(3, 1, Role.DIRECTOR, None)
LEE = Actor(4, 1, Role.LEAD, None)
NORA = Actor(5, 1, Role.LEAD, None)
ANA = Actor(6, 1, Role.LEAD, 6)
BEN = Actor(7, 1, Role.CREW, 7)
CHEN = Actor(8, 1, Role.CREW, 8)
SAM = Actor(14, 2, Role.DIRECTOR, None)
PRIYA = Actor(15, 2, Role.LEAD, None)

# Seeded missions
GATEWAY, ASTEROID, REBOOST, MEDICAL, TELESCOPE, COMMS, MARS, PAYLOAD = range(1, 9)
# Seeded slots
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT, GEOLOGIST, REBOOST_ENGINEER = range(1, 7)
FLIGHT_SURGEON, TELESCOPE_ENGINEER, COMMS_ENGINEER = 7, 8, 10
# Aurora skills
PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, FLIGHT_MEDICINE = range(1, 7)
HELIX_PILOTING = 7


def svc(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def d(iso):
    return date.fromisoformat(iso)


def snapshot(conn):
    """Everything a missions use case can change."""
    return {
        table: [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
        for table in ("missions", "slots", "slot_requirements", "audit_events", "approvals")
    }


def events(conn, mission_id):
    rows = conn.execute(
        "SELECT actor_id, event, from_status, to_status, data FROM audit_events"
        " WHERE mission_id = ? ORDER BY id",
        (mission_id,),
    ).fetchall()
    return [(r[0], r[1], r[2], r[3], json.loads(r[4])) for r in rows]


def last_events(conn, mission_id, n):
    return events(conn, mission_id)[-n:]


def status_of(conn, mission_id):
    return conn.execute("SELECT status FROM missions WHERE id = ?", (mission_id,)).fetchone()[0]


def propose_chen_for_reboost(conn):
    """Chen proposed as Station Reboost's second Engineer (Gus is already accepted)."""
    with pytest.raises(Forbidden) as err:
        missions.update_mission(svc(seeded_db, LEE), GATEWAY, name="Gateway (Lee)")
    assert err.value.code == "not_owner"
    with pytest.raises(Forbidden):
        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer())


def test_m1_transferring_a_pending_mission_returns_it_to_draft_and_clears_approvals(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, RUTH), COMMS, LEE.user_id)
    assert view.mission.status == MissionStatus.DRAFT
    assert view.approvals == ()
    assert [e[:4] for e in last_events(seeded_db, COMMS, 2)] == [
        (RUTH.user_id, "mission.transferred", None, None),
        (RUTH.user_id, "mission.returned_to_draft", "pending_approval", "draft"),
    ]
    assert last_events(seeded_db, COMMS, 1)[0][4]["cause"] == "mission.transferred"


def test_m1_transferring_an_active_mission_keeps_it_active(seeded_db):
    view = missions.transfer_ownership(svc(seeded_db, INGRID), TELESCOPE, NORA.user_id)
    assert (view.mission.status, view.mission.owner_id) == (MissionStatus.ACTIVE, NORA.user_id)
    assert [e[1] for e in last_events(seeded_db, TELESCOPE, 1)] == ["mission.transferred"]


@pytest.mark.parametrize(
    ("mission_id", "message"),
    [
        (MARS, "Can't transfer a mission that's completed"),
        (GATEWAY, "Can't transfer a mission that's cancelled"),
    ],
)
def test_m1_a_final_mission_cannot_be_transferred(seeded_db, mission_id, message):
    seeded_db.execute("UPDATE missions SET status = 'cancelled' WHERE id = ?", (GATEWAY,))
    before = snapshot(seeded_db)
    with pytest.raises(StateConflict) as err:
        missions.transfer_ownership(svc(seeded_db, RUTH), mission_id, NORA.user_id)
    assert (err.value.code, err.value.message) == ("mission_final", message)
    assert snapshot(seeded_db) == before
```

</details>

**🔧 Edit**

```json
{
  "replace_all": false,
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/tests/integration/test_missions_service.py",
  "old_string": "    with pytest.raises(Forbidden):\n        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer())\n\n\ndef test_m1_transferring_a_pending_mission_returns_it_to_draft_and_clears_approvals(seeded_db):",
  "new_string": "    with pytest.raises(Forbidden):\n        missions.add_slot(svc(seeded_db, LEE), GATEWAY, engineer())\n\n\ndef test_ac7_after_transfer_only_the_new_owner_can_propose_apply_the_match_and_submit(seeded_db):\n    missions.transfer_ownership(svc(seeded_db, RUTH), GATEWAY, NORA.user_id)\n\n    def refused_to_lee(call, doing):\n        before = snapshot(seeded_db)\n        with pytest.raises(Forbidden) as err:\n            call(svc(seeded_db, LEE))\n        assert (err.value.code, err.value.message) == (\n            \"not_owner\",\n            f\"Only the mission's owner can {doing} this mission\",\n        )\n        assert snapshot(seeded_db) == before\n\n    # Propose: the previous owner can't; the new owner can.\n    refused_to_lee(\n        lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, BEN.crew_profile_id),\n        \"propose crew for\",\n    )\n    ben = assignments.propose(svc(seeded_db, NORA), GATEWAY, FLIGHT_ENGINEER, BEN.crew_profile_id)\n    assert ben.status == AssignmentStatus.PROPOSED\n\n    # Apply the match: the same.\n    refused_to_lee(lambda c: matching.apply(c, GATEWAY), \"apply suggested crew to\")\n    made = matching.apply(svc(seeded_db, NORA), GATEWAY)\n    assert [(a.slot_id, a.crew_profile_id) for a in made] == [(COMMANDER, 6), (SPECIALIST, 9)]\n\n    # Submit, once every proposal is accepted: the same.\n    crew_actors = {7: BEN, 6: ANA, 9: Actor(9, 1, Role.CREW, 9)}\n    for a in (ben, *made):\n        assignments.accept(svc(seeded_db, crew_actors[a.crew_profile_id]), a.id)\n    refused_to_lee(lambda c: approvals.submit(c, GATEWAY), \"submit\")\n    view = approvals.submit(svc(seeded_db, NORA), GATEWAY)\n    assert view.mission.status == MissionStatus.PENDING_APPROVAL\n\n\ndef test_m1_transferring_a_pending_mission_returns_it_to_draft_and_clears_approvals(seeded_db):"
}
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -i '' 's/^from mission_control.services import missions$/from mission_control.services import approvals, assignments, matching, missions/' tests/integration/test_missions_service.py && sed -i '' 's/^transferring ownership (PRD M1–M3, M5, M7, §5.7, AC-4, AC-5, AC-7, AC-24, AC-27, AC-29)."""/transferring ownership (PRD M1–M3, M5, M7, §5.7, AC-4, AC-5, AC-7, AC-24, AC-27, AC-29).\n\nAC-7 is also checked across services here: after a transfer, only the new owner can propose,\napply the match and submit."""/' tests/integration/test_missions_service.py && head -6 tests/integration/test_missions_service.py && uv run pytest -q -o addopts='' tests/integration/test_missions_service.py -k "ac7" 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
The file /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/tests/integration/test_missions_service.py has been updated successfully.
```

</details>

<details>
<summary>↳ Result</summary>

```
"""M11: the missions service. Viewing, creating and editing missions and their slots, and
transferring ownership (PRD M1–M3, M5, M7, §5.7, AC-4, AC-5, AC-7, AC-24, AC-27, AC-29).

AC-7 is also checked across services here: after a transfer, only the new owner can propose,
apply the match and submit."""

..........                                                               [100%]
10 passed, 122 deselected in 0.40s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='tests/integration/test_missions_service.py'
s=open(p).read()
old='''    def refused_to_lee(call, doing):
        before = snapshot(seeded_db)
        with pytest.raises(Forbidden) as err:
            call(svc(seeded_db, LEE))
        assert (err.value.code, err.value.message) == (
            "not_owner",
            f"Only the mission's owner can {doing} this mission",
        )
        assert snapshot(seeded_db) == before
'''
new='''    def state():
        rows = seeded_db.execute("SELECT * FROM assignments ORDER BY id").fetchall()
        return snapshot(seeded_db), [tuple(r) for r in rows]

    def refused_to_lee(call, doing):
        before = state()
        with pytest.raises(Forbidden) as err:
            call(svc(seeded_db, LEE))
        assert (err.value.code, err.value.message) == (
            "not_owner",
            f"Only the mission's owner can {doing} this mission",
        )
        assert state() == before
'''
assert s.count(old)==1
s=s.replace(old,new)
open(p,'w').write(s)
EOF
uv run pytest -q -o addopts='' tests/integration/test_missions_service.py -k "ac7" 2>&1 | tail -1
```

<details>
<summary>↳ Result</summary>

```
10 passed, 122 deselected in 0.69s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -n "^def snapshot\|^def refused" -A10 tests/integration/test_assignments_service.py | head -30
```

<details>
<summary>↳ Result</summary>

```
82:def snapshot(conn):
83-    """Every table an assignment use case could change, to prove a refusal changed nothing."""
84-    tables = ("missions", "slots", "assignments", "approvals", "audit_events")
85-    return {
86-        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
87-    }
88-
89-
90:def refused(fn, *args, **kwargs):
91-    with pytest.raises(RuleViolation) as caught:
92-        fn(*args, **kwargs)
93-    return caught.value
94-
95-
96-# --- Propose (S1, AC-14) ------------------------------------------------------------------
97-
98-
99-def test_s1_owner_proposes_an_eligible_crew_member(seeded_db):
100-    before = last_audit_id(seeded_db)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='tests/integration/test_assignments_service.py'
s=open(p).read()
old='''def test_ac4_proposing_on_a_pending_mission_returns_it_to_draft(seeded_db):
    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, "Backup Engineer", 1, {SYS_ENG: 3})
'''
new='''def test_ac4_proposing_on_a_pending_mission_returns_it_to_draft(seeded_db):
    # Users can't add a slot to a Pending mission without sending it back to Draft, so the open
    # place is made through the repository: this checks the return to Draft on its own.
    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, "Backup Engineer", 1, {SYS_ENG: 3})
'''
assert s.count(old)==1
s=s.replace(old,new)
anchor='''def test_ac5_proposing_on_an_active_mission_is_refused(seeded_db):'''
add='''def test_ac4_a_pending_missions_slots_are_full_so_a_proposal_is_refused_and_it_stays_pending(
    seeded_db,
):
    # A mission can only be submitted with every place filled, so on a Pending mission a
    # proposal finds no open place: Deep Space Comms' only Engineer place is Ben's.
    before = snapshot(seeded_db)
    error = refused(assignments.propose, as_(seeded_db, NORA), DEEP_SPACE, DEEP_SPACE_ENGINEER, GUS_ID)
    assert (error.code, error.message) == (
        "rule_violation",
        "Gus can't be proposed as Engineer on Deep Space Comms Upgrade",
    )
    assert [(p.code, p.message, dict(p.refs)) for p in error.problems] == [
        (
            "slot_full",
            "Engineer on Deep Space Comms Upgrade has no open places",
            {"slot_id": DEEP_SPACE_ENGINEER},
        )
    ]
    assert mission_status(seeded_db, DEEP_SPACE) == "pending_approval"
    assert snapshot(seeded_db) == before


'''
assert s.count(anchor)==1
s=s.replace(anchor, add+anchor)
open(p,'w').write(s)
EOF
uv run ruff format tests | tail -1; uv run pytest -q -o addopts='' tests/integration/test_assignments_service.py -k "ac4" 2>&1 | tail -2
```

<details>
<summary>↳ Result</summary>

```
1 file reformatted, 56 files left unchanged
...                                                                      [100%]
3 passed, 78 deselected in 0.63s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "RuleViolation(" src | grep -v "class \|RuleViolation\.of"; grep -rn "InvalidInput(f\".*needs a reason\|needs a reason" src
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/missions/rules.py:98:        raise RuleViolation(message(names), problems)
src/mission_control/services/context.py:111:        raise RuleViolation(message, problems)
src/mission_control/infra/schema.sql:169:  CHECK (decision = 'approve' OR length(trim(coalesce(reason, ''))) > 0),   -- rejection needs a reason
src/mission_control/services/inputs.py:33:    Lunar Relay needs a reason" for `doing="Cancelling Lunar Relay"`."""
src/mission_control/services/inputs.py:36:        raise InvalidInput(f"{doing} needs a reason")
src/mission_control/services/crew.py:145:            problems.append(invalid("Unavailability needs a reason"))
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && grep -rn "StateConflict\|state_problem" src/mission_control/services; grep -rn "def _about\|_overlap\|_join\b\|_join_names" src
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/services/assignments.py:27:    StateConflict,
src/mission_control/services/assignments.py:261:        raise StateConflict(problem)
src/mission_control/services/approvals.py:22:    StateConflict,
src/mission_control/services/approvals.py:168:        raise StateConflict(problems[0])
src/mission_control/services/missions/__init__.py:7:3. check the mission's state with `touch_for_change` (StateConflict);
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 196,215p src/mission_control/services/assignments.py
```

<details>
<summary>↳ Result</summary>

```
def cascade_mission_end(
    ctx: ServiceContext, repos: Repos, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:
    """Apply a mission's completion or cancellation to its assignments: completing it completes
    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything
    else is left as it is. Each change is written and audited as the acting user.

    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked
    the mission's own transition, so the assignments change in the same transaction as the
    mission and roll back with it. It does no permission or state checks of its own. Returns the
    changed assignments, in id order."""
    if final_status not in _MISSION_ENDS:
        raise ValueError(f"a mission ends completed or cancelled, not {final_status.value}")
    if not ctx.conn.in_transaction:
        raise RuntimeError("cascade_mission_end runs inside the caller's ctx.write()")
    slots = _slot_specs(repos, mission)
    changed = []
    for assignment in repos.missions.assignments(mission.id):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && python3 - <<'EOF'
p='src/mission_control/services/assignments.py'
s=open(p).read()
old='''    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked'''
new='''    Call it inside the caller's `with ctx.write() as repos:`, after the caller has authorized and
    checked'''
assert s.count(old)==1
s=s.replace(old,new)
s=s.replace('''    checked
    the mission's own transition, so the assignments change in the same transaction as the
    mission and roll back with it. It does no permission or state checks of its own. Returns the
    changed assignments, in id order."""''','''    checked the mission's own transition, so the assignments change in the same transaction as
    the mission and roll back with it. It does no permission or state checks of its own. Returns
    the changed assignments, in id order."""''')
open(p,'w').write(s)
EOF
sed -n 199,208p src/mission_control/services/assignments.py
```

<details>
<summary>↳ Result</summary>

```
    ctx: ServiceContext, repos: Repos, mission: Mission, final_status: MissionStatus
) -> list[Assignment]:
    """Apply a mission's completion or cancellation to its assignments: completing it completes
    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything
    else is left as it is. Each change is written and audited as the acting user.

    Call it inside the caller's `with ctx.write() as repos:`, after the caller has authorized and
    checked the mission's own transition, so the assignments change in the same transaction as
    the mission and roll back with it. It does no permission or state checks of its own. Returns
    the changed assignments, in id order."""
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && sed -n 60,96p docs/technical-design.md; sed -n 160,180p README.md
```

<details>
<summary>↳ Result</summary>

````
```

| Layer | Folder | Responsibility | May depend on |
|---|---|---|---|
| CLI | `cli/` | Commands, output, prompts | API over HTTP only |
| API | `api/` | Validate input, resolve `Actor`, call a service, map errors | services |
| Services | `services/` | One use case = one transaction + audit | domain, infra |
| Domain | `domain/` | Every business rule, pure (no I/O) | nothing |
| Infra | `infra/` | Connections, schema, settings, scoped repositories, security, platform statements | domain types |

**How a request flows** (example: `mc missions submit 12`)

1. The CLI sends `POST /api/v1/missions/12/submit` with the bearer token.
2. The API resolves the token to an `Actor` (user, organisation, role) and calls `services.missions.submit(actor, 12)`.
3. The service opens `BEGIN IMMEDIATE` and loads the mission through `Repos(conn, actor.org_id)`.
4. `domain.lifecycle.check_submit(...)` returns a list of problems. If the list is empty, the service writes the new status and an audit event, then commits.
5. The API returns `200` with the mission, or `409` with every problem. The CLI prints one bullet per problem and exits with code `1`.

<details><summary>Folder layout</summary>

```
src/mission_control/
  domain/    dates  enums  errors  eligibility  matching  lifecycle  approvals  permissions  passwords  records
  infra/     db  schema.sql  settings  security  platform  repositories/
  services/  auth  admin  crew  missions  assignments  approvals  matching  audit  inbox
  api/       app  deps  errors  schemas/  routers/
  cli/       main  client  config  render  resolve  commands/
  seed/      data  loader
  admin_cli.py        # mc-admin: init-db, seed, create-org
tests/  unit/  integration/  api/  cli/  builders.py  conftest.py
```

`settings` reads the `MC_*` environment variables. `security` holds the unscoped login and token lookups, and `platform` the unscoped organisation statements `mc-admin create-org` needs before any tenant exists. Everything else goes through `Repos`.
</details>

---

| [`docs/cli-ux.md`](docs/cli-ux.md) | Mock CLI sessions for the matcher |
| [`docs/backlog.md`](docs/backlog.md) | Decisions deliberately left open for later |

## Code layout

```
src/mission_control/
  domain/       every business rule, as pure functions: dates, eligibility, matcher, lifecycle, permissions
  infra/        SQLite connections, schema, settings, tenant-scoped repositories, password hashing
                and tokens, and the organisation statements mc-admin needs
  services/     one use case per function: one transaction, its checks and its audit event
  api/          FastAPI app (mc-server): validates input, resolves the caller, maps errors
  cli/          the mc command, a client of the HTTP API
  seed/         the demo data, shared by mc-admin and the tests
  admin_cli.py  mc-admin: init-db, seed, create-org
tests/          unit/ (domain), integration/ (services, database), api/, cli/
```

`domain/` imports nothing from the other layers, and the CLI holds no business rules: it only calls the API. The [design](docs/technical-design.md#2-architecture) explains why.

## How it was built
````

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run pytest -W error -q -o addopts='' 2>&1 | tail -2; uv run ruff check | tail -1; uv run ruff format --check | tail -1; uv run python /tmp/fixcleanup/snapshot.py > /tmp/fixcleanup/after.txt 2>&1; echo exit $?; diff /tmp/fixcleanup/before.txt /tmp/fixcleanup/after.txt > /tmp/fixcleanup/snapshot.diff; wc -l /tmp/fixcleanup/snapshot.diff; grep "^[<>]" /tmp/fixcleanup/snapshot.diff | grep -v "^[<>] AUDIT" | cut -c1-200
```

<details>
<summary>↳ Result</summary>

```
.....................................................                    [100%]
1709 passed in 29.28s
All checks passed!
155 files already formatted
exit 0
      50 /tmp/fixcleanup/snapshot.diff
```

</details>

**🔧 Bash**

```bash
cat /tmp/fixcleanup/snapshot.diff
```

<details>
<summary>↳ Result</summary>

```
63,64c63,64
< AUDIT [1, "org.required_approvals_changed", null, null, null, null, null, null, {"from": 2, "to": 3}]
< AUDIT [1, "org.required_approvals_changed", null, null, null, null, null, null, {"from": 3, "to": 2}]
---
> AUDIT [1, "org.required_approvals_changed", null, null, null, null, null, null, {"changes": {"required_approvals": [2, 3]}}]
> AUDIT [1, "org.required_approvals_changed", null, null, null, null, null, null, {"changes": {"required_approvals": [3, 2]}}]
69,70c69,70
< AUDIT [1, "user.role_changed", null, null, null, null, null, null, {"from_role": "crew", "to_role": "lead", "user_id": 11, "user_name": "Fay Moreau"}]
< AUDIT [1, "user.role_changed", null, null, null, null, null, null, {"from_role": "director", "to_role": "crew", "user_id": 3, "user_name": "Ingrid Holm"}]
---
> AUDIT [1, "user.role_changed", null, null, null, null, null, null, {"changes": {"role": ["crew", "lead"]}, "user_id": 11, "user_name": "Fay Moreau"}]
> AUDIT [1, "user.role_changed", null, null, null, null, null, null, {"changes": {"role": ["director", "crew"]}, "user_id": 3, "user_name": "Ingrid Holm"}]
75,77c75,77
< AUDIT [1, "skill.updated", null, null, null, null, null, null, {"from_category": null, "from_name": "Systems Engineering", "skill_id": 3, "to_category": null, "to_name": "Systems Eng"}]
< AUDIT [1, "skill.updated", null, null, null, null, null, null, {"from_category": null, "from_name": "Systems Eng", "skill_id": 3, "to_category": "Eng", "to_name": "Systems Eng"}]
< AUDIT [1, "skill.updated", null, null, null, null, null, null, {"from_category": "Eng", "from_name": "Systems Eng", "skill_id": 3, "to_category": null, "to_name": "Sys Eng"}]
---
> AUDIT [1, "skill.updated", null, null, null, null, null, null, {"changes": {"name": ["Systems Engineering", "Systems Eng"]}, "skill_id": 3, "skill_name": "Systems Eng"}]
> AUDIT [1, "skill.updated", null, null, null, null, null, null, {"changes": {"category": [null, "Eng"]}, "skill_id": 3, "skill_name": "Systems Eng"}]
> AUDIT [1, "skill.updated", null, null, null, null, null, null, {"changes": {"category": ["Eng", null], "name": ["Systems Eng", "Sys Eng"]}, "skill_id": 3, "skill_name": "Sys Eng"}]
252,253c252,253
< AUDIT [7, "crew.details_updated", null, null, 7, null, null, null, {"crew_name": "Benji", "previous_name": "Ben"}]
< AUDIT [7, "crew.details_updated", null, null, 7, null, null, null, {"crew_name": "Benji", "previous_name": "Benji"}]
---
> AUDIT [7, "crew.details_updated", null, null, 7, null, null, null, {"changes": {"display_name": ["Ben", "Benji"]}, "crew_name": "Benji"}]
> AUDIT [7, "crew.details_updated", null, null, 7, null, null, null, {"changes": {}, "crew_name": "Benji"}]
256,258c256,258
< AUDIT [4, "crew.skill_set", null, null, 8, null, null, null, {"crew_name": "Chen", "level": 4, "previous_level": 3, "skill_name": "Systems Engineering"}]
< AUDIT [4, "crew.skill_set", null, null, 8, null, null, null, {"crew_name": "Chen", "level": 2, "previous_level": null, "skill_name": "Geology"}]
< AUDIT [4, "crew.skill_removed", null, null, 7, null, null, null, {"crew_name": "Benji", "previous_level": 3, "skill_name": "EVA"}]
---
> AUDIT [4, "crew.skill_set", null, null, 8, null, null, null, {"changes": {"level": [3, 4]}, "crew_name": "Chen", "skill_name": "Systems Engineering"}]
> AUDIT [4, "crew.skill_set", null, null, 8, null, null, null, {"changes": {"level": [null, 2]}, "crew_name": "Chen", "skill_name": "Geology"}]
> AUDIT [4, "crew.skill_removed", null, null, 7, null, null, null, {"changes": {"level": [3, null]}, "crew_name": "Benji", "skill_name": "EVA"}]
458,460c458,460
< AUDIT [1, "mission.transferred", 1, null, null, null, null, null, {"from_owner_id": 4, "from_owner_name": "Lee Park", "mission_name": "Gateway II", "to_owner_id": 5, "to_owner_name": "Nora Quinn"}]
< AUDIT [1, "mission.transferred", 6, null, null, null, null, null, {"from_owner_id": 5, "from_owner_name": "Nora Quinn", "mission_name": "DSC II", "to_owner_id": 4, "to_owner_name": "Lee Park"}]
< AUDIT [1, "mission.transferred", 5, null, null, null, null, null, {"from_owner_id": 4, "from_owner_name": "Lee Park", "mission_name": "Orbital Telescope Service", "to_owner_id": 5, "to_owner_name": "Nora Quinn"}]
---
> AUDIT [1, "mission.transferred", 1, null, null, null, null, null, {"changes": {"owner_id": [4, 5], "owner_name": ["Lee Park", "Nora Quinn"]}, "mission_name": "Gateway II"}]
> AUDIT [1, "mission.transferred", 6, null, null, null, null, null, {"changes": {"owner_id": [5, 4], "owner_name": ["Nora Quinn", "Lee Park"]}, "mission_name": "DSC II"}]
> AUDIT [1, "mission.transferred", 5, null, null, null, null, null, {"changes": {"owner_id": [4, 5], "owner_name": ["Lee Park", "Nora Quinn"]}, "mission_name": "Orbital Telescope Service"}]
463c463
< AUDIT [5, "slot.requirements_changed", 1, null, null, null, null, null, {"mission_name": "Gateway II", "previous_requirements": [{"min_level": 3, "skill_id": 3, "skill_name": "Systems Engineering"}], "requirements": [{"min_level": 4, "skill_id": 3, "skill_name": "Systems Engineering"}, {"min_level": 1, "skill_id": 4, "skill_name": "EVA"}], "slot_id": 1, "slot_name": "Flight Engineer"}]
---
> AUDIT [5, "slot.requirements_changed", 1, null, null, null, null, null, {"changes": {"requirements": [[{"min_level": 3, "skill_id": 3, "skill_name": "Systems Engineering"}], [{"min_level": 4, "skill_id": 3, "skill_name": "Systems Engineering"}, {"min_level": 1, "skill_id": 4, "skill_name": "EVA"}]]}, "mission_name": "Gateway II", "slot_id": 1, "slot_name": "Flight Engineer"}]
1018c1018
< AUDIT [1, "mission.transferred", 1, null, null, null, null, null, {"from_owner_id": 4, "from_owner_name": "Lee Park", "mission_name": "Lunar Gateway Resupply", "to_owner_id": 5, "to_owner_name": "Nora Quinn"}]
---
> AUDIT [1, "mission.transferred", 1, null, null, null, null, null, {"changes": {"owner_id": [4, 5], "owner_name": ["Lee Park", "Nora Quinn"]}, "mission_name": "Lunar Gateway Resupply"}]
```

</details>

**🔧 Bash**

```bash
/tmp/fixcleanup/golden.sh /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup /tmp/fixcleanup/golden_after.txt; diff <(sed -E 's/[0-9]+ [A-Z][a-z]+ [0-9]{4} [0-9:]{5}/<when>/' /tmp/fixcleanup/golden_before.txt) <(sed -E 's/[0-9]+ [A-Z][a-z]+ [0-9]{4} [0-9:]{5}/<when>/' /tmp/fixcleanup/golden_after.txt) && echo "IDENTICAL apart from timestamps"; cat /tmp/fixcleanup/golden_after.txt; pgrep -fl "uvicorn.*mission_control" || echo "no server left"
```

<details>
<summary>↳ Result</summary>

```
IDENTICAL apart from timestamps
### mc missions history 1
  When (UTC)          Who             What
  12 Oct 2026 05:36   Ruth Adeyemi    Created the mission
  12 Oct 2026 05:36   Lee Park        Proposed Ana for Commander
  12 Oct 2026 05:36   Lee Park        Proposed Chen for Flight Engineer
  12 Oct 2026 05:36   Lee Park        Proposed Dana for Mission Specialist
  12 Oct 2026 05:36   Ana Okafor      Accepted Commander
  12 Oct 2026 05:36   Chen Wu         Accepted Flight Engineer
  12 Oct 2026 05:36   Dana Reyes      Accepted Mission Specialist
  12 Oct 2026 05:36   Lee Park        Submitted for approval
  12 Oct 2026 05:36   Marco Bianchi   Approved
  12 Oct 2026 05:36   Ingrid Holm     Approved
  12 Oct 2026 05:36   Ingrid Holm     Mission became active
  12 Oct 2026 05:36   Lee Park        Completed
  12 Oct 2026 05:36   Lee Park        Ana's assignment completed
  12 Oct 2026 05:36   Lee Park        Chen's assignment completed
  12 Oct 2026 05:36   Lee Park        Dana's assignment completed
### extra: transfer 6 to lee, lee edits name and end date, history 6
  When (UTC)          Who             What
  12 Oct 2026 05:36   Nora Quinn      Created the mission
  12 Oct 2026 05:36   Nora Quinn      Submitted for approval
  12 Oct 2026 05:36   Marco Bianchi   Approved
  12 Oct 2026 05:36   Ruth Adeyemi    Handed the mission to Lee Park
  12 Oct 2026 05:36   Ruth Adeyemi    Mission went back to Draft
  12 Oct 2026 05:36   Lee Park        Edited the mission
no server left
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && uv run pytest -W error -o addopts='' -rs tests/cli/test_readme_smoke.py 2>&1 | tail -3; uv run pytest -W error -q -o addopts='' -rs 2>&1 | grep -i "skip" | head; git status --short
```

<details>
<summary>↳ Result</summary>

```
tests/cli/test_readme_smoke.py .....                                     [100%]

============================== 5 passed in 5.58s ===============================
 M src/mission_control/admin_cli.py
 M src/mission_control/cli/commands/common.py
 M src/mission_control/cli/commands/missions.py
 M src/mission_control/cli/main.py
 M src/mission_control/cli/resolve.py
 M src/mission_control/domain/approvals.py
 M src/mission_control/domain/eligibility.py
 M src/mission_control/domain/events.py
 M src/mission_control/domain/lifecycle.py
 M src/mission_control/infra/repositories/facts.py
 M src/mission_control/infra/repositories/mission_slots.py
 M src/mission_control/infra/security.py
 M src/mission_control/seed/data.py
 M src/mission_control/seed/loader.py
 M src/mission_control/services/admin.py
 M src/mission_control/services/approvals.py
 M src/mission_control/services/assignments.py
 M src/mission_control/services/auth.py
 M src/mission_control/services/context.py
 M src/mission_control/services/crew.py
 M src/mission_control/services/matching.py
 M src/mission_control/services/missions/changes.py
 M src/mission_control/services/missions/inputs.py
 M src/mission_control/services/missions/lifecycle.py
 M src/mission_control/services/missions/rules.py
 M src/mission_control/services/missions/slots.py
 M src/mission_control/services/missions/views.py
 M tests/cli/test_cli_missions.py
 M tests/integration/test_admin_service.py
 M tests/integration/test_assignments_service.py
 M tests/integration/test_crew_service.py
 M tests/integration/test_missions_service.py
 M tests/integration/test_repository_sql.py
 M tests/unit/domain/test_approvals.py
 M tests/unit/domain/test_events.py
?? src/mission_control/cli/base.py
?? src/mission_control/domain/wording.py
?? src/mission_control/services/inputs.py
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup && git diff src/mission_control/services/missions/rules.py src/mission_control/services/missions/changes.py | head -150; git diff --stat | tail -1
```

<details>
<summary>↳ Result</summary>

```
diff --git a/src/mission_control/services/missions/changes.py b/src/mission_control/services/missions/changes.py
index bbe3f12..d06d107 100644
--- a/src/mission_control/services/missions/changes.py
+++ b/src/mission_control/services/missions/changes.py
@@ -8,8 +8,9 @@ from mission_control.domain.eligibility import DatesEdit
 from mission_control.domain.enums import Action, MissionStatus, Role
 from mission_control.domain.errors import Problem, RuleViolation
 from mission_control.domain.events import Event
-from mission_control.domain.lifecycle import StateConflict, mission_status_after, state_problem
+from mission_control.domain.lifecycle import mission_status_after, require_state
 from mission_control.domain.permissions import Context
+from mission_control.domain.wording import join_names
 from mission_control.services.context import (
     ServiceContext,
     check,
@@ -17,21 +18,17 @@ from mission_control.services.context import (
     mission_context,
     visible_mission,
 )
+from mission_control.services.inputs import date_problems, invalid, invalid_input, refuse_input
 from mission_control.services.missions.inputs import (
     SlotInput,
-    date_problems,
-    invalid,
-    invalid_input,
     levels,
     name_problems,
-    refuse_input,
     requirement_data,
     slot_label,
     slot_problems,
 )
 from mission_control.services.missions.loading import open_for_edit, reload, resolve_skills
 from mission_control.services.missions.rules import (
-    join_names,
     owner_problems,
     record_change,
     refuse_if_invalidated,
@@ -165,7 +162,8 @@ def update_mission(
             mission,
             status,
             Event.MISSION_UPDATED,
-            {"mission_name": new_name, "changes": changes},
+            new_name,
+            {"changes": changes},
         )
         return mission_view(repos, reload(repos, mission))
 
@@ -176,9 +174,7 @@ def transfer_ownership(ctx: ServiceContext, mission_id: int, new_owner_id: int)
     with ctx.write() as repos:
         mission = visible_mission(ctx, repos, mission_id)
         ctx.authorize(Action.TRANSFER, mission_context(repos, mission))
-        problem = state_problem(mission.status, Action.TRANSFER)
-        if problem is not None:
-            raise StateConflict(problem)
+        require_state(mission.status, Action.TRANSFER)
         new_owner = found(repos.users.get(new_owner_id), "User")
         if new_owner.id == mission.owner_id:
             raise RuleViolation.of(
@@ -199,12 +195,12 @@ def transfer_ownership(ctx: ServiceContext, mission_id: int, new_owner_id: int)
             mission,
             status,
             Event.MISSION_TRANSFERRED,
+            mission.name,
             {
-                "mission_name": mission.name,
-                "from_owner_id": old_owner.id,
-                "from_owner_name": old_owner.name,
-                "to_owner_id": new_owner.id,
-                "to_owner_name": new_owner.name,
+                "changes": {
+                    "owner_id": [old_owner.id, new_owner.id],
+                    "owner_name": [old_owner.name, new_owner.name],
+                }
             },
         )
         return mission_view(repos, reload(repos, mission))
diff --git a/src/mission_control/services/missions/rules.py b/src/mission_control/services/missions/rules.py
index dc0f3fa..d6cd6f6 100644
--- a/src/mission_control/services/missions/rules.py
+++ b/src/mission_control/services/missions/rules.py
@@ -48,8 +48,13 @@ def refuse_taken_name(
         (s for s in slots if s.id != slot_id and _name_key(s.name) == _name_key(name)), None
     )
     if taken is not None:
-        message = f"{mission.name} already has a slot called {taken.name}"
-        raise RuleViolation(message, [Problem("already_exists", message, {"slot_id": taken.id})])
+        raise RuleViolation.of(
+            Problem(
+                "already_exists",
+                f"{mission.name} already has a slot called {taken.name}",
+                {"slot_id": taken.id},
+            )
+        )
 
 
 def repeated_name_problems(slots: Sequence[SlotInput]) -> list[Problem]:
@@ -142,21 +147,12 @@ def record_change(
     mission: Mission,
     status: MissionStatus,
     event: Event,
+    mission_name: str,
     data: Mapping[str, object],
 ) -> None:
     """Apply the status `touch_for_change` (or the transfer rule) gave, then audit the change
-    and, if a Pending mission went back to Draft, that return with its cause."""
-    ctx.audit(event, mission_id=mission.id, data=data)
+    and, if a Pending mission went back to Draft, that return with its cause. `mission_name` is
+    the mission's name once the change is made; the audit `data` starts with it."""
+    ctx.audit(event, mission_id=mission.id, data={"mission_name": mission_name, **data})
     if status != mission.status:
-        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))
-
-
-# Wording
-
-
-def join_names(names: Sequence[str]) -> str:
-    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
-
-
-def is_are(names: Sequence[str]) -> str:
-    return "is" if len(names) == 1 else "are"
+        return_to_draft(ctx, repos, mission, event, mission_name)
 35 files changed, 641 insertions(+), 515 deletions(-)
```

</details>

**🔧 SubagentHandback**

````json
{
  "message": "## Consistency clean-up: all 8 fixes done in `.worktrees/fix-cleanup`, nothing committed\n\nAll 8 fixes are in, uncommitted (35 files modified, 3 new). The tests pass: `uv run pytest -W error -q -o addopts=''` gives **1709 passed**, up from 1697, with no skips; `tests/cli/test_readme_smoke.py` ran 5 of 5. `ruff check` and `ruff format --check` are both clean.\n\nThe behaviour snapshot diff contains only audit `data` lines. The real `mc missions history` output is identical before and after, apart from timestamps.\n\n### Things for you to decide\n1. **Bio-only profile edits.** `crew.details_updated` still doesn't audit the bio, as before. So a bio-only edit now records `changes: {}`, where it used to record `previous_name == crew_name`. If you want it, I can add `\"bio\": [old, new]` to `changes`.\n2. **`security.py` signatures changed.** `login_state`, `password_hash_of` and `set_password_hash` now take `org_id` and filter `org_id = :org`. Callers in `services/auth.py` and one test were updated. Only login by email and the four session statements on `auth_tokens` are exempt from the SQL check.\n3. **`mc-admin` now imports `mission_control.cli.base`.** That new module holds only the shared Typer pieces and has no API or database access.\n4. **Two smaller changes:**\n   - The `Event` enum is regrouped by topic. The values are unchanged, and nothing iterates it except its test.\n   - `mission_view` now gets open places from `facts.slot_specs`, which adds 2 small queries per view.\n5. **Left alone:** the CLI keeps its own `render.join_names`, because the CLI doesn't import `domain`.\n\n### Per fix\n\n**1. One audit `data` shape — resolved: yes.**\n- Convention: names at the time (`mission_name`, `crew_name`, `slot_name`, `skill_name`, `user_name`), plus `changes: {field: [old, new]}` listing only the fields that changed. A value that didn't exist before, or no longer does, is null. This is documented in the `domain/events.py` docstring.\n- Converted events:\n  - `org.required_approvals_changed` → `{\"changes\": {\"required_approvals\": [2, 3]}}`\n  - `user.role_changed` → `changes.role`\n  - `skill.updated` → `skill_name` (the new name) plus `changes.name` / `changes.category`, only those that changed\n  - `mission.transferred` → `changes.owner_id` and `changes.owner_name`\n  - `slot.requirements_changed` → `changes.requirements: [old, new]`\n  - `crew.details_updated` → `changes.display_name`\n  - `crew.skill_set` / `crew.skill_removed` → `changes.level: [old, new|null]`\n- CLI renderer in `cli/commands/missions.py` now reads `{changes[owner_name][1]}`, and also falls back to plain text on a `TypeError`.\n- Tests updated in `test_admin_service.py`, `test_crew_service.py` and `test_missions_service.py`. New tests: the skill recategorise audit, and a CLI history test for a transfer, with and without names.\n\n**2. Single-reason refusals use `RuleViolation.of` — resolved: yes.**\n- Changed in `services/admin.py` (duplicate email, existing crew profile, `_name_taken`) and `services/missions/rules.py` (`refuse_taken_name`).\n- The only `RuleViolation(...)` left in `src/` is in the two places that raise several problems at once.\n\n**3. Shared helpers instead of copies — resolved: yes.**\n- New `domain/wording.py` with `join_names` and `is_are`. It replaces the copies in `eligibility.py`, `missions/rules.py` and `admin.py`.\n- `profile_context(profile)` in `services/context.py` replaces `_about` in `crew.py` and `assignments.py`.\n- `require_state(status, action)` in `domain/lifecycle.py` is now used by `approvals.py`, `matching.py`, `missions/lifecycle.py` and the transfer in `missions/changes.py`.\n- New `services/inputs.py` holds `refuse_input`, `invalid_input`, `invalid`, `date_problems` and the new `required_reason(reason, doing)`, which withdraw, reject and cancel now use. `missions/inputs.py` keeps only the mission-specific checks.\n- A `SlotRequirements` repository base in `mission_slots.py` is shared by `MissionSlots` and `FactsRepo`, so the requirements SQL exists once.\n- `mission_view` takes its open places from `facts.slot_specs`.\n- `eligibility.overlap_problem` is shared by the eligibility check and `crew.add_unavailability`.\n- New `cli/base.py` holds `HelpWhenBare` and `version_flag(program)`. `cli/main.py`, `cli/commands/common.py` and `admin_cli.py` use them.\n- `cli/resolve.py`: `skill_ids` and `skill_named` share `_catalogue` and `_skill_in`.\n\n**4. Dead `approver_problems` — resolved: yes.**\n- Removed from `domain/approvals.py`; nothing in `src/` used it.\n- Its unit tests in `tests/unit/domain/test_approvals.py` now run against `decision_problems`. The \"a Lead can't approve\" case is now a parameterised check through `permissions.authorize`: APPROVE and REJECT, as Lead and as Crew, each give `role_forbidden`.\n\n**5. Module references in `src/` — resolved: yes.**\n- `events.py` headings are now Missions, Slots, Assignments, Crew, Organisation and users, and Skill catalogue. `test_events.py` was regrouped to match.\n- The `seed/data.py` docstring no longer says \"tables in the PRD\".\n- A grep of `src/` for `M\\d+`, `AC-`, `§` and `PRD` now finds nothing.\n\n**6. Small coupling — resolved: yes.**\n- `record_change(..., event, mission_name, data)` takes the name explicitly and puts it first in `data`, so callers no longer pass it inside the dict.\n- `cascade_mission_end(ctx, repos, mission, final_status)` now takes `repos`; the caller and six tests were updated.\n\n**7. SQL check covers the seed loader and `security.py` — resolved: yes.**\n- `seed/loader.py` uses named parameters throughout. Each organisation's rows are written `org_id`-first with `:org` through a `_scoped` helper, so they pass the check without an exemption.\n- `security.py` uses named parameters throughout.\n- `test_repository_sql.py` now scans `platform.py`, `security.py` and `loader.py`.\n- Each module has its own documented exemption list:\n  - security: login by email, plus the four `auth_tokens` session statements;\n  - seed: the empty-database check, plus the organisation insert with its fixed id.\n- New tests check that each module has SQL, that every exemption is still in use, that module names don't clash with a repository, and that the exemptions cover only the listed statements.\n\n**8. Test gaps — resolved: yes.**\n- (a) New test `test_ac7_after_transfer_only_the_new_owner_can_propose_apply_the_match_and_submit` in `test_missions_service.py`. Lee is refused propose, apply-match and submit with `not_owner` and the exact message, and the database is unchanged. Nora succeeds at all three, ending Pending.\n- (b) New test `test_ac4_a_pending_missions_slots_are_full_so_a_proposal_is_refused_and_it_stays_pending` in `test_assignments_service.py`. Proposing Gus for Deep Space Comms' Engineer slot is refused with `slot_full`, the mission stays `pending_approval`, and the database is unchanged. The existing repository-based test is kept, with a comment explaining why it adds the slot that way.\n\n### Evidence\n- **Snapshot** (`/tmp/fixcleanup/snapshot.py`, 6 fresh seeded databases, about 230 service calls across admin, crew, missions, slots, assignments, approvals, matching, inbox and history, plus a full audit and state dump). It was confirmed to give the same output on two runs before any change. `/tmp/fixcleanup/snapshot.diff` is 50 lines, and every line is an `AUDIT` data-shape change. Two examples:\n  - Before: `{\"from\": 2, \"to\": 3}` → after: `{\"changes\": {\"required_approvals\": [2, 3]}}`\n  - Before: `{\"from_owner_id\": 4, \"from_owner_name\": \"Lee Park\", \"mission_name\": \"Lunar Gateway Resupply\", \"to_owner_id\": 5, \"to_owner_name\": \"Nora Quinn\"}` → after: `{\"changes\": {\"owner_id\": [4, 5], \"owner_name\": [\"Lee Park\", \"Nora Quinn\"]}, \"mission_name\": \"Lunar Gateway Resupply\"}`\n- **Real CLI run** (`/tmp/fixcleanup/golden.sh`: seed, uvicorn on a free port, a separate `HOME` per user). It ran the S1 golden path, then transferred mission 6 to Lee and had him edit it. `golden_before.txt` and `golden_after.txt` are identical apart from timestamps:\n```\n### mc missions history 1   (same before and after)\n  Ruth Adeyemi    Created the mission\n  Lee Park        Proposed Ana for Commander\n  ... Accepted ×3 · Submitted for approval · Approved ×2 · Mission became active · Completed\n  Lee Park        Ana's / Chen's / Dana's assignment completed\n### history 6\n  Ruth Adeyemi    Handed the mission to Lee Park      <- now read from changes.owner_name\n  Ruth Adeyemi    Mission went back to Draft\n  Lee Park        Edited the mission\n```\n- The server was stopped (no uvicorn process left), and everything stayed under `/tmp/fixcleanup/`.\n\n### Key files\n- New: `src/mission_control/domain/wording.py`, `src/mission_control/services/inputs.py`, `src/mission_control/cli/base.py`\n- Most-changed: `services/admin.py`, `services/crew.py`, `services/assignments.py`, `services/missions/{rules,changes,slots,inputs,lifecycle,views}.py`, `infra/security.py`, `seed/loader.py`, `infra/repositories/{facts,mission_slots}.py`, `tests/integration/test_repository_sql.py`\n\nAll paths are under `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/fix-cleanup/src/mission_control/` or `.../tests/`."
}
````

<details>
<summary>↳ Result</summary>

```
{"success":true,"message":"Report delivered to your caller."}
```

</details>
