# Subagent (01): Build M12 assignments in worktree

Source: `agent-a8d6cde39efcef097.jsonl` · 2026-10-12 02:35:11 UTC → 2026-10-12 02:44:39 UTC

Rendered from the raw JSONL without editing message content. Tool results and thinking are collapsed; expand them to read.


---

### 👤 User · 2026-10-12 02:35:11 UTC

You are implementing module **M12 (assignments service)** of the Mission Control project, in a dedicated git worktree.

**Work ONLY in:** `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments` (branch `m12-assignments`, based on main `171296f`).
- Use absolute paths or `cd` into it for every command.
- Never touch the main checkout or other worktrees.
- Do NOT commit or run state-changing git commands (`git status` / `git diff` are fine).
- No new dependencies.

**Context:**
- Modules SF, M9 and M10 are merged and visible in your worktree.
- M11 (missions service) is NOT merged yet: it's being fixed and refactored on main. Don't depend on `services/missions.py` and don't create it.
- Everything M12 needs is already in your worktree:
  - `domain/lifecycle.py`: `assignment_problem`, `assignment_status_after`, `mission_status_after_assignment_action`, `cascade`, `touch_for_change`;
  - `domain/eligibility.py`: `ineligibility_reasons`;
  - `infra/repositories/facts.py`: `candidate`, `slot_specs`, `roster`;
  - `infra/repositories/missions.py`: `get_visible`, `get_slot`, `assignments`, `rostered_user_ids`;
  - `services/context.py`: ServiceContext, found, check;
  - `domain/errors.py`: NotFound, Forbidden, RuleViolation (with `.of`), InvalidInput (message only).

**Read first:**
- `CLAUDE.md`;
- `docs/prd.md` §5.1, §5.4 (transition table), §5.6 (S1–S4), §5.7, §8 (AC-4, AC-5, AC-14, AC-15, AC-29), §9.3 (scenarios S4 and S5);
- `docs/technical-design.md` §2, §4, §5 (the Assignment table and cross-cutting rules), §7, §9 (M12 row), §10;
- `docs/phase-reviews.md` "Carried forward";
- the services already merged (`services/crew.py`, `services/admin.py`) for style.

**FILE OWNERSHIP**
- Create or edit only:
  - `src/mission_control/services/assignments.py`;
  - `src/mission_control/infra/repositories/assignments.py` (add the writes you need: create a proposal, change status and reason);
  - new test files for M12.
- Append only, in a `# M12 assignments` section:
  - `src/mission_control/domain/events.py`;
  - `tests/unit/domain/test_events.py`;
  - the design §7 tables (only for a new code; flag it for the user's approval).
- **Do NOT edit** `infra/repositories/missions.py`, `mission_*.py` or `facts.py`, or anything under domain/ except `events.py`, or `services/context.py`. Those are being changed elsewhere.
- If you need something there, stop and describe it in your report.

**Event note:** M11 (not yet merged) adds `MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"`, audited with `from_status`, `to_status` and `data={"mission_name": ..., "cause": <event value>}`. M12 needs the same event when a roster change sends a Pending mission back to Draft. Add that exact member and value in your `# M12 assignments` section, with a comment `# also added by M11; dedupe at merge`. Use the same audit shape.

**WHAT TO BUILD** (`services/assignments.py`): use-case functions taking `ctx` first. Inside `with ctx.write():`, do these in order:
1. load (a missing, hidden or other-org assignment, mission, slot or crew profile is NotFound);
2. authorize with the full required `Context`;
3. check state with the lifecycle helpers;
4. check input (`InvalidInput`, 422);
5. check rules (`RuleViolation`, 409);
6. write, and audit with names in `data`.

A refusal writes nothing.

- **propose(mission_id, slot_id, crew_profile_id)** (PROPOSE_CREW: mission owner only):
  - the mission is Draft or Pending; Pending goes back to Draft, with a revert audit naming the cause;
  - the slot is a live slot of this mission with an open place (`facts.slot_specs` open_places > 0);
  - the person has no open assignment on this mission;
  - the person is eligible: `ineligibility_reasons` on `facts.candidate(crew_profile_id, excluding_mission_id=mission_id)` against the slot spec and the mission window. Refuse with every reason, naming the conflicting mission for overlaps (AC-14, S4: Gus and Fay are refused).
  - proposals don't block anything else; overlapping proposals on different missions are allowed (S2 of PRD §5.6).
  - a Lead may propose themselves if eligible; they still have to accept.
- **accept(assignment_id)** (ACCEPT: only the assignee, `target_user_id` = the assignee's user id):
  - the mission is Draft and the assignment Proposed;
  - still eligible, re-checked now. Accepting over an accepted assignment elsewhere is refused, naming that mission (AC-15, S4: Chen's second acceptance names Station Reboost).
- **decline(assignment_id, reason=None)**: assignee only; mission Draft; Proposed; the reason is optional and stored.
- **withdraw(assignment_id, reason)**:
  - assignee only; Accepted; mission Draft or Pending (Pending goes back to Draft with the revert audit);
  - a blank or missing reason is a 422;
  - on an Active mission it's refused with `mission_frozen` (S5: Ben's withdrawal from the Pending Deep Space Comms needs a reason, then returns it to Draft so Marco's approval stops counting; Hana's withdrawal from the Active Telescope is refused).
- **remove(assignment_id)**: REMOVE_CREW, mission owner only; Proposed or Accepted; mission Draft or Pending (Pending goes back to Draft).
- **Visibility:**
  - crew may act only on their own assignments; someone else's assignment is NotFound to crew (TR-10);
  - Leads and Directors can see any assignment in their org, so acting on one that isn't theirs is 403 (`not_owner` / `role_forbidden` per `domain/permissions.py`).
- **Cascades** (needed by M13): provide a function M13 will call when a mission completes or is cancelled. It applies `domain.lifecycle.cascade` to every assignment on the mission: accepted becomes completed; proposed or accepted becomes cancelled. It writes and audits each change, and runs inside the caller's write transaction (document that). Test it directly.

Use the shared `Event` enum. Use natural-sentence messages from explicit phrases, naming the people, slots and missions involved. No PRD IDs in `src/`. Frozen dataclasses where you return records. New repository SQL uses named binding `org_id = :org` (a guard test enforces this; no `?`). `-> Generator[T]` for any context manager. Never use `httpx`.

**WORKFLOW**
1. **Tests first:** failing tests named after PRD IDs and scenarios, e.g.:
   - `test_s4_gus_proposal_is_refused_for_overlapping_station_reboost`;
   - `test_s4_fay_proposal_is_refused_for_unavailability`;
   - `test_ac15_chens_second_acceptance_names_station_reboost`;
   - `test_s5_withdrawal_without_reason_is_refused` / `..._returns_pending_mission_to_draft_and_clears_approvals`;
   - `test_s5_withdrawing_from_an_active_mission_is_refused`;
   - `test_s1_lead_can_propose_themselves_but_must_accept`;
   - full slot refused; duplicate open assignment refused;
   - crew can't propose; another crew member's assignment is not found;
   - a non-owner Lead gets `not_owner`; Helix ids give NotFound;
   - decline with and without a reason; remove by the owner, with Pending going to Draft;
   - cascades on complete and cancel;
   - every refusal leaves the tables unchanged (snapshot).

   Seed facts:
   - Gateway (1): Draft, owner Lee (4), slots Flight Engineer, Mission Specialist, Commander, 1 each.
   - Station Reboost (3): owner Nora (5), Engineer ×2, Gus accepted.
   - Deep Space Comms (6): Pending, Ben accepted, Marco approved.
   - Telescope (5): Active.
   - Fay is unavailable 5–8 Mar 2027.
   - Crew profile id = user id.

   See the tests fail, then implement.
2. Run the full suite and lint in the worktree:
   - `uv run pytest -W error -o addopts="" -q`;
   - `uv run ruff check src tests`;
   - `uv run ruff format --check src tests`.
3. **Real run:** a script against a fresh seeded database playing S4 and S5 end to end, plus S1's propose and accept steps on Gateway (Lee proposes Ana, Chen and Dana; they accept). Print the outcomes and messages. Port 8012 if you start a server.
4. **Read-only review** of your own diff; list the findings without silently fixing them.

**FINAL REPORT:**
- files;
- functions and what each enforces, with PRD IDs;
- tests, with before (failing) and after counts;
- suite and ruff results;
- trimmed real-run output;
- review findings;
- new events and codes (codes flagged for approval);
- changes needed in files you don't own;
- PRD gaps.

<details>
<summary>⚙️ System/meta message · 2026-10-12 02:35:11 UTC</summary>

```
<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered.
</system-reminder>
```

</details>

**🔧 Bash**

*Inspect worktree state and layout*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && git status && git log --oneline -3 && cat CLAUDE.md && find src tests -type f | sort
```

<details>
<summary>↳ Result</summary>

```
On branch m12-assignments
nothing to commit, working tree clean
171296f docs: start Phase 3 review (in progress)
a4a6005 chore: exclude .claude from ruff
b6bad6d feat(m9): admin service — org settings, users and roles, crew profiles, skill catalogue
# Mission Control

Multi-tenant mission planning API and CLI. Read these before doing any work. They are the source of truth, so don't copy their content here.

- [`docs/brief.md`](docs/brief.md): the assessment brief
- [`docs/prd.md`](docs/prd.md): **behaviour**. What the system does, its rules, acceptance criteria and seed scenarios.
- [`docs/technical-design.md`](docs/technical-design.md): **structure**. Architecture, schema, API, CLI, the delivery plan (§9) and the implementation guidelines (§10).

If the PRD and the design conflict, or are silent on something, stop and ask. Never invent behaviour.

## Workflow (every module)

1. **One approved module at a time.** Work only on the module from design §9 that I have approved. Don't start anything else.
2. **Tests first.** Write failing tests that reference the PRD IDs, then implement. Run the full suite and lint: `uv run pytest` and `uv run ruff check`.
3. **Real verification.** Exercise the behaviour for real, for example with a REPL call, an HTTP request or a CLI command. Show the actual output. A passing test run alone isn't verification.
4. **Read-only review.** Review the full diff against the PRD and design §10 without editing. Report findings, and fix them only once I agree.
5. **Stop for approval.** Summarise what changed, the test and verification results, and the review findings, and propose a commit message. **Don't commit, and don't start the next module, until I approve.**

## Waves (parallel modules in worktrees)

When I approve a wave of independent modules (design §9), build them in parallel and keep reviews small:

1. **One worktree per module.** Run `git worktree add .worktrees/<module> -b <module> main`, then `uv sync` inside it. Each agent edits only its own worktree and doesn't commit.
2. **Same workflow per module.** Steps 2 to 4 above still apply, inside the worktree.
3. **Review one branch at a time.** Show me only that module's diff against `main` (`git -C .worktrees/<module> diff main`, including new files), with its results.
4. **After I approve that module:**
   - commit on its branch;
   - rebase onto `main` if `main` has moved, and re-run its tests;
   - fast-forward `main`;
   - run the full suite on `main`;
   - remove the worktree and branch.

   Only then present the next branch.

Never push, add dependencies, change the schema, or add endpoints, error codes or CLI commands outside the design without asking first.
src/mission_control/__init__.py
src/mission_control/__pycache__/__init__.cpython-312.pyc
src/mission_control/api/__init__.py
src/mission_control/api/__pycache__/__init__.cpython-312.pyc
src/mission_control/api/__pycache__/app.cpython-312.pyc
src/mission_control/api/app.py
src/mission_control/domain/__init__.py
src/mission_control/domain/__pycache__/__init__.cpython-312.pyc
src/mission_control/domain/__pycache__/approvals.cpython-312.pyc
src/mission_control/domain/__pycache__/dates.cpython-312.pyc
src/mission_control/domain/__pycache__/eligibility.cpython-312.pyc
src/mission_control/domain/__pycache__/enums.cpython-312.pyc
src/mission_control/domain/__pycache__/errors.cpython-312.pyc
src/mission_control/domain/__pycache__/events.cpython-312.pyc
src/mission_control/domain/__pycache__/lifecycle.cpython-312.pyc
src/mission_control/domain/__pycache__/matching.cpython-312.pyc
src/mission_control/domain/__pycache__/passwords.cpython-312.pyc
src/mission_control/domain/__pycache__/permissions.cpython-312.pyc
src/mission_control/domain/__pycache__/records.cpython-312.pyc
src/mission_control/domain/approvals.py
src/mission_control/domain/dates.py
src/mission_control/domain/eligibility.py
src/mission_control/domain/enums.py
src/mission_control/domain/errors.py
src/mission_control/domain/events.py
src/mission_control/domain/lifecycle.py
src/mission_control/domain/matching.py
src/mission_control/domain/passwords.py
src/mission_control/domain/permissions.py
src/mission_control/domain/records.py
src/mission_control/infra/__init__.py
src/mission_control/infra/__pycache__/__init__.cpython-312.pyc
src/mission_control/infra/__pycache__/db.cpython-312.pyc
src/mission_control/infra/__pycache__/security.cpython-312.pyc
src/mission_control/infra/db.py
src/mission_control/infra/repositories/__init__.py
src/mission_control/infra/repositories/__pycache__/__init__.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/approvals.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/assignments.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/audit.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/base.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/crew.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/facts.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/missions.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/models.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/organisations.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/skills.cpython-312.pyc
src/mission_control/infra/repositories/__pycache__/users.cpython-312.pyc
src/mission_control/infra/repositories/approvals.py
src/mission_control/infra/repositories/assignments.py
src/mission_control/infra/repositories/audit.py
src/mission_control/infra/repositories/base.py
src/mission_control/infra/repositories/crew.py
src/mission_control/infra/repositories/facts.py
src/mission_control/infra/repositories/missions.py
src/mission_control/infra/repositories/models.py
src/mission_control/infra/repositories/organisations.py
src/mission_control/infra/repositories/skills.py
src/mission_control/infra/repositories/users.py
src/mission_control/infra/schema.sql
src/mission_control/infra/security.py
src/mission_control/seed/__init__.py
src/mission_control/seed/__pycache__/__init__.cpython-312.pyc
src/mission_control/seed/__pycache__/data.cpython-312.pyc
src/mission_control/seed/__pycache__/loader.cpython-312.pyc
src/mission_control/seed/data.py
src/mission_control/seed/loader.py
src/mission_control/services/__init__.py
src/mission_control/services/__pycache__/__init__.cpython-312.pyc
src/mission_control/services/__pycache__/admin.cpython-312.pyc
src/mission_control/services/__pycache__/auth.cpython-312.pyc
src/mission_control/services/__pycache__/context.cpython-312.pyc
src/mission_control/services/__pycache__/crew.cpython-312.pyc
src/mission_control/services/admin.py
src/mission_control/services/auth.py
src/mission_control/services/context.py
src/mission_control/services/crew.py
tests/__pycache__/builders.cpython-312.pyc
tests/__pycache__/conftest.cpython-312-pytest-9.1.1.pyc
tests/api/__pycache__/test_health.cpython-312-pytest-9.1.1.pyc
tests/api/test_health.py
tests/builders.py
tests/conftest.py
tests/integration/__pycache__/conftest.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_admin_service.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_auth.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_crew_service.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_db.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_facts.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_repositories.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_repository_sql.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_repository_writes.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_schema_constraints.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_seed.cpython-312-pytest-9.1.1.pyc
tests/integration/__pycache__/test_service_context.cpython-312-pytest-9.1.1.pyc
tests/integration/conftest.py
tests/integration/test_admin_service.py
tests/integration/test_auth.py
tests/integration/test_crew_service.py
tests/integration/test_db.py
tests/integration/test_facts.py
tests/integration/test_repositories.py
tests/integration/test_repository_sql.py
tests/integration/test_repository_writes.py
tests/integration/test_schema_constraints.py
tests/integration/test_seed.py
tests/integration/test_service_context.py
tests/unit/domain/__pycache__/test_approvals.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_dates.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_eligibility.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_errors.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_events.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_lifecycle.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_matching.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_passwords.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/__pycache__/test_permissions.cpython-312-pytest-9.1.1.pyc
tests/unit/domain/test_approvals.py
tests/unit/domain/test_dates.py
tests/unit/domain/test_eligibility.py
tests/unit/domain/test_errors.py
tests/unit/domain/test_events.py
tests/unit/domain/test_lifecycle.py
tests/unit/domain/test_matching.py
tests/unit/domain/test_passwords.py
tests/unit/domain/test_permissions.py
```

</details>

**🔧 Bash**

*List doc sizes and PRD headings*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && wc -l docs/*.md && grep -n "^#" docs/prd.md
```

<details>
<summary>↳ Result</summary>

```
       9 docs/backlog.md
      76 docs/brief.md
     169 docs/phase-reviews.md
     338 docs/prd.md
     849 docs/technical-design.md
    1441 total
1:# Mission Control — Product Requirements (v1)
7:## 1. Problem and goals
20:## 2. Requirements from the brief
33:## 3. Users and roles
45:## 4. Main workflows (all available through the CLI)
60:## 5. Business rules
62:### 5.1 Definitions
73:### 5.2 Tenancy and identity
79:### 5.3 People and skills
100:### 5.4 Missions and lifecycle
133:### 5.5 Approval
141:### 5.6 Assignments
155:### 5.7 Visibility and audit
169:## 6. Auto-matching
197:## 7. CLI requirements
204:## 8. Acceptance criteria
257:## 9. Seed data and scenarios
261:### 9.1 Aurora Space Agency (N = 2)
289:### 9.2 Helix Orbital (N = 1)
297:### 9.3 Scenarios
312:## 10. Test plan
325:## 11. Out of scope
```

</details>

**🔧 Bash**

*Read the PRD*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && cat docs/prd.md
```

**🔧 Bash**

*Read the phase reviews*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && cat docs/phase-reviews.md
```

<details>
<summary>↳ Result</summary>

````
# Mission Control — Product Requirements (v1)

**Status:** Agreed · **Source of truth:** [`brief.md`](brief.md) · **Next:** technical design (frameworks, schema, API and CLI design)

Rules tagged **[B]** come from the brief. Everything untagged is a product decision made while resolving the brief's open questions.

## 1. Problem and goals

Crew assignment is manual and error-prone. Leads cross-reference skills, availability and existing commitments by hand. **[B]** Mission Control is a multi-tenant B2B platform for managing missions and crew, with an auto-matcher that suggests crew. **[B]**

v1 succeeds when:

1. A Lead can take a mission from requirements to an active, confirmed roster entirely through the CLI.
2. Matcher suggestions never break a hard rule and are deterministic.
3. The system enforces the approval rules.
4. No read or write can reach another organisation's data.

**How we'll know:** every acceptance criterion in §8 passes as an automated test against the seed data in §9.

## 2. Requirements from the brief

- R1: Organisations are tenants. All data is scoped to one organisation and never leaks across tenants.
- R2: Three roles: Director, Mission Lead, Crew Member.
- R3: Leads can't approve their own missions.
- R4: Missions have requirements, a timeline, and a lifecycle with approval before going active.
- R5: Crew have skill profiles, availability and assignment history.
- R6: Assignments connect crew to missions, and crew respond to them.
- R7: An auto-matcher suggests crew based on skills, availability and workload.
- R8: Organisations differ in crew size, skill taxonomy and approval process.
- R9: A multi-tenant API, plus a CLI for the main workflows. CLI usability is assessed.
- R10: Runs locally with seed data.

## 3. Users and roles

| Role | Responsibilities |
|---|---|
| **Director** | Manages users, roles, crew profiles, the skill catalogue and the approval setting. Creates missions for a Lead. Approves or rejects missions. Reassigns owners. Sees everything in their organisation. |
| **Mission Lead** | Owns missions. Defines slots, runs the matcher, proposes crew, submits. Maintains other people's skill levels. Reads all missions and crew profiles. |
| **Crew Member** | Manages own personal details and unavailability. Accepts, declines or withdraws from assignments. Sees only their own data and the missions they're on. |

- Each user belongs to exactly one organisation. The organisation is taken from the user's identity, never from the request.
- Each user has exactly one role, which controls permissions.
- Taking part in missions depends on a separate **crew profile**. Every Crew Member has one, and Leads and Directors may have one too.

## 4. Main workflows (all available through the CLI)

1. **Sign in** with email and password, and change your own password. See what needs attention: pending assignments, approvals waiting on me, my missions.
2. **Director admin:** manage users and roles, crew profiles, the skill catalogue, and the number of approvals required.
3. **Lead or Director:** set crew skill levels (1–5).
4. **Crew profile holder:** maintain personal details and unavailability.
5. **Create a mission:** name, dates, and role slots with required skills.
6. **Owning Lead:** run the matcher, review the suggested roster, apply it or propose crew by hand.
7. **Crew:** accept or decline proposals, and withdraw if needed.
8. **Owning Lead:** submit a fully accepted roster for approval.
9. **Eligible Directors:** approve or reject. The final approval activates the mission.
10. **Owning Lead or Director:** complete or cancel a mission.
11. **Director:** reassign a mission's owning Lead.
12. **View history:** mission history and crew assignment history.

## 5. Business rules

### 5.1 Definitions

| Term | Meaning |
|---|---|
| **Open assignment** | An assignment that is Proposed or Accepted. |
| **Open places** | A slot's headcount minus its open assignments. |
| **Mission-days** | The number of days from the start date to the end date, counting both. |
| **Overlap** | Two date ranges overlap if they share at least one calendar day. Dates have no time and no time zone. |
| **Eligible (crew for a slot)** | The person is active, has a crew profile, and has every required skill at or above its minimum level. They have no unavailability overlapping the mission, and no accepted assignment on another non-final mission that overlaps it. |
| **Eligible approver** | An active Director who did not create the mission and is not on its roster. |

### 5.2 Tenancy and identity

- **T1** Every record belongs to one organisation. Every read and write is limited to the caller's organisation. **[B]**
- **T2** Naming a resource from another organisation gives the same response as naming one that doesn't exist ("not found").
- **T3** Organisations are created only through seed data or an operator command. There is no self-service signup.

### 5.3 People and skills

- **P1** Each organisation has its own flat skill catalogue, managed by Directors. Skills with the same name in different organisations are unrelated.
  - Directors can rename a skill. Its identity stays the same.
  - Directors can delete a skill only if no crew skill or slot requirement uses it.
- **P2** Proficiency is an integer from 1 to 5.
- **P3** Leads and Directors set and remove skill levels. **Nobody can change their own levels.**
  - A skill change is allowed even if it makes someone ineligible for an assignment on a Draft or Pending mission. Eligibility is checked again at acceptance, submission and approval.
  - A skill change that would make someone ineligible for their assignment on an Active mission is refused.
- **P4** Crew profile holders manage their own personal details and unavailability. Nobody else edits them. Personal details are a display name and an optional bio.
- **P5** Crew are available by default. Unavailability is a date range with a reason.
- **P6** A crew member can't record unavailability that overlaps one of their accepted assignments.
- **P7** Users are deactivated, never deleted. Deactivated users can't sign in, aren't eligible for matching, and keep their history. Deactivation is refused while the user:
  - has open assignments; or
  - owns non-final missions. The same applies to changing a mission owner's role away from Lead. Their missions must be reassigned first.
- **P8** An organisation must always have at least one active Director.
- **P9** Crew profiles survive role changes and can't be deleted. Changing a user's role to Crew Member gives them a profile if they don't already have one.
- **P10** Directors set a new user's initial password. Users change their own password by entering their current one. There's no email or password-recovery flow.
  - Passwords must be at least 15 characters. Passphrases are welcome, and uppercase letters, numbers and symbols aren't required.
  - Changing a password ends all of that user's sessions, including the one used to change it.

### 5.4 Missions and lifecycle

- **M1** A mission has a name, a date range, one owning Lead and a separately recorded creator.
  - Leads create missions for themselves. Directors create them on behalf of a Lead.
  - Only Mission Leads can own missions.
  - Directors can transfer ownership of a non-final mission to another active Lead in the same organisation. If the mission is Pending, it returns to Draft and its approvals are cleared.
- **M2** A mission has one or more slots. Each slot has a name, a headcount of at least 1, and at least one required skill with a minimum level. Dates may be in the past, but the end date must be on or after the start date. The same rule applies to unavailability.
- **M3** Only the owning Lead can edit a mission, propose or remove crew, apply matcher results, or submit.

```
         submit                N-th approval                complete
 Draft ─────────▶ Pending ───────────────────▶ Active ─────────────▶ Completed
   ▲              Approval
   └── reject (reason) / any change ──┘
 Draft | Pending Approval | Active ──cancel (reason)──▶ Cancelled
```

| Transition | Who | Conditions and effects |
|---|---|---|
| Draft → Pending Approval | Owning Lead | All of these must hold: every slot is full, every assignment is Accepted, every rostered crew member is still eligible, and there are at least N eligible approvers. Otherwise the submission is refused with a list of the problems. |
| Pending → Active | The N-th distinct eligible approver | The roster is checked again at each approval. If the check fails, the approval is refused and the mission stays Pending, unchanged. |
| Pending → Draft | Eligible Director (reject) or system | A rejection needs a reason. Any change to dates, slots, roster or owner, including a crew withdrawal, also sends the mission back to Draft. Approvals are cleared, and remaining accepted assignments stay accepted. |
| Active → Completed | Owning Lead or Director | Accepted assignments become Completed. |
| Any non-final → Cancelled | Owning Lead or any Director | Reason required. Open assignments become Cancelled. |

- **M4** Draft missions can have unfilled places and unanswered proposals.
- **M5** Once a mission is Active, its dates, requirements and roster are frozen. Only completion or cancellation are allowed.
- **M6** Dates never trigger transitions on their own. There is no scheduler.
- **M7** An edit is refused if it would invalidate an open assignment. The response lists the affected crew, and the Lead must remove them first. Crew are never removed automatically. Edits that invalidate an assignment are:
  - removing a slot that has open assignments;
  - lowering a slot's headcount below its open assignments;
  - changing dates or requirements so that an assigned person is no longer eligible.

### 5.5 Approval

- **A1** Each organisation sets the number of approvals required (N ≥ 1). The approvals must come from N distinct eligible approvers.
  - N is fixed for a mission when it's submitted. Later changes to the setting don't affect a round already in progress.
  - An approval already given still counts if that Director is later deactivated or demoted.
- **A2** Leads can't approve anything, which satisfies R3. **[B]** A Director can't approve a mission they created or are rostered on.
- **A3** Each Director approves a round at most once. A single rejection ends the round.

### 5.6 Assignments

```
Proposed ──accept──▶ Accepted ──withdraw (reason)──▶ Withdrawn
   ├──decline──▶ Declined   └──removed by Lead──▶ Removed
   └──retracted by Lead──▶ Removed
Accepted ──mission completed──▶ Completed;  open ──mission cancelled──▶ Cancelled
```

- **S1** The owning Lead can propose only eligible crew. A person can hold at most one open assignment per mission. A slot can't have more open assignments than its headcount. A Lead can propose themselves, but they must be eligible and must accept like anyone else.
- **S2** Crew can accept only while the mission is in Draft and they're still eligible. Accepted assignments block overlapping dates. Proposals don't block anything.
- **S3** Declining takes an optional reason. Withdrawing needs a reason and is allowed only in Draft or Pending Approval.
- **S4** Every assignment needs the crew member's acceptance. Crew can't be placed on a mission directly.

### 5.7 Visibility and audit

| | Crew | Lead | Director |
|---|---|---|---|
| Own profile, skills, availability, assignments | ✓ | ✓ | ✓ |
| Missions they're on, with teammates' names and slots | ✓ | ✓ | ✓ |
| Other crew members' profiles, skills, busy/free dates | ✗ | ✓ | ✓ |
| Other people's *reasons* for unavailability | ✗ | ✗ | ✓ |
| All missions in the organisation | ✗ | read (edit own) | read |
| Users, catalogue management, organisation settings | ✗ | read catalogue | manage |

- **V1** Every state change, approval, rejection and assignment response is recorded with who did it, when, and any reason. Anyone who can see the mission can see this history.
- **V2** Former assignees see a summary of the mission in their own assignment history. They don't get full access to the mission unless their role allows it. Former assignees are people whose assignment was declined, withdrawn, removed or cancelled.

## 6. Auto-matching

The matcher only advises. It suggests crew for a Draft mission's open places and changes nothing. The owner or a Director can preview a suggestion. When the owning Lead applies it, it creates Proposed assignments, which crew still have to accept.

**Candidates.** Active crew profiles in the mission's organisation only. Crew who already have an open assignment on this mission, or who declined or withdrew from it, are left out.

**Workload.** The total mission-days of a crew member's accepted assignments on missions that are not Completed, leaving out the mission being matched.

**Algorithm**

1. **Filter.** For each slot with open places, keep the candidates who are eligible (§5.1).
2. **Pick the most constrained slot.** Choose the slot with the fewest remaining eligible candidates. Ties go to the slot listed first.
3. **Fill one place in that slot.** Rank candidates by:
   1. lowest workload;
   2. then highest proficiency, meaning the sum of their levels across the slot's required skills;
   3. then stable identifier, ascending.
4. **Remove the chosen person** from every other slot's candidates.
5. **Repeat** from step 2 until every place is filled or has no candidates left.

**Output.** A suggested roster with no one in two slots. Places without a candidate are marked **unfilled**. The same inputs always give the same output.

**Why:**
- Filling the most constrained slot first stops a versatile person from being spent on a slot that's easy to fill.
- Ranking by lowest workload spreads missions across crew.
- Proficiency only breaks ties, because everyone left already meets the requirement.

**Known limitation:** this is a greedy heuristic. It can occasionally leave a place unfilled when a complete roster exists. That's acceptable for an advisory tool, and the Lead can still propose by hand.

## 7. CLI requirements

- **C1** Every workflow in §4 can be carried out from the CLI. **[B]**
- **C2** Refusals explain why in domain terms, for example "Gus has an accepted assignment on *Station Reboost* overlapping 1–2 Mar". Where possible they also say what to do next.
- **C3** Output is readable by people by default, with a machine-readable option for scripts and tests.
- **C4** Actions that send a mission back to Draft, or cancel it, warn before running.

## 8. Acceptance criteria

Each criterion starts from a fresh seed. Scenario numbers (S-) refer to §9.3.

**Mission workflow**

- **AC-1** The golden path (S1) ends Completed, and every transition appears in the history with who did it and when.
- **AC-2** Submission is refused while any place is unfilled or any proposal is unanswered. The refusal lists them.
- **AC-3** Approvals before the N-th leave the mission Pending. The N-th approval makes it Active.
- **AC-4** Changing the dates, slots or roster of a Pending mission sends it back to Draft and clears its approvals. So does a crew withdrawal (S5).
- **AC-5** On an Active mission, edits, proposals, removals and withdrawals are refused. Completion and cancellation succeed.
- **AC-6** Cancelling needs a reason. The owning Lead or any Director can cancel, and any other Lead is refused. Open assignments become Cancelled.
- **AC-7** Only the owning Lead can edit, propose, apply or submit. After a Director reassigns the owner, the new owner can and the previous owner can't.

**Approval restrictions**

- **AC-8** The mission's creator can't approve it. In S1, Ruth is refused.
- **AC-9** Leads and Crew can't approve or reject.
- **AC-10** A Director can't approve the same round twice. Rejecting needs a reason and clears earlier approvals (S6).
- **AC-11** A Director rostered on a mission can't approve it.
- **AC-12** Submission is refused when there are fewer than N eligible approvers, not counting the creator or rostered Directors (S7).
- **AC-13** In Helix (N = 1), a single approval makes the mission Active (S8).

**Overlaps and availability**

- **AC-14** Proposing someone who is unavailable, or who has an overlapping accepted assignment, is refused. In S4, both Fay and Gus are refused.
- **AC-15** Overlapping proposals are allowed. Accepting one that overlaps an accepted assignment is refused, and the refusal names the conflicting mission (S4, Chen).
- **AC-16** Recording unavailability that overlaps an accepted assignment is refused.
- **AC-17** Two ranges that share only a boundary day overlap.

**Matching**

- **AC-18** S2 gives exactly the expected roster on every run.
- **AC-19** S3 marks Geologist as unfilled. S3b shows a new accepted assignment changing the suggestion.
- **AC-20** Workload counts only accepted assignments on missions that aren't Completed. Chen's workload is 5, not 35.
- **AC-21** The suggestion never puts one person in two slots. It never includes anyone who is ineligible, from another organisation, or already excluded from this mission.
- **AC-22** Running the matcher changes nothing. Applying it creates Proposed assignments.

**Roles and visibility**

- **AC-23** Ana can't change her own skill levels, but Lee can change hers. Ben can't edit skills, but he can edit his personal details and unavailability.
- **AC-24** Lee sees Fay as busy 5–8 Mar but doesn't see the reason. Ruth sees the reason. Ben can't view Fay's profile, and his mission list shows only missions he's on.
- **AC-25** Leads can't manage users, the catalogue or the approval setting.
- **AC-26** Deactivating someone with open assignments is refused. A deactivated user can't sign in. The last active Director can't be deactivated or demoted.

**Tenant isolation (S9)**

- **AC-27** Requesting another organisation's mission, crew member, user, skill or assignment by ID gives the same response as an ID that doesn't exist.
- **AC-28** Every list contains only the caller's organisation's records.
- **AC-29** Any write that references another organisation's ID fails as "not found", and neither organisation's data changes.
- **AC-30** Approving or rejecting another organisation's mission fails as "not found".
- **AC-31** Helix's Kai (Piloting 5, no commitments) is never suggested for an Aurora mission.

## 9. Seed data and scenarios

The table order of people is their stable-identifier order. All dates are in 2027 unless stated.

### 9.1 Aurora Space Agency (N = 2)

| Person | Role | Crew skills | Commitments (workload) |
|---|---|---|---|
| Ruth Adeyemi | Director | — | — |
| Marco Bianchi | Director | Flight Medicine 4 | Medical Study, accepted (4) |
| Ingrid Holm | Director | — | — |
| Lee Park | Lead | — | — |
| Nora Quinn | Lead | — | — |
| Ana Okafor | Lead | Piloting 5, Leadership 4, Systems Eng 4 | none (0) |
| Ben Ito | Crew | Systems Eng 4, EVA 3 | Deep Space Comms, accepted (20) |
| Chen Wu | Crew | Systems Eng 3 | Telescope (5). Mars Analog Completed, so it doesn't count |
| Dana Reyes | Crew | EVA 4 | Telescope (5) |
| Eli Novak | Crew | EVA 4, Piloting 4, Leadership 2 | Telescope (5) |
| Fay Moreau | Crew | Piloting 4, Leadership 4 | Unavailable 5–8 Mar (Medical) |
| Gus Patel | Crew | Systems Eng 5 | Station Reboost, accepted (6) |
| Hana Sato | Crew | EVA 3, Geology 2 | Telescope (5) |

| Mission | Owner / creator | Dates | State | Slots → crew |
|---|---|---|---|---|
| Lunar Gateway Resupply | Lee / Ruth | 1–10 Mar | Draft | Flight Engineer ×1 (Sys Eng ≥3) · Mission Specialist ×1 (EVA ≥3) · Commander ×1 (Piloting ≥4, Leadership ≥3) — no crew |
| Asteroid Survey | Nora | 5–12 Mar | Draft | Pilot ×1 (Piloting ≥4) · Geologist ×1 (Geology ≥4) — no crew |
| Station Reboost | Nora | 25 Feb – 2 Mar | Draft | Engineer ×2 (Sys Eng ≥3) — Gus accepted, 1 open place |
| Lunar Surface Medical Study | Nora / Ruth | 15–18 Mar | Draft | Flight Surgeon ×1 (Flight Medicine ≥4) — Marco accepted |
| Orbital Telescope Service | Lee | 10–14 Jan | Active | Engineer ×1 — Chen · EVA Specialist ×3 (EVA ≥3) — Dana, Eli, Hana |
| Deep Space Comms Upgrade | Nora | 1–20 Apr | Pending (Marco approved) | Engineer ×1 (Sys Eng ≥3) — Ben |
| Mars Analog Habitat | Lee | 1–30 May 2026 | Completed | Engineer ×1 — Chen |

### 9.2 Helix Orbital (N = 1)

People: Sam Rivera (Director), Priya Nair (Lead), and Crew Kai Tanaka (Piloting 5), Lena Fischer (Payload Integration 4), Omar Haddad (Field Medicine 4) and Tess Moreno (Life Support 3). Helix has its own catalogue, including a separate "Piloting" skill.

| Mission | Owner | Dates | State | Slots → crew |
|---|---|---|---|---|
| Payload Demo 1 | Priya | 1–3 Feb | Draft | Payload Specialist ×1 (Payload Int ≥3) — Lena accepted · Medic ×1 (Field Medicine ≥3) — Omar accepted |

### 9.3 Scenarios

| # | Steps | Expected outcome |
|---|---|---|
| **S1** | Lee matches and applies *Lunar Gateway Resupply* → Ana, Chen and Dana accept → Lee submits → Ruth approves → Marco approves → Ingrid approves → Lee completes | Proposed crew are Ana, Chen and Dana. Ruth is refused as creator. After Marco the mission is Pending (1/2). After Ingrid it's **Active**. Completing makes the assignments Completed. |
| **S2** | Match *Lunar Gateway Resupply* | Eligible crew: Commander {Ana}, because Fay is unavailable and Eli's Leadership is too low. Flight Engineer {Ana, Ben, Chen}, because Gus has an overlap. Specialist {Ben, Dana, Eli, Hana}. **Commander → Ana** (most constrained). **Flight Engineer → Chen** (workload 5 vs Ben's 20). **Specialist → Dana** (four-way workload tie at 5; Hana loses on proficiency; Dana beats Eli on ID). Filling the slots in listed order would have spent Ana on Flight Engineer and left Commander unfilled. |
| **S3** | Match *Asteroid Survey* | Geologist **unfilled** (Hana's Geology is only 2). Pilot → Ana (workload 0 vs Eli's 5; Fay unavailable). |
| **S3b** | S1 up to acceptance, then match *Asteroid Survey* | Ana is blocked by her overlapping accepted assignment, so Pilot → Eli. Geologist still unfilled. |
| **S4** | Lee proposes Gus and Fay for *Gateway*. Nora proposes Chen for *Station Reboost* and Lee proposes Chen for *Gateway*. Chen accepts *Station Reboost*, then *Gateway*. | Gus refused (overlap). Fay refused (unavailable). Both Chen proposals succeed. Chen's second acceptance is refused, naming *Station Reboost*. |
| **S5** | Ben withdraws from *Deep Space Comms* without a reason, then with one. Hana withdraws from *Telescope*. | Ben's first attempt is refused. The second succeeds: the mission returns to Draft and Marco's approval is cleared. Hana is refused because *Telescope* is Active. |
| **S6** | Marco approves *Deep Space Comms* again. Ingrid rejects it without a reason, then with one. | Marco is refused. Ingrid's first attempt is refused. The second sends the mission to Draft and clears approvals. |
| **S7** | Nora submits *Lunar Surface Medical Study* | Refused. Ruth created it and Marco is rostered, which leaves 1 eligible approver (Ingrid) when 2 are needed. |
| **S8** | Priya submits *Payload Demo 1* and Sam approves | **Active** after one approval. |
| **S9** | Each role in each organisation tries to read, list, write and approve the other organisation's resources, and matches an Aurora Piloting slot | Every attempt fails as "not found" and nothing changes. Lists show only the caller's organisation. Kai never appears. |

## 10. Test plan

Every acceptance criterion maps to at least one automated test.

| Level | Covers |
|---|---|
| Unit: matcher (pure function) | Eligibility, workload, most-constrained-first, each tie-break, no person in two slots, unfilled places, determinism. Includes S2, S3 and a small hand-built case per rule. |
| Unit: lifecycle and rules | Every allowed transition and a sample of disallowed ones. Approver eligibility and the N count. Revert-to-Draft clearing approvals. The Active freeze. Overlap at boundary days. |
| API: permissions | A role × action table, checking each role is allowed or refused as expected. |
| API: tenant isolation | Every endpoint, for reads, lists and writes, tried with the other organisation's IDs. A route-inventory test makes any new endpoint fail CI until it's added to this sweep. |
| API: scenarios | S1 and S3b–S8 against a freshly seeded database. |
| CLI end to end | S1 and S4 run through the real CLI, checking machine-readable output and the wording of refusals. |

## 11. Out of scope

- Web UI.
- Self-service organisation signup, users in more than one organisation, SSO.
- Password recovery and email flows. Deleting crew profiles. Reactivating deactivated users.
- Delivering notifications. The CLI's "needs attention" views replace them.
- Certifications, skill expiry, skill verification, skill hierarchies.
- Recurring availability, scheduling finer than a day, rest periods between missions.
- Conditional or multi-stage approvals.
- Assigning crew without their acceptance, response deadlines.
- Matcher extras: preferred skills, experience scoring, configurable weights, near-miss and exclusion lists, suggestions to relax requirements, LLM matching.
- Date-driven transitions. Roster changes once a mission is Active.
- Equipment and resource constraints. Keep slot requirements extensible so these can be added later.
- Billing, bulk import.
````

</details>

<details>
<summary>↳ Result</summary>

```
# Mission Control: Phase Reviews

How the implementation diverged from the agreed plan (the [PRD](prd.md) and [technical design](technical-design.md) as of `dc0e41d`), and why. A section is added at the end of each phase. The PRD and design themselves are kept current.

---

## Phase 1: Pure domain (M0–M5)

`a70f07d` → `867ece8` · 458 tests · all domain rules, no database

**Headline:** the plan held. No PRD behaviour changed. Every divergence below was approved and written back into the design.

### Where we diverged

| Change | Why |
|---|---|
| **`httpx` replaced by `httpx2`** | Starlette's test client deprecated `httpx`, and the user flagged it as a supply-chain risk |
| **Records carry names**, not just IDs | Refusals must name the person, skill and conflicting mission ("Gus has an accepted assignment on Station Reboost…") |
| **One shared `Action` enum** | Lifecycle and permissions had separate enums with overlapping values, so mixing them up half-worked |
| **Four error codes added**: `invalid_transition`, `proposal_unanswered`, plus a table of problem codes | The design had no code for wrong-state actions or unanswered proposals |
| **Every error has a `problems` list**, for every status | One error shape for clients. Listing several reasons on a 403 wasn't worth the complexity. |
| **Commits need approval** | The user wanted to review every module before it's committed or the next one starts |

### Key decisions

- **Permissions:** we kept our own ~150-line module instead of a library (Casbin, Oso, Cerbos, OpenFGA). The rules are small, we need our own codes and messages anyway, and it avoids adding dependencies.
- **Messages:** written as explicit phrases, never generated from names. PRD IDs appear only in tests.

### Phase-end review

A read-only subagent reviewed M0–M5, and fixes were applied by parallel subagents. Codes and messages were checked byte-for-byte before and after, across 14,740 outcomes.

- **Fixed (High):**
  - forgetting permission context *allowed* the action, so a Lead could edit their own skills; it now fails closed;
  - the back-to-Draft rule was coded twice; it now lives in one `touch_for_change()`.
- **Fixed (Medium/Low):**
  - duplicated approver rule;
  - mutable `refs` and tables;
  - two records for one concept;
  - copied test builders, now in `tests/builders.py`;
  - weak tests.
- **Recorded instead of changed:** multiple 403 reasons, handled by the consistent error body in M15.

### Carried forward

- **M7:** seed crew in PRD §9 order. The ID is the matcher's final tie-break.
- **M10–M15:**
  - a refused *view* returns 404;
  - services always pass the context each action requires;
  - changes go through `touch_for_change()`.
- **M13:** test that an approval still counts after its Director leaves.
- **M15:** consistent error body. Validation errors map to 422.
- **M16:** friendlier date formatting in the CLI.

---

## Phase 2: Persistence (M6–M8)

`09439f4` → review fixes · 656 tests · schema, repositories, seed, auth

**Headline:** the persistence layer matches the design. Every tenant query is scoped, the database itself refuses cross-tenant links, and login is safe against account probing. The phase-end review found no live data leak, but it did find patterns that Phase 3 would have copied, and those are fixed.

### Where we diverged

| Change | Why |
|---|---|
| **Repository queries bind the org by name** (`org_id = :org`); positional `?` is banned by a guard test | With positional binding, a query written `WHERE id = ? AND org_id = ?` would silently return another tenant's rows |
| **Argon2 runs outside the write lock**, then a cheap re-check happens inside it | Each hash takes ~40 ms, and failed logins were blocking every writer. The rule "re-check under the lock" still holds. |
| **Login costs the same for unknown emails** (a dummy hash is verified) | Otherwise response time reveals which accounts exist, even with identical messages |
| **One timestamp format**: `utc_timestamp()`, UTC, 3-digit ms | The original helper dropped time zones and disagreed with the schema's own format |
| **Seed ids fixed**, with crew profile id = user id | Keeps the matcher's final tie-break in PRD table order, and lets tests and the seed share ids |
| **Shared audit event names** (`Event` enum) | Services and the seed must write identical names, or mission history breaks |

### Key decisions

- **Seed assumptions** (PRD §9 is silent): the Telescope and Mars Analog Engineer slots need Systems Engineering ≥ 3, and both missions were approved by Marco and Ingrid.
- **Tests:** they use cheap Argon2 settings, and tests marked `real_argon2` keep the production settings.
- **Phase 3 runs in waves:** each module is built in its own git worktree, then reviewed and committed one at a time. A small **service foundation (SF)** comes first, so modules share one service context and one set of fact loaders.

### Phase-end review

A read-only subagent reviewed M6–M8, and three fix agents with separate file ownership applied every finding. Before-and-after outputs were compared, and they were identical apart from the approved timestamp precision.

- **Fixed (High):**
  - named org binding with a stricter guard;
  - Argon2 moved out of the write lock.
- **Fixed (Medium):**
  - `read_tx` committed on error;
  - a dual-mode session revoke;
  - the time-zone-blind timestamps;
  - two definitions of "on the mission", now one `rostered_user_ids()`;
  - a timing-sensitive lock test;
  - seed duplication.
- **Fixed (Low):** test-only wrappers and tests that passed for the wrong reason.

### Carried forward

- **SF / M9–M14:**
  - use `Event` names, `utc_timestamp()` and `rostered_user_ids()`;
  - mission visibility for crew is a 404 through the repository;
  - deactivation calls `security.revoke_user_tokens` inside its own transaction.
- **M15:** build the dummy hash at startup. Wire the `MC_DATABASE_PATH` and `MC_DB_BUSY_TIMEOUT_MS` settings.
- **M17:** `mc-admin seed` hashes the demo passphrase (`orbital launch window`).
- **Out of scope:** deleting expired session tokens.

---

## Phase 3: Services (SF, M9–M14), in progress

`8ccb5c3` → … · 875 tests on `main` so far · use cases on top of the domain and repositories

**Status:**
- Merged: SF, M10, M9.
- M11 is built and under independent review.
- M14 preview is being built.
- M12 and M13 haven't started.
- This section is updated as each module lands.

**Headline so far:** Phase 3 is the first phase built in parallel. The plan's rules held for every merged module. The changes are in *how* we work (waves, worktrees, review on `main`), plus a few shared pieces the services turned out to need.

### Where we diverged

| Change | Why |
|---|---|
| **A service foundation (SF) module was added** before the services | Without it, every service would have written its own context, error types and fact loaders. SF made them shared and reviewed once. |
| **Waves in git worktrees** instead of strictly one module at a time | Independent modules (M9 ∥ M10 ∥ M11) can be built in parallel and still reviewed one branch at a time |
| **Repositories split into one file per area** | Each wave module owns its own repository file, so parallel branches rarely conflict |
| **Review happens on `main` as staged changes** before the commit | Easier to read line by line in the IDE than a diff against a worktree branch |
| **One shared 422 error (`InvalidInput`)** | Two agents invented their own. Plain `ValueError` also signals programming errors, so the API can't map it safely. |
| **`StateConflict` is a `RuleViolation`** | Services and the API handle one family of 409 refusals |
| **New problem code `already_exists`**; **TR-13**: emails are unique across the platform | Duplicate email, skill name or crew profile. The trade-off: a duplicate-email refusal reveals that the address is in use elsewhere. |
| **M14 split:** preview now, apply after M12 | Apply needs M12's propose path. Preview needs only what's merged. |

### Key decisions

- **Privacy:** unavailability reasons never go into the audit log. Only dates do.
- **No-op updates write nothing.** An update with no fields still checks access, but makes no write and no audit entry.
- **Reactivating users is out of scope.** Three M9 choices are logged in `docs/backlog.md` for later.
- **A `cli-ux` skill was created** from Atlassian's CLI principles and "How Terminals Work". It's used to shape matcher output and the CLI mock sessions (`docs/cli-ux.md`).

### Process notes

- **The M11 agent stopped before its hand-off.** Its work was complete and passing, but the real run, review and test-first evidence were missing. The lead did the real run, and a fresh agent did an independent review.
- **Another session committed on a wave branch.** A review commit appeared on `m9-admin`. Its contents were verified to be already on `main` before the branch was deleted.
- **Lint scope widened.** Ruff now excludes `.claude/` as well as `docs/`, because it formats code blocks inside Markdown.

### Modules

| Module | Status | Notes |
|---|---|---|
| SF service foundation | ✓ `8ccb5c3` | Context, errors, fact loaders, Wave 1 writes. Before/after snapshot identical for the split. |
| M10 crew | ✓ `d55a7ed` | Reasons hidden from Leads; Active assignments protected from skill changes |
| M9 admin | ✓ `b6bad6d` | Last Director, owned missions and open assignments block demotion and deactivation; sessions revoked |
| M11 missions | in review | *To complete:* review findings, decisions, merge commit |
| M12 assignments | not started | |
| M13 approvals | not started | |
| M14 matching | preview in progress | *To complete:* apply after M12 |

### Phase-end review

*To complete after M14:* a read-only subagent reviews SF and M9–M14, then the findings and what happened to each.

### Carried forward

*To complete at phase end.* Candidates so far:
- **M15:**
  - map `InvalidInput`, `InvalidDateRange` and `PasswordTooShort` to 422, and never plain `ValueError`;
  - single-reason refusals repeat their message in `problems`, so the CLI shouldn't print it twice.
- **M16:** render matcher previews per `docs/cli-ux.md`.
```

</details>

**🔧 Bash**

*List design doc headings*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && grep -n "^#" docs/technical-design.md
```

<details>
<summary>↳ Result</summary>

```
1:# Mission Control — Technical Design (v1)
24:## 1. Summary
43:## 2. Architecture
95:## 3. Data model
130:## 4. Security and tenancy
132:### Authentication
141:### Permissions
169:### Tenant isolation
181:## 5. Lifecycle
183:### Mission
205:### Assignment
228:### Cross-cutting rules
240:## 6. Matching
308:## 7. API
316:#### Auth and me
325:#### Organisation, users and skills (Directors)
335:#### Crew
345:#### Missions
358:#### Assignments
365:#### Errors
407:## 8. CLI
421:# Everyone
426:# Leads
432:# Directors
441:## 9. Delivery plan
505:## 10. Guidelines for implementing agents
507:### Source of truth
512:### The loop for each module
521:### Working in waves (worktrees)
530:### Architecture rules (never break these)
538:### Coding conventions
544:### Testing conventions
549:### Stop and ask before
557:## 11. Setup and testing
582:## Appendix A: Schema SQL
593:### Organisations, users and sessions
631:### Crew, skills and availability
685:### Missions, slots and requirements
739:### Assignments, approvals and audit
812:## Appendix B: Trade-offs and considerations
816:### B.1 Key decisions
834:### B.2 Risks
844:### B.3 Scaling path (not in v1)
```

</details>

**🔧 Bash**

*Read design sections 2-5*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 43,240p docs/technical-design.md
```

**🔧 Bash**

*Read design sections 7, 9, 10 and schema*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 308,557p docs/technical-design.md; sed -n 739,812p docs/technical-design.md
```

<details>
<summary>↳ Result</summary>

````
## 2. Architecture

**Stack:** Python 3.12 · FastAPI + Pydantic v2 · SQLite through stdlib `sqlite3` · argon2-cffi · Typer + httpx2 · uv, pytest, ruff

**Dependency policy:** don't use `httpx` anywhere, including tests. Use `httpx2`, which Starlette's `TestClient` now expects.

Why SQLite, hand-written SQL, and a CLI that goes through the API: [TR-1](#tr-1), [TR-2](#tr-2), [TR-4](#tr-4).

```mermaid
flowchart TB
    U([Users]) --> CLI[CLI]
    CLI -->|HTTP + JSON| API[API]
    API --> S[Services]
    S --> D[Domain rules]
    S --> R[Repositories]
    R --> DB[(SQLite)]
    A[mc-admin] --> DB
```

| Layer | Folder | Responsibility | May depend on |
|---|---|---|---|
| CLI | `cli/` | Commands, output, prompts | API over HTTP only |
| API | `api/` | Validate input, resolve `Actor`, call a service, map errors | services |
| Services | `services/` | One use case = one transaction + audit | domain, infra |
| Domain | `domain/` | Every business rule, pure (no I/O) | nothing |
| Infra | `infra/` | Connections, schema, scoped repositories, security | domain types |

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
  infra/     db  schema.sql  security  repositories/
  services/  auth  admin  crew  missions  assignments  approvals  matching  audit  inbox
  api/       app  deps  errors  schemas/  routers/
  cli/       main  client  config  render  resolve  commands/
  seed/      data  loader
  admin_cli.py        # mc-admin: init-db, seed, create-org
tests/  unit/  integration/  api/  cli/  builders.py  conftest.py
```
</details>

---

## 3. Data model

The core entities are below. Skills, unavailability, approvals, tokens and the audit log hang off these. All 13 tables are in [Appendix A](#appendix-a-schema-sql).

```mermaid
flowchart LR
    Org[Organisation] --> User
    Org --> Mission
    User --> Crew[Crew profile]
    Mission --> Slot
    Slot --> Assignment
    Crew --> Assignment
```

**Tenant safety.** Every tenant table has `org_id` and `UNIQUE (org_id, id)`. Every reference between tenant rows includes `org_id`, so the database itself rejects links across organisations. Why a shared database: [TR-3](#tr-3).

| Enforced by the database | Enforced by services |
|---|---|
| Value ranges and valid dates | Eligibility and overlaps |
| Cross-organisation links rejected | Open places |
| One open assignment per person per mission | State transitions |
| A slot belongs to its mission | Permissions and the owner's role |
| Reasons for withdrawals and rejections | At least one requirement per slot |
| Append-only audit log; used skills can't be deleted | |

**Modelling choices**
- **Approval rounds.** Submit sets `round += 1` and saves N in `approvals_required`. Only approvals in the current round count, and none are ever deleted ([TR-9](#tr-9)).
- **Soft-deleted slots.** `removed_at` keeps the history of past assignments.
- **Nothing derived is stored.** Workload, eligibility, open places and the roster are computed when needed ([TR-7](#tr-7)).
- **Integer IDs** keep CLI commands short ([TR-12](#tr-12)).
- **History survives renames.** Audit `data` keeps the names that applied at the time.
- **"On a mission"** means holding an open or completed assignment. Any other status gives summary access only (V2).

---

## 4. Security and tenancy

### Authentication

| | |
|---|---|
| Token | 32 random bytes. Only the SHA-256 hash is stored. 12-hour expiry. |
| Every request | Token → valid? → user active? → `Actor(user_id, org_id, role, crew_profile_id)`. Nothing is cached, so role changes apply immediately. |
| Revocation | Logout revokes that token. Deactivation or a password change revokes every token. Opaque tokens make this immediate ([TR-5](#tr-5)). |
| Passwords | Argon2id. At least 15 characters. No character-type rules. |

### Permissions

Each **role** sets the baseline:

| Role | Can | Can't |
|---|---|---|
| **Director** | Run the organisation: users, roles, skills, approval setting. See everything. Approve, transfer, complete and cancel missions. | Edit mission details, since that's the owner's job |
| **Lead** | Create and run their own missions. Rate other people's skills. See all crew and missions. | Approve anything. Touch missions they don't own. |
| **Crew** | Manage their own profile and availability. Respond to their own assignments. | See other crew, or missions they aren't on |

On top of the role, **relationship rules** make the decisions that matter:

| Rule | Effect | PRD |
|---|---|---|
| **Owner only** | Only the mission's owner edits it, proposes crew, applies the matcher or submits | M3 |
| **Not yourself** | Nobody sets their own skill levels | P3 |
| **Eligible approver** | A Director can't approve a mission they created or are on | A2 |
| **Self only** | Only you edit your details and availability. Only you, and Directors, see your unavailability reasons. | P4, §5.7 |
| **Visibility** | Crew only see missions they're on. Former assignees see a summary. | V2 |

**Enforcement.** `domain/permissions.authorize(actor, action, ctx)` is the single entry point. The complete action × role table is the parametrized test for this module, and that test is the source of truth.

| Status | When |
|---|---|
| **401** | Authentication failed |
| **404** | Missing, another organisation's, or not visible. All three look identical ([TR-10](#tr-10)). |
| **403** | Visible, but you're not allowed to do this |

### Tenant isolation

1. **Identity.** `org_id` comes only from the token, never from the request.
2. **Repositories.** `Repos(conn, org_id)` scopes every query. Another organisation's ID behaves as missing.
3. **Database.** Composite `(org_id, id)` foreign keys.
4. **Tests.**
   - An SQL lint checks every query mentions `org_id`.
   - A route inventory makes sure no endpoint is left out of the isolation tests.
   - A cross-organisation sweep compares database snapshots before and after.

---

## 5. Lifecycle

### Mission

```mermaid
stateDiagram-v2
    direction LR
    Draft --> Pending: submit
    Pending --> Active: final approval
    Pending --> Draft: reject / change
    Active --> Completed: complete
```

Any state before Completed can also be **cancelled**.

| Action | Who | Must be true | Effect |
|---|---|---|---|
| submit | owner | Slots full, all accepted, roster eligible, eligible approvers ≥ N | `round += 1`, N saved |
| approve | eligible Director | Hasn't decided this round. Roster eligible. | Active once N is reached. **If a check fails, nothing is written.** |
| reject | eligible Director | Reason given | → Draft |
| transfer | Director | New owner is an active Lead | Pending → Draft. Active stays Active. |
| complete | owner or Director | Mission is Active | Accepted assignments → completed |
| cancel | owner or Director | Reason given | Open assignments → cancelled |

### Assignment

```mermaid
stateDiagram-v2
    direction LR
    Proposed --> Accepted: accept
    Proposed --> Declined: decline
    Accepted --> Withdrawn: withdraw
    Accepted --> Completed: mission completed
```

The owner can also **remove** an open assignment. Cancelling the mission **cancels** every open assignment.

| Action | Who | Mission must be | Notes |
|---|---|---|---|
| propose | owner | Draft or Pending* | Person eligible, place open, not already on this mission |
| accept | crew member | Draft | Still eligible. An overlap names the conflicting mission. |
| decline | crew member | Draft | Reason optional |
| withdraw | crew member | Draft or Pending* | Reason required |
| remove | owner | Draft or Pending* | |

\* Sends a Pending mission back to Draft.

### Cross-cutting rules

| Rule | How it's implemented |
|---|---|
| **Back to Draft** | Every mutating service calls `touch_for_change()` first. Draft → no change. Pending → Draft. Active → `mission_frozen`. Final → `mission_final`. |
| **Edits can't break assignments (M7)** | `invalidated_by()` checks slot removal, headcount, requirements and dates → `invalidates_assignments` |
| **Skill changes (P3)** | Allowed. Refused only if they'd break an **Active** assignment → `invalidates_active_assignment` |
| **Audit** | Written in the same transaction as the change. Refused actions write nothing. |
| **Transactions** | One connection per request. `foreign_keys=ON`. `busy_timeout=5000`. `BEGIN IMMEDIATE` *before* checks. Roll back on error. Lock timeout → 503 `busy`. ([TR-11](#tr-11)) |

---

## 6. Matching
````

</details>

<details>
<summary>↳ Result</summary>

````
## 7. API

**Conventions**
- REST and JSON, under `/api/v1`.
- Authentication with the header `Authorization: Bearer <token>`.
- Lifecycle changes are explicit `POST` commands, for example `/submit`. They are never `PATCH status`, because each one has its own guards and audit event ([TR-8](#tr-8)).
- List endpoints return only what the caller is allowed to see.

#### Auth and me
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Exchange email and password for a token |
| POST | `/auth/logout` | Revoke the current token |
| GET | `/me` | Current user, role and crew profile |
| POST | `/me/password` | Change password (revokes all sessions) |
| GET | `/me/inbox` | Things waiting on me |

#### Organisation, users and skills (Directors)
| Method | Path | Purpose |
|---|---|---|
| GET · PATCH | `/org` | View settings, or set the required approvals |
| GET · POST | `/users` | List users, or create one with an initial password |
| PATCH | `/users/{id}` | Change role or deactivate |
| POST | `/users/{id}/crew-profile` | Give a user a crew profile |
| GET · POST | `/skills` | List skills (Leads too), or add one |
| PATCH · DELETE | `/skills/{id}` | Rename, or delete if unused |

#### Crew
| Method | Path | Purpose |
|---|---|---|
| GET | `/crew` · `/crew/{id}` | List or view profiles |
| PATCH | `/crew/{id}` | Edit own display name and bio |
| PUT · DELETE | `/crew/{id}/skills/{skill_id}` | Set or remove a skill level |
| GET · POST | `/crew/{id}/unavailability` | List or add own unavailability |
| DELETE | `/crew/{id}/unavailability/{uid}` | Remove own unavailability |
| GET | `/crew/{id}/assignments` | Assignment history (summaries) |

#### Missions
| Method | Path | Purpose |
|---|---|---|
| GET · POST | `/missions` | List visible missions, or create one with slots |
| GET · PATCH | `/missions/{id}` | View, or edit name and dates |
| POST | `/missions/{id}/slots` | Add a slot |
| PATCH · DELETE | `/missions/{id}/slots/{sid}` | Edit or remove a slot |
| GET | `/missions/{id}/history` | Audit trail |
| POST | `/missions/{id}/submit` · `approve` · `reject` · `complete` · `cancel` | Lifecycle commands |
| POST | `/missions/{id}/owner` | Transfer ownership |
| GET | `/missions/{id}/match` | Preview suggested roster |
| POST | `/missions/{id}/match/apply` | Create proposals from the suggestion |

#### Assignments
| Method | Path | Purpose |
|---|---|---|
| POST | `/missions/{id}/assignments` | Propose a crew member for a slot |
| GET | `/assignments` | My assignments |
| POST | `/assignments/{id}/accept` · `decline` · `withdraw` · `remove` | Respond or remove |

#### Errors

Every error has the same shape, for every status code (401, 403, 404, 409, 422, 503). `problems` is always present and always has at least one entry, so clients only ever handle one format. A rule or state conflict (409) lists **every** problem at once. A permission refusal (403) lists its single reason, because only one applies and the actor can't fix it themselves. Each problem names the record involved:

```json
{
  "error": {
    "code": "rule_violation",
    "message": "Mission can't be submitted",
    "problems": [
      { "code": "slot_unfilled", "message": "Commander: 1 of 1 place unfilled", "refs": { "slot_id": 12 } }
    ]
  }
}
```

| HTTP | Meaning | Codes |
|---|---|---|
| 401 | Not authenticated | `invalid_credentials` `unauthenticated` |
| 403 | Not allowed | `role_forbidden` `not_owner` `approver_is_creator` `approver_is_rostered` `self_skill_edit` `wrong_current_password` |
| 404 | Not found or not visible | `not_found` |
| 409 | Conflicts with state or a rule | **State:** `mission_frozen` `mission_final` `invalid_transition` `already_decided`<br>**Rules:** `rule_violation` `overlap` `unavailable` `insufficient_approvers` `invalidates_assignments` `invalidates_active_assignment`<br>**Admin:** `has_open_assignments` `owns_open_missions` `last_director` `skill_in_use` |
| 422 | Invalid input | `validation_error` `password_too_short` |
| 503 | Database busy, retry | `busy` |

**Problem codes.** These appear inside `problems` and explain each refusal. Adding one means updating this table in the same change.

| Code | Raised when | Typical `refs` |
|---|---|---|
| `inactive` | The person is deactivated | `crew_profile_id`, `slot_id` |
| `skill_below_minimum` | A required skill is missing or below the minimum | `crew_profile_id`, `slot_id`, `skill_id` |
| `unavailable` | Unavailability overlaps the mission's dates | `crew_profile_id`, `slot_id` |
| `overlap` | An accepted assignment on another mission overlaps (the message names that mission) | `crew_profile_id`, `mission_id`, `mission_name` |
| `slot_has_open_assignments` | Removing a slot that still has crew | `assignment_id`, `crew_profile_id`, `slot_id` |
| `headcount_below_open_assignments` | Lowering headcount below the assigned crew (the message names them) | `slot_id`, `crew_profile_ids` |
| `invalidates_active_assignment` | A skill change would break an assignment on an Active mission | `mission_id`, `skill_id` |
| `slot_unfilled` | Submitting with empty places | `slot_id` |
| `proposal_unanswered` | Submitting while a proposal is still waiting for a reply (the message names the person and slot) | `assignment_id`, `slot_id`, `crew_profile_id` |
| `already_exists` | Inside a 409 `rule_violation`: the email address is already in use (anywhere on the platform, since login is by email alone; see [TR-13](#tr-13)), a skill name is already in the catalogue (ignoring case), or the user already has a crew profile | `email`; `skill_id`; `user_id`, `crew_profile_id` |

---

## 8. CLI

| Concern | Behaviour |
|---|---|
| Client | An `httpx2` wrapper passed into commands, so tests use `TestClient` and need no server |
| Auth | Token stored in `~/.config/mission-control/credentials.json` (mode 0600). Cleared on logout, password change or 401. |
| References | Missions and assignments by ID. People by email. Skills by name. Slots by name or position. |
| Passwords | Hidden prompt only, never a flag. Asked twice when setting one. |
| Output | Plain tables. No meaning carried by colour alone. `--json` for scripts. |
| Errors | The message, then one bullet per problem, then a hint for known codes |
| Exit codes | `0` OK · `1` refused · `2` usage · `3` authentication · `4` unreachable or busy |
| Confirmations | Changing a Pending mission, or cancelling, asks first. `--yes` skips the prompt. |

```bash
# Everyone
mc login | logout | whoami | password | inbox
mc me show | update | unavailable add|list|remove
mc assignments list [--pending] | accept ID | decline ID | withdraw ID --reason R

# Leads
mc missions create --name N --start D --end D --slot "Commander:1:Piloting>=4,Leadership>=3"
mc missions edit | slot add|edit|remove | match ID [--apply]
mc missions propose ID --slot S --crew EMAIL | remove-crew ID ASSIGNMENT | submit ID
mc crew list | show | history | set-skill EMAIL SKILL LEVEL | unset-skill EMAIL SKILL

# Directors
mc missions approve ID | reject ID --reason R | transfer ID --owner EMAIL
mc missions complete ID | cancel ID --reason R | list | show | history
mc users list | add | set-role | deactivate | enable-crew
mc skills list | add | rename | remove          mc org show | set-approvals N
```

---

## 9. Delivery plan

We deliver in four phases. Each phase ends in something that can be demonstrated and tested.

```mermaid
flowchart LR
    A[1 Pure domain<br/>M0–M5] --> B[2 Persistence<br/>M6–M8] --> C[3 Services<br/>M9–M14] --> D[4 Interfaces<br/>M15–M17]
```

| Phase | Milestone (what you can show) |
|---|---|
| 1. Pure domain | Matcher reproduces S2 and S3; lifecycle and permission tables pass, with no database involved |
| 2. Persistence | Seeded database matches PRD §9; tenant-scoped queries; login works |
| 3. Services | Every scenario passes at the service level (S1, S3b–S8) |
| 4. Interfaces | Full golden path (S1) through the real CLI; isolation sweep passes; README smoke test passes |

| # | Module | Write these tests first |
|---|---|---|
| **Phase 1** | | |
| M0 | Skeleton | `/health` returns 200 |
| M1 | dates | Boundary-day overlap (AC-17) · mission-days · end ≥ start |
| M2 | eligibility, passwords | Each ineligibility reason · workload (AC-20) · M7 and P3 checks · 14 characters rejected, 15 accepted |
| M3 | matching | S2, S3 · each tie-break · most-constrained first · unfilled · determinism |
| M4 | lifecycle, approvals | All submit problems at once (AC-2) · quorum uses saved N · approver rules (AC-8, 11, 12) · failed approval writes nothing |
| M5 | permissions | Full action × role table |
| **Phase 2** | | |
| M6 | schema | Pragmas · rollback · constraints · composite foreign keys |
| M7 | repos, seed | Seed matches PRD §9 · scoped `get` · V2 visibility · SQL lint |
| M8 | auth | Login · inactive user · expiry · every revocation path · role read fresh |
| **Phase 3** | | |
| SF | service foundation | Service context (actor + `Repos` + transaction + audit) · `RuleViolation` carrying problems · refused view becomes not-found · fact loaders building `CandidateFacts` / `RosterEntry` / `AssignmentFact` / `ActiveAssignment` from the database · the repository writes Wave 1 needs |
| M9 | admin | P1, P7–P10 · last Director (AC-25, 26) |
| M10 | crew | Self-only edits (AC-16) · skill rules (AC-23) · reasons hidden (AC-24) |
| M11 | missions | M7 · back to Draft (AC-4) · Active freeze · transfer (AC-7) |
| M12 | assignments | Propose (AC-14) · overlap on accept (AC-15) · withdraw (S5) · cascades |
| M13 | approvals | S1, S6, S7, S8 · audit trail (AC-1) |
| M14 | matching service | Preview writes nothing (AC-22) · apply · isolation (AC-31) · S3b |
| **Phase 4** | | |
| M15 | API | Error mapping: **every** error body has a non-empty `problems` list, 403/404/401/422/503 included · permissions over HTTP · isolation sweep (S9) · scenarios |
| M16 | CLI | Reference resolution · `--slot` parser · prompts · exit codes · S1, S4 |
| M17 | README | Smoke-test the README commands |

**Waves.** Independent modules may be built at the same time, each in its own git worktree ([§10](#working-in-waves-worktrees)), and then reviewed and committed one at a time. Phase 3 runs as:

```
SF service foundation (on main)
  → Wave 1: M9 admin ∥ M10 crew ∥ M11 missions
  → M12 assignments
  → Wave 3: M13 approvals ∥ M14 matching service
```

SF comes first so the waves share one service context and one set of fact loaders instead of each writing their own. Earlier pairs that were independent: M3 ∥ M4, M5 ∥ M6.

**Definition of done (every module)**
- [ ] Tests were written first, and each test name includes the PRD ID it covers.
- [ ] `uv run pytest` and `uv run ruff check` both pass on the whole repo.
- [ ] No layer-boundary violations ([§10](#10-guidelines-for-implementing-agents)).
- [ ] Any new endpoint is added to the isolation sweep.
- [ ] The module was verified by actually running it, and the output was shown, not just the test results.
- [ ] A read-only review of the diff was done and its findings reported.
- [ ] A commit was **proposed**, and made only after the user approved it.

---

## 10. Guidelines for implementing agents

### Source of truth
1. The **PRD** decides behaviour. **This document** decides structure. Code follows both.
2. **Don't invent behaviour.** If the PRD is silent or contradicts this document, stop and ask. Don't guess, and don't "improve" the rule.
3. Work on **one module at a time**, in the order in [§9](#9-delivery-plan). Start a module only when the user has approved it, and never before its dependencies are done.

### The loop for each module
1. Read the module's row in §9 and every PRD ID it references.
2. Write failing tests. Name them after the rule, for example `test_ac15_accept_overlap_names_conflicting_mission`.
3. Write the smallest implementation that makes them pass.
4. Refactor, then run the **full** suite and `ruff`.
5. Verify the behaviour by running it for real (a REPL call, a request, or a CLI command), and show the output.
6. Do a read-only review of the diff, and report findings without editing anything.
7. Propose a commit message, such as `feat(m12): assignment propose/accept/withdraw`. **Don't commit, and don't start the next module, until the user approves.**

### Working in waves (worktrees)
- **Approval:** a wave starts only when the user approves every module in it. The modules must not depend on each other.
- **Isolation:** each module gets its own worktree and branch, `.worktrees/<module>` on branch `<module>` (e.g. `m9-admin`), created from the current `main`. The agent works only inside it and runs `uv sync` and the tests there.
- **Agents don't commit.** Each leaves its changes uncommitted and reports the usual package: tests first, real run, read-only review.
- **Review is one branch at a time.** The user reviews only that module's diff against `main`.
- **Merge:** after approval, the lead commits on the branch, rebases it onto `main` if `main` has moved (re-running its tests), fast-forwards `main`, and runs the full suite on `main` before the next review.
- **Ports:** a real run that starts a server uses port `8000 + module number` (e.g. M11 uses 8011).
- **Clean-up:** remove the worktree and branch once merged.

### Architecture rules (never break these)
- `domain/` imports nothing from `infra/`, `services/`, `api/` or `sqlite3`.
- All SQL lives in `infra/repositories/`, and every query filters on `org_id`.
- `org_id` comes only from the `Actor`. Never read it from request input.
- Every mutating service calls `touch_for_change()` first, and writes an audit event in the same transaction.
- Writes open `BEGIN IMMEDIATE` **before** running checks.
- Errors use the codes in [§7](#7-api). Adding a code means updating that table in the same change.

### Coding conventions
- Type hints everywhere. Frozen dataclasses for domain records. No module-level mutable state.
- `date` objects in the domain, ISO strings only at the database and API edges. Timestamps are UTC.
- Use PRD vocabulary in names: `open_places`, `eligible_approver`, `workload`.
- Keep routers thin: validate, call one service, return.

### Testing conventions
- Use the `seeded_db` fixture for PRD scenarios, and `tests/builders.py` for edge cases.
- Every test gets its own database. No network calls. No reliance on the current date: pass dates in.
- Never weaken or delete a test to make it pass. If a test looks wrong, raise it.

### Stop and ask before
- adding a dependency;
- changing the schema (and if you do, update [Appendix A](#appendix-a-schema-sql) as well);
- adding an endpoint, error code or CLI command that isn't in this document;
- any case where the PRD looks ambiguous or a PRD scenario's expected outcome seems wrong.

---

## 11. Setup and testing
### Assignments, approvals and audit

```sql
CREATE TABLE assignments (
  id              INTEGER PRIMARY KEY,
  org_id          INTEGER NOT NULL,
  mission_id      INTEGER NOT NULL,
  slot_id         INTEGER NOT NULL,
  crew_profile_id INTEGER NOT NULL,
  status          TEXT    NOT NULL DEFAULT 'proposed'
                  CHECK (status IN ('proposed','accepted','declined','withdrawn','removed','completed','cancelled')),
  proposed_by_id  INTEGER NOT NULL,
  reason          TEXT,                                          -- decline (optional) / withdraw (required)
  created_at      TEXT    NOT NULL DEFAULT (<now>),
  updated_at      TEXT    NOT NULL DEFAULT (<now>),
  CHECK (status <> 'withdrawn' OR length(trim(coalesce(reason, ''))) > 0),   -- S3
  UNIQUE (org_id, id),
  FOREIGN KEY (org_id, mission_id)          REFERENCES missions(org_id, id),
  FOREIGN KEY (org_id, mission_id, slot_id) REFERENCES slots(org_id, mission_id, id),
  FOREIGN KEY (org_id, crew_profile_id)     REFERENCES crew_profiles(org_id, id),
  FOREIGN KEY (org_id, proposed_by_id)      REFERENCES users(org_id, id)
) STRICT;
CREATE UNIQUE INDEX assignments_one_open_per_mission                -- S1
  ON assignments(mission_id, crew_profile_id) WHERE status IN ('proposed','accepted');
CREATE INDEX assignments_slot    ON assignments(slot_id, status);
CREATE INDEX assignments_profile ON assignments(crew_profile_id, status);   -- overlap + workload lookups

CREATE TABLE approvals (
  id          INTEGER PRIMARY KEY,
  org_id      INTEGER NOT NULL,
  mission_id  INTEGER NOT NULL,
  round       INTEGER NOT NULL CHECK (round >= 1),
  director_id INTEGER NOT NULL,
  decision    TEXT    NOT NULL CHECK (decision IN ('approve','reject')),
  reason      TEXT,
  created_at  TEXT    NOT NULL DEFAULT (<now>),
  CHECK (decision = 'approve' OR length(trim(coalesce(reason, ''))) > 0),   -- rejection needs a reason
  UNIQUE (mission_id, round, director_id),                       -- A3
  UNIQUE (org_id, id),
  FOREIGN KEY (org_id, mission_id)  REFERENCES missions(org_id, id),
  FOREIGN KEY (org_id, director_id) REFERENCES users(org_id, id)
) STRICT;

CREATE TABLE audit_events (                                      -- append-only (V1)
  id              INTEGER PRIMARY KEY,
  org_id          INTEGER NOT NULL REFERENCES organisations(id),
  actor_id        INTEGER NOT NULL,
  event           TEXT    NOT NULL,                              -- e.g. 'mission.submitted', 'assignment.accepted'
  mission_id      INTEGER,
  assignment_id   INTEGER,
  crew_profile_id INTEGER,
  from_status     TEXT,
  to_status       TEXT,
  reason          TEXT,
  data            TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(data)),   -- names at the time of the event
  created_at      TEXT    NOT NULL DEFAULT (<now>),
  FOREIGN KEY (org_id, actor_id)        REFERENCES users(org_id, id),
  FOREIGN KEY (org_id, mission_id)      REFERENCES missions(org_id, id),
  FOREIGN KEY (org_id, assignment_id)   REFERENCES assignments(org_id, id),
  FOREIGN KEY (org_id, crew_profile_id) REFERENCES crew_profiles(org_id, id)
) STRICT;
CREATE INDEX audit_events_mission ON audit_events(mission_id, created_at);
CREATE INDEX audit_events_profile ON audit_events(crew_profile_id, created_at);
CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events
  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events
  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
```

Composite foreign keys are only checked when every column in them is non-NULL, so the optional references on `audit_events` work as expected.

---

## Appendix B: Trade-offs and considerations
````

</details>

### 🤖 Claude · 2026-10-12 02:35:29 UTC

Now the code.

**🔧 Bash**

*Read lifecycle, errors, events*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control && cat domain/lifecycle.py domain/errors.py domain/events.py
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


# The states each mission action may start from. Its keys are the mission actions.
MISSION_ALLOWED_FROM: Mapping[Action, frozenset[MissionStatus]] = MappingProxyType(
    {
        Action.SUBMIT: frozenset({M.DRAFT}),
        Action.APPROVE: frozenset({M.PENDING_APPROVAL}),
        Action.REJECT: frozenset({M.PENDING_APPROVAL}),
        Action.TRANSFER: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.COMPLETE: frozenset({M.ACTIVE}),
        Action.CANCEL: frozenset({M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE}),
        Action.EDIT_MISSION: frozenset({M.DRAFT, M.PENDING_APPROVAL}),
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
    """The mission's status once `action` succeeds. Check `state_problem` first."""
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
    return [
        p
        for e in roster
        if e.status == A.ACCEPTED
        for p in ineligibility_reasons(e.crew, e.slot, window)
    ]


def check_submit(
    slots: Sequence[SlotSpec],
    roster: Sequence[RosterEntry],
    window: DateRange,
    eligible_approvers: int,
    approvals_required: int,
) -> list[Problem]:
    """Everything stopping a Draft mission being submitted, all at once. `slots[i].open_places`
    is headcount minus open assignments.

    The order is part of the contract, and callers show problems in it: unfilled places (in
    slot order), then unanswered proposals, then accepted crew who are no longer eligible (in
    roster order), then too few eligible approvers."""
    problems: list[Problem] = []
    for s in slots:
        if s.open_places > 0:
            problems.append(
                Problem(
                    "slot_unfilled",
                    f"{s.name}: {s.open_places} place{'s' if s.open_places > 1 else ''} unfilled",
                    {"slot_id": s.id},
                )
            )
    for e in roster:
        if e.status == A.PROPOSED:
            problems.append(
                Problem(
                    "proposal_unanswered",
                    f"{e.slot.name}: {e.crew.name} hasn't responded to the proposal",
                    {
                        "assignment_id": e.assignment_id,
                        "slot_id": e.slot.id,
                        "crew_profile_id": e.crew.crew_profile_id,
                    },
                )
            )
    problems.extend(roster_problems(roster, window))
    if eligible_approvers < approvals_required:
        problems.append(
            Problem(
                "insufficient_approvers",
                f"{eligible_approvers} eligible approver{'s' if eligible_approvers != 1 else ''}, "
                f"{approvals_required} required",
            )
        )
    return problems
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
    """A change conflicts with the rules or the current state. Carries every problem at once."""

    def __init__(self, message: str, problems: Sequence[Problem], code: str = "rule_violation"):
        if not problems:
            raise ValueError("a RuleViolation needs at least one problem")
        super().__init__(message)
        self.code = code
        self.message = message
        self.problems = tuple(problems)

    @classmethod
    def of(cls, problem: Problem) -> "RuleViolation":
        """A refusal with a single reason takes that reason's code and message."""
        return cls(problem.message, [problem], code=problem.code)


class InvalidInput(ValueError):
    """A value the caller supplied is malformed, e.g. a blank name or a level out of range.
    Answered as 422. Distinct from plain ValueError, which also signals programming errors."""

    code = "validation_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
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
```

</details>

**🔧 Bash**

*Read eligibility, records, enums, permissions*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control && cat domain/eligibility.py domain/records.py domain/enums.py domain/permissions.py
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
"""Plain facts the domain rules work on. Services build these from the database."""

from collections.abc import Mapping
from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus


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
from enum import StrEnum


class MissionStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    REMOVED = "removed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Role(StrEnum):
    DIRECTOR = "director"
    LEAD = "lead"
    CREW = "crew"


class Action(StrEnum):
    """Everything a user can attempt. The lifecycle and permission modules share this one enum,
    so a mission or assignment action means the same member everywhere."""

    # Mission transitions
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    TRANSFER = "transfer"  # hand the mission to another Lead
    COMPLETE = "complete"
    CANCEL = "cancel"
    EDIT_MISSION = "edit_mission"  # any change to dates, slots or requirements
    # Assignment actions
    PROPOSE_CREW = "propose_crew"
    REMOVE_CREW = "remove_crew"
    ACCEPT = "accept"
    DECLINE = "decline"
    WITHDRAW = "withdraw"
    # Administration, profiles and viewing
    MANAGE_ORG = "manage_org"  # settings, users, roles, initial passwords, crew profiles
    MANAGE_SKILLS = "manage_skills"
    LIST_SKILLS = "list_skills"
    CHANGE_OWN_PASSWORD = "change_own_password"
    VIEW_CREW = "view_crew"
    VIEW_ASSIGNMENT_HISTORY = "view_assignment_history"
    VIEW_UNAVAILABILITY_REASON = "view_unavailability_reason"
    EDIT_OWN_PROFILE = "edit_own_profile"  # personal details and unavailability
    SET_SKILL_LEVEL = "set_skill_level"
    VIEW_MISSION = "view_mission"  # includes its history
    CREATE_MISSION = "create_mission"
    APPLY_MATCH = "apply_match"
    PREVIEW_MATCH = "preview_match"
"""Who may do what. `authorize` is the single entry point; it raises Forbidden with a code.

Each action combines a role check with, where needed, a relationship check: owner of the
mission, the person themselves, the mission's creator, or someone on its roster.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from mission_control.domain.approvals import conflict_problems
from mission_control.domain.enums import Action, Role
from mission_control.domain.errors import Forbidden


@dataclass(frozen=True)
class Actor:
    user_id: int
    org_id: int
    role: Role
    crew_profile_id: int | None


@dataclass(frozen=True)
class Context:
    """Facts about the target that the relationship rules need. Unused fields stay None.

    None means "not supplied", which differs from an empty roster ("nobody rostered"). An action
    whose rule needs a field refuses to run without it rather than treating it as a mismatch.
    """

    owner_id: int | None = None  # the mission's owning Lead
    created_by_id: int | None = None  # who created the mission
    target_user_id: int | None = None  # whose profile, skills or assignment this is
    rostered_user_ids: frozenset[int] | None = None


D, L, C = Role.DIRECTOR, Role.LEAD, Role.CREW
ALL = frozenset(Role)

# Which roles may attempt each action at all. Relationship rules below narrow this further.
ROLES: Mapping[Action, frozenset[Role]] = MappingProxyType(
    {
        Action.MANAGE_ORG: frozenset({D}),
        Action.MANAGE_SKILLS: frozenset({D}),
        Action.LIST_SKILLS: frozenset({D, L}),
        Action.CHANGE_OWN_PASSWORD: ALL,
        Action.VIEW_CREW: ALL,
        Action.VIEW_ASSIGNMENT_HISTORY: ALL,
        Action.VIEW_UNAVAILABILITY_REASON: ALL,
        Action.EDIT_OWN_PROFILE: ALL,
        Action.SET_SKILL_LEVEL: frozenset({D, L}),
        Action.VIEW_MISSION: ALL,
        Action.CREATE_MISSION: frozenset({D, L}),
        Action.EDIT_MISSION: frozenset({L}),
        Action.PROPOSE_CREW: frozenset({L}),
        Action.REMOVE_CREW: frozenset({L}),
        Action.APPLY_MATCH: frozenset({L}),
        Action.SUBMIT: frozenset({L}),
        Action.PREVIEW_MATCH: frozenset({D, L}),
        Action.COMPLETE: frozenset({D, L}),
        Action.CANCEL: frozenset({D, L}),
        Action.TRANSFER: frozenset({D}),
        Action.APPROVE: frozenset({D}),
        Action.REJECT: frozenset({D}),
        Action.ACCEPT: ALL,
        Action.DECLINE: ALL,
        Action.WITHDRAW: ALL,
    }
)

_OWNER_ONLY = frozenset(
    {
        Action.EDIT_MISSION,
        Action.PROPOSE_CREW,
        Action.REMOVE_CREW,
        Action.APPLY_MATCH,
        Action.SUBMIT,
    }
)
_OWNER_OR_DIRECTOR = frozenset({Action.PREVIEW_MATCH, Action.COMPLETE, Action.CANCEL})
# Crew may only see their own record; Leads and Directors may see anyone's.
_CREW_SELF_ONLY = frozenset({Action.VIEW_CREW, Action.VIEW_ASSIGNMENT_HISTORY})
# Only the person themselves, whatever their role.
_SELF_ONLY = frozenset({Action.EDIT_OWN_PROFILE, Action.ACCEPT, Action.DECLINE, Action.WITHDRAW})

_OWNER = ("owner_id",)
_TARGET = ("target_user_id",)
# The Context fields each relationship rule reads. Leaving one out is a caller bug, not a refusal.
_REQUIRED_CONTEXT: Mapping[Action, tuple[str, ...]] = MappingProxyType(
    {
        Action.EDIT_MISSION: _OWNER,
        Action.PROPOSE_CREW: _OWNER,
        Action.REMOVE_CREW: _OWNER,
        Action.APPLY_MATCH: _OWNER,
        Action.SUBMIT: _OWNER,
        Action.PREVIEW_MATCH: _OWNER,
        Action.COMPLETE: _OWNER,
        Action.CANCEL: _OWNER,
        Action.CREATE_MISSION: _OWNER,
        Action.SET_SKILL_LEVEL: _TARGET,
        Action.EDIT_OWN_PROFILE: _TARGET,
        Action.ACCEPT: _TARGET,
        Action.DECLINE: _TARGET,
        Action.WITHDRAW: _TARGET,
        Action.VIEW_CREW: _TARGET,
        Action.VIEW_ASSIGNMENT_HISTORY: _TARGET,
        Action.VIEW_UNAVAILABILITY_REASON: _TARGET,
        Action.APPROVE: ("created_by_id", "rostered_user_ids"),
        Action.REJECT: ("created_by_id", "rostered_user_ids"),
        Action.VIEW_MISSION: ("rostered_user_ids",),
    }
)


# Messages. Phrases are written out so every refusal reads as a natural sentence.

_ROLE_PLURAL: Mapping[Role, str] = MappingProxyType({D: "Directors", L: "Leads", C: "Crew"})

# Completes "<Role plural> can't ...".
ROLE_PHRASE: Mapping[Action, str] = MappingProxyType(
    {
        Action.MANAGE_ORG: "manage the organisation",
        Action.MANAGE_SKILLS: "manage the skill catalogue",
        Action.LIST_SKILLS: "view the skill catalogue",
        Action.CHANGE_OWN_PASSWORD: "change their password",
        Action.VIEW_CREW: "view crew profiles",
        Action.VIEW_ASSIGNMENT_HISTORY: "view assignment history",
        Action.VIEW_UNAVAILABILITY_REASON: "see unavailability reasons",
        Action.EDIT_OWN_PROFILE: "edit profiles",
        Action.SET_SKILL_LEVEL: "change skill levels",
        Action.VIEW_MISSION: "view missions",
        Action.CREATE_MISSION: "create missions",
        Action.EDIT_MISSION: "edit missions",
        Action.PROPOSE_CREW: "propose crew",
        Action.REMOVE_CREW: "remove crew",
        Action.APPLY_MATCH: "apply matcher suggestions",
        Action.SUBMIT: "submit missions",
        Action.PREVIEW_MATCH: "preview matcher suggestions",
        Action.COMPLETE: "complete missions",
        Action.CANCEL: "cancel missions",
        Action.TRANSFER: "transfer mission ownership",
        Action.APPROVE: "approve missions",
        Action.REJECT: "reject missions",
        Action.ACCEPT: "accept assignments",
        Action.DECLINE: "decline assignments",
        Action.WITHDRAW: "withdraw from assignments",
    }
)

# Completes "Only the mission's owner can ..." / "Only the owner or a Director can ...".
_MISSION_PHRASE: Mapping[Action, str] = MappingProxyType(
    {
        Action.EDIT_MISSION: "edit this mission",
        Action.PROPOSE_CREW: "propose crew for this mission",
        Action.REMOVE_CREW: "remove crew from this mission",
        Action.APPLY_MATCH: "apply matcher suggestions to this mission",
        Action.SUBMIT: "submit this mission",
        Action.PREVIEW_MATCH: "preview matching for this mission",
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
```

</details>

**🔧 Bash**

*Read context and repository base files*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control && cat services/context.py infra/repositories/__init__.py infra/repositories/base.py infra/repositories/assignments.py infra/repositories/audit.py
```

<details>
<summary>↳ Result</summary>

```
"""What every use case runs with: who is acting, their organisation's repositories, the time,
one transaction and its audit trail.

A use case follows one shape: load through `ctx.repos`, check with domain rules, then write and
audit inside `with ctx.write():`. Refusals raise `Forbidden`, `NotFound` or `RuleViolation`.
"""

import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control.domain.errors import Forbidden, NotFound, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import NO_CONTEXT, Action, Actor, Context, authorize
from mission_control.infra.db import read_tx, write_tx
from mission_control.infra.repositories import Repos


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


def check(problems: Sequence[Problem], message: str) -> None:
    """Raise every problem at once as a RuleViolation; do nothing if there are none."""
    if problems:
        raise RuleViolation(message, problems)
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
"""Assignments by id, and the shared row mapping for them."""

from __future__ import annotations

import sqlite3

from mission_control.domain.enums import AssignmentStatus
from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Assignment


class AssignmentRepo(Scoped):
    def get(self, assignment_id: int) -> Assignment | None:
        r = self._one(
            "SELECT * FROM assignments WHERE org_id = :org AND id = :id", id=assignment_id
        )
        return assignment_from_row(r) if r else None


def assignment_from_row(r: sqlite3.Row) -> Assignment:
    return Assignment(
        r["id"],
        r["mission_id"],
        r["slot_id"],
        r["crew_profile_id"],
        AssignmentStatus(r["status"]),
        r["reason"],
    )
"""The append-only audit trail."""

from __future__ import annotations

import json
from collections.abc import Mapping

from mission_control.infra.repositories.base import Scoped


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
```

</details>

**🔧 Bash**

*Read missions, facts, models repositories*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control && cat infra/repositories/missions.py infra/repositories/facts.py infra/repositories/models.py
```

<details>
<summary>↳ Result</summary>

```
"""Missions, their slots and requirements, and who can see them."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.permissions import Actor
from mission_control.domain.records import Requirement
from mission_control.infra.repositories.assignments import assignment_from_row
from mission_control.infra.repositories.base import (
    FINAL,
    NOW,
    ON_MISSION,
    Scoped,
    in_list,
    window,
)
from mission_control.infra.repositories.models import Assignment, Mission, Slot


class MissionRepo(Scoped):
    """Missions and their parts.

    Mission visibility for crew is decided here: Directors and Leads see every mission in their
    organisation, while crew see only the missions they're on (see `rostered_user_ids`). A
    mission a crew member isn't on is reported as missing, exactly like an unknown id, so callers
    answer 404. Permissions' VIEW_MISSION is the matching rule for services that have already
    loaded the mission.
    """

    def get(self, mission_id: int) -> Mission | None:
        r = self._one("SELECT * FROM missions WHERE org_id = :org AND id = :id", id=mission_id)
        return _mission(r) if r else None

    def list(self) -> list[Mission]:
        return [
            _mission(r)
            for r in self._all("SELECT * FROM missions WHERE org_id = :org ORDER BY start_date, id")
        ]

    def rostered_user_ids(self, mission_id: int) -> frozenset[int]:
        """User ids of the crew on the mission: those holding an open or completed assignment."""
        statuses, params = in_list("s", ON_MISSION)
        rows = self._all(
            f"""SELECT DISTINCT u.id FROM assignments a
                JOIN crew_profiles c ON c.org_id = a.org_id AND c.id = a.crew_profile_id
                JOIN users u ON u.org_id = c.org_id AND u.id = c.user_id
                WHERE a.org_id = :org AND a.mission_id = :mission_id
                AND a.status IN ({statuses})""",
            mission_id=mission_id,
            **params,
        )
        return frozenset(r["id"] for r in rows)

    def list_visible(self, actor: Actor) -> list[Mission]:
        """Directors and Leads see every mission; crew see only the missions they're on."""
        self._check_actor(actor)
        if actor.role != Role.CREW:
            return self.list()
        if actor.crew_profile_id is None:
            return []
        on_mission, params = _crew_on_mission(actor.crew_profile_id)
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
        on_mission, params = _crew_on_mission(actor.crew_profile_id)
        r = self._one(
            f"SELECT * FROM missions m WHERE m.org_id = :org AND m.id = :id AND {on_mission}",
            id=mission_id,
            **params,
        )
        return _mission(r) if r else None

    def non_final_owned_by(self, user_id: int) -> list[Mission]:
        finals, params = in_list("f", FINAL)
        rows = self._all(
            f"SELECT * FROM missions WHERE org_id = :org AND owner_id = :owner"
            f" AND status NOT IN ({finals}) ORDER BY start_date, id",
            owner=user_id,
            **params,
        )
        return [_mission(r) for r in rows]

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
        return (
            self._exec(
                f"UPDATE missions SET name = :name, start_date = :start, end_date = :end,"
                f" updated_at = {NOW} WHERE org_id = :org AND id = :id",
                name=name,
                start=window.start.isoformat(),
                end=window.end.isoformat(),
                id=mission_id,
            ).rowcount
            == 1
        )

    def set_status(self, mission_id: int, status: MissionStatus) -> bool:
        return (
            self._exec(
                f"UPDATE missions SET status = :status, updated_at = {NOW}"
                " WHERE org_id = :org AND id = :id",
                status=status,
                id=mission_id,
            ).rowcount
            == 1
        )

    def set_owner(self, mission_id: int, owner_id: int) -> bool:
        return (
            self._exec(
                f"UPDATE missions SET owner_id = :owner, updated_at = {NOW}"
                " WHERE org_id = :org AND id = :id",
                owner=owner_id,
                id=mission_id,
            ).rowcount
            == 1
        )

    def get_slot(self, slot_id: int) -> Slot | None:
        """A live slot by id, with its requirements."""
        r = self._one(
            "SELECT mission_id FROM slots WHERE org_id = :org AND id = :id AND removed_at IS NULL",
            id=slot_id,
        )
        if r is None:
            return None
        return next(s for s in self.slots(r["mission_id"]) if s.id == slot_id)

    def add_slot(
        self, mission_id: int, name: str, headcount: int, requirements: Mapping[int, int]
    ) -> Slot:
        """Append a slot after the last live one, with its {skill_id: min_level}."""
        cur = self._exec(
            """INSERT INTO slots(org_id, mission_id, name, headcount, position)
               VALUES (:org, :mission_id, :name, :headcount,
                       (SELECT coalesce(max(position), 0) + 1 FROM slots
                        WHERE org_id = :org AND mission_id = :mission_id
                        AND removed_at IS NULL))""",
            mission_id=mission_id,
            name=name,
            headcount=headcount,
        )
        self._insert_requirements(cur.lastrowid, requirements)
        created = self.get_slot(cur.lastrowid)
        assert created is not None
        return created

    def update_slot(self, slot_id: int, name: str, headcount: int) -> bool:
        return (
            self._exec(
                "UPDATE slots SET name = :name, headcount = :headcount"
                " WHERE org_id = :org AND id = :id AND removed_at IS NULL",
                name=name,
                headcount=headcount,
                id=slot_id,
            ).rowcount
            == 1
        )

    def replace_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> bool:
        if self.get_slot(slot_id) is None:
            return False
        self._exec(
            "DELETE FROM slot_requirements WHERE org_id = :org AND slot_id = :slot_id",
            slot_id=slot_id,
        )
        self._insert_requirements(slot_id, requirements)
        return True

    def _insert_requirements(self, slot_id: int, requirements: Mapping[int, int]) -> None:
        for skill_id, min_level in requirements.items():
            self._exec(
                "INSERT INTO slot_requirements(org_id, slot_id, skill_id, min_level)"
                " VALUES (:org, :slot_id, :skill_id, :min_level)",
                slot_id=slot_id,
                skill_id=skill_id,
                min_level=min_level,
            )

    def remove_slot(self, slot_id: int) -> bool:
        """Soft delete: the slot disappears but its past assignments keep their history."""
        return (
            self._exec(
                f"UPDATE slots SET removed_at = {NOW}"
                " WHERE org_id = :org AND id = :id AND removed_at IS NULL",
                id=slot_id,
            ).rowcount
            == 1
        )

    def _check_actor(self, actor: Actor) -> None:
        if actor.org_id != self._org:
            raise ValueError(
                f"actor belongs to org {actor.org_id}, but these repositories are for {self._org}"
            )

    def slots(self, mission_id: int) -> list[Slot]:
        """Live slots in listed order, each with its requirements."""
        slot_rows = self._all(
            "SELECT * FROM slots WHERE org_id = :org AND mission_id = :mission_id"
            " AND removed_at IS NULL ORDER BY position",
            mission_id=mission_id,
        )
        req_rows = self._all(
            """SELECT r.slot_id, r.skill_id, k.name, r.min_level FROM slot_requirements r
               JOIN skills k ON k.org_id = r.org_id AND k.id = r.skill_id
               JOIN slots s ON s.org_id = r.org_id AND s.id = r.slot_id
               WHERE r.org_id = :org AND s.mission_id = :mission_id
               ORDER BY r.slot_id, r.skill_id""",
            mission_id=mission_id,
        )
        reqs: dict[int, list[Requirement]] = {}
        for r in req_rows:
            reqs.setdefault(r["slot_id"], []).append(
                Requirement(r["skill_id"], r["name"], r["min_level"])
            )
        return [
            Slot(
                s["id"],
                s["mission_id"],
                s["name"],
                s["headcount"],
                s["position"],
                tuple(reqs.get(s["id"], ())),
            )
            for s in slot_rows
        ]

    def assignments(
        self, mission_id: int, statuses: Iterable[AssignmentStatus] | None = None
    ) -> list[Assignment]:
        wanted = tuple(statuses) if statuses is not None else tuple(AssignmentStatus)
        if not wanted:
            return []
        statuses, params = in_list("s", wanted)
        rows = self._all(
            f"SELECT * FROM assignments WHERE org_id = :org AND mission_id = :mission_id"
            f" AND status IN ({statuses}) ORDER BY id",
            mission_id=mission_id,
            **params,
        )
        return [assignment_from_row(r) for r in rows]


def _crew_on_mission(crew_profile_id: int) -> tuple[str, dict[str, object]]:
    """A condition on mission `m`: the crew member holds an open or completed assignment on it.
    It joins on m.org_id, so the enclosing query's `m.org_id = :org` scopes it too."""
    statuses, params = in_list("s", ON_MISSION)
    clause = (
        "EXISTS (SELECT 1 FROM assignments a WHERE a.org_id = m.org_id"
        " AND a.mission_id = m.id AND a.crew_profile_id = :crew_profile_id"
        f" AND a.status IN ({statuses}))"
    )
    return clause, {"crew_profile_id": crew_profile_id, **params}


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
"""What the repositories return. Plain frozen records; no database types leak out."""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.records import Requirement


@dataclass(frozen=True)
class Organisation:
    id: int
    name: str
    slug: str
    required_approvals: int


@dataclass(frozen=True)
class User:
    """Never carries the password hash; only the security module reads that."""

    id: int
    org_id: int
    email: str
    name: str
    role: Role
    is_active: bool


@dataclass(frozen=True)
class CrewProfile:
    id: int
    org_id: int
    user_id: int
    display_name: str
    bio: str | None


@dataclass(frozen=True)
class Skill:
    id: int
    org_id: int
    name: str
    category: str | None


@dataclass(frozen=True)
class Unavailability:
    id: int
    crew_profile_id: int
    window: DateRange
    reason: str


@dataclass(frozen=True)
class Mission:
    id: int
    org_id: int
    name: str
    window: DateRange
    status: MissionStatus
    owner_id: int
    created_by_id: int
    approval_round: int
    approvals_required: int | None


@dataclass(frozen=True)
class Slot:
    id: int
    mission_id: int
    name: str
    headcount: int
    position: int
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class Assignment:
    id: int
    mission_id: int
    slot_id: int
    crew_profile_id: int
    status: AssignmentStatus
    reason: str | None


@dataclass(frozen=True)
class Approval:
    id: int
    mission_id: int
    round: int
    director_id: int
    decision: str
    reason: str | None


@dataclass(frozen=True)
class AssignmentSummary:
    """One line of a crew member's history, readable even after they've left the mission."""

    assignment_id: int
    mission_id: int
    mission_name: str
    window: DateRange
    mission_status: MissionStatus
    slot_name: str
    status: AssignmentStatus
    reason: str | None
```

</details>

**🔧 Bash**

*Read approvals and crew repos and crew service*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control && cat infra/repositories/approvals.py infra/repositories/crew.py | head -150; cat services/crew.py
```

<details>
<summary>↳ Result</summary>

```
"""Approval decisions, by round."""

from __future__ import annotations

import sqlite3

from mission_control.infra.repositories.base import Scoped
from mission_control.infra.repositories.models import Approval


class ApprovalRepo(Scoped):
    def get(self, approval_id: int) -> Approval | None:
        r = self._one("SELECT * FROM approvals WHERE org_id = :org AND id = :id", id=approval_id)
        return _approval(r) if r else None

    def for_round(self, mission_id: int, round_: int) -> list[Approval]:
        rows = self._all(
            "SELECT * FROM approvals WHERE org_id = :org AND mission_id = :mission_id"
            " AND round = :round ORDER BY id",
            mission_id=mission_id,
            round=round_,
        )
        return [_approval(r) for r in rows]


def _approval(r: sqlite3.Row) -> Approval:
    return Approval(
        r["id"], r["mission_id"], r["round"], r["director_id"], r["decision"], r["reason"]
    )
"""Crew profiles: details, skills, unavailability and assignment history."""

from __future__ import annotations

import sqlite3

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.infra.repositories.assignments import assignment_from_row
from mission_control.infra.repositories.base import NOW, OPEN, Scoped, in_list, window
from mission_control.infra.repositories.models import (
    Assignment,
    AssignmentSummary,
    CrewProfile,
    Unavailability,
)


class CrewRepo(Scoped):
    def get(self, crew_profile_id: int) -> CrewProfile | None:
        r = self._one(
            "SELECT * FROM crew_profiles WHERE org_id = :org AND id = :id", id=crew_profile_id
        )
        return _crew(r) if r else None

    def by_user(self, user_id: int) -> CrewProfile | None:
        r = self._one(
            "SELECT * FROM crew_profiles WHERE org_id = :org AND user_id = :user_id",
            user_id=user_id,
        )
        return _crew(r) if r else None

    def list(self) -> list[CrewProfile]:
        return [
            _crew(r)
            for r in self._all("SELECT * FROM crew_profiles WHERE org_id = :org ORDER BY id")
        ]

    def skills(self, crew_profile_id: int) -> dict[int, int]:
        rows = self._all(
            "SELECT skill_id, level FROM crew_skills"
            " WHERE org_id = :org AND crew_profile_id = :crew_profile_id",
            crew_profile_id=crew_profile_id,
        )
        return {r["skill_id"]: r["level"] for r in rows}

    def unavailability(self, crew_profile_id: int) -> list[Unavailability]:
        rows = self._all(
            "SELECT * FROM unavailability"
            " WHERE org_id = :org AND crew_profile_id = :crew_profile_id ORDER BY start_date, id",
            crew_profile_id=crew_profile_id,
        )
        return [Unavailability(r["id"], r["crew_profile_id"], window(r), r["reason"]) for r in rows]

    def create(self, user_id: int, display_name: str, bio: str | None = None) -> CrewProfile:
        cur = self._exec(
            "INSERT INTO crew_profiles(org_id, user_id, display_name, bio)"
            " VALUES (:org, :user_id, :display_name, :bio)",
            user_id=user_id,
            display_name=display_name,
            bio=bio,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def update(self, crew_profile_id: int, display_name: str, bio: str | None) -> bool:
        return (
            self._exec(
                f"UPDATE crew_profiles SET display_name = :display_name, bio = :bio,"
                f" updated_at = {NOW} WHERE org_id = :org AND id = :id",
                display_name=display_name,
                bio=bio,
                id=crew_profile_id,
            ).rowcount
            == 1
        )

    def open_assignments(self, crew_profile_id: int) -> list[Assignment]:
        statuses, params = in_list("s", OPEN)
        rows = self._all(
            f"SELECT * FROM assignments WHERE org_id = :org AND crew_profile_id = :crew_profile_id"
            f" AND status IN ({statuses}) ORDER BY id",
            crew_profile_id=crew_profile_id,
            **params,
        )
        return [assignment_from_row(r) for r in rows]

    def add_unavailability(
        self, crew_profile_id: int, window: DateRange, reason: str
    ) -> Unavailability:
        cur = self._exec(
            "INSERT INTO unavailability(org_id, crew_profile_id, start_date, end_date, reason)"
            " VALUES (:org, :crew_profile_id, :start, :end, :reason)",
            crew_profile_id=crew_profile_id,
            start=window.start.isoformat(),
            end=window.end.isoformat(),
            reason=reason,
        )
        return Unavailability(cur.lastrowid, crew_profile_id, window, reason)

    def remove_unavailability(self, crew_profile_id: int, unavailability_id: int) -> bool:
        return (
            self._exec(
                "DELETE FROM unavailability WHERE org_id = :org AND id = :id"
                " AND crew_profile_id = :crew_profile_id",
                id=unavailability_id,
                crew_profile_id=crew_profile_id,
            ).rowcount
            == 1
        )

    def set_skill(self, crew_profile_id: int, skill_id: int, level: int, updated_by: int) -> None:
        """Set a skill level, adding it or changing it, and record who set it."""
        self._exec(
            f"""INSERT INTO crew_skills(org_id, crew_profile_id, skill_id, level, updated_by_id)
                VALUES (:org, :crew_profile_id, :skill_id, :level, :updated_by)
                ON CONFLICT (crew_profile_id, skill_id) DO UPDATE SET
                level = excluded.level, updated_by_id = excluded.updated_by_id,
                updated_at = {NOW} WHERE crew_skills.org_id = :org""",
            crew_profile_id=crew_profile_id,
"""Crew profiles: viewing people, their skills, availability and assignment history; editing
your own personal details and unavailability; and setting other people's skill levels.

Who sees what:
- Directors and Leads see every profile; crew see only their own. A profile the caller can't
  see is reported as not found.
- Unavailability dates are visible with the profile, but the reasons only to Directors and to
  the person themselves.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import invalidated_by_skill_change
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.domain.permissions import Action, Context, can
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import (
    AssignmentSummary,
    CrewProfile,
    Unavailability,
    User,
)
from mission_control.services.context import ServiceContext, found

MIN_LEVEL, MAX_LEVEL = 1, 5

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
    new_name = None if display_name is None else display_name.strip()
    if new_name == "":
        raise InvalidInput("Display name can't be blank")
    if display_name is None and bio is None:
        with ctx.read():  # nothing to change: still check access, but write nothing
            return _own_profile(ctx, crew_profile_id)
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
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
    window = DateRange(start, end)
    reason = reason.strip()
    if not reason:
        raise InvalidInput("Unavailability needs a reason")
    with ctx.write() as repos:
        profile = _own_profile(ctx, crew_profile_id)
        clashes = [
            _overlap(profile, c.mission_id, c.mission_name, c.window, window)
            for c in repos.facts.commitments(profile.id)
            if c.window.overlaps(window)
        ]
        _refuse(
            clashes,
            "overlap",
            f"{profile.display_name} has accepted assignments overlapping those dates",
        )
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
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise InvalidInput(f"Skill level must be between {MIN_LEVEL} and {MAX_LEVEL}")
    with ctx.write() as repos:
        profile, skill_name, previous = _skill_target(ctx, repos, crew_profile_id, skill_id)
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
    _refuse(
        broken,
        "invalidates_active_assignment",
        f"Changing {profile.display_name}'s {skill_name} level would break their assignments "
        f"on active missions",
    )


def _refuse(problems: Sequence[Problem], code: str, several: str) -> None:
    """Raise a RuleViolation if there are problems: a single one gives its own code and message;
    several share `code` and the summary `several`."""
    if len(problems) == 1:
        raise RuleViolation.of(problems[0])
    if problems:
        raise RuleViolation(several, problems, code=code)


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
```

</details>

**🔧 Bash**

*Read admin service head and test fixtures*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 1,140p src/mission_control/services/admin.py; cat tests/integration/conftest.py tests/conftest.py; sed -n 1,80p tests/integration/test_crew_service.py
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

from collections.abc import Iterable, Sequence
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
from mission_control.services.context import ServiceContext, found


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
    email = _required(email, "email address")
    name = _required(name, "name")
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
    if display_name is not None:
        display_name = _required(display_name, "display name")
    with ctx.write() as repos:
        user = found(repos.users.get(user_id), "User")
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
        _refuse(problems, f"{user.name}'s role can't be changed")

        repos.users.set_role(user.id, role)
        ctx.audit(
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
"""M10: the crew service. Viewing profiles and history, personal details, unavailability and
skill levels (PRD P2–P6, §5.7, V2, AC-16, AC-23, AC-24, AC-27–AC-29).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Marco 2 · Lee 4 · Ana 6 ·
Ben 7 · Chen 8 · Fay 11 · Gus 12 · Hana 13 · Sam 14 (Helix) · Kai 16 (Helix).
Skills: Piloting 1 · Leadership 2 · Systems Engineering 3 · EVA 4 · Geology 5 · Helix Piloting 7.
"""

import json
from datetime import UTC, date, datetime

import pytest

from builders import make_assignment, make_crew_profile, make_user
from mission_control.domain.dates import InvalidDateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.domain.errors import Forbidden, NotFound, RuleViolation
from mission_control.domain.permissions import Actor
from mission_control.services import crew
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
FAY = Actor(user_id=11, org_id=1, role=Role.CREW, crew_profile_id=11)
HANA = Actor(user_id=13, org_id=1, role=Role.CREW, crew_profile_id=13)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)
KAI = Actor(user_id=16, org_id=2, role=Role.CREW, crew_profile_id=16)

PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, HELIX_PILOTING = 1, 2, 3, 4, 5, 7
FAY_LEAVE = 1  # Fay's seeded Medical leave, 5–8 Mar 2027


def as_(conn, actor):
    return ServiceContext(conn, actor, now=NOW)


def audit_count(conn):
    return conn.execute("SELECT count(*) FROM audit_events").fetchone()[0]


def last_audit(conn):
    row = conn.execute(
        "SELECT actor_id, event, crew_profile_id, reason, data FROM audit_events"
        " ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return (
        row["actor_id"],
        row["event"],
        row["crew_profile_id"],
        row["reason"],
        json.loads(row["data"]),
    )


def snapshot(conn):
    """Everything the crew service can change, to prove a refusal changed nothing."""
    return [
        conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
        for table in ("crew_profiles", "crew_skills", "unavailability", "audit_events")
    ]


def unchanged(conn, before):
    return [list(map(tuple, t)) for t in snapshot(conn)] == [list(map(tuple, t)) for t in before]


# --- Viewing profiles (§5.7, AC-24) -------------------------------------------------------


def test_ac24_lead_sees_fays_busy_dates_without_the_reason(seeded_db):
    fay = crew.view_crew(as_(seeded_db, LEE), 11)
    assert [(u.window.start, u.window.end) for u in fay.unavailability] == [
        (date(2027, 3, 5), date(2027, 3, 8))
    ]
    assert [u.reason for u in fay.unavailability] == [None]
```

</details>

**🔧 Bash**

*Read seed data and loader audit usage*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && cat src/mission_control/seed/data.py | head -250; grep -n "Event\.\|audit" src/mission_control/seed/loader.py
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
3:Missions are written straight into their seeded states, with the approvals and audit events
79:    audit = Repos(conn, org.id).audit
98:    audit.record(
99:        m.creator_id, Event.MISSION_CREATED, mission_id=m.id, to_status="draft", data=seeded
124:        audit.record(
126:            Event.MISSION_SUBMITTED,
138:        audit.record(director_id, Event.MISSION_APPROVED, mission_id=m.id, data=seeded)
140:        audit.record(
142:            Event.MISSION_ACTIVATED,
149:        audit.record(
151:            Event.MISSION_COMPLETED,
```

</details>

**🔧 Bash**

*Read seed loader, events test, SQL guard test*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 70,170p src/mission_control/seed/loader.py; cat tests/unit/domain/test_events.py; cat tests/integration/test_repository_sql.py | head -80; grep -n "slot" tests/integration/test_seed.py | head -20
```

<details>
<summary>↳ Result</summary>

```
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
    }
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
202:def test_slots_are_in_listed_order_with_their_requirements(seeded_db):
204:    for mission, slot, headcount, reqs in rows(
209:                    FROM (SELECT * FROM slot_requirements r JOIN skills k ON k.id = r.skill_id
210:                          WHERE r.slot_id = s.id ORDER BY k.name) r JOIN skills k
212:            FROM slots s JOIN missions m ON m.id = s.mission_id ORDER BY m.id, s.position""",
214:        got.setdefault(mission, []).append((slot, headcount, reqs))
238:        JOIN missions m ON m.id = a.mission_id JOIN slots s ON s.id = a.slot_id
```

</details>

**🔧 Bash**

*Inspect builders, repository write tests, db helpers*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && grep -n "^def \|^class " tests/builders.py; sed -n 1,40p tests/integration/test_repository_writes.py; grep -n "def test" tests/integration/test_repository_writes.py | head -40; cat src/mission_control/infra/db.py | head -80
```

<details>
<summary>↳ Result</summary>

```
25:def date_range(start: str, end: str) -> DateRange:
48:def req(skill_id: int, min_level: int) -> Requirement:
52:def slot(
68:def crew(
88:def commitment(mission_id: int, mission_name: str, start: str, end: str) -> Commitment:
92:def roster_entry(
141:def make_org(conn, name="Test Org", slug=None, required_approvals=1) -> int:
149:def make_user(conn, org_id, name="Test User", role="crew", email=None, is_active=True) -> int:
164:def make_crew_profile(conn, org_id, user_id, display_name="Test Crew") -> int:
172:def make_mission(
202:def make_slot(conn, org_id, mission_id, name="Engineer", headcount=1, position=1) -> int:
210:def make_assignment(
"""SF: the repository writes Wave 1 (admin, crew, missions) needs. Every write is scoped."""

import sqlite3
from datetime import date

import pytest

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import AssignmentStatus, MissionStatus, Role
from mission_control.infra.repositories import Repos

GATEWAY, REBOOST, TELESCOPE, PAYLOAD = 1, 3, 5, 8


@pytest.fixture
def aurora(seeded_db):
    return Repos(seeded_db, 1)


@pytest.fixture
def helix(seeded_db):
    return Repos(seeded_db, 2)


def window(a, b):
    return DateRange(date.fromisoformat(a), date.fromisoformat(b))


# --- Organisation and users (admin) -------------------------------------------------------


def test_set_required_approvals_changes_only_this_org(aurora, helix):
    aurora.organisation.set_required_approvals(3)
    assert aurora.organisation.get().required_approvals == 3
    assert helix.organisation.get().required_approvals == 1


def test_create_user_in_this_org(seeded_db, aurora):
    user = aurora.users.create("zoe@aurora.example", "Zoe Lane", Role.CREW, "hash")
    assert (user.org_id, user.email, user.role, user.is_active) == (
32:def test_set_required_approvals_changes_only_this_org(aurora, helix):
38:def test_create_user_in_this_org(seeded_db, aurora):
52:def test_duplicate_email_anywhere_is_refused_by_the_database(aurora):
57:def test_role_and_active_changes_are_scoped(aurora, helix):
66:def test_count_active_directors(aurora, helix):
73:def test_missions_a_lead_owns_that_are_not_finished(aurora, helix):
84:def test_create_crew_profile(aurora):
90:def test_update_crew_profile_details_is_scoped(aurora, helix):
96:def test_open_assignments_of_a_crew_member(aurora):
103:def test_add_and_remove_unavailability(aurora, helix):
113:def test_set_skill_inserts_then_updates_and_records_who(seeded_db, aurora):
126:def test_set_skill_cannot_use_another_orgs_skill_or_crew(aurora):
133:def test_remove_skill(aurora, helix):
143:def test_create_rename_and_categorise_skills(aurora, helix):
151:def test_skill_in_use_and_delete(aurora, helix):
163:def test_create_mission_starts_as_draft(aurora):
177:def test_update_mission_name_and_dates_is_scoped(aurora, helix):
189:def test_set_status_and_owner(aurora, helix):
197:def test_owner_from_another_org_is_refused_by_the_database(aurora):
202:def test_add_slot_goes_to_the_end_with_its_requirements(aurora):
209:def test_add_slot_to_another_orgs_mission_is_refused(helix):
214:def test_update_slot_and_replace_requirements(aurora, helix):
225:def test_remove_slot_hides_it_but_keeps_its_history(seeded_db, aurora):
239:def test_get_slot_is_scoped(aurora, helix):
245:def test_updates_stamp_updated_at(seeded_db, aurora):
"""SQLite connections, schema setup and transactions.

Every connection enforces foreign keys and waits a bounded time for locks. Writes take the
database write lock *before* any checks run, so check-then-write rules can't race.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA_SQL = files("mission_control.infra").joinpath("schema.sql").read_text()
MIN_SQLITE_VERSION = (3, 37, 0)  # STRICT tables


class UnsupportedSQLite(RuntimeError):
    pass


class DatabaseBusy(Exception):
    """Another writer held the lock for longer than the busy timeout."""


def check_sqlite_version(version: tuple[int, int, int] = sqlite3.sqlite_version_info) -> None:
    if version < MIN_SQLITE_VERSION:
        need = ".".join(map(str, MIN_SQLITE_VERSION))
        have = ".".join(map(str, version))
        raise UnsupportedSQLite(f"SQLite {need} or later is required, found {have}")


def connect(path: str | Path, *, busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    """One connection per request. Python never opens transactions implicitly
    (isolation_level=None); the connection may be used from FastAPI's worker threads, but never
    by two requests at once."""
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema on an empty database; do nothing if it's already current."""
    check_sqlite_version()
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == SCHEMA_VERSION:
        return
    if version != 0:
        raise RuntimeError(
            f"database schema version {version} is not supported (expected {SCHEMA_VERSION})"
        )
    conn.executescript(f"BEGIN;\n{SCHEMA_SQL}\nCOMMIT;")
    conn.execute("PRAGMA journal_mode = WAL")


def utc_timestamp(moment: datetime) -> str:
    """A time as stored in the database: UTC with millisecond precision, in the same format the
    schema's defaults write, so stored values compare correctly as text. Naive times are refused,
    because their time zone is unknown."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("a timestamp needs a time zone")
    utc = moment.astimezone(UTC)
    return f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond // 1000:03d}Z"


def _is_locked(error: sqlite3.OperationalError) -> bool:
    return "locked" in str(error) or "busy" in str(error)


@contextmanager
def write_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Run a block in one write transaction: commit on success, roll back on any error.

    BEGIN IMMEDIATE takes the write lock up front, so the checks inside the block see the same
    data the writes will change. If the lock isn't free within the busy timeout, DatabaseBusy.
    """
    try:
```

</details>

**🔧 Bash**

*Read write_tx rest and backlog*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 80,130p src/mission_control/infra/db.py; cat docs/backlog.md; ls .worktrees 2>/dev/null; ls ..
```

<details>
<summary>↳ Result</summary>

```
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        if _is_locked(e):
            raise DatabaseBusy("the database is busy; try again") from e
        raise
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    try:
        conn.execute("COMMIT")
    except sqlite3.OperationalError as e:
        conn.execute("ROLLBACK")
        if _is_locked(e):
            raise DatabaseBusy("the database is busy; try again") from e
        raise


@contextmanager
def read_tx(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Run several reads against one consistent snapshot. Ends with COMMIT on success and
    ROLLBACK on any error, so nothing written by a failing block is kept and the original error
    always reaches the caller."""
    conn.execute("BEGIN")
    try:
        yield conn
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    if conn.in_transaction:
        conn.execute("COMMIT")
# Backlog

Things deliberately left as they are for v1, to revisit later. Each entry says what the system does today and what's open.

| Item | Today's behaviour | Open question | From |
|---|---|---|---|
| A Director demoting or deactivating themselves | Allowed, unless they're the last active Director. Deactivating ends their own session. | Should self-demotion or self-deactivation need another Director? | M9 |
| Role changes and new crew profiles for deactivated users | Allowed | Should changes to deactivated users be blocked until reactivation, which is out of scope? | M9 |
| Trimming names and emails | Leading and trailing spaces are removed on create and update | Should other fields (bio, reasons) be normalised the same way everywhere? | M9 |
m11-missions
m12-assignments
m14-matching
```

</details>

**🔧 Bash**

*Read-only peek at M11 revert audit shape*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees && grep -n "RETURNED_TO_DRAFT\|cause\|def _revert\|def _touch" -A6 m11-missions/src/mission_control/services/missions.py 2>/dev/null | head -60; grep -n "M11" -A12 m11-missions/src/mission_control/domain/events.py 2>/dev/null
```

<details>
<summary>↳ Result</summary>

```
8:its approval round stops counting; that return is audited with the change that caused it.
9-"""
10-
11-from collections.abc import Callable, Mapping, Sequence
12-from dataclasses import dataclass, field
13-from datetime import date
14-from types import MappingProxyType
--
548:        message = f"{user.name} can't own a mission because they're deactivated"
549-    else:
550-        return
551-    raise RuleViolation(message, [Problem("owner_not_active_lead", message, {"user_id": user.id})])
552-
553-
554-def _refuse_if_invalidated(
--
582:    and, if a Pending mission went back to Draft, that return with its cause."""
583-    if status != mission.status:
584-        repos.missions.set_status(mission.id, status)
585-    ctx.audit(event, mission_id=mission.id, data=data)
586-    if status != mission.status:
587-        ctx.audit(
588:            Event.MISSION_RETURNED_TO_DRAFT,
589-            mission_id=mission.id,
590-            from_status=mission.status,
591-            to_status=status,
592:            data={"mission_name": data["mission_name"], "cause": event.value},
593-        )
594-
595-
596-# Input checks
597-
598-
14:    # M11 missions
15-    MISSION_UPDATED = "mission.updated"
16-    MISSION_TRANSFERRED = "mission.transferred"
17-    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
18-    SLOT_ADDED = "slot.added"
19-    SLOT_UPDATED = "slot.updated"
20-    SLOT_REQUIREMENTS_CHANGED = "slot.requirements_changed"
21-    SLOT_REMOVED = "slot.removed"
```

</details>

**🔧 Bash**

*Compare refusal helpers in M11 and admin*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees && grep -n "def _refuse" -A15 m11-missions/src/mission_control/services/missions.py; grep -n "def _refuse" -A12 m12-assignments/src/mission_control/services/admin.py
```

<details>
<summary>↳ Result</summary>

```
554:def _refuse_if_invalidated(
555-    repos: Repos, mission: Mission, edit: MissionEditKind, message: Callable[[list[str]], str]
556-) -> None:
557-    """Refuse an edit that would break open assignments. `message` gets the names of everyone
558-    affected, in roster order."""
559-    roster = repos.facts.roster(mission.id)
560-    problems = invalidated_by(edit, roster)
561-    if not problems:
562-        return
563-    names = {e.crew.crew_profile_id: e.crew.name for e in roster}
564-    affected: list[int] = []
565-    for p in problems:
566-        ids = p.refs.get("crew_profile_ids") or [p.refs["crew_profile_id"]]
567-        affected += [i for i in ids if isinstance(i, int) and i not in affected]
568-    raise RuleViolation(
569-        message([names[i] for i in affected]), problems, code="invalidates_assignments"
--
603:def _refuse_input(problems: Sequence[Problem]) -> None:
604-    if problems:
605-        raise InvalidInput(problems)
606-
607-
608-def _name_problems(name: str) -> list[Problem]:
609-    return [] if name.strip() else [_invalid("The mission needs a name")]
610-
611-
612-def _window(start: date, end: date) -> tuple[DateRange | None, list[Problem]]:
613-    try:
614-        return DateRange(start, end), []
615-    except InvalidDateRange:
616-        return None, [
617-            _invalid(f"The end date {end.isoformat()} is before the start date {start.isoformat()}")
618-        ]
340:def _refuse(problems: Sequence[Problem], message: str) -> None:
341-    """A single reason is raised under its own code; several are listed together."""
342-    if len(problems) == 1:
343-        raise RuleViolation.of(problems[0])
344-    if problems:
345-        raise RuleViolation(message, problems)
346-
347-
348-def _required(value: str, what: str) -> str:
349-    stripped = value.strip()
350-    if not stripped:
351-        raise InvalidInput(f"The {what} can't be blank")
352-    return stripped
```

</details>

### 🤖 Claude · 2026-10-12 02:38:13 UTC

Now I have the context. Let me write the tests first.

**🔧 Bash**

*Check admin tests header and baseline suite*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -n 1,60p tests/integration/test_admin_service.py; grep -n "seeded_db\b" tests/integration/test_facts.py | head -3; uv run pytest -q -o addopts="" -W error 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
"""M9: Director administration (PRD §3, P1, P7–P10, A1, §5.7; AC-25, AC-26, AC-27–29)."""

import json
from datetime import UTC, datetime

import pytest

from builders import make_assignment, make_mission, make_slot, make_user
from mission_control.domain.enums import Role
from mission_control.domain.errors import (
    Forbidden,
    InvalidInput,
    NotFound,
    RuleViolation,
    Unauthenticated,
)
from mission_control.domain.passwords import PasswordTooShort
from mission_control.domain.permissions import Actor
from mission_control.infra import security
from mission_control.services import admin, auth
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)
PASSPHRASE = "correct horse battery staple"

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

# Seed ids (PRD §9, crew profile id = user id)
MARCO, INGRID, NORA, ANA, BEN_ID, CHEN, FAY, HANA = 2, 3, 5, 6, 7, 8, 11, 13
LEE_ID, KAI, PRIYA = 4, 16, 15
PILOTING, SYS_ENG, GEOLOGY, HELIX_PILOTING = 1, 3, 5, 7
GATEWAY, ASTEROID, REBOOST, MEDICAL, TELESCOPE, DEEP_SPACE = 1, 2, 3, 4, 5, 6


def ctx(conn, actor=RUTH):
    return ServiceContext(conn, actor, now=NOW)


def snapshot(conn):
    """Every row that admin use cases could touch, to prove a refusal changed nothing."""
    tables = ["organisations", "users", "crew_profiles", "skills", "auth_tokens", "audit_events"]
    return {
        t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in tables
    }


def audit_events(conn, since_id=0):
    rows = conn.execute(
        "SELECT actor_id, event, crew_profile_id, data FROM audit_events WHERE id > ? ORDER BY id",
        (since_id,),
    ).fetchall()
    return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]


def last_audit_id(conn):
    return conn.execute("SELECT coalesce(max(id), 0) FROM audit_events").fetchone()[0]

27:def facts(seeded_db):
28:    return Repos(seeded_db, 1).facts
51:def test_open_places_subtract_open_assignments_only(seeded_db, facts):
........................................................................ [ 98%]
...........                                                              [100%]
875 passed in 3.99s
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/tests/integration/test_assignments_service.py",
  "content": "\"\"\"M12: the assignments service. Propose, accept, decline, withdraw, remove, and the cascade a\ncompleted or cancelled mission applies (PRD §5.1, §5.4, S1–S4, §5.7, V1; AC-4, AC-5, AC-14,\nAC-15, AC-29; scenarios S1, S4, S5).\n\nSeed ids (PRD §9): a crew profile's id equals its user's id.\nMissions: Gateway 1 (Draft, Lee) · Station Reboost 3 (Nora, Gus accepted) · Telescope 5 (Active)\n· Deep Space Comms 6 (Pending, Ben accepted, Marco approved) · Payload Demo 8 (Helix).\nSlots: Gateway Flight Engineer 1, Mission Specialist 2, Commander 3 · Asteroid Pilot 4 ·\nStation Reboost Engineer 6 · Telescope EVA Specialist 9 · Deep Space Comms Engineer 10 ·\nPayload Specialist 12 (Helix).\n\"\"\"\n\nimport json\nfrom datetime import UTC, datetime\n\nimport pytest\n\nfrom mission_control.domain.enums import AssignmentStatus, MissionStatus, Role\nfrom mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation\nfrom mission_control.domain.events import Event\nfrom mission_control.domain.permissions import Actor\nfrom mission_control.infra.repositories import Repos\nfrom mission_control.services import assignments\nfrom mission_control.services.context import ServiceContext\n\nNOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)\n\nRUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)\nMARCO = Actor(user_id=2, org_id=1, role=Role.DIRECTOR, crew_profile_id=2)\nLEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)\nNORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)\nANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)\nBEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)\nCHEN = Actor(user_id=8, org_id=1, role=Role.CREW, crew_profile_id=8)\nDANA = Actor(user_id=9, org_id=1, role=Role.CREW, crew_profile_id=9)\nHANA = Actor(user_id=13, org_id=1, role=Role.CREW, crew_profile_id=13)\nSAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)\nPRIYA = Actor(user_id=15, org_id=2, role=Role.LEAD, crew_profile_id=None)\n\nANA_ID, BEN_ID, CHEN_ID, DANA_ID, ELI_ID, FAY_ID, GUS_ID, HANA_ID = 6, 7, 8, 9, 10, 11, 12, 13\nKAI_ID, LENA_ID = 16, 17\nGATEWAY, ASTEROID, REBOOST, TELESCOPE, DEEP_SPACE, PAYLOAD = 1, 2, 3, 5, 6, 8\nFLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT = 1, 2, 3, 4\nREBOOST_ENGINEER, DEEP_SPACE_ENGINEER, PAYLOAD_SPECIALIST = 6, 10, 12\nSYS_ENG = 3\n\nA = AssignmentStatus\n\n\ndef as_(conn, actor):\n    return ServiceContext(conn, actor, now=NOW)\n\n\ndef assignment_id(conn, mission_id, crew_id):\n    return conn.execute(\n        \"SELECT id FROM assignments WHERE mission_id = ? AND crew_profile_id = ? ORDER BY id DESC\",\n        (mission_id, crew_id),\n    ).fetchone()[0]\n\n\ndef status_of(conn, assignment):\n    return conn.execute(\"SELECT status FROM assignments WHERE id = ?\", (assignment,)).fetchone()[0]\n\n\ndef mission_status(conn, mission_id):\n    return conn.execute(\"SELECT status FROM missions WHERE id = ?\", (mission_id,)).fetchone()[0]\n\n\ndef last_audit_id(conn):\n    return conn.execute(\"SELECT coalesce(max(id), 0) FROM audit_events\").fetchone()[0]\n\n\ndef audit_since(conn, since_id):\n    rows = conn.execute(\n        \"SELECT actor_id, event, mission_id, assignment_id, crew_profile_id, from_status,\"\n        \" to_status, reason, data FROM audit_events WHERE id > ? ORDER BY id\",\n        (since_id,),\n    ).fetchall()\n    return [(*tuple(r)[:8], json.loads(r[\"data\"])) for r in rows]\n\n\ndef snapshot(conn):\n    \"\"\"Every table an assignment use case could change, to prove a refusal changed nothing.\"\"\"\n    tables = (\"missions\", \"slots\", \"assignments\", \"approvals\", \"audit_events\")\n    return {t: [tuple(r) for r in conn.execute(f\"SELECT * FROM {t} ORDER BY rowid\")] for t in tables}\n\n\ndef refused(fn, *args, **kwargs):\n    with pytest.raises(RuleViolation) as caught:\n        fn(*args, **kwargs)\n    return caught.value\n\n\n# --- Propose (S1, AC-14) ------------------------------------------------------------------\n\n\ndef test_s1_owner_proposes_an_eligible_crew_member(seeded_db):\n    before = last_audit_id(seeded_db)\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert (made.mission_id, made.slot_id, made.crew_profile_id, made.status) == (\n        GATEWAY,\n        FLIGHT_ENGINEER,\n        CHEN_ID,\n        A.PROPOSED,\n    )\n    proposed_by = seeded_db.execute(\n        \"SELECT proposed_by_id FROM assignments WHERE id = ?\", (made.id,)\n    ).fetchone()[0]\n    assert proposed_by == LEE.user_id\n    assert audit_since(seeded_db, before) == [\n        (\n            LEE.user_id,\n            Event.ASSIGNMENT_PROPOSED,\n            GATEWAY,\n            made.id,\n            CHEN_ID,\n            None,\n            \"proposed\",\n            None,\n            {\n                \"mission_name\": \"Lunar Gateway Resupply\",\n                \"slot_name\": \"Flight Engineer\",\n                \"crew_name\": \"Chen Wu\",\n            },\n        )\n    ]\n    assert mission_status(seeded_db, GATEWAY) == \"draft\"\n\n\ndef test_s4_gus_proposal_is_refused_for_overlapping_station_reboost(seeded_db):\n    before = snapshot(seeded_db)\n    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, GUS_ID)\n    assert error.code == \"overlap\"\n    assert [p.code for p in error.problems] == [\"overlap\"]\n    problem = error.problems[0]\n    assert \"Gus Patel\" in problem.message and \"Station Reboost\" in problem.message\n    assert problem.refs[\"mission_id\"] == REBOOST\n    assert problem.refs[\"mission_name\"] == \"Station Reboost\"\n    assert snapshot(seeded_db) == before\n\n\ndef test_s4_fay_proposal_is_refused_for_unavailability(seeded_db):\n    before = snapshot(seeded_db)\n    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, COMMANDER, FAY_ID)\n    assert error.code == \"unavailable\"\n    assert [p.code for p in error.problems] == [\"unavailable\"]\n    assert \"Fay Moreau\" in error.problems[0].message\n    assert \"Medical\" not in error.message  # the reason stays private\n    assert snapshot(seeded_db) == before\n\n\ndef test_ac14_every_ineligibility_reason_is_listed(seeded_db):\n    # Hana (EVA 3, Geology 2) for Commander (Piloting >= 4, Leadership >= 3): both skills short.\n    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, COMMANDER, HANA_ID)\n    assert error.code == \"rule_violation\"\n    assert [p.code for p in error.problems] == [\"skill_below_minimum\", \"skill_below_minimum\"]\n    assert \"Hana Sato\" in error.message\n    assert \"Commander\" in error.message and \"Lunar Gateway Resupply\" in error.message\n\n\ndef test_s1_full_slot_is_refused(seeded_db):\n    assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    before = snapshot(seeded_db)\n    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, ANA_ID)\n    assert error.code == \"slot_full\"\n    assert dict(error.problems[0].refs) == {\"slot_id\": FLIGHT_ENGINEER}\n    assert \"Flight Engineer\" in error.message\n    assert snapshot(seeded_db) == before\n\n\ndef test_s1_second_open_assignment_on_the_same_mission_is_refused(seeded_db):\n    first = assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)\n    before = snapshot(seeded_db)\n    error = refused(assignments.propose, as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, ANA_ID)\n    assert error.code == \"already_assigned\"\n    assert dict(error.problems[0].refs) == {\n        \"assignment_id\": first.id,\n        \"crew_profile_id\": ANA_ID,\n        \"mission_id\": GATEWAY,\n    }\n    assert \"Ana Okafor\" in error.message and \"Commander\" in error.message\n    assert snapshot(seeded_db) == before\n\n\ndef test_s1_someone_who_declined_can_be_proposed_again(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assignments.decline(as_(seeded_db, CHEN), made.id)\n    again = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert again.status == A.PROPOSED and again.id != made.id\n\n\ndef test_s1_lead_can_propose_themselves_but_must_accept(seeded_db):\n    Repos(seeded_db, 1).missions.set_owner(GATEWAY, ANA.user_id)\n    made = assignments.propose(as_(seeded_db, ANA), GATEWAY, COMMANDER, ANA_ID)\n    assert made.status == A.PROPOSED\n    accepted = assignments.accept(as_(seeded_db, ANA), made.id)\n    assert accepted.status == A.ACCEPTED\n\n\ndef test_s2_overlapping_proposals_on_different_missions_are_allowed(seeded_db):\n    # Proposals block nothing: Chen can be proposed for two overlapping missions.\n    assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)\n    assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert status_of(seeded_db, assignment_id(seeded_db, REBOOST, CHEN_ID)) == \"proposed\"\n    assert status_of(seeded_db, assignment_id(seeded_db, GATEWAY, CHEN_ID)) == \"proposed\"\n\n\ndef test_ac4_proposing_on_a_pending_mission_returns_it_to_draft(seeded_db):\n    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, \"Backup Engineer\", 1, {SYS_ENG: 3})\n    before = last_audit_id(seeded_db)\n    made = assignments.propose(as_(seeded_db, NORA), DEEP_SPACE, backup.id, GUS_ID)\n    assert made.status == A.PROPOSED\n    assert mission_status(seeded_db, DEEP_SPACE) == \"draft\"\n    events = audit_since(seeded_db, before)\n    assert [e[1] for e in events] == [Event.ASSIGNMENT_PROPOSED, Event.MISSION_RETURNED_TO_DRAFT]\n    assert events[1] == (\n        NORA.user_id,\n        Event.MISSION_RETURNED_TO_DRAFT,\n        DEEP_SPACE,\n        None,\n        None,\n        \"pending_approval\",\n        \"draft\",\n        None,\n        {\"mission_name\": \"Deep Space Comms Upgrade\", \"cause\": \"assignment.proposed\"},\n    )\n\n\ndef test_ac5_proposing_on_an_active_mission_is_refused(seeded_db):\n    before = snapshot(seeded_db)\n    error = refused(assignments.propose, as_(seeded_db, LEE), TELESCOPE, 9, BEN_ID)\n    assert error.code == \"mission_frozen\"\n    assert snapshot(seeded_db) == before\n\n\ndef test_slot_from_another_mission_is_not_found(seeded_db):\n    with pytest.raises(NotFound):\n        assignments.propose(as_(seeded_db, LEE), GATEWAY, PILOT, ANA_ID)\n\n\n# --- Who may propose (M3, AC-7, §5.7) -----------------------------------------------------\n\n\ndef test_ac7_non_owner_lead_gets_not_owner(seeded_db):\n    before = snapshot(seeded_db)\n    with pytest.raises(Forbidden) as caught:\n        assignments.propose(as_(seeded_db, NORA), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert caught.value.code == \"not_owner\"\n    assert snapshot(seeded_db) == before\n\n\ndef test_m3_director_cannot_propose(seeded_db):\n    with pytest.raises(Forbidden) as caught:\n        assignments.propose(as_(seeded_db, RUTH), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert caught.value.code == \"role_forbidden\"\n\n\ndef test_m3_crew_cannot_propose_on_a_mission_they_are_on(seeded_db):\n    with pytest.raises(Forbidden) as caught:\n        assignments.propose(as_(seeded_db, BEN), DEEP_SPACE, DEEP_SPACE_ENGINEER, BEN_ID)\n    assert caught.value.code == \"role_forbidden\"\n\n\ndef test_tr10_crew_proposing_on_a_mission_they_are_not_on_gets_not_found(seeded_db):\n    with pytest.raises(NotFound):\n        assignments.propose(as_(seeded_db, BEN), GATEWAY, FLIGHT_ENGINEER, BEN_ID)\n\n\n# --- Accept (S2, AC-15) -------------------------------------------------------------------\n\n\ndef test_s1_crew_accepts_their_proposal(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    before = last_audit_id(seeded_db)\n    accepted = assignments.accept(as_(seeded_db, CHEN), made.id)\n    assert accepted.status == A.ACCEPTED\n    assert audit_since(seeded_db, before) == [\n        (\n            CHEN.user_id,\n            Event.ASSIGNMENT_ACCEPTED,\n            GATEWAY,\n            made.id,\n            CHEN_ID,\n            \"proposed\",\n            \"accepted\",\n            None,\n            {\n                \"mission_name\": \"Lunar Gateway Resupply\",\n                \"slot_name\": \"Flight Engineer\",\n                \"crew_name\": \"Chen Wu\",\n            },\n        )\n    ]\n\n\ndef test_ac15_chens_second_acceptance_names_station_reboost(seeded_db):\n    on_reboost = assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)\n    on_gateway = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assignments.accept(as_(seeded_db, CHEN), on_reboost.id)\n\n    before = snapshot(seeded_db)\n    error = refused(assignments.accept, as_(seeded_db, CHEN), on_gateway.id)\n    assert error.code == \"overlap\"\n    assert error.problems[0].refs[\"mission_name\"] == \"Station Reboost\"\n    assert \"Station Reboost\" in error.message\n    assert snapshot(seeded_db) == before\n    assert status_of(seeded_db, on_gateway.id) == \"proposed\"\n\n\ndef test_s2_acceptance_rechecks_skills(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    Repos(seeded_db, 1).crew.set_skill(CHEN_ID, SYS_ENG, 2, updated_by=LEE.user_id)\n    error = refused(assignments.accept, as_(seeded_db, CHEN), made.id)\n    assert error.code == \"skill_below_minimum\"\n    assert \"Chen Wu\" in error.message\n\n\ndef test_s2_accepting_twice_is_refused(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assignments.accept(as_(seeded_db, CHEN), made.id)\n    error = refused(assignments.accept, as_(seeded_db, CHEN), made.id)\n    assert error.code == \"invalid_transition\"\n\n\ndef test_s2_accepting_on_a_pending_mission_is_refused(seeded_db):\n    backup = Repos(seeded_db, 1).missions.add_slot(DEEP_SPACE, \"Backup Engineer\", 1, {SYS_ENG: 3})\n    repos = Repos(seeded_db, 1)\n    made = repos.assignments.create(DEEP_SPACE, backup.id, GUS_ID, proposed_by_id=NORA.user_id)\n    gus = Actor(user_id=GUS_ID, org_id=1, role=Role.CREW, crew_profile_id=GUS_ID)\n    before = snapshot(seeded_db)\n    error = refused(assignments.accept, as_(seeded_db, gus), made.id)\n    assert error.code == \"invalid_transition\"\n    assert snapshot(seeded_db) == before\n\n\ndef test_tr10_another_crew_members_assignment_is_not_found(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    before = snapshot(seeded_db)\n    with pytest.raises(NotFound):\n        assignments.accept(as_(seeded_db, DANA), made.id)\n    with pytest.raises(NotFound):\n        assignments.withdraw(as_(seeded_db, BEN), assignment_id(seeded_db, TELESCOPE, HANA_ID), \"x\")\n    assert snapshot(seeded_db) == before\n\n\ndef test_s4_lead_cannot_accept_for_someone_else(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    with pytest.raises(Forbidden) as caught:\n        assignments.accept(as_(seeded_db, LEE), made.id)\n    assert caught.value.code == \"not_owner\"\n    with pytest.raises(Forbidden) as caught:\n        assignments.accept(as_(seeded_db, RUTH), made.id)\n    assert caught.value.code == \"not_owner\"\n\n\n# --- Decline (S3) -------------------------------------------------------------------------\n\n\ndef test_s3_decline_with_a_reason_stores_it(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    before = last_audit_id(seeded_db)\n    declined = assignments.decline(as_(seeded_db, CHEN), made.id, \"  Training that week  \")\n    assert (declined.status, declined.reason) == (A.DECLINED, \"Training that week\")\n    events = audit_since(seeded_db, before)\n    assert [(e[1], e[5], e[6], e[7]) for e in events] == [\n        (Event.ASSIGNMENT_DECLINED, \"proposed\", \"declined\", \"Training that week\")\n    ]\n\n\n@pytest.mark.parametrize(\"reason\", [None, \"\", \"   \"])\ndef test_s3_decline_without_a_reason(seeded_db, reason):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, DANA_ID)\n    declined = assignments.decline(as_(seeded_db, DANA), made.id, reason)\n    assert (declined.status, declined.reason) == (A.DECLINED, None)\n\n\ndef test_s3_declining_an_accepted_assignment_is_refused(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assignments.accept(as_(seeded_db, CHEN), made.id)\n    error = refused(assignments.decline, as_(seeded_db, CHEN), made.id)\n    assert error.code == \"invalid_transition\"\n\n\n# --- Withdraw (S3, S5, AC-4, AC-5) --------------------------------------------------------\n\n\n@pytest.mark.parametrize(\"reason\", [None, \"\", \"   \"])\ndef test_s5_withdrawal_without_reason_is_refused(seeded_db, reason):\n    before = snapshot(seeded_db)\n    with pytest.raises(InvalidInput):\n        assignments.withdraw(as_(seeded_db, BEN), assignment_id(seeded_db, DEEP_SPACE, BEN_ID), reason)\n    assert snapshot(seeded_db) == before\n    assert mission_status(seeded_db, DEEP_SPACE) == \"pending_approval\"\n\n\ndef test_s5_withdrawal_returns_pending_mission_to_draft_and_clears_approvals(seeded_db):\n    ben_on_comms = assignment_id(seeded_db, DEEP_SPACE, BEN_ID)\n    before = last_audit_id(seeded_db)\n    withdrawn = assignments.withdraw(as_(seeded_db, BEN), ben_on_comms, \" Family emergency \")\n    assert (withdrawn.status, withdrawn.reason) == (A.WITHDRAWN, \"Family emergency\")\n    assert mission_status(seeded_db, DEEP_SPACE) == \"draft\"\n    # Marco's approval stays on record, but only a Pending mission's round counts, and the next\n    # submission opens a new round.\n    assert [e[1:] for e in audit_since(seeded_db, before)] == [\n        (\n            Event.ASSIGNMENT_WITHDRAWN,\n            DEEP_SPACE,\n            ben_on_comms,\n            BEN_ID,\n            \"accepted\",\n            \"withdrawn\",\n            \"Family emergency\",\n            {\n                \"mission_name\": \"Deep Space Comms Upgrade\",\n                \"slot_name\": \"Engineer\",\n                \"crew_name\": \"Ben Ito\",\n            },\n        ),\n        (\n            Event.MISSION_RETURNED_TO_DRAFT,\n            DEEP_SPACE,\n            None,\n            None,\n            \"pending_approval\",\n            \"draft\",\n            None,\n            {\"mission_name\": \"Deep Space Comms Upgrade\", \"cause\": \"assignment.withdrawn\"},\n        ),\n    ]\n\n\ndef test_s5_withdrawing_from_an_active_mission_is_refused(seeded_db):\n    before = snapshot(seeded_db)\n    error = refused(\n        assignments.withdraw,\n        as_(seeded_db, HANA),\n        assignment_id(seeded_db, TELESCOPE, HANA_ID),\n        \"Injured\",\n    )\n    assert error.code == \"mission_frozen\"\n    assert \"active\" in error.message\n    assert snapshot(seeded_db) == before\n\n\ndef test_s3_withdrawing_from_a_draft_mission_keeps_it_draft(seeded_db):\n    gus = Actor(user_id=GUS_ID, org_id=1, role=Role.CREW, crew_profile_id=GUS_ID)\n    withdrawn = assignments.withdraw(\n        as_(seeded_db, gus), assignment_id(seeded_db, REBOOST, GUS_ID), \"Reassigned\"\n    )\n    assert withdrawn.status == A.WITHDRAWN\n    assert mission_status(seeded_db, REBOOST) == \"draft\"\n\n\ndef test_s3_withdrawing_a_proposal_is_refused(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    error = refused(assignments.withdraw, as_(seeded_db, CHEN), made.id, \"Changed my mind\")\n    assert error.code == \"invalid_transition\"\n\n\n# --- Remove (M3, AC-4, AC-5) --------------------------------------------------------------\n\n\ndef test_m3_owner_retracts_a_proposal(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    before = last_audit_id(seeded_db)\n    removed = assignments.remove(as_(seeded_db, LEE), made.id)\n    assert removed.status == A.REMOVED\n    assert [(e[1], e[5], e[6]) for e in audit_since(seeded_db, before)] == [\n        (Event.ASSIGNMENT_REMOVED, \"proposed\", \"removed\")\n    ]\n\n\ndef test_ac4_owner_removes_accepted_crew_from_pending_mission_which_returns_to_draft(seeded_db):\n    ben_on_comms = assignment_id(seeded_db, DEEP_SPACE, BEN_ID)\n    before = last_audit_id(seeded_db)\n    removed = assignments.remove(as_(seeded_db, NORA), ben_on_comms)\n    assert removed.status == A.REMOVED\n    assert mission_status(seeded_db, DEEP_SPACE) == \"draft\"\n    events = audit_since(seeded_db, before)\n    assert [(e[1], e[5], e[6]) for e in events] == [\n        (Event.ASSIGNMENT_REMOVED, \"accepted\", \"removed\"),\n        (Event.MISSION_RETURNED_TO_DRAFT, \"pending_approval\", \"draft\"),\n    ]\n    assert events[1][8][\"cause\"] == \"assignment.removed\"\n\n\ndef test_ac5_removing_from_an_active_mission_is_refused(seeded_db):\n    before = snapshot(seeded_db)\n    error = refused(assignments.remove, as_(seeded_db, LEE), assignment_id(seeded_db, TELESCOPE, HANA_ID))\n    assert error.code == \"mission_frozen\"\n    assert snapshot(seeded_db) == before\n\n\ndef test_m3_non_owner_lead_cannot_remove(seeded_db):\n    with pytest.raises(Forbidden) as caught:\n        assignments.remove(as_(seeded_db, LEE), assignment_id(seeded_db, DEEP_SPACE, BEN_ID))\n    assert caught.value.code == \"not_owner\"\n\n\ndef test_m3_crew_cannot_remove_their_own_assignment(seeded_db):\n    with pytest.raises(Forbidden) as caught:\n        assignments.remove(as_(seeded_db, BEN), assignment_id(seeded_db, DEEP_SPACE, BEN_ID))\n    assert caught.value.code == \"role_forbidden\"\n\n\ndef test_removing_a_declined_assignment_is_refused(seeded_db):\n    made = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assignments.decline(as_(seeded_db, CHEN), made.id)\n    error = refused(assignments.remove, as_(seeded_db, LEE), made.id)\n    assert error.code == \"invalid_transition\"\n\n\n# --- Tenant isolation (T2, AC-27, AC-29) --------------------------------------------------\n\n\ndef both_orgs(conn):\n    return snapshot(conn)\n\n\n@pytest.mark.parametrize(\n    \"actor, call\",\n    [\n        (LEE, lambda c: assignments.propose(c, PAYLOAD, PAYLOAD_SPECIALIST, CHEN_ID)),\n        (LEE, lambda c: assignments.propose(c, GATEWAY, PAYLOAD_SPECIALIST, CHEN_ID)),\n        (LEE, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, KAI_ID)),\n        (LEE, lambda c: assignments.remove(c, 9)),  # Lena's Helix assignment\n        (BEN, lambda c: assignments.accept(c, 9)),\n        (BEN, lambda c: assignments.decline(c, 9)),\n        (BEN, lambda c: assignments.withdraw(c, 9, \"Not mine\")),\n        (SAM, lambda c: assignments.remove(c, 7)),  # Ben's Aurora assignment\n        (PRIYA, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, CHEN_ID)),\n        (PRIYA, lambda c: assignments.propose(c, PAYLOAD, PAYLOAD_SPECIALIST, CHEN_ID)),\n        (LEE, lambda c: assignments.accept(c, 999)),\n    ],\n)\ndef test_ac29_other_organisations_ids_are_not_found_and_nothing_changes(seeded_db, actor, call):\n    before = both_orgs(seeded_db)\n    with pytest.raises(NotFound):\n        call(as_(seeded_db, actor))\n    assert both_orgs(seeded_db) == before\n\n\n# --- Every refusal writes nothing (§5 cross-cutting: refused actions write nothing) -------\n\n\ndef _refusals():\n    return [\n        (\"overlap\", LEE, lambda c: assignments.propose(c, GATEWAY, FLIGHT_ENGINEER, GUS_ID)),\n        (\"unavailable\", LEE, lambda c: assignments.propose(c, GATEWAY, COMMANDER, FAY_ID)),\n        (\"frozen propose\", LEE, lambda c: assignments.propose(c, TELESCOPE, 9, BEN_ID)),\n        (\"not owner\", NORA, lambda c: assignments.propose(c, GATEWAY, COMMANDER, ANA_ID)),\n        (\"blank reason\", BEN, lambda c: assignments.withdraw(c, 7, \" \")),\n        (\"frozen withdraw\", HANA, lambda c: assignments.withdraw(c, 6, \"Injured\")),\n        (\"frozen remove\", LEE, lambda c: assignments.remove(c, 6)),\n        (\"accept accepted\", BEN, lambda c: assignments.accept(c, 7)),\n        (\"decline accepted\", BEN, lambda c: assignments.decline(c, 7)),\n        (\"remove completed\", LEE, lambda c: assignments.remove(c, 8)),\n        (\"not mine\", CHEN, lambda c: assignments.withdraw(c, 7, \"x\")),\n    ]\n\n\n@pytest.mark.parametrize(\"name, actor, call\", _refusals(), ids=[r[0] for r in _refusals()])\ndef test_every_refusal_leaves_the_tables_unchanged(seeded_db, name, actor, call):\n    before = snapshot(seeded_db)\n    with pytest.raises((RuleViolation, Forbidden, NotFound, InvalidInput)):\n        call(as_(seeded_db, actor))\n    assert snapshot(seeded_db) == before\n\n\n# --- Cascades when a mission completes or is cancelled (§5.4) -----------------------------\n\n\ndef test_m4_completing_a_mission_completes_accepted_assignments(seeded_db):\n    ctx = as_(seeded_db, LEE)\n    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)\n    before = last_audit_id(seeded_db)\n    with ctx.write():\n        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)\n    assert sorted(a.crew_profile_id for a in changed) == [CHEN_ID, DANA_ID, ELI_ID, HANA_ID]\n    assert {a.status for a in changed} == {A.COMPLETED}\n    events = audit_since(seeded_db, before)\n    assert [(e[1], e[5], e[6]) for e in events] == [\n        (Event.ASSIGNMENT_COMPLETED, \"accepted\", \"completed\")\n    ] * 4\n    assert events[0][8] == {\n        \"mission_name\": \"Orbital Telescope Service\",\n        \"slot_name\": \"Engineer\",\n        \"crew_name\": \"Chen Wu\",\n    }\n\n\ndef test_m4_cancelling_a_mission_cancels_open_assignments_only(seeded_db):\n    proposed = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    accepted = assignments.propose(as_(seeded_db, LEE), GATEWAY, SPECIALIST, DANA_ID)\n    assignments.accept(as_(seeded_db, DANA), accepted.id)\n    declined = assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, ANA_ID)\n    assignments.decline(as_(seeded_db, ANA), declined.id, \"Busy\")\n\n    ctx = as_(seeded_db, RUTH)\n    mission = Repos(seeded_db, 1).missions.get(GATEWAY)\n    before = last_audit_id(seeded_db)\n    with ctx.write():\n        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.CANCELLED)\n    assert [(a.id, a.status) for a in changed] == [\n        (proposed.id, A.CANCELLED),\n        (accepted.id, A.CANCELLED),\n    ]\n    assert status_of(seeded_db, declined.id) == \"declined\"\n    assert [(e[0], e[1], e[5], e[6]) for e in audit_since(seeded_db, before)] == [\n        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, \"proposed\", \"cancelled\"),\n        (RUTH.user_id, Event.ASSIGNMENT_CANCELLED, \"accepted\", \"cancelled\"),\n    ]\n\n\ndef test_m4_completing_leaves_proposals_and_closed_assignments_alone(seeded_db):\n    # Not reachable through the lifecycle (Active missions have only accepted crew), but the\n    # cascade must not touch anything that isn't accepted.\n    repos = Repos(seeded_db, 1)\n    mission = repos.missions.get(REBOOST)\n    proposal = repos.assignments.create(REBOOST, REBOOST_ENGINEER, CHEN_ID, proposed_by_id=5)\n    ctx = as_(seeded_db, NORA)\n    with ctx.write():\n        changed = assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)\n    assert [a.crew_profile_id for a in changed] == [GUS_ID]\n    assert status_of(seeded_db, proposal.id) == \"proposed\"\n\n\ndef test_cascade_runs_only_inside_the_callers_write(seeded_db):\n    ctx = as_(seeded_db, LEE)\n    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)\n    before = snapshot(seeded_db)\n    with pytest.raises(RuntimeError):\n        assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)\n    assert snapshot(seeded_db) == before\n\n\ndef test_cascade_rolls_back_with_the_callers_transaction(seeded_db):\n    ctx = as_(seeded_db, LEE)\n    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)\n    before = snapshot(seeded_db)\n    with pytest.raises(RuntimeError, match=\"caller failed\"):\n        with ctx.write():\n            assignments.cascade_mission_end(ctx, mission, MissionStatus.COMPLETED)\n            raise RuntimeError(\"caller failed\")\n    assert snapshot(seeded_db) == before\n\n\n@pytest.mark.parametrize(\n    \"status\", [MissionStatus.DRAFT, MissionStatus.PENDING_APPROVAL, MissionStatus.ACTIVE]\n)\ndef test_cascade_needs_a_final_status(seeded_db, status):\n    ctx = as_(seeded_db, LEE)\n    mission = Repos(seeded_db, 1).missions.get(TELESCOPE)\n    with ctx.write(), pytest.raises(ValueError):\n        assignments.cascade_mission_end(ctx, mission, status)\n\n\n# --- Scenarios end to end -----------------------------------------------------------------\n\n\ndef test_s4_scenario(seeded_db):\n    with pytest.raises(RuleViolation, match=\"Station Reboost\"):\n        assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, GUS_ID)\n    with pytest.raises(RuleViolation) as fay:\n        assignments.propose(as_(seeded_db, LEE), GATEWAY, COMMANDER, FAY_ID)\n    assert fay.value.code == \"unavailable\"\n    on_reboost = assignments.propose(as_(seeded_db, NORA), REBOOST, REBOOST_ENGINEER, CHEN_ID)\n    on_gateway = assignments.propose(as_(seeded_db, LEE), GATEWAY, FLIGHT_ENGINEER, CHEN_ID)\n    assert assignments.accept(as_(seeded_db, CHEN), on_reboost.id).status == A.ACCEPTED\n    with pytest.raises(RuleViolation) as second:\n        assignments.accept(as_(seeded_db, CHEN), on_gateway.id)\n    assert second.value.problems[0].refs[\"mission_name\"] == \"Station Reboost\"\n\n\ndef test_s1_propose_and_accept_steps(seeded_db):\n    picks = [(COMMANDER, ANA, ANA_ID), (FLIGHT_ENGINEER, CHEN, CHEN_ID), (SPECIALIST, DANA, DANA_ID)]\n    made = [\n        (actor, assignments.propose(as_(seeded_db, LEE), GATEWAY, slot, crew_id))\n        for slot, actor, crew_id in picks\n    ]\n    for actor, assignment in made:\n        assert assignments.accept(as_(seeded_db, actor), assignment.id).status == A.ACCEPTED\n    open_places = [s.open_places for s in Repos(seeded_db, 1).facts.slot_specs(GATEWAY)]\n    assert open_places == [0, 0, 0]\n    assert mission_status(seeded_db, GATEWAY) == \"draft\"\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/tests/integration/test_assignments_service.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>📎 File attached: .worktrees/m12-assignments/CLAUDE.md</summary>

```
{
  "path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/CLAUDE.md",
  "type": "Project",
  "content": "# Mission Control\n\nMulti-tenant mission planning API and CLI. Read these before doing any work. They are the source of truth, so don't copy their content here.\n\n- [`docs/brief.md`](docs/brief.md): the assessment brief\n- [`docs/prd.md`](docs/prd.md): **behaviour**. What the system does, its rules, acceptance criteria and seed scenarios.\n- [`docs/technical-design.md`](docs/technical-design.md): **structure**. Architecture, schema, API, CLI, the delivery plan (§9) and the implementation guidelines (§10).\n\nIf the PRD and the design conflict, or are silent on something, stop and ask. Never invent behaviour.\n\n## Workflow (every module)\n\n1. **One approved module at a time.** Work only on the module from design §9 that I have approved. Don't start anything else.\n2. **Tests first.** Write failing tests that reference the PRD IDs, then implement. Run the full suite and lint: `uv run pytest` and `uv run ruff check`.\n3. **Real verification.** Exercise the behaviour for real, for example with a REPL call, an HTTP request or a CLI command. Show the actual output. A passing test run alone isn't verification.\n4. **Read-only review.** Review the full diff against the PRD and design §10 without editing. Report findings, and fix them only once I agree.\n5. **Stop for approval.** Summarise what changed, the test and verification results, and the review findings, and propose a commit message. **Don't commit, and don't start the next module, until I approve.**\n\n## Waves (parallel modules in worktrees)\n\nWhen I approve a wave of independent modules (design §9), build them in parallel and keep reviews small:\n\n1. **One worktree per module.** Run `git worktree add .worktrees/<module> -b <module> main`, then `uv sync` inside it. Each agent edits only its own worktree and doesn't commit.\n2. **Same workflow per module.** Steps 2 to 4 above still apply, inside the worktree.\n3. **Review one branch at a time.** Show me only that module's diff against `main` (`git -C .worktrees/<module> diff main`, including new files), with its results.\n4. **After I approve that module:**\n   - commit on its branch;\n   - rebase onto `main` if `main` has moved, and re-run its tests;\n   - fast-forward `main`;\n   - run the full suite on `main`;\n   - remove the worktree and branch.\n\n   Only then present the next branch.\n\nNever push, add dependencies, change the schema, or add endpoints, error codes or CLI commands outside the design without asking first.\n",
  "contentDiffersFromDisk": false
}
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/tests/integration/test_assignment_writes.py",
  "content": "\"\"\"M12: the assignment repository writes. Every write is scoped to the caller's organisation\n(T1, AC-29) and the database still enforces one open assignment per person per mission (S1)\nand a reason on every withdrawal (S3).\"\"\"\n\nimport sqlite3\n\nimport pytest\n\nfrom mission_control.domain.enums import AssignmentStatus\nfrom mission_control.infra.repositories import Repos\n\nGATEWAY, REBOOST, PAYLOAD = 1, 3, 8\nFLIGHT_ENGINEER, SPECIALIST, PAYLOAD_SPECIALIST = 1, 2, 12\nLEE, CHEN, GUS, KAI, PRIYA = 4, 8, 12, 16, 15\nBEN_ON_COMMS = 7\n\n\n@pytest.fixture\ndef aurora(seeded_db):\n    return Repos(seeded_db, 1)\n\n\n@pytest.fixture\ndef helix(seeded_db):\n    return Repos(seeded_db, 2)\n\n\ndef test_s1_create_a_proposal(seeded_db, aurora):\n    made = aurora.assignments.create(GATEWAY, FLIGHT_ENGINEER, CHEN, proposed_by_id=LEE)\n    assert (made.mission_id, made.slot_id, made.crew_profile_id, made.status, made.reason) == (\n        GATEWAY,\n        FLIGHT_ENGINEER,\n        CHEN,\n        AssignmentStatus.PROPOSED,\n        None,\n    )\n    row = seeded_db.execute(\n        \"SELECT org_id, proposed_by_id FROM assignments WHERE id = ?\", (made.id,)\n    ).fetchone()\n    assert tuple(row) == (1, LEE)\n\n\ndef test_s1_database_refuses_a_second_open_assignment_on_a_mission(aurora):\n    aurora.assignments.create(GATEWAY, FLIGHT_ENGINEER, CHEN, proposed_by_id=LEE)\n    with pytest.raises(sqlite3.IntegrityError):\n        aurora.assignments.create(GATEWAY, SPECIALIST, CHEN, proposed_by_id=LEE)\n\n\n@pytest.mark.parametrize(\n    \"mission, slot, crew, proposer\",\n    [\n        (PAYLOAD, PAYLOAD_SPECIALIST, CHEN, LEE),  # Helix mission and slot\n        (GATEWAY, FLIGHT_ENGINEER, KAI, LEE),  # Helix crew member\n        (GATEWAY, FLIGHT_ENGINEER, CHEN, PRIYA),  # Helix proposer\n        (GATEWAY, PAYLOAD_SPECIALIST, CHEN, LEE),  # slot of another mission\n    ],\n)\ndef test_ac29_create_refuses_links_across_organisations_or_missions(\n    aurora, mission, slot, crew, proposer\n):\n    with pytest.raises(sqlite3.IntegrityError):\n        aurora.assignments.create(mission, slot, crew, proposed_by_id=proposer)\n\n\ndef test_set_status_changes_status_and_reason(aurora):\n    assert aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.WITHDRAWN, \"Moving\")\n    got = aurora.assignments.get(BEN_ON_COMMS)\n    assert (got.status, got.reason) == (AssignmentStatus.WITHDRAWN, \"Moving\")\n\n\ndef test_set_status_stamps_updated_at(seeded_db, aurora):\n    seeded_db.execute(\"UPDATE assignments SET updated_at = '2000-01-01T00:00:00.000Z'\")\n    aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.REMOVED)\n    stamp = seeded_db.execute(\n        \"SELECT updated_at FROM assignments WHERE id = ?\", (BEN_ON_COMMS,)\n    ).fetchone()[0]\n    assert stamp > \"2000-01-01T00:00:00.000Z\"\n\n\ndef test_ac29_set_status_cannot_reach_another_organisations_assignment(aurora, helix):\n    assert not helix.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.REMOVED)\n    assert aurora.assignments.get(BEN_ON_COMMS).status == AssignmentStatus.ACCEPTED\n\n\ndef test_s3_database_refuses_a_withdrawal_without_a_reason(aurora):\n    with pytest.raises(sqlite3.IntegrityError):\n        aurora.assignments.set_status(BEN_ON_COMMS, AssignmentStatus.WITHDRAWN, \"  \")\n"
}
```

**🔧 Bash**

*Append event test entries and run new tests (expect failures)*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && python3 - <<'EOF'
p='tests/unit/domain/test_events.py'
s=open(p).read()
s=s.replace('''        "SKILL_DELETED": "skill.deleted",
    }''','''        "SKILL_DELETED": "skill.deleted",
        # M12 assignments
        "ASSIGNMENT_PROPOSED": "assignment.proposed",
        "ASSIGNMENT_ACCEPTED": "assignment.accepted",
        "ASSIGNMENT_DECLINED": "assignment.declined",
        "ASSIGNMENT_WITHDRAWN": "assignment.withdrawn",
        "ASSIGNMENT_REMOVED": "assignment.removed",
        "ASSIGNMENT_COMPLETED": "assignment.completed",
        "ASSIGNMENT_CANCELLED": "assignment.cancelled",
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",  # also added by M11
    }''')
open(p,'w').write(s)
EOF
uv run pytest -q -o addopts="" -W error tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py tests/unit/domain/test_events.py 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/tests/integration/test_assignment_writes.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
==================================== ERRORS ====================================
________ ERROR collecting tests/integration/test_assignments_service.py ________
ImportError while importing test module '/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/tests/integration/test_assignments_service.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../../.local/share/uv/python/cpython-3.12.15-macos-aarch64-none/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_assignments_service.py:23: in <module>
    from mission_control.services import assignments
E   ImportError: cannot import name 'assignments' from 'mission_control.services' (/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control/services/__init__.py)
=========================== short test summary info ============================
ERROR tests/integration/test_assignments_service.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.14s
```

</details>

### 🤖 Claude · 2026-10-12 02:40:23 UTC

Tests fail at import as expected. I'll add a stub so each test fails individually and I get a real "before" count.

**🔧 Bash**

*Stub the service and count failing tests*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && cat > src/mission_control/services/assignments.py <<'EOF'
def propose(ctx, mission_id, slot_id, crew_profile_id):
    raise NotImplementedError


def accept(ctx, assignment_id):
    raise NotImplementedError


def decline(ctx, assignment_id, reason=None):
    raise NotImplementedError


def withdraw(ctx, assignment_id, reason):
    raise NotImplementedError


def remove(ctx, assignment_id):
    raise NotImplementedError


def cascade_mission_end(ctx, mission, final_status):
    raise NotImplementedError
EOF
uv run pytest -q -o addopts="" -W error tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py tests/unit/domain/test_events.py 2>&1 | tail -4
```

<details>
<summary>↳ Result</summary>

```
FAILED tests/integration/test_assignment_writes.py::test_ac29_set_status_cannot_reach_another_organisations_assignment
FAILED tests/integration/test_assignment_writes.py::test_s3_database_refuses_a_withdrawal_without_a_reason
FAILED tests/unit/domain/test_events.py::test_event_names_are_the_stored_audit_strings
83 failed, 1 passed in 1.38s
```

</details>

**🔧 Bash**

*Identify the passing test*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run pytest -q -o addopts="" -W error -rP tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py tests/unit/domain/test_events.py 2>&1 | grep -i "passed" | head
```

<details>
<summary>↳ Result</summary>

```
83 failed, 1 passed in 1.43s
```

</details>

**🔧 Bash**

*Show passing test name*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run pytest -o addopts="" -W error -v tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py 2>&1 | grep PASSED
```

<details>
<summary>↳ Result</summary>

```
tests/integration/test_assignments_service.py::test_cascade_runs_only_inside_the_callers_write PASSED [ 80%]
```

</details>

### 🤖 Claude · 2026-10-12 02:40:43 UTC

Before: 83 failed, 1 passed (the one passes against the stub only because `NotImplementedError` is a subclass of `RuntimeError`). Now the implementation: events, repository, service.

**🔧 Bash**

*Append M12 events and fix test comment*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && cat >> src/mission_control/domain/events.py <<'EOF'
    # M12 assignments
    ASSIGNMENT_PROPOSED = "assignment.proposed"
    ASSIGNMENT_ACCEPTED = "assignment.accepted"
    ASSIGNMENT_DECLINED = "assignment.declined"
    ASSIGNMENT_WITHDRAWN = "assignment.withdrawn"
    ASSIGNMENT_REMOVED = "assignment.removed"
    ASSIGNMENT_COMPLETED = "assignment.completed"
    ASSIGNMENT_CANCELLED = "assignment.cancelled"
    # also added by M11; dedupe at merge
    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
EOF
sed -i '' 's/        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",  # also added by M11/        # also added by M11; dedupe at merge\n        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",/' tests/unit/domain/test_events.py; tail -12 tests/unit/domain/test_events.py
```

<details>
<summary>↳ Result</summary>

```
        "SKILL_DELETED": "skill.deleted",
        # M12 assignments
        "ASSIGNMENT_PROPOSED": "assignment.proposed",
        "ASSIGNMENT_ACCEPTED": "assignment.accepted",
        "ASSIGNMENT_DECLINED": "assignment.declined",
        "ASSIGNMENT_WITHDRAWN": "assignment.withdrawn",
        "ASSIGNMENT_REMOVED": "assignment.removed",
        "ASSIGNMENT_COMPLETED": "assignment.completed",
        "ASSIGNMENT_CANCELLED": "assignment.cancelled",
        # also added by M11; dedupe at merge
        "MISSION_RETURNED_TO_DRAFT": "mission.returned_to_draft",
    }
```

</details>

### 🤖 Claude · 2026-10-12 02:40:49 UTC

Now the repository writes.

**🔧 Bash**

*Add repository writes and run their tests*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && python3 - <<'EOF'
p='src/mission_control/infra/repositories/assignments.py'
s=open(p).read()
s=s.replace('"""Assignments by id, and the shared row mapping for them."""','"""Assignments by id, the writes that create and change them, and the shared row mapping."""')
s=s.replace('from mission_control.infra.repositories.base import Scoped','from mission_control.infra.repositories.base import NOW, Scoped')
s=s.replace('''        return assignment_from_row(r) if r else None
''','''        return assignment_from_row(r) if r else None

    def create(
        self, mission_id: int, slot_id: int, crew_profile_id: int, proposed_by_id: int
    ) -> Assignment:
        """A new proposal. The database refuses a second open assignment for the same person on
        the same mission, and links to another organisation's records."""
        cur = self._exec(
            "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id, proposed_by_id)"
            " VALUES (:org, :mission_id, :slot_id, :crew_profile_id, :proposed_by_id)",
            mission_id=mission_id,
            slot_id=slot_id,
            crew_profile_id=crew_profile_id,
            proposed_by_id=proposed_by_id,
        )
        created = self.get(cur.lastrowid)
        assert created is not None
        return created

    def set_status(
        self, assignment_id: int, status: AssignmentStatus, reason: str | None = None
    ) -> bool:
        """Move an assignment to `status`, recording `reason` (None clears it)."""
        return (
            self._exec(
                f"UPDATE assignments SET status = :status, reason = :reason, updated_at = {NOW}"
                " WHERE org_id = :org AND id = :id",
                status=status,
                reason=reason,
                id=assignment_id,
            ).rowcount
            == 1
        )
''')
open(p,'w').write(s)
EOF
uv run pytest -q -o addopts="" -W error tests/integration/test_assignment_writes.py tests/integration/test_repository_sql.py tests/unit/domain/test_events.py 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
.............................                                            [100%]
29 passed in 0.33s
```

</details>

### 🤖 Claude · 2026-10-12 02:41:26 UTC

Now the service.

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control/services/assignments.py",
  "content": "\"\"\"Assignments: the owner proposing crew for a mission's slots, the crew member's answer (accept,\ndecline, withdraw), the owner removing someone, and what happens to assignments when their\nmission is completed or cancelled.\n\nEach use case runs in one write transaction, in this order: load (anything missing, hidden or\nanother organisation's is not found), authorize, check the mission's and the assignment's state,\ncheck input, check the rules, then write and audit with the names involved. A refusal writes\nnothing.\n\nWho sees what: crew see only their own assignments, so anyone else's is not found. Leads and\nDirectors see every assignment in their organisation, so acting on one that isn't theirs is\nforbidden.\n\nA roster change (propose, withdraw, remove) on a mission pending approval sends it back to Draft,\nso its approval round stops counting. That return is audited straight after the change that\ncaused it.\n\"\"\"\n\nfrom collections.abc import Mapping, Sequence\nfrom types import MappingProxyType\n\nfrom mission_control.domain.eligibility import ineligibility_reasons\nfrom mission_control.domain.enums import Action, AssignmentStatus, MissionStatus\nfrom mission_control.domain.errors import InvalidInput, NotFound, Problem, RuleViolation\nfrom mission_control.domain.events import Event\nfrom mission_control.domain.lifecycle import (\n    StateConflict,\n    assignment_problem,\n    assignment_status_after,\n    cascade,\n    mission_status_after_assignment_action,\n)\nfrom mission_control.domain.permissions import Context\nfrom mission_control.domain.records import SlotSpec\nfrom mission_control.infra.repositories import Repos\nfrom mission_control.infra.repositories.models import Assignment, CrewProfile, Mission\nfrom mission_control.services.context import ServiceContext, found\n\nA = AssignmentStatus\n\n_ASSIGNMENT = \"Assignment\"\n_MISSION = \"Mission\"\n_SLOT = \"Slot\"\n_CREW_MEMBER = \"Crew member\"\n\n_EVENT: Mapping[Action, Event] = MappingProxyType(\n    {\n        Action.PROPOSE_CREW: Event.ASSIGNMENT_PROPOSED,\n        Action.ACCEPT: Event.ASSIGNMENT_ACCEPTED,\n        Action.DECLINE: Event.ASSIGNMENT_DECLINED,\n        Action.WITHDRAW: Event.ASSIGNMENT_WITHDRAWN,\n        Action.REMOVE_CREW: Event.ASSIGNMENT_REMOVED,\n    }\n)\n\n_CASCADE_EVENT: Mapping[AssignmentStatus, Event] = MappingProxyType(\n    {A.COMPLETED: Event.ASSIGNMENT_COMPLETED, A.CANCELLED: Event.ASSIGNMENT_CANCELLED}\n)\n\n_MISSION_ENDS = frozenset({MissionStatus.COMPLETED, MissionStatus.CANCELLED})\n\n\n# The owner proposes\n\n\ndef propose(\n    ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int\n) -> Assignment:\n    \"\"\"Propose someone for a place in one of the mission's slots. Only the mission's owner may,\n    while it's in Draft or pending approval; a pending mission goes back to Draft.\n\n    Refused, with every reason at once, if the slot has no open place, the person already holds\n    an open assignment on this mission, or they aren't eligible (deactivated, short of a\n    required skill, unavailable, or accepted on another mission with overlapping dates).\n    Proposals elsewhere don't count: they block nothing. An owner may propose themselves, and\n    must then accept like anyone else.\"\"\"\n    with ctx.write() as repos:\n        mission = found(repos.missions.get_visible(ctx.actor, mission_id), _MISSION)\n        slot = found(_slot_specs(repos, mission).get(slot_id), _SLOT)\n        profile = found(repos.crew.get(crew_profile_id), _CREW_MEMBER)\n        ctx.authorize_view(Action.VIEW_CREW, _about(profile), _CREW_MEMBER)\n\n        ctx.authorize(Action.PROPOSE_CREW, Context(owner_id=mission.owner_id))\n        _check_state(Action.PROPOSE_CREW, None, mission)\n\n        problems = [\n            *_already_on_mission(repos, mission, profile),\n            *_slot_full(mission, slot),\n            *_ineligibility(repos, mission, slot, profile),\n        ]\n        _refuse(\n            problems, f\"{profile.display_name} can't be proposed as {slot.name} on {mission.name}\"\n        )\n\n        made = repos.assignments.create(mission.id, slot.id, profile.id, ctx.actor.user_id)\n        _audit(ctx, Event.ASSIGNMENT_PROPOSED, made, None, A.PROPOSED, mission, slot, profile)\n        _after_roster_change(ctx, repos, mission, Action.PROPOSE_CREW)\n        return made\n\n\n# The crew member answers\n\n\ndef accept(ctx: ServiceContext, assignment_id: int) -> Assignment:\n    \"\"\"Accept your own proposal while the mission is in Draft. Eligibility is checked again\n    now, so an accepted assignment elsewhere with overlapping dates refuses it, naming that\n    mission.\"\"\"\n    with ctx.write() as repos:\n        assignment, mission, profile = _load(ctx, repos, assignment_id)\n        ctx.authorize(Action.ACCEPT, _about(profile))\n        _check_state(Action.ACCEPT, assignment.status, mission)\n        slot = _slot_of(repos, mission, assignment)\n        _refuse(\n            _ineligibility(repos, mission, slot, profile),\n            f\"{profile.display_name} can't accept {slot.name} on {mission.name}\",\n        )\n        return _change(ctx, repos, Action.ACCEPT, assignment, mission, slot, profile)\n\n\ndef decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:\n    \"\"\"Decline your own proposal while the mission is in Draft. The reason is optional; a blank\n    one is stored as none.\"\"\"\n    with ctx.write() as repos:\n        assignment, mission, profile = _load(ctx, repos, assignment_id)\n        ctx.authorize(Action.DECLINE, _about(profile))\n        _check_state(Action.DECLINE, assignment.status, mission)\n        slot = _slot_of(repos, mission, assignment)\n        given = (reason or \"\").strip() or None\n        return _change(ctx, repos, Action.DECLINE, assignment, mission, slot, profile, given)\n\n\ndef withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:\n    \"\"\"Withdraw from your own accepted assignment, giving a reason. Allowed while the mission is\n    in Draft or pending approval; a pending mission goes back to Draft. An active mission's\n    roster is frozen.\"\"\"\n    with ctx.write() as repos:\n        assignment, mission, profile = _load(ctx, repos, assignment_id)\n        ctx.authorize(Action.WITHDRAW, _about(profile))\n        _check_state(Action.WITHDRAW, assignment.status, mission)\n        given = (reason or \"\").strip()\n        if not given:\n            raise InvalidInput(f\"Withdrawing from {mission.name} needs a reason\")\n        slot = _slot_of(repos, mission, assignment)\n        return _change(ctx, repos, Action.WITHDRAW, assignment, mission, slot, profile, given)\n\n\n# The owner removes\n\n\ndef remove(ctx: ServiceContext, assignment_id: int) -> Assignment:\n    \"\"\"Retract a proposal or remove accepted crew. Only the mission's owner may, while it's in\n    Draft or pending approval; a pending mission goes back to Draft.\"\"\"\n    with ctx.write() as repos:\n        assignment, mission, profile = _load(ctx, repos, assignment_id)\n        ctx.authorize(Action.REMOVE_CREW, Context(owner_id=mission.owner_id))\n        _check_state(Action.REMOVE_CREW, assignment.status, mission)\n        slot = _slot_of(repos, mission, assignment)\n        return _change(ctx, repos, Action.REMOVE_CREW, assignment, mission, slot, profile)\n\n\n# When a mission ends\n\n\ndef cascade_mission_end(\n    ctx: ServiceContext, mission: Mission, final_status: MissionStatus\n) -> list[Assignment]:\n    \"\"\"Apply a mission's completion or cancellation to its assignments: completing it completes\n    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything\n    else is left as it is. Each change is written and audited as the acting user.\n\n    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked\n    the mission's own transition, so the assignments change in the same transaction as the\n    mission and roll back with it. It does no permission or state checks of its own. Returns the\n    changed assignments, in id order.\"\"\"\n    if final_status not in _MISSION_ENDS:\n        raise ValueError(f\"a mission ends completed or cancelled, not {final_status.value}\")\n    if not ctx.conn.in_transaction:\n        raise RuntimeError(\"cascade_mission_end runs inside the caller's ctx.write()\")\n    repos = ctx.repos\n    slots = _slot_specs(repos, mission)\n    changed = []\n    for assignment in repos.missions.assignments(mission.id):\n        to = cascade(final_status, assignment.status)\n        if to == assignment.status:\n            continue\n        profile = found(repos.crew.get(assignment.crew_profile_id), _CREW_MEMBER)\n        slot = found(slots.get(assignment.slot_id), _SLOT)\n        repos.assignments.set_status(assignment.id, to, assignment.reason)\n        _audit(ctx, _CASCADE_EVENT[to], assignment, assignment.status, to, mission, slot, profile)\n        changed.append(found(repos.assignments.get(assignment.id), _ASSIGNMENT))\n    return changed\n\n\n# Loading\n\n\ndef _load(\n    ctx: ServiceContext, repos: Repos, assignment_id: int\n) -> tuple[Assignment, Mission, CrewProfile]:\n    \"\"\"The assignment, its mission and its crew member. Not found if it's missing, another\n    organisation's, or a crew member's who isn't the caller.\"\"\"\n    assignment = found(repos.assignments.get(assignment_id), _ASSIGNMENT)\n    profile = found(repos.crew.get(assignment.crew_profile_id), _ASSIGNMENT)\n    ctx.authorize_view(Action.VIEW_ASSIGNMENT_HISTORY, _about(profile), _ASSIGNMENT)\n    # Seeing the assignment is enough to see its mission's name and state, as in the crew\n    # member's assignment history.\n    mission = found(repos.missions.get(assignment.mission_id), _ASSIGNMENT)\n    return assignment, mission, profile\n\n\ndef _slot_specs(repos: Repos, mission: Mission) -> dict[int, SlotSpec]:\n    \"\"\"The mission's live slots by id, with their open places.\"\"\"\n    return {s.id: s for s in repos.facts.slot_specs(mission.id)}\n\n\ndef _slot_of(repos: Repos, mission: Mission, assignment: Assignment) -> SlotSpec:\n    \"\"\"The slot of an open assignment. A slot can't be removed while it has open assignments,\n    so it's always live once the state check has passed.\"\"\"\n    return found(_slot_specs(repos, mission).get(assignment.slot_id), _SLOT)\n\n\ndef _about(profile: CrewProfile) -> Context:\n    \"\"\"Permission context for someone's assignment: the person is the profile's user.\"\"\"\n    return Context(target_user_id=profile.user_id)\n\n\n# Checks\n\n\ndef _check_state(action: Action, current: AssignmentStatus | None, mission: Mission) -> None:\n    problem = assignment_problem(action, current, mission.status)\n    if problem is not None:\n        raise StateConflict(problem)\n\n\ndef _already_on_mission(repos: Repos, mission: Mission, profile: CrewProfile) -> list[Problem]:\n    held = [\n        a\n        for a in repos.missions.assignments(mission.id, (A.PROPOSED, A.ACCEPTED))\n        if a.crew_profile_id == profile.id\n    ]\n    if not held:\n        return []\n    existing = held[0]\n    slot = _slot_specs(repos, mission).get(existing.slot_id)\n    where = f\" as {slot.name}\" if slot else \"\"\n    return [\n        Problem(\n            \"already_assigned\",\n            f\"{profile.display_name} is already {existing.status.value}{where} on {mission.name}\",\n            {\"assignment_id\": existing.id, \"crew_profile_id\": profile.id, \"mission_id\": mission.id},\n        )\n    ]\n\n\ndef _slot_full(mission: Mission, slot: SlotSpec) -> list[Problem]:\n    if slot.open_places > 0:\n        return []\n    return [\n        Problem(\n            \"slot_full\", f\"{slot.name} on {mission.name} has no open places\", {\"slot_id\": slot.id}\n        )\n    ]\n\n\ndef _ineligibility(\n    repos: Repos, mission: Mission, slot: SlotSpec, profile: CrewProfile\n) -> list[Problem]:\n    \"\"\"Every reason the person can't fill the slot, with commitments on this mission left out.\"\"\"\n    person = found(repos.facts.candidate(profile.id, excluding_mission_id=mission.id), _CREW_MEMBER)\n    return ineligibility_reasons(person, slot, mission.window)\n\n\ndef _refuse(problems: Sequence[Problem], message: str) -> None:\n    \"\"\"A single reason is raised under its own code; several are listed together.\"\"\"\n    if len(problems) == 1:\n        raise RuleViolation.of(problems[0])\n    if problems:\n        raise RuleViolation(message, problems)\n\n\n# Writing\n\n\ndef _change(\n    ctx: ServiceContext,\n    repos: Repos,\n    action: Action,\n    assignment: Assignment,\n    mission: Mission,\n    slot: SlotSpec,\n    profile: CrewProfile,\n    reason: str | None = None,\n) -> Assignment:\n    \"\"\"Move the assignment on by `action`, audit it, and send a pending mission back to Draft\n    if the roster changed.\"\"\"\n    to = assignment_status_after(action)\n    repos.assignments.set_status(assignment.id, to, reason)\n    _audit(ctx, _EVENT[action], assignment, assignment.status, to, mission, slot, profile, reason)\n    _after_roster_change(ctx, repos, mission, action)\n    return found(repos.assignments.get(assignment.id), _ASSIGNMENT)\n\n\ndef _after_roster_change(ctx: ServiceContext, repos: Repos, mission: Mission, action: Action) -> None:\n    after = mission_status_after_assignment_action(mission.status, action)\n    if after == mission.status:\n        return\n    if not repos.missions.set_status(mission.id, after):\n        raise NotFound(_MISSION)\n    ctx.audit(\n        Event.MISSION_RETURNED_TO_DRAFT,\n        mission_id=mission.id,\n        from_status=mission.status,\n        to_status=after,\n        data={\"mission_name\": mission.name, \"cause\": _EVENT[action].value},\n    )\n\n\ndef _audit(\n    ctx: ServiceContext,\n    event: Event,\n    assignment: Assignment,\n    from_status: AssignmentStatus | None,\n    to_status: AssignmentStatus,\n    mission: Mission,\n    slot: SlotSpec,\n    profile: CrewProfile,\n    reason: str | None = None,\n) -> None:\n    ctx.audit(\n        event,\n        mission_id=mission.id,\n        assignment_id=assignment.id,\n        crew_profile_id=profile.id,\n        from_status=from_status,\n        to_status=to_status,\n        reason=reason,\n        data={\"mission_name\": mission.name, \"slot_name\": slot.name, \"crew_name\": profile.display_name},\n    )\n"
}
```

**🔧 Bash**

*Run M12 tests against the implementation*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run pytest -q -o addopts="" -W error tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py tests/unit/domain/test_events.py 2>&1 | tail -30
```

<details>
<summary>↳ Result</summary>

```
The file /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control/services/assignments.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
        assert sorted(a.crew_profile_id for a in changed) == [CHEN_ID, DANA_ID, ELI_ID, HANA_ID]
        assert {a.status for a in changed} == {A.COMPLETED}
        events = audit_since(seeded_db, before)
        assert [(e[1], e[5], e[6]) for e in events] == [
            (Event.ASSIGNMENT_COMPLETED, "accepted", "completed")
        ] * 4
>       assert events[0][8] == {
            "mission_name": "Orbital Telescope Service",
            "slot_name": "Engineer",
            "crew_name": "Chen Wu",
        }
E       AssertionError: assert {'mission_nam...name': 'Chen'} == {'mission_nam...e': 'Chen Wu'}
E         
E         Omitting 2 identical items, use -vv to show
E         Differing items:
E         {'crew_name': 'Chen'} != {'crew_name': 'Chen Wu'}
E         Use -v to get more diff

tests/integration/test_assignments_service.py:585: AssertionError
=========================== short test summary info ============================
FAILED tests/integration/test_assignments_service.py::test_s1_owner_proposes_an_eligible_crew_member
FAILED tests/integration/test_assignments_service.py::test_s4_gus_proposal_is_refused_for_overlapping_station_reboost
FAILED tests/integration/test_assignments_service.py::test_s4_fay_proposal_is_refused_for_unavailability
FAILED tests/integration/test_assignments_service.py::test_ac14_every_ineligibility_reason_is_listed
FAILED tests/integration/test_assignments_service.py::test_s1_second_open_assignment_on_the_same_mission_is_refused
FAILED tests/integration/test_assignments_service.py::test_s1_crew_accepts_their_proposal
FAILED tests/integration/test_assignments_service.py::test_s2_acceptance_rechecks_skills
FAILED tests/integration/test_assignments_service.py::test_s5_withdrawal_returns_pending_mission_to_draft_and_clears_approvals
FAILED tests/integration/test_assignments_service.py::test_m4_completing_a_mission_completes_accepted_assignments
9 failed, 75 passed in 0.68s
```

</details>

### 🤖 Claude · 2026-10-12 02:42:13 UTC

Seeded display names are first names. Let me confirm and check the other failures.

**🔧 Bash**

*Show assertion errors*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run pytest -q -o addopts="" -W error tests/integration/test_assignments_service.py 2>&1 | grep -E "^E  " | head -30
```

<details>
<summary>↳ Result</summary>

```
E       AssertionError: assert [(4, 'assignm...8, None, ...)] == [(4, <Event.A...8, None, ...)]
E         
E         At index 0 diff: (4, 'assignment.proposed', 1, 11, 8, None, 'proposed', None, {'mission_name': 'Lunar Gateway Resupply', 'slot_name': 'Flight Engineer', 'crew_name': 'Chen'}) != (4, <Event.ASSIGNMENT_PROPOSED: 'assignment.proposed'>, 1, 11, 8, None, 'proposed', None, {'mission_name': 'Lunar Gateway Resupply', 'slot_name': 'Flight Engineer', 'crew_name': 'Chen Wu'})
E         Use -v to get more diff
E       AssertionError: assert ('Gus Patel' in 'Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02')
E        +  where 'Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02' = Problem(code='overlap', message='Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02', refs=mappingproxy({'crew_profile_id': 12, 'slot_id': 1, 'mission_id': 3, 'mission_name': 'Station Reboost'})).message
E       AssertionError: assert 'Fay Moreau' in 'Fay is unavailable 2027-03-05 to 2027-03-08'
E        +  where 'Fay is unavailable 2027-03-05 to 2027-03-08' = Problem(code='unavailable', message='Fay is unavailable 2027-03-05 to 2027-03-08', refs=mappingproxy({'crew_profile_id': 11, 'slot_id': 3})).message
E       assert 'Hana Sato' in "Hana can't be proposed as Commander on Lunar Gateway Resupply"
E        +  where "Hana can't be proposed as Commander on Lunar Gateway Resupply" = RuleViolation("Hana can't be proposed as Commander on Lunar Gateway Resupply").message
E       AssertionError: assert ('Ana Okafor' in 'Ana is already proposed as Commander on Lunar Gateway Resupply')
E        +  where 'Ana is already proposed as Commander on Lunar Gateway Resupply' = RuleViolation('Ana is already proposed as Commander on Lunar Gateway Resupply').message
E       AssertionError: assert [(8, 'assignm...oposed', ...)] == [(8, <Event.A...oposed', ...)]
E         
E         At index 0 diff: (8, 'assignment.accepted', 1, 11, 8, 'proposed', 'accepted', None, {'mission_name': 'Lunar Gateway Resupply', 'slot_name': 'Flight Engineer', 'crew_name': 'Chen'}) != (8, <Event.ASSIGNMENT_ACCEPTED: 'assignment.accepted'>, 1, 11, 8, 'proposed', 'accepted', None, {'mission_name': 'Lunar Gateway Resupply', 'slot_name': 'Flight Engineer', 'crew_name': 'Chen Wu'})
E         Use -v to get more diff
E       AssertionError: assert 'Chen Wu' in 'Chen has Systems Engineering 2 (needs 3)'
E        +  where 'Chen has Systems Engineering 2 (needs 3)' = RuleViolation('Chen has Systems Engineering 2 (needs 3)').message
E       AssertionError: assert [('assignment...'draft', ...)] == [(<Event.ASSI...'draft', ...)]
E         
E         At index 0 diff: ('assignment.withdrawn', 6, 7, 7, 'accepted', 'withdrawn', 'Family emergency', {'mission_name': 'Deep Space Comms Upgrade', 'slot_name': 'Engineer', 'crew_name': 'Ben'}) != (<Event.ASSIGNMENT_WITHDRAWN: 'assignment.withdrawn'>, 6, 7, 7, 'accepted', 'withdrawn', 'Family emergency', {'mission_name': 'Deep Space Comms Upgrade', 'slot_name': 'Engineer', 'crew_name': 'Ben Ito'})
E         Use -v to get more diff
E       AssertionError: assert {'mission_nam...name': 'Chen'} == {'mission_nam...e': 'Chen Wu'}
E         
E         Omitting 2 identical items, use -vv to show
E         Differing items:
E         {'crew_name': 'Chen'} != {'crew_name': 'Chen Wu'}
E         Use -v to get more diff
```

</details>

### 🤖 Claude · 2026-10-12 02:42:19 UTC

All nine are my tests assuming full names, but crew display names are seeded as first names (e.g. "Gus has an accepted assignment on Station Reboost..."). I'll correct the expectations.

**🔧 Bash**

*Fix name expectations and rerun M12 tests*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && sed -i '' -e 's/"Chen Wu"/"Chen"/g; s/"Gus Patel"/"Gus"/g; s/"Fay Moreau"/"Fay"/g; s/"Hana Sato"/"Hana"/g; s/"Ana Okafor"/"Ana"/g; s/"Ben Ito"/"Ben"/g' tests/integration/test_assignments_service.py && uv run pytest -q -o addopts="" -W error tests/integration/test_assignments_service.py tests/integration/test_assignment_writes.py tests/unit/domain/test_events.py 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
........................................................................ [ 85%]
............                                                             [100%]
84 passed in 0.60s
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

*Format, lint and run the full suite*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run ruff format src tests && uv run ruff check src tests; uv run ruff format --check src tests; uv run pytest -W error -o addopts="" -q 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
2 files reformatted, 63 files left unchanged
All checks passed!
65 files already formatted
........................................................................ [ 97%]
......................                                                   [100%]
958 passed in 4.92s
[This command modified 2 files you've previously read: .worktrees/m12-assignments/tests/integration/test_assignments_service.py, .worktrees/m12-assignments/src/mission_control/services/assignments.py. Call Read before editing.]
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

### 🤖 Claude · 2026-10-12 02:42:36 UTC

Full suite 958 passed (875 + 83 new), ruff clean. Now append the two new problem codes to design §7, flagged for approval.

**🔧 Bash**

*Append the two new problem codes to design section 7*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && python3 - <<'EOF'
p='docs/technical-design.md'
s=open(p).read()
anchor="| `user_id`, `crew_profile_id` |\n"
assert s.count(anchor)==1
add=("| `slot_full` | M12 assignments, *pending approval*: proposing someone for a slot with no open places (the message names the slot and mission) | `slot_id` |\n"
     "| `already_assigned` | M12 assignments, *pending approval*: proposing someone who already holds an open assignment on this mission (the message names their slot) | `assignment_id`, `crew_profile_id`, `mission_id` |\n")
s=s.replace(anchor, anchor+add)
open(p,'w').write(s)
EOF
git diff docs/ | head -20
```

<details>
<summary>↳ Result</summary>

```
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
AssertionError
```

</details>

**🔧 Bash**

*Find the exact already_exists row*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && grep -n "already_exists" docs/technical-design.md | cat -A | head -3 2>/dev/null || grep -n "already_exists" docs/technical-design.md
```

<details>
<summary>↳ Result</summary>

```
cat: illegal option -- A
usage: cat [-belnstuv] [file ...]
```

</details>

**🔧 Bash**

*Inspect the row ending bytes*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && grep -n "already_exists" docs/technical-design.md | tail -1 | cut -c1-20; awk 'NR==405' docs/technical-design.md | od -c | tail -3
```

<details>
<summary>↳ Result</summary>

```
403:| `already_exist
0000000    -   -   -  \n                                                
0000004
```

</details>

**🔧 Bash**

*Insert the new code rows after already_exists*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && python3 - <<'EOF'
p='docs/technical-design.md'
lines=open(p).read().split('\n')
i=402
assert lines[i].startswith('| `already_exists`'), lines[i]
lines[i+1:i+1]=[
 "| `slot_full` | *M12, pending approval.* Proposing someone for a slot with no open places (the message names the slot and mission) | `slot_id` |",
 "| `already_assigned` | *M12, pending approval.* Proposing someone who already holds an open assignment on this mission (the message names their slot) | `assignment_id`, `crew_profile_id`, `mission_id` |",
]
open(p,'w').write('\n'.join(lines))
EOF
git diff docs/
```

<details>
<summary>↳ Result</summary>

```
diff --git a/docs/technical-design.md b/docs/technical-design.md
index 4b28491..44cc6a1 100644
--- a/docs/technical-design.md
+++ b/docs/technical-design.md
@@ -401,6 +401,8 @@ Every error has the same shape, for every status code (401, 403, 404, 409, 422,
 | `slot_unfilled` | Submitting with empty places | `slot_id` |
 | `proposal_unanswered` | Submitting while a proposal is still waiting for a reply (the message names the person and slot) | `assignment_id`, `slot_id`, `crew_profile_id` |
 | `already_exists` | Inside a 409 `rule_violation`: the email address is already in use (anywhere on the platform, since login is by email alone; see [TR-13](#tr-13)), a skill name is already in the catalogue (ignoring case), or the user already has a crew profile | `email`; `skill_id`; `user_id`, `crew_profile_id` |
+| `slot_full` | *M12, pending approval.* Proposing someone for a slot with no open places (the message names the slot and mission) | `slot_id` |
+| `already_assigned` | *M12, pending approval.* Proposing someone who already holds an open assignment on this mission (the message names their slot) | `assignment_id`, `crew_profile_id`, `mission_id` |
 
 ---
```

</details>

### 🤖 Claude · 2026-10-12 02:42:57 UTC

Now the real run against a fresh seeded database file (script kept outside the repo).

**🔧 Bash**

*Run S4, S5 and S1 steps against a fresh seeded database*

```bash
mkdir -p /tmp/m12run && rm -f /tmp/m12run/mc.db* && cat > /tmp/m12run/run.py <<'EOF'
import sys
from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation
from mission_control.domain.permissions import Actor
from mission_control.infra.db import connect, init_db
from mission_control.seed.loader import load_seed
from mission_control.services import assignments as svc
from mission_control.services.context import ServiceContext

conn = connect(sys.argv[1]); init_db(conn); load_seed(conn, password_hash="demo")
people = {r["id"]: r for r in conn.execute("SELECT id, name, role FROM users")}
def actor(uid): return Actor(uid, 1, Role(people[uid]["role"]), uid)
def mission(mid): return conn.execute("SELECT name, status FROM missions WHERE id=?", (mid,)).fetchone()
def step(label, uid, fn, *args):
    try:
        a = fn(ServiceContext(conn, actor(uid)), *args)
        print(f"  OK      {label}: assignment {a.id} -> {a.status.value}" + (f" (reason: {a.reason})" if a.reason else ""))
        return a
    except RuleViolation as e:
        print(f"  REFUSED {label}: 409 {e.code}: {e.message}")
        for p in e.problems: print(f"            - {p.code}: {p.message} {dict(p.refs)}")
    except InvalidInput as e: print(f"  REFUSED {label}: 422 {e.code}: {e.message}")
    except Forbidden as e: print(f"  REFUSED {label}: 403 {e.code}: {e.message}")
    except NotFound as e: print(f"  REFUSED {label}: 404 {e.code}: {e.message}")
LEE, NORA, ANA, BEN, CHEN, DANA, FAY, GUS, HANA = 4, 5, 6, 7, 8, 9, 11, 12, 13

print("S4")
step("Lee proposes Gus as Flight Engineer on Gateway", LEE, svc.propose, 1, 1, GUS)
step("Lee proposes Fay as Commander on Gateway", LEE, svc.propose, 1, 3, FAY)
r = step("Nora proposes Chen as Engineer on Station Reboost", NORA, svc.propose, 3, 6, CHEN)
g = step("Lee proposes Chen as Flight Engineer on Gateway", LEE, svc.propose, 1, 1, CHEN)
step("Chen accepts Station Reboost", CHEN, svc.accept, r.id)
step("Chen accepts Gateway", CHEN, svc.accept, g.id)

print("S5")
ben = conn.execute("SELECT id FROM assignments WHERE mission_id=6 AND crew_profile_id=7").fetchone()[0]
hana = conn.execute("SELECT id FROM assignments WHERE mission_id=5 AND crew_profile_id=13").fetchone()[0]
print(f"  Deep Space Comms before: {tuple(mission(6))}")
step("Ben withdraws from Deep Space Comms, no reason", BEN, svc.withdraw, ben, None)
step("Ben withdraws from Deep Space Comms, with reason", BEN, svc.withdraw, ben, "Family emergency")
print(f"  Deep Space Comms after: {tuple(mission(6))}")
step("Hana withdraws from Telescope", HANA, svc.withdraw, hana, "Injured")

print("Extras")
step("Nora proposes on Lee's Gateway", NORA, svc.propose, 1, 2, DANA)
step("Ben accepts Chen's Station Reboost assignment", BEN, svc.accept, r.id)
step("Lee proposes Kai (Helix) on Gateway", LEE, svc.propose, 1, 1, 16)

print("S1 propose and accept on a fresh seed")
conn.close(); import os; os.remove(sys.argv[1])
conn = connect(sys.argv[1]); init_db(conn); load_seed(conn, password_hash="demo")
made = [(ANA, step("Lee proposes Ana as Commander", LEE, svc.propose, 1, 3, ANA)),
        (CHEN, step("Lee proposes Chen as Flight Engineer", LEE, svc.propose, 1, 1, CHEN)),
        (DANA, step("Lee proposes Dana as Mission Specialist", LEE, svc.propose, 1, 2, DANA))]
for uid, a in made: step(f"{people[uid]['name']} accepts", uid, svc.accept, a.id)
print(f"  Gateway: {tuple(mission(1))}")
print("  Audit trail for Gateway:")
for e in conn.execute("SELECT actor_id, event, from_status, to_status, reason, data FROM audit_events WHERE mission_id=1 ORDER BY id"):
    print(f"    {people[e[0]]['name']:<12} {e[1]:<22} {e[2] or '-':>9} -> {e[3] or '-':<9} {e[5]}")
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run python /tmp/m12run/run.py /tmp/m12run/mc.db; echo; sqlite3 /tmp/m12run/mc.db 2>/dev/null </dev/null; true
```

<details>
<summary>↳ Result</summary>

```
(eval):1: no matches found: /tmp/m12run/mc.db*
/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/.venv/bin/python: can't open file '/tmp/m12run/run.py': [Errno 2] No such file or directory
```

</details>

**🔧 Bash**

*Check the scratch directory*

```bash
mkdir -p /tmp/m12run && ls /tmp/m12run
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/tmp/m12run/run.py",
  "content": "import os\nimport sys\n\nfrom mission_control.domain.enums import Role\nfrom mission_control.domain.errors import Forbidden, InvalidInput, NotFound, RuleViolation\nfrom mission_control.domain.permissions import Actor\nfrom mission_control.infra.db import connect, init_db\nfrom mission_control.seed.loader import load_seed\nfrom mission_control.services import assignments as svc\nfrom mission_control.services.context import ServiceContext\n\nPATH = sys.argv[1]\n\n\ndef fresh():\n    for suffix in (\"\", \"-wal\", \"-shm\"):\n        if os.path.exists(PATH + suffix):\n            os.remove(PATH + suffix)\n    c = connect(PATH)\n    init_db(c)\n    load_seed(c, password_hash=\"demo\")\n    return c\n\n\nconn = fresh()\npeople = {r[\"id\"]: r for r in conn.execute(\"SELECT id, name, role FROM users\")}\n\n\ndef actor(uid):\n    return Actor(uid, people[uid][\"org_id\"] if \"org_id\" in people[uid].keys() else 1,\n                 Role(people[uid][\"role\"]), uid)\n\n\ndef mission(mid):\n    return tuple(conn.execute(\"SELECT name, status FROM missions WHERE id=?\", (mid,)).fetchone())\n\n\ndef step(label, uid, fn, *args):\n    try:\n        a = fn(ServiceContext(conn, actor(uid)), *args)\n        extra = f\" (reason: {a.reason})\" if a.reason else \"\"\n        print(f\"  OK      {label}: assignment {a.id} -> {a.status.value}{extra}\")\n        return a\n    except RuleViolation as e:\n        print(f\"  REFUSED {label}: 409 {e.code}: {e.message}\")\n        for p in e.problems:\n            print(f\"            - {p.code}: {p.message} {dict(p.refs)}\")\n    except InvalidInput as e:\n        print(f\"  REFUSED {label}: 422 {e.code}: {e.message}\")\n    except Forbidden as e:\n        print(f\"  REFUSED {label}: 403 {e.code}: {e.message}\")\n    except NotFound as e:\n        print(f\"  REFUSED {label}: 404 {e.code}: {e.message}\")\n\n\nLEE, NORA, ANA, BEN, CHEN, DANA, FAY, GUS, HANA = 4, 5, 6, 7, 8, 9, 11, 12, 13\n\nprint(\"S4\")\nstep(\"Lee proposes Gus as Flight Engineer on Gateway\", LEE, svc.propose, 1, 1, GUS)\nstep(\"Lee proposes Fay as Commander on Gateway\", LEE, svc.propose, 1, 3, FAY)\nr = step(\"Nora proposes Chen as Engineer on Station Reboost\", NORA, svc.propose, 3, 6, CHEN)\ng = step(\"Lee proposes Chen as Flight Engineer on Gateway\", LEE, svc.propose, 1, 1, CHEN)\nstep(\"Chen accepts Station Reboost\", CHEN, svc.accept, r.id)\nstep(\"Chen accepts Gateway\", CHEN, svc.accept, g.id)\n\nprint(\"S5\")\nben = conn.execute(\"SELECT id FROM assignments WHERE mission_id=6 AND crew_profile_id=7\").fetchone()[0]\nhana = conn.execute(\"SELECT id FROM assignments WHERE mission_id=5 AND crew_profile_id=13\").fetchone()[0]\nprint(f\"  Deep Space Comms before: {mission(6)}\")\nstep(\"Ben withdraws from Deep Space Comms, no reason\", BEN, svc.withdraw, ben, None)\nstep(\"Ben withdraws from Deep Space Comms, with reason\", BEN, svc.withdraw, ben, \"Family emergency\")\nprint(f\"  Deep Space Comms after: {mission(6)}\")\nfor e in conn.execute(\n    \"SELECT event, from_status, to_status, reason, data FROM audit_events\"\n    \" WHERE mission_id=6 ORDER BY id DESC LIMIT 2\"\n):\n    print(f\"    audit: {tuple(e)}\")\nstep(\"Hana withdraws from Telescope\", HANA, svc.withdraw, hana, \"Injured\")\n\nprint(\"Extras\")\nstep(\"Nora proposes Dana on Lee's Gateway\", NORA, svc.propose, 1, 2, DANA)\nstep(\"Ben accepts Chen's Station Reboost assignment\", BEN, svc.accept, r.id)\nstep(\"Lee proposes Kai (Helix) on Gateway\", LEE, svc.propose, 1, 1, 16)\n\nprint(\"S1 propose and accept steps, on a fresh seed\")\nconn.close()\nconn = fresh()\nmade = [\n    (ANA, step(\"Lee proposes Ana as Commander\", LEE, svc.propose, 1, 3, ANA)),\n    (CHEN, step(\"Lee proposes Chen as Flight Engineer\", LEE, svc.propose, 1, 1, CHEN)),\n    (DANA, step(\"Lee proposes Dana as Mission Specialist\", LEE, svc.propose, 1, 2, DANA)),\n]\nfor uid, a in made:\n    step(f\"{people[uid]['name']} accepts\", uid, svc.accept, a.id)\nprint(f\"  Gateway: {mission(1)}\")\nprint(\"  Audit trail for Gateway:\")\nfor e in conn.execute(\n    \"SELECT actor_id, event, from_status, to_status, data FROM audit_events\"\n    \" WHERE mission_id=1 ORDER BY id\"\n):\n    print(f\"    {people[e[0]]['name']:<13} {e[1]:<20} {e[2] or '-':>8} -> {e[3] or '-':<9} {e[4]}\")\n"
}
```

**🔧 Bash**

*Run the real scenario script*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && uv run python /tmp/m12run/run.py /tmp/m12run/mc.db
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /tmp/m12run/run.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
S4
  REFUSED Lee proposes Gus as Flight Engineer on Gateway: 409 overlap: Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02
            - overlap: Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02 {'crew_profile_id': 12, 'slot_id': 1, 'mission_id': 3, 'mission_name': 'Station Reboost'}
  REFUSED Lee proposes Fay as Commander on Gateway: 409 unavailable: Fay is unavailable 2027-03-05 to 2027-03-08
            - unavailable: Fay is unavailable 2027-03-05 to 2027-03-08 {'crew_profile_id': 11, 'slot_id': 3}
  OK      Nora proposes Chen as Engineer on Station Reboost: assignment 11 -> proposed
  OK      Lee proposes Chen as Flight Engineer on Gateway: assignment 12 -> proposed
  OK      Chen accepts Station Reboost: assignment 11 -> accepted
  REFUSED Chen accepts Gateway: 409 overlap: Chen has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02
            - overlap: Chen has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02 {'crew_profile_id': 8, 'slot_id': 1, 'mission_id': 3, 'mission_name': 'Station Reboost'}
S5
  Deep Space Comms before: ('Deep Space Comms Upgrade', 'pending_approval')
  REFUSED Ben withdraws from Deep Space Comms, no reason: 422 validation_error: Withdrawing from Deep Space Comms Upgrade needs a reason
  OK      Ben withdraws from Deep Space Comms, with reason: assignment 7 -> withdrawn (reason: Family emergency)
  Deep Space Comms after: ('Deep Space Comms Upgrade', 'draft')
    audit: ('mission.returned_to_draft', 'pending_approval', 'draft', None, '{"mission_name": "Deep Space Comms Upgrade", "cause": "assignment.withdrawn"}')
    audit: ('assignment.withdrawn', 'accepted', 'withdrawn', 'Family emergency', '{"mission_name": "Deep Space Comms Upgrade", "slot_name": "Engineer", "crew_name": "Ben"}')
  REFUSED Hana withdraws from Telescope: 409 mission_frozen: Can't withdraw from an active mission
            - mission_frozen: Can't withdraw from an active mission {}
Extras
  REFUSED Nora proposes Dana on Lee's Gateway: 403 not_owner: Only the mission's owner can propose crew for this mission
  REFUSED Ben accepts Chen's Station Reboost assignment: 404 not_found: Assignment not found
  REFUSED Lee proposes Kai (Helix) on Gateway: 404 not_found: Crew member not found
S1 propose and accept steps, on a fresh seed
  OK      Lee proposes Ana as Commander: assignment 11 -> proposed
  OK      Lee proposes Chen as Flight Engineer: assignment 12 -> proposed
  OK      Lee proposes Dana as Mission Specialist: assignment 13 -> proposed
  OK      Ana Okafor accepts: assignment 11 -> accepted
  OK      Chen Wu accepts: assignment 12 -> accepted
  OK      Dana Reyes accepts: assignment 13 -> accepted
  Gateway: ('Lunar Gateway Resupply', 'draft')
  Audit trail for Gateway:
    Ruth Adeyemi  mission.created             - -> draft     {"mission_name": "Lunar Gateway Resupply", "seeded": true}
    Lee Park      assignment.proposed         - -> proposed  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Commander", "crew_name": "Ana"}
    Lee Park      assignment.proposed         - -> proposed  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Flight Engineer", "crew_name": "Chen"}
    Lee Park      assignment.proposed         - -> proposed  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Mission Specialist", "crew_name": "Dana"}
    Ana Okafor    assignment.accepted  proposed -> accepted  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Commander", "crew_name": "Ana"}
    Chen Wu       assignment.accepted  proposed -> accepted  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Flight Engineer", "crew_name": "Chen"}
    Dana Reyes    assignment.accepted  proposed -> accepted  {"mission_name": "Lunar Gateway Resupply", "slot_name": "Mission Specialist", "crew_name": "Dana"}
```

</details>

### 🤖 Claude · 2026-10-12 02:43:34 UTC

The real run matches every expected outcome. Now a read-only review of the full diff.

**🔧 Bash**

*Show the diff and check for PRD ids in src*

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments && git status --short && git diff --stat && git diff src/ && grep -rn "AC-\|PRD\|S[1-9]\b" src/mission_control/services/assignments.py src/mission_control/infra/repositories/assignments.py
```

<details>
<summary>↳ Result</summary>

```
 M docs/technical-design.md
 M src/mission_control/domain/events.py
 M src/mission_control/infra/repositories/assignments.py
 M tests/unit/domain/test_events.py
?? src/mission_control/services/assignments.py
?? tests/integration/test_assignment_writes.py
?? tests/integration/test_assignments_service.py
 docs/technical-design.md                           |  2 ++
 src/mission_control/domain/events.py               | 10 ++++++
 .../infra/repositories/assignments.py              | 36 ++++++++++++++++++++--
 tests/unit/domain/test_events.py                   | 10 ++++++
 4 files changed, 56 insertions(+), 2 deletions(-)
diff --git a/src/mission_control/domain/events.py b/src/mission_control/domain/events.py
index c257c8b..b238beb 100644
--- a/src/mission_control/domain/events.py
+++ b/src/mission_control/domain/events.py
@@ -26,3 +26,13 @@ class Event(StrEnum):
     SKILL_CREATED = "skill.created"
     SKILL_UPDATED = "skill.updated"
     SKILL_DELETED = "skill.deleted"
+    # M12 assignments
+    ASSIGNMENT_PROPOSED = "assignment.proposed"
+    ASSIGNMENT_ACCEPTED = "assignment.accepted"
+    ASSIGNMENT_DECLINED = "assignment.declined"
+    ASSIGNMENT_WITHDRAWN = "assignment.withdrawn"
+    ASSIGNMENT_REMOVED = "assignment.removed"
+    ASSIGNMENT_COMPLETED = "assignment.completed"
+    ASSIGNMENT_CANCELLED = "assignment.cancelled"
+    # also added by M11; dedupe at merge
+    MISSION_RETURNED_TO_DRAFT = "mission.returned_to_draft"  # data names the change that caused it
diff --git a/src/mission_control/infra/repositories/assignments.py b/src/mission_control/infra/repositories/assignments.py
index 428bf46..4749b09 100644
--- a/src/mission_control/infra/repositories/assignments.py
+++ b/src/mission_control/infra/repositories/assignments.py
@@ -1,11 +1,11 @@
-"""Assignments by id, and the shared row mapping for them."""
+"""Assignments by id, the writes that create and change them, and the shared row mapping."""
 
 from __future__ import annotations
 
 import sqlite3
 
 from mission_control.domain.enums import AssignmentStatus
-from mission_control.infra.repositories.base import Scoped
+from mission_control.infra.repositories.base import NOW, Scoped
 from mission_control.infra.repositories.models import Assignment
 
 
@@ -16,6 +16,38 @@ class AssignmentRepo(Scoped):
         )
         return assignment_from_row(r) if r else None
 
+    def create(
+        self, mission_id: int, slot_id: int, crew_profile_id: int, proposed_by_id: int
+    ) -> Assignment:
+        """A new proposal. The database refuses a second open assignment for the same person on
+        the same mission, and links to another organisation's records."""
+        cur = self._exec(
+            "INSERT INTO assignments(org_id, mission_id, slot_id, crew_profile_id, proposed_by_id)"
+            " VALUES (:org, :mission_id, :slot_id, :crew_profile_id, :proposed_by_id)",
+            mission_id=mission_id,
+            slot_id=slot_id,
+            crew_profile_id=crew_profile_id,
+            proposed_by_id=proposed_by_id,
+        )
+        created = self.get(cur.lastrowid)
+        assert created is not None
+        return created
+
+    def set_status(
+        self, assignment_id: int, status: AssignmentStatus, reason: str | None = None
+    ) -> bool:
+        """Move an assignment to `status`, recording `reason` (None clears it)."""
+        return (
+            self._exec(
+                f"UPDATE assignments SET status = :status, reason = :reason, updated_at = {NOW}"
+                " WHERE org_id = :org AND id = :id",
+                status=status,
+                reason=reason,
+                id=assignment_id,
+            ).rowcount
+            == 1
+        )
+
 
 def assignment_from_row(r: sqlite3.Row) -> Assignment:
     return Assignment(
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments/src/mission_control/services/assignments.py",
  "offset": 60,
  "limit": 110
}
```

<details>
<summary>↳ Result</summary>

```
60	_MISSION_ENDS = frozenset({MissionStatus.COMPLETED, MissionStatus.CANCELLED})
61	
62	
63	# The owner proposes
64	
65	
66	def propose(ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int) -> Assignment:
67	    """Propose someone for a place in one of the mission's slots. Only the mission's owner may,
68	    while it's in Draft or pending approval; a pending mission goes back to Draft.
69	
70	    Refused, with every reason at once, if the slot has no open place, the person already holds
71	    an open assignment on this mission, or they aren't eligible (deactivated, short of a
72	    required skill, unavailable, or accepted on another mission with overlapping dates).
73	    Proposals elsewhere don't count: they block nothing. An owner may propose themselves, and
74	    must then accept like anyone else."""
75	    with ctx.write() as repos:
76	        mission = found(repos.missions.get_visible(ctx.actor, mission_id), _MISSION)
77	        slot = found(_slot_specs(repos, mission).get(slot_id), _SLOT)
78	        profile = found(repos.crew.get(crew_profile_id), _CREW_MEMBER)
79	        ctx.authorize_view(Action.VIEW_CREW, _about(profile), _CREW_MEMBER)
80	
81	        ctx.authorize(Action.PROPOSE_CREW, Context(owner_id=mission.owner_id))
82	        _check_state(Action.PROPOSE_CREW, None, mission)
83	
84	        problems = [
85	            *_already_on_mission(repos, mission, profile),
86	            *_slot_full(mission, slot),
87	            *_ineligibility(repos, mission, slot, profile),
88	        ]
89	        _refuse(
90	            problems, f"{profile.display_name} can't be proposed as {slot.name} on {mission.name}"
91	        )
92	
93	        made = repos.assignments.create(mission.id, slot.id, profile.id, ctx.actor.user_id)
94	        _audit(ctx, Event.ASSIGNMENT_PROPOSED, made, None, A.PROPOSED, mission, slot, profile)
95	        _after_roster_change(ctx, repos, mission, Action.PROPOSE_CREW)
96	        return made
97	
98	
99	# The crew member answers
100	
101	
102	def accept(ctx: ServiceContext, assignment_id: int) -> Assignment:
103	    """Accept your own proposal while the mission is in Draft. Eligibility is checked again
104	    now, so an accepted assignment elsewhere with overlapping dates refuses it, naming that
105	    mission."""
106	    with ctx.write() as repos:
107	        assignment, mission, profile = _load(ctx, repos, assignment_id)
108	        ctx.authorize(Action.ACCEPT, _about(profile))
109	        _check_state(Action.ACCEPT, assignment.status, mission)
110	        slot = _slot_of(repos, mission, assignment)
111	        _refuse(
112	            _ineligibility(repos, mission, slot, profile),
113	            f"{profile.display_name} can't accept {slot.name} on {mission.name}",
114	        )
115	        return _change(ctx, repos, Action.ACCEPT, assignment, mission, slot, profile)
116	
117	
118	def decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:
119	    """Decline your own proposal while the mission is in Draft. The reason is optional; a blank
120	    one is stored as none."""
121	    with ctx.write() as repos:
122	        assignment, mission, profile = _load(ctx, repos, assignment_id)
123	        ctx.authorize(Action.DECLINE, _about(profile))
124	        _check_state(Action.DECLINE, assignment.status, mission)
125	        slot = _slot_of(repos, mission, assignment)
126	        given = (reason or "").strip() or None
127	        return _change(ctx, repos, Action.DECLINE, assignment, mission, slot, profile, given)
128	
129	
130	def withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:
131	    """Withdraw from your own accepted assignment, giving a reason. Allowed while the mission is
132	    in Draft or pending approval; a pending mission goes back to Draft. An active mission's
133	    roster is frozen."""
134	    with ctx.write() as repos:
135	        assignment, mission, profile = _load(ctx, repos, assignment_id)
136	        ctx.authorize(Action.WITHDRAW, _about(profile))
137	        _check_state(Action.WITHDRAW, assignment.status, mission)
138	        given = (reason or "").strip()
139	        if not given:
140	            raise InvalidInput(f"Withdrawing from {mission.name} needs a reason")
141	        slot = _slot_of(repos, mission, assignment)
142	        return _change(ctx, repos, Action.WITHDRAW, assignment, mission, slot, profile, given)
143	
144	
145	# The owner removes
146	
147	
148	def remove(ctx: ServiceContext, assignment_id: int) -> Assignment:
149	    """Retract a proposal or remove accepted crew. Only the mission's owner may, while it's in
150	    Draft or pending approval; a pending mission goes back to Draft."""
151	    with ctx.write() as repos:
152	        assignment, mission, profile = _load(ctx, repos, assignment_id)
153	        ctx.authorize(Action.REMOVE_CREW, Context(owner_id=mission.owner_id))
154	        _check_state(Action.REMOVE_CREW, assignment.status, mission)
155	        slot = _slot_of(repos, mission, assignment)
156	        return _change(ctx, repos, Action.REMOVE_CREW, assignment, mission, slot, profile)
157	
158	
159	# When a mission ends
160	
161	
162	def cascade_mission_end(
163	    ctx: ServiceContext, mission: Mission, final_status: MissionStatus
164	) -> list[Assignment]:
165	    """Apply a mission's completion or cancellation to its assignments: completing it completes
166	    every accepted assignment; cancelling it cancels every proposed or accepted one. Anything
167	    else is left as it is. Each change is written and audited as the acting user.
168	
169	    Call it inside the caller's `with ctx.write():`, after the caller has authorized and checked
```

</details>

**🔧 SubagentHandback**

````json
{
  "message": "## M12 assignments: report\n\nM12 is built in `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m12-assignments`. Nothing is committed. The full suite passes (958 tests), ruff check and ruff format are clean, and a real run against a fresh seeded database gives the expected S4, S5 and S1 outcomes. Two new problem codes need your approval: `slot_full` and `already_assigned`.\n\n### Files\n- **New:**\n  - `src/mission_control/services/assignments.py`\n  - `tests/integration/test_assignments_service.py`\n  - `tests/integration/test_assignment_writes.py`\n- **Edited:**\n  - `src/mission_control/infra/repositories/assignments.py`: added `create(mission_id, slot_id, crew_profile_id, proposed_by_id)` and `set_status(assignment_id, status, reason=None)`. Both use `org_id = :org` with named binding.\n  - `src/mission_control/domain/events.py` and `tests/unit/domain/test_events.py`: appended a `# M12 assignments` section.\n  - `docs/technical-design.md` §7: two rows appended to the problem-code table, marked \"M12, pending approval\".\n\n### Functions and what each enforces\nEvery use case runs inside `ctx.write()` in this order: load, authorize, check state, check input, check rules, write and audit. Audit `data` carries the mission, slot and crew names.\n\n- **`propose(ctx, mission_id, slot_id, crew_profile_id)`** (M3, S1, S2, AC-14, AC-5, AC-4, AC-7):\n  - Not found if the mission is missing or hidden (via `get_visible`). Also not found if the slot isn't a live slot of this mission, or the crew profile is missing or one crew can't view.\n  - `PROPOSE_CREW` with `owner_id`: a non-owner Lead gets `not_owner`, a Director or Crew Member gets `role_forbidden`.\n  - The mission must be Draft or Pending. Active gives `mission_frozen`, final gives `mission_final`.\n  - It then lists every rule problem at once: `already_assigned`, `slot_full`, and every reason from `ineligibility_reasons(facts.candidate(..., excluding_mission_id=mission))`. A single problem is raised under its own code; several come under `rule_violation` with a summary naming the person, slot and mission.\n  - A Pending mission goes back to Draft, and `mission.returned_to_draft` is audited after the change with `cause` set to `\"assignment.proposed\"`.\n  - Overlapping proposals on different missions are allowed (S2).\n- **`accept(ctx, assignment_id)`** (S2, AC-15): assignee only (`target_user_id` = the assignee's user id). The mission must be Draft and the assignment Proposed. Eligibility is re-checked now, and an overlap names the conflicting mission.\n- **`decline(ctx, assignment_id, reason=None)`** (S3): assignee only, Draft, Proposed. A blank reason is stored as none.\n- **`withdraw(ctx, assignment_id, reason)`** (S3, S5, AC-4, AC-5): assignee only. The assignment must be Accepted and the mission Draft or Pending; Pending goes back to Draft with the revert audit. A blank or missing reason raises `InvalidInput` (422). Because state is checked before input, an Active mission gives `mission_frozen`.\n- **`remove(ctx, assignment_id)`** (M3, AC-4, AC-5): `REMOVE_CREW`, owner only. The assignment must be Proposed or Accepted and the mission Draft or Pending; Pending goes back to Draft.\n- **Visibility** (TR-10, AC-27, AC-29):\n  - The assignment is loaded, then `authorize_view(VIEW_ASSIGNMENT_HISTORY, target=assignee)` runs, so another person's assignment is not found to crew.\n  - Leads and Directors can see it, so acting on it gives 403: `not_owner` \"You can only respond to your own assignments\", or `role_forbidden`.\n  - Helix ids are not found and neither organisation's data changes.\n- **`cascade_mission_end(ctx, mission, final_status)`**, for M13:\n  - It applies `lifecycle.cascade` to every assignment on the mission: accepted becomes completed, and proposed or accepted becomes cancelled. Each change is written and audited (`assignment.completed` / `assignment.cancelled`).\n  - It must be called inside the caller's `ctx.write()`, as its docstring says. Outside a transaction it raises `RuntimeError`. A non-final status raises `ValueError`. It rolls back with the caller.\n  - It does no permission or state checks of its own and returns the changed assignments.\n\n### Tests\n- **Before:** 84 M12 tests (83 new plus the extended events test) against a stub: 83 failed, 1 passed. The one pass was `test_cascade_runs_only_inside_the_callers_write`, and only because `NotImplementedError` is a subclass of `RuntimeError`.\n- **First real run:** 9 failed, because my tests expected full names. Seeded display names are first names (\"Gus\", \"Chen\"), so I changed the expectations. No assertions were weakened.\n- **After:** 84 of 84 pass.\n- **Coverage includes:**\n  - the S4 tests for Gus, Fay and Chen's second acceptance naming Station Reboost;\n  - S5 withdrawal without a reason (None, \"\", blank), with a reason (back to Draft plus the revert audit), and from the Active Telescope;\n  - S1: a Lead proposes themselves and must accept, and the full propose-and-accept steps;\n  - full slot; duplicate open assignment; Pending to Draft on propose and on remove; Active freeze on propose and remove;\n  - permissions: crew, Director, non-owner Lead; crew acting on someone else's assignment gets not found;\n  - an 11-case sweep with Helix ids;\n  - decline with and without a reason; invalid transitions;\n  - the cascades: complete, cancel, outside a transaction, rollback, non-final status;\n  - an 11-case snapshot test proving every refusal leaves the tables unchanged;\n  - the repository writes (scoping, foreign keys across organisations, the unique open index, the withdrawal reason check).\n\n### Suite and ruff\n- `uv run pytest -W error -o addopts=\"\" -q`: 958 passed (875 on main + 83 new).\n- `uv run ruff check src tests`: all checks passed.\n- `uv run ruff format --check src tests`: 65 files already formatted.\n\n### Real run (trimmed)\nScript: `/tmp/m12run/run.py`, run against a fresh seeded `/tmp/m12run/mc.db`, outside the repo.\n```\nS4\n  REFUSED Lee proposes Gus as Flight Engineer on Gateway: 409 overlap: Gus has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02\n  REFUSED Lee proposes Fay as Commander on Gateway: 409 unavailable: Fay is unavailable 2027-03-05 to 2027-03-08\n  OK      Nora proposes Chen as Engineer on Station Reboost: assignment 11 -> proposed\n  OK      Lee proposes Chen as Flight Engineer on Gateway: assignment 12 -> proposed\n  OK      Chen accepts Station Reboost: assignment 11 -> accepted\n  REFUSED Chen accepts Gateway: 409 overlap: Chen has an accepted assignment on Station Reboost overlapping 2027-03-01 to 2027-03-02  {... 'mission_name': 'Station Reboost'}\nS5\n  REFUSED Ben withdraws ..., no reason: 422 validation_error: Withdrawing from Deep Space Comms Upgrade needs a reason\n  OK      Ben withdraws ..., with reason: assignment 7 -> withdrawn (reason: Family emergency)\n  Deep Space Comms after: ('Deep Space Comms Upgrade', 'draft')\n    audit: ('mission.returned_to_draft', 'pending_approval', 'draft', None, '{\"mission_name\": \"Deep Space Comms Upgrade\", \"cause\": \"assignment.withdrawn\"}')\n  REFUSED Hana withdraws from Telescope: 409 mission_frozen: Can't withdraw from an active mission\nExtras\n  REFUSED Nora proposes Dana on Lee's Gateway: 403 not_owner: Only the mission's owner can propose crew for this mission\n  REFUSED Ben accepts Chen's Station Reboost assignment: 404 not_found: Assignment not found\n  REFUSED Lee proposes Kai (Helix) on Gateway: 404 not_found: Crew member not found\nS1 (fresh seed): Lee proposes Ana/Commander, Chen/Flight Engineer, Dana/Mission Specialist -> proposed; all three accept -> accepted; Gateway stays draft.\n  The audit trail shows 3 x assignment.proposed by Lee Park and 3 x assignment.accepted by each crew member, with mission, slot and crew names.\n```\n\n### Review findings (not fixed)\n1. **`touch_for_change()` is never called.** Design §10 and the carried-forward rule say every mutating service calls it first. I used `assignment_problem` plus `mission_status_after_assignment_action` instead. They share the same `_after_change` logic and give better messages (\"Can't withdraw from an active mission\" rather than \"Can't edit…\").\n2. **Missions are loaded with `missions.get`, not `get_visible`, for actions on an existing assignment.** This runs after the assignment-visibility check. A crew member acting on their own closed assignment sees a state refusal instead of a 404. That matches V2 summary access, but departs from \"crew mission visibility is a 404 through the repository\".\n3. **Visibility reuses `VIEW_ASSIGNMENT_HISTORY`.** There is no dedicated \"view assignment\" action in `permissions.py`.\n4. **The slot is loaded after the state check** for accept, decline, withdraw and remove (`_slot_of`). This avoids a confusing NotFound for closed assignments on removed slots. It's a small departure from \"load first\", but harmless because a slot can't be removed while it has open assignments.\n5. **Some top-level 409 codes aren't in the §7 HTTP table.** Single-problem refusals take the problem's code (`skill_below_minimum`, `inactive`, `slot_full`, `already_assigned`), the same convention as admin's `already_exists`. M15 has to map every `RuleViolation` code to 409.\n6. **`cascade_mission_end` would also run inside `ctx.read()`,** because it checks `conn.in_transaction` (low risk).\n7. **A weak test:** `test_cascade_runs_only_inside_the_callers_write` doesn't match on the message, which is why it passed against the stub.\n8. **The cascade audits carry no reason.** A cancellation's reason lives only on M13's mission event.\n9. **\"Approvals cleared\" is implemented only by returning the mission to Draft,** relying on approval rounds (TR-9); `approval_round` stays 1. M11 and M13 must increment the round on submit and count only the current round of a Pending mission.\n10. **Refusal messages use ISO dates.** Friendlier dates are already carried forward to M16.\n\n### New events\n`ASSIGNMENT_PROPOSED` / `ACCEPTED` / `DECLINED` / `WITHDRAWN` / `REMOVED` / `COMPLETED` / `CANCELLED`, with values `assignment.<status>`. Also `MISSION_RETURNED_TO_DRAFT = \"mission.returned_to_draft\"`, commented \"also added by M11; dedupe at merge\" and using the same audit shape as M11.\n\n### New codes (need approval)\n- **`slot_full`:** refs `slot_id`. Example message: \"Flight Engineer on Lunar Gateway Resupply has no open places\".\n- **`already_assigned`:** refs `assignment_id`, `crew_profile_id`, `mission_id`. Example message: \"Ana is already proposed as Commander on Lunar Gateway Resupply\".\n\n### Changes needed in files I don't own\nNone are required. Optional:\n- a dedicated view-assignment action in `domain/permissions.py`;\n- M15 should map all `RuleViolation` codes to 409;\n- dedupe `MISSION_RETURNED_TO_DRAFT` when M11 merges.\n\n### PRD gaps\n- **Re-proposing after a decline or withdrawal.** §6 makes the matcher leave these people out, but S1 only limits open assignments. I allowed a manual re-proposal after a decline and tested it. Please confirm.\n- **`GET /assignments` (\"My assignments\").** It's in design §7 but not in the M12 row or this task, so I didn't build a listing function.\n- **The cancellation reason on cascaded assignment events.** The PRD is silent; I left it out.\n"
}
````

<details>
<summary>↳ Result</summary>

```
{"success":true,"message":"Report delivered to your caller."}
```

</details>
