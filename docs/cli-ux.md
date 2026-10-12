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
