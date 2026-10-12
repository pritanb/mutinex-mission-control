# Mission Control

A multi-tenant API and CLI for planning space missions. Organisations manage crew and their skills, Mission Leads build missions and get crew suggestions from a deterministic matcher, and Directors approve missions before they go active.

## Prerequisites

- Python 3.12, with SQLite 3.37 or later (standard Python 3.12 builds have it)
- [uv](https://docs.astral.sh/uv/). It can install Python too: `uv python install 3.12`

## Quick start

```bash
uv sync
uv run mc-admin seed --reset      # demo data in ./mission_control.db
uv run mc-server                  # API on http://127.0.0.1:8000; leave it running
```

In a second terminal, from the same folder:

```bash
uv run mc login --email lee@aurora.example    # password: orbital launch window
uv run mc missions list
```

Every demo account's password is `orbital launch window`. `mc login` asks for it with the input hidden.

## Demo: the golden path

Lunar Gateway Resupply (mission 1) is a draft with three empty slots. Take it all the way to Completed. Each `mc login` replaces the previous session, so one terminal is enough. Start from a fresh seed (`uv run mc-admin seed --reset`, with the server stopped).

**1. Lee, the owning Lead, asks the matcher for crew and proposes its suggestion.**

```bash
uv run mc login --email lee@aurora.example
uv run mc inbox
uv run mc missions match 1                     # Commander → Ana, Flight Engineer → Chen, Mission Specialist → Dana
uv run mc missions match 1 --apply             # proposes them as assignments 11, 12 and 13
```

**2. Each crew member accepts their proposal.**

```bash
uv run mc login --email ana@aurora.example
uv run mc assignments list --pending
uv run mc assignments accept 11
uv run mc login --email chen@aurora.example
uv run mc assignments accept 12
uv run mc login --email dana@aurora.example
uv run mc assignments accept 13
```

**3. Lee submits it. Aurora needs two approvals.**

```bash
uv run mc login --email lee@aurora.example
uv run mc missions submit 1
```

**4. Directors approve. Ruth created the mission, so she can't approve it.**

```bash
uv run mc login --email ruth@aurora.example
uv run mc missions approve 1                   # refused: Ruth created this mission
uv run mc login --email marco@aurora.example
uv run mc missions approve 1                   # pending approval, 1 of 2
uv run mc login --email ingrid@aurora.example
uv run mc missions approve 1                   # 2 of 2: the mission is active
```

**5. Lee completes it, and the history shows every step with who did it and when.**

```bash
uv run mc login --email lee@aurora.example
uv run mc missions complete 1
uv run mc missions history 1
```

**Tenant isolation.** Sam is a Director at Helix Orbital. Aurora's missions don't exist as far as he can tell.

```bash
uv run mc login --email sam@helix.example
uv run mc missions list                        # only Helix's Payload Demo 1
uv run mc missions show 1                      # refused: looks exactly like an unknown ID
```

Every command has `--help`, and most take `--json`. `mc` exits with `0` OK, `1` refused, `2` usage, `3` not logged in, `4` server unreachable or busy, `130` interrupted.

## Demo accounts

All passwords are `orbital launch window`. Mission and crew details are in [PRD §9](docs/prd.md#9-seed-data-and-scenarios).

| Name | Email | Role | Organisation |
|---|---|---|---|
| Ruth Adeyemi | ruth@aurora.example | Director | Aurora Space Agency |
| Marco Bianchi | marco@aurora.example | Director | Aurora Space Agency |
| Ingrid Holm | ingrid@aurora.example | Director | Aurora Space Agency |
| Lee Park | lee@aurora.example | Mission Lead | Aurora Space Agency |
| Nora Quinn | nora@aurora.example | Mission Lead | Aurora Space Agency |
| Ana Okafor | ana@aurora.example | Mission Lead | Aurora Space Agency |
| Ben Ito | ben@aurora.example | Crew Member | Aurora Space Agency |
| Chen Wu | chen@aurora.example | Crew Member | Aurora Space Agency |
| Dana Reyes | dana@aurora.example | Crew Member | Aurora Space Agency |
| Eli Novak | eli@aurora.example | Crew Member | Aurora Space Agency |
| Fay Moreau | fay@aurora.example | Crew Member | Aurora Space Agency |
| Gus Patel | gus@aurora.example | Crew Member | Aurora Space Agency |
| Hana Sato | hana@aurora.example | Crew Member | Aurora Space Agency |
| Sam Rivera | sam@helix.example | Director | Helix Orbital |
| Priya Nair | priya@helix.example | Mission Lead | Helix Orbital |
| Kai Tanaka | kai@helix.example | Crew Member | Helix Orbital |
| Lena Fischer | lena@helix.example | Crew Member | Helix Orbital |
| Omar Haddad | omar@helix.example | Crew Member | Helix Orbital |
| Tess Moreno | tess@helix.example | Crew Member | Helix Orbital |

Aurora needs 2 approvals per mission and Helix needs 1. Marco and Ana also have crew profiles, so they can be rostered.

## Operators: `mc-admin`

`mc-admin` works on the database file directly, so run it on the machine that runs `mc-server`. There's no self-service signup: organisations come from the seed or from `create-org`.

```bash
uv run mc-admin init-db                        # an empty database, if you don't want the demo data
uv run mc-admin create-org --name "Orion Labs" --director-email zoe@orion.example --director-name "Zoe Lin"
```

`create-org` asks for the Director's password twice with the input hidden (at least 15 characters). Without a terminal, pipe it on stdin. The new organisation needs 1 approval per mission and starts with an empty skill catalogue. Its Director logs in with `mc` and sets up the rest (`mc skills add`, `mc users add`, `mc org set-approvals`).

`mc-admin seed` refuses a database that already has data. `seed --reset` deletes the file and everything in it first. Stop the server before resetting.

## Settings

Environment variables, all optional:

| Variable | Default | Used by |
|---|---|---|
| `MC_DATABASE_PATH` | `mission_control.db` in the current folder | `mc-server`, `mc-admin` |
| `MC_TOKEN_TTL_HOURS` | `12` | `mc-server` |
| `MC_DB_BUSY_TIMEOUT_MS` | `5000` | `mc-server`, `mc-admin` |
| `MC_API_URL` | `http://127.0.0.1:8000` | `mc` |

`mc-server` listens on `127.0.0.1:8000`. `mc` keeps its session token in `~/.config/mission-control/credentials.json`, readable only by you.

## Tests and lint

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```

Every test gets its own temporary SQLite file. `tests/cli/test_readme_smoke.py` runs this README's `mc-admin`, `mc-server` and `mc` commands for real, in order.

## Documents

| Document | What's in it |
|---|---|
| [`docs/brief.md`](docs/brief.md) | The assessment brief |
| [`docs/prd.md`](docs/prd.md) | Behaviour: roles, business rules, acceptance criteria, seed data and scenarios |
| [`docs/technical-design.md`](docs/technical-design.md) | Structure: architecture, schema, API, CLI, delivery plan, guidelines for coding agents, trade-offs |
| [`docs/phase-reviews.md`](docs/phase-reviews.md) | Where each phase diverged from the plan, and why |
| [`docs/cli-ux.md`](docs/cli-ux.md) | Mock CLI sessions for the matcher |
| [`docs/backlog.md`](docs/backlog.md) | Decisions deliberately left open for later |

## Code layout

```
src/mission_control/
  domain/       every business rule, as pure functions: dates, eligibility, matcher, lifecycle, permissions
  infra/        SQLite connections, schema, tenant-scoped repositories, password hashing and tokens
  services/     one use case per function: one transaction, its checks and its audit event
  api/          FastAPI app (mc-server): validates input, resolves the caller, maps errors
  cli/          the mc command, a client of the HTTP API
  seed/         the demo data, shared by mc-admin and the tests
  admin_cli.py  mc-admin: init-db, seed, create-org
tests/          unit/ (domain), integration/ (services, database), api/, cli/
```

`domain/` imports nothing from the other layers, and the CLI holds no business rules: it only calls the API. The [design](docs/technical-design.md#2-architecture) explains why.

## How it was built

The design documents were written first and then used to direct a coding agent (Claude Code):

- [`CLAUDE.md`](CLAUDE.md) holds the agent's rules: one approved module at a time, tests first, a real run, a read-only review, and no commit without approval. Independent modules ran in parallel git worktrees.
- [Design §9](docs/technical-design.md#9-delivery-plan) is the module-by-module plan, and [§10](docs/technical-design.md#10-guidelines-for-implementing-agents) the guidelines the agent followed.
- [`docs/phase-reviews.md`](docs/phase-reviews.md) records each phase's divergences and its end-of-phase review.
- The full, unedited AI transcripts are submitted with this repository.
