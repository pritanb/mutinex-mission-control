# Subagent (02): M16 CLI in worktree

Source: `agent-a5cbdff74dbba0f23.jsonl` · 2026-10-12 03:17:02 UTC → 2026-10-12 03:45:04 UTC

Rendered from the raw JSONL without editing message content. Tool results and thinking are collapsed; expand them to read.


---

### 👤 User · 2026-10-12 03:17:02 UTC

You are building module **M16 (CLI, `mc`)** of the Mission Control project, in a git worktree, as part of a parallel wave. Another agent is building M15 (HTTP API) in a separate worktree at the same time, so the real API doesn't exist yet on your branch; the lead is building M13/M14 on main.

## Where to work
- Work ONLY in `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli` (branch `m16-cli`, cut from main at 91f3810). Use absolute paths. Never touch the main checkout or other worktrees.
- **Do not commit.** Leave everything as uncommitted changes. Do not push. Do not run bare `git stash`.
- `pyproject.toml` and `uv.lock` are already modified there (typer, rich, httpx2 added as runtime deps). Don't add dependencies. **httpx is banned (supply-chain risk); use httpx2 only.** You may add one line to `[project.scripts]`: `mc = "mission_control.cli.app:main"` (or the equivalent entry point you create).

## Read first (source of truth)
- `CLAUDE.md`, `docs/prd.md`, `docs/technical-design.md` — especially §7 API (the contract you call: endpoints, request/response shapes, the error body with its `problems` list, status codes, problem codes), §8 CLI (commands, references, passwords, output, errors, exit codes `0/1/2/3/4`, confirmations, credentials at `~/.config/mission-control/credentials.json` mode 0600), §10 guidelines.
- `docs/cli-ux.md` — the approved mock sessions for `mc missions match`; render matcher previews exactly that way.
- The project skill at `.claude/skills/cli-ux/` (SKILL.md and references/: principles, terminal-mechanics, checklist, examples). Follow its core rules and run its checklist before you hand off.
- `docs/phase-reviews.md` carried-forward items for M16: friendlier date formatting; single-reason refusals repeat their message in `problems`, so don't print the message twice.

## Scope
- The whole `mc` command set in design §8 (Everyone, Leads, Directors), built against the §7 HTTP contract — including approve/reject/submit/complete/cancel and `match --apply`, even though those server routes arrive later.
- Layering: the CLI talks to the API only over HTTP through an `httpx2` client wrapper passed into commands (design §8: "so tests use TestClient and need no server"). The CLI must not import services, domain or infra.
- Tests: since the API isn't on this branch, test commands against an `httpx2.MockTransport` (or equivalent) returning responses shaped exactly like §7, covering reference resolution (missions/assignments by ID, people by email, skills by name, slots by name or position), the `--slot "Commander:1:Piloting>=4,Leadership>=3"` parser, prompts (hidden password prompt asked twice when setting; never a flag), confirmations and `--yes`, `--json`, pipe-safe output (data to stdout, messages to stderr, no colour when not a TTY, honour NO_COLOR), error rendering (message, one bullet per problem, hint for known codes), exit codes, credentials file handling (0600, cleared on logout/password change/401), Ctrl+C → exit 130, and the S1 and S4 flows. Make the config directory overridable for tests so they never touch the real home directory, but don't invent user-facing env vars or flags beyond the design without listing them as open questions.
- If the design is silent or ambiguous on something (a command's exact flags, an output format), **don't invent behaviour**: choose the most conservative option consistent with §8 and `docs/cli-ux.md`, and list it as an open question in your hand-off.

## How to work (project workflow)
1. Tests first, named with the PRD IDs they cover where relevant (no PRD/AC/§ references in `src/` — docstrings, comments, help text and messages stay free of them).
2. Run `uv run pytest`, `uv run ruff check` and `uv run ruff format --check` on the whole worktree; all must pass.
3. **Real verification:** actually run the `mc` binary in a terminal: `mc --help`, a few `<cmd> --help`, and some commands against a tiny local stub or a mock (or show error handling when the server is unreachable → exit 4), plus piped (`| cat`) output and `--json`. Capture actual output.
4. Read-only self-review of your full diff against design §8, `docs/cli-ux.md` and the cli-ux checklist; report findings grouped Blocker/Major/Minor.

Conventions: Python 3.12; `@contextmanager` functions are annotated `-> Generator[T]` (not `Iterator`); messages read naturally; match the surrounding code's style.

## Hand-off (your final message)
Concise: files added/changed; test count and lint result; real-run commands with their actual output (trimmed); the commands built; any §7 endpoint shapes you had to assume (so they can be checked against M15); cli-ux checklist findings; open questions/decisions for the user; a proposed commit message. Don't commit.

<details>
<summary>⚙️ System/meta message · 2026-10-12 03:17:02 UTC</summary>

```
<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered.
</system-reminder>
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && git status && git log --oneline -3 && ls -R src tests docs .claude/skills/cli-ux | head -100 && wc -l docs/*.md .claude/skills/cli-ux/*.md .claude/skills/cli-ux/references/*
```

<details>
<summary>↳ Result</summary>

```
On branch m16-cli
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   pyproject.toml
	modified:   uv.lock

no changes added to commit (use "git add" and/or "git commit -a")
91f3810 feat(m12): assignments service — propose, accept, decline, withdraw, remove, end-of-mission cascade
4e7152b feat(m14): matcher preview — suggest crew for a draft mission
39d7217 feat(m11): missions service — create, edit, slots, transfer (with review fixes)
.claude/skills/cli-ux:
SKILL.md
evals
references

.claude/skills/cli-ux/evals:
evals.json

.claude/skills/cli-ux/references:
checklist.md
examples.md
principles.md
terminal-mechanics.md

docs:
backlog.md
brief.md
cli-ux.md
phase-reviews.md
prd.md
technical-design.md

src:
mission_control

src/mission_control:
__init__.py
__pycache__
api
domain
infra
seed
services

src/mission_control/__pycache__:
__init__.cpython-312.pyc

src/mission_control/api:
__init__.py
__pycache__
app.py

src/mission_control/api/__pycache__:
__init__.cpython-312.pyc
app.cpython-312.pyc

src/mission_control/domain:
__init__.py
__pycache__
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

src/mission_control/domain/__pycache__:
__init__.cpython-312.pyc
approvals.cpython-312.pyc
dates.cpython-312.pyc
eligibility.cpython-312.pyc
enums.cpython-312.pyc
errors.cpython-312.pyc
events.cpython-312.pyc
lifecycle.cpython-312.pyc
matching.cpython-312.pyc
passwords.cpython-312.pyc
permissions.cpython-312.pyc
records.cpython-312.pyc

src/mission_control/infra:
__init__.py
__pycache__
db.py
repositories
schema.sql
security.py

src/mission_control/infra/__pycache__:
__init__.cpython-312.pyc
db.cpython-312.pyc
security.cpython-312.pyc

src/mission_control/infra/repositories:
__init__.py
__pycache__
approvals.py
assignments.py
audit.py
base.py
crew.py
facts.py
mission_crew.py
mission_slots.py
missions.py
       9 docs/backlog.md
      76 docs/brief.md
     193 docs/cli-ux.md
     169 docs/phase-reviews.md
     338 docs/prd.md
     856 docs/technical-design.md
      47 .claude/skills/cli-ux/SKILL.md
      50 .claude/skills/cli-ux/references/checklist.md
      89 .claude/skills/cli-ux/references/examples.md
      77 .claude/skills/cli-ux/references/principles.md
      85 .claude/skills/cli-ux/references/terminal-mechanics.md
    1989 total
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && cat docs/technical-design.md
```

<details>
<summary>↳ Result</summary>

```
<persisted-output>
Output too large (46.2KB). Full output saved to: /Users/pritanbarai/.claude/projects/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tool-results/b5vzobsr4.txt

Preview (first 2KB):
# Mission Control — Technical Design (v1)

> **Status:** Agreed · **Implements:** [`prd.md`](prd.md) · **Audience:** the engineering team and the coding agents implementing v1
>
> The PRD defines *what* the system does. This document defines *how* we build it, *why* we chose this approach, and *in what order* we deliver it. IDs such as P3, M7 or AC-15 refer to the PRD.

**Contents**
1. [Summary](#1-summary)
2. [Architecture](#2-architecture)
3. [Data model](#3-data-model)
4. [Security and tenancy](#4-security-and-tenancy)
5. [Lifecycle](#5-lifecycle)
6. [Matching](#6-matching)
7. [API](#7-api)
8. [CLI](#8-cli)
9. [Delivery plan](#9-delivery-plan)
10. [Guidelines for implementing agents](#10-guidelines-for-implementing-agents)
11. [Setup and testing](#11-setup-and-testing)
- [Appendix A: Schema SQL](#appendix-a-schema-sql)
- [Appendix B: Trade-offs and considerations](#appendix-b-trade-offs-and-considerations)

---

## 1. Summary

**What we're building.** A multi-tenant API and CLI for planning space missions:
- organisations manage crew and their skills;
- Leads define missions and get crew suggestions from a deterministic matcher;
- Directors approve missions before they go active.

**Design principles**

1. **Business rules live in one place.** All rules are pure functions in `domain/`, so they're easy to test and shared by every entry point.
2. **Tenant isolation in depth.** Identity, queries, database constraints and tests each block cross-tenant access independently.
3. **The CLI is just a client.** It uses the same API as any other client, so the API is the only place behaviour is enforced.
4. **Simple to run, simple to reason about.** One process, one SQLite file, no background jobs.
5. **Test-first.** Every module begins with failing tests derived from PRD acceptance criteria.

...
</persisted-output>
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/.claude/projects/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tool-results/b5vzobsr4.txt"
}
```

<details>
<summary>↳ Result</summary>

````
1	# Mission Control — Technical Design (v1)
2	
3	> **Status:** Agreed · **Implements:** [`prd.md`](prd.md) · **Audience:** the engineering team and the coding agents implementing v1
4	>
5	> The PRD defines *what* the system does. This document defines *how* we build it, *why* we chose this approach, and *in what order* we deliver it. IDs such as P3, M7 or AC-15 refer to the PRD.
6	
7	**Contents**
8	1. [Summary](#1-summary)
9	2. [Architecture](#2-architecture)
10	3. [Data model](#3-data-model)
11	4. [Security and tenancy](#4-security-and-tenancy)
12	5. [Lifecycle](#5-lifecycle)
13	6. [Matching](#6-matching)
14	7. [API](#7-api)
15	8. [CLI](#8-cli)
16	9. [Delivery plan](#9-delivery-plan)
17	10. [Guidelines for implementing agents](#10-guidelines-for-implementing-agents)
18	11. [Setup and testing](#11-setup-and-testing)
19	- [Appendix A: Schema SQL](#appendix-a-schema-sql)
20	- [Appendix B: Trade-offs and considerations](#appendix-b-trade-offs-and-considerations)
21	
22	---
23	
24	## 1. Summary
25	
26	**What we're building.** A multi-tenant API and CLI for planning space missions:
27	- organisations manage crew and their skills;
28	- Leads define missions and get crew suggestions from a deterministic matcher;
29	- Directors approve missions before they go active.
30	
31	**Design principles**
32	
33	1. **Business rules live in one place.** All rules are pure functions in `domain/`, so they're easy to test and shared by every entry point.
34	2. **Tenant isolation in depth.** Identity, queries, database constraints and tests each block cross-tenant access independently.
35	3. **The CLI is just a client.** It uses the same API as any other client, so the API is the only place behaviour is enforced.
36	4. **Simple to run, simple to reason about.** One process, one SQLite file, no background jobs.
37	5. **Test-first.** Every module begins with failing tests derived from PRD acceptance criteria.
38	
39	**Non-goals for v1:** web UI, horizontal scaling, notifications, background scheduling, SSO, migrations tooling. See [Appendix B](#appendix-b-trade-offs-and-considerations) for the trade-offs and what we'd change at scale.
40	
41	---
42	
43	## 2. Architecture
44	
45	**Stack:** Python 3.12 · FastAPI + Pydantic v2 · SQLite through stdlib `sqlite3` · argon2-cffi · Typer + httpx2 · uv, pytest, ruff
46	
47	**Dependency policy:** don't use `httpx` anywhere, including tests. Use `httpx2`, which Starlette's `TestClient` now expects.
48	
49	Why SQLite, hand-written SQL, and a CLI that goes through the API: [TR-1](#tr-1), [TR-2](#tr-2), [TR-4](#tr-4).
50	
51	```mermaid
52	flowchart TB
53	    U([Users]) --> CLI[CLI]
54	    CLI -->|HTTP + JSON| API[API]
55	    API --> S[Services]
56	    S --> D[Domain rules]
57	    S --> R[Repositories]
58	    R --> DB[(SQLite)]
59	    A[mc-admin] --> DB
60	```
61	
62	| Layer | Folder | Responsibility | May depend on |
63	|---|---|---|---|
64	| CLI | `cli/` | Commands, output, prompts | API over HTTP only |
65	| API | `api/` | Validate input, resolve `Actor`, call a service, map errors | services |
66	| Services | `services/` | One use case = one transaction + audit | domain, infra |
67	| Domain | `domain/` | Every business rule, pure (no I/O) | nothing |
68	| Infra | `infra/` | Connections, schema, scoped repositories, security | domain types |
69	
70	**How a request flows** (example: `mc missions submit 12`)
71	
72	1. The CLI sends `POST /api/v1/missions/12/submit` with the bearer token.
73	2. The API resolves the token to an `Actor` (user, organisation, role) and calls `services.missions.submit(actor, 12)`.
74	3. The service opens `BEGIN IMMEDIATE` and loads the mission through `Repos(conn, actor.org_id)`.
75	4. `domain.lifecycle.check_submit(...)` returns a list of problems. If the list is empty, the service writes the new status and an audit event, then commits.
76	5. The API returns `200` with the mission, or `409` with every problem. The CLI prints one bullet per problem and exits with code `1`.
77	
78	<details><summary>Folder layout</summary>
79	
80	```
81	src/mission_control/
82	  domain/    dates  enums  errors  eligibility  matching  lifecycle  approvals  permissions  passwords  records
83	  infra/     db  schema.sql  security  repositories/
84	  services/  auth  admin  crew  missions  assignments  approvals  matching  audit  inbox
85	  api/       app  deps  errors  schemas/  routers/
86	  cli/       main  client  config  render  resolve  commands/
87	  seed/      data  loader
88	  admin_cli.py        # mc-admin: init-db, seed, create-org
89	tests/  unit/  integration/  api/  cli/  builders.py  conftest.py
90	```
91	</details>
92	
93	---
94	
95	## 3. Data model
96	
97	The core entities are below. Skills, unavailability, approvals, tokens and the audit log hang off these. All 13 tables are in [Appendix A](#appendix-a-schema-sql).
98	
99	```mermaid
100	flowchart LR
101	    Org[Organisation] --> User
102	    Org --> Mission
103	    User --> Crew[Crew profile]
104	    Mission --> Slot
105	    Slot --> Assignment
106	    Crew --> Assignment
107	```
108	
109	**Tenant safety.** Every tenant table has `org_id` and `UNIQUE (org_id, id)`. Every reference between tenant rows includes `org_id`, so the database itself rejects links across organisations. Why a shared database: [TR-3](#tr-3).
110	
111	| Enforced by the database | Enforced by services |
112	|---|---|
113	| Value ranges and valid dates | Eligibility and overlaps |
114	| Cross-organisation links rejected | Open places |
115	| One open assignment per person per mission | State transitions |
116	| A slot belongs to its mission | Permissions and the owner's role |
117	| Reasons for withdrawals and rejections | At least one requirement per slot |
118	| Append-only audit log; used skills can't be deleted | |
119	
120	**Modelling choices**
121	- **Approval rounds.** Submit sets `round += 1` and saves N in `approvals_required`. Only approvals in the current round count, and none are ever deleted ([TR-9](#tr-9)).
122	- **Soft-deleted slots.** `removed_at` keeps the history of past assignments.
123	- **Nothing derived is stored.** Workload, eligibility, open places and the roster are computed when needed ([TR-7](#tr-7)).
124	- **Integer IDs** keep CLI commands short ([TR-12](#tr-12)).
125	- **History survives renames.** Audit `data` keeps the names that applied at the time.
126	- **"On a mission"** means holding an open or completed assignment. Any other status gives summary access only (V2).
127	
128	---
129	
130	## 4. Security and tenancy
131	
132	### Authentication
133	
134	| | |
135	|---|---|
136	| Token | 32 random bytes. Only the SHA-256 hash is stored. 12-hour expiry. |
137	| Every request | Token → valid? → user active? → `Actor(user_id, org_id, role, crew_profile_id)`. Nothing is cached, so role changes apply immediately. |
138	| Revocation | Logout revokes that token. Deactivation or a password change revokes every token. Opaque tokens make this immediate ([TR-5](#tr-5)). |
139	| Passwords | Argon2id. At least 15 characters. No character-type rules. |
140	
141	### Permissions
142	
143	Each **role** sets the baseline:
144	
145	| Role | Can | Can't |
146	|---|---|---|
147	| **Director** | Run the organisation: users, roles, skills, approval setting. See everything. Approve, transfer, complete and cancel missions. | Edit mission details, since that's the owner's job |
148	| **Lead** | Create and run their own missions. Rate other people's skills. See all crew and missions. | Approve anything. Touch missions they don't own. |
149	| **Crew** | Manage their own profile and availability. Respond to their own assignments. | See other crew, or missions they aren't on |
150	
151	On top of the role, **relationship rules** make the decisions that matter:
152	
153	| Rule | Effect | PRD |
154	|---|---|---|
155	| **Owner only** | Only the mission's owner edits it, proposes crew, applies the matcher or submits | M3 |
156	| **Not yourself** | Nobody sets their own skill levels | P3 |
157	| **Eligible approver** | A Director can't approve a mission they created or are on | A2 |
158	| **Self only** | Only you edit your details and availability. Only you, and Directors, see your unavailability reasons. | P4, §5.7 |
159	| **Visibility** | Crew only see missions they're on. Former assignees see a summary. | V2 |
160	
161	**Enforcement.** `domain/permissions.authorize(actor, action, ctx)` is the single entry point. The complete action × role table is the parametrized test for this module, and that test is the source of truth.
162	
163	| Status | When |
164	|---|---|
165	| **401** | Authentication failed |
166	| **404** | Missing, another organisation's, or not visible. All three look identical ([TR-10](#tr-10)). |
167	| **403** | Visible, but you're not allowed to do this |
168	
169	### Tenant isolation
170	
171	1. **Identity.** `org_id` comes only from the token, never from the request.
172	2. **Repositories.** `Repos(conn, org_id)` scopes every query. Another organisation's ID behaves as missing.
173	3. **Database.** Composite `(org_id, id)` foreign keys.
174	4. **Tests.**
175	   - An SQL lint checks every query mentions `org_id`.
176	   - A route inventory makes sure no endpoint is left out of the isolation tests.
177	   - A cross-organisation sweep compares database snapshots before and after.
178	
179	---
180	
181	## 5. Lifecycle
182	
183	### Mission
184	
185	```mermaid
186	stateDiagram-v2
187	    direction LR
188	    Draft --> Pending: submit
189	    Pending --> Active: final approval
190	    Pending --> Draft: reject / change
191	    Active --> Completed: complete
192	```
193	
194	Any state before Completed can also be **cancelled**.
195	
196	| Action | Who | Must be true | Effect |
197	|---|---|---|---|
198	| submit | owner | Slots full, all accepted, roster eligible, eligible approvers ≥ N | `round += 1`, N saved |
199	| approve | eligible Director | Hasn't decided this round. Roster eligible. | Active once N is reached. **If a check fails, nothing is written.** |
200	| reject | eligible Director | Reason given | → Draft |
201	| transfer | Director | New owner is an active Lead | Pending → Draft. Active stays Active. |
202	| complete | owner or Director | Mission is Active | Accepted assignments → completed |
203	| cancel | owner or Director | Reason given | Open assignments → cancelled |
204	
205	### Assignment
206	
207	```mermaid
208	stateDiagram-v2
209	    direction LR
210	    Proposed --> Accepted: accept
211	    Proposed --> Declined: decline
212	    Accepted --> Withdrawn: withdraw
213	    Accepted --> Completed: mission completed
214	```
215	
216	The owner can also **remove** an open assignment. Cancelling the mission **cancels** every open assignment.
217	
218	| Action | Who | Mission must be | Notes |
219	|---|---|---|---|
220	| propose | owner | Draft or Pending* | Person eligible, place open, not already on this mission |
221	| accept | crew member | Draft | Still eligible. An overlap names the conflicting mission. |
222	| decline | crew member | Draft | Reason optional |
223	| withdraw | crew member | Draft or Pending* | Reason required |
224	| remove | owner | Draft or Pending* | |
225	
226	\* Sends a Pending mission back to Draft.
227	
228	### Cross-cutting rules
229	
230	| Rule | How it's implemented |
231	|---|---|
232	| **Back to Draft** | Every mutating service calls `touch_for_change()` first. Draft → no change. Pending → Draft. Active → `mission_frozen`. Final → `mission_final`. |
233	| **Edits can't break assignments (M7)** | `invalidated_by()` checks slot removal, headcount, requirements and dates → `invalidates_assignments` |
234	| **Skill changes (P3)** | Allowed. Refused only if they'd break an **Active** assignment → `invalidates_active_assignment` |
235	| **Audit** | Written in the same transaction as the change. Refused actions write nothing. |
236	| **Transactions** | One connection per request. `foreign_keys=ON`. `busy_timeout=5000`. `BEGIN IMMEDIATE` *before* checks. Roll back on error. Lock timeout → 503 `busy`. ([TR-11](#tr-11)) |
237	
238	---
239	
240	## 6. Matching
241	
242	The matcher suggests crew for a Draft mission's open places. It's a pure function: same inputs, same output. It's greedy rather than optimal, which keeps it explainable ([TR-6](#tr-6)).
243	
244	**How it works**
245	
246	1. **Filter.** For each slot, keep candidates who are eligible: active, skills meet the requirements, available, and no overlapping accepted assignment.
247	2. **Pick a slot.** Take the open slot with the fewest candidates, so scarce skills are protected.
248	3. **Pick a person.** Take the lowest workload, then the highest proficiency, then the lowest ID.
249	4. **Place** that person and remove them from every other slot's candidates.
250	5. **Repeat** until all places are filled or marked **unfilled**.
251	
252	**Inputs** (`domain/records.py`). They carry names as well as IDs, so every refusal can name the person, skill and mission involved:
253	
254	| Record | Fields |
255	|---|---|
256	| `Requirement` | `skill_id`, `skill_name`, `min_level` |
257	| `SlotSpec` | `id`, `position`, `name`, `open_places`, `requirements: tuple[Requirement, ...]` |
258	| `Commitment` | `mission_id`, `mission_name`, `window`: an accepted assignment on another non-final mission |
259	| `CandidateFacts` | `crew_profile_id`, `name`, `active`, `skills: {skill_id: level}`, `unavailable: tuple[DateRange, ...]`, `accepted_elsewhere: tuple[Commitment, ...]`, `workload` |
260	| `RosterEntry` | `assignment_id`, `slot: SlotSpec`, `crew: CandidateFacts`, `status`: an open assignment on the mission being edited or submitted (`crew.accepted_elsewhere` excludes this mission) |
261	| `AssignmentFact` | `mission_id`, `mission_status`, `assignment_status`, `window`: one of a person's assignments, used to compute workload |
262	| `ActiveAssignment` | `mission_id`, `mission_name`, `slot_name`, `requirements`: an accepted assignment on an Active mission, used to check skill changes |
263	
264	```python
265	def suggest_roster(slots: list[SlotSpec], candidates: list[CandidateFacts],
266	                   window: DateRange) -> Suggestion:
267	    by_id = {c.crew_profile_id: c for c in candidates}
268	    eligible = {s.id: {c.crew_profile_id for c in candidates if is_eligible(c, s, window)}
269	                for s in slots}
270	    remaining = {s.id: s.open_places for s in slots}
271	    placements, unfilled = [], []
272	
273	    while open_slots := [s for s in slots if remaining[s.id] > 0]:
274	        # Most-constrained slot first; ties by listed position, then id.
275	        slot = min(open_slots, key=lambda s: (len(eligible[s.id]), s.position, s.id))
276	
277	        if not eligible[slot.id]:
278	            unfilled.append(Unfilled(slot.id, remaining[slot.id]))
279	            remaining[slot.id] = 0
280	            continue
281	
282	        # Lowest workload, then highest proficiency, then stable id.
283	        person = min((by_id[i] for i in eligible[slot.id]),
284	                     key=lambda c: (c.workload, -proficiency(c, slot), c.crew_profile_id))
285	
286	        placements.append(Placement(slot.id, person.crew_profile_id))
287	        remaining[slot.id] -= 1
288	        for ids in eligible.values():
289	            ids.discard(person.crew_profile_id)
290	
291	    return Suggestion(placements, unfilled)
292	
293	
294	def proficiency(c: CandidateFacts, slot: SlotSpec) -> int:
295	    return sum(c.skills.get(r.skill_id, 0) for r in slot.requirements)
296	```
297	
298	**Workload** = total mission-days of accepted assignments on missions that aren't completed, leaving out the mission being matched.
299	
300	| | Preview | Apply |
301	|---|---|---|
302	| Who | Owner or Director | Owner only |
303	| Writes | Nothing | Proposals, created through the normal `propose` path |
304	| Data | Loaded with one query per fact type | Recomputed inside the write transaction, so it's never stale |
305	
306	---
307	
308	## 7. API
309	
310	**Conventions**
311	- REST and JSON, under `/api/v1`.
312	- Authentication with the header `Authorization: Bearer <token>`.
313	- Lifecycle changes are explicit `POST` commands, for example `/submit`. They are never `PATCH status`, because each one has its own guards and audit event ([TR-8](#tr-8)).
314	- List endpoints return only what the caller is allowed to see.
315	
316	#### Auth and me
317	| Method | Path | Purpose |
318	|---|---|---|
319	| POST | `/auth/login` | Exchange email and password for a token |
320	| POST | `/auth/logout` | Revoke the current token |
321	| GET | `/me` | Current user, role and crew profile |
322	| POST | `/me/password` | Change password (revokes all sessions) |
323	| GET | `/me/inbox` | Things waiting on me |
324	
325	#### Organisation, users and skills (Directors)
326	| Method | Path | Purpose |
327	|---|---|---|
328	| GET · PATCH | `/org` | View settings, or set the required approvals |
329	| GET · POST | `/users` | List users, or create one with an initial password |
330	| PATCH | `/users/{id}` | Change role or deactivate |
331	| POST | `/users/{id}/crew-profile` | Give a user a crew profile |
332	| GET · POST | `/skills` | List skills (Leads too), or add one |
333	| PATCH · DELETE | `/skills/{id}` | Rename, or delete if unused |
334	
335	#### Crew
336	| Method | Path | Purpose |
337	|---|---|---|
338	| GET | `/crew` · `/crew/{id}` | List or view profiles |
339	| PATCH | `/crew/{id}` | Edit own display name and bio |
340	| PUT · DELETE | `/crew/{id}/skills/{skill_id}` | Set or remove a skill level |
341	| GET · POST | `/crew/{id}/unavailability` | List or add own unavailability |
342	| DELETE | `/crew/{id}/unavailability/{uid}` | Remove own unavailability |
343	| GET | `/crew/{id}/assignments` | Assignment history (summaries) |
344	
345	#### Missions
346	| Method | Path | Purpose |
347	|---|---|---|
348	| GET · POST | `/missions` | List visible missions, or create one with slots |
349	| GET · PATCH | `/missions/{id}` | View, or edit name and dates |
350	| POST | `/missions/{id}/slots` | Add a slot |
351	| PATCH · DELETE | `/missions/{id}/slots/{sid}` | Edit or remove a slot |
352	| GET | `/missions/{id}/history` | Audit trail |
353	| POST | `/missions/{id}/submit` · `approve` · `reject` · `complete` · `cancel` | Lifecycle commands |
354	| POST | `/missions/{id}/owner` | Transfer ownership |
355	| GET | `/missions/{id}/match` | Preview suggested roster |
356	| POST | `/missions/{id}/match/apply` | Create proposals from the suggestion |
357	
358	#### Assignments
359	| Method | Path | Purpose |
360	|---|---|---|
361	| POST | `/missions/{id}/assignments` | Propose a crew member for a slot |
362	| GET | `/assignments` | My assignments |
363	| POST | `/assignments/{id}/accept` · `decline` · `withdraw` · `remove` | Respond or remove |
364	
365	#### Errors
366	
367	Every error has the same shape, for every status code (401, 403, 404, 409, 422, 503). `problems` is always present and always has at least one entry, so clients only ever handle one format. A rule or state conflict (409) lists **every** problem at once. A permission refusal (403) lists its single reason, because only one applies and the actor can't fix it themselves. Each problem names the record involved:
368	
369	```json
370	{
371	  "error": {
372	    "code": "rule_violation",
373	    "message": "Mission can't be submitted",
374	    "problems": [
375	      { "code": "slot_unfilled", "message": "Commander: 1 of 1 place unfilled", "refs": { "slot_id": 12 } }
376	    ]
377	  }
378	}
379	```
380	
381	| HTTP | Meaning | Codes |
382	|---|---|---|
383	| 401 | Not authenticated | `invalid_credentials` `unauthenticated` |
384	| 403 | Not allowed | `role_forbidden` `not_owner` `approver_is_creator` `approver_is_rostered` `self_skill_edit` `wrong_current_password` |
385	| 404 | Not found or not visible | `not_found` |
386	| 409 | Conflicts with state or a rule | **State:** `mission_frozen` `mission_final` `invalid_transition` `already_decided`<br>**Rules:** `rule_violation` `overlap` `unavailable` `insufficient_approvers` `invalidates_assignments` `invalidates_active_assignment` `mission_needs_a_slot` `already_owner` `slot_full` `already_assigned`<br>**Admin:** `has_open_assignments` `owns_open_missions` `last_director` `skill_in_use` |
387	| 422 | Invalid input | `validation_error` `password_too_short` |
388	| 503 | Database busy, retry | `busy` |
389	
390	Malformed mission and slot values are 422 `validation_error`, and every mistake is listed at once: a blank mission or slot name, a headcount below 1, a slot with no required skill, a minimum level outside 1–5, an end date before the start date, or a Director creating a mission without naming its owner.
391	
392	**Problem codes.** These appear inside `problems` and explain each refusal. Adding one means updating this table in the same change.
393	
394	| Code | Raised when | Typical `refs` |
395	|---|---|---|
396	| `inactive` | The person is deactivated | `crew_profile_id`, `slot_id` |
397	| `skill_below_minimum` | A required skill is missing or below the minimum | `crew_profile_id`, `slot_id`, `skill_id` |
398	| `unavailable` | Unavailability overlaps the mission's dates | `crew_profile_id`, `slot_id` |
399	| `overlap` | An accepted assignment on another mission overlaps (the message names that mission) | `crew_profile_id`, `mission_id`, `mission_name` |
400	| `slot_has_open_assignments` | Removing a slot that still has crew | `assignment_id`, `crew_profile_id`, `slot_id` |
401	| `headcount_below_open_assignments` | Lowering headcount below the assigned crew (the message names them) | `slot_id`, `crew_profile_ids` |
402	| `invalidates_active_assignment` | A skill change would break an assignment on an Active mission | `mission_id`, `skill_id` |
403	| `slot_unfilled` | Submitting with empty places | `slot_id` |
404	| `proposal_unanswered` | Submitting while a proposal is still waiting for a reply (the message names the person and slot) | `assignment_id`, `slot_id`, `crew_profile_id` |
405	| `already_exists` | Inside a 409 `rule_violation`: the email address is already in use (anywhere on the platform, since login is by email alone; see [TR-13](#tr-13)), a skill name is already in the catalogue (ignoring case), the user already has a crew profile, or a mission already has a live slot with that name (ignoring case; a new mission's slots are also checked against each other, and have no `slot_id` yet) | `email`; `skill_id`; `user_id`, `crew_profile_id`; `slot_id` |
406	| `owner_not_active_lead` | The owner named for a new mission, or for a transfer, isn't a Mission Lead or is deactivated (inside a 409 `rule_violation`) | `user_id` |
407	| `mission_needs_a_slot` | Removing a mission's only slot (also the 409's own code) | `slot_id` |
408	| `already_owner` | Transferring a mission to the Lead who already owns it (also the 409's own code) | `user_id` |
409	| `slot_full` | Proposing someone for a slot with no open places (the message names the slot and mission) | `slot_id` |
410	| `already_assigned` | Proposing someone who already holds an open assignment on this mission (the message names their slot) | `assignment_id`, `crew_profile_id`, `mission_id` |
411	
412	---
413	
414	## 8. CLI
415	
416	| Concern | Behaviour |
417	|---|---|
418	| Client | An `httpx2` wrapper passed into commands, so tests use `TestClient` and need no server |
419	| Auth | Token stored in `~/.config/mission-control/credentials.json` (mode 0600). Cleared on logout, password change or 401. |
420	| References | Missions and assignments by ID. People by email. Skills by name. Slots by name or position. |
421	| Passwords | Hidden prompt only, never a flag. Asked twice when setting one. |
422	| Output | Plain tables. No meaning carried by colour alone. `--json` for scripts. |
423	| Errors | The message, then one bullet per problem, then a hint for known codes |
424	| Exit codes | `0` OK · `1` refused · `2` usage · `3` authentication · `4` unreachable or busy |
425	| Confirmations | Changing a Pending mission, or cancelling, asks first. `--yes` skips the prompt. |
426	
427	```bash
428	# Everyone
429	mc login | logout | whoami | password | inbox
430	mc me show | update | unavailable add|list|remove
431	mc assignments list [--pending] | accept ID | decline ID | withdraw ID --reason R
432	
433	# Leads
434	mc missions create --name N --start D --end D --slot "Commander:1:Piloting>=4,Leadership>=3"
435	mc missions edit | slot add|edit|remove | match ID [--apply]
436	mc missions propose ID --slot S --crew EMAIL | remove-crew ID ASSIGNMENT | submit ID
437	mc crew list | show | history | set-skill EMAIL SKILL LEVEL | unset-skill EMAIL SKILL
438	
439	# Directors
440	mc missions approve ID | reject ID --reason R | transfer ID --owner EMAIL
441	mc missions complete ID | cancel ID --reason R | list | show | history
442	mc users list | add | set-role | deactivate | enable-crew
443	mc skills list | add | rename | remove          mc org show | set-approvals N
444	```
445	
446	---
447	
448	## 9. Delivery plan
449	
450	We deliver in four phases. Each phase ends in something that can be demonstrated and tested.
451	
452	```mermaid
453	flowchart LR
454	    A[1 Pure domain<br/>M0–M5] --> B[2 Persistence<br/>M6–M8] --> C[3 Services<br/>M9–M14] --> D[4 Interfaces<br/>M15–M17]
455	```
456	
457	| Phase | Milestone (what you can show) |
458	|---|---|
459	| 1. Pure domain | Matcher reproduces S2 and S3; lifecycle and permission tables pass, with no database involved |
460	| 2. Persistence | Seeded database matches PRD §9; tenant-scoped queries; login works |
461	| 3. Services | Every scenario passes at the service level (S1, S3b–S8) |
462	| 4. Interfaces | Full golden path (S1) through the real CLI; isolation sweep passes; README smoke test passes |
463	
464	| # | Module | Write these tests first |
465	|---|---|---|
466	| **Phase 1** | | |
467	| M0 | Skeleton | `/health` returns 200 |
468	| M1 | dates | Boundary-day overlap (AC-17) · mission-days · end ≥ start |
469	| M2 | eligibility, passwords | Each ineligibility reason · workload (AC-20) · M7 and P3 checks · 14 characters rejected, 15 accepted |
470	| M3 | matching | S2, S3 · each tie-break · most-constrained first · unfilled · determinism |
471	| M4 | lifecycle, approvals | All submit problems at once (AC-2) · quorum uses saved N · approver rules (AC-8, 11, 12) · failed approval writes nothing |
472	| M5 | permissions | Full action × role table |
473	| **Phase 2** | | |
474	| M6 | schema | Pragmas · rollback · constraints · composite foreign keys |
475	| M7 | repos, seed | Seed matches PRD §9 · scoped `get` · V2 visibility · SQL lint |
476	| M8 | auth | Login · inactive user · expiry · every revocation path · role read fresh |
477	| **Phase 3** | | |
478	| SF | service foundation | Service context (actor + `Repos` + transaction + audit) · `RuleViolation` carrying problems · refused view becomes not-found · fact loaders building `CandidateFacts` / `RosterEntry` / `AssignmentFact` / `ActiveAssignment` from the database · the repository writes Wave 1 needs |
479	| M9 | admin | P1, P7–P10 · last Director (AC-25, 26) |
480	| M10 | crew | Self-only edits (AC-16) · skill rules (AC-23) · reasons hidden (AC-24) |
481	| M11 | missions | M7 · back to Draft (AC-4) · Active freeze · transfer (AC-7) |
482	| M12 | assignments | Propose (AC-14) · overlap on accept (AC-15) · withdraw (S5) · cascades |
483	| M13 | approvals | S1, S6, S7, S8 · audit trail (AC-1) |
484	| M14 | matching service | Preview writes nothing (AC-22) · apply · isolation (AC-31) · S3b |
485	| **Phase 4** | | |
486	| M15 | API | Error mapping: **every** error body has a non-empty `problems` list, 403/404/401/422/503 included · permissions over HTTP · isolation sweep (S9) · scenarios |
487	| M16 | CLI | Reference resolution · `--slot` parser · prompts · exit codes · S1, S4 |
488	| M17 | README | Smoke-test the README commands |
489	
490	**Waves.** Independent modules may be built at the same time, each in its own git worktree ([§10](#working-in-waves-worktrees)), and then reviewed and committed one at a time. Phase 3 runs as:
491	
492	```
493	SF service foundation (on main)
494	  → Wave 1: M9 admin ∥ M10 crew ∥ M11 missions
495	  → M12 assignments
496	  → Wave 3: M13 approvals ∥ M14 matching service
497	```
498	
499	SF comes first so the waves share one service context and one set of fact loaders instead of each writing their own. Earlier pairs that were independent: M3 ∥ M4, M5 ∥ M6.
500	
501	**Definition of done (every module)**
502	- [ ] Tests were written first, and each test name includes the PRD ID it covers.
503	- [ ] `uv run pytest` and `uv run ruff check` both pass on the whole repo.
504	- [ ] No layer-boundary violations ([§10](#10-guidelines-for-implementing-agents)).
505	- [ ] Any new endpoint is added to the isolation sweep.
506	- [ ] The module was verified by actually running it, and the output was shown, not just the test results.
507	- [ ] A read-only review of the diff was done and its findings reported.
508	- [ ] A commit was **proposed**, and made only after the user approved it.
509	
510	---
511	
512	## 10. Guidelines for implementing agents
513	
514	### Source of truth
515	1. The **PRD** decides behaviour. **This document** decides structure. Code follows both.
516	2. **Don't invent behaviour.** If the PRD is silent or contradicts this document, stop and ask. Don't guess, and don't "improve" the rule.
517	3. Work on **one module at a time**, in the order in [§9](#9-delivery-plan). Start a module only when the user has approved it, and never before its dependencies are done.
518	
519	### The loop for each module
520	1. Read the module's row in §9 and every PRD ID it references.
521	2. Write failing tests. Name them after the rule, for example `test_ac15_accept_overlap_names_conflicting_mission`.
522	3. Write the smallest implementation that makes them pass.
523	4. Refactor, then run the **full** suite and `ruff`.
524	5. Verify the behaviour by running it for real (a REPL call, a request, or a CLI command), and show the output.
525	6. Do a read-only review of the diff, and report findings without editing anything.
526	7. Propose a commit message, such as `feat(m12): assignment propose/accept/withdraw`. **Don't commit, and don't start the next module, until the user approves.**
527	
528	### Working in waves (worktrees)
529	- **Approval:** a wave starts only when the user approves every module in it. The modules must not depend on each other.
530	- **Isolation:** each module gets its own worktree and branch, `.worktrees/<module>` on branch `<module>` (e.g. `m9-admin`), created from the current `main`. The agent works only inside it and runs `uv sync` and the tests there.
531	- **Agents don't commit.** Each leaves its changes uncommitted and reports the usual package: tests first, real run, read-only review.
532	- **Review is one branch at a time.** The user reviews only that module's diff against `main`.
533	- **Merge:** after approval, the lead commits on the branch, rebases it onto `main` if `main` has moved (re-running its tests), fast-forwards `main`, and runs the full suite on `main` before the next review.
534	- **Ports:** a real run that starts a server uses port `8000 + module number` (e.g. M11 uses 8011).
535	- **Clean-up:** remove the worktree and branch once merged.
536	
537	### Architecture rules (never break these)
538	- `domain/` imports nothing from `infra/`, `services/`, `api/` or `sqlite3`.
539	- All SQL lives in `infra/repositories/`, and every query filters on `org_id`.
540	- `org_id` comes only from the `Actor`. Never read it from request input.
541	- Every mutating service calls `touch_for_change()` first, and writes an audit event in the same transaction.
542	- Writes open `BEGIN IMMEDIATE` **before** running checks.
543	- Errors use the codes in [§7](#7-api). Adding a code means updating that table in the same change.
544	
545	### Coding conventions
546	- Type hints everywhere. Frozen dataclasses for domain records. No module-level mutable state.
547	- `date` objects in the domain, ISO strings only at the database and API edges. Timestamps are UTC.
548	- Use PRD vocabulary in names: `open_places`, `eligible_approver`, `workload`.
549	- Keep routers thin: validate, call one service, return.
550	
551	### Testing conventions
552	- Use the `seeded_db` fixture for PRD scenarios, and `tests/builders.py` for edge cases.
553	- Every test gets its own database. No network calls. No reliance on the current date: pass dates in.
554	- Never weaken or delete a test to make it pass. If a test looks wrong, raise it.
555	
556	### Stop and ask before
557	- adding a dependency;
558	- changing the schema (and if you do, update [Appendix A](#appendix-a-schema-sql) as well);
559	- adding an endpoint, error code or CLI command that isn't in this document;
560	- any case where the PRD looks ambiguous or a PRD scenario's expected outcome seems wrong.
561	
562	---
563	
564	## 11. Setup and testing
565	
566	```bash
567	uv sync
568	uv run mc-admin seed --reset      # load PRD §9 data
569	uv run mc-server                  # API on 127.0.0.1:8000
570	uv run mc login --email lee@aurora.example
571	uv run pytest
572	```
573	
574	Settings: `MC_DATABASE_PATH` · `MC_TOKEN_TTL_HOURS=12` · `MC_DB_BUSY_TIMEOUT_MS=5000`
575	
576	| Level | Database | Covers |
577	|---|---|---|
578	| Unit | none | Domain rules, matcher, lifecycle, permission table |
579	| Integration | temporary file | Services, rollback, constraints, audit, SQL lint |
580	| API | temporary file | Error codes, auth, permissions, isolation sweep, scenarios S1 and S3b–S9 |
581	| CLI | temporary file | S1 and S4 end to end, `--json`, errors, exit codes, prompts |
582	
583	- **Shared seed.** `seed/data.py` drives both the demo and the tests, so they can't drift apart.
584	- **Isolated databases.** Every test gets a fresh SQLite file under `tmp_path`.
585	- **Fixtures.** `seeded_db` for scenarios; `tests/builders.py` for focused edge cases.
586	
587	---
588	
589	## Appendix A: Schema SQL
590	
591	The SQL becomes `infra/schema.sql`.
592	
593	**Conventions**
594	- Tables are `STRICT`, which needs SQLite 3.37 or later. `init_db` checks `sqlite3.sqlite_version` and refuses to start on anything older.
595	- Every tenant-owned table has `org_id NOT NULL` and `UNIQUE (org_id, id)`. That unique pair is the target for every reference from another tenant table, so a row can never point into another organisation.
596	- Dates are stored as `TEXT` in `YYYY-MM-DD` form. `date(x) IS x` rejects badly formed dates. Plain `=` wouldn't work here: it returns NULL on bad input, and a NULL check passes.
597	- Timestamps are UTC ISO `TEXT`, with the default `strftime('%Y-%m-%dT%H:%M:%fZ','now')`. Below this is written as `<now>`.
598	- All foreign keys are `ON DELETE RESTRICT` (SQLite's default). The only exception is `slot_requirements`, which cascades from its slot. Domain rows are never hard-deleted except unused skills (P1) and replaced slot requirements.
599	
600	### Organisations, users and sessions
601	
602	```sql
603	PRAGMA user_version = 1;
604	
605	CREATE TABLE organisations (
606	  id                 INTEGER PRIMARY KEY,
607	  name               TEXT    NOT NULL,
608	  slug               TEXT    NOT NULL UNIQUE,
609	  required_approvals INTEGER NOT NULL DEFAULT 1 CHECK (required_approvals >= 1),   -- A1
610	  created_at         TEXT    NOT NULL DEFAULT (<now>)
611	) STRICT;
612	
613	CREATE TABLE users (
614	  id            INTEGER PRIMARY KEY,
615	  org_id        INTEGER NOT NULL REFERENCES organisations(id),
616	  email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,        -- login is by email only
617	  name          TEXT    NOT NULL CHECK (length(trim(name)) > 0),
618	  role          TEXT    NOT NULL CHECK (role IN ('director','lead','crew')),
619	  password_hash TEXT    NOT NULL,                               -- Argon2id encoded hash
620	  is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
621	  created_at    TEXT    NOT NULL DEFAULT (<now>),
622	  updated_at    TEXT    NOT NULL DEFAULT (<now>),
623	  UNIQUE (org_id, id)
624	) STRICT;
625	CREATE INDEX users_org_role ON users(org_id, role, is_active);
626	
627	CREATE TABLE auth_tokens (                                      -- not tenant-owned; reached only via token hash
628	  id         INTEGER PRIMARY KEY,
629	  user_id    INTEGER NOT NULL REFERENCES users(id),
630	  token_hash TEXT    NOT NULL UNIQUE,                           -- SHA-256 hex; raw token never stored
631	  created_at TEXT    NOT NULL DEFAULT (<now>),
632	  expires_at TEXT    NOT NULL,
633	  revoked_at TEXT
634	) STRICT;
635	CREATE INDEX auth_tokens_user ON auth_tokens(user_id) WHERE revoked_at IS NULL;
636	```
637	
638	### Crew, skills and availability
639	
640	```sql
641	CREATE TABLE crew_profiles (
642	  id           INTEGER PRIMARY KEY,                             -- stable identifier for matcher ties
643	  org_id       INTEGER NOT NULL,
644	  user_id      INTEGER NOT NULL UNIQUE,                         -- at most one profile per user (P9)
645	  display_name TEXT    NOT NULL CHECK (length(trim(display_name)) > 0),   -- P4
646	  bio          TEXT,
647	  created_at   TEXT    NOT NULL DEFAULT (<now>),
648	  updated_at   TEXT    NOT NULL DEFAULT (<now>),
649	  UNIQUE (org_id, id),
650	  FOREIGN KEY (org_id, user_id) REFERENCES users(org_id, id)
651	) STRICT;
652	
653	CREATE TABLE skills (
654	  id         INTEGER PRIMARY KEY,                               -- stable across renames (P1)
655	  org_id     INTEGER NOT NULL REFERENCES organisations(id),
656	  name       TEXT    NOT NULL CHECK (length(trim(name)) > 0),
657	  category   TEXT,
658	  created_at TEXT    NOT NULL DEFAULT (<now>),
659	  UNIQUE (org_id, id),
660	  UNIQUE (org_id, name COLLATE NOCASE)
661	) STRICT;
662	
663	CREATE TABLE crew_skills (
664	  org_id          INTEGER NOT NULL,
665	  crew_profile_id INTEGER NOT NULL,
666	  skill_id        INTEGER NOT NULL,
667	  level           INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),   -- P2
668	  updated_by_id   INTEGER NOT NULL,
669	  updated_at      TEXT    NOT NULL DEFAULT (<now>),
670	  PRIMARY KEY (crew_profile_id, skill_id),
671	  FOREIGN KEY (org_id, crew_profile_id) REFERENCES crew_profiles(org_id, id),
672	  FOREIGN KEY (org_id, skill_id)        REFERENCES skills(org_id, id),   -- RESTRICT blocks deleting used skills
673	  FOREIGN KEY (org_id, updated_by_id)   REFERENCES users(org_id, id)
674	) STRICT;
675	CREATE INDEX crew_skills_skill ON crew_skills(skill_id);
676	
677	CREATE TABLE unavailability (
678	  id              INTEGER PRIMARY KEY,
679	  org_id          INTEGER NOT NULL,
680	  crew_profile_id INTEGER NOT NULL,
681	  start_date      TEXT    NOT NULL CHECK (date(start_date) IS start_date),
682	  end_date        TEXT    NOT NULL CHECK (date(end_date) IS end_date),
683	  reason          TEXT    NOT NULL CHECK (length(trim(reason)) > 0),   -- P5
684	  created_at      TEXT    NOT NULL DEFAULT (<now>),
685	  CHECK (end_date >= start_date),                                         -- M2
686	  UNIQUE (org_id, id),
687	  FOREIGN KEY (org_id, crew_profile_id) REFERENCES crew_profiles(org_id, id)
688	) STRICT;
689	CREATE INDEX unavailability_profile ON unavailability(crew_profile_id, start_date);
690	```
691	
692	### Missions, slots and requirements
693	
694	```sql
695	CREATE TABLE missions (
696	  id                 INTEGER PRIMARY KEY,
697	  org_id             INTEGER NOT NULL,
698	  name               TEXT    NOT NULL CHECK (length(trim(name)) > 0),
699	  start_date         TEXT    NOT NULL CHECK (date(start_date) IS start_date),
700	  end_date           TEXT    NOT NULL CHECK (date(end_date) IS end_date),
701	  status             TEXT    NOT NULL DEFAULT 'draft'
702	                     CHECK (status IN ('draft','pending_approval','active','completed','cancelled')),
703	  owner_id           INTEGER NOT NULL,                          -- must be an active Lead: enforced in services (M1)
704	  created_by_id      INTEGER NOT NULL,                          -- kept separately for approver eligibility (A2)
705	  approval_round     INTEGER NOT NULL DEFAULT 0 CHECK (approval_round >= 0),
706	  approvals_required INTEGER CHECK (approvals_required >= 1),  -- N copied at submit (A1)
707	  created_at         TEXT    NOT NULL DEFAULT (<now>),
708	  updated_at         TEXT    NOT NULL DEFAULT (<now>),
709	  CHECK (end_date >= start_date),
710	  CHECK (status IN ('draft','cancelled') OR approvals_required IS NOT NULL),
711	  UNIQUE (org_id, id),
712	  FOREIGN KEY (org_id, owner_id)      REFERENCES users(org_id, id),
713	  FOREIGN KEY (org_id, created_by_id) REFERENCES users(org_id, id)
714	) STRICT;
715	CREATE INDEX missions_org_status ON missions(org_id, status);
716	CREATE INDEX missions_owner      ON missions(owner_id, status);
717	
718	CREATE TABLE slots (
719	  id         INTEGER PRIMARY KEY,
720	  org_id     INTEGER NOT NULL,
721	  mission_id INTEGER NOT NULL,
722	  name       TEXT    NOT NULL CHECK (length(trim(name)) > 0),
723	  headcount  INTEGER NOT NULL CHECK (headcount >= 1),           -- M2
724	  position   INTEGER NOT NULL CHECK (position >= 1),            -- matcher tie-break: listed order
725	  removed_at TEXT,                                               -- soft delete keeps past assignments' history
726	  UNIQUE (org_id, id),
727	  UNIQUE (org_id, mission_id, id),                               -- lets assignments prove slot ∈ mission
728	  FOREIGN KEY (org_id, mission_id) REFERENCES missions(org_id, id)
729	) STRICT;
730	CREATE UNIQUE INDEX slots_live_position ON slots(mission_id, position) WHERE removed_at IS NULL;
731	
732	CREATE TABLE slot_requirements (
733	  org_id    INTEGER NOT NULL,
734	  slot_id   INTEGER NOT NULL,
735	  skill_id  INTEGER NOT NULL,
736	  min_level INTEGER NOT NULL CHECK (min_level BETWEEN 1 AND 5),
737	  PRIMARY KEY (slot_id, skill_id),
738	  FOREIGN KEY (org_id, slot_id)  REFERENCES slots(org_id, id) ON DELETE CASCADE,
739	  FOREIGN KEY (org_id, skill_id) REFERENCES skills(org_id, id)     -- RESTRICT blocks deleting used skills
740	) STRICT;
741	CREATE INDEX slot_requirements_skill ON slot_requirements(skill_id);
742	```
743	
744	"At least one required skill per slot" (M2) covers more than one row, so the service checks it when a slot is created or edited.
745	
746	### Assignments, approvals and audit
747	
748	```sql
749	CREATE TABLE assignments (
750	  id              INTEGER PRIMARY KEY,
751	  org_id          INTEGER NOT NULL,
752	  mission_id      INTEGER NOT NULL,
753	  slot_id         INTEGER NOT NULL,
754	  crew_profile_id INTEGER NOT NULL,
755	  status          TEXT    NOT NULL DEFAULT 'proposed'
756	                  CHECK (status IN ('proposed','accepted','declined','withdrawn','removed','completed','cancelled')),
757	  proposed_by_id  INTEGER NOT NULL,
758	  reason          TEXT,                                          -- decline (optional) / withdraw (required)
759	  created_at      TEXT    NOT NULL DEFAULT (<now>),
760	  updated_at      TEXT    NOT NULL DEFAULT (<now>),
761	  CHECK (status <> 'withdrawn' OR length(trim(coalesce(reason, ''))) > 0),   -- S3
762	  UNIQUE (org_id, id),
763	  FOREIGN KEY (org_id, mission_id)          REFERENCES missions(org_id, id),
764	  FOREIGN KEY (org_id, mission_id, slot_id) REFERENCES slots(org_id, mission_id, id),
765	  FOREIGN KEY (org_id, crew_profile_id)     REFERENCES crew_profiles(org_id, id),
766	  FOREIGN KEY (org_id, proposed_by_id)      REFERENCES users(org_id, id)
767	) STRICT;
768	CREATE UNIQUE INDEX assignments_one_open_per_mission                -- S1
769	  ON assignments(mission_id, crew_profile_id) WHERE status IN ('proposed','accepted');
770	CREATE INDEX assignments_slot    ON assignments(slot_id, status);
771	CREATE INDEX assignments_profile ON assignments(crew_profile_id, status);   -- overlap + workload lookups
772	
773	CREATE TABLE approvals (
774	  id          INTEGER PRIMARY KEY,
775	  org_id      INTEGER NOT NULL,
776	  mission_id  INTEGER NOT NULL,
777	  round       INTEGER NOT NULL CHECK (round >= 1),
778	  director_id INTEGER NOT NULL,
779	  decision    TEXT    NOT NULL CHECK (decision IN ('approve','reject')),
780	  reason      TEXT,
781	  created_at  TEXT    NOT NULL DEFAULT (<now>),
782	  CHECK (decision = 'approve' OR length(trim(coalesce(reason, ''))) > 0),   -- rejection needs a reason
783	  UNIQUE (mission_id, round, director_id),                       -- A3
784	  UNIQUE (org_id, id),
785	  FOREIGN KEY (org_id, mission_id)  REFERENCES missions(org_id, id),
786	  FOREIGN KEY (org_id, director_id) REFERENCES users(org_id, id)
787	) STRICT;
788	
789	CREATE TABLE audit_events (                                      -- append-only (V1)
790	  id              INTEGER PRIMARY KEY,
791	  org_id          INTEGER NOT NULL REFERENCES organisations(id),
792	  actor_id        INTEGER NOT NULL,
793	  event           TEXT    NOT NULL,                              -- e.g. 'mission.submitted', 'assignment.accepted'
794	  mission_id      INTEGER,
795	  assignment_id   INTEGER,
796	  crew_profile_id INTEGER,
797	  from_status     TEXT,
798	  to_status       TEXT,
799	  reason          TEXT,
800	  data            TEXT    NOT NULL DEFAULT '{}' CHECK (json_valid(data)),   -- names at the time of the event
801	  created_at      TEXT    NOT NULL DEFAULT (<now>),
802	  FOREIGN KEY (org_id, actor_id)        REFERENCES users(org_id, id),
803	  FOREIGN KEY (org_id, mission_id)      REFERENCES missions(org_id, id),
804	  FOREIGN KEY (org_id, assignment_id)   REFERENCES assignments(org_id, id),
805	  FOREIGN KEY (org_id, crew_profile_id) REFERENCES crew_profiles(org_id, id)
806	) STRICT;
807	CREATE INDEX audit_events_mission ON audit_events(mission_id, created_at);
808	CREATE INDEX audit_events_profile ON audit_events(crew_profile_id, created_at);
809	CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events
810	  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
811	CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events
812	  BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
813	```
814	
815	Composite foreign keys are only checked when every column in them is non-NULL, so the optional references on `audit_events` work as expected.
816	
817	---
818	
819	## Appendix B: Trade-offs and considerations
820	
821	The main sections reference these decisions by ID, for example [TR-1](#tr-1).
822	
823	### B.1 Key decisions
824	
825	| ID | Decision | Alternatives considered | Why we chose it | What it costs / when to revisit |
826	|---|---|---|---|---|
827	| <a id="tr-1"></a>TR-1 | **SQLite** | Postgres | No setup; one file; real constraints, partial indexes, foreign keys | One writer at a time. Move to Postgres for multiple instances or high write volume. |
828	| <a id="tr-2"></a>TR-2 | **Hand-written SQL** (`sqlite3`) | SQLAlchemy ORM | Every query is visible and easy to check for `org_id`; no hidden queries | More boilerplate. Revisit if the schema grows a lot. |
829	| <a id="tr-3"></a>TR-3 | **Shared database, `org_id` everywhere** | Database per tenant; Postgres row-level security | Simple, and strong enough when combined with composite foreign keys and tests | Relies on discipline, which our lint and sweep tests enforce. RLS is the upgrade path on Postgres. |
830	| <a id="tr-4"></a>TR-4 | **CLI calls the API** | CLI imports services directly | One place enforces rules; the API is used for real every day | Needs a running server. Tests avoid this with an in-process client. |
831	| <a id="tr-5"></a>TR-5 | **Opaque tokens in the database** | JWTs | Instant revocation on logout, deactivation or password change | One lookup per request, which is trivial at this scale |
832	| <a id="tr-6"></a>TR-6 | **Greedy, deterministic matcher** | Optimal assignment (bipartite matching, ILP) | Explainable ("lowest workload won"), predictable, easy to test | Can occasionally leave a place unfilled when a full roster exists. The matcher only advises, so the Lead can fill it manually. |
833	| <a id="tr-7"></a>TR-7 | **Compute, don't store** (workload, eligibility) | Cached columns | Can never go stale; small data | More reads per request. Add caching only if profiling shows a need. |
834	| <a id="tr-8"></a>TR-8 | **Command endpoints** (`/submit`) | `PATCH {status}` | Each transition has its own guards, audit event and CLI command | More routes |
835	| <a id="tr-9"></a>TR-9 | **Approval rounds** | Delete approvals on revert | History is never lost | Every query must filter by the current round |
836	| <a id="tr-10"></a>TR-10 | **404 for anything not visible** | 403 | Never reveals that another tenant's data exists | Slightly harder to debug. Logs record the real reason. |
837	| <a id="tr-11"></a>TR-11 | **`BEGIN IMMEDIATE` per write** | Optimistic locking or version columns | No race conditions in check-then-write rules | Writes are serialized, which is fine at this scale |
838	| <a id="tr-12"></a>TR-12 | **Integer IDs** | UUIDs | Short and easy to type in the CLI | IDs can be guessed, but 404s and scoping make that harmless |
839	| <a id="tr-13"></a>TR-13 | **Emails unique across the platform** | Unique per organisation, with login by org + email | Login needs only an email; one account per person | Refusing a duplicate email reveals that the address is in use in another organisation. The refusal names only the email, never that organisation or user. |
840	
841	### B.2 Risks
842	
843	| Risk | Mitigation |
844	|---|---|
845	| A new endpoint leaks data across tenants | Scoped repositories, composite foreign keys, a route inventory test that fails CI, and the isolation sweep |
846	| Rules drift between layers | Rules exist only in `domain/`. The CLI has none. Services call domain functions. |
847	| The greedy matcher leaves a fixable gap | The gap is reported as unfilled. Manual proposals are still possible. Optimal matching is a documented upgrade. |
848	| SQLite lock contention | Short transactions, `busy_timeout`, and a clear 503 `busy` that the CLI retries or reports |
849	| Agents invent behaviour when the PRD is silent | §10 guidelines: stop and ask, and never guess |
850	
851	### B.3 Scaling path (not in v1)
852	
853	1. Postgres with row-level security.
854	2. Several API instances behind a load balancer.
855	3. A background worker for notifications and date-driven transitions.
856	4. Optimal matching as an option for large organisations.
857
````

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && cat docs/prd.md
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && cat docs/cli-ux.md docs/phase-reviews.md docs/backlog.md
```

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && cat .claude/skills/cli-ux/SKILL.md .claude/skills/cli-ux/references/*.md
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

````
# CLI UX: `mc missions match`

Mock sessions for the matcher preview, written with the `cli-ux` skill (design mode). The service
(`services/matching.preview`, M14) returns the data. The CLI (M16) renders it as shown here.
Seed data is PRD §9. Names are the seeded display names.

**Conventions used below**
- `stdout` gets the data: the heading, the table and the summary line. `stderr` gets refusals and the `Next:` hints.
- On a TTY, `✓` is green, `!` is yellow and `✗` is red. The symbol always carries the meaning, so colour is never the only signal. Piped output or `NO_COLOR` gives the same text with no escape codes.
- **Plain-text markers.** The CLI uses plain words instead of symbols when stdout's encoding isn't UTF-8, or when `NO_COLOR` is set or `TERM=dumb`. Everything else stays the same. The mapping is:

  | Symbol | Plain text |
  |---|---|
  | `✓` | `OK:` |
  | `!` | `Note:` |
  | `✗` | `Error:` |
  | `·` (heading separator) | `-` |
  | `–` (date range) | `-` |

- Dates use the friendlier M16 format (`1–10 Mar 2027`). `--json` uses ISO dates.
- **The `--apply` hint** is printed only when the preview's `can_apply` is true, which means the caller owns the mission. A Director's preview never shows it. The hint is marked *available after M12*. Until then the CLI doesn't offer the flag, and the hint isn't printed.
- **Candidates.** Crew who hold a proposed or accepted assignment on the mission are never suggested for it, and neither is anyone who declined, withdrew or was removed from it.

## Help

```
$ mc missions match --help
Usage: mc missions match MISSION_ID [--apply] [--json]

  Suggest crew for a draft mission's open places. Nothing is changed.
  Owner or Director.

Options:
  --apply   Propose the suggested crew (owner only; available after M12)
  --json    Print the suggestion as JSON

Example:
  mc missions match 1
```

## S2: a full suggestion (Lee, on a TTY)

```
$ mc missions match 1
Lunar Gateway Resupply · 1–10 Mar 2027 · Draft
✓ Crew suggested for all 3 open places. Nothing has been proposed yet.

  Slot                 Suggested   Workload   Proficiency   Pick
  Flight Engineer      Chen        5 days     3             2
  Mission Specialist   Dana        5 days     4             3
  Commander            Ana         0 days     9             1

  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload
  wins, then highest proficiency (sum of the required skill levels).

Next: mc missions match 1 --apply    proposes Ana, Chen and Dana (available after M12)
```
Exit `0`.

**Ruth (Director)** sees the same heading, summary line and table. There is no `Next:` line, because `can_apply` is false for her.

## S3: an unfilled place (Nora)

```
$ mc missions match 2
Asteroid Survey · 5–12 Mar 2027 · Draft
! Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.

  Slot        Suggested   Workload   Proficiency   Pick
  Pilot       Ana         0 days     5             1
  Geologist   unfilled (1 place)

  The mission can't be submitted until every place is filled.

Next: mc missions match 2 --apply    proposes Ana for Pilot (available after M12)
      mc missions propose 2 --slot Geologist --crew EMAIL    fill Geologist by hand
```
Exit `0`: the preview worked. The unfilled place is reported, but it isn't an error.

## Refused: the mission isn't a draft (Lee)

The message is the lifecycle's own refusal (`state_problem(status, PREVIEW_MATCH)`). The CLI adds the mission ID, which it already knows, and a hint for each code.

```
$ mc missions match 5
✗ Mission 5: Can't suggest crew for an active mission.
  Only draft missions can be matched. See its crew: mc missions show 5
```
Exit `1`, on stderr. The other states:

| Code | Message | Hint |
|---|---|---|
| `invalid_transition` | `Can't suggest crew for a mission pending approval` | `Only draft missions can be matched. Its places are already filled: mc missions show 6` |
| `mission_final` | `Can't suggest crew for a mission that's completed` (or `cancelled`) | `Only draft missions can be matched. See it: mc missions show 7` |

## Refused: not allowed

```
$ mc missions match 1          # Ben (Crew), who isn't on Gateway
✗ Mission 1 not found.
  See your missions: mc missions list

$ mc missions match 1          # Nora (Lead), who doesn't own Gateway
✗ Only the owner or a Director can see suggested crew for this mission.
  See who owns it: mc missions show 1
```
Exit `1`, on stderr. Ben's refusal looks exactly like an unknown ID (TR-10).

## Piped

```
$ mc missions match 1 | cat
Lunar Gateway Resupply · 1–10 Mar 2027 · Draft
✓ Crew suggested for all 3 open places. Nothing has been proposed yet.

  Slot                 Suggested   Workload   Proficiency   Pick
  Flight Engineer      Chen        5 days     3             2
  Mission Specialist   Dana        5 days     4             3
  Commander            Ana         0 days     9             1

  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload
  wins, then highest proficiency (sum of the required skill levels).
```
There are no escape codes. The `Next:` hint went to stderr, so it shows on the terminal but not in `> file`.

With `NO_COLOR`, `TERM=dumb` or a non-UTF-8 terminal, the markers become plain words:

```
$ NO_COLOR=1 mc missions match 2
Asteroid Survey - 5-12 Mar 2027 - Draft
Note: Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.
...
$ NO_COLOR=1 mc missions match 5
Error: Mission 5: Can't suggest crew for an active mission.
```

## `--json`

```
$ mc missions match 2 --json
{
  "mission": {"id": 2, "name": "Asteroid Survey", "start_date": "2027-03-05", "end_date": "2027-03-12"},
  "can_apply": true,
  "open_places": 2,
  "unfilled_places": 1,
  "slots": [
    {"slot_id": 4, "name": "Pilot", "open_places": 1, "unfilled": 0,
     "suggested": [{"crew_profile_id": 6, "name": "Ana", "workload": 0, "proficiency": 5, "pick": 1}]},
    {"slot_id": 5, "name": "Geologist", "open_places": 1, "unfilled": 1, "suggested": []}
  ]
}
```
The JSON mirrors `MatchPreview`:
- `slots` covers every slot, in listed order. A slot that's already full has `open_places: 0`.
- `suggested` is in pick order.
- `workload` is in mission-days.
- `can_apply` is true only for the mission's owner.

A refusal prints the design §7 error body instead, with the same exit code.

## Exit codes

| Code | When |
|---|---|
| `0` | Preview shown, including when some places are unfilled |
| `1` | Refused: not found, not allowed, or the mission isn't a draft |
| `2` | Usage, e.g. `mc missions match abc` |
| `3` | Not logged in, or the session expired |
| `4` | Server unreachable or busy |
| `130` | Interrupted |

## Checklist (design review)

✓ means the design covers it, ✗ means there's a gap for M16, and n/a means it doesn't apply.

| Item | | Note |
|---|---|---|
| Help with an example | ✓ | Shown above |
| Flags over positionals | ✓ | Only one positional, the mission ID |
| A reaction for every action | ✓ | The summary line, including "Nothing has been proposed yet" |
| Next step suggested | ✓ | The `--apply` hint follows `can_apply`, so it's shown to the owner only. ✗ `--apply` itself waits for M12. |
| Skimmable, aligned table | ✓ | One row per place. A slot with several places gets one row per person. |
| Colour never the only signal | ✓ | `✓ ! ✗` plus words, with plain-text markers (`OK:` / `Note:` / `Error:`) when the output isn't UTF-8 or `NO_COLOR` / `TERM=dumb` is set |
| Errors name the object and the fix | ✓ | The CLI prefixes the mission ID, and each code has a hint. ✗ The domain wording doesn't name the mission. ✗ The 403 message doesn't name the owner. |
| Several problems listed together | n/a | Preview refusals carry one problem. For a single-problem refusal, the CLI must print the message once, not repeat it as a bullet. |
| stdout data, stderr messages | ✓ | |
| No escape codes when piped; `NO_COLOR` | ✓ | |
| Stable `--json` | ✓ | ✗ Still to decide for all commands in M16: does a refusal's JSON body go to stdout or stderr? |
| Documented exit codes | ✓ | |
| `\| head` without a broken-pipe traceback | ✗ | Applies to every command. Handle it in M16. |
| Progress | n/a | A single fast request |
| Prompts and confirmations | n/a | A preview writes nothing. `--apply` doesn't need a prompt, since crew still have to accept. |
| Ctrl+C exits 130 | ✓ | Listed in the exit codes |
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
# Backlog

Things deliberately left as they are for v1, to revisit later. Each entry says what the system does today and what's open.

| Item | Today's behaviour | Open question | From |
|---|---|---|---|
| A Director demoting or deactivating themselves | Allowed, unless they're the last active Director. Deactivating ends their own session. | Should self-demotion or self-deactivation need another Director? | M9 |
| Role changes and new crew profiles for deactivated users | Allowed | Should changes to deactivated users be blocked until reactivation, which is out of scope? | M9 |
| Trimming names and emails | Leading and trailing spaces are removed on create and update | Should other fields (bio, reasons) be normalised the same way everywhere? | M9 |
````

</details>

<details>
<summary>↳ Result</summary>

````
---
name: cli-ux
description: Design or review the user experience of a command-line tool (CLI) or terminal UI (TUI). Use when planning commands, flags, help text, output, prompts or errors, when writing a CLI UX spec or mock terminal sessions, when reviewing CLI code or a CLI diff for usability, or when building interactive or full-screen terminal features (spinners, progress bars, prompts, raw mode, alternate screen, colors, resizing). Triggers on "CLI", "command line", "terminal UI", "TUI", "help text", "error message", "flags", "--json", "progress bar", "spinner", "interactive prompt", "Ctrl+C", "colors in terminal".
---

# CLI and TUI UX

Make terminal tools that are easy to learn, safe to script, and that leave the terminal as they found it.

## Two modes

**Designing.** Start from the user's workflows, not the command list:
1. Write the main workflows as mock terminal sessions: the exact commands typed and the exact output.
2. Apply the core rules below to every command and message.
3. Check the terminal mechanics in [references/terminal-mechanics.md](references/terminal-mechanics.md) for anything interactive, coloured or full-screen.
4. Run the checklist in [references/checklist.md](references/checklist.md) before calling the design done.

**Reviewing.** Read the code or diff and, where possible, run the tool for real, in a terminal and piped (`| cat`), with bad input and with Ctrl+C.
- Walk [references/checklist.md](references/checklist.md).
- Report findings using the output format below.

## Core rules

1. **Follow conventions.** Behave like the tools users already know. Use standard flags: `--help`, `--version`, `-q`, `-v`, `--json`, `--yes`. Use standard exit codes.
2. **Help everywhere.** `tool --help` lists every command with a one-line description, and `tool <cmd> --help` shows usage, arguments, options and an example.
3. **React to every action.** Success says what happened ("Logged out."). Silence is reserved for scriptable and quiet modes.
4. **Errors say what went wrong and how to fix it.** Never show a raw stack trace or back-end error. Name the thing involved and give the next command to run.
5. **Suggest the next step** at the end of common sequences (after `login`, suggest `create`).
6. **Flags over positional arguments** once there is more than one value. Give short forms to frequent flags.
7. **Prompt for missing required input** only when attached to a terminal, and offer sensible defaults. When not interactive, fail with a clear error instead of hanging.
8. **Show progress** for anything over about a second: a spinner for unknown length, a bar or named steps for known length. Progress goes to stderr.
9. **Always an easy way out.** Ctrl+C stops cleanly, restores the terminal, and exits 130. Interactive screens say how to quit.
10. **Write for skimmers.** Paragraphs of at most 3 short sentences, lists over prose, and a few consistent icons or colours used only as markers.
11. **Pipe-safe output.** Data goes to stdout and messages to stderr. Colour, spinners and prompts only when stdout or stdin is a TTY. Honour `NO_COLOR`, and offer `--json` for machines.
12. **Never depend on colour alone** for meaning. Pair it with a word or symbol.

Details, rationale and source for each rule: [references/principles.md](references/principles.md). Before/after examples: [references/examples.md](references/examples.md).

## Review output format

Group findings by severity: **Blocker** (unsafe, or breaks scripts), **Major** (users get stuck), **Minor** (friction). Each finding gives:
- the command or file:line;
- what the user sees today (exact text);
- the rule it breaks;
- a concrete rewrite (exact text, or the code change).

End with what works well, so it isn't changed by accident.
# Review checklist

Run each item for real where you can: in a terminal, piped (`| cat`), with no TTY on stdin (`< /dev/null`), with `NO_COLOR=1`, with bad input, and with Ctrl+C. Mark each item ✓, ✗ (with a finding) or n/a.

## Discoverability
- [ ] `tool`, `tool --help` and `tool <cmd> --help` all work; each command has a one-line description and at least one example.
- [ ] `--version` works.
- [ ] Command and flag names are consistent: same verbs, same `noun verb` order, no near-synonyms.
- [ ] Unknown commands and flags give a suggestion, not just "invalid".

## Input
- [ ] More than one value means named flags, not positional order. Frequent flags have short forms.
- [ ] A missing required input prompts when interactive, and gives a clear error when not. It never hangs.
- [ ] Sensible defaults cover the common case.
- [ ] Secrets are never accepted as flags; they're prompted for with input hidden.
- [ ] Destructive actions ask for confirmation, and `--yes` skips it.
- [ ] Invalid input is rejected before any side effect, and the message says what's valid.

## Feedback and output
- [ ] Every command reports its result in words ("Mission 12 created"), and `--quiet` suppresses it.
- [ ] Anything over about 1 second shows a spinner, a bar or named steps, on stderr, and only on a TTY.
- [ ] The next likely command is suggested at the end of common flows.
- [ ] Text is skimmable: short paragraphs, aligned tables, values truncated by display width.
- [ ] Icons and colours are few, consistent, and never the only signal.

## Errors
- [ ] No raw stack traces or back-end errors without `--verbose` / `--debug`.
- [ ] Each error says what went wrong, names the objects involved, and says how to fix it (ideally the exact next command).
- [ ] Several problems are listed together, one per line.
- [ ] Errors go to stderr, with a documented non-zero exit code.

## Scripting
- [ ] stdout holds only data; messages and progress go to stderr.
- [ ] When piped, there are no colours, spinners or escape codes. `NO_COLOR` and `TERM=dumb` are honoured.
- [ ] `--json` output is stable, documented and complete.
- [ ] Exit codes are documented: 0 ok, 1 failed or refused, 2 usage, 130 interrupted.
- [ ] `tool list | head` exits quietly (no broken-pipe traceback).

## Exit and interruption
- [ ] Ctrl+C stops promptly, cleans up, restores the terminal and exits 130. A second Ctrl+C forces exit.
- [ ] Interactive and full-screen modes show how to quit.
- [ ] After any exit (normal, error, signal), the cursor is visible, echo works and the prompt isn't coloured.

## TUI-specific (if full-screen or raw mode)
- [ ] Uses the alternate screen and always leaves it. The final result is printed after leaving.
- [ ] Raw mode is restored on every exit path, including exceptions.
- [ ] Resizing (SIGWINCH) redraws correctly. Very small sizes degrade gracefully.
- [ ] Rendering doesn't flicker (only changed cells are drawn).
- [ ] Focus is visible and keyboard-movable. Mouse support, if any, is opt-in and copy/paste is still possible.
- [ ] Works with 16 colours. Truecolor only when detected.
# Before and after

## 1. Error message (rules 4, 5, 7)

Before:
```
$ mc missions propose 12 --slot Engineer --crew gus@aurora.example
Error: 409 Conflict {"error":{"code":"rule_violation"}}
```
After:
```
$ mc missions propose 12 --slot Engineer --crew gus@aurora.example
✗ Can't propose Gus Patel for Engineer on Lunar Gateway Resupply
  • Gus has an accepted assignment on Station Reboost overlapping 1–2 Mar 2027

  See who is free: mc missions match 12
```
It says what failed, names everyone involved, and gives the next command. Exit code 1, printed on stderr.

## 2. Flags over positional arguments (rule 6)

Before: `mc missions create "Europa Flyby" 2027-09-01 2027-09-20 lee@aurora.example`
(Which date is which? Is the email the owner or the creator?)

After: `mc missions create --name "Europa Flyby" --start 2027-09-01 --end 2027-09-20 --owner lee@aurora.example`

## 3. Missing required input (rule 7)

Before:
```
$ mc login
Error: --email is required
```
After (interactive):
```
$ mc login
Email: lee@aurora.example
Password: ••••••••••••••••
✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts 12 hours.
  Next: mc inbox
```
After (no TTY, e.g. in CI):
```
$ mc login < /dev/null
✗ No email given and no terminal to prompt on. Pass --email and pipe the password on stdin.
```

## 4. Pipe-safe output (rule 11)

Before: `mc missions list > missions.txt` writes `^[[32mactive^[[0m` and spinner frames into the file.

After:
- On a TTY: a coloured table, with a spinner on stderr while loading.
- Piped: a plain table on stdout, with no escape codes.
- `--json`: a stable JSON array.

Detection: `sys.stdout.isatty()` and `"NO_COLOR" not in os.environ`.

## 5. Ctrl+C in an interactive screen (rule 9, terminal mechanics)

Before: pressing Ctrl+C during a full-screen picker kills the process in raw mode. The shell is left with no echo and a hidden cursor, and the user has to type `reset` blind.

After:
```python
try:
    enter_alt_screen(); hide_cursor(); set_raw()
    choice = run_picker()
except KeyboardInterrupt:
    choice = None
finally:
    restore_mode(); show_cursor(); leave_alt_screen()   # every exit path
if choice is None:
    print("Cancelled.", file=sys.stderr); sys.exit(130)
print(f"✓ Selected {choice.name}")                       # after leaving the alt screen
```

## 6. Reaction plus next step (rules 3, 7)

Before:
```
$ mc missions submit 12
$
```
After:
```
$ mc missions submit 12
✓ Lunar Gateway Resupply submitted for approval (needs 2 of Ruth, Marco, Ingrid).
  You'll see it in `mc missions show 12`; Directors see it in `mc inbox`.
```
# Principles in detail

Sources:
- **[A]** Atlassian, "10 design principles for delightful CLIs" (https://www.atlassian.com/blog/jira-service-management/10-design-principles-for-delightful-clis).
- **[T]** "How Terminals Work" (https://how-terminals-work.vercel.app/).
- **[+]** A widely used convention that neither source covers, added for completeness.

## 1. Align with established conventions [A]
- Follow published style guides (Heroku CLI style guide, Microsoft style guide) and the tools your users already run.
- Use standard flags: `-h/--help`, `--version`, `-q/--quiet`, `-v/--verbose`, `-y/--yes`, `--json`, `--no-color`. [+]
- Exit codes [+]:
  - `0` success;
  - `1` general failure, or the request was refused;
  - `2` usage error (bad flags);
  - `130` interrupted by Ctrl+C (128 + SIGINT);
  - document any others.
- Command shape: `tool <noun> <verb>` or `tool <verb>`. Pick one and use it everywhere.

## 2. Build help into the tool [A]
- Top-level `--help` lists every command, subcommand and alias, each with a short description.
- `tool <cmd> --help` shows the full syntax: usage line, arguments, options with defaults, and at least one example.
- `tool` with no arguments shows short help, not an error. [+]
- An unknown command suggests the closest match ("Did you mean `missions`?"). [+]

## 3. Show progress visually [A]
- A text interface gives no other sign of life. Use a spinner for unknown durations and a progress bar for known ones.
- Split long jobs into named steps ("Seeding database… done", "Starting server…").
- Draw progress on stderr, and only on a TTY. When piped, print nothing or one line per step. [+][T]

## 4. A reaction for every action [A]
- Every command confirms what happened: `forge logout` gives "Logged out."
- Confirm with the result, not the verb: "Mission 12 submitted for approval (needs 2 approvals)", not "OK".
- `--quiet` suppresses confirmations. Scripts rely on exit codes. [+]

## 5. Human-readable errors [A]
- Never print a raw back-end error or stack trace. Show it only with `--verbose` or `--debug`.
- Each error says what went wrong and how to fix it. Link to more information if it exists.
- Name the objects involved, in the user's terms: "Gus has an accepted assignment on Station Reboost overlapping 1–2 Mar", not "constraint violation".
- When several things are wrong, list them all at once, one per line. [+]
- Errors go to stderr, with a non-zero exit code. [+]

## 6. Support skim-readers [A]
- Keep each paragraph to at most 3 sentences, or about 50–75 characters.
- Highlight the key fact with formatting or a list.
- Use a small, consistent set of icons, such as ✓ success, ✗ error, ! warning. They are markers, not decoration.
- Align tables, and truncate long values rather than wrapping them. [+]

## 7. Suggest the next best step [A]
- Find common command sequences and end each one with the likely next command: after `forge login`, suggest `forge create`.
- When something is refused, the hint is the fix ("Remove them first: `mc missions remove-crew 12 34`").

## 8. Consider your options [A]
- When a required option is missing, prompt for it instead of erroring, but only when stdin is a TTY. Without a TTY, error clearly and never block waiting for input. [+]
- Handle every case: no options, some options, and all options.
- Give sensible defaults so common cases need no flags: Forge defaults to the development environment.
- Never take secrets as flags (they end up in shell history and process lists). Prompt with input hidden, or read from stdin or a file. [+]

## 9. Provide an easy way out [A][T]
- Mark the exit paths. Interactive and full-screen modes say how to quit ("q to quit", "Ctrl+C to cancel").
- Ctrl+C must work. Catch SIGINT only to clean up (restore the terminal, remove temp files), then exit 130. [T][+]
- Destructive actions ask for confirmation, and `--yes` skips the prompt for scripts. [+]

## 10. Flags over arguments [A]
- Prefer labelled flags to positional arguments, so order needn't be memorised: `forge deploy --environment production --product jira`, not `forge deploy production jira`.
- Offer short forms for frequent flags: `-e production -p jira`.
- A single obvious argument (`tool show <id>`) is fine as a positional. Use flags from the second value onwards.

## 11. Pipe-safe output [+][T]
- stdout is for data, stderr for messages, progress and prompts. Then `tool list | grep x` and `tool list > file` work.
- Check `isatty(stdout)` before emitting colour, spinners or cursor movement.
- Honour `NO_COLOR` (any value disables colour) and a `--no-color` flag. `TERM=dumb` means no escape codes.
- `--json` prints stable, documented, machine-readable output, unchanged by colour or width.

## 12. Accessibility [+]
- Never use colour as the only signal; pair it with words or symbols.
- Avoid relying on Nerd Font or private-use icons, which show as boxes without the font. [T] Offer ASCII fallbacks.
- Keep wording plain. Screen readers read the raw text, so avoid decorative boxes made of characters.
# Terminal mechanics, as practical rules

Based on "How Terminals Work" (https://how-terminals-work.vercel.app/), marked **[T]**. Additions marked **[+]**. Read this before building anything coloured, interactive or full-screen.

## The stack [T]
- Data passes through these layers, inward for keystrokes and outward for output:
  - the terminal emulator (iTerm2, Ghostty, kitty) encodes keys and renders cells;
  - the PTY (pseudo-terminal, in the kernel) and its **line discipline**;
  - the shell (zsh, bash);
  - your program.
- A terminal is a grid of same-sized cells. Each cell holds one character plus style (colour, bold, underline). Everything else is escape sequences.

**Rule:** your program talks to a PTY, not a screen. Output can just as well go to a pipe or a file, so never assume a terminal is attached.

## Is anyone there? (TTY detection) [T][+]
- Check `isatty(stdin)` and `isatty(stdout)` separately.
- No TTY on stdout means no colour, spinners, cursor movement or alternate screen.
- No TTY on stdin means no prompts; fail with a clear message instead.
- `TERM` names the terminal type, and programs look up its capabilities in the **terminfo** database. It's only a string the terminal doesn't enforce, so treat it as a hint. [T]
- `TERM=dumb`, or an empty `TERM`, means plain text only. [+]
- Programs can also ask the terminal directly (e.g. the DA1 "what are you?" query), but only when attached to a TTY and with a timeout. [T]

## Escape codes [T]
- Control sequences start with ESC (byte `0x1B`). CSI sequences are `ESC [ … letter`. Common ones:
  - `ESC[0m` resets all styles;
  - `ESC[2J` clears the screen;
  - `ESC[H` moves the cursor to the home position, and `ESC[5;10H` to row 5, column 10;
  - `ESC[?25l` / `ESC[?25h` hide and show the cursor.
- **Rules:**
  - Always reset styles after styled text (`…ESC[0m`), or colour bleeds into the user's prompt.
  - If you hide the cursor, show it again on every exit path, including errors and Ctrl+C. [T][+]
  - Never write escape codes when not on a TTY; they show up as garbage in files and logs ("weird characters like `^[[34m`"). [T]

## Colour depth [T][+]
- **16 colours:** codes 30–37 normal, 90–97 bright (backgrounds 40–47, 100–107). They work everywhere and follow the user's theme, so they're the safe default.
- **256 colours:** `ESC[38;5;Nm`. Available when `TERM` contains `256color`.
- **Truecolor (24-bit):** `ESC[38;2;R;G;Bm`. Smooth gradients are only possible here. Detect it with `COLORTERM=truecolor` or `24bit`. [+]
- **Rules:**
  - Prefer the 16 named colours for meaning (red error, green success, yellow warning). Users' themes stay in charge, and contrast stays readable.
  - Degrade gracefully from truecolor to 256 to 16 to none.
  - `NO_COLOR` set means no colour at all. [+]

## Input: cooked vs raw mode [T]
- **Cooked (canonical) mode:** the line discipline buffers a whole line. Backspace edits it, and nothing reaches the program until Enter. Shells, `cat` and simple prompts use this.
- **Raw mode:** every key reaches the program immediately, with no editing. vim, htop, less and ssh use this.
- Arrow keys and function keys arrive as escape sequences of several bytes, e.g. `ESC [ A` for Up, and `CSI Z` for Shift+Tab. A program that doesn't decode them prints junk. [T]
- **Rules:**
  - Use cooked mode for simple prompts, so line editing comes free.
  - In raw mode you own everything: echo, editing, cursor and Ctrl+C. **Always restore cooked mode on exit, crash or signal**, or the user's shell is left broken (no echo; they need to run `reset`). [T][+]
  - Prefer a library (prompt_toolkit, Textual, Bubble Tea, Ink, crossterm) over hand-rolled raw mode.

## Signals [T]
- **Ctrl+C:** the terminal sends byte `0x03`. In cooked mode the line discipline turns it into **SIGINT** for the foreground process group before your program sees it. The default action is to terminate.
- **Ctrl+Z:** SIGTSTP, which suspends the process. `fg` resumes it in the foreground, `bg` in the background.
- **Window resize:** SIGWINCH. Query the new size (ioctl `TIOCGWINSZ` / `os.get_terminal_size`) and redraw.
- **In raw mode**, Ctrl+C arrives as plain byte `0x03`, and **your program must handle it itself**. [T]
- **Rules:**
  - Catch SIGINT only to clean up (restore terminal mode, show the cursor, leave the alternate screen, remove temp files, roll back), then exit 130. [+]
  - A second Ctrl+C during cleanup should exit immediately. [+]
  - If you support suspend (Ctrl+Z), restore the terminal before stopping, and re-enter raw mode and redraw on SIGCONT. [+]
  - When piped into something that exits early (`tool list | head`), handle SIGPIPE or a broken pipe quietly, without a traceback. [+]
  - Long-running non-interactive commands should respond to SIGTERM like SIGINT. [+]

## The alternate screen [T]
- Terminals have two buffers: the **normal screen**, with scrollback, and the **alternate screen**, a separate canvas.
  - `CSI ?1049h` enters the alternate screen; `CSI ?1049l` leaves it and restores the user's previous output.
  - vim, less, man, htop and tmux all use it.
- **Rules:**
  - Full-screen TUIs use the alternate screen, so they don't overwrite history, and **always leave it on exit**, including on crash or signal.
  - Plain CLIs (output the user wants to keep, copy or scroll back to) must **not** use it.
  - Things in the alternate screen vanish on exit, so print any final result after leaving it.

## Building TUIs [T]
- Lay the screen out as a tree of regions with bounds in cells, recomputed on resize. Exactly one region has focus and receives keys. Tab and arrows move focus, and unhandled events bubble up.
- Render to an in-memory buffer, then write only the changed cells in one go (double buffering). That prevents flicker.
- Hide the cursor while drawing and restore it afterwards.
- Mouse events are opt-in. Without mouse tracking, clicks belong to the terminal's own text selection. With it, clicks arrive as escape sequences with coordinates, and users lose easy copy/paste, so offer a way out (often holding Shift). [T]
- The app owns the cursor position. Clicking doesn't move it (Option+Click works only by faking arrow keys). Don't promise click-to-place behaviour. [T]
- The terminal stores no app state. Modes (e.g. Shift+Tab cycling) live in your program, which must redraw whenever state changes. [T]

## Character width [T]
- Most characters take 1 cell. CJK characters and many emoji take **2**. Nerd Font icons take 1, but render as boxes without the font.
- **Rules:**
  - Measure display width (`wcwidth`), not `len()`, when aligning tables or truncating.
  - Don't require Nerd Fonts. Offer plain fallbacks.
````

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && cat pyproject.toml && git diff pyproject.toml && cat src/mission_control/api/app.py && ls src/mission_control/services tests tests/* | head -80 && cat tests/conftest.py | head -60
```

<details>
<summary>↳ Result</summary>

```
[project]
name = "mission-control"
version = "0.1.0"
description = "Multi-tenant mission planning API and CLI"
requires-python = ">=3.12,<3.13"
dependencies = [
    "argon2-cffi>=25.1.0",
    "fastapi>=0.115",
    "httpx2>=2.13",
    "rich>=13",
    "typer>=0.12",
    "uvicorn>=0.30",
]

[project.scripts]
mc-server = "mission_control.api.app:main"

[dependency-groups]
dev = [
    "pytest>=8",
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
diff --git a/pyproject.toml b/pyproject.toml
index f7f3b35..5dcbb4a 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -6,6 +6,9 @@ requires-python = ">=3.12,<3.13"
 dependencies = [
     "argon2-cffi>=25.1.0",
     "fastapi>=0.115",
+    "httpx2>=2.13",
+    "rich>=13",
+    "typer>=0.12",
     "uvicorn>=0.30",
 ]
 
@@ -14,7 +17,6 @@ mc-server = "mission_control.api.app:main"
 
 [dependency-groups]
 dev = [
-    "httpx2>=2.13",
     "pytest>=8",
     "ruff>=0.6",
 ]
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Mission Control")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
tests/builders.py
tests/conftest.py

src/mission_control/services:
__init__.py
__pycache__
admin.py
assignments.py
auth.py
context.py
crew.py
matching.py
missions

tests:
__pycache__
api
builders.py
conftest.py
integration
unit

tests/__pycache__:
builders.cpython-312.pyc
conftest.cpython-312-pytest-9.1.1.pyc

tests/api:
__pycache__
test_health.py

tests/integration:
__pycache__
conftest.py
test_admin_service.py
test_assignment_writes.py
test_assignments_service.py
test_auth.py
test_crew_service.py
test_db.py
test_facts.py
test_matching_service.py
test_missions_service.py
test_repositories.py
test_repository_sql.py
test_repository_writes.py
test_schema_constraints.py
test_seed.py
test_service_context.py

tests/unit:
domain
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
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control && wc -l services/*.py services/missions/*.py domain/*.py && cat services/matching.py && grep -n "^def \|^class \|^    [a-z_]*:" services/*.py services/missions/*.py | head -200
```

<details>
<summary>↳ Result</summary>

```
       0 services/__init__.py
     368 services/admin.py
     360 services/assignments.py
     141 services/auth.py
     105 services/context.py
     339 services/crew.py
     118 services/matching.py
      57 services/missions/__init__.py
     201 services/missions/changes.py
      93 services/missions/inputs.py
      73 services/missions/loading.py
      20 services/missions/queries.py
     150 services/missions/rules.py
     194 services/missions/slots.py
     106 services/missions/views.py
       0 domain/__init__.py
      59 domain/approvals.py
      29 domain/dates.py
     209 domain/eligibility.py
      59 domain/enums.py
      76 domain/errors.py
      44 domain/events.py
     287 domain/lifecycle.py
      86 domain/matching.py
      11 domain/passwords.py
     232 domain/permissions.py
      77 domain/records.py
    3494 total
"""Matching: suggest crew for a draft mission's open places. Advisory only, so a preview writes
nothing.

The owner or a Director may preview; only the owner may apply. Candidates are the
organisation's crew, minus anyone holding an open assignment on the mission and anyone who
declined, withdrew or was removed from it. The suggestion carries each person's workload and
proficiency, which are what decided the pick.
"""

from dataclasses import dataclass

from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Action, AssignmentStatus
from mission_control.domain.lifecycle import StateConflict, state_problem
from mission_control.domain.matching import proficiency, suggest_roster
from mission_control.domain.permissions import can
from mission_control.domain.records import CandidateFacts, SlotSpec
from mission_control.services.context import ServiceContext, mission_context, visible_mission

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
        mission = visible_mission(ctx, repos, mission_id)
        about = mission_context(repos, mission)
        ctx.authorize(Action.PREVIEW_MATCH, about)
        if problem := state_problem(mission.status, Action.PREVIEW_MATCH):
            raise StateConflict(problem)

        left_out = {a.crew_profile_id for a in repos.missions.assignments(mission.id, _LEFT_OUT)}
        candidates = [
            c
            for c in repos.facts.candidates(excluding_mission_id=mission.id)
            if c.crew_profile_id not in left_out
        ]
        slots = repos.facts.slot_specs(mission.id)

    suggestion = suggest_roster(slots, candidates, mission.window)
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
services/auth.py:23:class Session:
services/auth.py:24:    token: str  # shown to the client once; only its hash is stored
services/auth.py:25:    expires_at: datetime
services/auth.py:26:    user: User
services/auth.py:29:def _now(now: datetime | None) -> datetime:
services/auth.py:33:def login(
services/auth.py:34:    conn: sqlite3.Connection,
services/auth.py:35:    email: str,
services/auth.py:36:    password: str,
services/auth.py:38:    now: datetime | None = None,
services/auth.py:39:    lifetime: timedelta = SESSION_LIFETIME,
services/auth.py:74:def authenticate(
services/auth.py:75:    conn: sqlite3.Connection, token: str | None, *, now: datetime | None = None
services/auth.py:93:def logout(conn: sqlite3.Connection, token: str, *, now: datetime | None = None) -> None:
services/auth.py:98:def revoke_all_sessions(
services/auth.py:99:    conn: sqlite3.Connection, user_id: int, *, now: datetime | None = None
services/auth.py:109:def change_password(
services/auth.py:110:    conn: sqlite3.Connection,
services/auth.py:111:    actor: Actor,
services/auth.py:112:    current_password: str,
services/auth.py:113:    new_password: str,
services/auth.py:115:    now: datetime | None = None,
services/auth.py:134:def _wrong_current_password() -> Forbidden:
services/auth.py:138:def _session_error() -> Unauthenticated:
services/admin.py:28:class _Keep(Enum):
services/admin.py:38:def view_organisation(ctx: ServiceContext) -> Organisation:
services/admin.py:43:def set_required_approvals(ctx: ServiceContext, n: int) -> Organisation:
services/admin.py:64:def list_users(ctx: ServiceContext) -> list[User]:
services/admin.py:69:def view_user(ctx: ServiceContext, user_id: int) -> User:
services/admin.py:74:def create_user(ctx: ServiceContext, email: str, name: str, role: Role, password: str) -> User:
services/admin.py:97:def create_crew_profile(
services/admin.py:98:    ctx: ServiceContext, user_id: int, display_name: str | None = None
services/admin.py:123:def change_role(ctx: ServiceContext, user_id: int, role: Role) -> User:
services/admin.py:154:def deactivate_user(ctx: ServiceContext, user_id: int) -> User:
services/admin.py:182:def _give_crew_profile(
services/admin.py:183:    ctx: ServiceContext, repos: Repos, user: User, display_name: str | None = None
services/admin.py:194:def _has_open_assignments(repos: Repos, user: User, profile: CrewProfile) -> list[Problem]:
services/admin.py:213:def _owns_open_missions(repos: Repos, user: User) -> list[Problem]:
services/admin.py:228:def _last_director(repos: Repos, user: User) -> list[Problem]:
services/admin.py:244:def list_skills(ctx: ServiceContext) -> list[Skill]:
services/admin.py:249:def add_skill(ctx: ServiceContext, name: str, category: str | None = None) -> Skill:
services/admin.py:266:def update_skill(
services/admin.py:267:    ctx: ServiceContext,
services/admin.py:268:    skill_id: int,
services/admin.py:270:    name: str | None = None,
services/admin.py:271:    category: str | None | _Keep = KEEP,
services/admin.py:301:def delete_skill(ctx: ServiceContext, skill_id: int) -> None:
services/admin.py:332:def _name_taken(existing: Skill) -> RuleViolation:
services/admin.py:340:def _refuse(problems: Sequence[Problem], message: str) -> None:
services/admin.py:348:def _required(value: str, what: str) -> str:
services/admin.py:355:def _optional(value: str | None) -> str | None:
services/admin.py:359:def _by_date(missions: list[Mission]) -> list[Mission]:
services/admin.py:363:def _join(names: Iterable[str]) -> str:
services/context.py:22:class ServiceContext:
services/context.py:64:def found[T](value: T | None, what: str) -> T:
services/context.py:71:def visible_mission(ctx: ServiceContext, repos: Repos, mission_id: int) -> Mission:
services/context.py:76:def mission_context(repos: Repos, mission: Mission) -> Context:
services/context.py:85:def return_to_draft(
services/context.py:86:    ctx: ServiceContext, repos: Repos, mission: Mission, cause: Event, mission_name: str
services/context.py:102:def check(problems: Sequence[Problem], message: str) -> None:
services/assignments.py:76:def propose(ctx: ServiceContext, mission_id: int, slot_id: int, crew_profile_id: int) -> Assignment:
services/assignments.py:114:def accept(ctx: ServiceContext, assignment_id: int) -> Assignment:
services/assignments.py:130:def decline(ctx: ServiceContext, assignment_id: int, reason: str | None = None) -> Assignment:
services/assignments.py:142:def withdraw(ctx: ServiceContext, assignment_id: int, reason: str | None) -> Assignment:
services/assignments.py:160:def remove(ctx: ServiceContext, assignment_id: int) -> Assignment:
services/assignments.py:174:def my_assignments(ctx: ServiceContext, pending: bool = False) -> list[AssignmentSummary]:
services/assignments.py:187:def cascade_mission_end(
services/assignments.py:188:    ctx: ServiceContext, mission: Mission, final_status: MissionStatus
services/assignments.py:220:def _load(
services/assignments.py:221:    ctx: ServiceContext, repos: Repos, assignment_id: int
services/assignments.py:234:def _slot_specs(repos: Repos, mission: Mission) -> dict[int, SlotSpec]:
services/assignments.py:239:def _slot_of(repos: Repos, mission: Mission, assignment: Assignment) -> SlotSpec:
services/assignments.py:245:def _about(profile: CrewProfile) -> Context:
services/assignments.py:253:def _check_state(action: Action, current: AssignmentStatus | None, mission: Mission) -> None:
services/assignments.py:259:def _already_on_mission(
services/assignments.py:260:    repos: Repos, mission: Mission, slots: Mapping[int, SlotSpec], profile: CrewProfile
services/assignments.py:281:def _slot_full(mission: Mission, slot: SlotSpec) -> list[Problem]:
services/assignments.py:291:def _ineligibility(
services/assignments.py:292:    repos: Repos, mission: Mission, slot: SlotSpec, profile: CrewProfile
services/assignments.py:299:def _refuse(problems: Sequence[Problem], message: str) -> None:
services/assignments.py:310:def _change(
services/assignments.py:311:    ctx: ServiceContext,
services/assignments.py:312:    repos: Repos,
services/assignments.py:313:    action: Action,
services/assignments.py:314:    assignment: Assignment,
services/assignments.py:315:    mission: Mission,
services/assignments.py:316:    slot: SlotSpec,
services/assignments.py:317:    profile: CrewProfile,
services/assignments.py:318:    reason: str | None = None,
services/assignments.py:329:def _after_roster_change(
services/assignments.py:330:    ctx: ServiceContext, repos: Repos, mission: Mission, action: Action
services/assignments.py:336:def _audit(
services/assignments.py:337:    ctx: ServiceContext,
services/assignments.py:338:    event: Event,
services/assignments.py:339:    assignment: Assignment,
services/assignments.py:340:    from_status: AssignmentStatus | None,
services/assignments.py:341:    to_status: AssignmentStatus,
services/assignments.py:342:    mission: Mission,
services/assignments.py:343:    slot: SlotSpec,
services/assignments.py:344:    profile: CrewProfile,
services/assignments.py:345:    reason: str | None = None,
services/missions/queries.py:9:def list_missions(ctx: ServiceContext) -> list[Mission]:
services/missions/queries.py:15:def get_mission(ctx: ServiceContext, mission_id: int) -> MissionView:
services/crew.py:34:class SkillLevel:
services/crew.py:35:    skill_id: int
services/crew.py:36:    skill_name: str
services/crew.py:37:    level: int
services/crew.py:41:class UnavailabilityView:
services/crew.py:44:    id: int
services/crew.py:45:    window: DateRange
services/crew.py:46:    reason: str | None
services/crew.py:50:class CrewView:
services/crew.py:53:    crew_profile_id: int
services/crew.py:54:    user_id: int
services/crew.py:55:    name: str
services/crew.py:56:    email: str
services/crew.py:57:    active: bool
services/crew.py:58:    bio: str | None
services/crew.py:59:    skills: tuple[SkillLevel, ...]  # by skill name
services/crew.py:60:    unavailability: tuple[UnavailabilityView, ...]  # by start date
services/crew.py:66:def list_crew(ctx: ServiceContext) -> list[CrewView]:
services/crew.py:79:def view_crew(ctx: ServiceContext, crew_profile_id: int) -> CrewView:
services/crew.py:86:def list_unavailability(ctx: ServiceContext, crew_profile_id: int) -> list[UnavailabilityView]:
services/crew.py:92:def assignment_history(ctx: ServiceContext, crew_profile_id: int) -> list[AssignmentSummary]:
services/crew.py:103:def update_details(
services/crew.py:104:    ctx: ServiceContext,
services/crew.py:105:    crew_profile_id: int,
services/crew.py:107:    display_name: str | None = None,
services/crew.py:108:    bio: str | None = None,
services/crew.py:131:def add_unavailability(
services/crew.py:132:    ctx: ServiceContext, crew_profile_id: int, start: date, end: date, reason: str
services/crew.py:161:def remove_unavailability(
services/crew.py:162:    ctx: ServiceContext, crew_profile_id: int, unavailability_id: int
services/crew.py:184:def set_skill_level(
services/crew.py:185:    ctx: ServiceContext, crew_profile_id: int, skill_id: int, level: int
services/crew.py:208:def remove_skill_level(ctx: ServiceContext, crew_profile_id: int, skill_id: int) -> None:
services/crew.py:228:def _about(profile: CrewProfile) -> Context:
services/crew.py:233:def _visible_profile(ctx: ServiceContext, crew_profile_id: int, action: Action) -> CrewProfile:
services/crew.py:241:def _own_profile(ctx: ServiceContext, crew_profile_id: int) -> CrewProfile:
services/crew.py:248:def _skill_target(
services/crew.py:249:    ctx: ServiceContext, repos: Repos, crew_profile_id: int, skill_id: int
services/crew.py:258:def _refuse_if_active_assignment_breaks(
services/crew.py:259:    repos: Repos, profile: CrewProfile, skill_id: int, skill_name: str, level: int | None
services/crew.py:272:def _refuse(problems: Sequence[Problem], code: str, several: str) -> None:
services/crew.py:281:def _overlap(
services/crew.py:282:    profile: CrewProfile, mission_id: int, mission_name: str, busy: DateRange, wanted: DateRange
services/crew.py:293:def _period(profile: CrewProfile, window: DateRange) -> dict[str, str]:
services/crew.py:301:def _skill_names(repos: Repos) -> dict[int, str]:
services/crew.py:305:def _view(
services/crew.py:306:    ctx: ServiceContext,
services/crew.py:307:    repos: Repos,
services/crew.py:308:    profile: CrewProfile,
services/crew.py:309:    user: User,
services/crew.py:310:    skill_names: Mapping[int, str],
services/crew.py:331:def _unavailability(
services/crew.py:332:    ctx: ServiceContext, repos: Repos, profile: CrewProfile
services/missions/changes.py:42:def create_mission(
services/missions/changes.py:43:    ctx: ServiceContext,
services/missions/changes.py:45:    name: str,
services/missions/changes.py:46:    start: date,
services/missions/changes.py:47:    end: date,
services/missions/changes.py:48:    slots: Sequence[SlotInput],
services/missions/changes.py:49:    owner_id: int | None = None,
services/missions/changes.py:104:def update_mission(
services/missions/changes.py:105:    ctx: ServiceContext,
services/missions/changes.py:106:    mission_id: int,
services/missions/changes.py:108:    name: str | None = None,
services/missions/changes.py:109:    start: date | None = None,
services/missions/changes.py:110:    end: date | None = None,
services/missions/changes.py:164:def transfer_ownership(ctx: ServiceContext, mission_id: int, new_owner_id: int) -> MissionView:
services/matching.py:31:class SuggestedCrew:
services/matching.py:34:    crew_profile_id: int
services/matching.py:35:    name: str
services/matching.py:36:    workload: int  # mission-days of accepted assignments elsewhere; lower wins
services/matching.py:37:    proficiency: int  # sum of their levels in the slot's required skills; breaks workload ties
services/matching.py:38:    pick: int  # 1 for the matcher's first pick; the most constrained slot is filled first
services/matching.py:42:class SlotSuggestion:
services/matching.py:43:    slot_id: int
services/matching.py:44:    name: str
services/matching.py:45:    open_places: int  # headcount minus open assignments; 0 means nothing to suggest
services/matching.py:46:    suggested: tuple[SuggestedCrew, ...]  # in pick order
services/matching.py:47:    unfilled: int  # open places left with no eligible candidate
services/matching.py:51:class MatchPreview:
services/matching.py:52:    mission_id: int
services/matching.py:53:    mission_name: str
services/matching.py:54:    window: DateRange
services/matching.py:55:    slots: tuple[SlotSuggestion, ...]  # every slot, in listed order
services/matching.py:56:    can_apply: bool  # whether this actor may turn the suggestion into proposals (owner only)
services/matching.py:67:def preview(ctx: ServiceContext, mission_id: int) -> MatchPreview:
services/matching.py:86:    chosen: dict[int, list[SuggestedCrew]] = {s.id: [] for s in slots}
services/matching.py:111:def _suggested(person: CandidateFacts, slot: SlotSpec, pick: int) -> SuggestedCrew:
services/missions/inputs.py:14:class SlotInput:
services/missions/inputs.py:17:    name: str
services/missions/inputs.py:18:    headcount: int
services/missions/inputs.py:19:    requirements: Mapping[int, int] = field(default_factory=dict)
services/missions/inputs.py:25:def refuse_input(problems: Sequence[Problem]) -> None:
services/missions/inputs.py:30:def invalid_input(problems: Sequence[Problem]) -> InvalidInput:
services/missions/inputs.py:36:def invalid(message: str, refs: Mapping[str, int] | None = None) -> Problem:
services/missions/inputs.py:40:def name_problems(name: str) -> list[Problem]:
services/missions/inputs.py:44:def date_problems(start: date, end: date) -> list[Problem]:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control && cat services/missions/views.py services/missions/slots.py | head -320 && grep -n "class\|^    [a-z_]*:" domain/records.py infra/repositories/base.py | head -80
```

<details>
<summary>↳ Result</summary>

```
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
"""Changing a mission's slots: adding one, renaming it or changing its headcount, replacing its
required skills, and removing it. Only the mission's owner can."""

from collections.abc import Mapping

from mission_control.domain.eligibility import SlotEdit, SlotRemoval
from mission_control.domain.errors import Problem, RuleViolation
from mission_control.domain.events import Event
from mission_control.services.context import ServiceContext
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
        if len(repos.missions.slots(mission.id)) == 1:
            raise RuleViolation.of(
                Problem(
                    "mission_needs_a_slot",
                    f"Can't remove {slot.name}: {mission.name} needs at least one slot",
                    {"slot_id": slot.id},
                )
            )
        refuse_if_invalidated(
            repos,
            mission,
            SlotRemoval(slot.id),
            lambda names: (
                f"Can't remove {slot.name} from {mission.name} while {join_names(names)} "
                f"{is_are(names)} assigned to it. Remove them from the mission first."
            ),
        )

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
domain/records.py:4:from dataclasses import dataclass
domain/records.py:13:@dataclass(frozen=True)
domain/records.py:14:class Requirement:
domain/records.py:15:    skill_id: int
domain/records.py:16:    skill_name: str
domain/records.py:17:    min_level: int
domain/records.py:20:@dataclass(frozen=True)
domain/records.py:21:class SlotSpec:
domain/records.py:22:    id: int
domain/records.py:23:    position: int
domain/records.py:24:    name: str
domain/records.py:25:    open_places: int
domain/records.py:26:    requirements: tuple[Requirement, ...]
domain/records.py:29:@dataclass(frozen=True)
domain/records.py:30:class Commitment:
domain/records.py:33:    mission_id: int
domain/records.py:34:    mission_name: str
domain/records.py:35:    window: DateRange
domain/records.py:38:@dataclass(frozen=True)
domain/records.py:39:class CandidateFacts:
domain/records.py:40:    crew_profile_id: int
domain/records.py:41:    name: str
domain/records.py:42:    active: bool
domain/records.py:43:    skills: Mapping[int, int]  # skill_id -> level
domain/records.py:44:    unavailable: tuple[DateRange, ...]
domain/records.py:45:    accepted_elsewhere: tuple[Commitment, ...]
domain/records.py:46:    workload: int
domain/records.py:49:@dataclass(frozen=True)
domain/records.py:50:class RosterEntry:
domain/records.py:54:    assignment_id: int
domain/records.py:55:    slot: SlotSpec
domain/records.py:56:    crew: CandidateFacts
domain/records.py:57:    status: AssignmentStatus
domain/records.py:60:@dataclass(frozen=True)
domain/records.py:61:class AssignmentFact:
domain/records.py:64:    mission_id: int
domain/records.py:65:    mission_status: MissionStatus
domain/records.py:66:    assignment_status: AssignmentStatus
domain/records.py:67:    window: DateRange
domain/records.py:70:@dataclass(frozen=True)
domain/records.py:71:class ActiveAssignment:
domain/records.py:74:    mission_id: int
domain/records.py:75:    mission_name: str
domain/records.py:76:    slot_name: str
domain/records.py:77:    requirements: tuple[Requirement, ...]
infra/repositories/base.py:29:class Scoped:
```

</details>

**🔧 Bash**

```bash
git worktree list && ls .worktrees/ && ls -R .worktrees/m15* 2>/dev/null | grep -v pycache | head -60
```

<details>
<summary>↳ Result</summary>

```
/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control                     91f3810 [main]
/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m15-api  91f3810 [m15-api]
/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli  91f3810 [m16-cli]
m15-api
m16-cli
CLAUDE.md
docs
pyproject.toml
src
tests
uv.lock

.worktrees/m15-api/docs:
backlog.md
brief.md
cli-ux.md
phase-reviews.md
prd.md
technical-design.md

.worktrees/m15-api/src:
mission_control

.worktrees/m15-api/src/mission_control:
__init__.py
api
domain
infra
seed
services

__init__.cpython-312.pyc

.worktrees/m15-api/src/mission_control/api:
__init__.py
app.py

__init__.cpython-312.pyc
app.cpython-312.pyc

.worktrees/m15-api/src/mission_control/domain:
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

__init__.cpython-312.pyc
approvals.cpython-312.pyc
dates.cpython-312.pyc
eligibility.cpython-312.pyc
enums.cpython-312.pyc
errors.cpython-312.pyc
events.cpython-312.pyc
lifecycle.cpython-312.pyc
matching.cpython-312.pyc
passwords.cpython-312.pyc
permissions.cpython-312.pyc
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control && cat infra/repositories/models.py domain/enums.py && sed -n 1,80p services/assignments.py && sed -n 1,60p services/auth.py
```

<details>
<summary>↳ Result</summary>

```
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

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from mission_control.domain.eligibility import ineligibility_reasons
from mission_control.domain.enums import Action, AssignmentStatus, MissionStatus
from mission_control.domain.errors import InvalidInput, Problem, RuleViolation
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
"""Logging in and out, resolving a request's token to an Actor, and changing passwords."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, Unauthenticated
from mission_control.domain.events import Event
from mission_control.domain.passwords import validate_password
from mission_control.domain.permissions import Actor
from mission_control.infra import security
from mission_control.infra.db import read_tx, write_tx
from mission_control.infra.repositories import Repos
from mission_control.infra.repositories.models import User

SESSION_LIFETIME = timedelta(hours=12)

_BAD_LOGIN = Unauthenticated("invalid_credentials", "Email or password is incorrect")


@dataclass(frozen=True)
class Session:
    token: str  # shown to the client once; only its hash is stored
    expires_at: datetime
    user: User


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
        raise _BAD_LOGIN
    verified_hash = found["password_hash"]
    if not security.verify_password(verified_hash, password):
        raise _BAD_LOGIN
    if not found["is_active"]:
        raise _BAD_LOGIN
    upgraded_hash = (
        security.hash_password(password) if security.needs_rehash(verified_hash) else None
    )
    token = security.new_token()
    expires = now + lifetime
    with write_tx(conn):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control && cat domain/errors.py && grep -n '"' domain/lifecycle.py | head -80 && grep -n 'f"\|"[A-Z]' domain/permissions.py | head -60
```

<details>
<summary>↳ Result</summary>

```
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
    Answered as 422. Distinct from plain ValueError, which also signals programming errors.

    `problems` lists every mistake at once; given none, the message is the only one."""

    code = "validation_error"

    def __init__(self, message: str, problems: Sequence[Problem] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.problems = tuple(problems) or (Problem(self.code, message),)
1:"""Mission and assignment state machines, and the checks a mission must pass to be submitted."""
33:# How each mission action reads after "Can't ...", e.g. "Can't approve a mission in draft".
36:        Action.SUBMIT: "submit",
37:        Action.APPROVE: "approve",
38:        Action.REJECT: "reject",
39:        Action.TRANSFER: "transfer",
40:        Action.COMPLETE: "complete",
41:        Action.CANCEL: "cancel",
42:        Action.EDIT_MISSION: "edit",
43:        Action.PREVIEW_MATCH: "suggest crew for",
48:# How each state reads after "a mission ...", e.g. "Can't approve a mission in draft".
51:        M.DRAFT: "in draft",
52:        M.PENDING_APPROVAL: "pending approval",
53:        M.COMPLETED: "that's completed",
54:        M.CANCELLED: "that's cancelled",
60:    """`doing` is the start of the sentence, e.g. "approve" or "withdraw from"."""
62:        return Problem("mission_frozen", f"Can't {doing} an active mission")
63:    code = "mission_final" if status in FINAL else "invalid_transition"
64:    return Problem(code, f"Can't {doing} a mission {_STATE_PHRASE[status]}")
68:    """The mission's state doesn't allow the change. `problem` says why; its code and message
69:    become the refusal's own."""
77:    """A change to a pending mission voids its approval round; otherwise status holds."""
82:    """The mission's status once a change to it is made. Every mutating service calls this
84:    can't be changed, so this raises `StateConflict`."""
92:        raise ValueError(f"{action!r} is not a mission action; use the assignment functions")
96:    """Why mission `action` isn't allowed from `status`, or None if it is. Raises ValueError
97:    for an action that isn't a mission action."""
107:    """The mission's status once `action` succeeds. Check `state_problem` first. Previewing a
108:    match changes nothing, so the status stays as it is."""
110:        raise ValueError(f"{_MISSION_VERB[action]} is not allowed from {status.value}")
161:# How each assignment action reads before "a mission ...".
164:        Action.PROPOSE_CREW: "propose crew for",
165:        Action.ACCEPT: "accept a proposal on",
166:        Action.DECLINE: "decline a proposal on",
167:        Action.WITHDRAW: "withdraw from",
168:        Action.REMOVE_CREW: "remove crew from",
175:# How each assignment action reads before "an assignment ...".
178:        Action.PROPOSE_CREW: "propose",
179:        Action.ACCEPT: "accept",
180:        Action.DECLINE: "decline",
181:        Action.WITHDRAW: "withdraw",
182:        Action.REMOVE_CREW: "remove",
189:        raise ValueError(f"{action!r} is not an assignment action; use the mission functions")
195:    """Why assignment `action` isn't allowed, or None. Mission state is checked before
196:    assignment state. Raises ValueError for an action that isn't an assignment action."""
202:        label = current.value if current else "missing"
204:            "invalid_transition", f"Can't {_ASSIGNMENT_VERB[action]} an assignment that is {label}"
220:    """What an assignment becomes when its mission completes or is cancelled."""
232:    """Accepted crew who are no longer eligible, e.g. after a skill change. Checked at submit
233:    and again at every approval."""
249:    """Everything stopping a Draft mission being submitted, all at once. `slots[i].open_places`
254:    roster order), then too few eligible approvers."""
260:                    "slot_unfilled",
261:                    f"{s.name}: {s.open_places} place{'s' if s.open_places > 1 else ''} unfilled",
262:                    {"slot_id": s.id},
269:                    "proposal_unanswered",
270:                    f"{e.slot.name}: {e.crew.name} hasn't responded to the proposal",
272:                        "assignment_id": e.assignment_id,
273:                        "slot_id": e.slot.id,
274:                        "crew_profile_id": e.crew.crew_profile_id,
282:                "insufficient_approvers",
283:                f"{eligible_approvers} eligible approver{'s' if eligible_approvers != 1 else ''}, "
284:                f"{approvals_required} required",
1:"""Who may do what. `authorize` is the single entry point; it raises Forbidden with a code.
26:    """Facts about the target that the relationship rules need. Unused fields stay None.
118:_ROLE_PLURAL: Mapping[Role, str] = MappingProxyType({D: "Directors", L: "Leads", C: "Crew"})
151:# Completes "Only the mission's owner can ..." / "Only the owner or a Director can ...".
165:_RESPOND_ONLY_TO_OWN = "You can only respond to your own assignments"
168:        Action.VIEW_CREW: "Crew can only view their own profile",
169:        Action.VIEW_ASSIGNMENT_HISTORY: "Crew can only view their own assignment history",
170:        Action.EDIT_OWN_PROFILE: "You can only edit your own profile and availability",
183:        raise Forbidden("role_forbidden", f"{_ROLE_PLURAL[actor.role]} can't {ROLE_PHRASE[action]}")
187:        raise ValueError(f"{action.value} needs context field(s): {', '.join(missing)}")
194:        raise Forbidden("not_owner", f"Only the mission's owner can {_MISSION_PHRASE[action]}")
197:        raise Forbidden("not_owner", f"Only the owner or a Director can {_MISSION_PHRASE[action]}")
200:        raise Forbidden("not_owner", "Leads can only create missions they own")
207:            "role_forbidden", "Only Directors can see other people's unavailability reasons"
211:        raise Forbidden("role_forbidden", "Crew can only view missions they're on")
217:        raise Forbidden("self_skill_edit", "You can't change your own skill levels")
220:        # Creator and roster rules are shared with the approval module. "Already decided" is a
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv sync 2>&1 | tail -2; uv pip list 2>/dev/null | grep -iE "typer|click|rich|httpx|starlette|fastapi|shellingham"; cat src/mission_control/domain/events.py; grep -n "_MISSION_PHRASE" -A 14 src/mission_control/domain/permissions.py | head -30
```

<details>
<summary>↳ Result</summary>

```
Resolved 35 packages in 20ms
Checked 33 packages in 5ms
click                8.5.0
fastapi              0.143.0
httpx2               2.13.1
rich                 15.0.0
shellingham          1.5.4
starlette            1.7.0
typer                0.27.3
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
152:_MISSION_PHRASE: Mapping[Action, str] = MappingProxyType(
153-    {
154-        Action.EDIT_MISSION: "edit this mission",
155-        Action.PROPOSE_CREW: "propose crew for this mission",
156-        Action.REMOVE_CREW: "remove crew from this mission",
157-        Action.APPLY_MATCH: "apply matcher suggestions to this mission",
158-        Action.SUBMIT: "submit this mission",
159-        Action.PREVIEW_MATCH: "see suggested crew for this mission",
160-        Action.COMPLETE: "complete this mission",
161-        Action.CANCEL: "cancel this mission",
162-    }
163-)
164-
165-_RESPOND_ONLY_TO_OWN = "You can only respond to your own assignments"
166-_SELF_ONLY_MESSAGE: Mapping[Action, str] = MappingProxyType(
--
194:        raise Forbidden("not_owner", f"Only the mission's owner can {_MISSION_PHRASE[action]}")
195-
196-    if action in _OWNER_OR_DIRECTOR and actor.role != D and not is_owner:
197:        raise Forbidden("not_owner", f"Only the owner or a Director can {_MISSION_PHRASE[action]}")
198-
199-    if action == Action.CREATE_MISSION and actor.role == L and not is_owner:
200-        raise Forbidden("not_owner", "Leads can only create missions they own")
201-
202-    if action in _CREW_SELF_ONLY and actor.role == C and not is_self:
203-        raise Forbidden("role_forbidden", _SELF_ONLY_MESSAGE[action])
204-
205-    if action == Action.VIEW_UNAVAILABILITY_REASON and actor.role != D and not is_self:
206-        raise Forbidden(
207-            "role_forbidden", "Only Directors can see other people's unavailability reasons"
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python -c "
import httpx2, typer, click, inspect
print([n for n in dir(httpx2) if 'Error' in n or n in ('Client','MockTransport','Response','Request','Timeout')])
import typer.main
print(inspect.signature(typer.Typer.__init__))
"; uv run python -c "import starlette.testclient as t, inspect; print(inspect.getsource(t).count('httpx2')); print(t.TestClient.__mro__)"
```

<details>
<summary>↳ Result</summary>

````
['Client', 'CloseError', 'ConnectError', 'DecodingError', 'HTTPError', 'HTTPStatusError', 'LocalProtocolError', 'MockTransport', 'NetworkError', 'ProtocolError', 'ProxyError', 'ReadError', 'RemoteProtocolError', 'Request', 'RequestError', 'Response', 'SSEError', 'StreamError', 'Timeout', 'TransportError', 'WriteError']
(self, *, name: Annotated[str | None, Doc('\n                The name of this application.\n                Mostly used to set the name for [subcommands](https://typer.tiangolo.com/tutorial/subcommands/), in which case it can be overridden by `add_typer(name=...)`.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(name="users")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10a99a030>, cls: Annotated[type[typer.core.TyperGroup] | None, Doc('\n                The class of this app. Mainly used when [using the Click library underneath](https://typer.tiangolo.com/tutorial/using-click/). Can usually be left at the default value `None`.\n                Otherwise, should be a subtype of `TyperGroup`.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(cls=TyperGroup)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10aca7350>, invoke_without_command: Annotated[bool, Doc('\n                By setting this to `True`, you can make sure a callback is executed even when no subcommand is provided.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(invoke_without_command=True)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ac66de0>, no_args_is_help: Annotated[bool, Doc('\n                If this is set to `True`, running a command without any arguments will automatically show the help page.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(no_args_is_help=True)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad341d0>, subcommand_metavar: Annotated[str | None, Doc("\n                **Note**: you probably shouldn't use this parameter, it is inherited\n                from Click and supported for compatibility.\n\n                ---\n\n                How to represent the subcommand argument in help.\n                ")] = <typer.models.DefaultPlaceholder object at 0x10ad34200>, chain: Annotated[bool, Doc("\n                **Note**: you probably shouldn't use this parameter, it is inherited\n                from Click and supported for compatibility.\n\n                ---\n\n                Allow passing more than one subcommand argument.\n                ")] = <typer.models.DefaultPlaceholder object at 0x10ad34230>, result_callback: Annotated[collections.abc.Callable[..., Any] | None, Doc("\n                **Note**: you probably shouldn't use this parameter, it is inherited\n                from Click and supported for compatibility.\n\n                ---\n\n                A function to call after the group's and subcommand's callbacks.\n                ")] = <typer.models.DefaultPlaceholder object at 0x10ad34260>, context_settings: Annotated[dict[Any, Any] | None, Doc('\n                Pass configurations for the [context](https://typer.tiangolo.com/tutorial/commands/context/).\n                Available configurations can be found in the docs for Click\'s `Context` [here](https://click.palletsprojects.com/en/stable/api/#context).\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad342c0>, callback: Annotated[collections.abc.Callable[..., Any] | None, Doc('\n                Add a callback to the main Typer app. Can be overridden with `@app.callback()`.\n                See [the tutorial about callbacks](https://typer.tiangolo.com/tutorial/commands/callback/) for more details.\n\n                **Example**\n\n                ```python\n                import typer\n\n                def callback():\n                    print("Running a command")\n\n                app = typer.Typer(callback=callback)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad34320>, help: Annotated[str | None, Doc('\n                Help text for the main Typer app.\n                See [the tutorial about name and help](https://typer.tiangolo.com/tutorial/subcommands/name-and-help) for different ways of setting a command\'s help,\n                and which one takes priority.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(help="Some help.")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad34350>, epilog: Annotated[str | None, Doc('\n                Text that will be printed right after the help text.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(epilog="May the force be with you")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad34380>, short_help: Annotated[str | None, Doc('\n                A shortened version of the help text that can be used e.g. in the help table listing subcommands.\n                When not defined, the normal `help` text will be used instead.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(help="A lot of explanation about user management", short_help="user management")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad343b0>, options_metavar: Annotated[str, Doc('\n                In the example usage string of the help text for a command, the default placeholder for various arguments is `[OPTIONS]`.\n                Set `options_metavar` to change this into a different string.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(options_metavar="[OPTS]")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad343e0>, add_help_option: Annotated[bool, Doc("\n                **Note**: you probably shouldn't use this parameter, it is inherited\n                from Click and supported for compatibility.\n\n                ---\n\n                By default each command registers a `--help` option. This can be disabled by this parameter.\n                ")] = <typer.models.DefaultPlaceholder object at 0x10ad34410>, hidden: Annotated[bool, Doc('\n                Hide this command from help outputs. `False` by default.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(hidden=True)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad34440>, deprecated: Annotated[bool, Doc('\n                Mark this command as being deprecated in the help text. `False` by default.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(deprecated=True)\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad34470>, add_completion: Annotated[bool, Doc('\n                Toggle whether or not to add the `--install-completion` and `--show-completion` options to the app.\n                Set to `True` by default.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(add_completion=False)\n                ```\n                ')] = True, rich_markup_mode: Annotated[Literal['markdown', 'rich', None], Doc('\n                Enable markup text if you have Rich installed. This can be set to `"markdown"`, `"rich"`, or `None`.\n                By default, `rich_markup_mode` is `None` if Rich is not installed, and `"rich"` if it is installed.\n                See [the tutorial on help formatting](https://typer.tiangolo.com/tutorial/commands/help/#rich-markdown-and-markup) for more information.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(rich_markup_mode="rich")\n                ```\n                ')] = 'rich', rich_help_panel: Annotated[str | None, Doc('\n                Set the panel name of the command when the help is printed with Rich.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(rich_help_panel="Utils and Configs")\n                ```\n                ')] = <typer.models.DefaultPlaceholder object at 0x10ad344a0>, suggest_commands: Annotated[bool, Doc('\n                As of version 0.20.0, Typer provides [support for mistyped command names](https://typer.tiangolo.com/tutorial/commands/help/#suggest-commands) by printing helpful suggestions.\n                You can turn this setting off with `suggest_commands`:\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(suggest_commands=False)\n                ```\n                ')] = True, pretty_exceptions_enable: Annotated[bool, Doc('\n                If you want to disable [pretty exceptions with Rich](https://typer.tiangolo.com/tutorial/exceptions/#exceptions-with-rich),\n                you can set `pretty_exceptions_enable` to `False`. When doing so, you will see the usual standard exception trace.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(pretty_exceptions_enable=False)\n                ```\n                ')] = True, pretty_exceptions_show_locals: Annotated[bool, Doc('\n                If Rich is installed, [error messages](https://typer.tiangolo.com/tutorial/exceptions/#exceptions-and-errors)\n                will be nicely printed.\n\n                If you set `pretty_exceptions_show_locals=True` it will also include the values of local variables for easy debugging.\n\n                However, if such a variable contains delicate information, you should consider leaving `pretty_exceptions_show_locals=False`\n                (the default) to `False` to enhance security.\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(pretty_exceptions_show_locals=True)\n                ```\n                ')] = False, pretty_exceptions_short: Annotated[bool, Doc('\n                By default, [pretty exceptions formatted with Rich](https://typer.tiangolo.com/tutorial/exceptions/#exceptions-with-rich) hide the long stack trace.\n                If you want to show the full trace instead, you can set the parameter `pretty_exceptions_short` to `False`:\n\n                **Example**\n\n                ```python\n                import typer\n\n                app = typer.Typer(pretty_exceptions_short=False)\n                ```\n                ')] = True)
5
(<class 'starlette.testclient.TestClient'>, <class 'httpx2.Client'>, <class 'httpx2._client.BaseClient'>, <class 'object'>)
````

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && F=$(uv run python -c "import typer.core as c; print(c.__file__)"); grep -n "def format_help\|rich_markup_mode is None\|HAS_RICH\|def main\|def _main\|standalone_mode\|KeyboardInterrupt\|Abort\|def format_usage\|collect_usage_pieces\|suggest" $F | head -60
```

<details>
<summary>↳ Result</summary>

```
21:from .exceptions import Abort, Exit
27:HAS_RICH = parse_boolean_env_var(os.getenv("TYPER_USE_RICH"), default=True)
29:if HAS_RICH:
158:def _main(
164:    standalone_mode: bool = True,
188:                if not standalone_mode:
200:            raise Abort() from e
201:        except KeyboardInterrupt as e:
204:            if not standalone_mode:
206:            if HAS_RICH and rich_markup_mode is not None:
221:        if standalone_mode:
233:    except Abort:
234:        if not standalone_mode:
236:        if HAS_RICH and rich_markup_mode is not None:
241:            _click.echo(_("Aborted!"), file=sys.stderr)
374:            if HAS_RICH and rich_markup_mode == "rich":
837:            if HAS_RICH and rich_markup_mode == "rich":
945:    def _main_shell_completion(
955:    def main(
960:        standalone_mode: bool = True,
969:            standalone_mode=standalone_mode,
975:    def format_help(self, ctx: _click.Context, formatter: _click.HelpFormatter) -> None:
976:        if not HAS_RICH or self.rich_markup_mode is None:
1005:        suggest_commands: bool = True,
1016:        self.suggest_commands = suggest_commands
1047:    def collect_usage_pieces(self, ctx: _click.Context) -> list[str]:
1048:        rv = super().collect_usage_pieces(ctx)
1142:    def _main_shell_completion(
1177:            if self.suggest_commands:
1183:                        suggestions = ", ".join(f"{m!r}" for m in matches)
1185:                        e.message = f"{message}. Did you mean {suggestions}?"
1188:    def main(
1193:        standalone_mode: bool = True,
1202:            standalone_mode=standalone_mode,
1208:    def format_help(self, ctx: _click.Context, formatter: _click.HelpFormatter) -> None:
1209:        if not HAS_RICH or self.rich_markup_mode is None:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && F=$(uv run python -c "import typer.core as c; print(c.__file__)"); sed -n 155,250p $F; sed -n 1040,1060p $F
```

<details>
<summary>↳ Result</summary>

```
    return default_value


def _main(
    self: _click.Command,
    *,
    args: Sequence[str] | None = None,
    prog_name: str | None = None,
    complete_var: str | None = None,
    standalone_mode: bool = True,
    windows_expand_args: bool = True,
    rich_markup_mode: MarkupMode = DEFAULT_MARKUP_MODE,
    **extra: Any,
) -> Any:
    # Originally copied from _click.main(), adopted to handle custom rich exceptions etc
    if args is None:
        args = sys.argv[1:]

        if os.name == "nt" and windows_expand_args:  # pragma: no cover
            args = _click.utils._expand_args(args)
    else:
        args = list(args)

    if prog_name is None:
        prog_name = _click.utils._detect_program_name()

    # Process shell completion requests and exit early.
    self._main_shell_completion(extra, prog_name, complete_var)

    try:
        try:
            with self.make_context(prog_name, args, **extra) as ctx:
                rv = self.invoke(ctx)
                if not standalone_mode:
                    return rv
                # it's not safe to `ctx.exit(rv)` here!
                # note that `rv` may actually contain data like "1" which
                # has obvious effects
                # more subtle case: `rv=[None, None]` can come out of
                # chained commands which all returned `None` -- so it's not
                # even always obvious that `rv` indicates success/failure
                # by its truthiness/falsiness
                ctx.exit()
        except EOFError as e:
            _click.echo(file=sys.stderr)
            raise Abort() from e
        except KeyboardInterrupt as e:
            raise Exit(130) from e
        except _click.exceptions.ClickException as e:
            if not standalone_mode:
                raise
            if HAS_RICH and rich_markup_mode is not None:
                from . import rich_utils

                rich_utils.rich_format_error(e)
            else:
                e.show()
            sys.exit(e.exit_code)
        except OSError as e:
            if e.errno == errno.EPIPE:
                sys.stdout = cast(TextIO, _click.utils.PacifyFlushWrapper(sys.stdout))
                sys.stderr = cast(TextIO, _click.utils.PacifyFlushWrapper(sys.stderr))
                sys.exit(1)
            else:
                raise
    except Exit as e:
        if standalone_mode:
            sys.exit(e.exit_code)
        else:
            # in non-standalone mode, return the exit code
            # note that this is only reached if `self.invoke` above raises
            # an Exit explicitly -- thus bypassing the check there which
            # would return its result
            # the results of non-standalone execution may therefore be
            # somewhat ambiguous: if there are codepaths which lead to
            # `ctx.exit(1)` and to `return 1`, the caller won't be able to
            # tell the difference between the two
            return e.exit_code
    except Abort:
        if not standalone_mode:
            raise
        if HAS_RICH and rich_markup_mode is not None:
            from . import rich_utils

            rich_utils.rich_abort_error()
        else:
            _click.echo(_("Aborted!"), file=sys.stderr)
        sys.exit(1)


class TyperArgument(_click.core.Parameter):
    param_type_name = "argument"

    def __init__(
        self,
        *,
        if name is None:
            raise TypeError("Command has no name.")
        self.commands[name] = cmd

    def get_command(self, ctx: _click.Context, cmd_name: str) -> _click.Command | None:
        return self.commands.get(cmd_name)

    def collect_usage_pieces(self, ctx: _click.Context) -> list[str]:
        rv = super().collect_usage_pieces(ctx)
        rv.append(self.subcommand_metavar)
        return rv

    def format_commands(
        self, ctx: _click.Context, formatter: _click.HelpFormatter
    ) -> None:
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
```

</details>

### 🤖 Claude · 2026-10-12 03:23:14 UTC

Now let me check a couple of typer details for injection and help formatting before writing tests.

**🔧 Bash**

```bash
mkdir -p /tmp/m16probe && cd /tmp/m16probe && cat > probe.py <<'EOF'
import typer, click
from typer.core import TyperCommand, TyperGroup
class Cmd(TyperCommand):
    def collect_usage_pieces(self, ctx):
        args = [p.make_metavar(ctx) for p in self.get_params(ctx) if isinstance(p, click.Argument)]
        return args + ["[--apply]"]
    def format_epilog(self, ctx, formatter):
        if self.epilog:
            formatter.write_paragraph(); formatter.write_text("Example:")
            with formatter.indentation():
                for l in self.epilog.splitlines(): formatter.write(" "*formatter.current_indent + l + "\n")
app = typer.Typer(rich_markup_mode=None, add_completion=False, no_args_is_help=True)
m = typer.Typer(rich_markup_mode=None, no_args_is_help=True, help="Missions")
app.add_typer(m, name="missions")
@m.command("match", cls=Cmd, epilog="mc missions match 1")
def match(mission_id: int = typer.Argument(..., metavar="MISSION_ID"), apply: bool = typer.Option(False, "--apply", help="Propose")):
    """Suggest crew for a draft mission's open places. Nothing is changed.

    Owner or Director."""
    print("ok", mission_id)
@m.command("list")
def lst(): pass
if __name__ == "__main__": app(prog_name="mc")
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python /tmp/m16probe/probe.py missions match --help; uv run python /tmp/m16probe/probe.py missions matc 1; echo "exit $?"; uv run python /tmp/m16probe/probe.py; echo "exit $?"
```

<details>
<summary>↳ Result</summary>

```
Usage: mc missions match [--apply]

  Suggest crew for a draft mission's open places. Nothing is changed.

  Owner or Director.

Arguments:
  MISSION_ID  [required]

Options:
  --apply  Propose
  --help   Show this message and exit.

Example:
  mc missions match 1
Usage: mc missions [OPTIONS] COMMAND [ARGS]...
Try 'mc missions --help' for help.

Error: No such command 'matc'. Did you mean 'match'?
exit 2
Usage: mc [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  missions  Missions
exit 2
```

</details>

### 🤖 Claude · 2026-10-12 03:23:29 UTC

Typer works as expected. Now I'll write the tests first. Let me set up the test infrastructure and test files.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && ls tests/api tests/unit/domain && sed -n 1,40p tests/api/test_health.py && sed -n 1,40p tests/integration/test_matching_service.py
```

<details>
<summary>↳ Result</summary>

```
tests/api:
__pycache__
test_health.py

tests/unit/domain:
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
from fastapi.testclient import TestClient

from mission_control.api.app import create_app


def test_m0_health_returns_200_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
"""M14: the matching service, preview only. Suggests crew for a Draft mission's open places and
writes nothing (PRD §6, AC-18 to AC-22, AC-31, S2, S3, S3b; design §6).

Seed ids (PRD §9): a crew profile's id equals its user's id. Ruth 1 · Lee 4 · Nora 5 · Ana 6 ·
Ben 7 · Chen 8 · Dana 9 · Eli 10 · Fay 11 · Gus 12 · Hana 13 · Sam 14 (Helix) · Kai 16 (Helix).
Missions: Gateway 1 · Asteroid 2 · Reboost 3 · Telescope 5 · Comms 6 · Mars 7 · Payload 8 (Helix).
Gateway slots: Flight Engineer 1 · Mission Specialist 2 · Commander 3. Asteroid: Pilot 4 ·
Geologist 5. Skills: Piloting 1 · Leadership 2.
"""

from datetime import UTC, date, datetime

import pytest

from builders import make_assignment, make_mission, make_slot
from mission_control.domain.dates import DateRange
from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, NotFound, RuleViolation
from mission_control.domain.lifecycle import StateConflict
from mission_control.domain.permissions import Actor
from mission_control.services import matching
from mission_control.services.context import ServiceContext

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)

RUTH = Actor(user_id=1, org_id=1, role=Role.DIRECTOR, crew_profile_id=None)
LEE = Actor(user_id=4, org_id=1, role=Role.LEAD, crew_profile_id=None)
NORA = Actor(user_id=5, org_id=1, role=Role.LEAD, crew_profile_id=None)
ANA = Actor(user_id=6, org_id=1, role=Role.LEAD, crew_profile_id=6)
BEN = Actor(user_id=7, org_id=1, role=Role.CREW, crew_profile_id=7)
SAM = Actor(user_id=14, org_id=2, role=Role.DIRECTOR, crew_profile_id=None)

GATEWAY, ASTEROID, REBOOST, TELESCOPE, COMMS, MARS, PAYLOAD = 1, 2, 3, 5, 6, 7, 8
FLIGHT_ENGINEER, SPECIALIST, COMMANDER, PILOT, GEOLOGIST = 1, 2, 3, 4, 5
PILOTING = 1
ANA_ID, BEN_ID, CHEN_ID, DANA_ID, ELI_ID, KAI_ID = 6, 7, 8, 9, 10, 16
HELIX_CREW = {16, 17, 18, 19}


def as_(conn, actor):
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && ls src/mission_control/seed && grep -n "Skill\|skill" src/mission_control/seed/data.py | head -30
```

<details>
<summary>↳ Result</summary>

```
__init__.py
__pycache__
data.py
loader.py
29:class Skill(NamedTuple):
45:    requirements: Mapping[int, int]  # skill id: min level
92:    Skill(1, 1, "Piloting"),
93:    Skill(2, 1, "Leadership"),
94:    Skill(3, 1, "Systems Engineering"),
95:    Skill(4, 1, "EVA"),
96:    Skill(5, 1, "Geology"),
97:    Skill(6, 1, "Flight Medicine"),
98:    Skill(7, 2, "Piloting"),
99:    Skill(8, 2, "Payload Integration"),
100:    Skill(9, 2, "Life Support"),
101:    Skill(10, 2, "Field Medicine"),
106:        # crew profile (= user) id: {skill id: level}
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && sed -n 60,92p src/mission_control/seed/data.py; grep -n "Slot(" src/mission_control/seed/data.py | head -20
```

<details>
<summary>↳ Result</summary>

```
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
42:class Slot(NamedTuple):
139:            Slot("Flight Engineer", 1, _ro({3: 3}), ()),
140:            Slot("Mission Specialist", 1, _ro({4: 3}), ()),
141:            Slot("Commander", 1, _ro({1: 4, 2: 3}), ()),
155:            Slot("Pilot", 1, _ro({1: 4}), ()),
156:            Slot("Geologist", 1, _ro({5: 4}), ()),
169:        (Slot("Engineer", 2, _ro({3: 3}), ((12, "accepted"),)),),
181:        (Slot("Flight Surgeon", 1, _ro({6: 4}), ((2, "accepted"),)),),
194:            Slot("Engineer", 1, _ro({3: 3}), ((8, "accepted"),)),
195:            Slot(
213:        (Slot("Engineer", 1, _ro({3: 3}), ((7, "accepted"),)),),
225:        (Slot("Engineer", 1, _ro({3: 3}), ((8, "completed"),)),),
238:            Slot("Payload Specialist", 1, _ro({8: 3}), ((17, "accepted"),)),
239:            Slot("Medic", 1, _ro({10: 3}), ((18, "accepted"),)),
```

</details>

### 🤖 Claude · 2026-10-12 03:24:29 UTC

I have enough context. Writing the test infrastructure first (fake API over `httpx2.MockTransport`), then the tests, then the implementation.

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/cli_fakes.py",
  "content": "\"\"\"Test doubles for the CLI: a scripted API behind `httpx2.MockTransport`, and a runner that\ninvokes `mc` in-process with its config directory under `tmp_path`.\n\nResponses are shaped like the design's HTTP contract: JSON bodies, and every error as\n`{\"error\": {\"code\", \"message\", \"problems\": [...]}}`.\n\"\"\"\n\nimport json\nfrom collections.abc import Callable, Mapping, Sequence\nfrom dataclasses import dataclass, field\nfrom pathlib import Path\nfrom typing import Any\n\nimport httpx2\nfrom typer.testing import CliRunner\n\nfrom mission_control.cli.config import CredentialStore, Credentials\nfrom mission_control.cli.env import Env\nfrom mission_control.cli.main import app\n\nBASE_URL = \"http://mc.test\"\nPREFIX = \"/api/v1\"\n\nHandler = Callable[[httpx2.Request], httpx2.Response]\n\n\ndef ok(body: Any = None, status: int = 200) -> httpx2.Response:\n    if body is None and status == 204:\n        return httpx2.Response(204)\n    return httpx2.Response(status, json=body)\n\n\ndef problem(code: str, message: str, **refs: Any) -> dict[str, Any]:\n    return {\"code\": code, \"message\": message, \"refs\": refs}\n\n\ndef error(\n    status: int, code: str, message: str, problems: Sequence[Mapping[str, Any]] | None = None\n) -> httpx2.Response:\n    listed = list(problems) if problems else [problem(code, message)]\n    return httpx2.Response(\n        status, json={\"error\": {\"code\": code, \"message\": message, \"problems\": listed}}\n    )\n\n\n@dataclass\nclass Call:\n    method: str\n    path: str\n    params: dict[str, str]\n    body: Any\n    token: str | None\n\n\n@dataclass\nclass FakeApi:\n    \"\"\"Routes `(method, path)` to a fixed response or a handler. Unrouted calls fail the test\n    loudly with a 599, so a missing route can't pass by accident.\"\"\"\n\n    routes: dict[tuple[str, str], Handler | httpx2.Response] = field(default_factory=dict)\n    calls: list[Call] = field(default_factory=list)\n\n    def on(self, method: str, path: str, response: Handler | httpx2.Response) -> None:\n        self.routes[(method.upper(), path)] = response\n\n    def handle(self, request: httpx2.Request) -> httpx2.Response:\n        path = request.url.path.removeprefix(PREFIX)\n        body = json.loads(request.content) if request.content else None\n        auth = request.headers.get(\"authorization\", \"\")\n        token = auth.removeprefix(\"Bearer \") if auth.startswith(\"Bearer \") else None\n        self.calls.append(Call(request.method, path, dict(request.url.params), body, token))\n        route = self.routes.get((request.method, path))\n        if route is None:\n            return httpx2.Response(599, json={\"unrouted\": f\"{request.method} {path}\"})\n        return route(request) if callable(route) else route\n\n    def client(self) -> httpx2.Client:\n        return httpx2.Client(transport=httpx2.MockTransport(self.handle), base_url=BASE_URL)\n\n    def sent(self, method: str, path: str) -> list[Call]:\n        return [c for c in self.calls if c.method == method and c.path == path]\n\n    def writes(self) -> list[Call]:\n        return [c for c in self.calls if c.method != \"GET\"]\n\n\n@dataclass\nclass Result:\n    exit_code: int\n    stdout: str\n    stderr: str\n    exception: BaseException | None\n\n\n@dataclass\nclass Mc:\n    \"\"\"Runs `mc` in-process against a FakeApi, with credentials kept under a temp directory.\"\"\"\n\n    api: FakeApi\n    config_dir: Path\n\n    @property\n    def store(self) -> CredentialStore:\n        return CredentialStore(self.config_dir)\n\n    def login_as(self, token: str = \"tok-lee\", email: str = \"lee@aurora.example\") -> None:\n        self.store.save(Credentials(token=token, email=email, expires_at=\"2027-01-05T21:00:00Z\"))\n\n    def __call__(\n        self,\n        *args: str,\n        input: str | None = None,\n        interactive: bool = False,\n        color: bool | None = False,\n        http: httpx2.Client | None = None,\n    ) -> Result:\n        env = Env(\n            http=http or self.api.client(),\n            config_dir=self.config_dir,\n            interactive=interactive,\n            color=color,\n        )\n        result = CliRunner().invoke(app, list(args), obj=env, input=input)\n        return Result(result.exit_code, result.stdout, result.stderr, result.exception)\n\n\n# Seed-shaped records (PRD §9). A crew profile's id equals its user's id.\n\nLEE_ME = {\n    \"id\": 4,\n    \"email\": \"lee@aurora.example\",\n    \"name\": \"Lee Park\",\n    \"role\": \"lead\",\n    \"is_active\": True,\n    \"crew_profile_id\": None,\n    \"organisation\": {\"id\": 1, \"name\": \"Aurora Space Agency\"},\n}\n\nSKILLS = [\n    {\"id\": 1, \"name\": \"Piloting\", \"category\": None},\n    {\"id\": 2, \"name\": \"Leadership\", \"category\": None},\n    {\"id\": 3, \"name\": \"Systems Engineering\", \"category\": None},\n    {\"id\": 4, \"name\": \"EVA\", \"category\": None},\n    {\"id\": 5, \"name\": \"Geology\", \"category\": None},\n]\n\n\ndef crew(cid: int, name: str, email: str, skills: Mapping[str, int] = (), **extra: Any) -> dict:\n    ids = {s[\"name\"]: s[\"id\"] for s in SKILLS}\n    record = {\n        \"crew_profile_id\": cid,\n        \"user_id\": cid,\n        \"name\": name,\n        \"email\": email,\n        \"active\": True,\n        \"bio\": None,\n        \"skills\": [\n            {\"skill_id\": ids[n], \"skill_name\": n, \"level\": lvl} for n, lvl in dict(skills).items()\n        ],\n        \"unavailability\": [],\n    }\n    record.update(extra)\n    return record\n\n\nCREW = [\n    crew(6, \"Ana Okafor\", \"ana@aurora.example\", {\"Piloting\": 5, \"Leadership\": 4}),\n    crew(7, \"Ben Ito\", \"ben@aurora.example\", {\"Systems Engineering\": 4, \"EVA\": 3}),\n    crew(8, \"Chen Wu\", \"chen@aurora.example\", {\"Systems Engineering\": 3}),\n    crew(9, \"Dana Reyes\", \"dana@aurora.example\", {\"EVA\": 4}),\n    crew(\n        11,\n        \"Fay Moreau\",\n        \"fay@aurora.example\",\n        {\"Piloting\": 4, \"Leadership\": 4},\n        unavailability=[\n            {\"id\": 1, \"start_date\": \"2027-03-05\", \"end_date\": \"2027-03-08\", \"reason\": None}\n        ],\n    ),\n    crew(12, \"Gus Patel\", \"gus@aurora.example\", {\"Systems Engineering\": 5}),\n]\n\nUSERS = [\n    {\"id\": 1, \"email\": \"ruth@aurora.example\", \"name\": \"Ruth Adeyemi\", \"role\": \"director\"},\n    {\"id\": 4, \"email\": \"lee@aurora.example\", \"name\": \"Lee Park\", \"role\": \"lead\"},\n    {\"id\": 5, \"email\": \"nora@aurora.example\", \"name\": \"Nora Quinn\", \"role\": \"lead\"},\n    {\"id\": 8, \"email\": \"chen@aurora.example\", \"name\": \"Chen Wu\", \"role\": \"crew\"},\n]\nfor _u in USERS:\n    _u[\"is_active\"] = True\n\n\ndef requirement(name: str, level: int) -> dict:\n    ids = {s[\"name\"]: s[\"id\"] for s in SKILLS}\n    return {\"skill_id\": ids[name], \"skill_name\": name, \"min_level\": level}\n\n\ndef gateway(\n    status: str = \"draft\",\n    assignments: Sequence[Mapping[str, Any]] = (),\n    approvals: Sequence[Mapping[str, Any]] = (),\n    open_places: Mapping[int, int] | None = None,\n) -> dict:\n    places = {1: 1, 2: 1, 3: 1} | dict(open_places or {})\n    return {\n        \"id\": 1,\n        \"name\": \"Lunar Gateway Resupply\",\n        \"start_date\": \"2027-03-01\",\n        \"end_date\": \"2027-03-10\",\n        \"status\": status,\n        \"owner_id\": 4,\n        \"owner_name\": \"Lee Park\",\n        \"created_by_id\": 1,\n        \"created_by_name\": \"Ruth Adeyemi\",\n        \"approval_round\": 0,\n        \"approvals_required\": None if status == \"draft\" else 2,\n        \"slots\": [\n            {\n                \"id\": 1,\n                \"position\": 1,\n                \"name\": \"Flight Engineer\",\n                \"headcount\": 1,\n                \"open_places\": places[1],\n                \"requirements\": [requirement(\"Systems Engineering\", 3)],\n            },\n            {\n                \"id\": 2,\n                \"position\": 2,\n                \"name\": \"Mission Specialist\",\n                \"headcount\": 1,\n                \"open_places\": places[2],\n                \"requirements\": [requirement(\"EVA\", 3)],\n            },\n            {\n                \"id\": 3,\n                \"position\": 3,\n                \"name\": \"Commander\",\n                \"headcount\": 1,\n                \"open_places\": places[3],\n                \"requirements\": [requirement(\"Piloting\", 4), requirement(\"Leadership\", 3)],\n            },\n        ],\n        \"assignments\": list(assignments),\n        \"approvals\": list(approvals),\n    }\n\n\nS2_PREVIEW = {\n    \"mission\": {\n        \"id\": 1,\n        \"name\": \"Lunar Gateway Resupply\",\n        \"start_date\": \"2027-03-01\",\n        \"end_date\": \"2027-03-10\",\n    },\n    \"can_apply\": True,\n    \"open_places\": 3,\n    \"unfilled_places\": 0,\n    \"slots\": [\n        {\n            \"slot_id\": 1,\n            \"name\": \"Flight Engineer\",\n            \"open_places\": 1,\n            \"unfilled\": 0,\n            \"suggested\": [\n                {\"crew_profile_id\": 8, \"name\": \"Chen\", \"workload\": 5, \"proficiency\": 3, \"pick\": 2}\n            ],\n        },\n        {\n            \"slot_id\": 2,\n            \"name\": \"Mission Specialist\",\n            \"open_places\": 1,\n            \"unfilled\": 0,\n            \"suggested\": [\n                {\"crew_profile_id\": 9, \"name\": \"Dana\", \"workload\": 5, \"proficiency\": 4, \"pick\": 3}\n            ],\n        },\n        {\n            \"slot_id\": 3,\n            \"name\": \"Commander\",\n            \"open_places\": 1,\n            \"unfilled\": 0,\n            \"suggested\": [\n                {\"crew_profile_id\": 6, \"name\": \"Ana\", \"workload\": 0, \"proficiency\": 9, \"pick\": 1}\n            ],\n        },\n    ],\n}\n\nS3_PREVIEW = {\n    \"mission\": {\n        \"id\": 2,\n        \"name\": \"Asteroid Survey\",\n        \"start_date\": \"2027-03-05\",\n        \"end_date\": \"2027-03-12\",\n    },\n    \"can_apply\": True,\n    \"open_places\": 2,\n    \"unfilled_places\": 1,\n    \"slots\": [\n        {\n            \"slot_id\": 4,\n            \"name\": \"Pilot\",\n            \"open_places\": 1,\n            \"unfilled\": 0,\n            \"suggested\": [\n                {\"crew_profile_id\": 6, \"name\": \"Ana\", \"workload\": 0, \"proficiency\": 5, \"pick\": 1}\n            ],\n        },\n        {\"slot_id\": 5, \"name\": \"Geologist\", \"open_places\": 1, \"unfilled\": 1, \"suggested\": []},\n    ],\n}\n"
}
```

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/conftest.py",
  "content": "import pytest\n\nfrom cli_fakes import FakeApi, Mc\n\n\n@pytest.fixture(autouse=True)\ndef _no_ambient_terminal_settings(monkeypatch):\n    \"\"\"The developer's own NO_COLOR, TERM or API URL must not change what the tests see.\"\"\"\n    for name in (\"NO_COLOR\", \"TERM\", \"MC_API_URL\"):\n        monkeypatch.delenv(name, raising=False)\n\n\n@pytest.fixture\ndef api() -> FakeApi:\n    return FakeApi()\n\n\n@pytest.fixture\ndef mc(api, tmp_path) -> Mc:\n    return Mc(api=api, config_dir=tmp_path / \"config\")\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/cli_fakes.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/conftest.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>📎 File attached: .worktrees/m16-cli/CLAUDE.md</summary>

```
{
  "path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/CLAUDE.md",
  "type": "Project",
  "content": "# Mission Control\n\nMulti-tenant mission planning API and CLI. Read these before doing any work. They are the source of truth, so don't copy their content here.\n\n- [`docs/brief.md`](docs/brief.md): the assessment brief\n- [`docs/prd.md`](docs/prd.md): **behaviour**. What the system does, its rules, acceptance criteria and seed scenarios.\n- [`docs/technical-design.md`](docs/technical-design.md): **structure**. Architecture, schema, API, CLI, the delivery plan (§9) and the implementation guidelines (§10).\n\nIf the PRD and the design conflict, or are silent on something, stop and ask. Never invent behaviour.\n\n## Workflow (every module)\n\n1. **One approved module at a time.** Work only on the module from design §9 that I have approved. Don't start anything else.\n2. **Tests first.** Write failing tests that reference the PRD IDs, then implement. Run the full suite and lint: `uv run pytest` and `uv run ruff check`.\n3. **Real verification.** Exercise the behaviour for real, for example with a REPL call, an HTTP request or a CLI command. Show the actual output. A passing test run alone isn't verification.\n4. **Read-only review.** Review the full diff against the PRD and design §10 without editing. Report findings, and fix them only once I agree.\n5. **Stop for approval.** Summarise what changed, the test and verification results, and the review findings, and propose a commit message. **Don't commit, and don't start the next module, until I approve.**\n\n## Waves (parallel modules in worktrees)\n\nWhen I approve a wave of independent modules (design §9), build them in parallel and keep reviews small:\n\n1. **One worktree per module.** Run `git worktree add .worktrees/<module> -b <module> main`, then `uv sync` inside it. Each agent edits only its own worktree and doesn't commit.\n2. **Same workflow per module.** Steps 2 to 4 above still apply, inside the worktree.\n3. **Review one branch at a time.** Show me only that module's diff against `main` (`git -C .worktrees/<module> diff main`, including new files), with its results.\n4. **After I approve that module:**\n   - commit on its branch;\n   - rebase onto `main` if `main` has moved, and re-run its tests;\n   - fast-forward `main`;\n   - run the full suite on `main`;\n   - remove the worktree and branch.\n\n   Only then present the next branch.\n\nNever push, add dependencies, change the schema, or add endpoints, error codes or CLI commands outside the design without asking first.\n",
  "contentDiffersFromDisk": false
}
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_parsing.py",
  "content": "\"\"\"M16: parsing what the user types. The `--slot` spec, requirement lists and dates (design §8).\n\nOnly syntax is checked here. Rules such as a headcount of at least 1 or a level from 1 to 5 belong\nto the server, so values that parse are passed through for it to judge.\n\"\"\"\n\nimport pytest\n\nfrom mission_control.cli.resolve import SpecError, parse_requirements, parse_slot_spec\n\n\ndef test_m16_slot_spec_parses_name_headcount_and_requirements():\n    spec = parse_slot_spec(\"Commander:1:Piloting>=4,Leadership>=3\")\n\n    assert spec.name == \"Commander\"\n    assert spec.headcount == 1\n    assert spec.requirements == ((\"Piloting\", 4), (\"Leadership\", 3))\n\n\ndef test_m16_slot_spec_trims_spaces_and_keeps_multi_word_names():\n    spec = parse_slot_spec(\" Flight Engineer : 2 : Systems Engineering >= 3 , EVA>=2 \")\n\n    assert spec.name == \"Flight Engineer\"\n    assert spec.headcount == 2\n    assert spec.requirements == ((\"Systems Engineering\", 3), (\"EVA\", 2))\n\n\ndef test_m16_slot_spec_allows_a_colon_in_the_slot_name():\n    spec = parse_slot_spec(\"Ops: Night:1:EVA>=3\")\n\n    assert spec.name == \"Ops: Night\"\n    assert spec.requirements == ((\"EVA\", 3),)\n\n\ndef test_m2_slot_spec_passes_rule_breaking_numbers_through_to_the_server():\n    \"\"\"Headcount 0 and level 9 parse; the server refuses them with every mistake listed.\"\"\"\n    spec = parse_slot_spec(\"Commander:0:Piloting>=9\")\n\n    assert spec.headcount == 0\n    assert spec.requirements == ((\"Piloting\", 9),)\n\n\ndef test_m2_slot_spec_with_no_requirements_is_left_for_the_server_to_refuse():\n    assert parse_slot_spec(\"Commander:1:\").requirements == ()\n\n\n@pytest.mark.parametrize(\n    \"text\",\n    [\"Commander\", \"Commander:1\", \"Commander:one:Piloting>=4\", \":1:Piloting>=4\"],\n)\ndef test_m16_slot_spec_rejects_malformed_text_with_the_expected_format(text):\n    with pytest.raises(SpecError) as raised:\n        parse_slot_spec(text)\n\n    assert \"NAME:HEADCOUNT:SKILL>=LEVEL\" in str(raised.value)\n    assert \"Commander:1:Piloting>=4,Leadership>=3\" in str(raised.value)\n\n\n@pytest.mark.parametrize(\"text\", [\"Piloting\", \"Piloting>=\", \">=4\", \"Piloting=4\", \"Piloting>=x\"])\ndef test_m16_requirements_reject_an_entry_without_skill_and_level(text):\n    with pytest.raises(SpecError) as raised:\n        parse_requirements(text)\n\n    assert \"SKILL>=LEVEL\" in str(raised.value)\n"
}
```

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_render.py",
  "content": "\"\"\"M16: output building blocks. Friendlier dates, aligned tables, markers that never rely on\ncolour, and colour only on a terminal (design §8, docs/cli-ux.md).\"\"\"\n\nimport io\nfrom datetime import date\n\nimport pytest\n\nfrom mission_control.cli.render import (\n    Span,\n    Style,\n    Terminal,\n    detect_style,\n    format_range,\n    format_timestamp,\n    table_lines,\n)\n\n\nclass FakeTty(io.StringIO):\n    def __init__(self, tty: bool = True, encoding: str = \"utf-8\"):\n        super().__init__()\n        self._tty = tty\n        self._encoding = encoding\n\n    def isatty(self) -> bool:\n        return self._tty\n\n    @property\n    def encoding(self) -> str:  # type: ignore[override]\n        return self._encoding\n\n\n@pytest.mark.parametrize(\n    (\"start\", \"end\", \"fancy\", \"plain\"),\n    [\n        (date(2027, 3, 1), date(2027, 3, 10), \"1–10 Mar 2027\", \"1-10 Mar 2027\"),\n        (date(2027, 3, 5), date(2027, 3, 5), \"5 Mar 2027\", \"5 Mar 2027\"),\n        (date(2027, 2, 25), date(2027, 3, 2), \"25 Feb – 2 Mar 2027\", \"25 Feb - 2 Mar 2027\"),\n        (date(2026, 12, 30), date(2027, 1, 2), \"30 Dec 2026 – 2 Jan 2027\", \"30 Dec 2026 - 2 Jan 2027\"),\n    ],\n)\ndef test_m16_dates_read_naturally(start, end, fancy, plain):\n    assert format_range(start, end) == fancy\n    assert format_range(start, end, plain=True) == plain\n\n\ndef test_m16_timestamps_are_shown_in_utc_without_seconds():\n    assert format_timestamp(\"2027-01-05T09:03:27.123Z\") == \"5 Jan 2027 09:03\"\n\n\ndef test_m16_tables_align_columns_with_no_trailing_spaces():\n    lines = table_lines(\n        [\"Slot\", \"Suggested\", \"Workload\"],\n        [[\"Flight Engineer\", \"Chen\", \"5 days\"], [\"Mission Specialist\", \"Dana\", \"5 days\"]],\n    )\n\n    assert lines == [\n        \"  Slot                 Suggested   Workload\",\n        \"  Flight Engineer      Chen        5 days\",\n        \"  Mission Specialist   Dana        5 days\",\n    ]\n\n\ndef test_m16_a_spanning_row_does_not_widen_the_other_columns():\n    lines = table_lines(\n        [\"Slot\", \"Suggested\", \"Pick\"],\n        [[\"Pilot\", \"Ana\", \"1\"], Span(\"Geologist\", \"unfilled (1 place)\")],\n    )\n\n    assert lines == [\n        \"  Slot        Suggested   Pick\",\n        \"  Pilot       Ana         1\",\n        \"  Geologist   unfilled (1 place)\",\n    ]\n\n\ndef test_m16_colour_only_on_a_terminal():\n    assert detect_style(FakeTty(tty=True), {\"TERM\": \"xterm-256color\"}) == Style(True, True)\n    assert detect_style(FakeTty(tty=False), {\"TERM\": \"xterm-256color\"}) == Style(False, True)\n\n\n@pytest.mark.parametrize(\"environ\", [{\"NO_COLOR\": \"1\", \"TERM\": \"xterm\"}, {\"TERM\": \"dumb\"}])\ndef test_m16_no_color_and_dumb_terminals_get_plain_words(environ):\n    assert detect_style(FakeTty(tty=True), environ) == Style(color=False, unicode=False)\n\n\ndef test_m16_a_non_utf8_terminal_gets_plain_words_but_keeps_colour():\n    assert detect_style(FakeTty(encoding=\"ascii\"), {\"TERM\": \"xterm\"}) == Style(True, False)\n\n\ndef test_m16_markers_carry_meaning_without_colour():\n    out, err = FakeTty(), FakeTty()\n    term = Terminal(out, err, Style(False, True), Style(False, True))\n    term.ok(\"Logged out.\")\n    term.note(\"Heads up.\")\n    term.error(\"Mission 5 not found.\", hint=\"See your missions: mc missions list\")\n\n    assert out.getvalue() == \"✓ Logged out.\\n! Heads up.\\n\"\n    assert err.getvalue() == \"✗ Mission 5 not found.\\n  See your missions: mc missions list\\n\"\n\n\ndef test_m16_plain_markers_use_words():\n    out, err = FakeTty(), FakeTty()\n    term = Terminal(out, err, Style(False, False), Style(False, False))\n    term.ok(\"Done.\")\n    term.note(\"Careful.\")\n    term.error(\"Broken.\", [\"first\", \"second\"])\n\n    assert out.getvalue() == \"OK: Done.\\nNote: Careful.\\n\"\n    assert err.getvalue() == \"Error: Broken.\\n  - first\\n  - second\\n\"\n\n\ndef test_m16_colour_wraps_only_the_marker_and_always_resets():\n    out, err = FakeTty(), FakeTty()\n    term = Terminal(out, err, Style(True, True), Style(True, True))\n    term.ok(\"Done.\")\n    term.error(\"Broken.\")\n\n    assert out.getvalue() == \"\\x1b[32m✓\\x1b[0m Done.\\n\"\n    assert err.getvalue() == \"\\x1b[31m✗\\x1b[0m Broken.\\n\"\n\n\ndef test_m16_next_steps_go_to_stderr_one_per_line():\n    out, err = FakeTty(), FakeTty()\n    term = Terminal(out, err, Style(False, True), Style(False, True))\n    term.next_steps([\"mc missions match 1 --apply\", \"mc missions show 1\"])\n\n    assert out.getvalue() == \"\"\n    assert err.getvalue() == \"Next: mc missions match 1 --apply\\n      mc missions show 1\\n\"\n"
}
```

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_config.py",
  "content": "\"\"\"M16: the credentials file. Kept at mode 0600, replaced atomically, and treated as logged out\nwhen missing or unreadable (design §8).\"\"\"\n\nimport stat\n\nfrom mission_control.cli.config import (\n    DEFAULT_API_URL,\n    CredentialStore,\n    Credentials,\n    api_url,\n    default_config_dir,\n)\n\n\ndef test_m16_credentials_live_under_the_users_config_directory(monkeypatch, tmp_path):\n    monkeypatch.setenv(\"HOME\", str(tmp_path))\n\n    assert default_config_dir() == tmp_path / \".config\" / \"mission-control\"\n    assert CredentialStore(default_config_dir()).path == (\n        tmp_path / \".config\" / \"mission-control\" / \"credentials.json\"\n    )\n\n\ndef test_m16_credentials_file_is_readable_only_by_the_user(tmp_path):\n    store = CredentialStore(tmp_path / \"cfg\")\n\n    store.save(Credentials(token=\"secret\", email=\"lee@aurora.example\", expires_at=None))\n\n    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600\n    assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700\n    assert store.load() == Credentials(\"secret\", \"lee@aurora.example\", None)\n\n\ndef test_m16_saving_tightens_a_file_that_was_left_readable(tmp_path):\n    store = CredentialStore(tmp_path)\n    store.path.write_text(\"{}\")\n    store.path.chmod(0o644)\n\n    store.save(Credentials(token=\"secret\", email=\"lee@aurora.example\"))\n\n    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600\n    assert not list(tmp_path.glob(\"*.tmp\"))\n\n\ndef test_m16_missing_or_corrupt_credentials_mean_logged_out(tmp_path):\n    store = CredentialStore(tmp_path)\n    assert store.load() is None\n\n    store.path.write_text(\"not json\")\n    assert store.load() is None\n\n    store.path.write_text('{\"email\": \"lee@aurora.example\"}')\n    assert store.load() is None\n\n\ndef test_m16_clearing_is_safe_when_already_logged_out(tmp_path):\n    store = CredentialStore(tmp_path)\n    store.clear()\n    store.save(Credentials(token=\"secret\", email=\"lee@aurora.example\"))\n\n    store.clear()\n\n    assert not store.path.exists()\n\n\ndef test_m16_api_url_defaults_to_the_local_server(monkeypatch):\n    monkeypatch.delenv(\"MC_API_URL\", raising=False)\n    assert api_url() == DEFAULT_API_URL == \"http://127.0.0.1:8000\"\n\n    monkeypatch.setenv(\"MC_API_URL\", \"http://127.0.0.1:8016/\")\n    assert api_url() == \"http://127.0.0.1:8016\"\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_parsing.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_render.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_config.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_auth.py",
  "content": "\"\"\"M16: signing in and out, who am I, and changing a password (PRD §4.1, P10; design §8).\n\nPasswords are only ever asked for with a hidden prompt, never taken as a flag. When stdin isn't a\nterminal they're read from it, one line per prompt, so scripts can pipe them in.\n\"\"\"\n\nimport stat\nfrom datetime import UTC, datetime, timedelta\n\nfrom cli_fakes import LEE_ME, error, ok\n\n\ndef _login_ok(request):\n    expires = datetime.now(UTC) + timedelta(hours=12)\n    return ok({\"token\": \"tok-new\", \"expires_at\": expires.isoformat().replace(\"+00:00\", \"Z\")})\n\n\ndef test_m16_login_prompts_for_email_and_hidden_password_then_stores_the_token(mc, api):\n    api.on(\"POST\", \"/auth/login\", _login_ok)\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"login\", input=\"lee@aurora.example\\norbital launch window\\n\", interactive=True)\n\n    assert result.exit_code == 0, result.stderr\n    assert \"Email: \" in result.stderr\n    assert \"Password: \" in result.stderr\n    assert \"orbital launch window\" not in result.stdout + result.stderr  # never echoed\n    assert api.sent(\"POST\", \"/auth/login\")[0].body == {\n        \"email\": \"lee@aurora.example\",\n        \"password\": \"orbital launch window\",\n    }\n    assert result.stdout == (\n        \"✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts 12 hours.\\n\"\n    )\n    assert \"Next: mc inbox\" in result.stderr\n    saved = mc.store.load()\n    assert saved.token == \"tok-new\" and saved.email == \"lee@aurora.example\"\n    assert stat.S_IMODE(mc.store.path.stat().st_mode) == 0o600\n    assert api.sent(\"GET\", \"/me\")[0].token == \"tok-new\"\n\n\ndef test_m16_login_with_email_flag_asks_only_for_the_password(mc, api):\n    api.on(\"POST\", \"/auth/login\", _login_ok)\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"login\", \"--email\", \"lee@aurora.example\", input=\"pw\\n\", interactive=True)\n\n    assert result.exit_code == 0\n    assert \"Email: \" not in result.stderr\n\n\ndef test_m16_login_reads_the_password_from_a_pipe_when_not_on_a_terminal(mc, api):\n    api.on(\"POST\", \"/auth/login\", _login_ok)\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"login\", \"--email\", \"lee@aurora.example\", input=\"orbital launch window\\n\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/auth/login\")[0].body[\"password\"] == \"orbital launch window\"\n    assert \"Password\" not in result.stderr\n\n\ndef test_m16_login_without_a_terminal_or_email_fails_clearly_instead_of_hanging(mc, api):\n    result = mc(\"login\", input=\"\")\n\n    assert result.exit_code == 2\n    assert \"Pass --email\" in result.stderr\n    assert api.calls == []\n\n\ndef test_m16_login_without_a_terminal_or_piped_password_fails_clearly(mc, api):\n    result = mc(\"login\", \"--email\", \"lee@aurora.example\", input=\"\")\n\n    assert result.exit_code == 2\n    assert \"pipe it on stdin\" in result.stderr\n    assert api.calls == []\n\n\ndef test_m16_password_is_never_a_flag(mc):\n    result = mc(\"login\", \"--email\", \"lee@aurora.example\", \"--password\", \"x\")\n\n    assert result.exit_code == 2\n    assert \"No such option\" in result.stderr\n\n\ndef test_p7_wrong_or_deactivated_login_exits_3_and_saves_nothing(mc, api):\n    api.on(\n        \"POST\",\n        \"/auth/login\",\n        error(401, \"invalid_credentials\", \"Email or password is incorrect\"),\n    )\n\n    result = mc(\"login\", \"--email\", \"lee@aurora.example\", input=\"nope\\n\")\n\n    assert result.exit_code == 3\n    assert result.stderr.startswith(\"✗ Email or password is incorrect.\\n\")\n    assert \"•\" not in result.stderr  # the single reason isn't repeated as a bullet\n    assert mc.store.load() is None\n\n\ndef test_m16_logout_revokes_the_token_and_clears_the_file(mc, api):\n    mc.login_as(\"tok-lee\")\n    api.on(\"POST\", \"/auth/logout\", ok(status=204))\n\n    result = mc(\"logout\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"✓ Logged out.\\n\"\n    assert api.sent(\"POST\", \"/auth/logout\")[0].token == \"tok-lee\"\n    assert not mc.store.path.exists()\n\n\ndef test_m16_logout_when_the_session_already_ended_still_clears_the_file(mc, api):\n    mc.login_as(\"tok-old\")\n    api.on(\"POST\", \"/auth/logout\", error(401, \"unauthenticated\", \"Your session has ended\"))\n\n    result = mc(\"logout\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"✓ Logged out.\\n\"\n    assert not mc.store.path.exists()\n\n\ndef test_m16_logout_when_not_logged_in_says_so_without_calling_the_server(mc, api):\n    result = mc(\"logout\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"✓ You're not logged in.\\n\"\n    assert api.calls == []\n\n\ndef test_m16_whoami_shows_the_current_user(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"whoami\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Name           Lee Park\\n\"\n        \"Email          lee@aurora.example\\n\"\n        \"Role           Mission Lead\\n\"\n        \"Organisation   Aurora Space Agency\\n\"\n        \"Crew profile   none\\n\"\n    )\n\n\ndef test_m16_whoami_json_prints_the_api_body(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"whoami\", \"--json\")\n\n    assert result.exit_code == 0\n    assert '\"email\": \"lee@aurora.example\"' in result.stdout\n\n\ndef test_m16_commands_need_a_login_and_exit_3_without_one(mc, api):\n    result = mc(\"whoami\")\n\n    assert result.exit_code == 3\n    assert result.stderr == \"✗ You're not logged in.\\n  Log in: mc login\\n\"\n    assert api.calls == []\n\n\ndef test_m16_a_401_clears_the_stored_session_and_exits_3(mc, api):\n    mc.login_as(\"tok-expired\")\n    api.on(\"GET\", \"/me\", error(401, \"unauthenticated\", \"Your session has expired\"))\n\n    result = mc(\"whoami\")\n\n    assert result.exit_code == 3\n    assert result.stderr == \"✗ Your session has expired.\\n  Log in again: mc login\\n\"\n    assert not mc.store.path.exists()\n\n\ndef test_p10_password_change_asks_current_then_new_twice_and_ends_the_session(mc, api):\n    mc.login_as(\"tok-lee\")\n    api.on(\"POST\", \"/me/password\", ok(status=204))\n\n    result = mc(\n        \"password\",\n        input=\"old password here\\nnew passphrase is long\\nnew passphrase is long\\n\",\n        interactive=True,\n    )\n\n    assert result.exit_code == 0, result.stderr\n    prompts = [line for line in result.stderr.splitlines() if line.endswith(\": \")]\n    assert result.stderr.index(\"Current password: \") < result.stderr.index(\"New password: \")\n    assert result.stderr.index(\"New password: \") < result.stderr.index(\"Repeat new password: \")\n    assert prompts == [] or all(\"password\" in p.lower() for p in prompts)\n    assert api.sent(\"POST\", \"/me/password\")[0].body == {\n        \"current_password\": \"old password here\",\n        \"new_password\": \"new passphrase is long\",\n    }\n    assert result.stdout == (\n        \"✓ Password changed. All your sessions have ended, including this one.\\n\"\n    )\n    assert \"Next: mc login\" in result.stderr\n    assert not mc.store.path.exists()\n\n\ndef test_p10_mismatched_new_passwords_change_nothing(mc, api):\n    mc.login_as()\n\n    result = mc(\"password\", input=\"old\\nnew one long enough\\ntypo one long enough\\n\", interactive=True)\n\n    assert result.exit_code == 2\n    assert \"The new passwords don't match. Nothing was changed.\" in result.stderr\n    assert api.calls == []\n    assert mc.store.path.exists()\n\n\ndef test_p10_short_password_is_refused_by_the_server_not_the_cli(mc, api):\n    mc.login_as()\n    api.on(\n        \"POST\",\n        \"/me/password\",\n        error(422, \"password_too_short\", \"Passwords must be at least 15 characters\"),\n    )\n\n    result = mc(\"password\", input=\"old\\nshort\\nshort\\n\", interactive=True)\n\n    assert result.exit_code == 1\n    assert \"✗ Passwords must be at least 15 characters.\" in result.stderr\n    assert mc.store.path.exists()  # nothing changed, so the session is still good\n\n\ndef test_p10_wrong_current_password_keeps_the_session(mc, api):\n    mc.login_as()\n    api.on(\n        \"POST\",\n        \"/me/password\",\n        error(403, \"wrong_current_password\", \"Your current password is incorrect\"),\n    )\n\n    result = mc(\"password\", input=\"bad\\nnew passphrase is long\\nnew passphrase is long\\n\")\n\n    assert result.exit_code == 1\n    assert result.stderr.startswith(\"✗ Your current password is incorrect.\\n\")\n    assert mc.store.path.exists()\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_auth.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='tests/cli/test_cli_auth.py'
s=open(p).read()
s=s.replace('''    prompts = [line for line in result.stderr.splitlines() if line.endswith(": ")]
''','').replace('''    assert prompts == [] or all("password" in p.lower() for p in prompts)
''','')
open(p,'w').write(s)
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_errors.py",
  "content": "\"\"\"M16: how refusals and failures reach the user. The message, one bullet per problem, a hint\nfor known codes, and the documented exit codes: 0 OK, 1 refused, 2 usage, 3 authentication,\n4 unreachable or busy, 130 interrupted (design §7, §8; PRD C2).\"\"\"\n\nimport json\n\nimport httpx2\n\nfrom cli_fakes import S2_PREVIEW, error, gateway, ok, problem\n\n\ndef test_c2_every_problem_is_listed_once_under_the_message(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\n        \"POST\",\n        \"/missions/1/submit\",\n        error(\n            409,\n            \"rule_violation\",\n            \"Mission can't be submitted\",\n            [\n                problem(\"slot_unfilled\", \"Flight Engineer: 1 place unfilled\", slot_id=1),\n                problem(\"slot_unfilled\", \"Commander: 1 place unfilled\", slot_id=3),\n                problem(\"insufficient_approvers\", \"1 eligible approver, 2 required\"),\n            ],\n        ),\n    )\n\n    result = mc(\"missions\", \"submit\", \"1\")\n\n    assert result.exit_code == 1\n    assert result.stdout == \"\"\n    assert result.stderr == (\n        \"✗ Mission can't be submitted.\\n\"\n        \"  • Flight Engineer: 1 place unfilled\\n\"\n        \"  • Commander: 1 place unfilled\\n\"\n        \"  • 1 eligible approver, 2 required\\n\"\n        \"  Fill the open places: mc missions match 1\\n\"\n    )\n\n\ndef test_m16_a_single_reason_refusal_prints_its_message_once(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/9\", error(404, \"not_found\", \"Mission not found\"))\n\n    result = mc(\"missions\", \"show\", \"9\")\n\n    assert result.exit_code == 1\n    assert result.stderr == \"✗ Mission 9 not found.\\n  See your missions: mc missions list\\n\"\n\n\ndef test_m16_refusal_with_json_prints_the_error_body_on_stdout(mc, api):\n    mc.login_as()\n    body = error(409, \"mission_frozen\", \"Can't suggest crew for an active mission\")\n    api.on(\"GET\", \"/missions/5/match\", body)\n\n    result = mc(\"missions\", \"match\", \"5\", \"--json\")\n\n    assert result.exit_code == 1\n    assert json.loads(result.stdout) == {\n        \"error\": {\n            \"code\": \"mission_frozen\",\n            \"message\": \"Can't suggest crew for an active mission\",\n            \"problems\": [\n                {\n                    \"code\": \"mission_frozen\",\n                    \"message\": \"Can't suggest crew for an active mission\",\n                    \"refs\": {},\n                }\n            ],\n        }\n    }\n    assert result.stderr == \"\"\n\n\ndef test_m16_usage_errors_exit_2_before_any_request(mc, api):\n    mc.login_as()\n\n    result = mc(\"missions\", \"match\", \"abc\")\n\n    assert result.exit_code == 2\n    assert \"'abc' is not a valid integer\" in result.stderr\n    assert api.calls == []\n\n\ndef test_m16_unknown_command_suggests_the_closest(mc):\n    result = mc(\"missions\", \"mach\", \"1\")\n\n    assert result.exit_code == 2\n    assert \"Did you mean 'match'?\" in result.stderr\n\n\ndef test_m16_unreachable_server_exits_4_and_says_how_to_start_it(mc):\n    mc.login_as()\n\n    def refuse(request):\n        raise httpx2.ConnectError(\"connection refused\", request=request)\n\n    result = mc(\"whoami\", http=httpx2.Client(transport=httpx2.MockTransport(refuse)))\n\n    assert result.exit_code == 4\n    assert \"✗ Can't reach the Mission Control server at \" in result.stderr\n    assert \"Is it running? Start it with: uv run mc-server\" in result.stderr\n    assert mc.store.path.exists()\n\n\ndef test_m16_busy_database_exits_4_with_a_retry_hint(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me\", error(503, \"busy\", \"The database is busy\"))\n\n    result = mc(\"whoami\")\n\n    assert result.exit_code == 4\n    assert result.stderr == \"✗ The database is busy.\\n  Try again in a moment.\\n\"\n\n\ndef test_m16_an_unexpected_server_response_is_reported_without_a_traceback(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me\", httpx2.Response(500, text=\"Internal Server Error\"))\n\n    result = mc(\"whoami\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ The server sent an unexpected response (HTTP 500).\\n\"\n        \"  Try again. If it keeps happening, check the server's log.\\n\"\n    )\n    assert \"Traceback\" not in result.stderr\n\n\ndef test_m16_ctrl_c_exits_130_quietly(mc):\n    mc.login_as()\n\n    def interrupt(request):\n        raise KeyboardInterrupt\n\n    result = mc(\"whoami\", http=httpx2.Client(transport=httpx2.MockTransport(interrupt)))\n\n    assert result.exit_code == 130\n    assert result.stderr.strip() == \"Cancelled.\"\n\n\ndef test_m16_ctrl_c_at_a_prompt_exits_130(mc):\n    result = mc(\"login\", input=\"\", interactive=True)  # end of input at the prompt\n\n    assert result.exit_code == 130\n    assert \"Cancelled.\" in result.stderr\n\n\ndef test_m16_bare_mc_shows_help_and_exits_0(mc):\n    result = mc()\n\n    assert result.exit_code == 0\n    assert \"Usage: mc\" in result.stdout\n    for group in (\"missions\", \"assignments\", \"crew\", \"users\", \"skills\", \"org\", \"me\"):\n        assert group in result.stdout\n\n\ndef test_m16_bare_group_shows_its_help_and_exits_0(mc):\n    result = mc(\"missions\")\n\n    assert result.exit_code == 0\n    assert \"match\" in result.stdout and \"submit\" in result.stdout\n\n\ndef test_m16_version_flag(mc):\n    result = mc(\"--version\")\n\n    assert result.exit_code == 0\n    assert result.stdout.startswith(\"mc \")\n\n\ndef test_m16_command_help_shows_usage_and_an_example(mc):\n    result = mc(\"missions\", \"match\", \"--help\")\n\n    assert result.exit_code == 0\n    assert result.stdout.startswith(\"Usage: mc missions match MISSION_ID [--apply] [--json]\\n\")\n    assert \"Suggest crew for a draft mission's open places. Nothing is changed.\" in result.stdout\n    assert \"Example:\\n  mc missions match 1\\n\" in result.stdout\n\n\ndef test_m16_colour_escapes_appear_only_when_enabled(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1/match\", ok(S2_PREVIEW))\n\n    plain = mc(\"missions\", \"match\", \"1\")\n    coloured = mc(\"missions\", \"match\", \"1\", color=True)\n\n    assert \"\\x1b[\" not in plain.stdout + plain.stderr\n    assert \"\\x1b[32m✓\\x1b[0m\" in coloured.stdout\n\n\ndef test_m16_no_color_env_gives_plain_words(mc, api, monkeypatch):\n    mc.login_as()\n    monkeypatch.setenv(\"NO_COLOR\", \"1\")\n    api.on(\"GET\", \"/missions/5/match\", error(409, \"mission_frozen\", \"Can't suggest crew for an active mission\"))\n\n    result = mc(\"missions\", \"match\", \"5\", color=None)\n\n    assert result.stderr.startswith(\"Error: Mission 5: Can't suggest crew for an active mission.\\n\")\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_errors.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_match.py",
  "content": "\"\"\"M16: `mc missions match` renders the matcher preview exactly as the approved mock sessions in\ndocs/cli-ux.md (PRD §6, AC-18, AC-19, AC-22; S2, S3).\"\"\"\n\nimport json\n\nfrom cli_fakes import S2_PREVIEW, S3_PREVIEW, error, gateway, ok\n\nS2_TABLE = (\n    \"Lunar Gateway Resupply · 1–10 Mar 2027 · Draft\\n\"\n    \"✓ Crew suggested for all 3 open places. Nothing has been proposed yet.\\n\"\n    \"\\n\"\n    \"  Slot                 Suggested   Workload   Proficiency   Pick\\n\"\n    \"  Flight Engineer      Chen        5 days     3             2\\n\"\n    \"  Mission Specialist   Dana        5 days     4             3\\n\"\n    \"  Commander            Ana         0 days     9             1\\n\"\n    \"\\n\"\n    \"  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload\\n\"\n    \"  wins, then highest proficiency (sum of the required skill levels).\\n\"\n)\n\n\ndef test_s2_full_suggestion_for_the_owner(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1/match\", ok(S2_PREVIEW))\n\n    result = mc(\"missions\", \"match\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == S2_TABLE\n    assert result.stderr == (\n        \"Next: mc missions match 1 --apply    proposes Ana, Chen and Dana\\n\"\n    )\n    assert api.writes() == []  # AC-22: a preview changes nothing\n\n\ndef test_s2_director_sees_the_same_table_without_the_apply_hint(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/missions/1/match\", ok(S2_PREVIEW | {\"can_apply\": False}))\n\n    result = mc(\"missions\", \"match\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == S2_TABLE\n    assert result.stderr == \"\"\n\n\ndef test_s3_unfilled_place_is_reported_but_is_not_an_error(mc, api):\n    mc.login_as(\"tok-nora\", \"nora@aurora.example\")\n    api.on(\"GET\", \"/missions/2/match\", ok(S3_PREVIEW))\n\n    result = mc(\"missions\", \"match\", \"2\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Asteroid Survey · 5–12 Mar 2027 · Draft\\n\"\n        \"! Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.\\n\"\n        \"\\n\"\n        \"  Slot        Suggested   Workload   Proficiency   Pick\\n\"\n        \"  Pilot       Ana         0 days     5             1\\n\"\n        \"  Geologist   unfilled (1 place)\\n\"\n        \"\\n\"\n        \"  The mission can't be submitted until every place is filled.\\n\"\n    )\n    assert result.stderr == (\n        \"Next: mc missions match 2 --apply    proposes Ana for Pilot\\n\"\n        \"      mc missions propose 2 --slot Geologist --crew EMAIL    fill Geologist by hand\\n\"\n    )\n\n\ndef test_m16_plain_words_with_no_color(mc, api, monkeypatch):\n    mc.login_as(\"tok-nora\", \"nora@aurora.example\")\n    monkeypatch.setenv(\"NO_COLOR\", \"1\")\n    api.on(\"GET\", \"/missions/2/match\", ok(S3_PREVIEW))\n\n    result = mc(\"missions\", \"match\", \"2\", color=None)\n\n    assert result.stdout.startswith(\n        \"Asteroid Survey - 5-12 Mar 2027 - Draft\\n\"\n        \"Note: Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.\\n\"\n    )\n\n\ndef test_m16_match_json_mirrors_the_preview(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/2/match\", ok(S3_PREVIEW))\n\n    result = mc(\"missions\", \"match\", \"2\", \"--json\")\n\n    assert result.exit_code == 0\n    assert json.loads(result.stdout) == S3_PREVIEW\n    assert result.stderr == \"\"\n\n\ndef test_m16_refused_when_the_mission_is_active(mc, api):\n    mc.login_as()\n    api.on(\n        \"GET\",\n        \"/missions/5/match\",\n        error(409, \"mission_frozen\", \"Can't suggest crew for an active mission\"),\n    )\n\n    result = mc(\"missions\", \"match\", \"5\")\n\n    assert result.exit_code == 1\n    assert result.stdout == \"\"\n    assert result.stderr == (\n        \"✗ Mission 5: Can't suggest crew for an active mission.\\n\"\n        \"  Only draft missions can be matched. See its crew: mc missions show 5\\n\"\n    )\n\n\ndef test_m16_refused_when_pending_or_final(mc, api):\n    mc.login_as()\n    api.on(\n        \"GET\",\n        \"/missions/6/match\",\n        error(409, \"invalid_transition\", \"Can't suggest crew for a mission pending approval\"),\n    )\n    api.on(\n        \"GET\",\n        \"/missions/7/match\",\n        error(409, \"mission_final\", \"Can't suggest crew for a mission that's completed\"),\n    )\n\n    pending = mc(\"missions\", \"match\", \"6\")\n    final = mc(\"missions\", \"match\", \"7\")\n\n    assert pending.stderr == (\n        \"✗ Mission 6: Can't suggest crew for a mission pending approval.\\n\"\n        \"  Only draft missions can be matched. Its places are already filled: \"\n        \"mc missions show 6\\n\"\n    )\n    assert final.stderr == (\n        \"✗ Mission 7: Can't suggest crew for a mission that's completed.\\n\"\n        \"  Only draft missions can be matched. See it: mc missions show 7\\n\"\n    )\n\n\ndef test_v2_hidden_mission_looks_exactly_like_an_unknown_id(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/missions/1/match\", error(404, \"not_found\", \"Mission not found\"))\n\n    result = mc(\"missions\", \"match\", \"1\")\n\n    assert result.exit_code == 1\n    assert result.stderr == \"✗ Mission 1 not found.\\n  See your missions: mc missions list\\n\"\n\n\ndef test_m3_another_leads_mission_is_refused_with_a_way_to_see_the_owner(mc, api):\n    mc.login_as(\"tok-nora\", \"nora@aurora.example\")\n    api.on(\n        \"GET\",\n        \"/missions/1/match\",\n        error(403, \"not_owner\", \"Only the owner or a Director can see suggested crew for this mission\"),\n    )\n\n    result = mc(\"missions\", \"match\", \"1\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ Only the owner or a Director can see suggested crew for this mission.\\n\"\n        \"  See who owns it: mc missions show 1\\n\"\n    )\n\n\ndef test_ac22_apply_creates_proposals_and_names_them(mc, api):\n    mc.login_as()\n    api.on(\n        \"POST\",\n        \"/missions/1/match/apply\",\n        ok(\n            [\n                {\"id\": 21, \"slot_id\": 3, \"crew_profile_id\": 6, \"status\": \"proposed\"},\n                {\"id\": 22, \"slot_id\": 1, \"crew_profile_id\": 8, \"status\": \"proposed\"},\n                {\"id\": 23, \"slot_id\": 2, \"crew_profile_id\": 9, \"status\": \"proposed\"},\n            ]\n        ),\n    )\n    proposed = [\n        {\"id\": 21, \"slot_id\": 3, \"slot_name\": \"Commander\", \"crew_profile_id\": 6,\n         \"crew_name\": \"Ana Okafor\", \"status\": \"proposed\", \"reason\": None},\n        {\"id\": 22, \"slot_id\": 1, \"slot_name\": \"Flight Engineer\", \"crew_profile_id\": 8,\n         \"crew_name\": \"Chen Wu\", \"status\": \"proposed\", \"reason\": None},\n        {\"id\": 23, \"slot_id\": 2, \"slot_name\": \"Mission Specialist\", \"crew_profile_id\": 9,\n         \"crew_name\": \"Dana Reyes\", \"status\": \"proposed\", \"reason\": None},\n    ]  # fmt: skip\n    api.on(\"GET\", \"/missions/1\", ok(gateway(assignments=proposed, open_places={1: 0, 2: 0, 3: 0})))\n\n    result = mc(\"missions\", \"match\", \"1\", \"--apply\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == (\n        \"✓ Proposed 3 crew for Lunar Gateway Resupply. Each of them needs to accept.\\n\"\n        \"\\n\"\n        \"  Assignment   Crew         Slot\\n\"\n        \"  21           Ana Okafor   Commander\\n\"\n        \"  22           Chen Wu      Flight Engineer\\n\"\n        \"  23           Dana Reyes   Mission Specialist\\n\"\n    )\n    assert \"Next: mc missions show 1\" in result.stderr\n    assert len(api.sent(\"POST\", \"/missions/1/match/apply\")) == 1\n\n\ndef test_m16_apply_with_nothing_to_propose(mc, api):\n    mc.login_as()\n    api.on(\"POST\", \"/missions/2/match/apply\", ok([]))\n\n    result = mc(\"missions\", \"match\", \"2\", \"--apply\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"! No crew could be proposed: no eligible crew for the open places.\\n\"\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_match.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_missions.py",
  "content": "\"\"\"M16: mission commands. References (missions by ID, people by email, skills by name, slots by\nname or position), the `--slot` spec on the wire, confirmations before changing a pending mission\nor cancelling, and what each command reports (design §8; PRD M1–M7, C4).\"\"\"\n\nimport json\n\nfrom cli_fakes import CREW, SKILLS, USERS, error, gateway, ok, problem\n\nNEW_MISSION = gateway() | {\"id\": 8, \"name\": \"Europa Flyby\", \"start_date\": \"2027-09-01\",\n                           \"end_date\": \"2027-09-20\"}  # fmt: skip\n\n\ndef _skills_and_crew(api):\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/users\", ok(USERS))\n\n\n# Create\n\n\ndef test_m2_create_sends_slots_with_skills_resolved_by_name(mc, api):\n    mc.login_as()\n    _skills_and_crew(api)\n    api.on(\"POST\", \"/missions\", ok(NEW_MISSION, status=201))\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"Europa Flyby\", \"--start\", \"2027-09-01\",\n        \"--end\", \"2027-09-20\", \"--slot\", \"Commander:1:piloting>=4,Leadership>=3\",\n        \"--slot\", \"Flight Engineer:2:Systems Engineering>=3\",\n    )  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/missions\")[0].body == {\n        \"name\": \"Europa Flyby\",\n        \"start_date\": \"2027-09-01\",\n        \"end_date\": \"2027-09-20\",\n        \"slots\": [\n            {\n                \"name\": \"Commander\",\n                \"headcount\": 1,\n                \"requirements\": [\n                    {\"skill_id\": 1, \"min_level\": 4},\n                    {\"skill_id\": 2, \"min_level\": 3},\n                ],\n            },\n            {\n                \"name\": \"Flight Engineer\",\n                \"headcount\": 2,\n                \"requirements\": [{\"skill_id\": 3, \"min_level\": 3}],\n            },\n        ],\n    }\n    assert result.stdout == \"✓ Created mission 8: Europa Flyby · 1–20 Sep 2027 · Draft\\n\"\n    assert \"Next: mc missions match 8\" in result.stderr\n\n\ndef test_m1_director_names_the_owner_by_email(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    _skills_and_crew(api)\n    api.on(\"POST\", \"/missions\", ok(NEW_MISSION, status=201))\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"Europa Flyby\", \"--start\", \"2027-09-01\",\n        \"--end\", \"2027-09-20\", \"--slot\", \"Commander:1:Piloting>=4\", \"--owner\", \"LEE@aurora.example\",\n    )  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/missions\")[0].body[\"owner_id\"] == 4\n\n\ndef test_m16_create_with_an_unknown_skill_names_it_and_sends_nothing(mc, api):\n    mc.login_as()\n    _skills_and_crew(api)\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"X\", \"--start\", \"2027-09-01\", \"--end\", \"2027-09-02\",\n        \"--slot\", \"Commander:1:Pilotting>=4\",\n    )  # fmt: skip\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ There's no skill called 'Pilotting'.\\n  See the skills: mc skills list\\n\"\n    )\n    assert api.writes() == []\n\n\ndef test_m16_create_with_a_malformed_slot_is_a_usage_error(mc, api):\n    mc.login_as()\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"X\", \"--start\", \"2027-09-01\", \"--end\", \"2027-09-02\",\n        \"--slot\", \"Commander-1-Piloting4\",\n    )  # fmt: skip\n\n    assert result.exit_code == 2\n    assert \"NAME:HEADCOUNT:SKILL>=LEVEL\" in result.stderr\n    assert api.calls == []\n\n\ndef test_m16_dates_must_be_iso(mc, api):\n    mc.login_as()\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"X\", \"--start\", \"1 Sep\", \"--end\", \"2027-09-02\",\n        \"--slot\", \"Commander:1:Piloting>=4\",\n    )  # fmt: skip\n\n    assert result.exit_code == 2\n    assert \"Use YYYY-MM-DD\" in result.stderr\n    assert api.calls == []\n\n\ndef test_m2_end_before_start_is_judged_by_the_server(mc, api):\n    mc.login_as()\n    _skills_and_crew(api)\n    api.on(\n        \"POST\",\n        \"/missions\",\n        error(422, \"validation_error\", \"The end date can't be before the start date\"),\n    )\n\n    result = mc(\n        \"missions\", \"create\", \"--name\", \"X\", \"--start\", \"2027-09-05\", \"--end\", \"2027-09-01\",\n        \"--slot\", \"Commander:1:Piloting>=4\",\n    )  # fmt: skip\n\n    assert result.exit_code == 1\n    assert \"✗ The end date can't be before the start date.\" in result.stderr\n\n\n# Lists and views\n\n\ndef test_m16_list_missions_as_a_table(mc, api):\n    mc.login_as()\n    api.on(\n        \"GET\",\n        \"/missions\",\n        ok(\n            [\n                gateway(),\n                gateway(\"pending_approval\") | {\"id\": 6, \"name\": \"Deep Space Comms Upgrade\",\n                                               \"start_date\": \"2027-04-01\", \"end_date\": \"2027-04-20\",\n                                               \"owner_name\": \"Nora Quinn\"},\n            ]\n        ),\n    )  # fmt: skip\n\n    result = mc(\"missions\", \"list\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"  ID   Mission                    Dates           Status             Owner\\n\"\n        \"  1    Lunar Gateway Resupply     1–10 Mar 2027   Draft              Lee Park\\n\"\n        \"  6    Deep Space Comms Upgrade   1–20 Apr 2027   Pending approval   Nora Quinn\\n\"\n    )\n\n\ndef test_v2_empty_mission_list(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/missions\", ok([]))\n\n    result = mc(\"missions\", \"list\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"No missions to show.\\n\"\n\n\ndef test_m16_show_mission_lists_slots_crew_and_approvals(mc, api):\n    mc.login_as()\n    crew_rows = [\n        {\"id\": 21, \"slot_id\": 1, \"slot_name\": \"Flight Engineer\", \"crew_profile_id\": 8,\n         \"crew_name\": \"Chen Wu\", \"status\": \"accepted\", \"reason\": None},\n    ]  # fmt: skip\n    approvals = [\n        {\"director_id\": 2, \"director_name\": \"Marco Bianchi\", \"decision\": \"approve\", \"reason\": None}\n    ]\n    api.on(\n        \"GET\",\n        \"/missions/1\",\n        ok(gateway(\"pending_approval\", crew_rows, approvals, open_places={1: 0})),\n    )\n\n    result = mc(\"missions\", \"show\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Lunar Gateway Resupply · 1–10 Mar 2027 · Pending approval\\n\"\n        \"Owner Lee Park · created by Ruth Adeyemi\\n\"\n        \"\\n\"\n        \"  #   Slot                 Requires                        Places\\n\"\n        \"  1   Flight Engineer      Systems Engineering>=3          full\\n\"\n        \"  2   Mission Specialist   EVA>=3                          1 of 1 open\\n\"\n        \"  3   Commander            Piloting>=4, Leadership>=3      1 of 1 open\\n\"\n        \"\\n\"\n        \"  Assignment   Crew      Slot              Status\\n\"\n        \"  21           Chen Wu   Flight Engineer   accepted\\n\"\n        \"\\n\"\n        \"Approvals: 1 of 2 (Marco Bianchi)\\n\"\n    )\n\n\ndef test_v1_history_shows_who_did_what_and_when(mc, api):\n    mc.login_as()\n    api.on(\n        \"GET\",\n        \"/missions/6/history\",\n        ok(\n            [\n                {\"id\": 1, \"created_at\": \"2027-01-02T10:00:00.000Z\", \"actor_id\": 5,\n                 \"actor_name\": \"Nora Quinn\", \"event\": \"mission.submitted\",\n                 \"from_status\": \"draft\", \"to_status\": \"pending_approval\", \"reason\": None,\n                 \"data\": {}},\n                {\"id\": 2, \"created_at\": \"2027-01-03T11:30:00.000Z\", \"actor_id\": 7,\n                 \"actor_name\": \"Ben Ito\", \"event\": \"assignment.withdrawn\",\n                 \"from_status\": \"accepted\", \"to_status\": \"withdrawn\", \"reason\": \"Family matter\",\n                 \"data\": {\"slot_name\": \"Engineer\", \"crew_name\": \"Ben Ito\"}},\n            ]\n        ),\n    )  # fmt: skip\n\n    result = mc(\"missions\", \"history\", \"6\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"  When (UTC)          Who          What                     Reason\\n\"\n        \"  2 Jan 2027 10:00    Nora Quinn   Submitted for approval\\n\"\n        \"  3 Jan 2027 11:30    Ben Ito      Withdrew from Engineer   Family matter\\n\"\n    )\n\n\n# Confirmations (C4)\n\n\ndef test_c4_editing_a_pending_mission_asks_first_and_yes_changes_it(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway(\"pending_approval\")))\n    api.on(\"PATCH\", \"/missions/1\", ok(gateway()))\n\n    result = mc(\"missions\", \"edit\", \"1\", \"--end\", \"2027-03-12\", input=\"y\\n\", interactive=True)\n\n    assert result.exit_code == 0, result.stderr\n    assert (\n        \"! Lunar Gateway Resupply is pending approval. Editing it sends it back to Draft and \"\n        \"clears its approvals.\" in result.stderr\n    )\n    assert \"Continue? [y/N]: \" in result.stderr\n    assert api.sent(\"PATCH\", \"/missions/1\")[0].body == {\"end_date\": \"2027-03-12\"}\n    assert result.stdout == \"✓ Updated Lunar Gateway Resupply. It's back in Draft.\\n\"\n\n\ndef test_c4_declining_the_prompt_changes_nothing(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway(\"pending_approval\")))\n\n    result = mc(\"missions\", \"edit\", \"1\", \"--name\", \"New\", input=\"n\\n\", interactive=True)\n\n    assert result.exit_code == 1\n    assert \"Nothing was changed.\" in result.stderr\n    assert api.writes() == []\n\n\ndef test_c4_without_a_terminal_the_change_needs_yes(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway(\"pending_approval\")))\n\n    result = mc(\"missions\", \"edit\", \"1\", \"--name\", \"New\")\n\n    assert result.exit_code == 2\n    assert \"Re-run with --yes to go ahead.\" in result.stderr\n    assert api.writes() == []\n\n\ndef test_c4_yes_skips_the_prompt(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway(\"pending_approval\")))\n    api.on(\"PATCH\", \"/missions/1\", ok(gateway()))\n\n    result = mc(\"missions\", \"edit\", \"1\", \"--name\", \"New\", \"--yes\")\n\n    assert result.exit_code == 0, result.stderr\n    assert \"Continue?\" not in result.stderr\n\n\ndef test_c4_editing_a_draft_does_not_ask(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"PATCH\", \"/missions/1\", ok(gateway()))\n\n    result = mc(\"missions\", \"edit\", \"1\", \"--name\", \"New\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == \"✓ Updated Lunar Gateway Resupply.\\n\"\n\n\ndef test_m16_edit_with_nothing_to_change_is_a_usage_error(mc, api):\n    mc.login_as()\n\n    result = mc(\"missions\", \"edit\", \"1\")\n\n    assert result.exit_code == 2\n    assert \"Nothing to change\" in result.stderr\n    assert api.calls == []\n\n\ndef test_c4_cancelling_always_asks_and_sends_the_reason(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"POST\", \"/missions/1/cancel\", ok(gateway(\"cancelled\")))\n\n    result = mc(\"missions\", \"cancel\", \"1\", \"--reason\", \"Budget cut\", input=\"y\\n\", interactive=True)\n\n    assert result.exit_code == 0, result.stderr\n    assert \"Cancel Lunar Gateway Resupply? Its open assignments will be cancelled too.\" in (\n        result.stderr\n    )\n    assert api.sent(\"POST\", \"/missions/1/cancel\")[0].body == {\"reason\": \"Budget cut\"}\n    assert result.stdout == \"✓ Cancelled Lunar Gateway Resupply.\\n\"\n\n\ndef test_ac6_cancel_needs_a_reason_flag(mc, api):\n    mc.login_as()\n\n    result = mc(\"missions\", \"cancel\", \"1\", \"--yes\")\n\n    assert result.exit_code == 2\n    assert \"--reason\" in result.stderr\n    assert api.calls == []\n\n\n# Slots: by name or position\n\n\ndef test_m16_slot_edit_finds_the_slot_by_position(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"PATCH\", \"/missions/1/slots/3\", ok(gateway()))\n\n    result = mc(\"missions\", \"slot\", \"edit\", \"1\", \"3\", \"--headcount\", \"2\",\n                \"--requires\", \"Piloting>=5\")  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"PATCH\", \"/missions/1/slots/3\")[0].body == {\n        \"headcount\": 2,\n        \"requirements\": [{\"skill_id\": 1, \"min_level\": 5}],\n    }\n    assert result.stdout == \"✓ Updated Commander on Lunar Gateway Resupply.\\n\"\n\n\ndef test_m16_slot_remove_finds_the_slot_by_name_ignoring_case(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"DELETE\", \"/missions/1/slots/2\", ok(gateway()))\n\n    result = mc(\"missions\", \"slot\", \"remove\", \"1\", \"mission specialist\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == \"✓ Removed Mission Specialist from Lunar Gateway Resupply.\\n\"\n\n\ndef test_m16_unknown_slot_lists_the_ones_that_exist(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n\n    by_name = mc(\"missions\", \"slot\", \"remove\", \"1\", \"Pilot\")\n    by_position = mc(\"missions\", \"slot\", \"remove\", \"1\", \"7\")\n\n    expected_hint = \"  Its slots: 1 Flight Engineer, 2 Mission Specialist, 3 Commander\\n\"\n    assert by_name.exit_code == 1\n    assert by_name.stderr == \"✗ Lunar Gateway Resupply has no slot called 'Pilot'.\\n\" + expected_hint\n    assert by_position.stderr == \"✗ Lunar Gateway Resupply has no slot 7.\\n\" + expected_hint\n    assert api.writes() == []\n\n\ndef test_m16_slot_add_uses_the_slot_spec(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"POST\", \"/missions/1/slots\", ok(gateway(), status=201))\n\n    result = mc(\"missions\", \"slot\", \"add\", \"1\", \"--slot\", \"Geologist:1:Geology>=4\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/missions/1/slots\")[0].body == {\n        \"name\": \"Geologist\",\n        \"headcount\": 1,\n        \"requirements\": [{\"skill_id\": 5, \"min_level\": 4}],\n    }\n    assert result.stdout == \"✓ Added Geologist to Lunar Gateway Resupply.\\n\"\n\n\ndef test_m7_slot_change_that_would_invalidate_crew_lists_them(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    message = (\n        \"Can't remove Flight Engineer from Lunar Gateway Resupply while Chen Wu is assigned to it. \"\n        \"Remove them from the mission first.\"\n    )\n    api.on(\n        \"DELETE\",\n        \"/missions/1/slots/1\",\n        error(\n            409,\n            \"invalidates_assignments\",\n            message,\n            [problem(\"slot_has_open_assignments\", \"Chen Wu is assigned to Flight Engineer\",\n                     assignment_id=21, crew_profile_id=8, slot_id=1)],\n        ),\n    )  # fmt: skip\n\n    result = mc(\"missions\", \"slot\", \"remove\", \"1\", \"Flight Engineer\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        f\"✗ {message}\\n\"\n        \"  • Chen Wu is assigned to Flight Engineer\\n\"\n        \"  Remove crew first: mc missions remove-crew 1 21\\n\"\n    )\n\n\n# Crew on a mission\n\n\ndef test_s1_propose_resolves_slot_by_name_and_crew_by_email(mc, api):\n    mc.login_as()\n    _skills_and_crew(api)\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\n        \"POST\",\n        \"/missions/1/assignments\",\n        ok({\"id\": 21, \"mission_id\": 1, \"slot_id\": 1, \"crew_profile_id\": 8, \"status\": \"proposed\",\n            \"reason\": None}, status=201),\n    )  # fmt: skip\n\n    result = mc(\"missions\", \"propose\", \"1\", \"--slot\", \"Flight Engineer\",\n                \"--crew\", \"Chen@Aurora.example\")  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/missions/1/assignments\")[0].body == {\n        \"slot_id\": 1,\n        \"crew_profile_id\": 8,\n    }\n    assert result.stdout == (\n        \"✓ Proposed Chen Wu for Flight Engineer on Lunar Gateway Resupply (assignment 21). \"\n        \"They need to accept.\\n\"\n    )\n\n\ndef test_m16_propose_unknown_email_is_refused_before_writing(mc, api):\n    mc.login_as()\n    _skills_and_crew(api)\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n\n    result = mc(\"missions\", \"propose\", \"1\", \"--slot\", \"1\", \"--crew\", \"zed@aurora.example\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ There's no crew member with the email zed@aurora.example.\\n\"\n        \"  See the crew: mc crew list\\n\"\n    )\n    assert api.writes() == []\n\n\ndef test_m16_remove_crew_checks_the_assignment_is_on_that_mission(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n\n    result = mc(\"missions\", \"remove-crew\", \"1\", \"99\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ Assignment 99 isn't on Lunar Gateway Resupply.\\n  See its crew: mc missions show 1\\n\"\n    )\n    assert api.writes() == []\n\n\ndef test_ac4_remove_crew_from_a_pending_mission_confirms(mc, api):\n    mc.login_as()\n    row = {\"id\": 21, \"slot_id\": 1, \"slot_name\": \"Flight Engineer\", \"crew_profile_id\": 8,\n           \"crew_name\": \"Chen Wu\", \"status\": \"accepted\", \"reason\": None}  # fmt: skip\n    api.on(\"GET\", \"/missions/1\", ok(gateway(\"pending_approval\", [row])))\n    api.on(\"POST\", \"/assignments/21/remove\", ok(row | {\"status\": \"removed\"}))\n\n    result = mc(\"missions\", \"remove-crew\", \"1\", \"21\", \"--yes\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == (\n        \"✓ Removed Chen Wu from Flight Engineer on Lunar Gateway Resupply. It's back in Draft.\\n\"\n    )\n\n\n# Lifecycle\n\n\ndef test_s1_submit_reports_the_approvals_needed(mc, api):\n    mc.login_as()\n    api.on(\"POST\", \"/missions/1/submit\", ok(gateway(\"pending_approval\")))\n\n    result = mc(\"missions\", \"submit\", \"1\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == (\n        \"✓ Submitted Lunar Gateway Resupply for approval. It needs 2 approvals.\\n\"\n    )\n\n\ndef test_ac3_approval_before_the_last_leaves_it_pending(mc, api):\n    mc.login_as(\"tok-marco\", \"marco@aurora.example\")\n    approvals = [{\"director_id\": 2, \"director_name\": \"Marco Bianchi\", \"decision\": \"approve\",\n                  \"reason\": None}]  # fmt: skip\n    api.on(\"POST\", \"/missions/1/approve\", ok(gateway(\"pending_approval\", approvals=approvals)))\n\n    result = mc(\"missions\", \"approve\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"✓ Approved Lunar Gateway Resupply. It's pending approval (1 of 2 approvals).\\n\"\n    )\n\n\ndef test_ac3_final_approval_makes_it_active(mc, api):\n    mc.login_as(\"tok-ingrid\", \"ingrid@aurora.example\")\n    api.on(\"POST\", \"/missions/1/approve\", ok(gateway(\"active\")))\n\n    result = mc(\"missions\", \"approve\", \"1\")\n\n    assert result.stdout == \"✓ Approved Lunar Gateway Resupply. It's now active.\\n\"\n\n\ndef test_ac8_creator_cannot_approve(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\n        \"POST\",\n        \"/missions/1/approve\",\n        error(403, \"approver_is_creator\", \"You can't approve a mission you created\"),\n    )\n\n    result = mc(\"missions\", \"approve\", \"1\")\n\n    assert result.exit_code == 1\n    assert result.stderr == \"✗ You can't approve a mission you created.\\n\"\n\n\ndef test_ac10_reject_sends_the_reason(mc, api):\n    mc.login_as(\"tok-ingrid\", \"ingrid@aurora.example\")\n    api.on(\"POST\", \"/missions/6/reject\", ok(gateway() | {\"id\": 6, \"name\": \"Deep Space Comms Upgrade\"}))\n\n    result = mc(\"missions\", \"reject\", \"6\", \"--reason\", \"Roster too thin\")\n\n    assert result.exit_code == 0\n    assert api.sent(\"POST\", \"/missions/6/reject\")[0].body == {\"reason\": \"Roster too thin\"}\n    assert result.stdout == \"✓ Rejected Deep Space Comms Upgrade. It's back in Draft.\\n\"\n\n\ndef test_ac7_transfer_resolves_the_new_owner_by_email(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/users\", ok(USERS))\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"POST\", \"/missions/1/owner\", ok(gateway() | {\"owner_id\": 5, \"owner_name\": \"Nora Quinn\"}))\n\n    result = mc(\"missions\", \"transfer\", \"1\", \"--owner\", \"nora@aurora.example\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/missions/1/owner\")[0].body == {\"owner_id\": 5}\n    assert result.stdout == \"✓ Lunar Gateway Resupply now belongs to Nora Quinn.\\n\"\n\n\ndef test_s1_complete(mc, api):\n    mc.login_as()\n    api.on(\"POST\", \"/missions/1/complete\", ok(gateway(\"completed\")))\n\n    result = mc(\"missions\", \"complete\", \"1\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"✓ Completed Lunar Gateway Resupply. Its accepted assignments are completed too.\\n\"\n    )\n\n\ndef test_m16_action_json_prints_the_api_body(mc, api):\n    mc.login_as()\n    api.on(\"POST\", \"/missions/1/submit\", ok(gateway(\"pending_approval\")))\n\n    result = mc(\"missions\", \"submit\", \"1\", \"--json\")\n\n    assert json.loads(result.stdout)[\"status\"] == \"pending_approval\"\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_missions.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_people.py",
  "content": "\"\"\"M16: everyone's own commands (inbox, assignments, profile and availability) and the crew,\nusers, skills and organisation commands (design §8; PRD §4, P1–P10, S2–S3, V2).\"\"\"\n\nfrom cli_fakes import CREW, LEE_ME, SKILLS, USERS, error, ok\n\nGATEWAY_PROPOSAL = {\n    \"assignment_id\": 21,\n    \"mission_id\": 1,\n    \"mission_name\": \"Lunar Gateway Resupply\",\n    \"start_date\": \"2027-03-01\",\n    \"end_date\": \"2027-03-10\",\n    \"mission_status\": \"draft\",\n    \"slot_name\": \"Flight Engineer\",\n    \"status\": \"proposed\",\n    \"reason\": None,\n}\nCOMMS_ACCEPTED = {\n    \"assignment_id\": 31,\n    \"mission_id\": 6,\n    \"mission_name\": \"Deep Space Comms Upgrade\",\n    \"start_date\": \"2027-04-01\",\n    \"end_date\": \"2027-04-20\",\n    \"mission_status\": \"pending_approval\",\n    \"slot_name\": \"Engineer\",\n    \"status\": \"accepted\",\n    \"reason\": None,\n}\nBEN_ME = LEE_ME | {\"id\": 7, \"email\": \"ben@aurora.example\", \"name\": \"Ben Ito\", \"role\": \"crew\",\n                   \"crew_profile_id\": 7}  # fmt: skip\n\n\ndef _assignment(aid, status, reason=None):\n    return ok({\"id\": aid, \"mission_id\": 1, \"slot_id\": 1, \"crew_profile_id\": 8, \"status\": status,\n               \"reason\": reason})  # fmt: skip\n\n\n# Inbox and assignments\n\n\ndef test_m16_inbox_groups_what_is_waiting(mc, api):\n    mc.login_as(\"tok-chen\", \"chen@aurora.example\")\n    api.on(\n        \"GET\",\n        \"/me/inbox\",\n        ok({\"assignments\": [GATEWAY_PROPOSAL], \"approvals\": [], \"missions\": []}),\n    )\n\n    result = mc(\"inbox\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Proposals waiting for your answer\\n\"\n        \"  Assignment   Mission                  Slot              Dates\\n\"\n        \"  21           Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027\\n\"\n    )\n    assert \"Next: mc assignments accept 21\" in result.stderr\n\n\ndef test_m16_empty_inbox(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me/inbox\", ok({\"assignments\": [], \"approvals\": [], \"missions\": []}))\n\n    result = mc(\"inbox\")\n\n    assert result.stdout == \"✓ Nothing needs your attention.\\n\"\n\n\ndef test_s2_assignments_list_pending_only(mc, api):\n    mc.login_as(\"tok-chen\", \"chen@aurora.example\")\n    api.on(\"GET\", \"/assignments\", ok([GATEWAY_PROPOSAL]))\n\n    result = mc(\"assignments\", \"list\", \"--pending\")\n\n    assert result.exit_code == 0\n    assert api.calls[-1].params == {\"pending\": \"true\"}\n    assert result.stdout == (\n        \"  ID   Mission                  Slot              Dates           Status\\n\"\n        \"  21   Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027   proposed\\n\"\n    )\n\n\ndef test_s2_accept_names_the_slot_and_mission(mc, api):\n    mc.login_as(\"tok-chen\", \"chen@aurora.example\")\n    api.on(\"GET\", \"/assignments\", ok([GATEWAY_PROPOSAL]))\n    api.on(\"POST\", \"/assignments/21/accept\", _assignment(21, \"accepted\"))\n\n    result = mc(\"assignments\", \"accept\", \"21\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == \"✓ Accepted Flight Engineer on Lunar Gateway Resupply.\\n\"\n\n\ndef test_s3_decline_with_an_optional_reason(mc, api):\n    mc.login_as(\"tok-chen\", \"chen@aurora.example\")\n    api.on(\"GET\", \"/assignments\", ok([GATEWAY_PROPOSAL]))\n    api.on(\"POST\", \"/assignments/21/decline\", _assignment(21, \"declined\"))\n\n    plain = mc(\"assignments\", \"decline\", \"21\")\n    reasoned = mc(\"assignments\", \"decline\", \"21\", \"--reason\", \"On leave\")\n\n    assert plain.exit_code == reasoned.exit_code == 0\n    assert api.sent(\"POST\", \"/assignments/21/decline\")[0].body is None\n    assert api.sent(\"POST\", \"/assignments/21/decline\")[1].body == {\"reason\": \"On leave\"}\n    assert plain.stdout == \"✓ Declined Flight Engineer on Lunar Gateway Resupply.\\n\"\n\n\ndef test_s5_withdraw_from_a_pending_mission_warns_then_sends_the_reason(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/assignments\", ok([COMMS_ACCEPTED]))\n    api.on(\"POST\", \"/assignments/31/withdraw\", _assignment(31, \"withdrawn\", \"Family matter\"))\n\n    result = mc(\n        \"assignments\", \"withdraw\", \"31\", \"--reason\", \"Family matter\", input=\"y\\n\", interactive=True\n    )\n\n    assert result.exit_code == 0, result.stderr\n    assert (\n        \"! Deep Space Comms Upgrade is pending approval. Withdrawing sends it back to Draft and \"\n        \"clears its approvals.\" in result.stderr\n    )\n    assert api.sent(\"POST\", \"/assignments/31/withdraw\")[0].body == {\"reason\": \"Family matter\"}\n    assert result.stdout == (\n        \"✓ Withdrew from Engineer on Deep Space Comms Upgrade. It's back in Draft.\\n\"\n    )\n\n\ndef test_s5_withdraw_from_an_active_mission_is_refused_by_the_server(mc, api):\n    mc.login_as(\"tok-hana\", \"hana@aurora.example\")\n    telescope = COMMS_ACCEPTED | {\"assignment_id\": 41, \"mission_id\": 5,\n                                  \"mission_name\": \"Orbital Telescope Service\",\n                                  \"mission_status\": \"active\"}  # fmt: skip\n    api.on(\"GET\", \"/assignments\", ok([telescope]))\n    api.on(\n        \"POST\",\n        \"/assignments/41/withdraw\",\n        error(409, \"mission_frozen\", \"Can't withdraw from an active mission\"),\n    )\n\n    result = mc(\"assignments\", \"withdraw\", \"41\", \"--reason\", \"Sick\")\n\n    assert result.exit_code == 1\n    assert result.stderr.startswith(\"✗ Can't withdraw from an active mission.\\n\")\n\n\ndef test_m16_someone_elses_assignment_looks_unknown(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/assignments\", ok([]))\n    api.on(\"POST\", \"/assignments/21/accept\", error(404, \"not_found\", \"Assignment not found\"))\n\n    result = mc(\"assignments\", \"accept\", \"21\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ Assignment 21 not found.\\n  See your assignments: mc assignments list\\n\"\n    )\n\n\n# My profile and availability\n\n\ndef test_p4_me_show_includes_profile_skills_and_unavailability(mc, api):\n    mc.login_as(\"tok-fay\", \"fay@aurora.example\")\n    fay = next(c for c in CREW if c[\"crew_profile_id\"] == 11)\n    fay = fay | {\"unavailability\": [{\"id\": 1, \"start_date\": \"2027-03-05\",\n                                     \"end_date\": \"2027-03-08\", \"reason\": \"Medical\"}]}  # fmt: skip\n    api.on(\"GET\", \"/me\", ok(BEN_ME | {\"name\": \"Fay Moreau\", \"email\": \"fay@aurora.example\",\n                                      \"crew_profile_id\": 11}))  # fmt: skip\n    api.on(\"GET\", \"/crew/11\", ok(fay))\n\n    result = mc(\"me\", \"show\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Name           Fay Moreau\\n\"\n        \"Email          fay@aurora.example\\n\"\n        \"Role           Crew Member\\n\"\n        \"Organisation   Aurora Space Agency\\n\"\n        \"Bio            none\\n\"\n        \"\\n\"\n        \"  Skill        Level\\n\"\n        \"  Piloting     4\\n\"\n        \"  Leadership   4\\n\"\n        \"\\n\"\n        \"  Unavailable   Dates          Reason\\n\"\n        \"  1             5–8 Mar 2027   Medical\\n\"\n    )\n\n\ndef test_p4_me_update_sends_only_what_changed(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/me\", ok(BEN_ME))\n    api.on(\"PATCH\", \"/crew/7\", ok(CREW[1]))\n\n    result = mc(\"me\", \"update\", \"--bio\", \"EVA and systems\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"PATCH\", \"/crew/7\")[0].body == {\"bio\": \"EVA and systems\"}\n    assert result.stdout == \"✓ Updated your profile.\\n\"\n\n\ndef test_m16_me_without_a_crew_profile_explains(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/me\", ok(LEE_ME))\n\n    result = mc(\"me\", \"unavailable\", \"list\")\n\n    assert result.exit_code == 1\n    assert result.stderr == (\n        \"✗ You don't have a crew profile.\\n  A Director can give you one: mc users enable-crew EMAIL\\n\"\n    )\n\n\ndef test_p5_add_unavailability(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/me\", ok(BEN_ME))\n    api.on(\n        \"POST\",\n        \"/crew/7/unavailability\",\n        ok({\"id\": 4, \"start_date\": \"2027-06-01\", \"end_date\": \"2027-06-03\", \"reason\": \"Leave\"},\n           status=201),\n    )  # fmt: skip\n\n    result = mc(\"me\", \"unavailable\", \"add\", \"--start\", \"2027-06-01\", \"--end\", \"2027-06-03\",\n                \"--reason\", \"Leave\")  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"POST\", \"/crew/7/unavailability\")[0].body == {\n        \"start_date\": \"2027-06-01\",\n        \"end_date\": \"2027-06-03\",\n        \"reason\": \"Leave\",\n    }\n    assert result.stdout == \"✓ Added unavailability 4: 1–3 Jun 2027 (Leave).\\n\"\n\n\ndef test_ac16_unavailability_overlapping_an_accepted_assignment_is_refused(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/me\", ok(BEN_ME))\n    message = \"You have an accepted assignment on Deep Space Comms Upgrade overlapping 1–3 Apr\"\n    api.on(\"POST\", \"/crew/7/unavailability\", error(409, \"overlap\", message))\n\n    result = mc(\"me\", \"unavailable\", \"add\", \"--start\", \"2027-04-01\", \"--end\", \"2027-04-03\",\n                \"--reason\", \"Leave\")  # fmt: skip\n\n    assert result.exit_code == 1\n    assert result.stderr.startswith(f\"✗ {message}.\\n\")\n\n\ndef test_p5_remove_unavailability(mc, api):\n    mc.login_as(\"tok-ben\", \"ben@aurora.example\")\n    api.on(\"GET\", \"/me\", ok(BEN_ME))\n    api.on(\"DELETE\", \"/crew/7/unavailability/4\", ok(status=204))\n\n    result = mc(\"me\", \"unavailable\", \"remove\", \"4\")\n\n    assert result.exit_code == 0\n    assert result.stdout == \"✓ Removed unavailability 4.\\n\"\n\n\n# Crew\n\n\ndef test_ac24_lead_sees_busy_dates_without_reasons(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    fay = next(c for c in CREW if c[\"crew_profile_id\"] == 11)\n    api.on(\"GET\", \"/crew/11\", ok(fay))\n\n    result = mc(\"crew\", \"show\", \"fay@aurora.example\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"Name    Fay Moreau\\n\"\n        \"Email   fay@aurora.example\\n\"\n        \"Bio     none\\n\"\n        \"\\n\"\n        \"  Skill        Level\\n\"\n        \"  Piloting     4\\n\"\n        \"  Leadership   4\\n\"\n        \"\\n\"\n        \"  Unavailable   Dates\\n\"\n        \"  1             5–8 Mar 2027\\n\"\n    )\n\n\ndef test_m16_crew_list(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/crew\", ok(CREW[:2]))\n\n    result = mc(\"crew\", \"list\")\n\n    assert result.stdout == (\n        \"  Name         Email                Skills\\n\"\n        \"  Ana Okafor   ana@aurora.example   Piloting 5, Leadership 4\\n\"\n        \"  Ben Ito      ben@aurora.example   Systems Engineering 4, EVA 3\\n\"\n    )\n\n\ndef test_ac23_set_skill_by_email_and_skill_name(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"PUT\", \"/crew/6/skills/1\", ok(CREW[0]))\n\n    result = mc(\"crew\", \"set-skill\", \"ana@aurora.example\", \"piloting\", \"4\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"PUT\", \"/crew/6/skills/1\")[0].body == {\"level\": 4}\n    assert result.stdout == \"✓ Set Ana Okafor's Piloting to 4.\\n\"\n\n\ndef test_ac23_own_skills_are_refused_by_the_server(mc, api):\n    mc.login_as(\"tok-ana\", \"ana@aurora.example\")\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\n        \"PUT\",\n        \"/crew/6/skills/1\",\n        error(403, \"self_skill_edit\", \"You can't change your own skill levels\"),\n    )\n\n    result = mc(\"crew\", \"set-skill\", \"ana@aurora.example\", \"Piloting\", \"5\")\n\n    assert result.exit_code == 1\n    assert result.stderr == \"✗ You can't change your own skill levels.\\n\"\n\n\ndef test_p3_unset_skill(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"DELETE\", \"/crew/6/skills/2\", ok(status=204))\n\n    result = mc(\"crew\", \"unset-skill\", \"ana@aurora.example\", \"Leadership\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == \"✓ Removed Leadership from Ana Okafor's skills.\\n\"\n\n\ndef test_m16_crew_history(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/crew/8/assignments\", ok([GATEWAY_PROPOSAL | {\"status\": \"declined\"}]))\n\n    result = mc(\"crew\", \"history\", \"chen@aurora.example\")\n\n    assert result.exit_code == 0\n    assert result.stdout == (\n        \"  Assignment   Mission                  Slot              Dates           Status\\n\"\n        \"  21           Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027   declined\\n\"\n    )\n\n\n# Users, skills and the organisation (Directors)\n\n\ndef test_p10_add_user_asks_for_the_initial_password_twice(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    created = {\"id\": 20, \"email\": \"zoe@aurora.example\", \"name\": \"Zoe Lin\", \"role\": \"crew\",\n               \"is_active\": True}  # fmt: skip\n    api.on(\"POST\", \"/users\", ok(created, status=201))\n\n    result = mc(\n        \"users\", \"add\", \"--email\", \"zoe@aurora.example\", \"--name\", \"Zoe Lin\", \"--role\", \"crew\",\n        input=\"a long first passphrase\\na long first passphrase\\n\", interactive=True,\n    )  # fmt: skip\n\n    assert result.exit_code == 0, result.stderr\n    assert \"Initial password: \" in result.stderr\n    assert \"Repeat initial password: \" in result.stderr\n    assert api.sent(\"POST\", \"/users\")[0].body == {\n        \"email\": \"zoe@aurora.example\",\n        \"name\": \"Zoe Lin\",\n        \"role\": \"crew\",\n        \"password\": \"a long first passphrase\",\n    }\n    assert result.stdout == \"✓ Added Zoe Lin (zoe@aurora.example) as a Crew Member.\\n\"\n\n\ndef test_m16_role_must_be_one_of_the_three(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n\n    result = mc(\"users\", \"set-role\", \"lee@aurora.example\", \"captain\")\n\n    assert result.exit_code == 2\n    assert \"director\" in result.stderr and \"lead\" in result.stderr\n    assert api.calls == []\n\n\ndef test_ac26_last_director_cannot_be_demoted(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/users\", ok(USERS))\n    api.on(\n        \"PATCH\",\n        \"/users/1\",\n        error(409, \"last_director\", \"Ruth Adeyemi is the last active Director\"),\n    )\n\n    result = mc(\"users\", \"set-role\", \"ruth@aurora.example\", \"lead\")\n\n    assert result.exit_code == 1\n    assert api.sent(\"PATCH\", \"/users/1\")[0].body == {\"role\": \"lead\"}\n    assert result.stderr.startswith(\"✗ Ruth Adeyemi is the last active Director.\\n\")\n\n\ndef test_p7_deactivate_user(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/users\", ok(USERS))\n    api.on(\"PATCH\", \"/users/8\", ok(USERS[3] | {\"is_active\": False}))\n\n    result = mc(\"users\", \"deactivate\", \"chen@aurora.example\")\n\n    assert result.exit_code == 0, result.stderr\n    assert api.sent(\"PATCH\", \"/users/8\")[0].body == {\"is_active\": False}\n    assert result.stdout == \"✓ Deactivated Chen Wu. They can no longer log in.\\n\"\n\n\ndef test_p9_enable_crew(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/users\", ok(USERS))\n    api.on(\"POST\", \"/users/4/crew-profile\", ok({\"crew_profile_id\": 4}, status=201))\n\n    result = mc(\"users\", \"enable-crew\", \"lee@aurora.example\")\n\n    assert result.exit_code == 0, result.stderr\n    assert result.stdout == \"✓ Lee Park now has a crew profile.\\n\"\n\n\ndef test_m16_users_list(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/users\", ok(USERS[:2] + [USERS[3] | {\"is_active\": False}]))\n\n    result = mc(\"users\", \"list\")\n\n    assert result.stdout == (\n        \"  ID   Name           Email                 Role           Status\\n\"\n        \"  1    Ruth Adeyemi   ruth@aurora.example   Director       active\\n\"\n        \"  4    Lee Park       lee@aurora.example    Mission Lead   active\\n\"\n        \"  8    Chen Wu        chen@aurora.example   Crew Member    deactivated\\n\"\n    )\n\n\ndef test_ac25_lead_cannot_manage_users(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/users\", error(403, \"role_forbidden\", \"Leads can't manage users\"))\n\n    result = mc(\"users\", \"deactivate\", \"chen@aurora.example\")\n\n    assert result.exit_code == 1\n    assert result.stderr == \"✗ Leads can't manage users.\\n\"\n\n\ndef test_p1_skills_add_rename_remove(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"POST\", \"/skills\", ok({\"id\": 11, \"name\": \"Robotics\", \"category\": None}, status=201))\n    api.on(\"PATCH\", \"/skills/5\", ok({\"id\": 5, \"name\": \"Planetary Geology\", \"category\": None}))\n    api.on(\"DELETE\", \"/skills/4\", ok(status=204))\n\n    added = mc(\"skills\", \"add\", \"Robotics\")\n    renamed = mc(\"skills\", \"rename\", \"geology\", \"Planetary Geology\")\n    removed = mc(\"skills\", \"remove\", \"EVA\")\n\n    assert added.stdout == \"✓ Added skill Robotics.\\n\"\n    assert api.sent(\"POST\", \"/skills\")[0].body == {\"name\": \"Robotics\"}\n    assert renamed.stdout == \"✓ Renamed Geology to Planetary Geology.\\n\"\n    assert api.sent(\"PATCH\", \"/skills/5\")[0].body == {\"name\": \"Planetary Geology\"}\n    assert removed.stdout == \"✓ Removed skill EVA.\\n\"\n\n\ndef test_p1_used_skill_cannot_be_removed(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"DELETE\", \"/skills/4\", error(409, \"skill_in_use\", \"EVA is still in use\"))\n\n    result = mc(\"skills\", \"remove\", \"EVA\")\n\n    assert result.exit_code == 1\n    assert result.stderr.startswith(\"✗ EVA is still in use.\\n\")\n\n\ndef test_m16_skills_list(mc, api):\n    mc.login_as()\n    api.on(\"GET\", \"/skills\", ok(SKILLS[:2]))\n\n    result = mc(\"skills\", \"list\")\n\n    assert result.stdout == \"Piloting\\nLeadership\\n\"\n\n\ndef test_a1_org_show_and_set_approvals(mc, api):\n    mc.login_as(\"tok-ruth\", \"ruth@aurora.example\")\n    org = {\"id\": 1, \"name\": \"Aurora Space Agency\", \"slug\": \"aurora\", \"required_approvals\": 2}\n    api.on(\"GET\", \"/org\", ok(org))\n    api.on(\"PATCH\", \"/org\", ok(org | {\"required_approvals\": 3}))\n\n    shown = mc(\"org\", \"show\")\n    changed = mc(\"org\", \"set-approvals\", \"3\")\n\n    assert shown.stdout == \"Organisation         Aurora Space Agency\\nApprovals required   2\\n\"\n    assert api.sent(\"PATCH\", \"/org\")[0].body == {\"required_approvals\": 3}\n    assert changed.stdout == (\n        \"✓ Missions now need 3 approvals. Missions already pending keep the number they were \"\n        \"submitted with.\\n\"\n    )\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_people.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_scenarios.py",
  "content": "\"\"\"M16: the PRD scenarios S1 (golden path) and S4 (overlaps) driven through `mc`, one user after\nanother, against a small stateful stand-in for the API (PRD §9.3, AC-1, AC-3, AC-8, AC-14, AC-15).\n\nThe stand-in only keeps the state these flows touch, and answers with the design's response and\nerror shapes. Business rules are the server's; here they're scripted to the PRD's expected\noutcomes, so the tests check what the CLI sends and how it reports each step.\n\"\"\"\n\nimport json\nfrom dataclasses import dataclass, field\n\nimport httpx2\n\nfrom cli_fakes import CREW, SKILLS, USERS, FakeApi, error, gateway, ok, problem\n\nPEOPLE = {\n    \"ruth@aurora.example\": (1, \"Ruth Adeyemi\", \"director\", None),\n    \"marco@aurora.example\": (2, \"Marco Bianchi\", \"director\", 2),\n    \"ingrid@aurora.example\": (3, \"Ingrid Holm\", \"director\", None),\n    \"lee@aurora.example\": (4, \"Lee Park\", \"lead\", None),\n    \"nora@aurora.example\": (5, \"Nora Quinn\", \"lead\", None),\n    \"ana@aurora.example\": (6, \"Ana Okafor\", \"lead\", 6),\n    \"chen@aurora.example\": (8, \"Chen Wu\", \"crew\", 8),\n    \"dana@aurora.example\": (9, \"Dana Reyes\", \"crew\", 9),\n}\nSLOT_NAMES = {1: \"Flight Engineer\", 2: \"Mission Specialist\", 3: \"Commander\"}\n\n\n@dataclass\nclass Server:\n    \"\"\"Just enough of the API for S1 and S4.\"\"\"\n\n    api: FakeApi\n    tokens: dict[str, str] = field(default_factory=dict)\n    status: str = \"draft\"\n    assignments: dict[int, dict] = field(default_factory=dict)\n    approvals: list[dict] = field(default_factory=list)\n    history: list[dict] = field(default_factory=list)\n    accepted_reboost: set[int] = field(default_factory=set)\n\n    def __post_init__(self) -> None:\n        on = self.api.on\n        on(\"POST\", \"/auth/login\", self.login)\n        on(\"GET\", \"/me\", self.authed(self.me))\n        on(\"GET\", \"/skills\", self.authed(lambda r, u: ok(SKILLS)))\n        on(\"GET\", \"/crew\", self.authed(lambda r, u: ok(CREW)))\n        on(\"GET\", \"/users\", self.authed(lambda r, u: ok(USERS)))\n        on(\"GET\", \"/missions/1\", self.authed(lambda r, u: ok(self.mission())))\n        on(\"GET\", \"/missions/1/match\", self.authed(self.match))\n        on(\"POST\", \"/missions/1/match/apply\", self.authed(self.apply))\n        on(\"GET\", \"/assignments\", self.authed(self.mine))\n        for aid in (21, 22, 23):\n            on(\"POST\", f\"/assignments/{aid}/accept\", self.authed(self.accept(aid)))\n        on(\"POST\", \"/missions/1/submit\", self.authed(self.submit))\n        on(\"POST\", \"/missions/1/approve\", self.authed(self.approve))\n        on(\"POST\", \"/missions/1/complete\", self.authed(self.complete))\n        on(\"GET\", \"/missions/1/history\", self.authed(lambda r, u: ok(self.history)))\n\n    # plumbing\n\n    def authed(self, handler):\n        def wrapped(request: httpx2.Request) -> httpx2.Response:\n            auth = request.headers.get(\"authorization\", \"\")\n            email = self.tokens.get(auth.removeprefix(\"Bearer \"))\n            if email is None:\n                return error(401, \"unauthenticated\", \"Your session has ended\")\n            return handler(request, PEOPLE[email])\n\n        return wrapped\n\n    def login(self, request: httpx2.Request) -> httpx2.Response:\n        body = json.loads(request.content)\n        if body[\"email\"] not in PEOPLE or body[\"password\"] != \"orbital launch window\":\n            return error(401, \"invalid_credentials\", \"Email or password is incorrect\")\n        token = f\"tok-{body['email'].split('@')[0]}\"\n        self.tokens[token] = body[\"email\"]\n        return ok({\"token\": token, \"expires_at\": \"2099-01-01T00:00:00Z\"})\n\n    def me(self, request, user) -> httpx2.Response:\n        uid, name, role, cpid = user\n        email = next(e for e, p in PEOPLE.items() if p == user)\n        return ok({\"id\": uid, \"email\": email, \"name\": name, \"role\": role, \"is_active\": True,\n                   \"crew_profile_id\": cpid,\n                   \"organisation\": {\"id\": 1, \"name\": \"Aurora Space Agency\"}})  # fmt: skip\n\n    def log(self, user, event, from_status=None, to_status=None) -> None:\n        self.history.append(\n            {\"id\": len(self.history) + 1, \"created_at\": f\"2027-01-05T09:{len(self.history):02d}:00Z\",\n             \"actor_id\": user[0], \"actor_name\": user[1], \"event\": event,\n             \"from_status\": from_status, \"to_status\": to_status, \"reason\": None, \"data\": {}}\n        )  # fmt: skip\n\n    def mission(self) -> dict:\n        open_places = {\n            slot: 1 - sum(1 for a in self.assignments.values()\n                          if a[\"slot_id\"] == slot and a[\"status\"] in (\"proposed\", \"accepted\"))\n            for slot in SLOT_NAMES\n        }  # fmt: skip\n        m = gateway(self.status, list(self.assignments.values()), self.approvals, open_places)\n        m[\"approvals_required\"] = None if self.status == \"draft\" else 2\n        return m\n\n    # endpoints\n\n    def match(self, request, user) -> httpx2.Response:\n        from cli_fakes import S2_PREVIEW\n\n        return ok(S2_PREVIEW | {\"can_apply\": user[0] == 4})\n\n    def apply(self, request, user) -> httpx2.Response:\n        for aid, slot, cpid, name in ((21, 3, 6, \"Ana Okafor\"), (22, 1, 8, \"Chen Wu\"),\n                                      (23, 2, 9, \"Dana Reyes\")):  # fmt: skip\n            self.assignments[aid] = {\"id\": aid, \"slot_id\": slot, \"slot_name\": SLOT_NAMES[slot],\n                                     \"crew_profile_id\": cpid, \"crew_name\": name,\n                                     \"status\": \"proposed\", \"reason\": None}  # fmt: skip\n            self.log(user, \"assignment.proposed\")\n        return ok(\n            [{k: a[k] for k in (\"id\", \"slot_id\", \"crew_profile_id\", \"status\")}\n             for a in self.assignments.values()],\n            status=201,\n        )  # fmt: skip\n\n    def mine(self, request, user) -> httpx2.Response:\n        rows = [\n            {\"assignment_id\": a[\"id\"], \"mission_id\": 1, \"mission_name\": \"Lunar Gateway Resupply\",\n             \"start_date\": \"2027-03-01\", \"end_date\": \"2027-03-10\", \"mission_status\": self.status,\n             \"slot_name\": a[\"slot_name\"], \"status\": a[\"status\"], \"reason\": None}\n            for a in self.assignments.values() if a[\"crew_profile_id\"] == user[3]\n        ]  # fmt: skip\n        if request.url.params.get(\"pending\") == \"true\":\n            rows = [r for r in rows if r[\"status\"] == \"proposed\"]\n        return ok(rows)\n\n    def accept(self, aid):\n        def handler(request, user) -> httpx2.Response:\n            a = self.assignments.get(aid)\n            if a is None or a[\"crew_profile_id\"] != user[3]:\n                return error(404, \"not_found\", \"Assignment not found\")\n            a[\"status\"] = \"accepted\"\n            self.log(user, \"assignment.accepted\", \"proposed\", \"accepted\")\n            return ok({\"id\": aid, \"mission_id\": 1, \"slot_id\": a[\"slot_id\"],\n                       \"crew_profile_id\": a[\"crew_profile_id\"], \"status\": \"accepted\",\n                       \"reason\": None})  # fmt: skip\n\n        return handler\n\n    def submit(self, request, user) -> httpx2.Response:\n        waiting = [a for a in self.assignments.values() if a[\"status\"] != \"accepted\"]\n        if waiting:\n            return error(409, \"rule_violation\", \"Mission can't be submitted\", [\n                problem(\"proposal_unanswered\",\n                        f\"{a['slot_name']}: {a['crew_name']} hasn't responded to the proposal\",\n                        assignment_id=a[\"id\"]) for a in waiting\n            ])  # fmt: skip\n        self.status = \"pending_approval\"\n        self.log(user, \"mission.submitted\", \"draft\", \"pending_approval\")\n        return ok(self.mission())\n\n    def approve(self, request, user) -> httpx2.Response:\n        if user[0] == 1:\n            return error(403, \"approver_is_creator\", \"You can't approve a mission you created\")\n        self.approvals.append({\"director_id\": user[0], \"director_name\": user[1],\n                               \"decision\": \"approve\", \"reason\": None})  # fmt: skip\n        self.log(user, \"mission.approved\")\n        if len(self.approvals) == 2:\n            self.status = \"active\"\n            self.log(user, \"mission.activated\", \"pending_approval\", \"active\")\n        return ok(self.mission())\n\n    def complete(self, request, user) -> httpx2.Response:\n        self.status = \"completed\"\n        for a in self.assignments.values():\n            a[\"status\"] = \"completed\"\n        self.log(user, \"mission.completed\", \"active\", \"completed\")\n        return ok(self.mission())\n\n\ndef _login(mc, email):\n    result = mc(\"login\", \"--email\", email, input=\"orbital launch window\\n\")\n    assert result.exit_code == 0, result.stderr\n    return result\n\n\ndef test_s1_golden_path_through_the_cli(mc, api):\n    server = Server(api)\n\n    _login(mc, \"lee@aurora.example\")\n    preview = mc(\"missions\", \"match\", \"1\")\n    assert preview.exit_code == 0\n    assert \"Commander            Ana\" in preview.stdout\n    applied = mc(\"missions\", \"match\", \"1\", \"--apply\")\n    assert applied.exit_code == 0, applied.stderr\n    assert \"Proposed 3 crew for Lunar Gateway Resupply\" in applied.stdout\n\n    early = mc(\"missions\", \"submit\", \"1\")\n    assert early.exit_code == 1  # AC-2: proposals still unanswered\n    assert \"  • Commander: Ana Okafor hasn't responded to the proposal\\n\" in early.stderr\n\n    for email, aid in ((\"ana\", 21), (\"chen\", 22), (\"dana\", 23)):\n        _login(mc, f\"{email}@aurora.example\")\n        pending = mc(\"assignments\", \"list\", \"--pending\", \"--json\")\n        assert [row[\"assignment_id\"] for row in json.loads(pending.stdout)] == [aid]\n        accepted = mc(\"assignments\", \"accept\", str(aid))\n        assert accepted.exit_code == 0, accepted.stderr\n        assert accepted.stdout.startswith(\"✓ Accepted \")\n\n    _login(mc, \"lee@aurora.example\")\n    submitted = mc(\"missions\", \"submit\", \"1\")\n    assert submitted.stdout == (\n        \"✓ Submitted Lunar Gateway Resupply for approval. It needs 2 approvals.\\n\"\n    )\n\n    _login(mc, \"ruth@aurora.example\")\n    ruth = mc(\"missions\", \"approve\", \"1\")\n    assert ruth.exit_code == 1  # AC-8: the creator can't approve\n    assert ruth.stderr == \"✗ You can't approve a mission you created.\\n\"\n\n    _login(mc, \"marco@aurora.example\")\n    marco = mc(\"missions\", \"approve\", \"1\")\n    assert marco.stdout == (\n        \"✓ Approved Lunar Gateway Resupply. It's pending approval (1 of 2 approvals).\\n\"\n    )\n\n    _login(mc, \"ingrid@aurora.example\")\n    ingrid = mc(\"missions\", \"approve\", \"1\")\n    assert ingrid.stdout == \"✓ Approved Lunar Gateway Resupply. It's now active.\\n\"\n\n    _login(mc, \"lee@aurora.example\")\n    completed = mc(\"missions\", \"complete\", \"1\")\n    assert completed.exit_code == 0\n\n    shown = json.loads(mc(\"missions\", \"show\", \"1\", \"--json\").stdout)\n    assert shown[\"status\"] == \"completed\"\n    assert {a[\"status\"] for a in shown[\"assignments\"]} == {\"completed\"}\n\n    history = mc(\"missions\", \"history\", \"1\")  # AC-1: every transition, who and when\n    for line in (\"Lee Park       Submitted for approval\", \"Marco Bianchi  Approved\",\n                 \"Ingrid Holm    Mission became active\", \"Lee Park       Completed\"):  # fmt: skip\n        who, what = line.split(maxsplit=2)[:2], line.split(\"  \")[-1].strip()\n        assert \" \".join(who) in history.stdout and what in history.stdout\n    assert server.status == \"completed\"\n\n\ndef test_s4_overlaps_and_unavailability_through_the_cli(mc, api):\n    tokens = {\"tok-lee\": \"lee\", \"tok-nora\": \"nora\", \"tok-chen\": \"chen\"}\n    proposals: list[tuple[str, dict]] = []\n\n    def who(request):\n        return tokens[request.headers[\"authorization\"].removeprefix(\"Bearer \")]\n\n    reboost = gateway() | {\"id\": 3, \"name\": \"Station Reboost\", \"start_date\": \"2027-02-25\",\n                           \"end_date\": \"2027-03-02\", \"owner_id\": 5, \"owner_name\": \"Nora Quinn\"}\n    reboost[\"slots\"] = [{\"id\": 6, \"position\": 1, \"name\": \"Engineer\", \"headcount\": 2,\n                         \"open_places\": 1, \"requirements\": []}]  # fmt: skip\n    api.on(\"GET\", \"/skills\", ok(SKILLS))\n    api.on(\"GET\", \"/crew\", ok(CREW))\n    api.on(\"GET\", \"/missions/1\", ok(gateway()))\n    api.on(\"GET\", \"/missions/3\", ok(reboost))\n\n    def propose_gateway(request):\n        body = json.loads(request.content)\n        if body[\"crew_profile_id\"] == 12:\n            return error(409, \"rule_violation\", \"Can't propose Gus Patel for Flight Engineer\", [\n                problem(\"overlap\", \"Gus Patel has an accepted assignment on Station Reboost \"\n                        \"overlapping 1–2 Mar\", crew_profile_id=12, mission_id=3,\n                        mission_name=\"Station Reboost\")])  # fmt: skip\n        if body[\"crew_profile_id\"] == 11:\n            return error(409, \"rule_violation\", \"Can't propose Fay Moreau for Commander\", [\n                problem(\"unavailable\", \"Fay Moreau is unavailable 5–8 Mar\",\n                        crew_profile_id=11, slot_id=3)])  # fmt: skip\n        proposals.append((who(request), body))\n        return ok({\"id\": 25, \"mission_id\": 1, \"slot_id\": 1, \"crew_profile_id\": 8,\n                   \"status\": \"proposed\", \"reason\": None}, status=201)  # fmt: skip\n\n    def propose_reboost(request):\n        proposals.append((who(request), json.loads(request.content)))\n        return ok({\"id\": 24, \"mission_id\": 3, \"slot_id\": 6, \"crew_profile_id\": 8,\n                   \"status\": \"proposed\", \"reason\": None}, status=201)  # fmt: skip\n\n    api.on(\"POST\", \"/missions/1/assignments\", propose_gateway)\n    api.on(\"POST\", \"/missions/3/assignments\", propose_reboost)\n    api.on(\"GET\", \"/assignments\", ok([]))\n    api.on(\"POST\", \"/assignments/24/accept\", ok({\"id\": 24, \"status\": \"accepted\"}))\n    api.on(\n        \"POST\",\n        \"/assignments/25/accept\",\n        error(409, \"overlap\", \"You have an accepted assignment on Station Reboost overlapping \"\n              \"1–2 Mar\"),\n    )  # fmt: skip\n\n    mc.login_as(\"tok-lee\")\n    gus = mc(\"missions\", \"propose\", \"1\", \"--slot\", \"Flight Engineer\", \"--crew\", \"gus@aurora.example\")\n    fay = mc(\"missions\", \"propose\", \"1\", \"--slot\", \"Commander\", \"--crew\", \"fay@aurora.example\")\n\n    assert gus.exit_code == fay.exit_code == 1  # AC-14\n    assert gus.stderr == (\n        \"✗ Can't propose Gus Patel for Flight Engineer.\\n\"\n        \"  • Gus Patel has an accepted assignment on Station Reboost overlapping 1–2 Mar\\n\"\n        \"  See who is free: mc missions match 1\\n\"\n    )\n    assert \"  • Fay Moreau is unavailable 5–8 Mar\\n\" in fay.stderr\n\n    mc.login_as(\"tok-nora\", \"nora@aurora.example\")\n    assert mc(\"missions\", \"propose\", \"3\", \"--slot\", \"Engineer\", \"--crew\",\n              \"chen@aurora.example\").exit_code == 0  # fmt: skip\n    mc.login_as(\"tok-lee\")\n    assert mc(\"missions\", \"propose\", \"1\", \"--slot\", \"1\", \"--crew\",\n              \"chen@aurora.example\").exit_code == 0  # fmt: skip\n    assert proposals == [\n        (\"nora\", {\"slot_id\": 6, \"crew_profile_id\": 8}),\n        (\"lee\", {\"slot_id\": 1, \"crew_profile_id\": 8}),\n    ]\n\n    mc.login_as(\"tok-chen\", \"chen@aurora.example\")\n    first = mc(\"assignments\", \"accept\", \"24\")\n    second = mc(\"assignments\", \"accept\", \"25\")\n\n    assert first.exit_code == 0\n    assert second.exit_code == 1  # AC-15: names the conflicting mission\n    assert second.stderr.startswith(\n        \"✗ You have an accepted assignment on Station Reboost overlapping 1–2 Mar.\\n\"\n    )\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli/test_cli_scenarios.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='tests/cli/test_cli_scenarios.py'
s=open(p).read()
old=s[s.index('    history = mc("missions", "history", "1")'):s.index('    assert server.status == "completed"')]
new='''    history = mc("missions", "history", "1").stdout.splitlines()  # AC-1: who did what, when
    for who, what in (
        ("Lee Park", "Submitted for approval"),
        ("Marco Bianchi", "Approved"),
        ("Ingrid Holm", "Mission became active"),
        ("Lee Park", "Completed"),
    ):
        assert any(who in line and what in line and "Jan 2027" in line for line in history)
'''
s=s.replace(old,new)
open(p,'w').write(s)
EOF
uv run pytest tests/cli -q 2>&1 | tail -5
```

<details>
<summary>↳ Result</summary>

```
tests/cli/conftest.py:3: in <module>
    from cli_fakes import FakeApi, Mc
tests/cli/cli_fakes.py:17: in <module>
    from mission_control.cli.config import CredentialStore, Credentials
E   ModuleNotFoundError: No module named 'mission_control.cli'
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

### 🤖 Claude · 2026-10-12 03:30:05 UTC

Tests are red (no `cli` package yet). Now the implementation, starting with config and the HTTP client.

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/config.py",
  "content": "\"\"\"Where the CLI finds the server, and where it keeps the session from `mc login`: a small JSON\nfile that only the user can read.\"\"\"\n\nimport json\nimport os\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\n\nDEFAULT_API_URL = \"http://127.0.0.1:8000\"\n_CREDENTIALS_FILE = \"credentials.json\"\n\n\ndef default_config_dir() -> Path:\n    return Path.home() / \".config\" / \"mission-control\"\n\n\ndef api_url() -> str:\n    \"\"\"The server's base URL. `MC_API_URL` overrides the local default.\"\"\"\n    return (os.environ.get(\"MC_API_URL\") or \"\").strip().rstrip(\"/\") or DEFAULT_API_URL\n\n\n@dataclass(frozen=True)\nclass Credentials:\n    token: str\n    email: str\n    expires_at: str | None = None\n\n\nclass CredentialStore:\n    \"\"\"The session token on disk. The file is written with mode 0600 inside a 0700 directory,\n    and replaced atomically so a crash never leaves half a file.\"\"\"\n\n    def __init__(self, directory: Path) -> None:\n        self.directory = directory\n\n    @property\n    def path(self) -> Path:\n        return self.directory / _CREDENTIALS_FILE\n\n    def load(self) -> Credentials | None:\n        \"\"\"The saved session, or None when there isn't a usable one.\"\"\"\n        try:\n            data = json.loads(self.path.read_text(encoding=\"utf-8\"))\n        except (OSError, ValueError):\n            return None\n        if not isinstance(data, dict):\n            return None\n        token = data.get(\"token\")\n        if not isinstance(token, str) or not token:\n            return None\n        expires_at = data.get(\"expires_at\")\n        return Credentials(\n            token=token,\n            email=str(data.get(\"email\") or \"\"),\n            expires_at=expires_at if isinstance(expires_at, str) else None,\n        )\n\n    def save(self, credentials: Credentials) -> None:\n        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)\n        os.chmod(self.directory, 0o700)\n        temporary = self.path.with_name(self.path.name + \".tmp\")\n        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)\n        try:\n            os.fchmod(fd, 0o600)  # the mode given to open() is ignored if the file existed\n            with os.fdopen(fd, \"w\", encoding=\"utf-8\") as file:\n                json.dump(asdict(credentials), file)\n        except BaseException:\n            temporary.unlink(missing_ok=True)\n            raise\n        os.replace(temporary, self.path)\n\n    def clear(self) -> None:\n        self.path.unlink(missing_ok=True)\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/config.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
mkdir -p /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat > __init__.py <<'EOF'
"""`mc`, the Mission Control command-line client. It reaches the system only through the HTTP
API."""
EOF
cat > commands/__init__.py <<'EOF'
"""One module per command group."""
EOF
cat > errors.py <<'EOF'
"""Failures the CLI reports itself, before or instead of asking the server, and the exit codes
every command uses."""

from collections.abc import Sequence

OK = 0
REFUSED = 1
USAGE = 2
AUTHENTICATION = 3
UNAVAILABLE = 4
INTERRUPTED = 130


class CliError(Exception):
    """Something to tell the user, with an optional next step, and the exit code to use."""

    exit_code = REFUSED

    def __init__(self, message: str, *, hint: str | None = None, bullets: Sequence[str] = ()):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.bullets = tuple(bullets)


class Refused(CliError):
    """A reference that doesn't match anything, e.g. an email nobody has."""


class Declined(CliError):
    """The user answered no to a confirmation."""

    def __init__(self) -> None:
        super().__init__("Nothing was changed.")


class UsageProblem(CliError):
    """Input the CLI can't use, found before anything was sent."""

    exit_code = USAGE


class NotLoggedIn(CliError):
    exit_code = AUTHENTICATION

    def __init__(self) -> None:
        super().__init__("You're not logged in.", hint="Log in: mc login")
EOF
```

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/client.py",
  "content": "\"\"\"The CLI's only way into Mission Control: JSON requests to the HTTP API through an `httpx2`\nclient. Tests pass in a client with a mock transport, or the API's own test client, so no server\nis needed.\"\"\"\n\nfrom collections.abc import Callable, Mapping\nfrom dataclasses import dataclass, field\nfrom typing import Any\n\nimport httpx2\n\nfrom mission_control.cli.errors import AUTHENTICATION, REFUSED, UNAVAILABLE\n\nAPI_PREFIX = \"/api/v1\"\nTIMEOUT = httpx2.Timeout(15.0, connect=5.0)  # the server may wait up to 5 s for a busy database\n\n\n@dataclass(frozen=True)\nclass Problem:\n    code: str\n    message: str\n    refs: Mapping[str, Any] = field(default_factory=dict)\n\n\nclass ApiError(Exception):\n    \"\"\"The server refused the request. Carries its error body: a code, a message and every\n    problem. Commands may attach a `subject` (e.g. \"Mission 5\") and hints for known codes, which\n    are used when the refusal is shown.\"\"\"\n\n    def __init__(\n        self,\n        status: int,\n        code: str,\n        message: str,\n        problems: tuple[Problem, ...] = (),\n        body: Mapping[str, Any] | None = None,\n    ) -> None:\n        super().__init__(message)\n        self.status = status\n        self.code = code\n        self.message = message\n        self.problems = problems\n        self.body: Mapping[str, Any] = body or {}\n        self.subject: str | None = None\n        self.hints: dict[str, str] = {}\n\n    @property\n    def exit_code(self) -> int:\n        if self.status == 401:\n            return AUTHENTICATION\n        if self.status == 503:\n            return UNAVAILABLE\n        return REFUSED\n\n    @property\n    def has_error_body(self) -> bool:\n        return isinstance(self.body.get(\"error\"), Mapping)\n\n\nclass Unreachable(Exception):\n    def __init__(self, url: str) -> None:\n        super().__init__(url)\n        self.url = url\n\n\nclass Api:\n    \"\"\"Sends requests with the session token and turns error responses into `ApiError`.\n\n    A 401 on a request that carried a token means the session is over, so\n    `on_session_ended` runs (the CLI clears the saved token) before the error is raised.\"\"\"\n\n    def __init__(\n        self,\n        http: httpx2.Client,\n        token: str | None = None,\n        on_session_ended: Callable[[], None] | None = None,\n    ) -> None:\n        self._http = http\n        self._token = token\n        self._on_session_ended = on_session_ended\n\n    def get(self, path: str, params: Mapping[str, str] | None = None) -> Any:\n        return self._send(\"GET\", path, params=params)\n\n    def post(self, path: str, body: Any = None) -> Any:\n        return self._send(\"POST\", path, body=body)\n\n    def put(self, path: str, body: Any = None) -> Any:\n        return self._send(\"PUT\", path, body=body)\n\n    def patch(self, path: str, body: Any = None) -> Any:\n        return self._send(\"PATCH\", path, body=body)\n\n    def delete(self, path: str) -> Any:\n        return self._send(\"DELETE\", path)\n\n    def _send(\n        self,\n        method: str,\n        path: str,\n        *,\n        body: Any = None,\n        params: Mapping[str, str] | None = None,\n    ) -> Any:\n        headers = {\"Accept\": \"application/json\"}\n        if self._token:\n            headers[\"Authorization\"] = f\"Bearer {self._token}\"\n        try:\n            response = self._http.request(\n                method,\n                API_PREFIX + path,\n                json=body,\n                params=dict(params) if params else None,\n                headers=headers,\n            )\n        except httpx2.TransportError as exc:\n            raise Unreachable(str(self._http.base_url).rstrip(\"/\")) from exc\n\n        if response.is_success:\n            if response.status_code == 204 or not response.content:\n                return None\n            try:\n                return response.json()\n            except ValueError:\n                raise _unexpected(response) from None\n\n        failure = _error(response)\n        if response.status_code == 401 and self._token and self._on_session_ended:\n            self._on_session_ended()\n        raise failure\n\n\ndef _error(response: httpx2.Response) -> ApiError:\n    try:\n        body = response.json()\n    except ValueError:\n        return _unexpected(response)\n    error = body.get(\"error\") if isinstance(body, dict) else None\n    if not (\n        isinstance(error, dict)\n        and isinstance(error.get(\"code\"), str)\n        and isinstance(error.get(\"message\"), str)\n    ):\n        return _unexpected(response)\n    problems = tuple(\n        Problem(str(p.get(\"code\", \"\")), str(p.get(\"message\", \"\")), p.get(\"refs\") or {})\n        for p in error.get(\"problems\") or ()\n        if isinstance(p, dict)\n    )\n    return ApiError(response.status_code, error[\"code\"], error[\"message\"], problems, body)\n\n\ndef _unexpected(response: httpx2.Response) -> ApiError:\n    return ApiError(\n        response.status_code,\n        \"unexpected_response\",\n        f\"The server sent an unexpected response (HTTP {response.status_code})\",\n    )\n"
}
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/client.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/render.py",
  "content": "\"\"\"Everything the CLI prints. Data goes to stdout, messages and next steps to stderr. Colour only\nmarks a symbol, never carries meaning alone, and appears only on a terminal. With `NO_COLOR`,\n`TERM=dumb` or a non-UTF-8 terminal the symbols become plain words.\"\"\"\n\nimport json\nimport os\nfrom collections.abc import Iterable, Mapping, Sequence\nfrom dataclasses import dataclass\nfrom datetime import UTC, date, datetime\nfrom typing import Any, TextIO\n\nfrom rich.cells import cell_len\n\n_GAP = \"   \"\n_INDENT = \"  \"\n\n_GREEN, _YELLOW, _RED, _RESET = \"\\x1b[32m\", \"\\x1b[33m\", \"\\x1b[31m\", \"\\x1b[0m\"\n\nMISSION_STATUS = {\n    \"draft\": \"Draft\",\n    \"pending_approval\": \"Pending approval\",\n    \"active\": \"Active\",\n    \"completed\": \"Completed\",\n    \"cancelled\": \"Cancelled\",\n}\nROLE = {\"director\": \"Director\", \"lead\": \"Mission Lead\", \"crew\": \"Crew Member\"}\n\n\n@dataclass(frozen=True)\nclass Style:\n    color: bool\n    unicode: bool\n\n\ndef detect_style(stream: TextIO, environ: Mapping[str, str]) -> Style:\n    \"\"\"Colour needs a terminal, no `NO_COLOR` and a `TERM` that isn't dumb. Symbols need UTF-8\n    and the same opt-outs.\"\"\"\n    term = environ.get(\"TERM\", \"\")\n    opted_out = \"NO_COLOR\" in environ or term == \"dumb\"\n    is_tty = _isatty(stream)\n    encoding = (getattr(stream, \"encoding\", None) or \"\").lower().replace(\"-\", \"\")\n    return Style(\n        color=is_tty and not opted_out and bool(term),\n        unicode=encoding == \"utf8\" and not opted_out,\n    )\n\n\ndef _isatty(stream: TextIO) -> bool:\n    try:\n        return stream.isatty()\n    except (AttributeError, ValueError):\n        return False\n\n\n# Dates\n\n\ndef parse_date(value: str) -> date:\n    return date.fromisoformat(value)\n\n\ndef format_range(start: date, end: date, *, plain: bool = False) -> str:\n    \"\"\"`1–10 Mar 2027`, `25 Feb – 2 Mar 2027`, `30 Dec 2026 – 2 Jan 2027`, or one day.\"\"\"\n    dash = \"-\" if plain else \"–\"\n    if start == end:\n        return _day(end, year=True)\n    if (start.year, start.month) == (end.year, end.month):\n        return f\"{start.day}{dash}{_day(end, year=True)}\"\n    left = _day(start, year=start.year != end.year)\n    return f\"{left} {dash} {_day(end, year=True)}\"\n\n\ndef _day(d: date, *, year: bool) -> str:\n    text = f\"{d.day} {d.strftime('%b')}\"\n    return f\"{text} {d.year}\" if year else text\n\n\ndef format_timestamp(value: str) -> str:\n    \"\"\"A UTC timestamp from the server as `5 Jan 2027 09:03`.\"\"\"\n    moment = datetime.fromisoformat(value.replace(\"Z\", \"+00:00\")).astimezone(UTC)\n    return f\"{moment.day} {moment.strftime('%b %Y %H:%M')}\"\n\n\n# Tables\n\n\n@dataclass(frozen=True)\nclass Span:\n    \"\"\"A row whose first cell lines up with the column and whose text runs across the rest.\"\"\"\n\n    first: str\n    rest: str\n\n\ndef table_lines(\n    headers: Sequence[str], rows: Iterable[Sequence[str] | Span], indent: str = _INDENT\n) -> list[str]:\n    \"\"\"Columns padded by display width, three spaces apart, with no trailing spaces.\"\"\"\n    rows = list(rows)\n    widths = [cell_len(h) for h in headers]\n    for row in rows:\n        cells = [row.first] if isinstance(row, Span) else row\n        for i, cell in enumerate(cells):\n            widths[i] = max(widths[i], cell_len(cell))\n\n    def line(cells: Sequence[str]) -> str:\n        padded = [c + \" \" * (widths[i] - cell_len(c)) for i, c in enumerate(cells)]\n        return (indent + _GAP.join(padded)).rstrip()\n\n    lines = [line(headers)]\n    for row in rows:\n        if isinstance(row, Span):\n            lines.append(line([row.first]) + \" \" * (widths[0] - cell_len(row.first)) + _GAP + row.rest)\n            lines[-1] = lines[-1].rstrip()\n        else:\n            lines.append(line(row))\n    return lines\n\n\ndef field_lines(pairs: Sequence[tuple[str, str]]) -> list[str]:\n    width = max(cell_len(k) for k, _ in pairs)\n    return [f\"{k}{' ' * (width - cell_len(k))}{_GAP}{v}\".rstrip() for k, v in pairs]\n\n\n# Words\n\n\ndef join_names(names: Sequence[str]) -> str:\n    \"\"\"`Ana`, `Ana and Chen`, `Ana, Chen and Dana`.\"\"\"\n    if len(names) <= 1:\n        return \"\".join(names)\n    return f\"{', '.join(names[:-1])} and {names[-1]}\"\n\n\ndef plural(count: int, word: str, many: str | None = None) -> str:\n    return f\"{count} {word if count == 1 else many or word + 's'}\"\n\n\ndef sentence(text: str) -> str:\n    \"\"\"End a server message with a full stop unless it already has one.\"\"\"\n    text = text.strip()\n    return text if not text or text[-1] in \".!?\" else text + \".\"\n\n\nclass Terminal:\n    \"\"\"Writes data to stdout and messages to stderr, each styled for its own stream.\"\"\"\n\n    def __init__(self, out: TextIO, err: TextIO, out_style: Style, err_style: Style) -> None:\n        self.out = out\n        self.err = err\n        self.out_style = out_style\n        self.err_style = err_style\n\n    @classmethod\n    def for_streams(cls, out: TextIO, err: TextIO, color: bool | None = None) -> \"Terminal\":\n        out_style, err_style = detect_style(out, os.environ), detect_style(err, os.environ)\n        if color is not None:\n            out_style = Style(color, out_style.unicode)\n            err_style = Style(color, err_style.unicode)\n        return cls(out, err, out_style, err_style)\n\n    # Plain-text forms of the separators\n\n    @property\n    def sep(self) -> str:\n        return \" · \" if self.out_style.unicode else \" - \"\n\n    def dates(self, start: str, end: str) -> str:\n        return format_range(parse_date(start), parse_date(end), plain=not self.out_style.unicode)\n\n    def heading(self, *parts: str) -> str:\n        return self.sep.join(p for p in parts if p)\n\n    # stdout\n\n    def line(self, text: str = \"\") -> None:\n        self.out.write(text + \"\\n\")\n\n    def lines(self, lines: Iterable[str]) -> None:\n        for text in lines:\n            self.line(text)\n\n    def table(self, headers: Sequence[str], rows: Iterable[Sequence[str] | Span]) -> None:\n        self.lines(table_lines(headers, rows))\n\n    def fields(self, pairs: Sequence[tuple[str, str]]) -> None:\n        self.lines(field_lines(pairs))\n\n    def json(self, data: Any) -> None:\n        self.line(json.dumps(data, indent=2, ensure_ascii=False))\n\n    def ok(self, message: str) -> None:\n        self.line(self._marker(\"✓\", \"OK:\", _GREEN, self.out_style) + \" \" + message)\n\n    def note(self, message: str) -> None:\n        self.line(self._marker(\"!\", \"Note:\", _YELLOW, self.out_style) + \" \" + message)\n\n    # stderr\n\n    def say(self, text: str = \"\") -> None:\n        self.err.write(text + \"\\n\")\n\n    def warn(self, message: str) -> None:\n        self.say(self._marker(\"!\", \"Note:\", _YELLOW, self.err_style) + \" \" + message)\n\n    def error(\n        self, message: str, bullets: Sequence[str] = (), hint: str | Sequence[str] | None = None\n    ) -> None:\n        self.say(self._marker(\"✗\", \"Error:\", _RED, self.err_style) + \" \" + message)\n        bullet = \"•\" if self.err_style.unicode else \"-\"\n        for text in bullets:\n            self.say(f\"{_INDENT}{bullet} {text}\")\n        hints = [hint] if isinstance(hint, str) else list(hint or ())\n        for text in hints:\n            self.say(_INDENT + text)\n\n    def next_steps(self, steps: Sequence[str]) -> None:\n        for i, step in enumerate(steps):\n            self.say((\"Next: \" if i == 0 else \"      \") + step)\n\n    @staticmethod\n    def _marker(symbol: str, word: str, colour: str, style: Style) -> str:\n        if not style.unicode:\n            return word\n        return f\"{colour}{symbol}{_RESET}\" if style.color else symbol\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/render.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Edit**

```json
{
  "replace_all": false,
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/render.py",
  "old_string": "        if isinstance(row, Span):\n            lines.append(line([row.first]) + \" \" * (widths[0] - cell_len(row.first)) + _GAP + row.rest)\n            lines[-1] = lines[-1].rstrip()\n        else:\n            lines.append(line(row))",
  "new_string": "        if isinstance(row, Span):\n            pad = \" \" * (widths[0] - cell_len(row.first))\n            lines.append((indent + row.first + pad + _GAP + row.rest).rstrip())\n        else:\n            lines.append(line(row))"
}
```

<details>
<summary>↳ Result</summary>

```
The file /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/render.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && F=$(uv run python -c "import click.testing as t; print(t.__file__)"); grep -n "def visible_input\|def hidden_input\|def _getchar" -A 12 $F | head -50
```

<details>
<summary>↳ Result</summary>

```
475:        def visible_input(prompt: str | None = None) -> str:
476-            sys.stdout.write(prompt or "")
477-            try:
478-                val = next(text_input).rstrip("\r\n")
479-            except StopIteration as e:
480-                raise EOFError() from e
481-            sys.stdout.write(f"{val}\n")
482-            sys.stdout.flush()
483-            return val
484-
485-        @_pause_echo(echo_input)  # type: ignore
486:        def hidden_input(prompt: str | None = None) -> str:
487-            sys.stdout.write(f"{prompt or ''}\n")
488-            sys.stdout.flush()
489-            try:
490-                return next(text_input).rstrip("\r\n")
491-            except StopIteration as e:
492-                raise EOFError() from e
493-
494-        @_pause_echo(echo_input)  # type: ignore
495:        def _getchar(echo: bool) -> str:
496-            char = sys.stdin.read(1)
497-
498-            if echo:
499-                sys.stdout.write(char)
500-
501-            sys.stdout.flush()
502-            return char
503-
504-        default_color = color
505-
506-        def should_strip_ansi(
507-            stream: t.IO[t.Any] | None = None, color: bool | None = None
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat > env.py <<'EOF'
"""What every command runs with: the HTTP client, the saved session, the terminal and whether
there's anyone at the keyboard. Tests build one with a mock client and a temporary config
directory; a real run builds the defaults."""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import httpx2

from mission_control.cli.client import TIMEOUT, Api
from mission_control.cli.config import CredentialStore, api_url, default_config_dir
from mission_control.cli.errors import NotLoggedIn
from mission_control.cli.render import Terminal


@dataclass
class Env:
    http: httpx2.Client | None = None
    config_dir: Path | None = None
    interactive: bool | None = None  # None: ask whether stdin is a terminal
    color: bool | None = None  # None: decide from the terminal and NO_COLOR
    _terminal: Terminal | None = field(default=None, init=False, repr=False)

    @property
    def store(self) -> CredentialStore:
        return CredentialStore(self.config_dir or default_config_dir())

    @property
    def term(self) -> Terminal:
        # Built on first use, so it writes to the streams in place when the command runs.
        if self._terminal is None:
            self._terminal = Terminal.for_streams(sys.stdout, sys.stderr, self.color)
        return self._terminal

    @property
    def is_interactive(self) -> bool:
        if self.interactive is not None:
            return self.interactive
        try:
            return sys.stdin.isatty()
        except (AttributeError, ValueError):
            return False

    def client(self) -> httpx2.Client:
        if self.http is None:
            self.http = httpx2.Client(base_url=api_url(), timeout=TIMEOUT)
        return self.http

    def anonymous_api(self) -> Api:
        return Api(self.client())

    def api(self) -> Api:
        """An API client for the logged-in user. A 401 clears the saved session."""
        credentials = self.store.load()
        if credentials is None:
            raise NotLoggedIn()
        return Api(self.client(), credentials.token, on_session_ended=self.store.clear)
EOF
cat > prompts.py <<'EOF'
"""Asking the user things. Prompts go to stderr so they never mix with data. Passwords are read
with the input hidden, or from stdin, one line per prompt, when there's no terminal."""

import sys

import click

from mission_control.cli.env import Env
from mission_control.cli.errors import Declined, UsageProblem


def _read(label: str, *, hidden: bool) -> str:
    sys.stderr.write(f"{label}: ")
    sys.stderr.flush()
    reader = click.termui.hidden_prompt_func if hidden else click.termui.visible_prompt_func
    try:
        return reader("")
    except EOFError:
        # Ctrl+D at a prompt: treat it like Ctrl+C.
        raise KeyboardInterrupt from None


def ask(env: Env, label: str, *, missing: str) -> str:
    """A visible answer. Without a terminal, fail with `missing` instead of waiting."""
    if not env.is_interactive:
        raise UsageProblem(missing)
    while not (answer := _read(label, hidden=False).strip()):
        pass
    return answer


def ask_secret(env: Env, label: str) -> str:
    if env.is_interactive:
        return _read(label, hidden=True)
    line = sys.stdin.readline()
    if not line:
        raise UsageProblem(
            "No password given, and there's no terminal to ask on.",
            hint="Run this in a terminal, or pipe it on stdin.",
        )
    return line.rstrip("\r\n")


def ask_new_secret(env: Env, label: str, repeat: str, *, mismatch: str) -> str:
    """A password being set: asked twice, and both answers must match."""
    first = ask_secret(env, label)
    if first != ask_secret(env, repeat):
        raise UsageProblem(mismatch)
    return first


def confirm(env: Env, warning: str, *, yes: bool, question: str = "Continue?") -> None:
    """Show `warning` and ask before going ahead. `--yes` skips the question. Without a terminal
    the change needs `--yes`, so a script never waits on a prompt."""
    if yes:
        return
    env.term.warn(warning)
    if not env.is_interactive:
        raise UsageProblem("There's no terminal to confirm on.", hint="Re-run with --yes to go ahead.")
    answer = _read(f"{question} [y/N]", hidden=False)
    if answer.strip().lower() not in ("y", "yes"):
        raise Declined()
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat > refusals.py <<'EOF'
"""Turning a refusal into what the user reads: the message, one bullet per problem that adds
something, and a next step for the codes we know."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass

from mission_control.cli.client import ApiError
from mission_control.cli.render import sentence

# A mission's state stopped the action. The message says "a mission", so the CLI adds which one.
STATE_CODES = frozenset({"mission_frozen", "mission_final", "invalid_transition"})

GENERIC_HINTS = {
    "unauthenticated": "Log in again: mc login",
    "busy": "Try again in a moment.",
    "unexpected_response": "Try again. If it keeps happening, check the server's log.",
}


@dataclass(frozen=True)
class Shown:
    message: str
    bullets: tuple[str, ...]
    hints: tuple[str, ...]


@contextmanager
def refusals(
    subject: str | None = None, *, name_state: bool = False, **hints: str
) -> Generator[None]:
    """Give refusals raised inside the block the context only the command knows: the `subject`
    (e.g. "Mission 5") for a not-found message, whether a state refusal should name it, and a
    hint per code."""
    try:
        yield
    except ApiError as error:
        if error.subject is None:
            error.subject = subject
            error.name_state = name_state
        error.hints = hints | error.hints
        raise


def present(error: ApiError) -> Shown:
    message = error.message
    subject = error.subject
    if subject:
        kind = subject.split()[0]
        if error.code == "not_found" and message.lower() == f"{kind} not found".lower():
            message = f"{subject} not found"
        elif error.code in STATE_CODES and getattr(error, "name_state", False):
            message = f"{subject}: {message}"

    bullets = tuple(p.message for p in error.problems if p.message and p.message != error.message)

    hints: list[str] = []
    for code in (error.code, *(p.code for p in error.problems)):
        hint = error.hints.get(code) or GENERIC_HINTS.get(code)
        if hint and hint not in hints:
            hints.append(hint)
    return Shown(sentence(message), bullets, tuple(hints))
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && python3 - <<'EOF'
p='client.py'
s=open(p).read()
s=s.replace('''        self.subject: str | None = None
        self.hints: dict[str, str] = {}''','''        self.subject: str | None = None
        self.name_state = False
        self.hints: dict[str, str] = {}''')
s=s.replace('''    problem. Commands may attach a `subject` (e.g. "Mission 5") and hints for known codes, which
    are used when the refusal is shown."""''','''    problem. Commands may attach a `subject` (e.g. "Mission 5"), whether a state refusal should
    name it, and hints for known codes, which are used when the refusal is shown."""''')
open(p,'w').write(s)
p='refusals.py'
s=open(p).read()
s=s.replace('''        elif error.code in STATE_CODES and getattr(error, "name_state", False):''','''        elif error.code in STATE_CODES and error.name_state:''')
s=s.replace('''    hints: list[str] = []
    for code in (error.code, *(p.code for p in error.problems)):
        hint = error.hints.get(code) or GENERIC_HINTS.get(code)
        if hint and hint not in hints:
            hints.append(hint)
    return Shown(sentence(message), bullets, tuple(hints))''','''    hints: list[str] = []
    for code, refs in ((error.code, {}), *((p.code, p.refs) for p in error.problems)):
        hint = _fill(error.hints.get(code) or GENERIC_HINTS.get(code), refs)
        if hint and hint not in hints:
            hints.append(hint)
    return Shown(sentence(message), bullets, tuple(hints))


def _fill(template: str | None, refs: Mapping[str, object]) -> str | None:
    """A hint may name a record from the problem's refs, e.g. `{assignment_id}`. Without that
    ref the hint is skipped rather than shown half-filled."""
    if template is None:
        return None
    try:
        return template.format_map(dict(refs))
    except (KeyError, IndexError, ValueError):
        return None''')
s=s.replace("from collections.abc import Generator\n","from collections.abc import Generator, Mapping\n")
s=s.replace('''    hint per code."""''','''    hint per code. A hint may use `{name}` placeholders filled from the problem's refs."""''')
open(p,'w').write(s)
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat >> refusals.py <<'EOF'


def report(env: "Env", failure: BaseException) -> int:
    """Show a failure on stderr (or a refusal's error body on stdout, with `--json`) and return
    the exit code to use."""
    term = env.term
    if isinstance(failure, KeyboardInterrupt | click.Abort):
        term.say()
        term.say("Cancelled.")
        return INTERRUPTED
    if isinstance(failure, Unreachable):
        term.error(
            f"Can't reach the Mission Control server at {failure.url}.",
            hint="Is it running? Start it with: uv run mc-server",
        )
        return UNAVAILABLE
    if isinstance(failure, ApiError):
        if env.json_output and failure.has_error_body:
            term.json(failure.body)
        else:
            shown = present(failure)
            term.error(shown.message, shown.bullets, shown.hints)
        return failure.exit_code
    if isinstance(failure, CliError):
        term.error(sentence(failure.message), failure.bullets, failure.hint)
        return failure.exit_code
    raise failure
EOF
python3 - <<'EOF'
p='refusals.py'
s=open(p).read()
s=s.replace('''from mission_control.cli.client import ApiError
from mission_control.cli.render import sentence''','''import click

from mission_control.cli.client import ApiError, Unreachable
from mission_control.cli.env import Env
from mission_control.cli.errors import INTERRUPTED, UNAVAILABLE, CliError
from mission_control.cli.render import sentence''')
s=s.replace('def report(env: "Env", failure','def report(env: Env, failure')
open(p,'w').write(s)
p='env.py'
s=open(p).read()
s=s.replace('''    color: bool | None = None  # None: decide from the terminal and NO_COLOR
''','''    color: bool | None = None  # None: decide from the terminal and NO_COLOR
    json_output: bool = False  # set by a command run with --json
''')
open(p,'w').write(s)
EOF
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
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/common.py",
  "content": "\"\"\"Plumbing every command shares: the group and command classes (help layout, error handling),\nthe current `Env`, and common options.\"\"\"\n\nfrom datetime import date\nfrom typing import Annotated, Any\n\nimport click\nimport typer\nfrom typer.core import TyperCommand, TyperGroup\n\nfrom mission_control.cli.client import ApiError, Unreachable\nfrom mission_control.cli.env import Env\nfrom mission_control.cli.errors import CliError\nfrom mission_control.cli.refusals import report\n\n\nclass Command(TyperCommand):\n    \"\"\"Usage lines that spell out the options (`mc missions match MISSION_ID [--apply]`), and\n    the epilog shown as an example block.\"\"\"\n\n    def collect_usage_pieces(self, ctx: click.Context) -> list[str]:\n        pieces: list[str] = []\n        options: list[str] = []\n        for param in self.get_params(ctx):\n            if param.param_type_name == \"argument\":\n                pieces.append(param.make_metavar(ctx))\n            elif isinstance(param, click.Option) and param.name != \"help\" and not param.hidden:\n                flag = max(param.opts, key=len)\n                text = flag if param.is_flag else f\"{flag} {param.make_metavar(ctx)}\"\n                options.append(text if param.required else f\"[{text}]\")\n        return pieces + options\n\n    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:\n        if not self.epilog:\n            return\n        examples = [line.strip() for line in self.epilog.strip().splitlines() if line.strip()]\n        formatter.write_paragraph()\n        formatter.write_text(\"Example:\" if len(examples) == 1 else \"Examples:\")\n        with formatter.indentation():\n            for line in examples:\n                formatter.write(f\"{' ' * formatter.current_indent}{line}\\n\")\n\n\nclass Group(TyperGroup):\n    \"\"\"A bare group prints its help and exits 0. Failures raised by commands are reported here\n    with their exit code, so tests and real runs behave the same.\"\"\"\n\n    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:\n        if not args and not ctx.resilient_parsing:\n            click.echo(ctx.get_help())\n            ctx.exit(0)\n        return super().parse_args(ctx, args)\n\n    def invoke(self, ctx: click.Context) -> Any:\n        try:\n            return super().invoke(ctx)\n        except (CliError, ApiError, Unreachable, KeyboardInterrupt, click.Abort) as failure:\n            env = ctx.find_object(Env) or Env()\n            raise typer.Exit(report(env, failure)) from None\n\n\ndef group(help: str) -> typer.Typer:\n    return typer.Typer(\n        cls=Group,\n        help=help,\n        rich_markup_mode=None,\n        add_completion=False,\n        pretty_exceptions_enable=False,\n    )\n\n\ndef current_env() -> Env:\n    ctx = click.get_current_context()\n    env = ctx.find_object(Env)\n    if env is None:\n        env = ctx.ensure_object(Env)\n    return env\n\n\ndef start(json_output: bool = False) -> Env:\n    \"\"\"The command's Env, remembering whether output is JSON so refusals print as JSON too.\"\"\"\n    env = current_env()\n    env.json_output = json_output\n    return env\n\n\ndef iso_date(value: str | None) -> str | None:\n    if value is None:\n        return None\n    try:\n        return date.fromisoformat(value).isoformat()\n    except ValueError:\n        raise typer.BadParameter(f\"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2027-03-01.\") from None\n\n\nJson = Annotated[bool, typer.Option(\"--json\", help=\"Print the result as JSON\")]\nYes = Annotated[bool, typer.Option(\"--yes\", \"-y\", help=\"Don't ask for confirmation\")]\nMissionId = Annotated[int, typer.Argument(metavar=\"MISSION_ID\", help=\"The mission's ID\")]\nEmail = Annotated[str, typer.Argument(metavar=\"EMAIL\", help=\"The person's email address\")]\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/common.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat >> commands/common.py <<'EOF'


def command(app: typer.Typer, name: str, example: str | None = None, **settings: Any) -> Any:
    """Register a command with the shared help layout. `example` lines appear under Example."""
    return app.command(name, cls=Command, epilog=example, **settings)
EOF
cat > resolve.py <<'EOF'
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
            raise Refused(f"There's no skill called '{name}'", hint="See the skills: mc skills list")
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
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

<details>
<summary>✏️ User edited None</summary>

```
92	    except ValueError:
93	        raise typer.BadParameter(f"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2027-03-01.") from None
94	
95	
96	Json = Annotated[bool, typer.Option("--json", help="Print the result as JSON")]
97	Yes = Annotated[bool, typer.Option("--yes", "-y", help="Don't ask for confirmation")]
98	MissionId = Annotated[int, typer.Argument(metavar="MISSION_ID", help="The mission's ID")]
99	Email = Annotated[str, typer.Argument(metavar="EMAIL", help="The person's email address")]
100	
101	
102	def command(app: typer.Typer, name: str, example: str | None = None, **settings: Any) -> Any:
103	    """Register a command with the shared help layout. `example` lines appear under Example."""
104	    return app.command(name, cls=Command, epilog=example, **settings)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control && sed -n 336,360p services/assignments.py; grep -n '"[a-z_]*_name"' services/missions/*.py services/context.py | head -20
```

<details>
<summary>↳ Result</summary>

```
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
services/missions/inputs.py:91:        {"skill_id": r.skill_id, "skill_name": r.skill_name, "min_level": r.min_level}
services/missions/changes.py:86:                "mission_name": mission.name,
services/missions/changes.py:88:                "owner_name": owner.name,
services/missions/changes.py:93:                        "slot_name": s.name.strip(),
services/missions/changes.py:159:            {"mission_name": new_name, "changes": changes},
services/missions/changes.py:194:                "mission_name": mission.name,
services/missions/changes.py:196:                "from_owner_name": old_owner.name,
services/missions/changes.py:198:                "to_owner_name": new_owner.name,
services/missions/rules.py:139:        return_to_draft(ctx, repos, mission, event, str(data["mission_name"]))
services/context.py:98:        data={"mission_name": mission_name, "cause": cause.value},
services/missions/slots.py:55:                "mission_name": mission.name,
services/missions/slots.py:57:                "slot_name": added.name,
services/missions/slots.py:109:                "mission_name": mission.name,
services/missions/slots.py:111:                "slot_name": new_name,
services/missions/slots.py:151:                "mission_name": mission.name,
services/missions/slots.py:153:                "slot_name": slot.name,
services/missions/slots.py:192:            {"mission_name": mission.name, "slot_id": slot.id, "slot_name": slot.name},
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/account.py",
  "content": "\"\"\"Signing in and out, who am I, changing my password, and what's waiting on me.\"\"\"\n\nfrom datetime import UTC, datetime\nfrom typing import Annotated, Any\n\nimport typer\n\nfrom mission_control.cli.client import ApiError\nfrom mission_control.cli.commands.common import Json, command, start\nfrom mission_control.cli.config import Credentials\nfrom mission_control.cli.prompts import ask, ask_new_secret, ask_secret\nfrom mission_control.cli.refusals import refusals\nfrom mission_control.cli.render import ROLE, Terminal, plural\n\n\ndef register(app: typer.Typer) -> None:\n    command(app, \"login\", example=\"mc login --email lee@aurora.example\")(login)\n    command(app, \"logout\", example=\"mc logout\")(logout)\n    command(app, \"whoami\", example=\"mc whoami\")(whoami)\n    command(app, \"password\", example=\"mc password\")(password)\n    command(app, \"inbox\", example=\"mc inbox\")(inbox)\n\n\ndef login(\n    email: Annotated[\n        str | None,\n        typer.Option(\"--email\", \"-e\", metavar=\"EMAIL\", help=\"Your email address (asked if left out)\"),\n    ] = None,\n) -> None:\n    \"\"\"Log in. Your password is asked for with the input hidden.\n\n    Without a terminal, pass --email and pipe the password on stdin.\n    \"\"\"\n    env = start()\n    if email is None:\n        email = ask(\n            env,\n            \"Email\",\n            missing=\"No email given, and there's no terminal to ask on. Pass --email, and pipe \"\n            \"the password on stdin.\",\n        )\n    secret = ask_secret(env, \"Password\")\n    with refusals():\n        session = env.anonymous_api().post(\"/auth/login\", {\"email\": email, \"password\": secret})\n    env.store.save(Credentials(session[\"token\"], email, session.get(\"expires_at\")))\n    me = env.api().get(\"/me\")\n\n    about = ROLE.get(me[\"role\"], me[\"role\"])\n    if org := _org_name(me):\n        about = f\"{about}, {org}\"\n    lasts = _session_length(session.get(\"expires_at\"))\n    env.term.ok(f\"Logged in as {me['name']} ({about}).{lasts}\")\n    env.term.next_steps([\"mc inbox\"])\n\n\ndef logout() -> None:\n    \"\"\"Log out and end this session on the server.\"\"\"\n    env = start()\n    if env.store.load() is None:\n        env.term.ok(\"You're not logged in.\")\n        return\n    try:\n        env.api().post(\"/auth/logout\")\n    except ApiError as error:\n        if error.status != 401:  # a session that already ended is as good as logged out\n            raise\n    env.store.clear()\n    env.term.ok(\"Logged out.\")\n\n\ndef whoami(json_output: Json = False) -> None:\n    \"\"\"Show who you're logged in as.\"\"\"\n    env = start(json_output)\n    me = env.api().get(\"/me\")\n    if json_output:\n        env.term.json(me)\n        return\n    env.term.fields(_identity(me) + [(\"Crew profile\", \"yes\" if me.get(\"crew_profile_id\") else \"none\")])\n\n\ndef password() -> None:\n    \"\"\"Change your password. Asks for your current one, then the new one twice.\n\n    Every session ends afterwards, including this one, so log in again.\n    \"\"\"\n    env = start()\n    api = env.api()\n    current = ask_secret(env, \"Current password\")\n    new = ask_new_secret(\n        env,\n        \"New password\",\n        \"Repeat new password\",\n        mismatch=\"The new passwords don't match. Nothing was changed.\",\n    )\n    api.post(\"/me/password\", {\"current_password\": current, \"new_password\": new})\n    env.store.clear()\n    env.term.ok(\"Password changed. All your sessions have ended, including this one.\")\n    env.term.next_steps([\"mc login\"])\n\n\ndef inbox(json_output: Json = False) -> None:\n    \"\"\"Show what's waiting on you: proposals to answer, approvals to give, your missions.\"\"\"\n    env = start(json_output)\n    data = env.api().get(\"/me/inbox\")\n    if json_output:\n        env.term.json(data)\n        return\n    term = env.term\n    proposals = data.get(\"assignments\") or []\n    approvals = data.get(\"approvals\") or []\n    missions = data.get(\"missions\") or []\n    if not (proposals or approvals or missions):\n        term.ok(\"Nothing needs your attention.\")\n        return\n\n    sections = 0\n    if proposals:\n        sections = _section(term, sections, \"Proposals waiting for your answer\")\n        term.table(\n            [\"Assignment\", \"Mission\", \"Slot\", \"Dates\"],\n            [\n                [str(a[\"assignment_id\"]), a[\"mission_name\"], a[\"slot_name\"],\n                 term.dates(a[\"start_date\"], a[\"end_date\"])]\n                for a in proposals\n            ],\n        )  # fmt: skip\n    if approvals:\n        sections = _section(term, sections, \"Missions waiting for your approval\")\n        term.table([\"ID\", \"Mission\", \"Dates\"], [_mission_row(term, m)[:3] for m in approvals])\n    if missions:\n        sections = _section(term, sections, \"Your missions\")\n        term.table([\"ID\", \"Mission\", \"Dates\", \"Status\"], [_mission_row(term, m) for m in missions])\n\n    steps = []\n    if proposals:\n        first = proposals[0][\"assignment_id\"]\n        steps += [f\"mc assignments accept {first}\", f\"mc assignments decline {first}\"]\n    if approvals:\n        steps.append(f\"mc missions show {approvals[0]['id']}\")\n    term.next_steps(steps)\n\n\ndef _section(term: Terminal, shown: int, title: str) -> int:\n    if shown:\n        term.line()\n    term.line(title)\n    return shown + 1\n\n\ndef _mission_row(term: Terminal, mission: dict[str, Any]) -> list[str]:\n    from mission_control.cli.render import MISSION_STATUS\n\n    return [\n        str(mission[\"id\"]),\n        mission[\"name\"],\n        term.dates(mission[\"start_date\"], mission[\"end_date\"]),\n        MISSION_STATUS.get(mission[\"status\"], mission[\"status\"]),\n    ]\n\n\ndef _org_name(me: dict[str, Any]) -> str | None:\n    org = me.get(\"organisation\")\n    return org.get(\"name\") if isinstance(org, dict) else None\n\n\ndef _identity(me: dict[str, Any]) -> list[tuple[str, str]]:\n    pairs = [\n        (\"Name\", me[\"name\"]),\n        (\"Email\", me[\"email\"]),\n        (\"Role\", ROLE.get(me[\"role\"], me[\"role\"])),\n    ]\n    if org := _org_name(me):\n        pairs.append((\"Organisation\", org))\n    return pairs\n\n\ndef _session_length(expires_at: str | None) -> str:\n    if not expires_at:\n        return \"\"\n    try:\n        expires = datetime.fromisoformat(expires_at.replace(\"Z\", \"+00:00\"))\n    except ValueError:\n        return \"\"\n    hours = round((expires - datetime.now(UTC)).total_seconds() / 3600)\n    return f\" Session lasts {plural(hours, 'hour')}.\" if hours >= 1 else \"\"\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/account.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/views.py",
  "content": "\"\"\"How API records read on screen, shared by the command groups.\"\"\"\n\nfrom collections.abc import Mapping, Sequence\nfrom typing import Any\n\nfrom mission_control.cli.render import MISSION_STATUS, ROLE, Terminal\n\n\ndef mission_status(mission: Mapping[str, Any]) -> str:\n    return MISSION_STATUS.get(mission[\"status\"], mission[\"status\"])\n\n\ndef mission_heading(term: Terminal, mission: Mapping[str, Any]) -> str:\n    \"\"\"`Lunar Gateway Resupply · 1–10 Mar 2027 · Draft`.\"\"\"\n    dates = term.dates(mission[\"start_date\"], mission[\"end_date\"])\n    return term.heading(mission[\"name\"], dates, mission_status(mission))\n\n\ndef mission_row(term: Terminal, mission: Mapping[str, Any]) -> list[str]:\n    return [\n        str(mission[\"id\"]),\n        mission[\"name\"],\n        term.dates(mission[\"start_date\"], mission[\"end_date\"]),\n        mission_status(mission),\n    ]\n\n\ndef org_name(me: Mapping[str, Any]) -> str | None:\n    org = me.get(\"organisation\")\n    return org.get(\"name\") if isinstance(org, Mapping) else None\n\n\ndef identity(me: Mapping[str, Any], name: str | None = None) -> list[tuple[str, str]]:\n    pairs = [\n        (\"Name\", name or me[\"name\"]),\n        (\"Email\", me[\"email\"]),\n        (\"Role\", ROLE.get(me[\"role\"], me[\"role\"])),\n    ]\n    if org := org_name(me):\n        pairs.append((\"Organisation\", org))\n    return pairs\n\n\ndef requirements_text(requirements: Sequence[Mapping[str, Any]]) -> str:\n    \"\"\"`Piloting>=4, Leadership>=3`, the same form `--slot` takes.\"\"\"\n    return \", \".join(f\"{r['skill_name']}>={r['min_level']}\" for r in requirements)\n\n\ndef skills_text(skills: Sequence[Mapping[str, Any]]) -> str:\n    return \", \".join(f\"{s['skill_name']} {s['level']}\" for s in skills)\n\n\ndef assignment_summary_rows(term: Terminal, rows: Sequence[Mapping[str, Any]]) -> list[list[str]]:\n    return [\n        [\n            str(a[\"assignment_id\"]),\n            a[\"mission_name\"],\n            a[\"slot_name\"],\n            term.dates(a[\"start_date\"], a[\"end_date\"]),\n            a[\"status\"],\n        ]\n        for a in rows\n    ]\n\n\ndef show_profile(\n    term: Terminal,\n    pairs: list[tuple[str, str]],\n    profile: Mapping[str, Any],\n    *,\n    own: bool,\n) -> None:\n    \"\"\"A crew profile: details, skills, and unavailability. Reasons appear only when the\n    server sent them; IDs only on your own, since you need them to remove an entry.\"\"\"\n    term.fields(pairs + [(\"Bio\", profile.get(\"bio\") or \"none\")])\n    term.line()\n    skills = profile.get(\"skills\") or []\n    if skills:\n        term.table([\"Skill\", \"Level\"], [[s[\"skill_name\"], str(s[\"level\"])] for s in skills])\n    else:\n        term.line(\"No skills recorded yet.\")\n    term.line()\n    unavailable = profile.get(\"unavailability\") or []\n    if not unavailable:\n        term.line(\"No unavailability recorded.\")\n        return\n    with_reasons = any(u.get(\"reason\") for u in unavailable)\n    headers = ([\"ID\"] if own else []) + [\"Unavailable\"] + ([\"Reason\"] if with_reasons else [])\n    rows = []\n    for u in unavailable:\n        row = ([str(u[\"id\"])] if own else []) + [term.dates(u[\"start_date\"], u[\"end_date\"])]\n        rows.append(row + ([u.get(\"reason\") or \"\"] if with_reasons else []))\n    term.table(headers, rows)\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/views.py (file state is current in your context — no need to Read it back)
```

</details>

### 🤖 Claude · 2026-10-12 03:35:06 UTC

Now update account.py to use views, and write the me and assignments commands.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && python3 - <<'EOF'
p='account.py'
s=open(p).read()
start=s.index('def _section(')
end=s.index('def _session_length(')
s=s[:start]+'''def _section(term: Terminal, shown: int, title: str) -> int:
    if shown:
        term.line()
    term.line(title)
    return shown + 1


'''+s[end:]
s=s.replace("_mission_row(term, m)","mission_row(term, m)").replace("_identity(me)","identity(me)").replace("_org_name(me)","org_name(me)")
s=s.replace('''from datetime import UTC, datetime
from typing import Annotated, Any
''','''from datetime import UTC, datetime
from typing import Annotated
''')
s=s.replace('''from mission_control.cli.render import ROLE, Terminal, plural
''','''from mission_control.cli.render import ROLE, Terminal, plural
from mission_control.cli.views import identity, mission_row, org_name
''')
open(p,'w').write(s)
EOF
cat > me.py <<'EOF'
"""Your own crew profile: details, skills and unavailability."""

from typing import Annotated, Any

import typer

from mission_control.cli.client import Api
from mission_control.cli.commands.common import Json, command, group, iso_date, start
from mission_control.cli.errors import Refused, UsageProblem
from mission_control.cli.render import Terminal
from mission_control.cli.views import identity, show_profile

app = group("Your profile and availability.")
unavailable_app = group("Dates you can't fly.")
app.add_typer(unavailable_app, name="unavailable")

Date = Annotated[str, typer.Option(metavar="YYYY-MM-DD", callback=iso_date)]


def _profile_id(api: Api) -> tuple[dict[str, Any], int]:
    me = api.get("/me")
    profile_id = me.get("crew_profile_id")
    if not profile_id:
        raise Refused(
            "You don't have a crew profile",
            hint="A Director can give you one: mc users enable-crew EMAIL",
        )
    return me, profile_id


@command(app, "show", example="mc me show")
def show(json_output: Json = False) -> None:
    """Show your details, skills and unavailability."""
    env = start(json_output)
    api = env.api()
    me = api.get("/me")
    profile = api.get(f"/crew/{me['crew_profile_id']}") if me.get("crew_profile_id") else None
    if json_output:
        env.term.json({"user": me, "crew_profile": profile})
        return
    if profile is None:
        env.term.fields(identity(me) + [("Crew profile", "none")])
        return
    show_profile(env.term, identity(me, profile["name"]), profile, own=True)


@command(app, "update", example='mc me update --name "Ben Ito" --bio "EVA and systems"')
def update(
    name: Annotated[str | None, typer.Option("--name", metavar="NAME", help="Your display name")] = None,
    bio: Annotated[str | None, typer.Option("--bio", metavar="TEXT", help="A short bio")] = None,
    json_output: Json = False,
) -> None:
    """Change your display name or bio."""
    if name is None and bio is None:
        raise UsageProblem("Nothing to change. Pass --name or --bio.")
    env = start(json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    body = {"display_name": name, "bio": bio}
    profile = api.patch(f"/crew/{profile_id}", {k: v for k, v in body.items() if v is not None})
    if json_output:
        env.term.json(profile)
        return
    env.term.ok("Updated your profile.")


@command(
    unavailable_app,
    "add",
    example="mc me unavailable add --start 2027-06-01 --end 2027-06-03 --reason Leave",
)
def add_unavailability(
    start_date: Annotated[str, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
                                            help="First day you're away")],
    end_date: Annotated[str, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date,
                                          help="Last day you're away")],
    reason: Annotated[str, typer.Option("--reason", metavar="TEXT",
                                        help="Why (only Directors and you see it)")],
    json_output: Json = False,
) -> None:  # fmt: skip
    """Record dates you're unavailable. Both days count."""
    env = start(json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    added = api.post(
        f"/crew/{profile_id}/unavailability",
        {"start_date": start_date, "end_date": end_date, "reason": reason},
    )
    if json_output:
        env.term.json(added)
        return
    dates = env.term.dates(added["start_date"], added["end_date"])
    env.term.ok(f"Added unavailability {added['id']}: {dates} ({added['reason']}).")


@command(unavailable_app, "list", example="mc me unavailable list")
def list_unavailability(json_output: Json = False) -> None:
    """List the dates you've said you're unavailable."""
    env = start(json_output)
    api = env.api()
    _, profile_id = _profile_id(api)
    entries = api.get(f"/crew/{profile_id}/unavailability")
    if json_output:
        env.term.json(entries)
        return
    _unavailability_table(env.term, entries)


@command(unavailable_app, "remove", example="mc me unavailable remove 4")
def remove_unavailability(
    unavailability_id: Annotated[int, typer.Argument(metavar="ID", help="From mc me unavailable list")],
) -> None:
    """Remove one of your unavailability entries."""
    env = start()
    api = env.api()
    _, profile_id = _profile_id(api)
    api.delete(f"/crew/{profile_id}/unavailability/{unavailability_id}")
    env.term.ok(f"Removed unavailability {unavailability_id}.")


def _unavailability_table(term: Terminal, entries: list[dict[str, Any]]) -> None:
    if not entries:
        term.line("No unavailability recorded.")
        return
    term.table(
        ["ID", "Unavailable", "Reason"],
        [[str(u["id"]), term.dates(u["start_date"], u["end_date"]), u.get("reason") or ""]
         for u in entries],
    )  # fmt: skip
EOF
cat > assignments.py <<'EOF'
"""Your assignments: list them, and accept, decline or withdraw."""

from typing import Annotated, Any

import typer

from mission_control.cli.client import Api
from mission_control.cli.commands.common import Json, Yes, command, group, start
from mission_control.cli.prompts import confirm
from mission_control.cli.refusals import refusals
from mission_control.cli.views import assignment_summary_rows

app = group("Your assignments: accept, decline or withdraw.")

AssignmentId = Annotated[
    int, typer.Argument(metavar="ASSIGNMENT_ID", help="From mc assignments list or mc inbox")
]


def _refusals(assignment_id: int):  # noqa: ANN202
    return refusals(
        f"Assignment {assignment_id}", not_found="See your assignments: mc assignments list"
    )


def _mine(api: Api, assignment_id: int) -> dict[str, Any] | None:
    """Your summary of the assignment (mission, slot, mission status), if it's yours."""
    for row in api.get("/assignments"):
        if row["assignment_id"] == assignment_id:
            return row
    return None


def _what(summary: dict[str, Any] | None, assignment_id: int) -> str:
    if summary is None:
        return f"assignment {assignment_id}"
    return f"{summary['slot_name']} on {summary['mission_name']}"


@command(app, "list", example="mc assignments list --pending")
def list_assignments(
    pending: Annotated[bool, typer.Option("--pending", help="Only proposals waiting for your answer")] = False,
    json_output: Json = False,
) -> None:
    """List your assignments."""
    env = start(json_output)
    rows = env.api().get("/assignments", {"pending": "true"} if pending else None)
    if json_output:
        env.term.json(rows)
        return
    if not rows:
        env.term.line("No proposals are waiting for you." if pending else "You have no assignments.")
        return
    env.term.table(
        ["ID", "Mission", "Slot", "Dates", "Status"], assignment_summary_rows(env.term, rows)
    )


@command(app, "accept", example="mc assignments accept 21")
def accept(assignment_id: AssignmentId, json_output: Json = False) -> None:
    """Accept a proposal. Only while the mission is a draft."""
    env = start(json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        result = api.post(f"/assignments/{assignment_id}/accept")
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Accepted {_what(summary, assignment_id)}.")


@command(app, "decline", example='mc assignments decline 21 --reason "On leave"')
def decline(
    assignment_id: AssignmentId,
    reason: Annotated[str | None, typer.Option("--reason", metavar="TEXT", help="Why (optional)")] = None,
    json_output: Json = False,
) -> None:
    """Decline a proposal."""
    env = start(json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        body = {"reason": reason} if reason is not None else None
        result = api.post(f"/assignments/{assignment_id}/decline", body)
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Declined {_what(summary, assignment_id)}.")


@command(app, "withdraw", example='mc assignments withdraw 31 --reason "Family matter"')
def withdraw(
    assignment_id: AssignmentId,
    reason: Annotated[str, typer.Option("--reason", metavar="TEXT", help="Why you're withdrawing")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    """Withdraw from an accepted assignment. A mission pending approval goes back to Draft."""
    env = start(json_output)
    api = env.api()
    with _refusals(assignment_id):
        summary = _mine(api, assignment_id)
        pending = summary is not None and summary["mission_status"] == "pending_approval"
        if pending:
            confirm(
                env,
                f"{summary['mission_name']} is pending approval. Withdrawing sends it back to "
                "Draft and clears its approvals.",
                yes=yes,
            )
        result = api.post(f"/assignments/{assignment_id}/withdraw", {"reason": reason})
    if json_output:
        env.term.json(result)
        return
    back = " It's back in Draft." if pending else ""
    env.term.ok(f"Withdrew from {_what(summary, assignment_id)}.{back}")
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/missions.py",
  "content": "\"\"\"Missions: create and edit them, crew them (by hand or with the matcher), and take them\nthrough submission, approval, completion or cancellation.\"\"\"\n\nimport shlex\nfrom collections.abc import Sequence\nfrom contextlib import AbstractContextManager\nfrom typing import Annotated, Any\n\nimport typer\n\nfrom mission_control.cli.client import Api\nfrom mission_control.cli.commands.common import (\n    Json,\n    MissionId,\n    Yes,\n    command,\n    group,\n    iso_date,\n    start,\n)\nfrom mission_control.cli.env import Env\nfrom mission_control.cli.errors import Refused, UsageProblem\nfrom mission_control.cli.prompts import confirm\nfrom mission_control.cli.refusals import refusals\nfrom mission_control.cli.render import Span, Terminal, format_timestamp, join_names, plural\nfrom mission_control.cli.resolve import (\n    SLOT_EXAMPLE,\n    crew_by_email,\n    parse_requirements,\n    parse_slot_spec,\n    requirement_body,\n    skill_ids,\n    slot_in,\n    user_by_email,\n)\nfrom mission_control.cli.views import mission_heading, mission_row, requirements_text\n\napp = group(\"Create, crew and run missions.\")\nslot_app = group(\"Add, change or remove a mission's slots.\")\napp.add_typer(slot_app, name=\"slot\")\n\nSlotRef = Annotated[str, typer.Argument(metavar=\"SLOT\", help=\"The slot's name, or its position (1 for the first)\")]\nReason = Annotated[str, typer.Option(\"--reason\", metavar=\"TEXT\", help=\"Why (recorded in the history)\")]\nStartDate = Annotated[str, typer.Option(\"--start\", metavar=\"YYYY-MM-DD\", callback=iso_date, help=\"First day\")]\nEndDate = Annotated[str, typer.Option(\"--end\", metavar=\"YYYY-MM-DD\", callback=iso_date, help=\"Last day\")]\nSlotSpecs = Annotated[\n    list[str],\n    typer.Option(\"--slot\", metavar=\"SPEC\", help=f\"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}\"),\n]\n\n\ndef _refusals(mission_id: int, **hints: str) -> AbstractContextManager[None]:\n    return refusals(\n        f\"Mission {mission_id}\",\n        name_state=True,\n        not_found=\"See your missions: mc missions list\",\n        not_owner=f\"See who owns it: mc missions show {mission_id}\",\n        **hints,\n    )\n\n\ndef _invalidated_hints(mission_id: int) -> dict[str, str]:\n    \"\"\"Hints for an edit refused because it would invalidate crew's assignments.\"\"\"\n    return {\n        \"slot_has_open_assignments\": (\n            f\"Remove crew first: mc missions remove-crew {mission_id} {{assignment_id}}\"\n        ),\n        \"headcount_below_open_assignments\": f\"See who is assigned: mc missions show {mission_id}\",\n        \"skill_below_minimum\": f\"See who is assigned: mc missions show {mission_id}\",\n        \"unavailable\": f\"See who is assigned: mc missions show {mission_id}\",\n        \"overlap\": f\"See who is assigned: mc missions show {mission_id}\",\n    }\n\n\ndef _confirm_if_pending(env: Env, mission: dict[str, Any], doing: str, yes: bool) -> bool:\n    \"\"\"Ask before a change that sends a pending mission back to Draft. True if it was pending.\"\"\"\n    if mission[\"status\"] != \"pending_approval\":\n        return False\n    confirm(\n        env,\n        f\"{mission['name']} is pending approval. {doing} sends it back to Draft and clears its \"\n        \"approvals.\",\n        yes=yes,\n    )\n    return True\n\n\ndef _back(was_pending: bool) -> str:\n    return \" It's back in Draft.\" if was_pending else \"\"\n\n\ndef _done(env: Env, json_output: bool, body: Any, message: str) -> None:\n    if json_output:\n        env.term.json(body)\n    else:\n        env.term.ok(message)\n\n\ndef _slot_body(api: Api, specs: Sequence[str]) -> list[dict[str, Any]]:\n    parsed = [parse_slot_spec(s) for s in specs]\n    ids = skill_ids(api, [name for spec in parsed for name, _ in spec.requirements])\n    return [\n        {\"name\": s.name, \"headcount\": s.headcount, \"requirements\": requirement_body(s.requirements, ids)}\n        for s in parsed\n    ]\n\n\n# Create, list, show, history\n\n\n@command(\n    app,\n    \"create\",\n    example=(\n        'mc missions create --name \"Europa Flyby\" --start 2027-09-01 --end 2027-09-20 '\n        f'--slot \"{SLOT_EXAMPLE}\"'\n    ),\n)\ndef create(\n    name: Annotated[str, typer.Option(\"--name\", metavar=\"NAME\", help=\"The mission's name\")],\n    start_date: StartDate,\n    end_date: EndDate,\n    slots: SlotSpecs,\n    owner: Annotated[\n        str | None,\n        typer.Option(\"--owner\", metavar=\"EMAIL\", help=\"The owning Lead (Directors create for a Lead)\"),\n    ] = None,\n    json_output: Json = False,\n) -> None:\n    \"\"\"Create a draft mission with one or more slots. Repeat --slot for each.\"\"\"\n    for spec in slots:\n        parse_slot_spec(spec)  # report a malformed spec before anything is sent\n    env = start(json_output)\n    api = env.api()\n    body: dict[str, Any] = {\n        \"name\": name,\n        \"start_date\": start_date,\n        \"end_date\": end_date,\n        \"slots\": _slot_body(api, slots),\n    }\n    if owner is not None:\n        body[\"owner_id\"] = user_by_email(api, owner)[\"id\"]\n    with refusals():\n        mission = api.post(\"/missions\", body)\n    if json_output:\n        env.term.json(mission)\n        return\n    env.term.ok(f\"Created mission {mission['id']}: {mission_heading(env.term, mission)}\")\n    env.term.next_steps([f\"mc missions match {mission['id']}\"])\n\n\n@command(app, \"list\", example=\"mc missions list\")\ndef list_missions(json_output: Json = False) -> None:\n    \"\"\"List the missions you can see.\"\"\"\n    env = start(json_output)\n    missions = env.api().get(\"/missions\")\n    if json_output:\n        env.term.json(missions)\n        return\n    if not missions:\n        env.term.line(\"No missions to show.\")\n        return\n    with_owner = any(m.get(\"owner_name\") for m in missions)\n    headers = [\"ID\", \"Mission\", \"Dates\", \"Status\"] + ([\"Owner\"] if with_owner else [])\n    env.term.table(\n        headers,\n        [mission_row(env.term, m) + ([m.get(\"owner_name\") or \"\"] if with_owner else []) for m in missions],\n    )\n\n\n@command(app, \"show\", example=\"mc missions show 1\")\ndef show(mission_id: MissionId, json_output: Json = False) -> None:\n    \"\"\"Show a mission: its slots, crew and approvals.\"\"\"\n    env = start(json_output)\n    with _refusals(mission_id):\n        mission = env.api().get(f\"/missions/{mission_id}\")\n    if json_output:\n        env.term.json(mission)\n        return\n    _show_mission(env.term, mission)\n\n\ndef _show_mission(term: Terminal, mission: dict[str, Any]) -> None:\n    term.line(mission_heading(term, mission))\n    owner = f\"Owner {mission.get('owner_name') or mission['owner_id']}\"\n    if mission.get(\"created_by_name\") and mission.get(\"created_by_id\") != mission.get(\"owner_id\"):\n        owner = term.heading(owner, f\"created by {mission['created_by_name']}\")\n    term.line(owner)\n    term.line()\n    term.table(\n        [\"#\", \"Slot\", \"Requires\", \"Places\"],\n        [\n            [str(s[\"position\"]), s[\"name\"], requirements_text(s[\"requirements\"]),\n             \"full\" if s[\"open_places\"] <= 0 else f\"{s['open_places']} of {s['headcount']} open\"]\n            for s in mission[\"slots\"]\n        ],\n    )  # fmt: skip\n    term.line()\n    crew = mission.get(\"assignments\") or []\n    if crew:\n        term.table(\n            [\"Assignment\", \"Crew\", \"Slot\", \"Status\"],\n            [[str(a[\"id\"]), a[\"crew_name\"], a[\"slot_name\"], a[\"status\"]] for a in crew],\n        )\n    else:\n        term.line(\"No crew proposed yet.\")\n    required = mission.get(\"approvals_required\")\n    if mission[\"status\"] in (\"pending_approval\", \"active\", \"completed\") and required:\n        approvers = [a[\"director_name\"] for a in mission.get(\"approvals\") or [] if a[\"decision\"] == \"approve\"]\n        names = f\" ({join_names(approvers)})\" if approvers else \"\"\n        term.line()\n        term.line(f\"Approvals: {len(approvers)} of {required}{names}\")\n\n\n_EVENTS: dict[str, tuple[str, str]] = {\n    # event: (with the names from its data, without them)\n    \"mission.created\": (\"Created the mission\", \"Created the mission\"),\n    \"mission.updated\": (\"Edited the mission\", \"Edited the mission\"),\n    \"mission.submitted\": (\"Submitted for approval\", \"Submitted for approval\"),\n    \"mission.approved\": (\"Approved\", \"Approved\"),\n    \"mission.rejected\": (\"Rejected\", \"Rejected\"),\n    \"mission.activated\": (\"Mission became active\", \"Mission became active\"),\n    \"mission.completed\": (\"Completed\", \"Completed\"),\n    \"mission.cancelled\": (\"Cancelled\", \"Cancelled\"),\n    \"mission.transferred\": (\"Handed the mission to {to_owner_name}\", \"Changed the owner\"),\n    \"mission.returned_to_draft\": (\"Mission went back to Draft\", \"Mission went back to Draft\"),\n    \"slot.added\": (\"Added slot {slot_name}\", \"Added a slot\"),\n    \"slot.updated\": (\"Changed slot {slot_name}\", \"Changed a slot\"),\n    \"slot.requirements_changed\": (\"Changed the skills for {slot_name}\", \"Changed a slot's skills\"),\n    \"slot.removed\": (\"Removed slot {slot_name}\", \"Removed a slot\"),\n    \"assignment.proposed\": (\"Proposed {crew_name} for {slot_name}\", \"Proposed crew\"),\n    \"assignment.accepted\": (\"Accepted {slot_name}\", \"Accepted a proposal\"),\n    \"assignment.declined\": (\"Declined {slot_name}\", \"Declined a proposal\"),\n    \"assignment.withdrawn\": (\"Withdrew from {slot_name}\", \"Withdrew\"),\n    \"assignment.removed\": (\"Removed {crew_name} from {slot_name}\", \"Removed crew\"),\n    \"assignment.completed\": (\"{crew_name}'s assignment completed\", \"Assignment completed\"),\n    \"assignment.cancelled\": (\"{crew_name}'s assignment cancelled\", \"Assignment cancelled\"),\n}\n\n\ndef _event_text(entry: dict[str, Any]) -> str:\n    named, plain = _EVENTS.get(entry[\"event\"], (entry[\"event\"], entry[\"event\"]))\n    try:\n        return named.format_map(entry.get(\"data\") or {})\n    except (KeyError, IndexError, ValueError):\n        return plain\n\n\n@command(app, \"history\", example=\"mc missions history 1\")\ndef history(mission_id: MissionId, json_output: Json = False) -> None:\n    \"\"\"Show who changed a mission, what they did and when.\"\"\"\n    env = start(json_output)\n    with _refusals(mission_id):\n        entries = env.api().get(f\"/missions/{mission_id}/history\")\n    if json_output:\n        env.term.json(entries)\n        return\n    if not entries:\n        env.term.line(\"Nothing has happened to this mission yet.\")\n        return\n    with_reasons = any(e.get(\"reason\") for e in entries)\n    env.term.table(\n        [\"When (UTC)\", \"Who\", \"What\"] + ([\"Reason\"] if with_reasons else []),\n        [\n            [format_timestamp(e[\"created_at\"]), e.get(\"actor_name\") or str(e.get(\"actor_id\")),\n             _event_text(e)] + ([e.get(\"reason\") or \"\"] if with_reasons else [])\n            for e in entries\n        ],\n    )  # fmt: skip\n\n\n# Edit and slots\n\n\n@command(app, \"edit\", example=\"mc missions edit 1 --end 2027-03-12\")\ndef edit(\n    mission_id: MissionId,\n    name: Annotated[str | None, typer.Option(\"--name\", metavar=\"NAME\", help=\"A new name\")] = None,\n    start_date: Annotated[str | None, typer.Option(\"--start\", metavar=\"YYYY-MM-DD\", callback=iso_date,\n                                                   help=\"A new first day\")] = None,\n    end_date: Annotated[str | None, typer.Option(\"--end\", metavar=\"YYYY-MM-DD\", callback=iso_date,\n                                                 help=\"A new last day\")] = None,\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:  # fmt: skip\n    \"\"\"Change a mission's name or dates. Owner only.\n\n    A mission pending approval goes back to Draft, so you're asked first.\n    \"\"\"\n    body = {\"name\": name, \"start_date\": start_date, \"end_date\": end_date}\n    body = {k: v for k, v in body.items() if v is not None}\n    if not body:\n        raise UsageProblem(\"Nothing to change. Pass --name, --start or --end.\")\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id, **_invalidated_hints(mission_id)):\n        mission = api.get(f\"/missions/{mission_id}\")\n        was_pending = _confirm_if_pending(env, mission, \"Editing it\", yes)\n        updated = api.patch(f\"/missions/{mission_id}\", body)\n    _done(env, json_output, updated, f\"Updated {updated['name']}.{_back(was_pending)}\")\n\n\n@command(slot_app, \"add\", example=f'mc missions slot add 1 --slot \"Geologist:1:Geology>=4\"')\ndef add_slot(\n    mission_id: MissionId,\n    spec: Annotated[str, typer.Option(\"--slot\", metavar=\"SPEC\",\n                                      help=f\"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}\")],\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:  # fmt: skip\n    \"\"\"Add a slot to a mission. Owner only.\"\"\"\n    parse_slot_spec(spec)\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id):\n        mission = api.get(f\"/missions/{mission_id}\")\n        body = _slot_body(api, [spec])[0]\n        was_pending = _confirm_if_pending(env, mission, \"Adding a slot\", yes)\n        updated = api.post(f\"/missions/{mission_id}/slots\", body)\n    _done(env, json_output, updated, f\"Added {body['name']} to {mission['name']}.{_back(was_pending)}\")\n\n\n@command(\n    slot_app,\n    \"edit\",\n    example='mc missions slot edit 1 Commander --headcount 2 --requires \"Piloting>=4,Leadership>=3\"',\n)\ndef edit_slot(\n    mission_id: MissionId,\n    slot: SlotRef,\n    name: Annotated[str | None, typer.Option(\"--name\", metavar=\"NAME\", help=\"A new name\")] = None,\n    headcount: Annotated[int | None, typer.Option(\"--headcount\", metavar=\"N\",\n                                                  help=\"How many people it needs\")] = None,\n    requires: Annotated[str | None, typer.Option(\"--requires\", metavar=\"SKILL>=LEVEL,...\",\n                                                 help=\"Replace its required skills\")] = None,\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:  # fmt: skip\n    \"\"\"Rename a slot, change its headcount or replace its required skills. Owner only.\"\"\"\n    requirements = parse_requirements(requires) if requires is not None else None\n    if name is None and headcount is None and requirements is None:\n        raise UsageProblem(\"Nothing to change. Pass --name, --headcount or --requires.\")\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id, **_invalidated_hints(mission_id)):\n        mission = api.get(f\"/missions/{mission_id}\")\n        target = slot_in(mission, slot)\n        body: dict[str, Any] = {}\n        if name is not None:\n            body[\"name\"] = name\n        if headcount is not None:\n            body[\"headcount\"] = headcount\n        if requirements is not None:\n            ids = skill_ids(api, [n for n, _ in requirements])\n            body[\"requirements\"] = requirement_body(requirements, ids)\n        was_pending = _confirm_if_pending(env, mission, \"Changing a slot\", yes)\n        updated = api.patch(f\"/missions/{mission_id}/slots/{target['id']}\", body)\n    _done(\n        env, json_output, updated, f\"Updated {target['name']} on {mission['name']}.{_back(was_pending)}\"\n    )\n\n\n@command(slot_app, \"remove\", example='mc missions slot remove 1 \"Mission Specialist\"')\ndef remove_slot(mission_id: MissionId, slot: SlotRef, yes: Yes = False, json_output: Json = False) -> None:\n    \"\"\"Remove a slot. Owner only. Refused while anyone is assigned to it.\"\"\"\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id, **_invalidated_hints(mission_id)):\n        mission = api.get(f\"/missions/{mission_id}\")\n        target = slot_in(mission, slot)\n        was_pending = _confirm_if_pending(env, mission, \"Removing a slot\", yes)\n        updated = api.delete(f\"/missions/{mission_id}/slots/{target['id']}\")\n    _done(\n        env,\n        json_output,\n        updated,\n        f\"Removed {target['name']} from {mission['name']}.{_back(was_pending)}\",\n    )\n\n\n# Crew\n\n\n@command(app, \"match\", example=\"mc missions match 1\")\ndef match(\n    mission_id: MissionId,\n    apply: Annotated[bool, typer.Option(\"--apply\", help=\"Propose the suggested crew (owner only)\")] = False,\n    json_output: Annotated[bool, typer.Option(\"--json\", help=\"Print the suggestion as JSON\")] = False,\n) -> None:\n    \"\"\"Suggest crew for a draft mission's open places. Nothing is changed.\n\n    Owner or Director.\n    \"\"\"\n    env = start(json_output)\n    api = env.api()\n    hints = {\n        \"mission_frozen\": f\"Only draft missions can be matched. See its crew: mc missions show {mission_id}\",\n        \"invalid_transition\": (\n            \"Only draft missions can be matched. Its places are already filled: \"\n            f\"mc missions show {mission_id}\"\n        ),\n        \"mission_final\": f\"Only draft missions can be matched. See it: mc missions show {mission_id}\",\n    }\n    with _refusals(mission_id, **hints):\n        if apply:\n            _apply(env, api, mission_id, json_output)\n            return\n        preview = api.get(f\"/missions/{mission_id}/match\")\n    if json_output:\n        env.term.json(preview)\n        return\n    _show_preview(env.term, mission_id, preview)\n\n\ndef _show_preview(term: Terminal, mission_id: int, preview: dict[str, Any]) -> None:\n    mission = preview[\"mission\"]\n    term.line(term.heading(mission[\"name\"], term.dates(mission[\"start_date\"], mission[\"end_date\"]), \"Draft\"))\n    slots = [s for s in preview[\"slots\"] if s[\"open_places\"] > 0]\n    open_places = preview[\"open_places\"]\n    unfilled = [s for s in slots if s[\"unfilled\"] > 0]\n    suggested = sorted(\n        ((p, s) for s in slots for p in s[\"suggested\"]), key=lambda pair: pair[0][\"pick\"]\n    )\n    if open_places == 0:\n        term.ok(\"Every place already has someone proposed or accepted. Nothing to suggest.\")\n        return\n    if not unfilled:\n        places = \"the 1 open place\" if open_places == 1 else f\"all {open_places} open places\"\n        term.ok(f\"Crew suggested for {places}. Nothing has been proposed yet.\")\n    else:\n        names = join_names([s[\"name\"] for s in unfilled])\n        verb = \"has\" if len(unfilled) == 1 else \"have\"\n        filled = open_places - preview[\"unfilled_places\"]\n        term.note(\n            f\"Crew suggested for {filled} of {plural(open_places, 'open place')}. \"\n            f\"{names} {verb} no eligible crew left.\"\n        )\n    term.line()\n    rows: list[list[str] | Span] = []\n    for slot in slots:\n        for person in slot[\"suggested\"]:\n            rows.append([slot[\"name\"], person[\"name\"], plural(person[\"workload\"], \"day\"),\n                         str(person[\"proficiency\"]), str(person[\"pick\"])])  # fmt: skip\n        if slot[\"unfilled\"]:\n            rows.append(Span(slot[\"name\"], f\"unfilled ({plural(slot['unfilled'], 'place')})\"))\n    term.table([\"Slot\", \"Suggested\", \"Workload\", \"Proficiency\", \"Pick\"], rows)\n    term.line()\n    if unfilled:\n        term.line(\"  The mission can't be submitted until every place is filled.\")\n    else:\n        term.line(\"  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload\")\n        term.line(\"  wins, then highest proficiency (sum of the required skill levels).\")\n\n    if not preview.get(\"can_apply\"):\n        return\n    steps = []\n    if suggested:\n        if len(suggested) == 1:\n            person, slot = suggested[0]\n            who = f\"{person['name']} for {slot['name']}\"\n        else:\n            who = join_names([p[\"name\"] for p, _ in suggested])\n        steps.append(f\"mc missions match {mission_id} --apply    proposes {who}\")\n    for slot in unfilled:\n        steps.append(\n            f\"mc missions propose {mission_id} --slot {shlex.quote(slot['name'])} --crew EMAIL    \"\n            f\"fill {slot['name']} by hand\"\n        )\n    term.next_steps(steps)\n\n\ndef _apply(env: Env, api: Api, mission_id: int, json_output: bool) -> None:\n    proposed = api.post(f\"/missions/{mission_id}/match/apply\")\n    if json_output:\n        env.term.json(proposed)\n        return\n    if not proposed:\n        env.term.note(\"No crew could be proposed: no eligible crew for the open places.\")\n        return\n    mission = api.get(f\"/missions/{mission_id}\")\n    by_id = {a[\"id\"]: a for a in mission.get(\"assignments\") or []}\n    env.term.ok(\n        f\"Proposed {len(proposed)} crew for {mission['name']}. \"\n        f\"{'They need' if len(proposed) == 1 else 'Each of them needs'} to accept.\"\n    )\n    env.term.line()\n    rows = []\n    for item in proposed:\n        known = by_id.get(item[\"id\"], {})\n        rows.append([str(item[\"id\"]), known.get(\"crew_name\", \"\"), known.get(\"slot_name\", \"\")])\n    env.term.table([\"Assignment\", \"Crew\", \"Slot\"], rows)\n    env.term.next_steps([f\"mc missions show {mission_id}\"])\n\n\n@command(\n    app,\n    \"propose\",\n    example='mc missions propose 1 --slot \"Flight Engineer\" --crew chen@aurora.example',\n)\ndef propose(\n    mission_id: MissionId,\n    slot: Annotated[str, typer.Option(\"--slot\", metavar=\"SLOT\", help=\"The slot's name or position\")],\n    crew: Annotated[str, typer.Option(\"--crew\", metavar=\"EMAIL\", help=\"The crew member's email\")],\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:\n    \"\"\"Propose a crew member for a slot. Owner only. They still need to accept.\"\"\"\n    env = start(json_output)\n    api = env.api()\n    free = f\"See who is free: mc missions match {mission_id}\"\n    hints = {\n        \"overlap\": free,\n        \"unavailable\": free,\n        \"skill_below_minimum\": free,\n        \"inactive\": free,\n        \"slot_full\": f\"See the open places: mc missions show {mission_id}\",\n    }\n    with _refusals(mission_id, **hints):\n        mission = api.get(f\"/missions/{mission_id}\")\n        target = slot_in(mission, slot)\n        person = crew_by_email(api, crew)\n        was_pending = _confirm_if_pending(env, mission, \"Proposing crew\", yes)\n        assignment = api.post(\n            f\"/missions/{mission_id}/assignments\",\n            {\"slot_id\": target[\"id\"], \"crew_profile_id\": person[\"crew_profile_id\"]},\n        )\n    _done(\n        env,\n        json_output,\n        assignment,\n        f\"Proposed {person['name']} for {target['name']} on {mission['name']} \"\n        f\"(assignment {assignment['id']}). They need to accept.{_back(was_pending)}\",\n    )\n\n\n@command(app, \"remove-crew\", example=\"mc missions remove-crew 1 21\")\ndef remove_crew(\n    mission_id: MissionId,\n    assignment_id: Annotated[int, typer.Argument(metavar=\"ASSIGNMENT_ID\", help=\"From mc missions show\")],\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:\n    \"\"\"Remove someone from a mission, or take back a proposal. Owner only.\"\"\"\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id):\n        mission = api.get(f\"/missions/{mission_id}\")\n        held = next((a for a in mission.get(\"assignments\") or [] if a[\"id\"] == assignment_id), None)\n        if held is None:\n            raise Refused(\n                f\"Assignment {assignment_id} isn't on {mission['name']}\",\n                hint=f\"See its crew: mc missions show {mission_id}\",\n            )\n        was_pending = _confirm_if_pending(env, mission, \"Removing crew\", yes)\n        result = api.post(f\"/assignments/{assignment_id}/remove\")\n    _done(\n        env,\n        json_output,\n        result,\n        f\"Removed {held['crew_name']} from {held['slot_name']} on {mission['name']}.\"\n        f\"{_back(was_pending)}\",\n    )\n\n\n# Lifecycle\n\n\n@command(app, \"submit\", example=\"mc missions submit 1\")\ndef submit(mission_id: MissionId, json_output: Json = False) -> None:\n    \"\"\"Submit a fully crewed draft for approval. Owner only.\"\"\"\n    env = start(json_output)\n    hints = {\n        \"slot_unfilled\": f\"Fill the open places: mc missions match {mission_id}\",\n        \"proposal_unanswered\": f\"See who hasn't answered: mc missions show {mission_id}\",\n    }\n    with _refusals(mission_id, **hints):\n        mission = env.api().post(f\"/missions/{mission_id}/submit\")\n    needs = mission.get(\"approvals_required\")\n    after = f\" It needs {plural(needs, 'approval')}.\" if needs else \"\"\n    _done(env, json_output, mission, f\"Submitted {mission['name']} for approval.{after}\")\n\n\n@command(app, \"approve\", example=\"mc missions approve 1\")\ndef approve(mission_id: MissionId, json_output: Json = False) -> None:\n    \"\"\"Approve a mission pending approval. Directors who didn't create it and aren't on it.\"\"\"\n    env = start(json_output)\n    with _refusals(mission_id):\n        mission = env.api().post(f\"/missions/{mission_id}/approve\")\n    if mission[\"status\"] == \"active\":\n        state = \"It's now active.\"\n    else:\n        given = sum(1 for a in mission.get(\"approvals\") or [] if a[\"decision\"] == \"approve\")\n        state = f\"It's pending approval ({given} of {plural(mission['approvals_required'], 'approval')}).\"\n    _done(env, json_output, mission, f\"Approved {mission['name']}. {state}\")\n\n\n@command(app, \"reject\", example='mc missions reject 6 --reason \"Roster too thin\"')\ndef reject(mission_id: MissionId, reason: Reason, json_output: Json = False) -> None:\n    \"\"\"Reject a mission pending approval. It goes back to Draft. Directors only.\"\"\"\n    env = start(json_output)\n    with _refusals(mission_id):\n        mission = env.api().post(f\"/missions/{mission_id}/reject\", {\"reason\": reason})\n    _done(env, json_output, mission, f\"Rejected {mission['name']}. It's back in Draft.\")\n\n\n@command(app, \"transfer\", example=\"mc missions transfer 1 --owner nora@aurora.example\")\ndef transfer(\n    mission_id: MissionId,\n    owner: Annotated[str, typer.Option(\"--owner\", metavar=\"EMAIL\", help=\"The new owning Lead\")],\n    yes: Yes = False,\n    json_output: Json = False,\n) -> None:\n    \"\"\"Hand a mission to another Lead. Directors only.\"\"\"\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id):\n        new_owner = user_by_email(api, owner)\n        mission = api.get(f\"/missions/{mission_id}\")\n        was_pending = _confirm_if_pending(env, mission, \"Changing the owner\", yes)\n        updated = api.post(f\"/missions/{mission_id}/owner\", {\"owner_id\": new_owner[\"id\"]})\n    _done(\n        env,\n        json_output,\n        updated,\n        f\"{updated['name']} now belongs to {new_owner['name']}.{_back(was_pending)}\",\n    )\n\n\n@command(app, \"complete\", example=\"mc missions complete 5\")\ndef complete(mission_id: MissionId, json_output: Json = False) -> None:\n    \"\"\"Mark an active mission completed. Owner or Director.\"\"\"\n    env = start(json_output)\n    with _refusals(mission_id):\n        mission = env.api().post(f\"/missions/{mission_id}/complete\")\n    _done(\n        env,\n        json_output,\n        mission,\n        f\"Completed {mission['name']}. Its accepted assignments are completed too.\",\n    )\n\n\n@command(app, \"cancel\", example='mc missions cancel 1 --reason \"Budget cut\"')\ndef cancel(mission_id: MissionId, reason: Reason, yes: Yes = False, json_output: Json = False) -> None:\n    \"\"\"Cancel a mission that isn't finished. Owner or Director. Asks first.\"\"\"\n    env = start(json_output)\n    api = env.api()\n    with _refusals(mission_id):\n        mission = api.get(f\"/missions/{mission_id}\")\n        confirm(\n            env,\n            f\"Cancelling {mission['name']} can't be undone. Its open assignments will be cancelled too.\",\n            yes=yes,\n            question=f\"Cancel {mission['name']}?\",\n        )\n        cancelled = api.post(f\"/missions/{mission_id}/cancel\", {\"reason\": reason})\n    _done(env, json_output, cancelled, f\"Cancelled {cancelled['name']}.\")\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/missions.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && cat > crew.py <<'EOF'
"""Crew profiles: list and view them, see someone's assignment history, and set skill levels."""

from typing import Annotated

import typer

from mission_control.cli.commands.common import Email, Json, command, group, start
from mission_control.cli.refusals import refusals
from mission_control.cli.resolve import crew_by_email, skill_named
from mission_control.cli.views import assignment_summary_rows, show_profile, skills_text

app = group("Crew profiles, skill levels and assignment history.")

Skill = Annotated[str, typer.Argument(metavar="SKILL", help="The skill's name")]


@command(app, "list", example="mc crew list")
def list_crew(json_output: Json = False) -> None:
    """List the crew you can see."""
    env = start(json_output)
    crew = env.api().get("/crew")
    if json_output:
        env.term.json(crew)
        return
    if not crew:
        env.term.line("No crew to show.")
        return
    env.term.table(
        ["Name", "Email", "Skills"],
        [
            [c["name"] + ("" if c.get("active", True) else " (deactivated)"), c["email"],
             skills_text(c.get("skills") or [])]
            for c in crew
        ],
    )  # fmt: skip


@command(app, "show", example="mc crew show fay@aurora.example")
def show(email: Email, json_output: Json = False) -> None:
    """Show someone's profile, skills and unavailable dates."""
    env = start(json_output)
    api = env.api()
    person = crew_by_email(api, email)
    profile = api.get(f"/crew/{person['crew_profile_id']}")
    if json_output:
        env.term.json(profile)
        return
    pairs = [("Name", profile["name"]), ("Email", profile["email"])]
    if not profile.get("active", True):
        pairs.append(("Status", "deactivated"))
    show_profile(env.term, pairs, profile, own=False)


@command(app, "history", example="mc crew history chen@aurora.example")
def history(email: Email, json_output: Json = False) -> None:
    """Show someone's assignment history, including missions they've left."""
    env = start(json_output)
    api = env.api()
    person = crew_by_email(api, email)
    rows = api.get(f"/crew/{person['crew_profile_id']}/assignments")
    if json_output:
        env.term.json(rows)
        return
    if not rows:
        env.term.line(f"{person['name']} has no assignments yet.")
        return
    env.term.table(
        ["Assignment", "Mission", "Slot", "Dates", "Status"], assignment_summary_rows(env.term, rows)
    )


@command(app, "set-skill", example="mc crew set-skill ana@aurora.example Piloting 5")
def set_skill(
    email: Email,
    skill: Skill,
    level: Annotated[int, typer.Argument(metavar="LEVEL", help="1 to 5")],
    json_output: Json = False,
) -> None:
    """Set someone's level in a skill. Leads and Directors, never for themselves."""
    env = start(json_output)
    api = env.api()
    person = crew_by_email(api, email)
    found = skill_named(api, skill)
    with refusals():
        result = api.put(
            f"/crew/{person['crew_profile_id']}/skills/{found['id']}", {"level": level}
        )
    if json_output:
        env.term.json(result)
        return
    env.term.ok(f"Set {person['name']}'s {found['name']} to {level}.")


@command(app, "unset-skill", example="mc crew unset-skill ana@aurora.example Leadership")
def unset_skill(email: Email, skill: Skill) -> None:
    """Remove a skill from someone's profile. Leads and Directors, never for themselves."""
    env = start()
    api = env.api()
    person = crew_by_email(api, email)
    found = skill_named(api, skill)
    api.delete(f"/crew/{person['crew_profile_id']}/skills/{found['id']}")
    env.term.ok(f"Removed {found['name']} from {person['name']}'s skills.")
EOF
cat > admin.py <<'EOF'
"""Running the organisation (Directors): users and roles, the skill catalogue, and how many
approvals a mission needs."""

from enum import StrEnum
from typing import Annotated

import typer

from mission_control.cli.commands.common import Email, Json, command, group, start
from mission_control.cli.prompts import ask_new_secret
from mission_control.cli.render import ROLE, plural
from mission_control.cli.resolve import skill_named, user_by_email

users_app = group("Users and roles (Directors).")
skills_app = group("The skill catalogue (Directors manage it; Leads can list it).")
org_app = group("Organisation settings (Directors).")


class RoleName(StrEnum):
    director = "director"
    lead = "lead"
    crew = "crew"


RoleArg = Annotated[RoleName, typer.Argument(metavar="ROLE", help="director, lead or crew")]
SkillName = Annotated[str, typer.Argument(metavar="NAME", help="The skill's name")]


def _a(role: str) -> str:
    label = ROLE.get(role, role)
    return f"an {label}" if label[0] in "AEIOU" else f"a {label}"


# Users


@users_app.command("list")
def _placeholder() -> None:  # replaced below; keeps the command order in help
    pass


users_app.registered_commands.clear()


@command(users_app, "list", example="mc users list")
def list_users(json_output: Json = False) -> None:
    """List everyone in your organisation."""
    env = start(json_output)
    users = env.api().get("/users")
    if json_output:
        env.term.json(users)
        return
    env.term.table(
        ["ID", "Name", "Email", "Role", "Status"],
        [
            [str(u["id"]), u["name"], u["email"], ROLE.get(u["role"], u["role"]),
             "active" if u.get("is_active", True) else "deactivated"]
            for u in users
        ],
    )  # fmt: skip


@command(
    users_app,
    "add",
    example='mc users add --email zoe@aurora.example --name "Zoe Lin" --role crew',
)
def add_user(
    email: Annotated[str, typer.Option("--email", metavar="EMAIL", help="Their email; they log in with it")],
    name: Annotated[str, typer.Option("--name", metavar="NAME", help="Their full name")],
    role: Annotated[RoleName, typer.Option("--role", metavar="ROLE", help="director, lead or crew")],
    json_output: Json = False,
) -> None:
    """Add a user. You set their initial password, asked for twice with the input hidden."""
    env = start(json_output)
    api = env.api()
    secret = ask_new_secret(
        env,
        "Initial password",
        "Repeat initial password",
        mismatch="The passwords don't match. Nothing was changed.",
    )
    user = api.post(
        "/users", {"email": email, "name": name, "role": role.value, "password": secret}
    )
    if json_output:
        env.term.json(user)
        return
    env.term.ok(f"Added {user['name']} ({user['email']}) as {_a(user['role'])}.")
    env.term.next_steps([f"They log in with: mc login --email {user['email']}"])


@command(users_app, "set-role", example="mc users set-role nora@aurora.example director")
def set_role(email: Email, role: RoleArg, json_output: Json = False) -> None:
    """Change someone's role."""
    env = start(json_output)
    api = env.api()
    user = user_by_email(api, email)
    updated = api.patch(f"/users/{user['id']}", {"role": role.value})
    if json_output:
        env.term.json(updated)
        return
    env.term.ok(f"{user['name']} is now {_a(role.value)}.")


@command(users_app, "deactivate", example="mc users deactivate chen@aurora.example")
def deactivate(email: Email, json_output: Json = False) -> None:
    """Deactivate someone. They can't log in, and their history stays."""
    env = start(json_output)
    api = env.api()
    user = user_by_email(api, email)
    updated = api.patch(f"/users/{user['id']}", {"is_active": False})
    if json_output:
        env.term.json(updated)
        return
    env.term.ok(f"Deactivated {user['name']}. They can no longer log in.")


@command(users_app, "enable-crew", example="mc users enable-crew lee@aurora.example")
def enable_crew(email: Email, json_output: Json = False) -> None:
    """Give someone a crew profile, so they can be put on missions."""
    env = start(json_output)
    api = env.api()
    user = user_by_email(api, email)
    profile = api.post(f"/users/{user['id']}/crew-profile")
    if json_output:
        env.term.json(profile)
        return
    env.term.ok(f"{user['name']} now has a crew profile.")


# Skills


@command(skills_app, "list", example="mc skills list")
def list_skills(json_output: Json = False) -> None:
    """List the skill catalogue."""
    env = start(json_output)
    skills = env.api().get("/skills")
    if json_output:
        env.term.json(skills)
        return
    if not skills:
        env.term.line("No skills yet.")
        return
    if any(s.get("category") for s in skills):
        env.term.table(["Skill", "Category"], [[s["name"], s.get("category") or ""] for s in skills])
    else:
        env.term.lines(s["name"] for s in skills)


@command(skills_app, "add", example='mc skills add "Robotics"')
def add_skill(name: SkillName, json_output: Json = False) -> None:
    """Add a skill to the catalogue."""
    env = start(json_output)
    skill = env.api().post("/skills", {"name": name})
    if json_output:
        env.term.json(skill)
        return
    env.term.ok(f"Added skill {skill['name']}.")


@command(skills_app, "rename", example='mc skills rename Geology "Planetary Geology"')
def rename_skill(
    name: SkillName,
    new_name: Annotated[str, typer.Argument(metavar="NEW_NAME", help="What to call it")],
    json_output: Json = False,
) -> None:
    """Rename a skill. Everyone who has it keeps it."""
    env = start(json_output)
    api = env.api()
    skill = skill_named(api, name)
    renamed = api.patch(f"/skills/{skill['id']}", {"name": new_name})
    if json_output:
        env.term.json(renamed)
        return
    env.term.ok(f"Renamed {skill['name']} to {renamed['name']}.")


@command(skills_app, "remove", example="mc skills remove Robotics")
def remove_skill(name: SkillName) -> None:
    """Remove a skill nobody has and no slot requires."""
    env = start()
    api = env.api()
    skill = skill_named(api, name)
    api.delete(f"/skills/{skill['id']}")
    env.term.ok(f"Removed skill {skill['name']}.")


# Organisation


@command(org_app, "show", example="mc org show")
def show_org(json_output: Json = False) -> None:
    """Show your organisation's settings."""
    env = start(json_output)
    org = env.api().get("/org")
    if json_output:
        env.term.json(org)
        return
    env.term.fields(
        [("Organisation", org["name"]), ("Approvals required", str(org["required_approvals"]))]
    )


@command(org_app, "set-approvals", example="mc org set-approvals 2")
def set_approvals(
    count: Annotated[int, typer.Argument(metavar="N", help="Approvals a mission needs to go active")],
    json_output: Json = False,
) -> None:
    """Set how many Directors must approve a mission."""
    env = start(json_output)
    org = env.api().patch("/org", {"required_approvals": count})
    if json_output:
        env.term.json(org)
        return
    env.term.ok(
        f"Missions now need {plural(org['required_approvals'], 'approval')}. Missions already "
        "pending keep the number they were submitted with."
    )
EOF
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && python3 - <<'EOF'
p='admin.py'
s=open(p).read()
s=s.replace('''@users_app.command("list")
def _placeholder() -> None:  # replaced below; keeps the command order in help
    pass


users_app.registered_commands.clear()


''','')
open(p,'w').write(s)
EOF
cat > ../main.py <<'EOF'
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

app = group("Mission Control: plan missions, crew them and get them approved.")
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
        typer.Option("--version", help="Show the version and exit", callback=_show_version, is_eager=True),
    ] = False,
) -> None:
    """Mission Control: plan missions, crew them and get them approved.

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
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='pyproject.toml'
s=open(p).read()
s=s.replace('''[project.scripts]
mc-server = "mission_control.api.app:main"
''','''[project.scripts]
mc = "mission_control.cli.main:main"
mc-server = "mission_control.api.app:main"
''')
open(p,'w').write(s)
EOF
uv sync 2>&1 | tail -1; uv run pytest tests/cli -q -x 2>&1 | tail -30
```

<details>
<summary>↳ Result</summary>

```
 ~ mission-control==0.1.0 (from file:///Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli)
F
=================================== FAILURES ===================================
__ test_m16_login_prompts_for_email_and_hidden_password_then_stores_the_token __

mc = Mc(api=FakeApi(routes={('POST', '/auth/login'): <function _login_ok at 0x10b3bccc0>, ('GET', '/me'): <Response [200 OK.../folders/jh/4w284m3j7hlf7dnyy7mbw5k00000gn/T/pytest-of-pritanbarai/pytest-136/test_m16_login_prompts_for_ema0/config'))
api = FakeApi(routes={('POST', '/auth/login'): <function _login_ok at 0x10b3bccc0>, ('GET', '/me'): <Response [200 OK]>}, calls=[])

    def test_m16_login_prompts_for_email_and_hidden_password_then_stores_the_token(mc, api):
        api.on("POST", "/auth/login", _login_ok)
        api.on("GET", "/me", ok(LEE_ME))
    
        result = mc("login", input="lee@aurora.example\norbital launch window\n", interactive=True)
    
>       assert result.exit_code == 0, result.stderr
E       AssertionError: 
E       assert 1 == 0
E        +  where 1 = Result(exit_code=1, stdout='', stderr='', exception=RuntimeError('There is no active click context.')).exit_code

tests/cli/test_cli_auth.py:24: AssertionError
=========================== short test summary info ============================
FAILED tests/cli/test_cli_auth.py::test_m16_login_prompts_for_email_and_hidden_password_then_stores_the_token
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python -c "
import sys; sys.path.insert(0,'tests/cli'); sys.path.insert(0,'tests')
from cli_fakes import *
import traceback
from pathlib import Path
api=FakeApi(); m=Mc(api, Path('/tmp/m16probe/cfg'))
r=m('whoami')
traceback.print_exception(r.exception)
" 2>&1 | tail -15
```

<details>
<summary>↳ Result</summary>

```
  File "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/typer/main.py", line 1524, in wrapper
    return callback(**use_params)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/account.py", line 74, in whoami
    env = start(json_output)
          ^^^^^^^^^^^^^^^^^^
  File "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/common.py", line 82, in start
    env = current_env()
          ^^^^^^^^^^^^^
  File "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/common.py", line 73, in current_env
    ctx = click.get_current_context()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/click/globals.py", line 39, in get_current_context
    raise RuntimeError("There is no active click context.") from e
RuntimeError: There is no active click context.
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python -c "
import typer.core as c; print(c._click, c._click.__file__ if hasattr(c._click,'__file__') else '')
import typer; print([n for n in dir(typer) if 'context' in n.lower() or n in ('Abort','Exit','BadParameter','echo','prompt')])
"; ls .venv/lib/python3.12/site-packages/typer/
```

<details>
<summary>↳ Result</summary>

```
<module 'typer._click' from '/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/typer/_click/__init__.py'> /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/typer/_click/__init__.py
['Abort', 'BadParameter', 'Context', 'Exit', 'echo', 'prompt']
__init__.py
__main__.py
__pycache__
_click
_completion_classes.py
_completion_shared.py
_types.py
_typing.py
cli.py
colors.py
completion.py
core.py
exceptions.py
main.py
models.py
params.py
py.typed
rich_utils.py
testing.py
utils.py
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/typer && sed -n 1,60p __init__.py | grep -v "^#"; ls _click; grep -n "hidden_prompt_func\|visible_prompt_func\|termui" testing.py | head
```

<details>
<summary>↳ Result</summary>

```
"""Typer, build great CLIs. Easy to code. Based on Python type hints."""

__version__ = "0.27.3"

from shutil import get_terminal_size as get_terminal_size

from . import colors as colors
from ._click.exceptions import BadParameter as BadParameter
from ._click.termui import confirm as confirm
from ._click.termui import getchar as getchar
from ._click.termui import progressbar as progressbar
from ._click.termui import prompt as prompt
from ._click.termui import secho as secho
from ._click.termui import style as style
from ._click.utils import echo as echo
from ._click.utils import format_filename as format_filename
from ._click.utils import get_app_dir as get_app_dir
from ._click.utils import get_binary_stream as get_binary_stream
from ._click.utils import get_text_stream as get_text_stream
from .exceptions import Abort as Abort
from .exceptions import Exit as Exit
from .exceptions import TyperException as TyperException
from .main import Typer as Typer
from .main import launch as launch
from .main import run as run
from .models import CallbackParam as CallbackParam
from .models import Context as Context
from .models import FileBinaryRead as FileBinaryRead
from .models import FileBinaryWrite as FileBinaryWrite
from .models import FileText as FileText
from .models import FileTextWrite as FileTextWrite
from .params import Argument as Argument
from .params import Option as Option
LICENSE.txt
__init__.py
__pycache__
_compat.py
_termui_impl.py
_textwrap.py
_winconsole.py
core.py
decorators.py
exceptions.py
formatting.py
globals.py
parser.py
py.typed
shell_completion.py
termui.py
types.py
utils.py
14:from ._click import _compat, formatting, termui, utils
233:        old_visible_prompt_func = termui.visible_prompt_func
234:        old_hidden_prompt_func = termui.hidden_prompt_func
235:        old__getchar_func = termui._getchar
238:        termui.visible_prompt_func = visible_input
239:        termui.hidden_prompt_func = hidden_input  # ty: ignore[invalid-assignment]
240:        termui._getchar = _getchar
268:            termui.visible_prompt_func = old_visible_prompt_func
269:            termui.hidden_prompt_func = old_hidden_prompt_func
270:            termui._getchar = old__getchar_func
```

</details>

<details>
<summary>💭 Thinking</summary>

Since Typer 0.27 vendors its own click, I'll avoid importing click directly—commands will use typer.Context, and prompts will go through an injectable prompter so tests can verify which prompts were hidden.



</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/lib/python3.12/site-packages/typer && sed -n 1,20p exceptions.py; grep -n "class Context" -A3 models.py
```

<details>
<summary>↳ Result</summary>

```
class TyperException(Exception):
    """A Typer-specific exception"""

    exit_code = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message

    def format_message(self) -> str:
        return self.message


class Abort(RuntimeError):
    """An internal signalling exception that signals Typer to abort."""


31:class Context(_click.Context):
32-    """
33-    The [`Context`](https://click.palletsprojects.com/en/stable/api/#click.Context) has some additional data about the current execution of your program.
34-    When declaring it in a [callback](https://typer.tiangolo.com/tutorial/options/callback-and-context/) function,
```

</details>

### 🤖 Claude · 2026-10-12 03:38:24 UTC

Now rewriting prompts/env/common to the public typer API.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && cat > prompts.py <<'EOF'
"""Asking the user things. Prompts go to the terminal (stderr, or the tty for passwords), never to
stdout. Passwords are read with the input hidden, or from stdin, one line per prompt, when
there's no terminal."""

import getpass
import sys
from typing import Protocol

from mission_control.cli.errors import Declined, UsageProblem


class Prompter(Protocol):
    def ask(self, label: str) -> str: ...

    def ask_hidden(self, label: str) -> str: ...


class TerminalPrompter:
    """Reads answers from the keyboard. Ctrl+C raises KeyboardInterrupt; Ctrl+D is treated the
    same, as a way out."""

    def ask(self, label: str) -> str:
        sys.stderr.write(f"{label}: ")
        sys.stderr.flush()
        line = sys.stdin.readline()
        if not line:
            raise KeyboardInterrupt
        return line.rstrip("\r\n")

    def ask_hidden(self, label: str) -> str:
        try:
            return getpass.getpass(f"{label}: ")
        except EOFError:
            raise KeyboardInterrupt from None


def ask(env: "Env", label: str, *, missing: str) -> str:
    """A visible answer. Without a terminal, fail with `missing` instead of waiting."""
    if not env.is_interactive:
        raise UsageProblem(missing)
    while not (answer := env.prompter.ask(label).strip()):
        pass
    return answer


def ask_secret(env: "Env", label: str) -> str:
    if env.is_interactive:
        return env.prompter.ask_hidden(label)
    line = sys.stdin.readline()
    if not line:
        raise UsageProblem(
            "No password given, and there's no terminal to ask on.",
            hint="Run this in a terminal, or pipe it on stdin.",
        )
    return line.rstrip("\r\n")


def ask_new_secret(env: "Env", label: str, repeat: str, *, mismatch: str) -> str:
    """A password being set: asked twice, and both answers must match."""
    first = ask_secret(env, label)
    if first != ask_secret(env, repeat):
        raise UsageProblem(mismatch)
    return first


def confirm(env: "Env", warning: str, *, yes: bool, question: str = "Continue?") -> None:
    """Show `warning` and ask before going ahead. `--yes` skips the question. Without a terminal
    the change needs `--yes`, so a script never waits on a prompt."""
    if yes:
        return
    env.term.warn(warning)
    if not env.is_interactive:
        raise UsageProblem("There's no terminal to confirm on.", hint="Re-run with --yes to go ahead.")
    if env.prompter.ask(f"{question} [y/N]").strip().lower() not in ("y", "yes"):
        raise Declined()


from mission_control.cli.env import Env  # noqa: E402  (Env needs Prompter defined first)
EOF
python3 - <<'EOF'
p='env.py'
s=open(p).read()
s=s.replace('''from mission_control.cli.errors import NotLoggedIn
from mission_control.cli.render import Terminal
''','''from mission_control.cli.errors import NotLoggedIn
from mission_control.cli.prompts import Prompter, TerminalPrompter
from mission_control.cli.render import Terminal
''')
s=s.replace('''    json_output: bool = False  # set by a command run with --json
''','''    prompter: Prompter = field(default_factory=TerminalPrompter)
    json_output: bool = False  # set by a command run with --json
''')
open(p,'w').write(s)
EOF
echo done
```

<details>
<summary>↳ Result</summary>

```
done
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && python3 - <<'EOF'
p='prompts.py'
s=open(p).read()
s=s.replace('''

from mission_control.cli.env import Env  # noqa: E402  (Env needs Prompter defined first)
''','')
s=s.replace('''from typing import Protocol

from mission_control.cli.errors import Declined, UsageProblem
''','''from typing import TYPE_CHECKING, Protocol

from mission_control.cli.errors import Declined, UsageProblem

if TYPE_CHECKING:
    from mission_control.cli.env import Env
''')
open(p,'w').write(s)

p='commands/common.py'
s=open(p).read()
s=s.replace('''import click
import typer
from typer.core import TyperCommand, TyperGroup
''','''import typer
from typer.core import TyperCommand, TyperGroup
''')
s=s.replace('''    def collect_usage_pieces(self, ctx: click.Context) -> list[str]:
        pieces: list[str] = []
        options: list[str] = []
        for param in self.get_params(ctx):
            if param.param_type_name == "argument":
                pieces.append(param.make_metavar(ctx))
            elif isinstance(param, click.Option) and param.name != "help" and not param.hidden:''','''    def collect_usage_pieces(self, ctx: typer.Context) -> list[str]:
        pieces: list[str] = []
        options: list[str] = []
        for param in self.get_params(ctx):
            if param.param_type_name == "argument":
                pieces.append(param.make_metavar(ctx))
            elif param.param_type_name == "option" and param.name != "help" and not param.hidden:''')
s=s.replace('''    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:''','''    def format_epilog(self, ctx: typer.Context, formatter: Any) -> None:''')
s=s.replace('''    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            click.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except (CliError, ApiError, Unreachable, KeyboardInterrupt, click.Abort) as failure:''','''    def parse_args(self, ctx: typer.Context, args: list[str]) -> list[str]:
        if not args and not ctx.resilient_parsing:
            typer.echo(ctx.get_help())
            ctx.exit(0)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: typer.Context) -> Any:
        try:
            return super().invoke(ctx)
        except (CliError, ApiError, Unreachable, KeyboardInterrupt) as failure:''')
s=s.replace('''def current_env() -> Env:
    ctx = click.get_current_context()
    env = ctx.find_object(Env)
    if env is None:
        env = ctx.ensure_object(Env)
    return env


def start(json_output: bool = False) -> Env:
    """The command's Env, remembering whether output is JSON so refusals print as JSON too."""
    env = current_env()
    env.json_output = json_output
    return env''','''def start(ctx: typer.Context, json_output: bool = False) -> Env:
    """The command's Env, remembering whether output is JSON so refusals print as JSON too."""
    env = ctx.ensure_object(Env)
    env.json_output = json_output
    return env''')
open(p,'w').write(s)

p='refusals.py'
s=open(p).read()
s=s.replace('''import click

''','')
s=s.replace('''    if isinstance(failure, KeyboardInterrupt | click.Abort):''','''    if isinstance(failure, KeyboardInterrupt):''')
open(p,'w').write(s)
EOF
grep -rn "click" --include=*.py . | grep -v "^./commands/common.py.*#"
```

<details>
<summary>↳ Result</summary>

```
(eval):88: no matches found: --include=*.py
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && grep -rn "click" . ; python3 - <<'EOF'
import re,glob
for p in glob.glob('commands/*.py'):
    if p.endswith(('common.py','__init__.py')): continue
    s=open(p).read()
    lines=s.split('\n'); out=[]; i=0
    while i < len(lines):
        line=lines[i]; out.append(line)
        m=re.match(r'^def ([a-z_]+)\((.*)$', line)
        if m and 'start(' in '\n'.join(lines[i:i+40]).split('\ndef ')[0] and not m.group(1).startswith('_'):
            rest=m.group(2)
            if rest.startswith(')'):
                out[-1]=f'def {m.group(1)}(ctx: typer.Context{rest}'
            elif rest=='' :
                out.append('    ctx: typer.Context,')
            else:
                out[-1]=f'def {m.group(1)}(ctx: typer.Context, {rest}'
        i+=1
    s='\n'.join(out)
    s=s.replace('start()','start(ctx)').replace('start(json_output)','start(ctx, json_output)')
    open(p,'w').write(s)
EOF
grep -n "^def [a-z]" commands/*.py | grep -v "ctx: typer.Context" ; grep -n "ctx: typer.Context,$" commands/*.py | head -3
```

<details>
<summary>↳ Result</summary>

```
commands/assignments.py:41:def list_assignments(
commands/assignments.py:75:def decline(
commands/assignments.py:95:def withdraw(
commands/account.py:17:def register(app: typer.Typer) -> None:
commands/account.py:25:def login(
commands/admin.py:60:def add_user(
commands/admin.py:157:def rename_skill(
commands/admin.py:201:def set_approvals(
commands/missions.py:119:def create(
commands/missions.py:277:def edit(
commands/missions.py:306:def add_slot(
commands/missions.py:331:def edit_slot(
commands/missions.py:389:def match(
commands/missions.py:505:def propose(
commands/missions.py:543:def remove_crew(
commands/missions.py:614:def transfer(
commands/common.py:61:def group(help: str) -> typer.Typer:
commands/common.py:78:def iso_date(value: str | None) -> str | None:
commands/common.py:93:def command(app: typer.Typer, name: str, example: str | None = None, **settings: Any) -> Any:
commands/crew.py:73:def set_skill(
commands/me.py:48:def update(
commands/me.py:73:def add_unavailability(
commands/me.py:112:def remove_unavailability(
commands/account.py:26:    ctx: typer.Context,
commands/assignments.py:42:    ctx: typer.Context,
commands/assignments.py:76:    ctx: typer.Context,
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/tests/cli && python3 - <<'EOF'
p='cli_fakes.py'
s=open(p).read()
s=s.replace('''@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    exception: BaseException | None
''','''@dataclass
class ScriptedPrompter:
    """Answers prompts from a list and records each one as (label, hidden). Running out of
    answers behaves like Ctrl+C."""

    answers: list[str]
    asked: list[tuple[str, bool]] = field(default_factory=list)

    def ask(self, label: str) -> str:
        self.asked.append((label, False))
        return self._next()

    def ask_hidden(self, label: str) -> str:
        self.asked.append((label, True))
        return self._next()

    def _next(self) -> str:
        if not self.answers:
            raise KeyboardInterrupt
        return self.answers.pop(0)


@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    exception: BaseException | None
    asked: list[tuple[str, bool]] = field(default_factory=list)
''')
s=s.replace('''        input: str | None = None,
        interactive: bool = False,
        color: bool | None = False,
        http: httpx2.Client | None = None,
    ) -> Result:
        env = Env(
            http=http or self.api.client(),
            config_dir=self.config_dir,
            interactive=interactive,
            color=color,
        )
        result = CliRunner().invoke(app, list(args), obj=env, input=input)
        return Result(result.exit_code, result.stdout, result.stderr, result.exception)''','''        input: str | None = None,
        answers: Sequence[str] | None = None,
        color: bool | None = False,
        http: httpx2.Client | None = None,
    ) -> Result:
        """`answers` makes the run interactive and answers its prompts in order. Without it
        there's no terminal, and `input` is what's piped to stdin."""
        prompter = ScriptedPrompter(list(answers or ()))
        env = Env(
            http=http or self.api.client(),
            config_dir=self.config_dir,
            interactive=answers is not None,
            color=color,
            prompter=prompter,
        )
        result = CliRunner().invoke(app, list(args), obj=env, input=input)
        return Result(
            result.exit_code, result.stdout, result.stderr, result.exception, prompter.asked
        )''')
open(p,'w').write(s)

p='test_cli_auth.py'
s=open(p).read()
s=s.replace('''    result = mc("login", input="lee@aurora.example\\norbital launch window\\n", interactive=True)

    assert result.exit_code == 0, result.stderr
    assert "Email: " in result.stderr
    assert "Password: " in result.stderr
    assert "orbital launch window" not in result.stdout + result.stderr  # never echoed''','''    result = mc("login", answers=["lee@aurora.example", "orbital launch window"])

    assert result.exit_code == 0, result.stderr
    assert result.asked == [("Email", False), ("Password", True)]  # the password is hidden
    assert "orbital launch window" not in result.stdout + result.stderr''')
s=s.replace('''    result = mc("login", "--email", "lee@aurora.example", input="pw\\n", interactive=True)

    assert result.exit_code == 0
    assert "Email: " not in result.stderr''','''    result = mc("login", "--email", "lee@aurora.example", answers=["pw"])

    assert result.exit_code == 0
    assert result.asked == [("Password", True)]''')
s=s.replace('''    result = mc(
        "password",
        input="old password here\\nnew passphrase is long\\nnew passphrase is long\\n",
        interactive=True,
    )

    assert result.exit_code == 0, result.stderr
    assert result.stderr.index("Current password: ") < result.stderr.index("New password: ")
    assert result.stderr.index("New password: ") < result.stderr.index("Repeat new password: ")
''','''    result = mc(
        "password",
        answers=["old password here", "new passphrase is long", "new passphrase is long"],
    )

    assert result.exit_code == 0, result.stderr
    assert result.asked == [
        ("Current password", True),
        ("New password", True),
        ("Repeat new password", True),
    ]
''')
s=s.replace('''    result = mc("password", input="old\\nnew one long enough\\ntypo one long enough\\n", interactive=True)''','''    result = mc("password", answers=["old", "new one long enough", "typo one long enough"])''')
s=s.replace('''    result = mc("password", input="old\\nshort\\nshort\\n", interactive=True)''','''    result = mc("password", answers=["old", "short", "short"])''')
open(p,'w').write(s)

p='test_cli_errors.py'
s=open(p).read()
s=s.replace('''    result = mc("login", input="", interactive=True)  # end of input at the prompt''','''    result = mc("login", answers=[])  # Ctrl+C at the first prompt''')
open(p,'w').write(s)

p='test_cli_missions.py'
s=open(p).read()
s=s.replace('''    result = mc("missions", "edit", "1", "--end", "2027-03-12", input="y\\n", interactive=True)''','''    result = mc("missions", "edit", "1", "--end", "2027-03-12", answers=["y"])''')
s=s.replace('''    assert "Continue? [y/N]: " in result.stderr''','''    assert result.asked == [("Continue? [y/N]", False)]''')
s=s.replace('''    result = mc("missions", "edit", "1", "--name", "New", input="n\\n", interactive=True)''','''    result = mc("missions", "edit", "1", "--name", "New", answers=["n"])''')
s=s.replace('''    assert "Continue?" not in result.stderr''','''    assert result.asked == []''')
s=s.replace('''    result = mc("missions", "cancel", "1", "--reason", "Budget cut", input="y\\n", interactive=True)

    assert result.exit_code == 0, result.stderr
    assert "Cancel Lunar Gateway Resupply? Its open assignments will be cancelled too." in (
        result.stderr
    )''','''    result = mc("missions", "cancel", "1", "--reason", "Budget cut", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert result.stderr == (
        "! Cancelling Lunar Gateway Resupply can't be undone. Its open assignments will be "
        "cancelled too.\\n"
    )
    assert result.asked == [("Cancel Lunar Gateway Resupply? [y/N]", False)]''')
open(p,'w').write(s)

p='test_cli_people.py'
s=open(p).read()
s=s.replace('''        "assignments", "withdraw", "31", "--reason", "Family matter", input="y\\n", interactive=True
    )''','''        "assignments", "withdraw", "31", "--reason", "Family matter", answers=["y"]
    )''')
s=s.replace('''        input="a long first passphrase\\na long first passphrase\\n", interactive=True,
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert "Initial password: " in result.stderr
    assert "Repeat initial password: " in result.stderr''','''        answers=["a long first passphrase", "a long first passphrase"],
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert result.asked == [("Initial password", True), ("Repeat initial password", True)]''')
open(p,'w').write(s)
EOF
grep -rn "interactive=True" . ; cd ../.. && uv run pytest tests/cli -q 2>&1 | tail -40
```

<details>
<summary>↳ Result</summary>

```
api = FakeApi(routes={('GET', '/crew'): <Response [200 OK]>, ('GET', '/crew/11'): <Response [200 OK]>}, calls=[Call(method='...', params={}, body=None, token='tok-lee'), Call(method='GET', path='/crew/11', params={}, body=None, token='tok-lee')])

    def test_ac24_lead_sees_busy_dates_without_reasons(mc, api):
        mc.login_as()
        api.on("GET", "/crew", ok(CREW))
        fay = next(c for c in CREW if c["crew_profile_id"] == 11)
        api.on("GET", "/crew/11", ok(fay))
    
        result = mc("crew", "show", "fay@aurora.example")
    
        assert result.exit_code == 0
>       assert result.stdout == (
            "Name    Fay Moreau\n"
            "Email   fay@aurora.example\n"
            "Bio     none\n"
            "\n"
            "  Skill        Level\n"
            "  Piloting     4\n"
            "  Leadership   4\n"
            "\n"
            "  Unavailable   Dates\n"
            "  1             5–8 Mar 2027\n"
        )
E       AssertionError: assert 'Name    Fay ...–8 Mar 2027\n' == 'Name    Fay ...–8 Mar 2027\n'
E         
E         Skipping 119 identical leading characters in diff, use -v to show
E         - navailable   Dates
E         -   1             5–8 Mar 2027
E         + navailable
E         +   5–8 Mar 2027

tests/cli/test_cli_people.py:271: AssertionError
=========================== short test summary info ============================
FAILED tests/cli/test_cli_errors.py::test_m16_usage_errors_exit_2_before_any_request
FAILED tests/cli/test_cli_errors.py::test_m16_bare_mc_shows_help_and_exits_0
FAILED tests/cli/test_cli_errors.py::test_m16_command_help_shows_usage_and_an_example
FAILED tests/cli/test_cli_missions.py::test_m16_show_mission_lists_slots_crew_and_approvals
FAILED tests/cli/test_cli_missions.py::test_v1_history_shows_who_did_what_and_when
FAILED tests/cli/test_cli_people.py::test_p4_me_show_includes_profile_skills_and_unavailability
FAILED tests/cli/test_cli_people.py::test_ac24_lead_sees_busy_dates_without_reasons
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='tests/cli/test_cli_people.py'
s=open(p).read()
s=s.replace('''        "  Unavailable   Dates          Reason\\n"
        "  1             5–8 Mar 2027   Medical\\n"''','''        "  ID   Unavailable    Reason\\n"
        "  1    5–8 Mar 2027   Medical\\n"''')
s=s.replace('''        "  Unavailable   Dates\\n"
        "  1             5–8 Mar 2027\\n"''','''        "  Unavailable\\n"
        "  5–8 Mar 2027\\n"''')
open(p,'w').write(s)
EOF
uv run pytest tests/cli -q 2>&1 | grep -B5 "^E  " | head -120
```

<details>
<summary>↳ Result</summary>

```
        result = mc("missions", "match", "abc")
    
        assert result.exit_code == 2
>       assert "'abc' is not a valid integer" in result.stderr
E       assert "'abc' is not a valid integer" in "Usage: root missions match MISSION_ID [--apply] [--json]\nTry 'root missions match --help' for help.\n\nError: Invalid value for 'MISSION_ID': 'abc' is not a valid int.\n"
E        +  where "Usage: root missions match MISSION_ID [--apply] [--json]\nTry 'root missions match --help' for help.\n\nError: Invalid value for 'MISSION_ID': 'abc' is not a valid int.\n" = Result(exit_code=2, stdout='', stderr="Usage: root missions match MISSION_ID [--apply] [--json]\nTry 'root missions ma...p' for help.\n\nError: Invalid value for 'MISSION_ID': 'abc' is not a valid int.\n", exception=SystemExit(2), asked=[]).stderr
--
    def test_m16_bare_mc_shows_help_and_exits_0(mc):
        result = mc()
    
        assert result.exit_code == 0
>       assert "Usage: mc" in result.stdout
E       assert 'Usage: mc' in 'Usage: root [OPTIONS] COMMAND [ARGS]...\n\n  Mission Control: plan missions, crew them and get them approved.\n\nOpti...    The skill catalogue (Directors manage it; Leads can list it).\n  org          Organisation settings (Directors).\n'
E        +  where 'Usage: root [OPTIONS] COMMAND [ARGS]...\n\n  Mission Control: plan missions, crew them and get them approved.\n\nOpti...    The skill catalogue (Directors manage it; Leads can list it).\n  org          Organisation settings (Directors).\n' = Result(exit_code=0, stdout="Usage: root [OPTIONS] COMMAND [ARGS]...\n\n  Mission Control: plan missions, crew them and...age it; Leads can list it).\n  org          Organisation settings (Directors).\n", stderr='', exception=None, asked=[]).stdout
--
    def test_m16_command_help_shows_usage_and_an_example(mc):
        result = mc("missions", "match", "--help")
    
        assert result.exit_code == 0
>       assert result.stdout.startswith("Usage: mc missions match MISSION_ID [--apply] [--json]\n")
E       assert False
E        +  where False = <built-in method startswith of str object at 0x107037120>('Usage: mc missions match MISSION_ID [--apply] [--json]\n')
E        +    where <built-in method startswith of str object at 0x107037120> = "Usage: root missions match MISSION_ID [--apply] [--json]\n\n  Suggest crew for a draft mission's open places. Nothing...\n  --json   Print the suggestion as JSON\n  --help   Show this message and exit.\n\nExample:\n  mc missions match 1\n".startswith
E        +      where "Usage: root missions match MISSION_ID [--apply] [--json]\n\n  Suggest crew for a draft mission's open places. Nothing...\n  --json   Print the suggestion as JSON\n  --help   Show this message and exit.\n\nExample:\n  mc missions match 1\n" = Result(exit_code=0, stdout="Usage: root missions match MISSION_ID [--apply] [--json]\n\n  Suggest crew for a draft mis...SON\n  --help   Show this message and exit.\n\nExample:\n  mc missions match 1\n", stderr='', exception=None, asked=[]).stdout
--
            "  Assignment   Crew      Slot              Status\n"
            "  21           Chen Wu   Flight Engineer   accepted\n"
            "\n"
            "Approvals: 1 of 2 (Marco Bianchi)\n"
        )
E       AssertionError: assert 'Lunar Gatewa...co Bianchi)\n' == 'Lunar Gatewa...co Bianchi)\n'
E         
E         Skipping 146 identical leading characters in diff, use -v to show
E         -              Places
E         ? ---
E         +           Places
E         -   1   Flight Engineer      Systems Engineering>=3          full
E         ?                                                         ---...
E         
E         ...Full output truncated (12 lines hidden), use '-vv' to show
--
>       assert result.stdout == (
            "  When (UTC)          Who          What                     Reason\n"
            "  2 Jan 2027 10:00    Nora Quinn   Submitted for approval\n"
            "  3 Jan 2027 11:30    Ben Ito      Withdrew from Engineer   Family matter\n"
        )
E       AssertionError: assert '  When (UTC)...mily matter\n' == '  When (UTC)...mily matter\n'
E         
E         -   When (UTC)          Who          What                     Reason
E         ?                      -
E         +   When (UTC)         Who          What                     Reason
E         -   2 Jan 2027 10:00    Nora Quinn   Submitted for approval
E         ?                      -
E         +   2 Jan 2027 10:00   Nora Quinn   Submitted for approval...
E         
E         ...Full output truncated (3 lines hidden), use '-vv' to show
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
import re
p='tests/cli/cli_fakes.py'
s=open(p).read()
s=s.replace("result = CliRunner().invoke(app, list(args), obj=env, input=input)","result = CliRunner().invoke(app, list(args), obj=env, input=input, prog_name=\"mc\")")
open(p,'w').write(s)
p='tests/cli/test_cli_errors.py'
s=open(p).read()
s=s.replace("assert \"'abc' is not a valid integer\" in result.stderr","assert \"Invalid value for 'MISSION_ID': 'abc' is not a valid int\" in result.stderr")
open(p,'w').write(s)
EOF
uv run pytest tests/cli -q -k "show_mission_lists or history_shows" -vv 2>&1 | grep -A30 "Full diff" | head -60
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python - <<'EOF'
import sys; sys.path[:0]=['tests/cli','tests']
from pathlib import Path
import tempfile
from cli_fakes import *
import test_cli_missions as t
api=FakeApi(); m=Mc(api, Path(tempfile.mkdtemp()))
m.login_as()
crew_rows=[{"id": 21, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,"crew_name": "Chen Wu", "status": "accepted", "reason": None}]
approvals=[{"director_id": 2, "director_name": "Marco Bianchi", "decision": "approve", "reason": None}]
api.on("GET","/missions/1",ok(gateway("pending_approval", crew_rows, approvals, open_places={1: 0})))
print(m("missions","show","1").stdout)
api.on("GET","/missions",ok([gateway(), gateway("pending_approval") | {"id": 6, "name": "Deep Space Comms Upgrade","start_date": "2027-04-01", "end_date": "2027-04-20","owner_name": "Nora Quinn"}]))
print(m("missions","list").stdout)
EOF
```

<details>
<summary>↳ Result</summary>

```
Lunar Gateway Resupply · 1–10 Mar 2027 · Pending approval
Owner Lee Park · created by Ruth Adeyemi

  #   Slot                 Requires                     Places
  1   Flight Engineer      Systems Engineering>=3       full
  2   Mission Specialist   EVA>=3                       1 of 1 open
  3   Commander            Piloting>=4, Leadership>=3   1 of 1 open

  Assignment   Crew      Slot              Status
  21           Chen Wu   Flight Engineer   accepted

Approvals: 1 of 2 (Marco Bianchi)

  ID   Mission                    Dates           Status             Owner
  1    Lunar Gateway Resupply     1–10 Mar 2027   Draft              Lee Park
  6    Deep Space Comms Upgrade   1–20 Apr 2027   Pending approval   Nora Quinn
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='tests/cli/test_cli_missions.py'
s=open(p).read()
s=s.replace('''        "  #   Slot                 Requires                        Places\\n"
        "  1   Flight Engineer      Systems Engineering>=3          full\\n"
        "  2   Mission Specialist   EVA>=3                          1 of 1 open\\n"
        "  3   Commander            Piloting>=4, Leadership>=3      1 of 1 open\\n"''','''        "  #   Slot                 Requires                     Places\\n"
        "  1   Flight Engineer      Systems Engineering>=3       full\\n"
        "  2   Mission Specialist   EVA>=3                       1 of 1 open\\n"
        "  3   Commander            Piloting>=4, Leadership>=3   1 of 1 open\\n"''')
s=s.replace('''        "  When (UTC)          Who          What                     Reason\\n"
        "  2 Jan 2027 10:00    Nora Quinn   Submitted for approval\\n"
        "  3 Jan 2027 11:30    Ben Ito      Withdrew from Engineer   Family matter\\n"''','''        "  When (UTC)         Who          What                     Reason\\n"
        "  2 Jan 2027 10:00   Nora Quinn   Submitted for approval\\n"
        "  3 Jan 2027 11:30   Ben Ito      Withdrew from Engineer   Family matter\\n"''')
open(p,'w').write(s)
p='src/mission_control/cli/commands/common.py'
s=open(p).read()
s=s.replace('''def group(help: str) -> typer.Typer:
    return typer.Typer(
        cls=Group,''','''def group(help: str, name: str | None = None) -> typer.Typer:
    return typer.Typer(
        name=name,
        cls=Group,''')
open(p,'w').write(s)
p='src/mission_control/cli/main.py'
s=open(p).read()
s=s.replace('''app = group("Mission Control: plan missions, crew them and get them approved.")''','''app = group("Mission Control: plan missions, crew them and get them approved.", name="mc")''')
open(p,'w').write(s)
EOF
uv run pytest tests/cli -q 2>&1 | tail -5; uv run ruff check src/mission_control/cli tests/cli 2>&1 | tail -30
```

<details>
<summary>↳ Result</summary>

```
........................................................................ [ 48%]
........................................................................ [ 97%]
....                                                                     [100%]
   |
help: Organize imports
   |
12 | import httpx2
   -
13 | from cli_fakes import CREW, SKILLS, USERS, FakeApi, error, gateway, ok, problem
   |

E501 Line too long (101 > 100)
  --> tests/cli/test_cli_scenarios.py:88:101
   |
86 |     def log(self, user, event, from_status=None, to_status=None) -> None:
87 |         self.history.append(
88 |             {"id": len(self.history) + 1, "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",
   |                                                                                                     ^
89 |              "actor_id": user[0], "actor_name": user[1], "event": event,
90 |              "from_status": from_status, "to_status": to_status, "reason": None, "data": {}}
   |

E501 Line too long (101 > 100)
   --> tests/cli/test_cli_scenarios.py:295:101
    |
294 |     mc.login_as("tok-lee")
295 |     gus = mc("missions", "propose", "1", "--slot", "Flight Engineer", "--crew", "gus@aurora.example")
    |                                                                                                     ^
296 |     fay = mc("missions", "propose", "1", "--slot", "Commander", "--crew", "fay@aurora.example")
    |

Found 56 errors.
[*] 6 fixable with `--fix`.
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run ruff format src/mission_control/cli tests/cli && uv run ruff check --fix src/mission_control/cli tests/cli 2>&1 | grep -E "^[A-Z][0-9]+|-->" | paste - - | sort | head -60
```

<details>
<summary>↳ Result</summary>

```
16 files reformatted, 14 files left unchanged
E501 Line too long (101 > 100)	   --> src/mission_control/cli/commands/missions.py:352:101
E501 Line too long (101 > 100)	  --> tests/cli/test_cli_scenarios.py:87:101
E501 Line too long (102 > 100)	   --> src/mission_control/cli/commands/missions.py:302:101
E501 Line too long (102 > 100)	   --> src/mission_control/cli/commands/missions.py:443:101
E501 Line too long (103 > 100)	   --> tests/cli/test_cli_people.py:207:101
E501 Line too long (105 > 100)	   --> src/mission_control/cli/commands/missions.py:714:101
E501 Line too long (106 > 100)	   --> src/mission_control/cli/commands/missions.py:646:101
E501 Line too long (109 > 100)	   --> src/mission_control/cli/commands/missions.py:438:101
[This command modified 12 files you've previously read: .worktrees/m16-cli/tests/cli/test_cli_missions.py, .worktrees/m16-cli/tests/cli/test_cli_match.py, .worktrees/m16-cli/tests/cli/test_cli_config.py, .worktrees/m16-cli/src/mission_control/cli/commands/missions.py, .worktrees/m16-cli/tests/cli/test_cli_render.py and 7 more. Call Read before editing.]
```

</details>

<details>
<summary>✏️ User edited None</summary>

```
1	import pytest
2	from cli_fakes import FakeApi, Mc
3	
4	
5	@pytest.fixture(autouse=True)
6	def _no_ambient_terminal_settings(monkeypatch):
7	    """The developer's own NO_COLOR, TERM or API URL must not change what the tests see."""
8	    for name in ("NO_COLOR", "TERM", "MC_API_URL"):
9	        monkeypatch.delenv(name, raising=False)
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

<details>
<summary>✏️ User edited None</summary>

```
1	"""M16: the credentials file. Kept at mode 0600, replaced atomically, and treated as logged out
2	when missing or unreadable (design §8)."""
3	
4	import stat
5	
6	from mission_control.cli.config import (
7	    DEFAULT_API_URL,
8	    Credentials,
9	    CredentialStore,
10	    api_url,
11	    default_config_dir,
12	)
13	
14	
15	def test_m16_credentials_live_under_the_users_config_directory(monkeypatch, tmp_path):
16	    monkeypatch.setenv("HOME", str(tmp_path))
17
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && for n in 302 352 438 443 646 714; do sed -n "${n}p" src/mission_control/cli/commands/missions.py; done; sed -n 85,90p tests/cli/test_cli_scenarios.py; sed -n 205,209p tests/cli/test_cli_people.py
```

<details>
<summary>↳ Result</summary>

```
    start_date: Annotated[str | None, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
    example='mc missions slot edit 1 Commander --headcount 2 --requires "Piloting>=4,Leadership>=3"',
        "mission_frozen": f"Only draft missions can be matched. See its crew: mc missions show {mission_id}",
        "mission_final": f"Only draft missions can be matched. See it: mc missions show {mission_id}",
        state = f"It's pending approval ({given} of {plural(mission['approvals_required'], 'approval')})."
            f"Cancelling {mission['name']} can't be undone. Its open assignments will be cancelled too.",
    def log(self, user, event, from_status=None, to_status=None) -> None:
        self.history.append(
            {"id": len(self.history) + 1, "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",
             "actor_id": user[0], "actor_name": user[1], "event": event,
             "from_status": from_status, "to_status": to_status, "reason": None, "data": {}}
        )  # fmt: skip
    assert result.exit_code == 1
    assert result.stderr == (
        "✗ You don't have a crew profile.\n  A Director can give you one: mc users enable-crew EMAIL\n"
    )
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands/missions.py",
  "offset": 1,
  "limit": 80
}
```

<details>
<summary>↳ Result</summary>

```
1	"""Missions: create and edit them, crew them (by hand or with the matcher), and take them
2	through submission, approval, completion or cancellation."""
3	
4	import shlex
5	from collections.abc import Sequence
6	from contextlib import AbstractContextManager
7	from typing import Annotated, Any
8	
9	import typer
10	
11	from mission_control.cli.client import Api
12	from mission_control.cli.commands.common import (
13	    Json,
14	    MissionId,
15	    Yes,
16	    command,
17	    group,
18	    iso_date,
19	    start,
20	)
21	from mission_control.cli.env import Env
22	from mission_control.cli.errors import Refused, UsageProblem
23	from mission_control.cli.prompts import confirm
24	from mission_control.cli.refusals import refusals
25	from mission_control.cli.render import Span, Terminal, format_timestamp, join_names, plural
26	from mission_control.cli.resolve import (
27	    SLOT_EXAMPLE,
28	    crew_by_email,
29	    parse_requirements,
30	    parse_slot_spec,
31	    requirement_body,
32	    skill_ids,
33	    slot_in,
34	    user_by_email,
35	)
36	from mission_control.cli.views import mission_heading, mission_row, requirements_text
37	
38	app = group("Create, crew and run missions.")
39	slot_app = group("Add, change or remove a mission's slots.")
40	app.add_typer(slot_app, name="slot")
41	
42	SlotRef = Annotated[
43	    str, typer.Argument(metavar="SLOT", help="The slot's name, or its position (1 for the first)")
44	]
45	Reason = Annotated[
46	    str, typer.Option("--reason", metavar="TEXT", help="Why (recorded in the history)")
47	]
48	StartDate = Annotated[
49	    str, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="First day")
50	]
51	EndDate = Annotated[
52	    str, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="Last day")
53	]
54	SlotSpecs = Annotated[
55	    list[str],
56	    typer.Option(
57	        "--slot", metavar="SPEC", help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}"
58	    ),
59	]
60	
61	
62	def _refusals(mission_id: int, **hints: str) -> AbstractContextManager[None]:
63	    return refusals(
64	        f"Mission {mission_id}",
65	        name_state=True,
66	        not_found="See your missions: mc missions list",
67	        not_owner=f"See who owns it: mc missions show {mission_id}",
68	        **hints,
69	    )
70	
71	
72	def _invalidated_hints(mission_id: int) -> dict[str, str]:
73	    """Hints for an edit refused because it would invalidate crew's assignments."""
74	    return {
75	        "slot_has_open_assignments": (
76	            f"Remove crew first: mc missions remove-crew {mission_id} {{assignment_id}}"
77	        ),
78	        "headcount_below_open_assignments": f"See who is assigned: mc missions show {mission_id}",
79	        "skill_below_minimum": f"See who is assigned: mc missions show {mission_id}",
80	        "unavailable": f"See who is assigned: mc missions show {mission_id}",
```

</details>

### 🤖 Claude · 2026-10-12 03:40:17 UTC

Let me clean up the over-long, `fmt: skip`-heavy signatures in missions.py by introducing option aliases.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && grep -n "fmt: skip" src/mission_control/cli/ -r; sed -n 290,360p src/mission_control/cli/commands/missions.py
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/cli/commands/me.py:84:) -> None:  # fmt: skip
src/mission_control/cli/commands/me.py:136:    )  # fmt: skip
src/mission_control/cli/commands/missions.py:217:    )  # fmt: skip
src/mission_control/cli/commands/missions.py:291:    )  # fmt: skip
src/mission_control/cli/commands/missions.py:308:) -> None:  # fmt: skip
src/mission_control/cli/commands/missions.py:334:) -> None:  # fmt: skip
src/mission_control/cli/commands/missions.py:365:) -> None:  # fmt: skip
src/mission_control/cli/commands/missions.py:488:                         str(person["proficiency"]), str(person["pick"])])  # fmt: skip
src/mission_control/cli/commands/admin.py:52:    )  # fmt: skip
src/mission_control/cli/commands/crew.py:35:    )  # fmt: skip
src/mission_control/cli/commands/account.py:132:        )  # fmt: skip
        ],
    )  # fmt: skip


# Edit and slots


@command(app, "edit", example="mc missions edit 1 --end 2027-03-12")
def edit(
    ctx: typer.Context,
    mission_id: MissionId,
    name: Annotated[str | None, typer.Option("--name", metavar="NAME", help="A new name")] = None,
    start_date: Annotated[str | None, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
                                                   help="A new first day")] = None,
    end_date: Annotated[str | None, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date,
                                                 help="A new last day")] = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:  # fmt: skip
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
        was_pending = _confirm_if_pending(env, mission, "Editing it", yes)
        updated = api.patch(f"/missions/{mission_id}", body)
    _done(env, json_output, updated, f"Updated {updated['name']}.{_back(was_pending)}")


@command(slot_app, "add", example='mc missions slot add 1 --slot "Geologist:1:Geology>=4"')
def add_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    spec: Annotated[str, typer.Option("--slot", metavar="SPEC",
                                      help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:  # fmt: skip
    """Add a slot to a mission. Owner only."""
    parse_slot_spec(spec)
    env = start(ctx, json_output)
    api = env.api()
    with _refusals(mission_id):
        mission = api.get(f"/missions/{mission_id}")
        body = _slot_body(api, [spec])[0]
        was_pending = _confirm_if_pending(env, mission, "Adding a slot", yes)
        updated = api.post(f"/missions/{mission_id}/slots", body)
    _done(
        env, json_output, updated, f"Added {body['name']} to {mission['name']}.{_back(was_pending)}"
    )


@command(
    slot_app,
    "edit",
    example='mc missions slot edit 1 Commander --headcount 2 --requires "Piloting>=4,Leadership>=3"',
)
def edit_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    slot: SlotRef,
    name: Annotated[str | None, typer.Option("--name", metavar="NAME", help="A new name")] = None,
    headcount: Annotated[int | None, typer.Option("--headcount", metavar="N",
                                                  help="How many people it needs")] = None,
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && python3 - <<'EOF'
p='missions.py'
s=open(p).read()
# aliases
s=s.replace('''SlotSpecs = Annotated[''','''NewName = Annotated[str | None, typer.Option("--name", metavar="NAME", help="A new name")]
NewStart = Annotated[
    str | None,
    typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="A new first day"),
]
NewEnd = Annotated[
    str | None,
    typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="A new last day"),
]
Headcount = Annotated[
    int | None, typer.Option("--headcount", metavar="N", help="How many people it needs")
]
Requires = Annotated[
    str | None,
    typer.Option("--requires", metavar="SKILL>=LEVEL,...", help="Replace its required skills"),
]
SlotSpec = Annotated[
    str,
    typer.Option(
        "--slot", metavar="SPEC", help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}"
    ),
]
SlotSpecs = Annotated[''')
s=s.replace('''    name: Annotated[str | None, typer.Option("--name", metavar="NAME", help="A new name")] = None,
    start_date: Annotated[str | None, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
                                                   help="A new first day")] = None,
    end_date: Annotated[str | None, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date,
                                                 help="A new last day")] = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:  # fmt: skip''','''    name: NewName = None,
    start_date: NewStart = None,
    end_date: NewEnd = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:''')
s=s.replace('''    spec: Annotated[str, typer.Option("--slot", metavar="SPEC",
                                      help=f"NAME:HEADCOUNT:SKILL>=LEVEL,... e.g. {SLOT_EXAMPLE}")],
    yes: Yes = False,
    json_output: Json = False,
) -> None:  # fmt: skip''','''    spec: SlotSpec,
    yes: Yes = False,
    json_output: Json = False,
) -> None:''')
import re
i=s.index('def edit_slot(')
j=s.index('"""Rename a slot', i)
s=s[:i]+'''def edit_slot(
    ctx: typer.Context,
    mission_id: MissionId,
    slot: SlotRef,
    name: NewName = None,
    headcount: Headcount = None,
    requires: Requires = None,
    yes: Yes = False,
    json_output: Json = False,
) -> None:
    '''+s[j:]
s=s.replace('''    example='mc missions slot edit 1 Commander --headcount 2 --requires "Piloting>=4,Leadership>=3"',''','''    example='mc missions slot edit 1 Commander --headcount 2 --requires "Piloting>=5"',''')
s=s.replace('''        "mission_frozen": f"Only draft missions can be matched. See its crew: mc missions show {mission_id}",''','''        "mission_frozen": (
            f"Only draft missions can be matched. See its crew: mc missions show {mission_id}"
        ),''')
s=s.replace('''        "mission_final": f"Only draft missions can be matched. See it: mc missions show {mission_id}",''','''        "mission_final": (
            f"Only draft missions can be matched. See it: mc missions show {mission_id}"
        ),''')
s=s.replace('''        state = f"It's pending approval ({given} of {plural(mission['approvals_required'], 'approval')})."''','''        needed = plural(mission["approvals_required"], "approval")
        state = f"It's pending approval ({given} of {needed})."''')
s=s.replace('''            f"Cancelling {mission['name']} can't be undone. Its open assignments will be cancelled too.",''','''            f"Cancelling {mission['name']} can't be undone. Its open assignments will be "
            "cancelled too.",''')
s=s.replace('  # fmt: skip','')
open(p,'w').write(s)
for p in ['me.py','admin.py','crew.py','account.py']:
    s=open(p).read().replace('  # fmt: skip','')
    open(p,'w').write(s)
EOF
grep -n "def add_unavailability" -A12 me.py
```

<details>
<summary>↳ Result</summary>

```
75:def add_unavailability(
76-    ctx: typer.Context,
77-    start_date: Annotated[str, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
78-                                            help="First day you're away")],
79-    end_date: Annotated[str, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date,
80-                                          help="Last day you're away")],
81-    reason: Annotated[str, typer.Option("--reason", metavar="TEXT",
82-                                        help="Why (only Directors and you see it)")],
83-    json_output: Json = False,
84-) -> None:
85-    """Record dates you're unavailable. Both days count."""
86-    env = start(ctx, json_output)
87-    api = env.api()
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli/commands && python3 - <<'EOF'
p='me.py'
s=open(p).read()
s=s.replace('''Date = Annotated[str, typer.Option(metavar="YYYY-MM-DD", callback=iso_date)]
''','''AwayFrom = Annotated[
    str,
    typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date, help="First day you're away"),
]
AwayTo = Annotated[
    str,
    typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date, help="Last day you're away"),
]
AwayReason = Annotated[
    str, typer.Option("--reason", metavar="TEXT", help="Why (only Directors and you see it)")
]
''')
s=s.replace('''    start_date: Annotated[str, typer.Option("--start", metavar="YYYY-MM-DD", callback=iso_date,
                                            help="First day you're away")],
    end_date: Annotated[str, typer.Option("--end", metavar="YYYY-MM-DD", callback=iso_date,
                                          help="Last day you're away")],
    reason: Annotated[str, typer.Option("--reason", metavar="TEXT",
                                        help="Why (only Directors and you see it)")],''','''    start_date: AwayFrom,
    end_date: AwayTo,
    reason: AwayReason,''')
open(p,'w').write(s)
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run ruff format src/mission_control/cli tests/cli >/dev/null && uv run ruff check src/mission_control/cli tests/cli 2>&1 | grep -E "^[A-Z][0-9]+|-->" | paste - - ; uv run pytest tests/cli -q 2>&1 | tail -2
```

<details>
<summary>↳ Result</summary>

```
E501 Line too long (103 > 100)	   --> tests/cli/test_cli_people.py:207:101
E501 Line too long (101 > 100)	  --> tests/cli/test_cli_scenarios.py:87:101
........................................................................ [ 97%]
....                                                                     [100%]
[This command modified 2 files you've previously read: .worktrees/m16-cli/src/mission_control/cli/commands/missions.py, .worktrees/m16-cli/src/mission_control/cli/commands/account.py. Call Read before editing.]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='tests/cli/test_cli_people.py'
s=open(p).read()
s=s.replace('''        "✗ You don't have a crew profile.\\n  A Director can give you one: mc users enable-crew EMAIL\\n"''','''        "✗ You don't have a crew profile.\\n"
        "  A Director can give you one: mc users enable-crew EMAIL\\n"''')
open(p,'w').write(s)
p='tests/cli/test_cli_scenarios.py'
s=open(p).read()
s=s.replace('''            {"id": len(self.history) + 1, "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",''','''            {"id": len(self.history) + 1,
             "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",''')
open(p,'w').write(s)
EOF
uv run ruff format src tests >/dev/null; uv run ruff check && uv run ruff format --check && uv run pytest -q 2>&1 | tail -2
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
109 files already formatted
........................................................................ [ 94%]
.................................................................        [100%]
[This command modified 2 files you've previously read: .worktrees/m16-cli/tests/cli/test_cli_scenarios.py, .worktrees/m16-cli/tests/cli/test_cli_people.py. Call Read before editing.]
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run pytest -q 2>&1 | grep -E "passed|failed"; uv run pytest tests/cli -q 2>&1 | grep -E "passed|failed"; grep -rn "import click\|from click\|httpx[^2]" src tests | grep -v "httpx2" | head; grep -rn "AC-\|M[0-9]\+\b\|§\|PRD" src/mission_control/cli | head
```

<details>
<summary>↳ Result</summary>

```
(Bash completed with no output)
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run pytest 2>&1 | tail -3; uv run pytest tests/cli 2>&1 | tail -1
```

<details>
<summary>↳ Result</summary>

```
........................................................................ [ 94%]
.................................................................        [100%]
1289 passed in 6.28s
148 passed in 1.11s
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && grep -rn "^from mission_control\.\|^import mission_control" src/mission_control/cli | grep -v "mission_control.cli" ; echo "---layer ok"; uv run mc --help; echo "exit $?"; uv run mc missions --help; uv run mc missions match --help; uv run mc missions create --help; uv run mc --version
```

<details>
<summary>↳ Result</summary>

```
---layer ok
Usage: mc [OPTIONS] COMMAND [ARGS]...

  Mission Control: plan missions, crew them and get them approved.

Options:
  --version  Show the version and exit
  --help     Show this message and exit.

Commands:
  login        Log in.
  logout       Log out and end this session on the server.
  whoami       Show who you're logged in as.
  password     Change your password.
  inbox        Show what's waiting on you: proposals to answer, approvals...
  me           Your profile and availability.
  assignments  Your assignments: accept, decline or withdraw.
  missions     Create, crew and run missions.
  crew         Crew profiles, skill levels and assignment history.
  users        Users and roles (Directors).
  skills       The skill catalogue (Directors manage it; Leads can list it).
  org          Organisation settings (Directors).
exit 0
Usage: mc missions [OPTIONS] COMMAND [ARGS]...

  Create, crew and run missions.

Options:
  --help  Show this message and exit.

Commands:
  create       Create a draft mission with one or more slots.
  list         List the missions you can see.
  show         Show a mission: its slots, crew and approvals.
  history      Show who changed a mission, what they did and when.
  edit         Change a mission's name or dates.
  match        Suggest crew for a draft mission's open places.
  propose      Propose a crew member for a slot.
  remove-crew  Remove someone from a mission, or take back a proposal.
  submit       Submit a fully crewed draft for approval.
  approve      Approve a mission pending approval.
  reject       Reject a mission pending approval.
  transfer     Hand a mission to another Lead.
  complete     Mark an active mission completed.
  cancel       Cancel a mission that isn't finished.
  slot         Add, change or remove a mission's slots.
Usage: mc missions match MISSION_ID [--apply] [--json]

  Suggest crew for a draft mission's open places. Nothing is changed.

  Owner or Director.

Arguments:
  MISSION_ID  The mission's ID  [required]

Options:
  --apply  Propose the suggested crew (owner only)
  --json   Print the suggestion as JSON
  --help   Show this message and exit.

Example:
  mc missions match 1
Usage: mc missions create --name NAME --start YYYY-MM-DD --end YYYY-MM-DD
                          --slot SPEC [--owner EMAIL] [--json]

  Create a draft mission with one or more slots. Repeat --slot for each.

Options:
  --name NAME         The mission's name  [required]
  --start YYYY-MM-DD  First day  [required]
  --end YYYY-MM-DD    Last day  [required]
  --slot SPEC         NAME:HEADCOUNT:SKILL>=LEVEL,... e.g.
                      Commander:1:Piloting>=4,Leadership>=3  [required]
  --owner EMAIL       The owning Lead (Directors create for a Lead)
  --json              Print the result as JSON
  --help              Show this message and exit.

Example:
  mc missions create --name "Europa Flyby" --start 2027-09-01 --end 2027-09-20 --slot "Commander:1:Piloting>=4,Leadership>=3"
mc 0.1.0
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/src/mission_control/cli && python3 - <<'EOF'
p='commands/common.py'
s=open(p).read()
s=s.replace('''def group(help: str, name: str | None = None) -> typer.Typer:''','''def group(help: str | None = None, name: str | None = None) -> typer.Typer:
    """A command group. Without `help`, its callback's docstring is the help."""''')
open(p,'w').write(s)
p='main.py'
s=open(p).read()
s=s.replace('''app = group("Mission Control: plan missions, crew them and get them approved.", name="mc")''','''app = group(name="mc")''')
s=s.replace('''    """Mission Control: plan missions, crew them and get them approved.

    Exit codes: 0 OK, 1 refused, 2 usage, 3 not logged in, 4 server unreachable or busy,
    130 interrupted.
    """''','''    """Mission Control: plan missions, crew them and get them approved.

    Start with mc login, then mc inbox. Every command has --help.

    Exit codes: 0 OK, 1 refused, 2 usage, 3 not logged in, 4 server unreachable or busy,
    130 interrupted.
    """''')
open(p,'w').write(s)
p='commands/account.py'
s=open(p).read()
s=s.replace('''    """Show what's waiting on you: proposals to answer, approvals to give, your missions."""''','''    """Show what's waiting on you.

    Proposals to answer, missions waiting for your approval, and your missions.
    """''')
open(p,'w').write(s)
EOF
cd ../../.. && uv run mc 2>&1 | head -12; echo "exit $?"
```

<details>
<summary>↳ Result</summary>

```
Usage: mc [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit
  --help     Show this message and exit.

Commands:
  login        Log in.
  logout       Log out and end this session on the server.
  whoami       Show who you're logged in as.
  password     Change your password.
  inbox        Show what's waiting on you.
exit 0
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && grep -n "def group" -A12 src/mission_control/cli/commands/common.py
```

<details>
<summary>↳ Result</summary>

```
61:def group(help: str | None = None, name: str | None = None) -> typer.Typer:
62-    """A command group. Without `help`, its callback's docstring is the help."""
63-    return typer.Typer(
64-        name=name,
65-        cls=Group,
66-        help=help,
67-        rich_markup_mode=None,
68-        add_completion=False,
69-        pretty_exceptions_enable=False,
70-    )
71-
72-
73-def start(ctx: typer.Context, json_output: bool = False) -> Env:
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='src/mission_control/cli/commands/common.py'
s=open(p).read()
s=s.replace('''    """A command group. Without `help`, its callback's docstring is the help."""
    return typer.Typer(
        name=name,
        cls=Group,
        help=help,
        rich_markup_mode=None,
        add_completion=False,
        pretty_exceptions_enable=False,
    )''','''    """A command group. Without `help`, its callback's docstring is the help."""
    named: dict[str, str] = {"help": help} if help else {}
    if name:
        named["name"] = name
    return typer.Typer(
        cls=Group,
        rich_markup_mode=None,
        add_completion=False,
        pretty_exceptions_enable=False,
        **named,
    )''')
open(p,'w').write(s)
EOF
uv run mc 2>&1 | head -12
```

<details>
<summary>↳ Result</summary>

```
Usage: mc [OPTIONS] COMMAND [ARGS]...

  Mission Control: plan missions, crew them and get them approved.

  Start with mc login, then mc inbox. Every command has --help.

  Exit codes: 0 OK, 1 refused, 2 usage, 3 not logged in, 4 server unreachable
  or busy, 130 interrupted.

Options:
  --version  Show the version and exit
  --help     Show this message and exit.
```

</details>

**🔧 Bash**

```bash
mkdir -p /tmp/m16stub && cat > /tmp/m16stub/stub.py <<'EOF'
"""Throwaway stand-in for the M15 API, shaped like design section 7, for a real `mc` run."""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()
P = "/api/v1"
TOKENS = {}


def err(status, code, message, problems=None):
    return JSONResponse({"error": {"code": code, "message": message,
                                   "problems": problems or [{"code": code, "message": message, "refs": {}}]}}, status)


def who(request):
    auth = request.headers.get("authorization", "")
    return TOKENS.get(auth.removeprefix("Bearer "))


@app.post(P + "/auth/login")
async def login(request: Request):
    body = await request.json()
    if body["password"] != "orbital launch window":
        return err(401, "invalid_credentials", "Email or password is incorrect")
    TOKENS["tok-" + body["email"]] = body["email"]
    return {"token": "tok-" + body["email"], "expires_at": "2099-01-01T00:00:00Z"}


@app.post(P + "/auth/logout")
async def logout(request: Request):
    TOKENS.pop(request.headers.get("authorization", "").removeprefix("Bearer "), None)
    return Response(status_code=204)


@app.get(P + "/me")
async def me(request: Request):
    if not who(request):
        return err(401, "unauthenticated", "Your session has ended")
    return {"id": 4, "email": who(request), "name": "Lee Park", "role": "lead", "is_active": True,
            "crew_profile_id": None, "organisation": {"id": 1, "name": "Aurora Space Agency"}}


S2 = {"mission": {"id": 1, "name": "Lunar Gateway Resupply", "start_date": "2027-03-01", "end_date": "2027-03-10"},
      "can_apply": True, "open_places": 3, "unfilled_places": 0, "slots": [
          {"slot_id": 1, "name": "Flight Engineer", "open_places": 1, "unfilled": 0,
           "suggested": [{"crew_profile_id": 8, "name": "Chen", "workload": 5, "proficiency": 3, "pick": 2}]},
          {"slot_id": 2, "name": "Mission Specialist", "open_places": 1, "unfilled": 0,
           "suggested": [{"crew_profile_id": 9, "name": "Dana", "workload": 5, "proficiency": 4, "pick": 3}]},
          {"slot_id": 3, "name": "Commander", "open_places": 1, "unfilled": 0,
           "suggested": [{"crew_profile_id": 6, "name": "Ana", "workload": 0, "proficiency": 9, "pick": 1}]}]}
S3 = {"mission": {"id": 2, "name": "Asteroid Survey", "start_date": "2027-03-05", "end_date": "2027-03-12"},
      "can_apply": True, "open_places": 2, "unfilled_places": 1, "slots": [
          {"slot_id": 4, "name": "Pilot", "open_places": 1, "unfilled": 0,
           "suggested": [{"crew_profile_id": 6, "name": "Ana", "workload": 0, "proficiency": 5, "pick": 1}]},
          {"slot_id": 5, "name": "Geologist", "open_places": 1, "unfilled": 1, "suggested": []}]}


@app.get(P + "/missions/{mid}/match")
async def match(mid: int, request: Request):
    if not who(request):
        return err(401, "unauthenticated", "Your session has ended")
    if mid == 1:
        return S2
    if mid == 2:
        return S3
    if mid == 5:
        return err(409, "mission_frozen", "Can't suggest crew for an active mission")
    return err(404, "not_found", "Mission not found")


@app.post(P + "/missions/{mid}/submit")
async def submit(mid: int, request: Request):
    return err(409, "rule_violation", "Mission can't be submitted", [
        {"code": "slot_unfilled", "message": "Flight Engineer: 1 place unfilled", "refs": {"slot_id": 1}},
        {"code": "slot_unfilled", "message": "Commander: 1 place unfilled", "refs": {"slot_id": 3}},
        {"code": "insufficient_approvers", "message": "1 eligible approver, 2 required", "refs": {}}])


MISSIONS = [{"id": i, "name": f"Mission {i:03d}", "start_date": "2027-03-01", "end_date": "2027-03-10",
             "status": "draft", "owner_id": 4, "owner_name": "Lee Park"} for i in range(1, 3001)]


@app.get(P + "/missions")
async def missions(request: Request):
    return MISSIONS


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8016, log_level="warning")
EOF
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && echo ok
```

**🔧 Bash**

```bash
cd /tmp/m16stub && /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/python -I /tmp/m16stub/stub.py
```

```json
{
  "run_in_background": true
}
```

<details>
<summary>↳ Result</summary>

```
ok
```

</details>

<details>
<summary>↳ Result</summary>

```
Command running in background with ID: br8ave8fz. Output is being written to: /private/tmp/claude-501/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tasks/br8ave8fz.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; directory changes made by the backgrounded command do not apply to subsequent commands.
```

</details>

**🔧 Bash**

```bash
sleep 2; export HOME=/tmp/m16home MC_API_URL=http://127.0.0.1:8016; MC=/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/mc; mkdir -p $HOME
echo '$ mc whoami   (not logged in)'; $MC whoami; echo "exit $?"
echo '$ echo "wrong" | mc login --email lee@aurora.example'; echo "wrong" | $MC login --email lee@aurora.example; echo "exit $?"
echo '$ echo "orbital launch window" | mc login --email lee@aurora.example'; echo "orbital launch window" | $MC login --email lee@aurora.example; echo "exit $?"
ls -l $HOME/.config/mission-control/; stat -f "%Sp %N" $HOME/.config/mission-control
echo '$ mc whoami'; $MC whoami; echo "exit $?"
echo '$ mc missions match 1  | cat'; $MC missions match 1 | cat; echo "exit $?"
echo '$ mc missions match 2 2>/dev/null'; $MC missions match 2 2>/dev/null; echo "exit $?"
echo '$ NO_COLOR=1 mc missions match 2'; NO_COLOR=1 $MC missions match 2; echo "exit $?"
echo '$ mc missions match 5'; $MC missions match 5; echo "exit $?"
echo '$ mc missions match 5 --json'; $MC missions match 5 --json; echo "exit $?"
echo '$ mc missions match 9'; $MC missions match 9; echo "exit $?"
echo '$ mc missions submit 1'; $MC missions submit 1; echo "exit $?"
echo '$ mc missions match abc'; $MC missions match abc; echo "exit $?"
```

<details>
<summary>↳ Result</summary>

```
$ mc whoami   (not logged in)
✗ You're not logged in.
  Log in: mc login
exit 3
$ echo "wrong" | mc login --email lee@aurora.example
✗ Email or password is incorrect.
exit 3
$ echo "orbital launch window" | mc login --email lee@aurora.example
Next: mc inbox
✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts 633092 hours.
exit 0
total 8
-rw-------@ 1 pritanbarai  wheel  104 Oct 12 14:42 credentials.json
drwx------ /tmp/m16home/.config/mission-control
$ mc whoami
Name           Lee Park
Email          lee@aurora.example
Role           Mission Lead
Organisation   Aurora Space Agency
Crew profile   none
exit 0
$ mc missions match 1  | cat
Next: mc missions match 1 --apply    proposes Ana, Chen and Dana
Lunar Gateway Resupply · 1–10 Mar 2027 · Draft
✓ Crew suggested for all 3 open places. Nothing has been proposed yet.

  Slot                 Suggested   Workload   Proficiency   Pick
  Flight Engineer      Chen        5 days     3             2
  Mission Specialist   Dana        5 days     4             3
  Commander            Ana         0 days     9             1

  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload
  wins, then highest proficiency (sum of the required skill levels).
exit 0
$ mc missions match 2 2>/dev/null
Asteroid Survey · 5–12 Mar 2027 · Draft
! Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.

  Slot        Suggested   Workload   Proficiency   Pick
  Pilot       Ana         0 days     5             1
  Geologist   unfilled (1 place)

  The mission can't be submitted until every place is filled.
exit 0
$ NO_COLOR=1 mc missions match 2
Next: mc missions match 2 --apply    proposes Ana for Pilot
      mc missions propose 2 --slot Geologist --crew EMAIL    fill Geologist by hand
Asteroid Survey - 5-12 Mar 2027 - Draft
Note: Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.

  Slot        Suggested   Workload   Proficiency   Pick
  Pilot       Ana         0 days     5             1
  Geologist   unfilled (1 place)

  The mission can't be submitted until every place is filled.
exit 0
$ mc missions match 5
✗ Mission 5: Can't suggest crew for an active mission.
  Only draft missions can be matched. See its crew: mc missions show 5
exit 1
$ mc missions match 5 --json
{
  "error": {
    "code": "mission_frozen",
    "message": "Can't suggest crew for an active mission",
    "problems": [
      {
        "code": "mission_frozen",
        "message": "Can't suggest crew for an active mission",
        "refs": {}
      }
    ]
  }
}
exit 1
$ mc missions match 9
✗ Mission 9 not found.
  See your missions: mc missions list
exit 1
$ mc missions submit 1
✗ Mission can't be submitted.
  • Flight Engineer: 1 place unfilled
  • Commander: 1 place unfilled
  • 1 eligible approver, 2 required
  Fill the open places: mc missions match 1
exit 1
$ mc missions match abc
Usage: mc missions match MISSION_ID [--apply] [--json]
Try 'mc missions match --help' for help.

Error: Invalid value for 'MISSION_ID': 'abc' is not a valid int.
exit 2
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='src/mission_control/cli/render.py'
s=open(p).read()
s=s.replace('''    def say(self, text: str = "") -> None:
        self.err.write(text + "\\n")''','''    def say(self, text: str = "") -> None:
        self.out.flush()  # keep data and messages in order when stdout is a pipe
        self.err.write(text + "\\n")
        self.err.flush()''')
open(p,'w').write(s)
EOF
export HOME=/tmp/m16home MC_API_URL=http://127.0.0.1:8016; MC=/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/mc
echo '$ mc missions match 1 | cat'; $MC missions match 1 | cat; echo "exit $?"
echo '$ mc missions list | head -3'; $MC missions list | head -3; echo "exit ${pipestatus[1]} (mc)"
echo '$ mc missions list --json | head -4'; $MC missions list --json | head -4; echo "exit ${pipestatus[1]} (mc)"
echo '$ mc missions cancel 1 --reason test < /dev/null'; $MC missions cancel 1 --reason test < /dev/null; echo "exit $?"
echo '$ mc logout'; $MC logout; echo "exit $?"; ls $HOME/.config/mission-control/
echo '$ mc logout (again)'; $MC logout; echo "exit $?"
echo '$ MC_API_URL=http://127.0.0.1:8099 mc login --email lee@aurora.example <<< pw'; MC_API_URL=http://127.0.0.1:8099 $MC login --email lee@aurora.example <<< "pw"; echo "exit $?"
echo '$ mc login < /dev/null'; $MC login < /dev/null; echo "exit $?"
```

<details>
<summary>↳ Result</summary>

```
$ mc missions match 1 | cat
Next: mc missions match 1 --apply    proposes Ana, Chen and Dana
Lunar Gateway Resupply · 1–10 Mar 2027 · Draft
✓ Crew suggested for all 3 open places. Nothing has been proposed yet.

  Slot                 Suggested   Workload   Proficiency   Pick
  Flight Engineer      Chen        5 days     3             2
  Mission Specialist   Dana        5 days     4             3
  Commander            Ana         0 days     9             1

  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload
  wins, then highest proficiency (sum of the required skill levels).
exit 0
$ mc missions list | head -3
  ID     Mission        Dates           Status   Owner
  1      Mission 001    1–10 Mar 2027   Draft    Lee Park
  2      Mission 002    1–10 Mar 2027   Draft    Lee Park
exit 1 (mc)
$ mc missions list --json | head -4
[
  {
    "id": 1,
    "name": "Mission 001",
exit 1 (mc)
$ mc missions cancel 1 --reason test < /dev/null
✗ The server sent an unexpected response (HTTP 404).
  Try again. If it keeps happening, check the server's log.
exit 1
$ mc logout
✓ Logged out.
exit 0
$ mc logout (again)
✓ You're not logged in.
exit 0
$ MC_API_URL=http://127.0.0.1:8099 mc login --email lee@aurora.example <<< pw
✗ Can't reach the Mission Control server at http://127.0.0.1:8099.
  Is it running? Start it with: uv run mc-server
exit 4
$ mc login < /dev/null
✗ No email given, and there's no terminal to ask on. Pass --email, and pipe the password on stdin.
exit 2
```

</details>

<details>
<summary>✏️ User edited None</summary>

```

```

</details>

**🔧 Bash**

```bash
cd /tmp/m16stub && python3 - <<'EOF'
p='stub.py'
s=open(p).read()
s=s.replace('''@app.get(P + "/missions")''','''@app.get(P + "/missions/1")
async def gateway(request: Request):
    return {"id": 1, "name": "Lunar Gateway Resupply", "start_date": "2027-03-01", "end_date": "2027-03-10",
            "status": "pending_approval", "owner_id": 4, "owner_name": "Lee Park", "created_by_id": 1,
            "created_by_name": "Ruth Adeyemi", "approval_round": 1, "approvals_required": 2,
            "slots": [{"id": 1, "position": 1, "name": "Flight Engineer", "headcount": 1, "open_places": 0,
                       "requirements": [{"skill_id": 3, "skill_name": "Systems Engineering", "min_level": 3}]}],
            "assignments": [{"id": 22, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,
                             "crew_name": "Chen Wu", "status": "accepted", "reason": None}],
            "approvals": [{"director_id": 2, "director_name": "Marco Bianchi", "decision": "approve", "reason": None}]}


@app.get(P + "/missions")''')
open(p,'w').write(s)
EOF
pkill -f m16stub/stub.py; sleep 1; echo restarted
```

**🔧 Bash**

```bash
cd /tmp/m16stub && /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/python -I /tmp/m16stub/stub.py
```

```json
{
  "run_in_background": true
}
```

<details>
<summary>↳ Result</summary>

```
restarted
```

</details>

<details>
<summary>↳ Result</summary>

```
Command running in background with ID: bei37btny. Output is being written to: /private/tmp/claude-501/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tasks/bei37btny.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control; directory changes made by the backgrounded command do not apply to subsequent commands.
```

</details>

**👤 User (sent while Claude was working):**

<task-notification>
<task-id>br8ave8fz</task-id>
<tool-use-id>toolu_014X891ZQCUT6tBWzpAToASW</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tasks/br8ave8fz.output</output-file>
<status>failed</status>
<summary>Background command "cd /tmp/m16stub &amp;&amp; /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/python -I /tmp/m16stub/stub.py" failed with exit code 144</summary>
</task-notification>

**🔧 Bash**

```bash
sleep 2; export HOME=/tmp/m16home MC_API_URL=http://127.0.0.1:8016; MC=/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/mc
echo "orbital launch window" | $MC login --email lee@aurora.example >/dev/null 2>&1
echo '$ mc missions show 1'; $MC missions show 1; echo "exit $?"
echo '$ mc missions cancel 1 --reason test < /dev/null'; $MC missions cancel 1 --reason test < /dev/null; echo "exit $?"
echo '$ mc missions slot remove 1 Pilot < /dev/null'; $MC missions slot remove 1 Pilot < /dev/null; echo "exit $?"
echo '$ mc missions create --name X --start 1-Sep --end 2027-09-02 --slot "Cmdr:1:Piloting>=4"'; $MC missions create --name X --start 1-Sep --end 2027-09-02 --slot "Cmdr:1:Piloting>=4"; echo "exit $?"
echo '$ mc missions create --name X --start 2027-09-01 --end 2027-09-02 --slot "Commander-1"'; $MC missions create --name X --start 2027-09-01 --end 2027-09-02 --slot "Commander-1"; echo "exit $?"
echo '$ Ctrl+C during mc login (stdin waiting on a fifo, SIGINT sent)'
rm -f /tmp/m16stub/fifo; mkfifo /tmp/m16stub/fifo
( sleep 5 > /tmp/m16stub/fifo & ); $MC login --email lee@aurora.example < /tmp/m16stub/fifo & PID=$!; sleep 1.5; kill -INT $PID; wait $PID; echo "exit $?"
```

<details>
<summary>↳ Result</summary>

```
$ mc missions show 1
Lunar Gateway Resupply · 1–10 Mar 2027 · Pending approval
Owner Lee Park · created by Ruth Adeyemi

  #   Slot              Requires                 Places
  1   Flight Engineer   Systems Engineering>=3   full

  Assignment   Crew      Slot              Status
  22           Chen Wu   Flight Engineer   accepted

Approvals: 1 of 2 (Marco Bianchi)
exit 0
$ mc missions cancel 1 --reason test < /dev/null
! Cancelling Lunar Gateway Resupply can't be undone. Its open assignments will be cancelled too.
✗ There's no terminal to confirm on.
  Re-run with --yes to go ahead.
exit 2
$ mc missions slot remove 1 Pilot < /dev/null
✗ Lunar Gateway Resupply has no slot called 'Pilot'.
  Its slots: 1 Flight Engineer
exit 1
$ mc missions create --name X --start 1-Sep --end 2027-09-02 --slot "Cmdr:1:Piloting>=4"
Usage: mc missions create --name NAME --start YYYY-MM-DD --end YYYY-MM-DD
                          --slot SPEC [--owner EMAIL] [--json]
Try 'mc missions create --help' for help.

Error: Invalid value for '--start': '1-Sep' isn't a date. Use YYYY-MM-DD, e.g. 2027-03-01.
exit 2
$ mc missions create --name X --start 2027-09-01 --end 2027-09-02 --slot "Commander-1"
✗ 'Commander-1' isn't a slot. Use NAME:HEADCOUNT:SKILL>=LEVEL[,SKILL>=LEVEL...], e.g. Commander:1:Piloting>=4,Leadership>=3.
exit 2
$ Ctrl+C during mc login (stdin waiting on a fifo, SIGINT sent)
✗ No password given, and there's no terminal to ask on.
  Run this in a terminal, or pipe it on stdin.
exit 2
```

</details>

**🔧 Bash**

```bash
cat > /tmp/m16stub/ctrlc.py <<'EOF'
"""Run `mc` in a pseudo-terminal, press Ctrl+C at a prompt, and report what happened."""
import os, pty, sys, time
argv = sys.argv[1:]
pid, fd = pty.fork()
if pid == 0:
    os.execv(argv[0], argv)
out = b""
deadline = time.time() + 10
while time.time() < deadline and b":" not in out:
    out += os.read(fd, 1024)
os.write(fd, b"\x03")  # Ctrl+C, turned into SIGINT by the line discipline
time.sleep(0.5)
try:
    while True:
        chunk = os.read(fd, 1024)
        if not chunk:
            break
        out += chunk
except OSError:
    pass
_, status = os.waitpid(pid, 0)
print(out.decode(errors="replace").replace("\r", ""))
print("exit", os.waitstatus_to_exitcode(status))
EOF
export HOME=/tmp/m16home MC_API_URL=http://127.0.0.1:8016; MC=/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/mc
echo '$ mc login   (Ctrl+C at the Email prompt, in a real pty)'; python3 -I /tmp/m16stub/ctrlc.py $MC login
echo '$ mc login --email lee@aurora.example   (Ctrl+C at the hidden Password prompt)'; python3 -I /tmp/m16stub/ctrlc.py $MC login --email lee@aurora.example
echo '$ mc missions cancel 1 --reason test   (Ctrl+C at the confirmation)'; python3 -I /tmp/m16stub/ctrlc.py $MC missions cancel 1 --reason test
echo '$ mc missions match 1  (on a pty: colour)'; python3 - <<'EOF'
import os, pty
pid, fd = pty.fork()
if pid == 0:
    os.environ["TERM"]="xterm-256color"
    os.execv("/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/mc", ["mc","missions","match","1"])
out=b""
try:
    while (c := os.read(fd, 4096)): out += c
except OSError: pass
os.waitpid(pid,0)
print(repr(out.decode().split("\r\n")[1]))
EOF
```

<details>
<summary>↳ Result</summary>

```
$ mc login   (Ctrl+C at the Email prompt, in a real pty)
Email: ^C
Cancelled.

exit 130
$ mc login --email lee@aurora.example   (Ctrl+C at the hidden Password prompt)
Password: 
Cancelled.

exit 130
$ mc missions cancel 1 --reason test   (Ctrl+C at the confirmation)
[33m![0m Cancelling Lunar Gateway Resupply can't be undone. Its open assignments will be cancelled too.
Cancel Lunar Gateway Resupply? [y/N]: ^C
Cancelled.

exit 130
$ mc missions match 1  (on a pty: colour)
'\x1b[32m✓\x1b[0m Crew suggested for all 3 open places. Nothing has been proposed yet.'
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && uv run python -c "
from fastapi.testclient import TestClient
from mission_control.api.app import create_app
from mission_control.cli.client import Api, ApiError
api = Api(TestClient(create_app()), token='t')
try: api.get('/me')
except ApiError as e: print('TestClient works as the http client ->', e.status, e.code)
"
```

<details>
<summary>↳ Result</summary>

```
TestClient works as the http client -> 404 unexpected_response
```

</details>

### 🤖 Claude · 2026-10-12 03:43:30 UTC

Real runs behave as designed. Now a read-only self-review of the full diff.

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && git status --short && git diff --stat && wc -l src/mission_control/cli/*.py src/mission_control/cli/commands/*.py tests/cli/*.py && cat src/mission_control/cli/refusals.py src/mission_control/cli/commands/common.py
```

<details>
<summary>↳ Result</summary>

```
 M pyproject.toml
 M uv.lock
?? src/mission_control/cli/
?? tests/cli/
 pyproject.toml |  5 ++++-
 uv.lock        | 66 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++--
 2 files changed, 68 insertions(+), 3 deletions(-)
       2 src/mission_control/cli/__init__.py
     158 src/mission_control/cli/client.py
      73 src/mission_control/cli/config.py
      61 src/mission_control/cli/env.py
      47 src/mission_control/cli/errors.py
      70 src/mission_control/cli/main.py
      80 src/mission_control/cli/prompts.py
     102 src/mission_control/cli/refusals.py
     227 src/mission_control/cli/render.py
     123 src/mission_control/cli/resolve.py
      93 src/mission_control/cli/views.py
       1 src/mission_control/cli/commands/__init__.py
     171 src/mission_control/cli/commands/account.py
     228 src/mission_control/cli/commands/admin.py
     126 src/mission_control/cli/commands/assignments.py
     101 src/mission_control/cli/commands/common.py
     107 src/mission_control/cli/commands/crew.py
     145 src/mission_control/cli/commands/me.py
     757 src/mission_control/cli/commands/missions.py
     340 tests/cli/cli_fakes.py
      19 tests/cli/conftest.py
     240 tests/cli/test_cli_auth.py
      71 tests/cli/test_cli_config.py
     204 tests/cli/test_cli_errors.py
     211 tests/cli/test_cli_match.py
     594 tests/cli/test_cli_missions.py
      64 tests/cli/test_cli_parsing.py
     502 tests/cli/test_cli_people.py
     135 tests/cli/test_cli_render.py
     333 tests/cli/test_cli_scenarios.py
    5385 total
"""Turning a refusal into what the user reads: the message, one bullet per problem that adds
something, and a next step for the codes we know."""

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass

from mission_control.cli.client import ApiError, Unreachable
from mission_control.cli.env import Env
from mission_control.cli.errors import INTERRUPTED, UNAVAILABLE, CliError
from mission_control.cli.render import sentence

# A mission's state stopped the action. The message says "a mission", so the CLI adds which one.
STATE_CODES = frozenset({"mission_frozen", "mission_final", "invalid_transition"})

GENERIC_HINTS = {
    "unauthenticated": "Log in again: mc login",
    "busy": "Try again in a moment.",
    "unexpected_response": "Try again. If it keeps happening, check the server's log.",
}


@dataclass(frozen=True)
class Shown:
    message: str
    bullets: tuple[str, ...]
    hints: tuple[str, ...]


@contextmanager
def refusals(
    subject: str | None = None, *, name_state: bool = False, **hints: str
) -> Generator[None]:
    """Give refusals raised inside the block the context only the command knows: the `subject`
    (e.g. "Mission 5") for a not-found message, whether a state refusal should name it, and a
    hint per code. A hint may use `{name}` placeholders filled from the problem's refs."""
    try:
        yield
    except ApiError as error:
        if error.subject is None:
            error.subject = subject
            error.name_state = name_state
        error.hints = hints | error.hints
        raise


def present(error: ApiError) -> Shown:
    message = error.message
    subject = error.subject
    if subject:
        kind = subject.split()[0]
        if error.code == "not_found" and message.lower() == f"{kind} not found".lower():
            message = f"{subject} not found"
        elif error.code in STATE_CODES and error.name_state:
            message = f"{subject}: {message}"

    bullets = tuple(p.message for p in error.problems if p.message and p.message != error.message)

    hints: list[str] = []
    for code, refs in ((error.code, {}), *((p.code, p.refs) for p in error.problems)):
        hint = _fill(error.hints.get(code) or GENERIC_HINTS.get(code), refs)
        if hint and hint not in hints:
            hints.append(hint)
    return Shown(sentence(message), bullets, tuple(hints))


def _fill(template: str | None, refs: Mapping[str, object]) -> str | None:
    """A hint may name a record from the problem's refs, e.g. `{assignment_id}`. Without that
    ref the hint is skipped rather than shown half-filled."""
    if template is None:
        return None
    try:
        return template.format_map(dict(refs))
    except (KeyError, IndexError, ValueError):
        return None


def report(env: Env, failure: BaseException) -> int:
    """Show a failure on stderr (or a refusal's error body on stdout, with `--json`) and return
    the exit code to use."""
    term = env.term
    if isinstance(failure, KeyboardInterrupt):
        term.say()
        term.say("Cancelled.")
        return INTERRUPTED
    if isinstance(failure, Unreachable):
        term.error(
            f"Can't reach the Mission Control server at {failure.url}.",
            hint="Is it running? Start it with: uv run mc-server",
        )
        return UNAVAILABLE
    if isinstance(failure, ApiError):
        if env.json_output and failure.has_error_body:
            term.json(failure.body)
        else:
            shown = present(failure)
            term.error(shown.message, shown.bullets, shown.hints)
        return failure.exit_code
    if isinstance(failure, CliError):
        term.error(sentence(failure.message), failure.bullets, failure.hint)
        return failure.exit_code
    raise failure
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
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && export HOME=/tmp/m16home MC_API_URL=http://127.0.0.1:8016; grep -rnE "AC-[0-9]|\bM[0-9]{1,2}\b|§|PRD" src/mission_control/cli; echo "(no PRD refs above)"; uv run mc assignments withdraw 3; echo "exit $?"; uv run mc users set-role a@b captain; echo "exit $?"; uv run mc missions cancel --help
```

<details>
<summary>↳ Result</summary>

```
(no PRD refs above)
Usage: mc assignments withdraw ASSIGNMENT_ID --reason TEXT [--yes] [--json]
Try 'mc assignments withdraw --help' for help.

Error: Missing option '--reason'.
exit 2
Usage: mc users set-role EMAIL ROLE [--json]
Try 'mc users set-role --help' for help.

Error: Invalid value for 'ROLE': 'captain' is not one of 'director', 'lead', 'crew'.
exit 2
Usage: mc missions cancel MISSION_ID --reason TEXT [--yes] [--json]

  Cancel a mission that isn't finished. Owner or Director. Asks first.

Arguments:
  MISSION_ID  The mission's ID  [required]

Options:
  --reason TEXT  Why (recorded in the history)  [required]
  -y, --yes      Don't ask for confirmation
  --json         Print the result as JSON
  --help         Show this message and exit.

Example:
  mc missions cancel 1 --reason "Budget cut"
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && grep -n "import" src/mission_control/cli/commands/account.py src/mission_control/cli/commands/assignments.py | head -30; grep -n "noqa\|ANN202" -r src/mission_control/cli
```

<details>
<summary>↳ Result</summary>

```
src/mission_control/cli/commands/assignments.py:3:from typing import Annotated, Any
src/mission_control/cli/commands/assignments.py:5:import typer
src/mission_control/cli/commands/assignments.py:7:from mission_control.cli.client import Api
src/mission_control/cli/commands/assignments.py:8:from mission_control.cli.commands.common import Json, Yes, command, group, start
src/mission_control/cli/commands/assignments.py:9:from mission_control.cli.prompts import confirm
src/mission_control/cli/commands/assignments.py:10:from mission_control.cli.refusals import refusals
src/mission_control/cli/commands/assignments.py:11:from mission_control.cli.views import assignment_summary_rows
src/mission_control/cli/commands/account.py:3:from datetime import UTC, datetime
src/mission_control/cli/commands/account.py:4:from typing import Annotated
src/mission_control/cli/commands/account.py:6:import typer
src/mission_control/cli/commands/account.py:8:from mission_control.cli.client import ApiError
src/mission_control/cli/commands/account.py:9:from mission_control.cli.commands.common import Json, command, start
src/mission_control/cli/commands/account.py:10:from mission_control.cli.config import Credentials
src/mission_control/cli/commands/account.py:11:from mission_control.cli.prompts import ask, ask_new_secret, ask_secret
src/mission_control/cli/commands/account.py:12:from mission_control.cli.refusals import refusals
src/mission_control/cli/commands/account.py:13:from mission_control.cli.render import ROLE, Terminal, plural
src/mission_control/cli/commands/account.py:14:from mission_control.cli.views import identity, mission_row, org_name
src/mission_control/cli/commands/assignments.py:20:def _refusals(assignment_id: int):  # noqa: ANN202
```

</details>

**🔧 Bash**

```bash
cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && python3 - <<'EOF'
p='src/mission_control/cli/commands/assignments.py'
s=open(p).read()
s=s.replace("def _refusals(assignment_id: int):  # noqa: ANN202","def _refusals(assignment_id: int) -> AbstractContextManager[None]:")
s=s.replace("from typing import Annotated, Any\n","from contextlib import AbstractContextManager\nfrom typing import Annotated, Any\n")
open(p,'w').write(s)
EOF
uv run ruff check && uv run ruff format --check | tail -1 && uv run pytest 2>&1 | tail -1
```

<details>
<summary>↳ Result</summary>

```
All checks passed!
109 files already formatted
1289 passed in 6.70s
```

</details>

**🔧 Bash**

```bash
pkill -f m16stub/stub.py; rm -rf /tmp/m16home /tmp/m16stub /tmp/m16probe; cd /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli && git status --short && git diff pyproject.toml | grep "^[+-]"
```

<details>
<summary>↳ Result</summary>

```
 M pyproject.toml
 M uv.lock
?? src/mission_control/cli/
?? tests/cli/
--- a/pyproject.toml
+++ b/pyproject.toml
+    "httpx2>=2.13",
+    "rich>=13",
+    "typer>=0.12",
+mc = "mission_control.cli.main:main"
-    "httpx2>=2.13",
```

</details>

**👤 User (sent while Claude was working):**

<task-notification>
<task-id>bei37btny</task-id>
<tool-use-id>toolu_01Y5oSDrUJpKTV4qopKNPrhk</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-pritanbarai-Desktop-JOBS-mutinex-mission-control/6c4baffc-0101-4fc8-a4a8-d54a1fd1d1c3/tasks/bei37btny.output</output-file>
<status>failed</status>
<summary>Background command "cd /tmp/m16stub &amp;&amp; /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli/.venv/bin/python -I /tmp/m16stub/stub.py" failed with exit code 144</summary>
</task-notification>

**🔧 SubagentHandback**

````json
{
  "message": "## M16 (CLI, `mc`): hand-off\n\nEverything is uncommitted in `/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/.worktrees/m16-cli` on branch `m16-cli`. Nothing is committed or pushed.\n\n**Results:** 1289 tests pass on the whole worktree, 148 of them new CLI tests. `uv run ruff check` and `uv run ruff format --check` both pass. The `mc` binary was run for real against a throwaway API stub on port 8016 (outside the repo). It used `HOME=/tmp/m16home`, so the real home directory wasn't touched, and it has been deleted.\n\n### Files\n- **Changed:** `pyproject.toml` adds one line to `[project.scripts]`: `mc = \"mission_control.cli.main:main\"`. `uv.lock` was already modified and I left it as it was.\n- **New, in `src/mission_control/cli/`:**\n  - `main.py`: the app, `--version`, and a quiet exit on a broken pipe.\n  - `client.py`: the httpx2 `Api` wrapper, `ApiError` and `Unreachable`.\n  - `config.py`: the credentials store.\n  - `env.py`: the per-run object that tests inject.\n  - `errors.py`: the exit codes.\n  - `prompts.py`: hidden prompts and confirmations.\n  - `refusals.py`: turns errors into message, bullets and hints, and maps them to exit codes.\n  - `render.py`: dates, tables, markers, colour detection.\n  - `resolve.py`: the `--slot` parser and reference resolution.\n  - `views.py`: shared screen layouts.\n  - `commands/`: `common.py`, `account.py`, `me.py`, `assignments.py`, `missions.py`, `crew.py`, `admin.py`.\n- **New, in `tests/cli/`:** `cli_fakes.py` (a `FakeApi` over `httpx2.MockTransport`, the in-process runner and a scripted prompter), `conftest.py`, and test files for parsing, render, config, auth, errors, match, missions, people and scenarios (S1 and S4).\n\nThe CLI imports only `mission_control.cli.*`; I checked with grep. It doesn't use `click`, because typer 0.27 vendors its own copy, so commands take `typer.Context` instead. httpx2 is the only HTTP library. There are no PRD, AC or § references anywhere in `src/`.\n\n### Commands built\nEverything in design §8:\n- **Everyone:** `login`, `logout`, `whoami`, `password`, `inbox`.\n- **Profile:** `me show`, `me update`, `me unavailable add|list|remove`.\n- **Assignments:** `assignments list [--pending]`, `accept`, `decline`, `withdraw --reason`.\n- **Missions:** `create`, `list`, `show`, `history`, `edit`, `slot add|edit|remove`, `match [--apply]`, `propose`, `remove-crew`, `submit`, `approve`, `reject`, `transfer`, `complete`, `cancel`.\n- **Crew:** `crew list|show|history|set-skill|unset-skill`.\n- **Directors:** `users list|add|set-role|deactivate|enable-crew`, `skills list|add|rename|remove`, `org show|set-approvals`.\n\nEvery command has `--help` with a usage line and an example, and data commands take `--json`. Commands that change a pending mission ask first and accept `--yes`; `cancel` always asks.\n\n### Real-run output (trimmed)\n```\n$ mc whoami                                  -> ✗ You're not logged in. / Log in: mc login       exit 3\n$ echo wrong | mc login --email lee@aurora.example -> ✗ Email or password is incorrect.          exit 3\n$ echo \"orbital launch window\" | mc login --email lee@aurora.example\n✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts … hours.  /  Next: mc inbox\ncredentials.json is -rw-------, its directory is drwx------\n$ mc missions match 1 | cat       -> the S2 table exactly as in docs/cli-ux.md, no escape codes; the Next: line went to stderr\n$ NO_COLOR=1 mc missions match 2  -> \"Asteroid Survey - 5-12 Mar 2027 - Draft\" / \"Note: Crew suggested for 1 of 2 …\"\n$ mc missions match 5             -> ✗ Mission 5: Can't suggest crew for an active mission. / Only draft missions can be matched. See its crew: mc missions show 5   exit 1\n$ mc missions match 5 --json      -> the §7 error body on stdout                                    exit 1\n$ mc missions match 9             -> ✗ Mission 9 not found. / See your missions: mc missions list\n$ mc missions submit 1            -> ✗ Mission can't be submitted. / • Flight Engineer: 1 place unfilled / • Commander: … / • 1 eligible approver, 2 required / Fill the open places: mc missions match 1\n$ mc missions match abc           -> Error: Invalid value for 'MISSION_ID': 'abc' is not a valid int.   exit 2\n$ mc missions cancel 1 --reason test < /dev/null -> ! Cancelling … can't be undone… / ✗ There's no terminal to confirm on. / Re-run with --yes to go ahead.   exit 2\n$ mc missions list | head -3      -> 3 lines, no traceback (exit 1, typer's broken-pipe handling)\n$ MC_API_URL=http://127.0.0.1:8099 mc login … -> ✗ Can't reach the Mission Control server at http://127.0.0.1:8099. / Is it running? Start it with: uv run mc-server   exit 4\nCtrl+C in a real pty at Email:, at the hidden Password: and at the confirm prompt -> \"Cancelled.\"  exit 130\nIn a pty, colour wraps only the marker: '\\x1b[32m✓\\x1b[0m Crew suggested …'\n```\nI also checked that Starlette's `TestClient` can be used directly as the CLI's http client.\n\n### §7 response shapes I assumed (check against M15)\n§7 doesn't define success bodies, so these are guesses based on the service dataclasses. All paths sit under `/api/v1`, and dates are ISO strings.\n- **`POST /auth/login`:** `{token, expires_at}`.\n- **`GET /me`:** `{id, email, name, role, is_active, crew_profile_id, organisation: {id, name}}`.\n- **Mission list:** each item has `{id, name, start_date, end_date, status, owner_id, …}`. `owner_name` is optional; the Owner column only appears when it's there.\n- **Mission view** (from `GET /missions/{id}`, and from every lifecycle and edit command): mission fields plus `owner_name`, `created_by_name`, `approvals_required`, and:\n  - `slots: [{id, position, name, headcount, open_places, requirements: [{skill_id, skill_name, min_level}]}]`\n  - `assignments: [{id, slot_id, slot_name, crew_profile_id, crew_name, status, reason}]`\n  - `approvals: [{director_id, director_name, decision, reason}]`\n- **`GET /missions/{id}/match`:** exactly the cli-ux.md JSON.\n- **`POST …/match/apply`:** a list of assignments (only `id` is relied on). The CLI then re-reads the mission view to get names.\n- **`GET /missions/{id}/history`:** `[{id, created_at, actor_id, actor_name, event, from_status, to_status, reason, data}]`. `data` holds the audit names (`crew_name`, `slot_name`, `to_owner_name`).\n- **`GET /assignments`** (`?pending=true`), `GET /crew/{id}/assignments`, and inbox `assignments`: `[{assignment_id, mission_id, mission_name, start_date, end_date, mission_status, slot_name, status, reason}]`.\n- **`GET /me/inbox`:** `{assignments, approvals: [mission], missions: [mission]}`.\n- **Crew:** `{crew_profile_id, user_id, name, email, active, bio, skills: [{skill_id, skill_name, level}], unavailability: [{id, start_date, end_date, reason|null}]}`.\n- **Skill:** `{id, name, category}`. **Org:** `{id, name, slug, required_approvals}`.\n- **Request bodies:**\n  - `POST /missions`: `{name, start_date, end_date, owner_id?, slots: [{name, headcount, requirements: [{skill_id, min_level}]}]}`\n  - `PATCH /missions/{id}`: `{name?, start_date?, end_date?}`\n  - Slot add and edit: `{name?, headcount?, requirements?}`\n  - Propose: `{slot_id, crew_profile_id}`\n  - `reject`, `cancel`, `withdraw`: `{reason}`. `decline`: `{reason}`, or no body.\n  - Transfer: `{owner_id}`\n  - Password change: `{current_password, new_password}`\n  - Add user: `{email, name, role, password}`\n  - Set role: `{role}`. Deactivate: `{is_active: false}`.\n  - Set skill: `PUT … {level}`. Set approvals: `{required_approvals}`.\n  - Edit profile: `PATCH /crew/{id} {display_name?, bio?}`. Add unavailability: `{start_date, end_date, reason}`.\n- **Other expectations:** DELETE may return 204. A response without the §7 error shape (for example a 500, or FastAPI's default 404) is shown as \"The server sent an unexpected response (HTTP n)\", exit 1.\n\n### cli-ux checklist findings (read-only self-review)\n- **Blocker:** none.\n- **Major:**\n  1. The S1 and S4 tests use a scripted stand-in for the API, not the real one. Once M15 lands they should be repointed at `TestClient` and `seeded_db`, which is what design §11 means by CLI tests.\n  2. Some response shapes above are guesses; mismatches will appear as `KeyError`s.\n- **Minor:**\n  1. Only the login email is prompted for when missing. Other required flags fail with exit 2 and click's \"Missing option '--reason'\".\n  2. There's no `--quiet`, and long table values aren't truncated to the terminal width.\n  3. `| head` exits 1, not 0.\n  4. `--json` on a DELETE that returns 204 prints `null`.\n  5. Logging in as another user doesn't revoke the previous token on the server.\n- **Works well; keep as is:**\n  - stdout carries data, stderr carries messages, hints and prompts, and stdout is flushed before each stderr line.\n  - The plain-word markers (`OK:`, `Note:`, `Error:`) with `NO_COLOR`, `TERM=dumb` or a non-UTF-8 terminal.\n  - A single-reason refusal is never printed twice; bullets that repeat the message are dropped.\n  - Mission refusals name the mission ID, and hints can fill in IDs from a problem's refs, e.g. `remove-crew 1 21`.\n  - The match output matches the mock sessions in docs/cli-ux.md byte for byte.\n  - Credentials are written atomically, mode 0600 in a 0700 directory, and cleared on logout, password change or a 401.\n\n### Open questions and decisions for you\n1. **`MC_API_URL`**: a new environment variable, defaulting to `http://127.0.0.1:8000`. The design has no way to point the CLI at another server; this follows the existing `MC_*` naming.\n2. **Piped passwords:** without a terminal, passwords are read from stdin, one line per prompt. They're never accepted as a flag. This is what makes scripts and tests possible, and the cli-ux skill's own example does it.\n3. **Refusal with `--json`:** the §7 error body goes to **stdout**, with the same exit code. This was the decision cli-ux.md left open. Errors the CLI finds itself (unknown email, not logged in, unreachable) stay as text on stderr.\n4. **Answering \"n\" to a confirmation** exits 1 (\"Nothing was changed.\"). With no terminal and no `--yes`, it exits 2.\n5. **Flags the design doesn't list:**\n   - `decline --reason` (optional), because PRD S3 allows an optional reason.\n   - `create --owner EMAIL`, for Directors.\n   - `slot add --slot SPEC`.\n   - `slot edit --name/--headcount/--requires \"Skill>=N,…\"`.\n   - `me update --name/--bio`.\n   - `--version`, and `-y` as a short form of `--yes`.\n6. **Confirmations:**\n   - Asked before: `edit`, every `slot` change, `propose`, `remove-crew`, `transfer` and `withdraw`, but only when the mission is pending approval. `cancel` always asks.\n   - No confirmation for `reject`, `users deactivate` or `skills remove`; the design lists only pending changes and cancelling.\n7. **`--reason` is required** by the CLI's own syntax for `withdraw`, `reject` and `cancel`, as §8 writes it. So S5's \"withdraw without a reason\" ends as a usage error (exit 2) before reaching the server.\n8. **Slot references:** a bare number always means the slot's position; anything else is matched by name, ignoring case.\n9. **`match --apply`** is available and has no \"available after M12\" marker, since M12 is merged. Full slots are left out of the match table.\n10. **`me show --json`** prints `{\"user\": …, \"crew_profile\": …}`, a shape I made up.\n11. **Other exit codes:** an unexpected 5xx exits 1, while 503 `busy` exits 4 with \"Try again in a moment.\" (no retry). A 422 from the server exits 1, because it's a refusal, not a usage error.\n12. **Mission history** shows times in UTC, in a \"When (UTC)\" column.\n\n### Proposed commit message\n```\nfeat(m16): mc CLI — every §8 command over the HTTP API, with prompts, confirmations, --json, and pipe-safe output\n\n- httpx2 Api wrapper passed in through Env (MockTransport or TestClient in tests)\n- credentials at ~/.config/mission-control/credentials.json (0600, atomic; cleared on logout, password change or 401)\n- references: missions and assignments by ID, people by email, skills by name, slots by name or position; --slot spec parser\n- refusals: the message, one bullet per extra problem, hints for known codes; exit codes 0/1/2/3/4/130\n- matcher preview rendered per docs/cli-ux.md; friendlier date ranges; NO_COLOR, TERM=dumb and non-UTF-8 fallbacks\n- tests: parsing, render, config, prompts, confirmations, errors, every command group, S1 and S4\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n```\n"
}
````

<details>
<summary>↳ Result</summary>

```
{"success":true,"message":"Report delivered to your caller."}
```

</details>
