# Subagent (01): Create shared test builders

Source: `agent-a26b2d5af52f2fbea.jsonl` · 2026-10-11 12:20:58 UTC → 2026-10-11 12:24:10 UTC

Rendered from the raw JSONL without editing message content. Tool results and thinking are collapsed; expand them to read.


---

### 👤 User · 2026-10-11 12:20:58 UTC

You are applying an approved TEST-ONLY refactor to a Python project. Repository: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control. No other agent is editing files now.

Scope: create `tests/builders.py` and update test files under `tests/unit/domain/` to use it. Do NOT edit anything under src/, docs/, pyproject.toml or CLAUDE.md. Do NOT run git commands that change state (no add, commit, stash, checkout, reset). Do NOT add dependencies. Verify with `uv run pytest -W error` (currently 458 passed) and `uv run ruff check src tests && uv run ruff format src tests`. When you finish, the test count must not go down: no tests deleted, renamed away or weakened. Same tests, same assertions, same expected values.

The problem (from a code-quality review):
- Test helpers and seed constants are copied across test files:
  - `tests/unit/domain/test_eligibility.py` defines skill ids `PILOTING, LEADERSHIP, SYS_ENG, EVA` with a `NAMES` dict, plus `req()`, `slot()`, `crew()` and `d()`.
  - `tests/unit/domain/test_matching.py` defines the same skill ids with a dict called `SKILL`, plus `req()`, `person()` and `rng()`, and the Aurora seed people (ANA, BEN, … with ids 6–13 in PRD §9 table order).
  - `tests/unit/domain/test_lifecycle.py` has its own `EVA` requirement, `slot()` and `entry()` building `CandidateFacts`/`RosterEntry` by hand.
  - `tests/unit/domain/test_dates.py` has `r()`.
- So `CandidateFacts` is built by hand in three files. When `CandidateFacts`/`SlotSpec`/`RosterEntry` gain a field in later modules, several files would have to change.
- Seed people also get inconsistent ids: Ana is 1 in the eligibility tests and 6 in the matching tests.
- docs/technical-design.md (§2 folder layout, §10 testing conventions) plans a `tests/builders.py` for focused fixtures. Read §10 and the records in src/mission_control/domain/records.py first.

What to do:
1. Create `tests/builders.py` with small keyword-friendly builders and constants:
   - `date_range(start: str, end: str) -> DateRange` (ISO strings).
   - Skill constants matching PRD §9.1 Aurora (read docs/prd.md §9.1): ids for Piloting, Leadership, Systems Eng, EVA, Geology, Flight Medicine, plus one read-only name lookup.
   - `req(skill_id, min_level) -> Requirement`, filling the name from the lookup.
   - `slot(*requirements, id=..., position=..., name=..., open_places=...) -> SlotSpec`, with sensible defaults.
   - `crew(name=..., id=..., active=True, skills=None, unavailable=(), accepted_elsewhere=(), workload=0) -> CandidateFacts`.
   - `commitment(mission_id, mission_name, start, end) -> Commitment`.
   - `roster_entry(crew, slot, id=..., status=AssignmentStatus.ACCEPTED) -> RosterEntry`.
   - The Aurora seed crew as CandidateFacts constants with the PRD §9 table-order ids already used in test_matching.py (Ana 6, Ben 7, Chen 8, Dana 9, Eli 10, Fay 11, Gus 12, Hana 13), with their PRD skills, workloads, unavailability and commitments exactly as test_matching.py has them. Also the Lunar Gateway Resupply / Asteroid Survey windows and slots as test_matching.py defines them.

   Keep builders thin: no logic beyond defaults. Records are frozen dataclasses, so module-level constants are fine.
2. Make `tests/builders.py` importable from tests. The project uses pytest with `testpaths = ["tests"]` (see pyproject.toml). Pick the least invasive working approach, e.g. a `tests/conftest.py` that adds the tests dir to sys.path, or `pythonpath = ["tests"]` under `[tool.pytest.ini_options]`. You may NOT edit pyproject.toml, so use conftest if that's needed. Make sure `uv run pytest` from the repo root works.
3. Update test_eligibility.py, test_matching.py, test_lifecycle.py and test_dates.py to import from builders instead of defining their own copies. Where a test intentionally uses a local variation (e.g. a person who is inactive, or a custom slot for one tie-break), build it with the shared builders and arguments rather than a new local helper. Small local helpers that are genuinely specific to one file (e.g. `fact()` for AssignmentFact in the workload tests, or `roster()` in test_matching) may stay local.
4. Where switching to shared seed ids changes a test's numbers (e.g. Ana's id in test_eligibility), update the assertions so the test checks exactly what it checked before. Don't weaken anything. If a test relied on a specific id for a tie-break, keep the tie-break meaningful.
5. Leave test_permissions.py, test_approvals.py and tests/api/test_health.py alone unless they duplicate these same builders. They mostly use user ids, not CandidateFacts.

When done, report: what builders.py provides, how it's made importable, per-file what was removed/replaced, the test count before and after, and the final pytest and ruff output.

<details>
<summary>⚙️ System/meta message · 2026-10-11 12:20:58 UTC</summary>

```
<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered.
</system-reminder>
```

</details>

**🔧 Bash**

```bash
ls tests tests/unit tests/unit/domain; cat src/mission_control/domain/records.py; wc -l tests/unit/domain/*.py; grep -n "pytest" -A8 pyproject.toml | head -30; ls tests/*.py tests/unit/*.py 2>/dev/null
```

**🔧 Bash**

```bash
grep -n "^## 10" -A60 docs/technical-design.md | head -80; grep -n "9.1" -A40 docs/prd.md | head -80
```

<details>
<summary>↳ Result</summary>

````
491:## 10. Guidelines for implementing agents
492-
493-### Source of truth
494-1. The **PRD** decides behaviour. **This document** decides structure. Code follows both.
495-2. **Don't invent behaviour.** If the PRD is silent or contradicts this document, stop and ask. Don't guess, and don't "improve" the rule.
496-3. Work on **one module at a time**, in the order in [§9](#9-delivery-plan). Start a module only when the user has approved it, and never before its dependencies are done.
497-
498-### The loop for each module
499-1. Read the module's row in §9 and every PRD ID it references.
500-2. Write failing tests. Name them after the rule, for example `test_ac15_accept_overlap_names_conflicting_mission`.
501-3. Write the smallest implementation that makes them pass.
502-4. Refactor, then run the **full** suite and `ruff`.
503-5. Verify the behaviour by running it for real (a REPL call, a request, or a CLI command), and show the output.
504-6. Do a read-only review of the diff, and report findings without editing anything.
505-7. Propose a commit message, such as `feat(m12): assignment propose/accept/withdraw`. **Don't commit, and don't start the next module, until the user approves.**
506-
507-### Architecture rules (never break these)
508-- `domain/` imports nothing from `infra/`, `services/`, `api/` or `sqlite3`.
509-- All SQL lives in `infra/repositories/`, and every query filters on `org_id`.
510-- `org_id` comes only from the `Actor`. Never read it from request input.
511-- Every mutating service calls `touch_for_change()` first, and writes an audit event in the same transaction.
512-- Writes open `BEGIN IMMEDIATE` **before** running checks.
513-- Errors use the codes in [§7](#7-api). Adding a code means updating that table in the same change.
514-
515-### Coding conventions
516-- Type hints everywhere. Frozen dataclasses for domain records. No module-level mutable state.
517-- `date` objects in the domain, ISO strings only at the database and API edges. Timestamps are UTC.
518-- Use PRD vocabulary in names: `open_places`, `eligible_approver`, `workload`.
519-- Keep routers thin: validate, call one service, return.
520-
521-### Testing conventions
522-- Use the `seeded_db` fixture for PRD scenarios, and `tests/builders.py` for edge cases.
523-- Every test gets its own database. No network calls. No reliance on the current date: pass dates in.
524-- Never weaken or delete a test to make it pass. If a test looks wrong, raise it.
525-
526-### Stop and ask before
527-- adding a dependency;
528-- changing the schema (and if you do, update [Appendix A](#appendix-a-schema-sql) as well);
529-- adding an endpoint, error code or CLI command that isn't in this document;
530-- any case where the PRD looks ambiguous or a PRD scenario's expected outcome seems wrong.
531-
532----
533-
534-## 11. Setup and testing
535-
536-```bash
537-uv sync
538-uv run mc-admin seed --reset      # load PRD §9 data
539-uv run mc-server                  # API on 127.0.0.1:8000
540-uv run mc login --email lee@aurora.example
541-uv run pytest
542-```
543-
544-Settings: `MC_DATABASE_PATH` · `MC_TOKEN_TTL_HOURS=12` · `MC_DB_BUSY_TIMEOUT_MS=5000`
545-
546-| Level | Database | Covers |
547-|---|---|---|
548-| Unit | none | Domain rules, matcher, lifecycle, permission table |
549-| Integration | temporary file | Services, rollback, constraints, audit, SQL lint |
550-| API | temporary file | Error codes, auth, permissions, isolation sweep, scenarios S1 and S3b–S9 |
551-| CLI | temporary file | S1 and S4 end to end, `--json`, errors, exit codes, prompts |
261:### 9.1 Aurora Space Agency (N = 2)
262-
263-| Person | Role | Crew skills | Commitments (workload) |
264-|---|---|---|---|
265-| Ruth Adeyemi | Director | — | — |
266-| Marco Bianchi | Director | Flight Medicine 4 | Medical Study, accepted (4) |
267-| Ingrid Holm | Director | — | — |
268-| Lee Park | Lead | — | — |
269-| Nora Quinn | Lead | — | — |
270-| Ana Okafor | Lead | Piloting 5, Leadership 4, Systems Eng 4 | none (0) |
271-| Ben Ito | Crew | Systems Eng 4, EVA 3 | Deep Space Comms, accepted (20) |
272-| Chen Wu | Crew | Systems Eng 3 | Telescope (5). Mars Analog Completed, so it doesn't count |
273-| Dana Reyes | Crew | EVA 4 | Telescope (5) |
274-| Eli Novak | Crew | EVA 4, Piloting 4, Leadership 2 | Telescope (5) |
275-| Fay Moreau | Crew | Piloting 4, Leadership 4 | Unavailable 5–8 Mar (Medical) |
276-| Gus Patel | Crew | Systems Eng 5 | Station Reboost, accepted (6) |
277-| Hana Sato | Crew | EVA 3, Geology 2 | Telescope (5) |
278-
279-| Mission | Owner / creator | Dates | State | Slots → crew |
280-|---|---|---|---|---|
281-| Lunar Gateway Resupply | Lee / Ruth | 1–10 Mar | Draft | Flight Engineer ×1 (Sys Eng ≥3) · Mission Specialist ×1 (EVA ≥3) · Commander ×1 (Piloting ≥4, Leadership ≥3) — no crew |
282-| Asteroid Survey | Nora | 5–12 Mar | Draft | Pilot ×1 (Piloting ≥4) · Geologist ×1 (Geology ≥4) — no crew |
283-| Station Reboost | Nora | 25 Feb – 2 Mar | Draft | Engineer ×2 (Sys Eng ≥3) — Gus accepted, 1 open place |
284-| Lunar Surface Medical Study | Nora / Ruth | 15–18 Mar | Draft | Flight Surgeon ×1 (Flight Medicine ≥4) — Marco accepted |
285-| Orbital Telescope Service | Lee | 10–14 Jan | Active | Engineer ×1 — Chen · EVA Specialist ×3 (EVA ≥3) — Dana, Eli, Hana |
286-| Deep Space Comms Upgrade | Nora | 1–20 Apr | Pending (Marco approved) | Engineer ×1 (Sys Eng ≥3) — Ben |
287-| Mars Analog Habitat | Lee | 1–30 May 2026 | Completed | Engineer ×1 — Chen |
288-
289-### 9.2 Helix Orbital (N = 1)
290-
291-People: Sam Rivera (Director), Priya Nair (Lead), and Crew Kai Tanaka (Piloting 5), Lena Fischer (Payload Integration 4), Omar Haddad (Field Medicine 4) and Tess Moreno (Life Support 3). Helix has its own catalogue, including a separate "Piloting" skill.
292-
293-| Mission | Owner | Dates | State | Slots → crew |
294-|---|---|---|---|---|
295-| Payload Demo 1 | Priya | 1–3 Feb | Draft | Payload Specialist ×1 (Payload Int ≥3) — Lena accepted · Medic ×1 (Field Medicine ≥3) — Omar accepted |
296-
297-### 9.3 Scenarios
298-
299-| # | Steps | Expected outcome |
300-|---|---|---|
301-| **S1** | Lee matches and applies *Lunar Gateway Resupply* → Ana, Chen and Dana accept → Lee submits → Ruth approves → Marco approves → Ingrid approves → Lee completes | Proposed crew are Ana, Chen and Dana. Ruth is refused as creator. After Marco the mission is Pending (1/2). After Ingrid it's **Active**. Completing makes the assignments Completed. |
````

</details>

<details>
<summary>↳ Result (error)</summary>

```
Exit code 1
tests:
api
unit

tests/unit:
domain

tests/unit/domain:
__pycache__
test_approvals.py
test_dates.py
test_eligibility.py
test_lifecycle.py
test_matching.py
test_passwords.py
test_permissions.py
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
     127 tests/unit/domain/test_approvals.py
      77 tests/unit/domain/test_dates.py
     413 tests/unit/domain/test_eligibility.py
     427 tests/unit/domain/test_lifecycle.py
     262 tests/unit/domain/test_matching.py
      38 tests/unit/domain/test_passwords.py
     265 tests/unit/domain/test_permissions.py
    1609 total
17:    "pytest>=8",
18-    "ruff>=0.6",
19-]
20-
21-[build-system]
22-requires = ["hatchling"]
23-build-backend = "hatchling.build"
24-
25-[tool.hatch.build.targets.wheel]
--
28:[tool.pytest.ini_options]
29-testpaths = ["tests"]
30-addopts = "-q"
31-
32-[tool.ruff]
33-line-length = 100
34-target-version = "py312"
35-src = ["src", "tests"]
36-extend-exclude = ["docs"]
(eval):1: no matches found: tests/*.py
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/unit/domain/test_matching.py"
}
```

<details>
<summary>↳ Result</summary>

```
1	import random
2	from datetime import date
3	
4	from mission_control.domain.dates import DateRange
5	from mission_control.domain.eligibility import is_eligible
6	from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster
7	from mission_control.domain.records import CandidateFacts, Commitment, Requirement, SlotSpec
8	
9	# --- PRD §9.1 Aurora seed, expressed as matcher inputs ------------------------------------
10	
11	PILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY = 1, 2, 3, 4, 5
12	SKILL = {
13	    PILOTING: "Piloting",
14	    LEADERSHIP: "Leadership",
15	    SYS_ENG: "Systems Eng",
16	    EVA: "EVA",
17	    GEOLOGY: "Geology",
18	}
19	
20	
21	def req(skill_id: int, min_level: int) -> Requirement:
22	    return Requirement(skill_id, SKILL[skill_id], min_level)
23	
24	
25	def rng(start: str, end: str) -> DateRange:
26	    return DateRange(date.fromisoformat(start), date.fromisoformat(end))
27	
28	
29	def person(id, name, skills, workload=0, unavailable=(), accepted_elsewhere=(), active=True):
30	    return CandidateFacts(
31	        crew_profile_id=id,
32	        name=name,
33	        active=active,
34	        skills=skills,
35	        unavailable=tuple(unavailable),
36	        accepted_elsewhere=tuple(accepted_elsewhere),
37	        workload=workload,
38	    )
39	
40	
41	STATION_REBOOST = Commitment(3, "Station Reboost", rng("2027-02-25", "2027-03-02"))
42	
43	# IDs follow the PRD §9 table order (the stable identifier used for the last tie-break).
44	ANA = person(6, "Ana", {PILOTING: 5, LEADERSHIP: 4, SYS_ENG: 4}, workload=0)
45	BEN = person(7, "Ben", {SYS_ENG: 4, EVA: 3}, workload=20)
46	CHEN = person(8, "Chen", {SYS_ENG: 3}, workload=5)
47	DANA = person(9, "Dana", {EVA: 4}, workload=5)
48	ELI = person(10, "Eli", {EVA: 4, PILOTING: 4, LEADERSHIP: 2}, workload=5)
49	FAY = person(11, "Fay", {PILOTING: 4, LEADERSHIP: 4}, unavailable=[rng("2027-03-05", "2027-03-08")])
50	GUS = person(12, "Gus", {SYS_ENG: 5}, workload=6, accepted_elsewhere=[STATION_REBOOST])
51	HANA = person(13, "Hana", {EVA: 3, GEOLOGY: 2}, workload=5)
52	AURORA_CREW = [ANA, BEN, CHEN, DANA, ELI, FAY, GUS, HANA]
53	
54	# Lunar Gateway Resupply, 1–10 Mar 2027. Slots listed Flight Engineer first, as in the PRD.
55	GATEWAY_WINDOW = rng("2027-03-01", "2027-03-10")
56	FLIGHT_ENGINEER = SlotSpec(21, 1, "Flight Engineer", 1, (req(SYS_ENG, 3),))
57	SPECIALIST = SlotSpec(22, 2, "Mission Specialist", 1, (req(EVA, 3),))
58	COMMANDER = SlotSpec(23, 3, "Commander", 1, (req(PILOTING, 4), req(LEADERSHIP, 3)))
59	GATEWAY_SLOTS = [FLIGHT_ENGINEER, SPECIALIST, COMMANDER]
60	
61	# Asteroid Survey, 5–12 Mar 2027.
62	ASTEROID_WINDOW = rng("2027-03-05", "2027-03-12")
63	PILOT = SlotSpec(31, 1, "Pilot", 1, (req(PILOTING, 4),))
64	GEOLOGIST = SlotSpec(32, 2, "Geologist", 1, (req(GEOLOGY, 4),))
65	ASTEROID_SLOTS = [PILOT, GEOLOGIST]
66	
67	
68	def roster(s: Suggestion) -> dict[int, list[int]]:
69	    """slot_id -> crew ids placed there, in pick order."""
70	    out: dict[int, list[int]] = {}
71	    for p in s.placements:
72	        out.setdefault(p.slot_id, []).append(p.crew_profile_id)
73	    return out
74	
75	
76	# --- PRD scenarios -----------------------------------------------------------------------
77	
78	
79	def test_s2_gateway_roster_is_ana_chen_dana():
80	    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
81	    assert roster(s) == {
82	        COMMANDER.id: [ANA.crew_profile_id],
83	        FLIGHT_ENGINEER.id: [CHEN.crew_profile_id],
84	        SPECIALIST.id: [DANA.crew_profile_id],
85	    }
86	    assert s.unfilled == ()
87	
88	
89	def test_s2_commander_is_filled_first_because_it_is_most_constrained():
90	    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
91	    assert s.placements[0] == Placement(COMMANDER.id, ANA.crew_profile_id)
92	
93	
94	def test_s2_listed_order_would_have_left_commander_unfilled():
95	    # The counterfactual from the PRD: filling Flight Engineer first gives it Ana (workload 0),
96	    # and then nobody eligible is left for Commander. Most-constrained-first avoids this.
97	    only_fe = suggest_roster([FLIGHT_ENGINEER], AURORA_CREW, GATEWAY_WINDOW)
98	    assert only_fe.placements == (Placement(FLIGHT_ENGINEER.id, ANA.crew_profile_id),)
99	    without_ana = [c for c in AURORA_CREW if c is not ANA]
100	    assert suggest_roster([COMMANDER], without_ana, GATEWAY_WINDOW).unfilled == (
101	        Unfilled(COMMANDER.id, 1),
102	    )
103	
104	
105	def test_ac18_s2_is_identical_on_every_run():
106	    first = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
107	    for _ in range(20):
108	        assert suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW) == first
109	
110	
111	def test_ac18_input_order_does_not_change_the_result():
112	    expected = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
113	    shuffler = random.Random(42)
114	    for _ in range(20):
115	        crew, slots = AURORA_CREW[:], GATEWAY_SLOTS[:]
116	        shuffler.shuffle(crew)
117	        shuffler.shuffle(slots)
118	        assert suggest_roster(slots, crew, GATEWAY_WINDOW) == expected
119	
120	
121	def test_ac19_s3_asteroid_survey_pilot_is_ana_and_geologist_unfilled():
122	    s = suggest_roster(ASTEROID_SLOTS, AURORA_CREW, ASTEROID_WINDOW)
123	    assert roster(s) == {PILOT.id: [ANA.crew_profile_id]}
124	    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)
125	
126	
127	def test_ac19_s3b_ana_accepting_gateway_moves_pilot_to_eli():
128	    gateway = Commitment(1, "Lunar Gateway Resupply", GATEWAY_WINDOW)
129	    ana_committed = person(6, "Ana", ANA.skills, workload=10, accepted_elsewhere=[gateway])
130	    crew = [ana_committed if c is ANA else c for c in AURORA_CREW]
131	    s = suggest_roster(ASTEROID_SLOTS, crew, ASTEROID_WINDOW)
132	    assert roster(s) == {PILOT.id: [ELI.crew_profile_id]}
133	    assert s.unfilled == (Unfilled(GEOLOGIST.id, 1),)
134	
135	
136	# --- Each tie-break on its own -----------------------------------------------------------
137	
138	ONE_SKILL = SlotSpec(1, 1, "Engineer", 1, (req(SYS_ENG, 3),))
139	WINDOW = rng("2027-06-01", "2027-06-05")
140	
141	
142	def test_lowest_workload_wins():
143	    busy = person(1, "Busy", {SYS_ENG: 5}, workload=20)
144	    free = person(2, "Free", {SYS_ENG: 3}, workload=5)
145	    s = suggest_roster([ONE_SKILL], [busy, free], WINDOW)
146	    assert s.placements == (Placement(1, 2),)
147	
148	
149	def test_on_equal_workload_higher_proficiency_wins():
150	    low = person(1, "Low", {SYS_ENG: 3}, workload=5)
151	    high = person(2, "High", {SYS_ENG: 4}, workload=5)
152	    assert suggest_roster([ONE_SKILL], [low, high], WINDOW).placements == (Placement(1, 2),)
153	
154	
155	def test_proficiency_is_the_sum_across_the_slots_required_skills():
156	    slot = SlotSpec(1, 1, "Commander", 1, (req(PILOTING, 4), req(LEADERSHIP, 3)))
157	    a = person(1, "A", {PILOTING: 5, LEADERSHIP: 3})  # 8
158	    b = person(2, "B", {PILOTING: 4, LEADERSHIP: 5})  # 9
159	    assert suggest_roster([slot], [a, b], WINDOW).placements == (Placement(1, 2),)
160	
161	
162	def test_skills_the_slot_does_not_require_do_not_count_towards_proficiency():
163	    a = person(1, "A", {SYS_ENG: 4, EVA: 5, GEOLOGY: 5})
164	    b = person(2, "B", {SYS_ENG: 5})
165	    assert suggest_roster([ONE_SKILL], [a, b], WINDOW).placements == (Placement(1, 2),)
166	
167	
168	def test_on_equal_workload_and_proficiency_lowest_id_wins():
169	    later = person(9, "Later", {SYS_ENG: 4}, workload=5)
170	    earlier = person(3, "Earlier", {SYS_ENG: 4}, workload=5)
171	    assert suggest_roster([ONE_SKILL], [later, earlier], WINDOW).placements == (Placement(1, 3),)
172	
173	
174	def test_slots_with_equal_candidate_counts_go_in_listed_position():
175	    first = SlotSpec(7, 1, "First", 1, (req(SYS_ENG, 3),))
176	    second = SlotSpec(5, 2, "Second", 1, (req(SYS_ENG, 3),))
177	    a = person(1, "A", {SYS_ENG: 4})
178	    b = person(2, "B", {SYS_ENG: 4})
179	    s = suggest_roster([second, first], [a, b], WINDOW)
180	    # "First" (position 1) picks before "Second", so it gets the better-ranked person (A)
181	    assert s.placements == (Placement(7, 1), Placement(5, 2))
182	
183	
184	def test_slots_with_equal_count_and_position_fall_back_to_slot_id():
185	    a_slot = SlotSpec(8, 1, "A", 1, (req(SYS_ENG, 3),))
186	    b_slot = SlotSpec(4, 1, "B", 1, (req(SYS_ENG, 3),))
187	    x, y = person(1, "X", {SYS_ENG: 4}), person(2, "Y", {SYS_ENG: 4})
188	    assert suggest_roster([a_slot, b_slot], [x, y], WINDOW).placements[0].slot_id == 4
189	
190	
191	# --- Structural guarantees ---------------------------------------------------------------
192	
193	
194	def test_ac21_nobody_is_placed_in_two_slots():
195	    s = suggest_roster(GATEWAY_SLOTS, AURORA_CREW, GATEWAY_WINDOW)
196	    ids = [p.crew_profile_id for p in s.placements]
197	    assert len(ids) == len(set(ids))
198	
199	
200	def test_ac21_every_placement_is_eligible_for_its_slot():
201	    by_id = {c.crew_profile_id: c for c in AURORA_CREW}
202	    slots = {sl.id: sl for sl in GATEWAY_SLOTS + ASTEROID_SLOTS}
203	    for slot_list, window in [(GATEWAY_SLOTS, GATEWAY_WINDOW), (ASTEROID_SLOTS, ASTEROID_WINDOW)]:
204	        for p in suggest_roster(slot_list, AURORA_CREW, window).placements:
205	            assert is_eligible(by_id[p.crew_profile_id], slots[p.slot_id], window)
206	
207	
208	def test_ac21_inactive_unavailable_and_overlapping_people_are_never_suggested():
209	    s = suggest_roster(
210	        GATEWAY_SLOTS + [SlotSpec(24, 4, "Extra", 5, (req(PILOTING, 1),))],
211	        AURORA_CREW + [person(99, "Gone", {PILOTING: 5}, active=False)],
212	        GATEWAY_WINDOW,
213	    )
214	    placed = {p.crew_profile_id for p in s.placements}
215	    assert not placed & {FAY.crew_profile_id, GUS.crew_profile_id, 99}
216	
217	
218	def test_multi_place_slot_takes_several_people_in_rank_order():
219	    slot = SlotSpec(1, 1, "Engineer", 2, (req(SYS_ENG, 3),))
220	    crew = [
221	        person(1, "A", {SYS_ENG: 3}, workload=9),
222	        person(2, "B", {SYS_ENG: 3}, workload=1),
223	        person(3, "C", {SYS_ENG: 3}, workload=5),
224	    ]
225	    assert suggest_roster([slot], crew, WINDOW).placements == (Placement(1, 2), Placement(1, 3))
226	
227	
228	def test_places_left_when_candidates_run_out_are_marked_unfilled():
229	    slot = SlotSpec(1, 1, "Engineer", 3, (req(SYS_ENG, 3),))
230	    s = suggest_roster([slot], [person(1, "A", {SYS_ENG: 3})], WINDOW)
231	    assert s.placements == (Placement(1, 1),)
232	    assert s.unfilled == (Unfilled(1, 2),)
233	
234	
235	def test_slots_without_open_places_are_ignored():
236	    full = SlotSpec(1, 1, "Engineer", 0, (req(SYS_ENG, 3),))
237	    s = suggest_roster([full], [person(1, "A", {SYS_ENG: 3})], WINDOW)
238	    assert s == Suggestion(placements=(), unfilled=())
239	
240	
241	def test_no_slots_or_no_candidates_gives_an_empty_or_unfilled_suggestion():
242	    assert suggest_roster([], AURORA_CREW, WINDOW) == Suggestion((), ())
243	    assert suggest_roster([ONE_SKILL], [], WINDOW) == Suggestion((), (Unfilled(1, 1),))
244	
245	
246	def test_candidate_counts_are_recounted_after_every_pick():
247	    # Every slot starts with 2 candidates, so they would be filled in listed order X, Y, W if
248	    # counts were only taken once:
249	    #   X (2 places) gets A and B; Y then picks D over C (D has lower workload); W is left with
250	    #   nobody, because its candidates were B and D.
251	    # Recounting after each pick notices that once B is gone W has only D left (1 candidate)
252	    # while Y still has C and D (2), so W picks D first and Y takes C. Every place is filled.
253	    x = SlotSpec(1, 1, "X", 2, (req(SYS_ENG, 1),))  # candidates: A, B
254	    y = SlotSpec(2, 2, "Y", 1, (req(EVA, 1),))  # candidates: C, D
255	    w = SlotSpec(3, 3, "W", 1, (req(GEOLOGY, 1),))  # candidates: B, D
256	    a = person(1, "A", {SYS_ENG: 1})
257	    b = person(2, "B", {SYS_ENG: 1, GEOLOGY: 1})
258	    c = person(3, "C", {EVA: 1}, workload=9)
259	    d_ = person(4, "D", {EVA: 1, GEOLOGY: 1})
260	    s = suggest_roster([x, y, w], [a, b, c, d_], WINDOW)
261	    assert roster(s) == {1: [1, 2], 3: [4], 2: [3]}
262	    assert s.unfilled == ()
263
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/unit/domain/test_eligibility.py"
}
```

<details>
<summary>↳ Result</summary>

```
1	from datetime import date
2	
3	import pytest
4	
5	from mission_control.domain.dates import DateRange
6	from mission_control.domain.eligibility import (
7	    DatesEdit,
8	    SlotEdit,
9	    SlotRemoval,
10	    ineligibility_reasons,
11	    invalidated_by,
12	    invalidated_by_skill_change,
13	    is_eligible,
14	    workload,
15	)
16	from mission_control.domain.enums import AssignmentStatus, MissionStatus
17	from mission_control.domain.errors import Problem
18	from mission_control.domain.records import (
19	    ActiveAssignment,
20	    AssignmentFact,
21	    CandidateFacts,
22	    Commitment,
23	    Requirement,
24	    RosterEntry,
25	    SlotSpec,
26	)
27	
28	# Skill ids and names used across tests (Aurora catalogue, PRD §9.1)
29	PILOTING, LEADERSHIP, SYS_ENG, EVA = 1, 2, 3, 4
30	NAMES = {PILOTING: "Piloting", LEADERSHIP: "Leadership", SYS_ENG: "Systems Eng", EVA: "EVA"}
31	
32	GATEWAY = DateRange(date(2027, 3, 1), date(2027, 3, 10))
33	
34	
35	def req(skill_id: int, min_level: int) -> Requirement:
36	    return Requirement(skill_id, NAMES[skill_id], min_level)
37	
38	
39	def slot(*requirements: Requirement, name="Commander", id=10, open_places=1) -> SlotSpec:
40	    return SlotSpec(
41	        id=id, position=1, name=name, open_places=open_places, requirements=tuple(requirements)
42	    )
43	
44	
45	def crew(
46	    name="Ana", id=1, active=True, skills=None, unavailable=(), accepted_elsewhere=(), workload=0
47	) -> CandidateFacts:
48	    return CandidateFacts(
49	        crew_profile_id=id,
50	        name=name,
51	        active=active,
52	        skills=skills or {},
53	        unavailable=tuple(unavailable),
54	        accepted_elsewhere=tuple(accepted_elsewhere),
55	        workload=workload,
56	    )
57	
58	
59	def d(s: str) -> date:
60	    return date.fromisoformat(s)
61	
62	
63	COMMANDER = slot(req(PILOTING, 4), req(LEADERSHIP, 3))
64	
65	
66	# Eligibility: one test per reason (PRD §5.1 "Eligible")
67	
68	
69	def test_eligible_when_every_condition_holds():
70	    ana = crew(skills={PILOTING: 5, LEADERSHIP: 4})
71	    assert is_eligible(ana, COMMANDER, GATEWAY)
72	    assert ineligibility_reasons(ana, COMMANDER, GATEWAY) == []
73	
74	
75	def test_inactive_person_is_not_eligible():
76	    ana = crew(active=False, skills={PILOTING: 5, LEADERSHIP: 4})
77	    [problem] = ineligibility_reasons(ana, COMMANDER, GATEWAY)
78	    assert problem.code == "inactive"
79	    assert "Ana" in problem.message
80	
81	
82	def test_skill_below_minimum_is_not_eligible():
83	    # PRD S2: Eli has Leadership 2, Commander needs 3
84	    eli = crew(name="Eli", skills={PILOTING: 4, LEADERSHIP: 2})
85	    [problem] = ineligibility_reasons(eli, COMMANDER, GATEWAY)
86	    assert problem.code == "skill_below_minimum"
87	    assert "Eli" in problem.message and "Leadership" in problem.message
88	    assert problem.refs["skill_id"] == LEADERSHIP
89	
90	
91	def test_missing_skill_is_not_eligible():
92	    dana = crew(name="Dana", skills={EVA: 4})
93	    problems = ineligibility_reasons(dana, COMMANDER, GATEWAY)
94	    assert {p.code for p in problems} == {"skill_below_minimum"}
95	    assert {p.refs["skill_id"] for p in problems} == {PILOTING, LEADERSHIP}
96	
97	
98	def test_skill_exactly_at_minimum_is_eligible():
99	    assert is_eligible(crew(skills={PILOTING: 4, LEADERSHIP: 3}), COMMANDER, GATEWAY)
100	
101	
102	def test_unavailability_overlapping_the_mission_is_not_eligible():
103	    # PRD S2: Fay is unavailable 5–8 Mar
104	    fay = crew(
105	        name="Fay",
106	        skills={PILOTING: 4, LEADERSHIP: 4},
107	        unavailable=[DateRange(d("2027-03-05"), d("2027-03-08"))],
108	    )
109	    [problem] = ineligibility_reasons(fay, COMMANDER, GATEWAY)
110	    assert problem.code == "unavailable"
111	    assert "Fay" in problem.message
112	
113	
114	def test_ac17_unavailability_on_the_boundary_day_is_not_eligible():
115	    fay = crew(
116	        name="Fay",
117	        skills={PILOTING: 4, LEADERSHIP: 4},
118	        unavailable=[DateRange(d("2027-03-10"), d("2027-03-12"))],
119	    )
120	    assert not is_eligible(fay, COMMANDER, GATEWAY)
121	
122	
123	def test_overlapping_accepted_assignment_elsewhere_is_not_eligible_and_names_the_mission():
124	    # PRD S2 / S4: Gus has accepted Station Reboost, 25 Feb – 2 Mar
125	    reboost = Commitment(
126	        mission_id=3,
127	        mission_name="Station Reboost",
128	        window=DateRange(d("2027-02-25"), d("2027-03-02")),
129	    )
130	    gus = crew(name="Gus", skills={SYS_ENG: 5}, accepted_elsewhere=[reboost])
131	    [problem] = ineligibility_reasons(gus, slot(req(SYS_ENG, 3), name="Flight Engineer"), GATEWAY)
132	    assert problem.code == "overlap"
133	    assert "Gus" in problem.message and "Station Reboost" in problem.message
134	    # the message gives the overlapping days (1–2 Mar), not the whole other mission
135	    assert "2027-03-01" in problem.message and "2027-03-02" in problem.message
136	    assert problem.refs["mission_id"] == 3
137	
138	
139	def test_non_overlapping_commitments_do_not_block():
140	    telescope = Commitment(
141	        mission_id=5,
142	        mission_name="Orbital Telescope Service",
143	        window=DateRange(d("2027-01-10"), d("2027-01-14")),
144	    )
145	    chen = crew(
146	        name="Chen",
147	        skills={SYS_ENG: 3},
148	        accepted_elsewhere=[telescope],
149	        unavailable=[DateRange(d("2027-04-01"), d("2027-04-02"))],
150	    )
151	    assert is_eligible(chen, slot(req(SYS_ENG, 3)), GATEWAY)
152	
153	
154	def test_all_reasons_are_reported_together():
155	    reboost = Commitment(3, "Station Reboost", DateRange(d("2027-02-25"), d("2027-03-02")))
156	    person = crew(
157	        active=False,
158	        skills={},
159	        accepted_elsewhere=[reboost],
160	        unavailable=[DateRange(d("2027-03-05"), d("2027-03-05"))],
161	    )
162	    codes = [p.code for p in ineligibility_reasons(person, slot(req(SYS_ENG, 3)), GATEWAY)]
163	    assert sorted(codes) == ["inactive", "overlap", "skill_below_minimum", "unavailable"]
164	
165	
166	# Workload (PRD §6, AC-20)
167	
168	
169	def fact(
170	    *,
171	    mission_id: int,
172	    days: int,
173	    mission_status=MissionStatus.ACTIVE,
174	    status=AssignmentStatus.ACCEPTED,
175	) -> AssignmentFact:
176	    start = date(2027, 1, 1)
177	    window = DateRange(start, date.fromordinal(start.toordinal() + days - 1))
178	    return AssignmentFact(
179	        mission_id=mission_id,
180	        mission_status=mission_status,
181	        assignment_status=status,
182	        window=window,
183	    )
184	
185	
186	def test_ac20_chen_workload_counts_telescope_but_not_completed_mars_analog():
187	    telescope = fact(mission_id=105, days=5, mission_status=MissionStatus.ACTIVE)
188	    mars_analog = fact(
189	        mission_id=107,
190	        days=30,
191	        mission_status=MissionStatus.COMPLETED,
192	        status=AssignmentStatus.COMPLETED,
193	    )
194	    assert workload([telescope, mars_analog], excluding_mission_id=101) == 5
195	
196	
197	def test_ac20_accepted_on_a_completed_mission_does_not_count():
198	    facts = [fact(mission_id=107, days=30, mission_status=MissionStatus.COMPLETED)]
199	    assert workload(facts, excluding_mission_id=101) == 0
200	
201	
202	def test_workload_counts_accepted_on_every_non_completed_mission_state():
203	    facts = [
204	        fact(mission_id=102, days=1, mission_status=MissionStatus.DRAFT),
205	        fact(mission_id=103, days=2, mission_status=MissionStatus.PENDING_APPROVAL),
206	        fact(mission_id=104, days=4, mission_status=MissionStatus.ACTIVE),
207	    ]
208	    assert workload(facts, excluding_mission_id=199) == 7
209	
210	
211	def test_workload_ignores_assignments_that_are_not_accepted():
212	    facts = [
213	        fact(mission_id=102, days=3, status=s)
214	        for s in AssignmentStatus
215	        if s != AssignmentStatus.ACCEPTED
216	    ]
217	    assert workload(facts, excluding_mission_id=199) == 0
218	
219	
220	def test_workload_excludes_the_mission_being_matched():
221	    facts = [fact(mission_id=101, days=10), fact(mission_id=102, days=5)]
222	    assert workload(facts, excluding_mission_id=101) == 5
223	
224	
225	# Edits that would invalidate open assignments (PRD M7)
226	
227	
228	def open_assignment(person: CandidateFacts, slot_spec: SlotSpec, id=100) -> RosterEntry:
229	    return RosterEntry(
230	        assignment_id=id, slot=slot_spec, crew=person, status=AssignmentStatus.ACCEPTED
231	    )
232	
233	
234	ANA = crew(skills={PILOTING: 5, LEADERSHIP: 4})
235	
236	
237	def test_m7_removing_a_slot_with_open_assignments_is_refused():
238	    [problem] = invalidated_by(SlotRemoval(slot_id=COMMANDER.id), [open_assignment(ANA, COMMANDER)])
239	    assert problem.code == "slot_has_open_assignments"
240	    assert "Ana" in problem.message and "Commander" in problem.message
241	
242	
243	def test_m7_removing_a_slot_without_open_assignments_is_allowed():
244	    other = slot(req(EVA, 3), name="Specialist", id=11)
245	    assert invalidated_by(SlotRemoval(slot_id=other.id), [open_assignment(ANA, COMMANDER)]) == []
246	
247	
248	def test_m7_lowering_headcount_below_open_assignments_is_refused():
249	    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12, open_places=0)
250	    gus, chen = (
251	        crew(name="Gus", id=7, skills={SYS_ENG: 5}),
252	        crew(name="Chen", id=3, skills={SYS_ENG: 3}),
253	    )
254	    assignments = [open_assignment(gus, engineers, 1), open_assignment(chen, engineers, 2)]
255	    problems = invalidated_by(SlotEdit(slot_id=12, headcount=1), assignments)
256	    assert [p.code for p in problems] == ["headcount_below_open_assignments"]
257	    assert "Engineer" in problems[0].message
258	
259	
260	def test_m7_lowering_headcount_to_exactly_the_open_assignments_is_allowed():
261	    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12)
262	    gus = crew(name="Gus", skills={SYS_ENG: 5})
263	    assert (
264	        invalidated_by(SlotEdit(slot_id=12, headcount=1), [open_assignment(gus, engineers)]) == []
265	    )
266	
267	
268	def test_m7_raising_requirements_above_an_assignees_level_is_refused():
269	    edit = SlotEdit(slot_id=COMMANDER.id, requirements=(req(PILOTING, 4), req(LEADERSHIP, 5)))
270	    [problem] = invalidated_by(edit, [open_assignment(ANA, COMMANDER)])
271	    assert problem.code == "skill_below_minimum"
272	    assert "Ana" in problem.message and "Commander" in problem.message
273	
274	
275	def test_m7_requirement_edit_on_another_slot_does_not_affect_this_one():
276	    edit = SlotEdit(slot_id=99, requirements=(req(LEADERSHIP, 5),))
277	    assert invalidated_by(edit, [open_assignment(ANA, COMMANDER)]) == []
278	
279	
280	def test_m7_moving_dates_onto_unavailability_is_refused():
281	    fay = crew(
282	        name="Fay",
283	        skills={PILOTING: 4, LEADERSHIP: 4},
284	        unavailable=[DateRange(d("2027-04-01"), d("2027-04-03"))],
285	    )
286	    edit = DatesEdit(window=DateRange(d("2027-03-30"), d("2027-04-05")))
287	    [problem] = invalidated_by(edit, [open_assignment(fay, COMMANDER)])
288	    assert problem.code == "unavailable"
289	    assert "Fay" in problem.message and "Commander" in problem.message
290	
291	
292	def test_m7_moving_dates_onto_another_accepted_assignment_is_refused():
293	    comms = Commitment(6, "Deep Space Comms Upgrade", DateRange(d("2027-04-01"), d("2027-04-20")))
294	    ben = crew(name="Ben", skills={SYS_ENG: 4}, accepted_elsewhere=[comms])
295	    fe = slot(req(SYS_ENG, 3), name="Flight Engineer")
296	    [problem] = invalidated_by(
297	        DatesEdit(window=DateRange(d("2027-04-15"), d("2027-04-25"))), [open_assignment(ben, fe)]
298	    )
299	    assert problem.code == "overlap"
300	    assert "Deep Space Comms Upgrade" in problem.message
301	
302	
303	def test_m7_harmless_date_change_is_allowed():
304	    edit = DatesEdit(window=DateRange(d("2027-03-02"), d("2027-03-11")))
305	    assert invalidated_by(edit, [open_assignment(ANA, COMMANDER)]) == []
306	
307	
308	def test_m7_every_affected_assignment_is_listed():
309	    fe = slot(req(SYS_ENG, 3), name="Flight Engineer", id=11)
310	    blocked = [DateRange(d("2027-05-01"), d("2027-05-02"))]
311	    a = open_assignment(
312	        crew(name="Ana", id=1, skills={PILOTING: 5, LEADERSHIP: 4}, unavailable=blocked),
313	        COMMANDER,
314	        1,
315	    )
316	    b = open_assignment(crew(name="Chen", id=3, skills={SYS_ENG: 3}, unavailable=blocked), fe, 2)
317	    problems = invalidated_by(DatesEdit(window=DateRange(d("2027-05-01"), d("2027-05-05"))), [a, b])
318	    assert [p.refs["assignment_id"] for p in problems] == [1, 2]
319	
320	
321	# Skill changes against Active assignments (PRD P3)
322	
323	
324	TELESCOPE_EVA = ActiveAssignment(
325	    mission_id=5,
326	    mission_name="Orbital Telescope Service",
327	    slot_name="EVA Specialist",
328	    requirements=(req(EVA, 3),),
329	)
330	
331	
332	def test_p3_lowering_a_skill_below_an_active_assignments_requirement_is_refused():
333	    [problem] = invalidated_by_skill_change("Hana", EVA, 2, [TELESCOPE_EVA])
334	    assert problem.code == "invalidates_active_assignment"
335	    assert "Hana" in problem.message and "Orbital Telescope Service" in problem.message
336	    assert problem.refs["mission_id"] == 5
337	
338	
339	def test_p3_removing_a_skill_needed_by_an_active_assignment_is_refused():
340	    assert invalidated_by_skill_change("Hana", EVA, None, [TELESCOPE_EVA])
341	
342	
343	def test_p3_change_that_still_meets_the_requirement_is_allowed():
344	    assert invalidated_by_skill_change("Hana", EVA, 3, [TELESCOPE_EVA]) == []
345	
346	
347	def test_p3_change_to_a_skill_the_active_slot_does_not_require_is_allowed():
348	    assert invalidated_by_skill_change("Hana", PILOTING, None, [TELESCOPE_EVA]) == []
349	
350	
351	def test_p3_without_active_assignments_any_change_is_allowed():
352	    # Draft and Pending assignments never block; the caller passes only Active ones
353	    assert invalidated_by_skill_change("Hana", EVA, None, []) == []
354	
355	
356	# Regression: M7 refusals must list the affected crew
357	
358	
359	def test_m7_headcount_refusal_names_every_assigned_person():
360	    engineers = slot(req(SYS_ENG, 3), name="Engineer", id=12)
361	    gus = crew(name="Gus", id=7, skills={SYS_ENG: 5})
362	    chen = crew(name="Chen", id=3, skills={SYS_ENG: 3})
363	    [problem] = invalidated_by(
364	        SlotEdit(slot_id=12, headcount=1),
365	        [open_assignment(gus, engineers, 1), open_assignment(chen, engineers, 2)],
366	    )
367	    assert "Gus" in problem.message and "Chen" in problem.message
368	    assert problem.refs["crew_profile_ids"] == [7, 3]
369	
370	
371	# Regression: a dates edit only reports availability conflicts
372	
373	
374	def test_m7_dates_edit_reports_only_unavailability_and_overlap():
375	    # inactive, no skills, and unavailable on the new dates: only "unavailable" applies to a
376	    # date change
377	    person = crew(
378	        name="Ivy",
379	        active=False,
380	        skills={},
381	        unavailable=[DateRange(d("2027-04-01"), d("2027-04-01"))],
382	    )
383	    problems = invalidated_by(
384	        DatesEdit(window=DateRange(d("2027-04-01"), d("2027-04-02"))),
385	        [open_assignment(person, COMMANDER)],
386	    )
387	    assert [p.code for p in problems] == ["unavailable"]
388	
389	
390	# Regression: problems never share or expose a mutable refs mapping
391	
392	
393	def test_problems_from_one_check_do_not_share_refs():
394	    person = crew(active=False, skills={})
395	    first, second, *_ = ineligibility_reasons(person, COMMANDER, GATEWAY)
396	    assert first.refs is not second.refs
397	    assert first.refs == {"crew_profile_id": 1, "slot_id": COMMANDER.id}
398	
399	
400	def test_problem_refs_cannot_be_mutated():
401	    [problem] = ineligibility_reasons(
402	        crew(active=False, skills={PILOTING: 5, LEADERSHIP: 4}), COMMANDER, GATEWAY
403	    )
404	    with pytest.raises(TypeError):
405	        problem.refs["slot_id"] = 99  # type: ignore[index]
406	    assert problem.refs["slot_id"] == COMMANDER.id
407	
408	
409	def test_problem_copies_the_refs_it_is_given():
410	    refs = {"slot_id": 1}
411	    problem = Problem("x", "y", refs)
412	    refs["slot_id"] = 2
413	    assert problem.refs == {"slot_id": 1}
414
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/unit/domain/test_lifecycle.py"
}
```

<details>
<summary>↳ Result</summary>

```
1	from datetime import date
2	
3	import pytest
4	
5	from mission_control.domain import lifecycle, permissions
6	from mission_control.domain.dates import DateRange
7	from mission_control.domain.enums import Action
8	from mission_control.domain.enums import AssignmentStatus as A
9	from mission_control.domain.enums import MissionStatus as M
10	from mission_control.domain.lifecycle import (
11	    MISSION_ALLOWED_FROM,
12	    StateConflict,
13	    assignment_problem,
14	    assignment_status_after,
15	    cascade,
16	    check_submit,
17	    mission_status_after,
18	    mission_status_after_assignment_action,
19	    state_problem,
20	    touch_for_change,
21	)
22	from mission_control.domain.records import CandidateFacts, Requirement, RosterEntry, SlotSpec
23	
24	WINDOW = DateRange(date(2027, 3, 1), date(2027, 3, 10))
25	EVA = Requirement(4, "EVA", 3)
26	ALL_STATUSES = list(M)
27	
28	
29	# --- Mission transition table -------------------------------------------------------------
30	
31	MISSION_ACTIONS = [
32	    Action.SUBMIT,
33	    Action.APPROVE,
34	    Action.REJECT,
35	    Action.TRANSFER,
36	    Action.COMPLETE,
37	    Action.CANCEL,
38	    Action.EDIT_MISSION,
39	]
40	ASSIGNMENT_ACTIONS = [
41	    Action.PROPOSE_CREW,
42	    Action.ACCEPT,
43	    Action.DECLINE,
44	    Action.WITHDRAW,
45	    Action.REMOVE_CREW,
46	]
47	
48	ALLOWED = {
49	    Action.SUBMIT: {M.DRAFT},
50	    Action.APPROVE: {M.PENDING_APPROVAL},
51	    Action.REJECT: {M.PENDING_APPROVAL},
52	    Action.TRANSFER: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
53	    Action.COMPLETE: {M.ACTIVE},
54	    Action.CANCEL: {M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE},
55	    Action.EDIT_MISSION: {M.DRAFT, M.PENDING_APPROVAL},
56	}
57	
58	
59	@pytest.mark.parametrize("action", MISSION_ACTIONS)
60	@pytest.mark.parametrize("status", ALL_STATUSES)
61	def test_transition_table_allows_exactly_the_designed_states(action, status):
62	    problem = state_problem(status, action)
63	    if status in ALLOWED[action]:
64	        assert problem is None
65	    else:
66	        assert problem is not None
67	
68	
69	@pytest.mark.parametrize("action", MISSION_ACTIONS)
70	@pytest.mark.parametrize("status", [M.COMPLETED, M.CANCELLED])
71	def test_finished_missions_refuse_everything_with_mission_final(action, status):
72	    assert state_problem(status, action).code == "mission_final"
73	
74	
75	@pytest.mark.parametrize(
76	    "action",
77	    [Action.EDIT_MISSION, Action.SUBMIT, Action.APPROVE, Action.REJECT],
78	)
79	def test_ac5_active_mission_refuses_changes_with_mission_frozen(action):
80	    assert state_problem(M.ACTIVE, action).code == "mission_frozen"
81	
82	
83	@pytest.mark.parametrize("action", [Action.COMPLETE, Action.CANCEL, Action.TRANSFER])
84	def test_ac5_active_mission_still_allows_complete_cancel_and_transfer(action):
85	    assert state_problem(M.ACTIVE, action) is None
86	
87	
88	@pytest.mark.parametrize(
89	    "status, action",
90	    [
91	        (M.DRAFT, Action.APPROVE),
92	        (M.DRAFT, Action.REJECT),
93	        (M.DRAFT, Action.COMPLETE),
94	        (M.PENDING_APPROVAL, Action.SUBMIT),
95	        (M.PENDING_APPROVAL, Action.COMPLETE),
96	    ],
97	)
98	def test_wrong_state_in_draft_or_pending_is_invalid_transition(status, action):
99	    problem = state_problem(status, action)
100	    assert problem.code == "invalid_transition"
101	    assert status.value.replace("_", " ") in problem.message.lower()
102	
103	
104	def test_submit_moves_draft_to_pending():
105	    assert mission_status_after(M.DRAFT, Action.SUBMIT) == M.PENDING_APPROVAL
106	
107	
108	def test_ac3_approval_before_quorum_stays_pending_and_at_quorum_goes_active():
109	    assert (
110	        mission_status_after(M.PENDING_APPROVAL, Action.APPROVE, reaches_quorum=False)
111	        == M.PENDING_APPROVAL
112	    )
113	    assert mission_status_after(M.PENDING_APPROVAL, Action.APPROVE, reaches_quorum=True) == M.ACTIVE
114	
115	
116	def test_reject_returns_to_draft():
117	    assert mission_status_after(M.PENDING_APPROVAL, Action.REJECT) == M.DRAFT
118	
119	
120	def test_ac4_any_change_to_a_pending_mission_returns_it_to_draft():
121	    assert mission_status_after(M.PENDING_APPROVAL, Action.EDIT_MISSION) == M.DRAFT
122	    assert mission_status_after(M.DRAFT, Action.EDIT_MISSION) == M.DRAFT
123	
124	
125	def test_m1_transfer_sends_pending_back_to_draft_but_leaves_draft_and_active_alone():
126	    assert mission_status_after(M.PENDING_APPROVAL, Action.TRANSFER) == M.DRAFT
127	    assert mission_status_after(M.DRAFT, Action.TRANSFER) == M.DRAFT
128	    assert mission_status_after(M.ACTIVE, Action.TRANSFER) == M.ACTIVE
129	
130	
131	# --- Back to Draft: touch_for_change ------------------------------------------------------
132	
133	
134	def test_touch_for_change_leaves_a_draft_mission_in_draft():
135	    assert touch_for_change(M.DRAFT) == M.DRAFT
136	
137	
138	def test_ac4_touch_for_change_sends_a_pending_mission_back_to_draft():
139	    assert touch_for_change(M.PENDING_APPROVAL) == M.DRAFT
140	
141	
142	def test_ac5_touch_for_change_refuses_an_active_mission_as_frozen():
143	    with pytest.raises(StateConflict) as raised:
144	        touch_for_change(M.ACTIVE)
145	    assert raised.value.problem.code == "mission_frozen"
146	    assert raised.value.problem.message == "Can't edit an active mission"
147	
148	
149	@pytest.mark.parametrize(
150	    "status, message",
151	    [
152	        (M.COMPLETED, "Can't edit a mission that's completed"),
153	        (M.CANCELLED, "Can't edit a mission that's cancelled"),
154	    ],
155	)
156	def test_touch_for_change_refuses_a_finished_mission_as_final(status, message):
157	    with pytest.raises(StateConflict) as raised:
158	        touch_for_change(status)
159	    assert raised.value.problem.code == "mission_final"
160	    assert raised.value.problem.message == message
161	
162	
163	def test_complete_and_cancel_reach_final_states():
164	    assert mission_status_after(M.ACTIVE, Action.COMPLETE) == M.COMPLETED
165	    for s in (M.DRAFT, M.PENDING_APPROVAL, M.ACTIVE):
166	        assert mission_status_after(s, Action.CANCEL) == M.CANCELLED
167	
168	
169	def test_status_after_refuses_a_transition_the_table_does_not_allow():
170	    with pytest.raises(ValueError):
171	        mission_status_after(M.DRAFT, Action.COMPLETE)
172	
173	
174	# --- Assignment transitions ---------------------------------------------------------------
175	
176	ASSIGNMENT_CASES = [
177	    # action, assignment status, allowed mission states
178	    (Action.PROPOSE_CREW, None, {M.DRAFT, M.PENDING_APPROVAL}),
179	    (Action.ACCEPT, A.PROPOSED, {M.DRAFT}),
180	    (Action.DECLINE, A.PROPOSED, {M.DRAFT}),
181	    (Action.WITHDRAW, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
182	    (Action.REMOVE_CREW, A.PROPOSED, {M.DRAFT, M.PENDING_APPROVAL}),
183	    (Action.REMOVE_CREW, A.ACCEPTED, {M.DRAFT, M.PENDING_APPROVAL}),
184	]
185	
186	
187	@pytest.mark.parametrize("action, current, allowed", ASSIGNMENT_CASES)
188	@pytest.mark.parametrize("mission", ALL_STATUSES)
189	def test_assignment_actions_only_in_allowed_mission_states(action, current, allowed, mission):
190	    problem = assignment_problem(action, current, mission)
191	    assert (problem is None) == (mission in allowed)
192	
193	
194	def test_ac5_active_mission_refuses_assignment_changes_with_mission_frozen():
195	    for action, current, _ in ASSIGNMENT_CASES:
196	        assert assignment_problem(action, current, M.ACTIVE).code == "mission_frozen"
197	
198	
199	@pytest.mark.parametrize(
200	    "action, current",
201	    [
202	        (Action.ACCEPT, A.ACCEPTED),
203	        (Action.DECLINE, A.ACCEPTED),
204	        (Action.WITHDRAW, A.PROPOSED),
205	        (Action.REMOVE_CREW, A.DECLINED),
206	        (Action.ACCEPT, A.WITHDRAWN),
207	    ],
208	)
209	def test_assignment_action_from_the_wrong_assignment_status_is_invalid(action, current):
210	    assert assignment_problem(action, current, M.DRAFT).code == "invalid_transition"
211	
212	
213	def test_assignment_status_after_each_action():
214	    assert assignment_status_after(Action.PROPOSE_CREW) == A.PROPOSED
215	    assert assignment_status_after(Action.ACCEPT) == A.ACCEPTED
216	    assert assignment_status_after(Action.DECLINE) == A.DECLINED
217	    assert assignment_status_after(Action.WITHDRAW) == A.WITHDRAWN
218	    assert assignment_status_after(Action.REMOVE_CREW) == A.REMOVED
219	
220	
221	@pytest.mark.parametrize("action", [Action.PROPOSE_CREW, Action.WITHDRAW, Action.REMOVE_CREW])
222	def test_ac4_roster_changes_send_a_pending_mission_back_to_draft(action):
223	    assert mission_status_after_assignment_action(M.PENDING_APPROVAL, action) == M.DRAFT
224	    assert mission_status_after_assignment_action(M.DRAFT, action) == M.DRAFT
225	
226	
227	@pytest.mark.parametrize("action", [Action.ACCEPT, Action.DECLINE])
228	def test_responding_to_a_proposal_does_not_change_the_mission(action):
229	    assert mission_status_after_assignment_action(M.DRAFT, action) == M.DRAFT
230	
231	
232	def test_cascade_on_complete_turns_accepted_into_completed():
233	    assert cascade(M.COMPLETED, A.ACCEPTED) == A.COMPLETED
234	
235	
236	def test_cascade_on_cancel_turns_open_assignments_into_cancelled():
237	    assert cascade(M.CANCELLED, A.PROPOSED) == A.CANCELLED
238	    assert cascade(M.CANCELLED, A.ACCEPTED) == A.CANCELLED
239	
240	
241	def test_cascade_leaves_closed_assignments_alone():
242	    for closed in (A.DECLINED, A.WITHDRAWN, A.REMOVED):
243	        assert cascade(M.CANCELLED, closed) == closed
244	        assert cascade(M.COMPLETED, closed) == closed
245	
246	
247	# --- Submit guard (AC-2, AC-12) -----------------------------------------------------------
248	
249	
250	def slot(id, name, open_places):
251	    return SlotSpec(id=id, position=id, name=name, open_places=open_places, requirements=(EVA,))
252	
253	
254	def entry(assignment_id, slot_spec, name, status=A.ACCEPTED, eva=4, unavailable=()):
255	    crew = CandidateFacts(
256	        crew_profile_id=assignment_id,
257	        name=name,
258	        active=True,
259	        skills={EVA.skill_id: eva},
260	        unavailable=tuple(unavailable),
261	        accepted_elsewhere=(),
262	        workload=0,
263	    )
264	    return RosterEntry(assignment_id=assignment_id, slot=slot_spec, crew=crew, status=status)
265	
266	
267	def test_complete_accepted_roster_with_enough_approvers_can_be_submitted():
268	    s = slot(1, "Specialist", 0)
269	    assert (
270	        check_submit([s], [entry(1, s, "Dana")], WINDOW, eligible_approvers=2, approvals_required=2)
271	        == []
272	    )
273	
274	
275	def test_ac2_every_problem_is_reported_at_once():
276	    commander = slot(1, "Commander", 1)  # nobody assigned yet
277	    specialist = slot(2, "Specialist", 0)
278	    roster = [
279	        entry(1, specialist, "Dana", status=A.PROPOSED),
280	        entry(2, specialist, "Hana", eva=2),
281	    ]  # accepted but no longer qualifies
282	    problems = check_submit(
283	        [commander, specialist], roster, WINDOW, eligible_approvers=1, approvals_required=2
284	    )
285	    codes = [p.code for p in problems]
286	    assert codes == [
287	        "slot_unfilled",
288	        "proposal_unanswered",
289	        "skill_below_minimum",
290	        "insufficient_approvers",
291	    ]
292	
293	
294	def test_ac2_unfilled_place_message_names_the_slot_and_count():
295	    [p] = check_submit([slot(1, "Commander", 1)], [], WINDOW, 2, 2)
296	    assert p.code == "slot_unfilled"
297	    assert "Commander" in p.message and p.refs["slot_id"] == 1
298	
299	
300	def test_ac2_unanswered_proposal_names_the_person_and_slot():
301	    s = slot(1, "Specialist", 0)
302	    [p] = check_submit([s], [entry(7, s, "Dana", status=A.PROPOSED)], WINDOW, 2, 2)
303	    assert p.code == "proposal_unanswered"
304	    assert "Dana" in p.message and "Specialist" in p.message
305	    assert p.refs["assignment_id"] == 7
306	
307	
308	def test_roster_member_who_became_unavailable_blocks_submission():
309	    s = slot(1, "Specialist", 0)
310	    leave = [DateRange(date(2027, 3, 5), date(2027, 3, 6))]
311	    [p] = check_submit([s], [entry(1, s, "Fay", unavailable=leave)], WINDOW, 2, 2)
312	    assert p.code == "unavailable"
313	
314	
315	def test_ac12_too_few_eligible_approvers_blocks_submission():
316	    s = slot(1, "Flight Surgeon", 0)
317	    [p] = check_submit(
318	        [s], [entry(1, s, "Marco")], WINDOW, eligible_approvers=1, approvals_required=2
319	    )
320	    assert p.code == "insufficient_approvers"
321	    assert "1" in p.message and "2" in p.message
322	
323	
324	# Regression: refusal wording reads naturally
325	
326	
327	@pytest.mark.parametrize(
328	    "status, action, message",
329	    [
330	        (M.DRAFT, Action.APPROVE, "Can't approve a mission in draft"),
331	        (M.PENDING_APPROVAL, Action.SUBMIT, "Can't submit a mission pending approval"),
332	        (M.ACTIVE, Action.EDIT_MISSION, "Can't edit an active mission"),
333	        (M.COMPLETED, Action.CANCEL, "Can't cancel a mission that's completed"),
334	    ],
335	)
336	def test_mission_refusal_wording(status, action, message):
337	    assert state_problem(status, action).message == message
338	
339	
340	@pytest.mark.parametrize(
341	    "action, current, mission, message",
342	    [
343	        (Action.WITHDRAW, A.ACCEPTED, M.ACTIVE, "Can't withdraw from an active mission"),
344	        (
345	            Action.ACCEPT,
346	            A.PROPOSED,
347	            M.PENDING_APPROVAL,
348	            "Can't accept a proposal on a mission pending approval",
349	        ),
350	        (
351	            Action.PROPOSE_CREW,
352	            None,
353	            M.COMPLETED,
354	            "Can't propose crew for a mission that's completed",
355	        ),
356	        (
357	            Action.REMOVE_CREW,
358	            A.ACCEPTED,
359	            M.CANCELLED,
360	            "Can't remove crew from a mission that's cancelled",
361	        ),
362	        (
363	            Action.DECLINE,
364	            A.PROPOSED,
365	            M.ACTIVE,
366	            "Can't decline a proposal on an active mission",
367	        ),
368	    ],
369	)
370	def test_assignment_refusal_wording(action, current, mission, message):
371	    assert assignment_problem(action, current, mission).message == message
372	
373	
374	# One action enum: lifecycle and permissions agree on what each action is
375	
376	
377	def test_mission_table_covers_exactly_the_mission_actions():
378	    assert set(MISSION_ALLOWED_FROM) == set(MISSION_ACTIONS)
379	
380	
381	def test_lifecycle_and_permissions_share_one_action_enum():
382	    lifecycle_keys = set(MISSION_ALLOWED_FROM) | set(lifecycle._ASSIGNMENT_RULES)
383	    assert lifecycle_keys == set(MISSION_ACTIONS) | set(ASSIGNMENT_ACTIONS)
384	    assert lifecycle_keys <= set(Action)
385	    assert all(type(key) is Action for key in lifecycle_keys)
386	    assert all(type(key) is Action for key in permissions.ROLES)
387	    # The member lifecycle uses is the very member permissions checks.
388	    assert set(permissions.ROLES) == set(Action)
389	    assert lifecycle_keys <= set(permissions.ROLES)
390	    assert not hasattr(lifecycle, "MissionAction")
391	    assert not hasattr(lifecycle, "AssignmentAction")
392	    assert permissions.Action is Action
393	
394	
395	@pytest.mark.parametrize("action", sorted(set(Action) - set(MISSION_ACTIONS)))
396	def test_mission_functions_refuse_a_non_mission_action_as_a_programming_error(action):
397	    with pytest.raises(ValueError, match="not a mission action"):
398	        state_problem(M.DRAFT, action)
399	    with pytest.raises(ValueError, match="not a mission action"):
400	        mission_status_after(M.DRAFT, action)
401	
402	
403	@pytest.mark.parametrize("action", sorted(set(Action) - set(ASSIGNMENT_ACTIONS)))
404	def test_assignment_functions_refuse_a_non_assignment_action_as_a_programming_error(action):
405	    with pytest.raises(ValueError, match="not an assignment action"):
406	        assignment_problem(action, A.PROPOSED, M.DRAFT)
407	    with pytest.raises(ValueError, match="not an assignment action"):
408	        assignment_status_after(action)
409	    with pytest.raises(ValueError, match="not an assignment action"):
410	        mission_status_after_assignment_action(M.DRAFT, action)
411	
412	
413	@pytest.mark.parametrize(
414	    "action, current, message",
415	    [
416	        (Action.REMOVE_CREW, A.DECLINED, "Can't remove an assignment that is declined"),
417	        (Action.ACCEPT, A.WITHDRAWN, "Can't accept an assignment that is withdrawn"),
418	        (Action.WITHDRAW, None, "Can't withdraw an assignment that is missing"),
419	    ],
420	)
421	def test_wrong_assignment_status_wording(action, current, message):
422	    assert assignment_problem(action, current, M.DRAFT).message == message
423	
424	
425	def test_status_after_refusal_names_the_action_in_words():
426	    with pytest.raises(ValueError, match="^edit is not allowed from active$"):
427	        mission_status_after(M.ACTIVE, Action.EDIT_MISSION)
428
```

</details>

**🔧 Read**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/unit/domain/test_dates.py"
}
```

<details>
<summary>↳ Result</summary>

```
1	from datetime import date
2	
3	import pytest
4	
5	from mission_control.domain.dates import DateRange, InvalidDateRange
6	
7	
8	def r(start: str, end: str) -> DateRange:
9	    return DateRange(date.fromisoformat(start), date.fromisoformat(end))
10	
11	
12	# Overlap (PRD §5.1 "Overlap", AC-17)
13	
14	
15	def test_ac17_ranges_sharing_only_a_boundary_day_overlap():
16	    assert r("2027-02-25", "2027-03-01").overlaps(r("2027-03-01", "2027-03-10"))
17	    assert r("2027-03-01", "2027-03-10").overlaps(r("2027-02-25", "2027-03-01"))
18	
19	
20	def test_overlap_when_one_range_contains_the_other():
21	    assert r("2027-03-01", "2027-03-31").overlaps(r("2027-03-05", "2027-03-08"))
22	    assert r("2027-03-05", "2027-03-08").overlaps(r("2027-03-01", "2027-03-31"))
23	
24	
25	def test_overlap_with_identical_single_day_ranges():
26	    assert r("2027-03-05", "2027-03-05").overlaps(r("2027-03-05", "2027-03-05"))
27	
28	
29	def test_adjacent_ranges_do_not_overlap():
30	    assert not r("2027-02-25", "2027-02-28").overlaps(r("2027-03-01", "2027-03-10"))
31	    assert not r("2027-03-01", "2027-03-10").overlaps(r("2027-02-25", "2027-02-28"))
32	
33	
34	def test_separate_ranges_do_not_overlap():
35	    assert not r("2027-01-10", "2027-01-14").overlaps(r("2027-03-01", "2027-03-10"))
36	
37	
38	# Mission-days (PRD §5.1 "Mission-days")
39	
40	
41	def test_mission_days_counts_both_start_and_end():
42	    # PRD §9: Lunar Gateway Resupply, 1–10 Mar = 10 mission-days
43	    assert r("2027-03-01", "2027-03-10").mission_days == 10
44	
45	
46	def test_mission_days_single_day_range_is_one():
47	    assert r("2027-03-05", "2027-03-05").mission_days == 1
48	
49	
50	def test_mission_days_across_month_boundary():
51	    # PRD §9: Station Reboost, 25 Feb – 2 Mar 2027 = 6 mission-days (Gus's workload)
52	    assert r("2027-02-25", "2027-03-02").mission_days == 6
53	
54	
55	# Validity (PRD M2)
56	
57	
58	def test_m2_end_before_start_is_rejected():
59	    with pytest.raises(InvalidDateRange):
60	        r("2027-03-10", "2027-03-01")
61	
62	
63	def test_m2_invalid_date_range_is_a_value_error():
64	    with pytest.raises(ValueError):
65	        r("2027-03-10", "2027-03-01")
66	
67	
68	def test_m2_past_dates_are_allowed():
69	    # PRD §9: Mars Analog Habitat, May 2026 (in the past) is a valid range
70	    past = r("2026-05-01", "2026-05-30")
71	    assert past.mission_days == 30
72	
73	
74	def test_date_range_is_immutable():
75	    rng = r("2027-03-01", "2027-03-10")
76	    with pytest.raises(AttributeError):
77	        rng.start = date(2027, 1, 1)  # type: ignore[misc]
78
```

</details>

**🔧 Bash**

```bash
find tests -name "*.py" -not -path "*/__pycache__/*"; uv run pytest -W error 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
tests/api/test_health.py
tests/unit/domain/test_lifecycle.py
tests/unit/domain/test_dates.py
tests/unit/domain/test_passwords.py
tests/unit/domain/test_approvals.py
tests/unit/domain/test_eligibility.py
tests/unit/domain/test_matching.py
tests/unit/domain/test_permissions.py
........................................................................ [ 94%]
..........................                                               [100%]
458 passed in 0.42s
```

</details>

**🔧 Bash**

```bash
sed -n 1,200p src/mission_control/domain/eligibility.py | grep -n "crew_profile_ids\|sorted" ; cat src/mission_control/domain/dates.py | head -30
```

<details>
<summary>↳ Result</summary>

```
156:                    "crew_profile_ids": [e.crew.crew_profile_id for e in in_slot],
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
```

</details>

### 🤖 Claude · 2026-10-11 12:21:50 UTC

Now writing builders.py and conftest.py.

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/builders.py",
  "content": "\"\"\"Small builders and PRD §9.1 Aurora seed records for focused domain tests.\n\nBuilders only fill in defaults. Records are frozen dataclasses, so the module-level\nconstants below can be shared between tests. Build variations with the builders or\n`dataclasses.replace`, never by mutating a constant.\n\"\"\"\n\nfrom collections.abc import Iterable, Mapping\nfrom datetime import date\nfrom types import MappingProxyType\n\nfrom mission_control.domain.dates import DateRange\nfrom mission_control.domain.enums import AssignmentStatus\nfrom mission_control.domain.records import (\n    CandidateFacts,\n    Commitment,\n    Requirement,\n    RosterEntry,\n    SlotSpec,\n)\n\n# --- Dates --------------------------------------------------------------------------------\n\n\ndef date_range(start: str, end: str) -> DateRange:\n    \"\"\"A DateRange from two ISO dates, both inclusive.\"\"\"\n    return DateRange(date.fromisoformat(start), date.fromisoformat(end))\n\n\n# --- Aurora skill catalogue (PRD §9.1) ----------------------------------------------------\n\nPILOTING, LEADERSHIP, SYS_ENG, EVA, GEOLOGY, FLIGHT_MEDICINE = 1, 2, 3, 4, 5, 6\nSKILL_NAMES: Mapping[int, str] = MappingProxyType(\n    {\n        PILOTING: \"Piloting\",\n        LEADERSHIP: \"Leadership\",\n        SYS_ENG: \"Systems Eng\",\n        EVA: \"EVA\",\n        GEOLOGY: \"Geology\",\n        FLIGHT_MEDICINE: \"Flight Medicine\",\n    }\n)\n\n\n# --- Record builders ----------------------------------------------------------------------\n\n\ndef req(skill_id: int, min_level: int) -> Requirement:\n    return Requirement(skill_id, SKILL_NAMES[skill_id], min_level)\n\n\ndef slot(\n    *requirements: Requirement,\n    id: int = 10,\n    position: int = 1,\n    name: str = \"Commander\",\n    open_places: int = 1,\n) -> SlotSpec:\n    return SlotSpec(\n        id=id,\n        position=position,\n        name=name,\n        open_places=open_places,\n        requirements=tuple(requirements),\n    )\n\n\ndef crew(\n    name: str = \"Test Crew\",\n    id: int = 1,\n    active: bool = True,\n    skills: Mapping[int, int] | None = None,\n    unavailable: Iterable[DateRange] = (),\n    accepted_elsewhere: Iterable[Commitment] = (),\n    workload: int = 0,\n) -> CandidateFacts:\n    return CandidateFacts(\n        crew_profile_id=id,\n        name=name,\n        active=active,\n        skills=skills or {},\n        unavailable=tuple(unavailable),\n        accepted_elsewhere=tuple(accepted_elsewhere),\n        workload=workload,\n    )\n\n\ndef commitment(mission_id: int, mission_name: str, start: str, end: str) -> Commitment:\n    return Commitment(mission_id, mission_name, date_range(start, end))\n\n\ndef roster_entry(\n    crew: CandidateFacts,\n    slot: SlotSpec,\n    id: int = 100,\n    status: AssignmentStatus = AssignmentStatus.ACCEPTED,\n) -> RosterEntry:\n    return RosterEntry(assignment_id=id, slot=slot, crew=crew, status=status)\n\n\n# --- Aurora seed crew (PRD §9.1) ----------------------------------------------------------\n\nSTATION_REBOOST = commitment(3, \"Station Reboost\", \"2027-02-25\", \"2027-03-02\")\n\n# IDs follow the PRD §9 table order (the stable identifier used for the last tie-break).\nANA = crew(\"Ana\", 6, skills={PILOTING: 5, LEADERSHIP: 4, SYS_ENG: 4}, workload=0)\nBEN = crew(\"Ben\", 7, skills={SYS_ENG: 4, EVA: 3}, workload=20)\nCHEN = crew(\"Chen\", 8, skills={SYS_ENG: 3}, workload=5)\nDANA = crew(\"Dana\", 9, skills={EVA: 4}, workload=5)\nELI = crew(\"Eli\", 10, skills={EVA: 4, PILOTING: 4, LEADERSHIP: 2}, workload=5)\nFAY = crew(\n    \"Fay\",\n    11,\n    skills={PILOTING: 4, LEADERSHIP: 4},\n    unavailable=[date_range(\"2027-03-05\", \"2027-03-08\")],\n)\nGUS = crew(\"Gus\", 12, skills={SYS_ENG: 5}, workload=6, accepted_elsewhere=[STATION_REBOOST])\nHANA = crew(\"Hana\", 13, skills={EVA: 3, GEOLOGY: 2}, workload=5)\nAURORA_CREW = (ANA, BEN, CHEN, DANA, ELI, FAY, GUS, HANA)\n\n# --- Aurora seed missions (PRD §9.1) ------------------------------------------------------\n\n# Lunar Gateway Resupply, 1–10 Mar 2027. Slots listed Flight Engineer first, as in the PRD.\nGATEWAY_WINDOW = date_range(\"2027-03-01\", \"2027-03-10\")\nFLIGHT_ENGINEER = slot(req(SYS_ENG, 3), id=21, position=1, name=\"Flight Engineer\")\nSPECIALIST = slot(req(EVA, 3), id=22, position=2, name=\"Mission Specialist\")\nCOMMANDER = slot(req(PILOTING, 4), req(LEADERSHIP, 3), id=23, position=3, name=\"Commander\")\nGATEWAY_SLOTS = (FLIGHT_ENGINEER, SPECIALIST, COMMANDER)\n\n# Asteroid Survey, 5–12 Mar 2027.\nASTEROID_WINDOW = date_range(\"2027-03-05\", \"2027-03-12\")\nPILOT = slot(req(PILOTING, 4), id=31, position=1, name=\"Pilot\")\nGEOLOGIST = slot(req(GEOLOGY, 4), id=32, position=2, name=\"Geologist\")\nASTEROID_SLOTS = (PILOT, GEOLOGIST)\n"
}
```

**🔧 Write**

```json
{
  "file_path": "/Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/conftest.py",
  "content": "\"\"\"Shared test setup. Puts this directory on sys.path so tests can `import builders`.\"\"\"\n\nimport sys\nfrom pathlib import Path\n\n_TESTS_DIR = str(Path(__file__).resolve().parent)\nif _TESTS_DIR not in sys.path:\n    sys.path.insert(0, _TESTS_DIR)\n"
}
```

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/builders.py (file state is current in your context — no need to Read it back)
```

</details>

<details>
<summary>↳ Result</summary>

```
File created successfully at: /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests/conftest.py (file state is current in your context — no need to Read it back)
```

</details>

**🔧 Bash**

```bash
grep -n "def suggest_roster" -A6 src/mission_control/domain/matching.py; grep -n "^from\|^import" src/mission_control/domain/matching.py
```

<details>
<summary>↳ Result</summary>

```
40:def suggest_roster(
41-    slots: Sequence[SlotSpec], candidates: Sequence[CandidateFacts], window: DateRange
42-) -> Suggestion:
43-    by_id = {c.crew_profile_id: c for c in candidates}
44-
45-    # Step 1: who could fill each slot. Computed once, then shrunk as people are placed.
46-    # Eligibility doesn't change during a run, only who is still free.
10:from collections.abc import Sequence
11:from dataclasses import dataclass
13:from mission_control.domain.dates import DateRange
14:from mission_control.domain.eligibility import is_eligible
15:from mission_control.domain.records import CandidateFacts, SlotSpec
```

</details>

### 🤖 Claude · 2026-10-11 12:22:13 UTC

Now rewriting test_matching.py's helper section and tests.

**🔧 Bash**

```bash
python3 - <<'EOF'
import re
p='tests/unit/domain/test_matching.py'
s=open(p).read()
start=s.index('import random')
end=s.index('def roster(')
header='''import random
from dataclasses import replace

from builders import (
    ANA,
    ASTEROID_SLOTS,
    ASTEROID_WINDOW,
    AURORA_CREW,
    CHEN,
    COMMANDER,
    DANA,
    ELI,
    EVA,
    FAY,
    FLIGHT_ENGINEER,
    GATEWAY_SLOTS,
    GATEWAY_WINDOW,
    GEOLOGIST,
    GEOLOGY,
    GUS,
    LEADERSHIP,
    PILOT,
    PILOTING,
    SPECIALIST,
    SYS_ENG,
    commitment,
    crew,
    date_range,
    req,
    slot,
)
from mission_control.domain.eligibility import is_eligible
from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster

# PRD §9.1 Aurora seed crew, Lunar Gateway Resupply and Asteroid Survey come from builders.


'''
s=header+s[end:]
rep=[
('        crew, slots = AURORA_CREW[:], GATEWAY_SLOTS[:]','        crew, slots = list(AURORA_CREW), list(GATEWAY_SLOTS)'),
('    gateway = Commitment(1, "Lunar Gateway Resupply", GATEWAY_WINDOW)\n    ana_committed = person(6, "Ana", ANA.skills, workload=10, accepted_elsewhere=[gateway])',
 '    gateway = commitment(1, "Lunar Gateway Resupply", "2027-03-01", "2027-03-10")\n    assert gateway.window == GATEWAY_WINDOW\n    ana_committed = replace(ANA, workload=10, accepted_elsewhere=(gateway,))'),
('ONE_SKILL = SlotSpec(1, 1, "Engineer", 1, (req(SYS_ENG, 3),))','ONE_SKILL = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=1)'),
('WINDOW = rng(','WINDOW = date_range('),
('    slot = SlotSpec(1, 1, "Commander", 1, (req(PILOTING, 4), req(LEADERSHIP, 3)))\n',
 '    commander = slot(\n        req(PILOTING, 4), req(LEADERSHIP, 3), id=1, position=1, name="Commander", open_places=1\n    )\n'),
('    assert suggest_roster([slot], [a, b], WINDOW).placements == (Placement(1, 2),)','    assert suggest_roster([commander], [a, b], WINDOW).placements == (Placement(1, 2),)'),
('    first = SlotSpec(7, 1, "First", 1, (req(SYS_ENG, 3),))','    first = slot(req(SYS_ENG, 3), id=7, position=1, name="First", open_places=1)'),
('    second = SlotSpec(5, 2, "Second", 1, (req(SYS_ENG, 3),))','    second = slot(req(SYS_ENG, 3), id=5, position=2, name="Second", open_places=1)'),
('    a_slot = SlotSpec(8, 1, "A", 1, (req(SYS_ENG, 3),))','    a_slot = slot(req(SYS_ENG, 3), id=8, position=1, name="A", open_places=1)'),
('    b_slot = SlotSpec(4, 1, "B", 1, (req(SYS_ENG, 3),))','    b_slot = slot(req(SYS_ENG, 3), id=4, position=1, name="B", open_places=1)'),
('    slots = {sl.id: sl for sl in GATEWAY_SLOTS + ASTEROID_SLOTS}','    slots = {sl.id: sl for sl in GATEWAY_SLOTS + ASTEROID_SLOTS}'),
('        GATEWAY_SLOTS + [SlotSpec(24, 4, "Extra", 5, (req(PILOTING, 1),))],\n        AURORA_CREW + [person(99, "Gone", {PILOTING: 5}, active=False)],',
 '        [*GATEWAY_SLOTS, slot(req(PILOTING, 1), id=24, position=4, name="Extra", open_places=5)],\n        [*AURORA_CREW, crew("Gone", 99, skills={PILOTING: 5}, active=False)],'),
('    slot = SlotSpec(1, 1, "Engineer", 2, (req(SYS_ENG, 3),))\n    crew = [',
 '    engineer = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=2)\n    candidates = ['),
('    assert suggest_roster([slot], crew, WINDOW).placements == (Placement(1, 2), Placement(1, 3))',
 '    assert suggest_roster([engineer], candidates, WINDOW).placements == (\n        Placement(1, 2),\n        Placement(1, 3),\n    )'),
('    slot = SlotSpec(1, 1, "Engineer", 3, (req(SYS_ENG, 3),))\n    s = suggest_roster([slot], [person(1, "A", {SYS_ENG: 3})], WINDOW)',
 '    engineer = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=3)\n    s = suggest_roster([engineer], [crew("A", 1, skills={SYS_ENG: 3})], WINDOW)'),
('    full = SlotSpec(1, 1, "Engineer", 0, (req(SYS_ENG, 3),))','    full = slot(req(SYS_ENG, 3), id=1, position=1, name="Engineer", open_places=0)'),
('    x = SlotSpec(1, 1, "X", 2, (req(SYS_ENG, 1),))','    x = slot(req(SYS_ENG, 1), id=1, position=1, name="X", open_places=2)'),
('    y = SlotSpec(2, 2, "Y", 1, (req(EVA, 1),))','    y = slot(req(EVA, 1), id=2, position=2, name="Y", open_places=1)'),
('    w = SlotSpec(3, 3, "W", 1, (req(GEOLOGY, 1),))','    w = slot(req(GEOLOGY, 1), id=3, position=3, name="W", open_places=1)'),
]
for a,b in rep:
    assert a in s, a
    s=s.replace(a,b)
# person(id, "Name", {skills}, kw...) -> crew("Name", id, skills={...}, kw...)
s=re.sub(r'person\((\d+), ("[^"]*"), (\{[^}]*\})', r'crew(\2, \1, skills=\3', s)
assert 'person(' not in s and 'SlotSpec' not in s and 'rng(' not in s, [l for l in s.splitlines() if 'person(' in l or 'SlotSpec' in l]
open(p,'w').write(s)
EOF
grep -n "Commitment\|GATEWAY_SLOTS + \|without_ana" tests/unit/domain/test_matching.py
```

<details>
<summary>↳ Result</summary>

```
69:    without_ana = [c for c in AURORA_CREW if c is not ANA]
70:    assert suggest_roster([COMMANDER], without_ana, GATEWAY_WINDOW).unfilled == (
175:    slots = {sl.id: sl for sl in GATEWAY_SLOTS + ASTEROID_SLOTS}
```

</details>

**🔧 Bash**

```bash
python3 - <<'EOF'
p='tests/unit/domain/test_matching.py'
s=open(p).read()
s=s.replace('    gateway = commitment(1, "Lunar Gateway Resupply", "2027-03-01", "2027-03-10")\n    assert gateway.window == GATEWAY_WINDOW\n','    gateway = Commitment(1, "Lunar Gateway Resupply", GATEWAY_WINDOW)\n')
s=s.replace('    commitment,\n','')
s=s.replace('from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster\n','from mission_control.domain.matching import Placement, Suggestion, Unfilled, suggest_roster\nfrom mission_control.domain.records import Commitment\n')
open(p,'w').write(s)
EOF
uv run pytest -W error tests/unit/domain/test_matching.py 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
......................                                                   [100%]
22 passed in 0.04s
```

</details>

### 🤖 Claude · 2026-10-11 12:22:39 UTC

Now test_eligibility.py.

**🔧 Bash**

```bash
python3 - <<'EOF'
p='tests/unit/domain/test_eligibility.py'
s=open(p).read()
start=0
end=s.index('# Eligibility: one test per reason')
header='''from dataclasses import replace
from datetime import date

import pytest

from builders import (
    ANA,
    COMMANDER,
    ELI,
    EVA,
    FAY,
    GUS,
    LEADERSHIP,
    PILOTING,
    SYS_ENG,
    commitment,
    crew,
    date_range,
    req,
    roster_entry,
    slot,
)
from builders import GATEWAY_WINDOW as GATEWAY
from builders import BEN, CHEN
from mission_control.domain.dates import DateRange
from mission_control.domain.eligibility import (
    DatesEdit,
    SlotEdit,
    SlotRemoval,
    ineligibility_reasons,
    invalidated_by,
    invalidated_by_skill_change,
    is_eligible,
    workload,
)
from mission_control.domain.enums import AssignmentStatus, MissionStatus
from mission_control.domain.errors import Problem
from mission_control.domain.records import ActiveAssignment, AssignmentFact

# Seed people, skills, the Gateway window (1–10 Mar 2027) and its Commander slot
# (Piloting ≥4, Leadership ≥3) come from builders (PRD §9.1).


'''
s=header+s[end:]
rep=[
# eligible
('''    ana = crew(skills={PILOTING: 5, LEADERSHIP: 4})
    assert is_eligible(ana, COMMANDER, GATEWAY)
    assert ineligibility_reasons(ana, COMMANDER, GATEWAY) == []''',
'''    assert is_eligible(ANA, COMMANDER, GATEWAY)
    assert ineligibility_reasons(ANA, COMMANDER, GATEWAY) == []'''),
('''    ana = crew(active=False, skills={PILOTING: 5, LEADERSHIP: 4})
    [problem] = ineligibility_reasons(ana, COMMANDER, GATEWAY)''',
'''    ana = replace(ANA, active=False)
    [problem] = ineligibility_reasons(ana, COMMANDER, GATEWAY)'''),
('''    eli = crew(name="Eli", skills={PILOTING: 4, LEADERSHIP: 2})
    [problem] = ineligibility_reasons(eli, COMMANDER, GATEWAY)''',
'''    [problem] = ineligibility_reasons(ELI, COMMANDER, GATEWAY)'''),
('''    fay = crew(
        name="Fay",
        skills={PILOTING: 4, LEADERSHIP: 4},
        unavailable=[DateRange(d("2027-03-05"), d("2027-03-08"))],
    )
    [problem] = ineligibility_reasons(fay, COMMANDER, GATEWAY)''',
'''    [problem] = ineligibility_reasons(FAY, COMMANDER, GATEWAY)'''),
('''    fay = crew(
        name="Fay",
        skills={PILOTING: 4, LEADERSHIP: 4},
        unavailable=[DateRange(d("2027-03-10"), d("2027-03-12"))],
    )
    assert not is_eligible(fay, COMMANDER, GATEWAY)''',
'''    fay = replace(FAY, unavailable=(date_range("2027-03-10", "2027-03-12"),))
    assert not is_eligible(fay, COMMANDER, GATEWAY)'''),
('''    reboost = Commitment(
        mission_id=3,
        mission_name="Station Reboost",
        window=DateRange(d("2027-02-25"), d("2027-03-02")),
    )
    gus = crew(name="Gus", skills={SYS_ENG: 5}, accepted_elsewhere=[reboost])
    [problem] = ineligibility_reasons(gus, slot(req(SYS_ENG, 3), name="Flight Engineer"), GATEWAY)''',
'''    [problem] = ineligibility_reasons(GUS, slot(req(SYS_ENG, 3), name="Flight Engineer"), GATEWAY)'''),
('''    telescope = Commitment(
        mission_id=5,
        mission_name="Orbital Telescope Service",
        window=DateRange(d("2027-01-10"), d("2027-01-14")),
    )
    chen = crew(
        name="Chen",
        skills={SYS_ENG: 3},
        accepted_elsewhere=[telescope],
        unavailable=[DateRange(d("2027-04-01"), d("2027-04-02"))],
    )''',
'''    telescope = commitment(5, "Orbital Telescope Service", "2027-01-10", "2027-01-14")
    chen = replace(
        CHEN,
        accepted_elsewhere=(telescope,),
        unavailable=(date_range("2027-04-01", "2027-04-02"),),
    )'''),
('''    reboost = Commitment(3, "Station Reboost", DateRange(d("2027-02-25"), d("2027-03-02")))
    person = crew(
        active=False,
        skills={},
        accepted_elsewhere=[reboost],
        unavailable=[DateRange(d("2027-03-05"), d("2027-03-05"))],
    )''',
'''    reboost = commitment(3, "Station Reboost", "2027-02-25", "2027-03-02")
    person = crew(
        active=False,
        skills={},
        accepted_elsewhere=[reboost],
        unavailable=[date_range("2027-03-05", "2027-03-05")],
    )'''),
('''def open_assignment(person: CandidateFacts, slot_spec: SlotSpec, id=100) -> RosterEntry:
    return RosterEntry(
        assignment_id=id, slot=slot_spec, crew=person, status=AssignmentStatus.ACCEPTED
    )


ANA = crew(skills={PILOTING: 5, LEADERSHIP: 4})


''',''),
('''    gus, chen = (
        crew(name="Gus", id=7, skills={SYS_ENG: 5}),
        crew(name="Chen", id=3, skills={SYS_ENG: 3}),
    )
    assignments = [open_assignment(gus, engineers, 1), open_assignment(chen, engineers, 2)]''',
'''    assignments = [roster_entry(GUS, engineers, 1), roster_entry(CHEN, engineers, 2)]'''),
('''    gus = crew(name="Gus", skills={SYS_ENG: 5})
    assert (
        invalidated_by(SlotEdit(slot_id=12, headcount=1), [open_assignment(gus, engineers)]) == []
    )''',
'''    assert invalidated_by(SlotEdit(slot_id=12, headcount=1), [roster_entry(GUS, engineers)]) == []'''),
('''    fay = crew(
        name="Fay",
        skills={PILOTING: 4, LEADERSHIP: 4},
        unavailable=[DateRange(d("2027-04-01"), d("2027-04-03"))],
    )
    edit = DatesEdit(window=DateRange(d("2027-03-30"), d("2027-04-05")))
    [problem] = invalidated_by(edit, [open_assignment(fay, COMMANDER)])''',
'''    fay = replace(FAY, unavailable=(date_range("2027-04-01", "2027-04-03"),))
    edit = DatesEdit(window=date_range("2027-03-30", "2027-04-05"))
    [problem] = invalidated_by(edit, [roster_entry(fay, COMMANDER)])'''),
('''    comms = Commitment(6, "Deep Space Comms Upgrade", DateRange(d("2027-04-01"), d("2027-04-20")))
    ben = crew(name="Ben", skills={SYS_ENG: 4}, accepted_elsewhere=[comms])
    fe = slot(req(SYS_ENG, 3), name="Flight Engineer")
    [problem] = invalidated_by(
        DatesEdit(window=DateRange(d("2027-04-15"), d("2027-04-25"))), [open_assignment(ben, fe)]
    )''',
'''    comms = commitment(6, "Deep Space Comms Upgrade", "2027-04-01", "2027-04-20")
    ben = replace(BEN, accepted_elsewhere=(comms,))
    fe = slot(req(SYS_ENG, 3), name="Flight Engineer")
    [problem] = invalidated_by(
        DatesEdit(window=date_range("2027-04-15", "2027-04-25")), [roster_entry(ben, fe)]
    )'''),
('''    edit = DatesEdit(window=DateRange(d("2027-03-02"), d("2027-03-11")))''',
'''    edit = DatesEdit(window=date_range("2027-03-02", "2027-03-11"))'''),
('''    blocked = [DateRange(d("2027-05-01"), d("2027-05-02"))]
    a = open_assignment(
        crew(name="Ana", id=1, skills={PILOTING: 5, LEADERSHIP: 4}, unavailable=blocked),
        COMMANDER,
        1,
    )
    b = open_assignment(crew(name="Chen", id=3, skills={SYS_ENG: 3}, unavailable=blocked), fe, 2)
    problems = invalidated_by(DatesEdit(window=DateRange(d("2027-05-01"), d("2027-05-05"))), [a, b])''',
'''    blocked = (date_range("2027-05-01", "2027-05-02"),)
    a = roster_entry(replace(ANA, unavailable=blocked), COMMANDER, 1)
    b = roster_entry(replace(CHEN, unavailable=blocked), fe, 2)
    problems = invalidated_by(DatesEdit(window=date_range("2027-05-01", "2027-05-05")), [a, b])'''),
('''    gus = crew(name="Gus", id=7, skills={SYS_ENG: 5})
    chen = crew(name="Chen", id=3, skills={SYS_ENG: 3})
    [problem] = invalidated_by(
        SlotEdit(slot_id=12, headcount=1),
        [open_assignment(gus, engineers, 1), open_assignment(chen, engineers, 2)],
    )
    assert "Gus" in problem.message and "Chen" in problem.message
    assert problem.refs["crew_profile_ids"] == [7, 3]''',
'''    [problem] = invalidated_by(
        SlotEdit(slot_id=12, headcount=1),
        [roster_entry(GUS, engineers, 1), roster_entry(CHEN, engineers, 2)],
    )
    assert "Gus" in problem.message and "Chen" in problem.message
    # listed in assignment order, not id order
    assert problem.refs["crew_profile_ids"] == [GUS.crew_profile_id, CHEN.crew_profile_id]
    assert problem.refs["crew_profile_ids"] == [12, 8]'''),
('''        unavailable=[DateRange(d("2027-04-01"), d("2027-04-01"))],
    )
    problems = invalidated_by(
        DatesEdit(window=DateRange(d("2027-04-01"), d("2027-04-02"))),
        [open_assignment(person, COMMANDER)],''',
'''        unavailable=[date_range("2027-04-01", "2027-04-01")],
    )
    problems = invalidated_by(
        DatesEdit(window=date_range("2027-04-01", "2027-04-02")),
        [roster_entry(person, COMMANDER)],'''),
('''    person = crew(active=False, skills={})
    first, second, *_ = ineligibility_reasons(person, COMMANDER, GATEWAY)''',
'''    person = crew(id=1, active=False, skills={})
    first, second, *_ = ineligibility_reasons(person, COMMANDER, GATEWAY)'''),
('''        crew(active=False, skills={PILOTING: 5, LEADERSHIP: 4}), COMMANDER, GATEWAY''',
'''        replace(ANA, active=False), COMMANDER, GATEWAY'''),
]
for a,b in rep:
    assert a in s, a
    s=s.replace(a,b)
s=s.replace('open_assignment(','roster_entry(')
open(p,'w').write(s)
EOF
grep -n "d(\"\|DateRange\|Commitment\|open_assignment\|date(" tests/unit/domain/test_eligibility.py
```

<details>
<summary>↳ Result</summary>

```
25:from mission_control.domain.dates import DateRange
132:    start = date(2027, 1, 1)
133:    window = DateRange(start, date.fromordinal(start.toordinal() + days - 1))
184:def test_m7_removing_a_slot_with_open_assignments_is_refused():
186:    assert problem.code == "slot_has_open_assignments"
190:def test_m7_removing_a_slot_without_open_assignments_is_allowed():
195:def test_m7_lowering_headcount_below_open_assignments_is_refused():
199:    assert [p.code for p in problems] == ["headcount_below_open_assignments"]
203:def test_m7_lowering_headcount_to_exactly_the_open_assignments_is_allowed():
```

</details>

**🔧 Bash**

```bash
python3 - <<'EOF'
p='tests/unit/domain/test_eligibility.py'
s=open(p).read()
s=s.replace('from builders import BEN, CHEN\n','')
s=s.replace('    ANA,\n    COMMANDER,','    ANA,\n    BEN,\n    CHEN,\n    COMMANDER,',1)
s=s.replace('''    # listed in assignment order, not id order
    assert problem.refs["crew_profile_ids"] == [GUS.crew_profile_id, CHEN.crew_profile_id]
    assert problem.refs["crew_profile_ids"] == [12, 8]''','''    # Gus (12) then Chen (8): assignment order, not id order
    assert problem.refs["crew_profile_ids"] == [12, 8]''')
open(p,'w').write(s)
EOF
uv run pytest -W error tests/unit/domain/test_eligibility.py 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
...................................                                      [100%]
35 passed in 0.04s
```

</details>

### 🤖 Claude · 2026-10-11 12:23:20 UTC

Now test_lifecycle.py and test_dates.py.

**🔧 Bash**

```bash
python3 - <<'EOF'
p='tests/unit/domain/test_lifecycle.py'
s=open(p).read()
rep=[
('''from datetime import date

import pytest

from mission_control.domain import lifecycle, permissions
from mission_control.domain.dates import DateRange
''','''import pytest

from builders import EVA, crew, date_range, req, roster_entry, slot
from mission_control.domain import lifecycle, permissions
'''),
('from mission_control.domain.records import CandidateFacts, Requirement, RosterEntry, SlotSpec\n',''),
('''WINDOW = DateRange(date(2027, 3, 1), date(2027, 3, 10))
EVA = Requirement(4, "EVA", 3)''','''WINDOW = date_range("2027-03-01", "2027-03-10")
EVA_3 = req(EVA, 3)'''),
('''def slot(id, name, open_places):
    return SlotSpec(id=id, position=id, name=name, open_places=open_places, requirements=(EVA,))


def entry(assignment_id, slot_spec, name, status=A.ACCEPTED, eva=4, unavailable=()):
    crew = CandidateFacts(
        crew_profile_id=assignment_id,
        name=name,
        active=True,
        skills={EVA.skill_id: eva},
        unavailable=tuple(unavailable),
        accepted_elsewhere=(),
        workload=0,
    )
    return RosterEntry(assignment_id=assignment_id, slot=slot_spec, crew=crew, status=status)


''',''),
('''    s = slot(1, "Specialist", 0)
    assert (
        check_submit([s], [entry(1, s, "Dana")], WINDOW, eligible_approvers=2, approvals_required=2)
        == []
    )''','''    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    dana = roster_entry(crew("Dana", 1, skills={EVA: 4}), s, id=1)
    assert check_submit([s], [dana], WINDOW, eligible_approvers=2, approvals_required=2) == []'''),
('''    commander = slot(1, "Commander", 1)  # nobody assigned yet
    specialist = slot(2, "Specialist", 0)
    roster = [
        entry(1, specialist, "Dana", status=A.PROPOSED),
        entry(2, specialist, "Hana", eva=2),
    ]  # accepted but no longer qualifies''','''    commander = slot(EVA_3, id=1, position=1, name="Commander", open_places=1)  # nobody yet
    specialist = slot(EVA_3, id=2, position=2, name="Specialist", open_places=0)
    roster = [
        roster_entry(crew("Dana", 1, skills={EVA: 4}), specialist, id=1, status=A.PROPOSED),
        roster_entry(crew("Hana", 2, skills={EVA: 2}), specialist, id=2),
    ]  # accepted but no longer qualifies'''),
('''    [p] = check_submit([slot(1, "Commander", 1)], [], WINDOW, 2, 2)''',
'''    commander = slot(EVA_3, id=1, position=1, name="Commander", open_places=1)
    [p] = check_submit([commander], [], WINDOW, 2, 2)'''),
('''    s = slot(1, "Specialist", 0)
    [p] = check_submit([s], [entry(7, s, "Dana", status=A.PROPOSED)], WINDOW, 2, 2)''',
'''    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    dana = roster_entry(crew("Dana", 7, skills={EVA: 4}), s, id=7, status=A.PROPOSED)
    [p] = check_submit([s], [dana], WINDOW, 2, 2)'''),
('''    s = slot(1, "Specialist", 0)
    leave = [DateRange(date(2027, 3, 5), date(2027, 3, 6))]
    [p] = check_submit([s], [entry(1, s, "Fay", unavailable=leave)], WINDOW, 2, 2)''',
'''    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    leave = [date_range("2027-03-05", "2027-03-06")]
    fay = roster_entry(crew("Fay", 1, skills={EVA: 4}, unavailable=leave), s, id=1)
    [p] = check_submit([s], [fay], WINDOW, 2, 2)'''),
('''    s = slot(1, "Flight Surgeon", 0)
    [p] = check_submit(
        [s], [entry(1, s, "Marco")], WINDOW, eligible_approvers=1, approvals_required=2
    )''','''    s = slot(EVA_3, id=1, position=1, name="Flight Surgeon", open_places=0)
    marco = roster_entry(crew("Marco", 1, skills={EVA: 4}), s, id=1)
    [p] = check_submit([s], [marco], WINDOW, eligible_approvers=1, approvals_required=2)'''),
]
for a,b in rep:
    assert a in s, a
    s=s.replace(a,b)
assert 'entry(' not in s.replace('roster_entry(','')
open(p,'w').write(s)

p='tests/unit/domain/test_dates.py'
s=open(p).read()
s=s.replace('''from mission_control.domain.dates import DateRange, InvalidDateRange


def r(start: str, end: str) -> DateRange:
    return DateRange(date.fromisoformat(start), date.fromisoformat(end))
''','''from builders import date_range as r
from mission_control.domain.dates import InvalidDateRange
''')
open(p,'w').write(s)
EOF
uv run ruff check src tests && uv run ruff format src tests && uv run ruff check src tests; uv run pytest -W error 2>&1 | tail -3
```

<details>
<summary>↳ Result</summary>

```
I001 [*] Import block is un-sorted or un-formatted
 --> tests/unit/domain/test_dates.py:1:1
  |
1 | / from datetime import date
2 | |
3 | | import pytest
4 | |
5 | | from builders import date_range as r
6 | | from mission_control.domain.dates import InvalidDateRange
  | |_________________________________________________________^
help: Organize imports
  |
7 |
  -
8 | # Overlap (PRD §5.1 "Overlap", AC-17)
  |

Found 1 error.
[*] 1 fixable with `--fix`.
........................................................................ [ 94%]
..........................                                               [100%]
458 passed in 0.44s
[This command modified 2 files you've previously read: tests/unit/domain/test_dates.py, tests/unit/domain/test_lifecycle.py. Call Read before editing.]
```

</details>

**🔧 Bash**

```bash
python3 - <<'EOF'
import re
p='tests/unit/domain/test_dates.py'
s=open(p).read()
s=s.replace('from builders import date_range as r\n','from builders import date_range\n')
s=re.sub(r'\br\(', 'date_range(', s)
open(p,'w').write(s)
EOF
uv run ruff check --fix tests && uv run ruff format src tests && uv run ruff check src tests && uv run ruff format --check src tests; uv run pytest -W error 2>&1 | tail -3; grep -n "^from\|^import\|date(" tests/unit/domain/test_dates.py
```

<details>
<summary>↳ Result</summary>

```
E501 Line too long (102 > 100)
  --> tests/unit/domain/test_dates.py:26:101
   |
25 | def test_adjacent_ranges_do_not_overlap():
26 |     assert not date_range("2027-02-25", "2027-02-28").overlaps(date_range("2027-03-01", "2027-03-10"))
   |                                                                                                     ^^
27 |     assert not date_range("2027-03-01", "2027-03-10").overlaps(date_range("2027-02-25", "2027-02-28"))
   |

E501 Line too long (102 > 100)
  --> tests/unit/domain/test_dates.py:27:101
   |
25 | def test_adjacent_ranges_do_not_overlap():
26 |     assert not date_range("2027-02-25", "2027-02-28").overlaps(date_range("2027-03-01", "2027-03-10"))
27 |     assert not date_range("2027-03-01", "2027-03-10").overlaps(date_range("2027-02-25", "2027-02-28"))
   |                                                                                                     ^^

E501 Line too long (102 > 100)
  --> tests/unit/domain/test_dates.py:31:101
   |
30 | def test_separate_ranges_do_not_overlap():
31 |     assert not date_range("2027-01-10", "2027-01-14").overlaps(date_range("2027-03-01", "2027-03-10"))
   |                                                                                                     ^^

Found 4 errors (1 fixed, 3 remaining).
........................................................................ [ 94%]
..........................                                               [100%]
458 passed in 0.33s
1:from datetime import date
3:import pytest
5:from builders import date_range
6:from mission_control.domain.dates import InvalidDateRange
73:        rng.start = date(2027, 1, 1)  # type: ignore[misc]
[This command modified 1 file you've previously read: tests/unit/domain/test_dates.py. Call Read before editing.]
```

</details>

**🔧 Bash**

```bash
uv run ruff format src tests && uv run ruff check src tests && uv run ruff format src tests; sed -n 20,35p tests/unit/domain/test_dates.py
```

<details>
<summary>↳ Result</summary>

```
2 files reformatted, 22 files left unchanged
All checks passed!
24 files left unchanged

def test_overlap_with_identical_single_day_ranges():
    assert date_range("2027-03-05", "2027-03-05").overlaps(date_range("2027-03-05", "2027-03-05"))


def test_adjacent_ranges_do_not_overlap():
    assert not date_range("2027-02-25", "2027-02-28").overlaps(
        date_range("2027-03-01", "2027-03-10")
    )
    assert not date_range("2027-03-01", "2027-03-10").overlaps(
        date_range("2027-02-25", "2027-02-28")
    )


def test_separate_ranges_do_not_overlap():
    assert not date_range("2027-01-10", "2027-01-14").overlaps(
[This command modified 2 files you've previously read: tests/unit/domain/test_eligibility.py, tests/unit/domain/test_dates.py. Call Read before editing.]
```

</details>

**🔧 Bash**

```bash
uv run pytest -W error 2>&1 | tail -2; uv run ruff check src tests && uv run ruff format src tests; grep -c "^def test_\|^    def test_" tests/unit/domain/test_{eligibility,matching,lifecycle,dates}.py; sed -n 255,300p tests/unit/domain/test_lifecycle.py
```

<details>
<summary>↳ Result</summary>

```
..........................                                               [100%]
458 passed in 0.35s
All checks passed!
24 files left unchanged
tests/unit/domain/test_lifecycle.py:39
tests/unit/domain/test_dates.py:12
tests/unit/domain/test_matching.py:22
tests/unit/domain/test_eligibility.py:35
    specialist = slot(EVA_3, id=2, position=2, name="Specialist", open_places=0)
    roster = [
        roster_entry(crew("Dana", 1, skills={EVA: 4}), specialist, id=1, status=A.PROPOSED),
        roster_entry(crew("Hana", 2, skills={EVA: 2}), specialist, id=2),
    ]  # accepted but no longer qualifies
    problems = check_submit(
        [commander, specialist], roster, WINDOW, eligible_approvers=1, approvals_required=2
    )
    codes = [p.code for p in problems]
    assert codes == [
        "slot_unfilled",
        "proposal_unanswered",
        "skill_below_minimum",
        "insufficient_approvers",
    ]


def test_ac2_unfilled_place_message_names_the_slot_and_count():
    commander = slot(EVA_3, id=1, position=1, name="Commander", open_places=1)
    [p] = check_submit([commander], [], WINDOW, 2, 2)
    assert p.code == "slot_unfilled"
    assert "Commander" in p.message and p.refs["slot_id"] == 1


def test_ac2_unanswered_proposal_names_the_person_and_slot():
    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    dana = roster_entry(crew("Dana", 7, skills={EVA: 4}), s, id=7, status=A.PROPOSED)
    [p] = check_submit([s], [dana], WINDOW, 2, 2)
    assert p.code == "proposal_unanswered"
    assert "Dana" in p.message and "Specialist" in p.message
    assert p.refs["assignment_id"] == 7


def test_roster_member_who_became_unavailable_blocks_submission():
    s = slot(EVA_3, id=1, position=1, name="Specialist", open_places=0)
    leave = [date_range("2027-03-05", "2027-03-06")]
    fay = roster_entry(crew("Fay", 1, skills={EVA: 4}, unavailable=leave), s, id=1)
    [p] = check_submit([s], [fay], WINDOW, 2, 2)
    assert p.code == "unavailable"


def test_ac12_too_few_eligible_approvers_blocks_submission():
    s = slot(EVA_3, id=1, position=1, name="Flight Surgeon", open_places=0)
    marco = roster_entry(crew("Marco", 1, skills={EVA: 4}), s, id=1)
    [p] = check_submit([s], [marco], WINDOW, eligible_approvers=1, approvals_required=2)
    assert p.code == "insufficient_approvers"
```

</details>

**🔧 SubagentHandback**

```json
{
  "message": "I've added `tests/builders.py` and moved all four test files over to it. The test count is the same before and after: **458 passed**. I didn't touch anything under src/, docs/, pyproject.toml or CLAUDE.md, and I ran no git commands (the directory isn't a git repo anyway). No test was renamed or deleted, and the per-file counts are unchanged: eligibility 35, matching 22, lifecycle 39, dates 12.\n\n**What `tests/builders.py` provides**\n- `date_range(start, end)` from ISO strings.\n- Skill ids from PRD §9.1: `PILOTING=1, LEADERSHIP=2, SYS_ENG=3, EVA=4, GEOLOGY=5, FLIGHT_MEDICINE=6`, and a read-only `SKILL_NAMES` lookup.\n- Builders, each just filling in defaults:\n  - `req(skill_id, min_level)` takes the name from `SKILL_NAMES`.\n  - `slot(*requirements, id=10, position=1, name=\"Commander\", open_places=1)`.\n  - `crew(name=\"Test Crew\", id=1, active=True, skills=None, unavailable=(), accepted_elsewhere=(), workload=0)`.\n  - `commitment(mission_id, mission_name, start, end)`.\n  - `roster_entry(crew, slot, id=100, status=AssignmentStatus.ACCEPTED)`.\n- Seed constants, with the same values test_matching.py had:\n  - `STATION_REBOOST` (id 3, 25 Feb – 2 Mar 2027).\n  - The crew `ANA`=6, `BEN`=7, `CHEN`=8, `DANA`=9, `ELI`=10, `FAY`=11, `GUS`=12, `HANA`=13, and `AURORA_CREW`.\n  - Lunar Gateway Resupply: `GATEWAY_WINDOW`, `FLIGHT_ENGINEER` (21), `SPECIALIST` (22), `COMMANDER` (23), `GATEWAY_SLOTS`.\n  - Asteroid Survey: `ASTEROID_WINDOW`, `PILOT` (31), `GEOLOGIST` (32), `ASTEROID_SLOTS`.\n  - `AURORA_CREW`, `GATEWAY_SLOTS` and `ASTEROID_SLOTS` are tuples, so they can't be changed by mistake.\n\n**How it's importable:** a new `tests/conftest.py` puts the tests directory on `sys.path`, so test files can `from builders import ...`. `uv run pytest` works from the repo root.\n\n**Changes per file**\n- **test_matching.py:**\n  - Removed `SKILL`, `req`, `rng`, `person`, `STATION_REBOOST`, the eight seed people and the Gateway/Asteroid windows and slots; they're all imported now. `roster()` stays local.\n  - Local `SlotSpec(...)` and `person(...)` calls now use `slot(..., id=, position=, name=, open_places=)` and `crew(name, id, skills=..., ...)` with the same values.\n  - S3b's committed Ana is `replace(ANA, workload=10, accepted_elsewhere=(gateway,))`.\n  - Because the seed collections are tuples now, I used `list(...)` before shuffling and `[*X, extra]` where the test adds to them.\n- **test_eligibility.py:**\n  - Removed `NAMES`, `req`, `slot`, `crew`, `d`, local `GATEWAY`/`COMMANDER`/`ANA` and `open_assignment`; the last is now `roster_entry`.\n  - Seed people are used directly where a test models them: `ANA`, `ELI`, `FAY`, `GUS`. Variations use `dataclasses.replace`: inactive Ana, Fay with other unavailability, Chen with the Telescope commitment, Ben with Deep Space Comms.\n  - `Commitment(...)` became `commitment(...)`, and `fact()` stays local.\n- **test_lifecycle.py:** removed the local `EVA` requirement (now `EVA_3 = req(EVA, 3)`), `slot()` and `entry()`. Every roster entry is now `roster_entry(crew(name, id, skills={EVA: n}, ...), slot, id=..., status=...)`. I kept the same values, including crew id = assignment id and position = slot id.\n- **test_dates.py:** `r()` was removed and calls `date_range()` instead.\n\n**Where the numbers or inputs changed**\n- **Gus and Chen's ids:** `test_m7_headcount_refusal_names_every_assigned_person` expected `crew_profile_ids == [7, 3]`. With the shared ids it now expects `[12, 8]`. That is still Gus then Chen, larger id first, so it still checks that people are listed in assignment order, not sorted by id.\n- **Commander slot id:** eligibility's Commander is now the shared seed slot, id 23 instead of 10. The tests only refer to it as `COMMANDER.id`, and its id doesn't clash with the other slot ids those tests use (11, 12, 99).\n- **Default crew id:** `test_problems_from_one_check_do_not_share_refs` now passes `id=1` explicitly, so its expected `crew_profile_id: 1` stays the same.\n- **Extra seed skills:** using the seed people adds skills the old local copies didn't have (Ana also has Systems Eng 4, Eli also has EVA 4, and Gus/Chen/Ben now carry their seed workload). None of the slots in those tests require those skills, and every assertion is unchanged and passes.\n\n**Final output**\n- `uv run pytest -W error`: `458 passed in 0.35s`\n- `uv run ruff check src tests`: `All checks passed!`\n- `uv run ruff format src tests`: `24 files left unchanged`\n\nFiles are in /Users/pritanbarai/Desktop/JOBS/mutinex_mission_control/tests:\n- builders.py (new)\n- conftest.py (new)\n- unit/domain/test_eligibility.py\n- unit/domain/test_matching.py\n- unit/domain/test_lifecycle.py\n- unit/domain/test_dates.py"
}
```

<details>
<summary>↳ Result</summary>

```
{"success":true,"message":"Report delivered to your caller."}
```

</details>
