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
