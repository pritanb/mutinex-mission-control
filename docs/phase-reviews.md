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
