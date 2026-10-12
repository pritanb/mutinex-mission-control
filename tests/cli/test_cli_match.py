"""M16: `mc missions match` renders the matcher preview exactly as the approved mock sessions in
docs/cli-ux.md (PRD §6, AC-18, AC-19, AC-22; S2, S3)."""

import json

from cli_fakes import S2_PREVIEW, S3_PREVIEW, error, gateway, ok

S2_TABLE = (
    "Lunar Gateway Resupply · 1–10 Mar 2027 · Draft\n"
    "✓ Crew suggested for all 3 open places. Nothing has been proposed yet.\n"
    "\n"
    "  Slot                 Suggested   Workload   Proficiency   Pick\n"
    "  Flight Engineer      Chen        5 days     3             2\n"
    "  Mission Specialist   Dana        5 days     4             3\n"
    "  Commander            Ana         0 days     9             1\n"
    "\n"
    "  Slots with the fewest eligible crew are filled first. Within a slot, lowest workload\n"
    "  wins, then highest proficiency (sum of the required skill levels).\n"
)


def test_s2_full_suggestion_for_the_owner(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1/match", ok(S2_PREVIEW))

    result = mc("missions", "match", "1")

    assert result.exit_code == 0
    assert result.stdout == S2_TABLE
    assert result.stderr == ("Next: mc missions match 1 --apply    proposes Ana, Chen and Dana\n")
    assert api.writes() == []  # AC-22: a preview changes nothing


def test_s2_director_sees_the_same_table_without_the_apply_hint(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/missions/1/match", ok(S2_PREVIEW | {"can_apply": False}))

    result = mc("missions", "match", "1")

    assert result.exit_code == 0
    assert result.stdout == S2_TABLE
    assert result.stderr == ""


def test_s3_unfilled_place_is_reported_but_is_not_an_error(mc, api):
    mc.login_as("tok-nora", "nora@aurora.example")
    api.on("GET", "/missions/2/match", ok(S3_PREVIEW))

    result = mc("missions", "match", "2")

    assert result.exit_code == 0
    assert result.stdout == (
        "Asteroid Survey · 5–12 Mar 2027 · Draft\n"
        "! Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.\n"
        "\n"
        "  Slot        Suggested   Workload   Proficiency   Pick\n"
        "  Pilot       Ana         0 days     5             1\n"
        "  Geologist   unfilled (1 place)\n"
        "\n"
        "  The mission can't be submitted until every place is filled.\n"
    )
    assert result.stderr == (
        "Next: mc missions match 2 --apply    proposes Ana for Pilot\n"
        "      mc missions propose 2 --slot Geologist --crew EMAIL    fill Geologist by hand\n"
    )


def test_m16_plain_words_with_no_color(mc, api, monkeypatch):
    mc.login_as("tok-nora", "nora@aurora.example")
    monkeypatch.setenv("NO_COLOR", "1")
    api.on("GET", "/missions/2/match", ok(S3_PREVIEW))

    result = mc("missions", "match", "2", color=None)

    assert result.stdout.startswith(
        "Asteroid Survey - 5-12 Mar 2027 - Draft\n"
        "Note: Crew suggested for 1 of 2 open places. Geologist has no eligible crew left.\n"
    )


def test_m16_match_json_mirrors_the_preview(mc, api):
    mc.login_as()
    api.on("GET", "/missions/2/match", ok(S3_PREVIEW))

    result = mc("missions", "match", "2", "--json")

    assert result.exit_code == 0
    assert json.loads(result.stdout) == S3_PREVIEW
    assert result.stderr == ""


def test_m16_refused_when_the_mission_is_active(mc, api):
    mc.login_as()
    api.on(
        "GET",
        "/missions/5/match",
        error(409, "mission_frozen", "Can't suggest crew for an active mission"),
    )

    result = mc("missions", "match", "5")

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == (
        "✗ Mission 5: Can't suggest crew for an active mission.\n"
        "  Only draft missions can be matched. See its crew: mc missions show 5\n"
    )


def test_m16_refused_when_pending_or_final(mc, api):
    mc.login_as()
    api.on(
        "GET",
        "/missions/6/match",
        error(409, "invalid_transition", "Can't suggest crew for a mission pending approval"),
    )
    api.on(
        "GET",
        "/missions/7/match",
        error(409, "mission_final", "Can't suggest crew for a mission that's completed"),
    )

    pending = mc("missions", "match", "6")
    final = mc("missions", "match", "7")

    assert pending.stderr == (
        "✗ Mission 6: Can't suggest crew for a mission pending approval.\n"
        "  Only draft missions can be matched. Its places are already filled: "
        "mc missions show 6\n"
    )
    assert final.stderr == (
        "✗ Mission 7: Can't suggest crew for a mission that's completed.\n"
        "  Only draft missions can be matched. See it: mc missions show 7\n"
    )


def test_v2_hidden_mission_looks_exactly_like_an_unknown_id(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/missions/1/match", error(404, "not_found", "Mission not found"))

    result = mc("missions", "match", "1")

    assert result.exit_code == 1
    assert result.stderr == "✗ Mission 1 not found.\n  See your missions: mc missions list\n"


def test_m3_another_leads_mission_is_refused_with_a_way_to_see_the_owner(mc, api):
    mc.login_as("tok-nora", "nora@aurora.example")
    api.on(
        "GET",
        "/missions/1/match",
        error(
            403, "not_owner", "Only the owner or a Director can see suggested crew for this mission"
        ),
    )

    result = mc("missions", "match", "1")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ Only the owner or a Director can see suggested crew for this mission.\n"
        "  See who owns it: mc missions show 1\n"
    )


def test_ac22_apply_creates_proposals_and_names_them(mc, api):
    mc.login_as()
    api.on(
        "POST",
        "/missions/1/match/apply",
        ok(
            [
                {
                    "id": 21,
                    "mission_id": 1,
                    "slot_id": 3,
                    "crew_profile_id": 6,
                    "status": "proposed",
                    "reason": None,
                },
                {
                    "id": 22,
                    "mission_id": 1,
                    "slot_id": 1,
                    "crew_profile_id": 8,
                    "status": "proposed",
                    "reason": None,
                },
                {
                    "id": 23,
                    "mission_id": 1,
                    "slot_id": 2,
                    "crew_profile_id": 9,
                    "status": "proposed",
                    "reason": None,
                },
            ],
            status=201,
        ),
    )
    proposed = [
        {"id": 21, "slot_id": 3, "slot_name": "Commander", "crew_profile_id": 6,
         "crew_name": "Ana Okafor", "status": "proposed", "reason": None},
        {"id": 22, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,
         "crew_name": "Chen Wu", "status": "proposed", "reason": None},
        {"id": 23, "slot_id": 2, "slot_name": "Mission Specialist", "crew_profile_id": 9,
         "crew_name": "Dana Reyes", "status": "proposed", "reason": None},
    ]  # fmt: skip
    api.on("GET", "/missions/1", ok(gateway(assignments=proposed, open_places={1: 0, 2: 0, 3: 0})))

    result = mc("missions", "match", "1", "--apply")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == (
        "✓ Proposed 3 crew for Lunar Gateway Resupply. Each of them needs to accept.\n"
        "\n"
        "  Assignment   Crew         Slot\n"
        "  21           Ana Okafor   Commander\n"
        "  22           Chen Wu      Flight Engineer\n"
        "  23           Dana Reyes   Mission Specialist\n"
    )
    assert "Next: mc missions show 1" in result.stderr
    assert len(api.sent("POST", "/missions/1/match/apply")) == 1


def test_m16_apply_with_nothing_to_propose(mc, api):
    mc.login_as()
    api.on("POST", "/missions/2/match/apply", ok([], status=201))

    result = mc("missions", "match", "2", "--apply")

    assert result.exit_code == 0
    assert result.stdout == "! No crew could be proposed: no eligible crew for the open places.\n"
