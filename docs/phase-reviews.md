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

## Phase 3: Services (SF, M9–M14)

`8ccb5c3` → `234142c` plus M14 apply and the inbox · use cases on top of the domain and repositories

**Headline:** the first phase built in parallel. Every PRD rule now holds at the service level, and every scenario (S1–S9) runs through the services. The changes were in *how* we worked, plus one convention for refusals and an inbox the design had named but not defined.

### Where we diverged

| Change | Why |
|---|---|
| **A service foundation (SF) module was added** before the services | Without it, every service would have written its own context, error types and fact loaders |
| **Waves in git worktrees** instead of strictly one module at a time | Independent modules (M9 ∥ M10 ∥ M11, then M13 ∥ M14) were built in parallel and still reviewed one branch at a time |
| **Repositories split into one file per area**, missions further split into missions, slots and crew | Parallel branches rarely conflict; each file stays readable |
| **Review happens on `main` as staged changes** before the commit | Easier to read line by line in the IDE |
| **One 409 convention:** a rule refusal's code is always `rule_violation`, with a summary message and every reason as a problem | Services had mixed two conventions. Clients now branch on `problems[].code`. State conflicts keep their own codes. |
| **One shared 422 error (`InvalidInput`)** listing every mistake | Two agents invented their own; plain `ValueError` also signals bugs |
| **New problem codes:** `already_exists`, `owner_not_active_lead`, `mission_needs_a_slot`, `already_owner`, `slot_full`, `already_assigned` | Each refusal names its reason; all are in design §7 |
| **TR-13:** emails are unique across the platform | Login is by email alone. Trade-off: a duplicate-email refusal reveals the address is in use elsewhere. |
| **The inbox is defined** (design §7): a live to-do list of proposals to answer, missions to approve, and your draft missions to staff or submit | The design listed `GET /me/inbox` without saying what's in it. Nothing is stored; a stored-notifications model was considered and rejected as more to build and keep in sync. |
| **The matcher also leaves out crew the owner removed** (PRD §6, AC-21) | Suggesting someone the owner just took off would be odd |

### Key decisions

- **Edits that break assignments:** refused only for *new* problems; a shortfall someone already had in the same skill doesn't block.
- **Permission before lookups:** a refused caller can't learn whether a user, crew member or skill exists.
- **A name-only change keeps a Pending mission Pending;** any other change sends it back to Draft, audited with its cause.
- **Re-proposing after a decline is allowed.**
- **Approvals count per round,** with N saved at submit; an approval still counts after its Director leaves.
- **Privacy:** unavailability reasons never go into the audit log.
- **No-op updates write nothing.** Reactivating users is out of scope (`docs/backlog.md`).

### Process notes

- The M11 agent stopped before its hand-off; the lead did the real run and a fresh agent reviewed it.
- Another session committed on a wave branch; its contents were verified to be on `main` before the branch was deleted.
- Every refactor (SF split, repository split, missions package) was checked with a before/after behaviour snapshot.

### Modules

| Module | Commit | Notes |
|---|---|---|
| SF service foundation | `8ccb5c3` | Context, errors, fact loaders |
| M10 crew | `d55a7ed` | Reasons hidden from Leads; Active assignments protected from skill changes |
| M9 admin | `b6bad6d` | Last Director, owned missions and open assignments block demotion and deactivation |
| M11 missions | `8f204f0`, `39d7217` | Create, edit, slots, transfer; repository split first |
| M14 preview | `4e7152b` | Suggest crew for a draft mission; writes nothing |
| M12 assignments | `91f3810` | Propose, accept, decline, withdraw, remove, end-of-mission cascade |
| M13 approvals | `234142c` | Submit, approve, reject, complete, cancel, mission history |
| 409 convention | `5392748`, `2b279fa` | `rule_violation` everywhere; design §7 updated |
| M14 apply and inbox | *pending* | Apply proposes through the same path as a hand proposal; inbox per design §7 |

### Phase-end review

A read-only subagent reviewed SF, M9–M14 and the inbox. No High issues: every write is one transaction taken before its checks, refusals write nothing, and a foreign id gets the same 404 as a missing one everywhere. Fixes were applied by parallel subagents, each proving its fix with a test and a real run.

- **Fixed (Medium):**
  - crew and admin checked input before permission (Ben setting a level of 9 got 422, not 403); now load → authorise → input, with every mistake in one 422;
  - two 409s stopped at the first problem (create mission, remove the last slot); both now list every problem;
  - the "can this Director still approve" rule was coded twice; one domain helper now serves approve and the inbox;
  - the matcher's exclusion of removed crew wasn't in the PRD; the PRD now says so.
- **Fixed (Low):** audit `data` used four shapes for before/after values; duplicated helpers; module names in `events.py` comments; design wording about `touch_for_change`; singular wording for one clash; seed and session SQL brought under the SQL lint.
- **Tests added:** AC-7 after a transfer for propose, apply and submit; several problems at once; the realistic refusal for proposing on a Pending mission.

### Carried forward

- **Phase 4:** consistent error body with non-empty `problems`; 422 for `InvalidInput`, `InvalidDateRange` and `PasswordTooShort`; matcher previews per `docs/cli-ux.md`; the inbox's "ready to submit" includes eligible approvers.

---

## Phase 4: Interfaces (M15–M17)

*pending* · HTTP API, `mc` CLI, `mc-admin`, README

**Headline:** built as one background wave (M15 ∥ M16, then M17) while Phase 3 finished, then reconciled together. The full S1 golden path runs through the real `mc` binary against the real server, and the README's own commands are tested.

### Where we diverged

| Change | Why |
|---|---|
| **The CLI was built against the design's API before the API existed**, then reconciled | Parallel work. The design defines errors but not success bodies, so the CLI guessed; reconciliation found and fixed the mismatches. |
| **CLI tests check their fake responses against the real API models** | Hand-written fakes hid three mismatches (deactivate field, owner column, inbox shape) |
| **`GET /me` returns the account, organisation and crew profile** via a new `auth.whoami` | `mc whoami` needs names, not just ids |
| **`owner_name` in the mission list** | `mc missions list` shows owners |
| **405 `method_not_allowed` and 500 `internal_error`** use the standard error body; a 500 never includes details | One error shape for every status |
| **`MC_API_URL`** setting for the CLI | The design had no way to point the CLI at a server |
| **Passwords:** hidden prompt at a terminal, stdin otherwise, never a flag | Scripts and tests need a non-interactive path |
| **With `--json`, a refusal prints the error body to stdout** with the same exit code | Scripts get one parseable format |
| **Confirmations** for changes to a pending mission, cancel, and deactivating a user; `-y` for `--yes` | Deactivation can't be undone |
| **`mc login` ends the previous session**; logging out offline still removes the local token (exit 4) | Old tokens no longer linger for 12 hours |
| **`mc-admin init-db | seed [--reset] | create-org`**; its organisation SQL lives in `infra/platform.py`, covered by the SQL lint | Operators create organisations (PRD T3) without SQL outside `infra/` |

### Accepted deviations

- **Malformed JSON gets 422 before 401**, because FastAPI parses the body before authentication. The 422 reveals nothing about the endpoint.
- **API response schemas reuse the repositories' record types** rather than only service views.
- **Some foreign ids get 403, not 404,** where a role is refused before any lookup (Leads on admin routes). A missing id gets the same 403, so "same response as a missing id" holds.
- **`seed --reset` deletes without asking;** the flag is the consent.

### Phase-end review

A read-only subagent reviewed M15–M17 and drove the real binaries. Fixes were applied by parallel subagents, each verified with a test and a real run.

- **Fixed (High):** every failed login re-raised one shared exception, whose growing traceback kept the attempted plaintext passwords in memory. Each failure now raises a fresh exception.
- **Fixed (Medium):** owner column missing against the real API; fakes unchecked against the API; crew `set-skill` showed the wrong refusal; piped passwords expected the new one twice; `mc-admin` SQL outside `infra/`.
- **Fixed (Low):** 500s were plain text; isolation sweep missed request variants that reach a different service; re-login left the old session valid; a leftover skip could hide a broken README test; confirmations shown for actions the server would refuse; wording.

- **Polish after the end-to-end run:** the too-few-approvers reason now reads "Only 1 Director can approve this mission; it needs 2"; `mc missions show` says who rejected a mission and why; cancelling says how many open assignments were cancelled; bio changes are audited.

### Backlog

- Split `cli/commands/missions.py` (~750 lines) into lifecycle, crew and slot modules.
- Check the CLI's request bodies against the API's request models, as responses already are.
