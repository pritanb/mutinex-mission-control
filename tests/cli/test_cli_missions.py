"""M16: mission commands. References (missions by ID, people by email, skills by name, slots by
name or position), the `--slot` spec on the wire, confirmations before changing a pending mission
or cancelling, and what each command reports (design §8; PRD M1–M7, C4)."""

import json

from cli_fakes import CREW, LEE_ME, SKILLS, USERS, error, gateway, ok, problem, summary

NEW_MISSION = gateway() | {"id": 8, "name": "Europa Flyby", "start_date": "2027-09-01",
                           "end_date": "2027-09-20"}  # fmt: skip


def _skills_and_crew(api):
    api.on("GET", "/skills", ok(SKILLS))
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/users", ok(USERS))


# Create


def test_m2_create_sends_slots_with_skills_resolved_by_name(mc, api):
    mc.login_as()
    _skills_and_crew(api)
    api.on("POST", "/missions", ok(NEW_MISSION, status=201))

    result = mc(
        "missions", "create", "--name", "Europa Flyby", "--start", "2027-09-01",
        "--end", "2027-09-20", "--slot", "Commander:1:piloting>=4,Leadership>=3",
        "--slot", "Flight Engineer:2:Systems Engineering>=3",
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/missions")[0].body == {
        "name": "Europa Flyby",
        "start_date": "2027-09-01",
        "end_date": "2027-09-20",
        "slots": [
            {
                "name": "Commander",
                "headcount": 1,
                "requirements": [
                    {"skill_id": 1, "min_level": 4},
                    {"skill_id": 2, "min_level": 3},
                ],
            },
            {
                "name": "Flight Engineer",
                "headcount": 2,
                "requirements": [{"skill_id": 3, "min_level": 3}],
            },
        ],
    }
    assert result.stdout == "✓ Created mission 8: Europa Flyby · 1–20 Sep 2027 · Draft\n"
    assert "Next: mc missions match 8" in result.stderr


def test_m1_director_names_the_owner_by_email(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    _skills_and_crew(api)
    api.on("POST", "/missions", ok(NEW_MISSION, status=201))

    result = mc(
        "missions", "create", "--name", "Europa Flyby", "--start", "2027-09-01",
        "--end", "2027-09-20", "--slot", "Commander:1:Piloting>=4", "--owner", "LEE@aurora.example",
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/missions")[0].body["owner_id"] == 4


def test_m16_create_with_an_unknown_skill_names_it_and_sends_nothing(mc, api):
    mc.login_as()
    _skills_and_crew(api)

    result = mc(
        "missions", "create", "--name", "X", "--start", "2027-09-01", "--end", "2027-09-02",
        "--slot", "Commander:1:Pilotting>=4",
    )  # fmt: skip

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ There's no skill called 'Pilotting'.\n  See the skills: mc skills list\n"
    )
    assert api.writes() == []


def test_m16_create_with_a_malformed_slot_is_a_usage_error(mc, api):
    mc.login_as()

    result = mc(
        "missions", "create", "--name", "X", "--start", "2027-09-01", "--end", "2027-09-02",
        "--slot", "Commander-1-Piloting4",
    )  # fmt: skip

    assert result.exit_code == 2
    assert "NAME:HEADCOUNT:SKILL>=LEVEL" in result.stderr
    assert api.calls == []


def test_m16_dates_must_be_iso(mc, api):
    mc.login_as()

    result = mc(
        "missions", "create", "--name", "X", "--start", "1 Sep", "--end", "2027-09-02",
        "--slot", "Commander:1:Piloting>=4",
    )  # fmt: skip

    assert result.exit_code == 2
    assert "Use YYYY-MM-DD" in result.stderr
    assert api.calls == []


def test_m2_end_before_start_is_judged_by_the_server(mc, api):
    mc.login_as()
    _skills_and_crew(api)
    api.on(
        "POST",
        "/missions",
        error(422, "validation_error", "The end date can't be before the start date"),
    )

    result = mc(
        "missions", "create", "--name", "X", "--start", "2027-09-05", "--end", "2027-09-01",
        "--slot", "Commander:1:Piloting>=4",
    )  # fmt: skip

    assert result.exit_code == 1
    assert "✗ The end date can't be before the start date." in result.stderr


# Lists and views


def test_m16_list_missions_as_a_table(mc, api):
    mc.login_as()
    api.on(
        "GET",
        "/missions",
        ok(
            [
                summary(gateway()),
                summary(gateway("pending_approval") | {"id": 6, "name": "Deep Space Comms Upgrade",
                                               "start_date": "2027-04-01", "end_date": "2027-04-20",
                                               "owner_id": 5, "owner_name": "Nora Quinn"}),
            ]
        ),
    )  # fmt: skip

    result = mc("missions", "list")

    assert result.exit_code == 0
    assert result.stdout == (
        "  ID   Mission                    Dates           Status             Owner\n"
        "  1    Lunar Gateway Resupply     1–10 Mar 2027   Draft              Lee Park\n"
        "  6    Deep Space Comms Upgrade   1–20 Apr 2027   Pending approval   Nora Quinn\n"
    )


def test_v2_empty_mission_list(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/missions", ok([]))

    result = mc("missions", "list")

    assert result.exit_code == 0
    assert result.stdout == "No missions to show.\n"


def test_m16_show_mission_lists_slots_crew_and_approvals(mc, api):
    mc.login_as()
    crew_rows = [
        {"id": 21, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,
         "crew_name": "Chen Wu", "status": "accepted", "reason": None},
    ]  # fmt: skip
    approvals = [
        {"director_id": 2, "director_name": "Marco Bianchi", "decision": "approve", "reason": None}
    ]
    api.on(
        "GET",
        "/missions/1",
        ok(gateway("pending_approval", crew_rows, approvals, open_places={1: 0})),
    )

    result = mc("missions", "show", "1")

    assert result.exit_code == 0
    assert result.stdout == (
        "Lunar Gateway Resupply · 1–10 Mar 2027 · Pending approval\n"
        "Owner Lee Park · created by Ruth Adeyemi\n"
        "\n"
        "  #   Slot                 Requires                     Places\n"
        "  1   Flight Engineer      Systems Engineering>=3       full\n"
        "  2   Mission Specialist   EVA>=3                       1 of 1 open\n"
        "  3   Commander            Piloting>=4, Leadership>=3   1 of 1 open\n"
        "\n"
        "  Assignment   Crew      Slot              Status\n"
        "  21           Chen Wu   Flight Engineer   Accepted\n"
        "\n"
        "Approvals: 1 of 2 (Marco Bianchi)\n"
    )


def test_show_says_who_rejected_a_mission_and_why(mc, api):
    mc.login_as()
    mission = gateway() | {
        "approval_round": 1,
        "rejection": {
            "director_id": 3,
            "director_name": "Ingrid Holm",
            "decision": "reject",
            "reason": "Budget not signed off",
        },
    }
    api.on("GET", "/missions/1", ok(mission))

    result = mc("missions", "show", "1")

    assert result.exit_code == 0
    assert result.stdout.splitlines()[:3] == [
        "Lunar Gateway Resupply · 1–10 Mar 2027 · Draft",
        "Owner Lee Park · created by Ruth Adeyemi",
        "Rejected by Ingrid Holm: Budget not signed off",
    ]


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


def test_v1_history_names_the_new_owner_from_the_changes_in_a_transfer(mc, api):
    mc.login_as()

    def entry(id, data):
        return {"id": id, "created_at": "2027-01-02T10:00:00.000Z", "actor_id": 1,
                "actor_name": "Ruth Adeyemi", "event": "mission.transferred",
                "assignment_id": None, "crew_profile_id": None, "from_status": None,
                "to_status": None, "reason": None, "data": data}  # fmt: skip

    changes = {"owner_id": [4, 5], "owner_name": ["Lee Park", "Nora Quinn"]}
    api.on(
        "GET",
        "/missions/1/history",
        ok([entry(1, {"mission_name": "Gateway", "changes": changes}), entry(2, {})]),
    )

    result = mc("missions", "history", "1")

    assert result.exit_code == 0
    assert result.stdout == (
        "  When (UTC)         Who            What\n"
        "  2 Jan 2027 10:00   Ruth Adeyemi   Handed the mission to Nora Quinn\n"
        "  2 Jan 2027 10:00   Ruth Adeyemi   Changed the owner\n"
    )


# Confirmations (C4)


def test_c4_editing_a_pending_mission_asks_first_and_yes_changes_it(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
    api.on("PATCH", "/missions/1", ok(gateway()))

    result = mc("missions", "edit", "1", "--end", "2027-03-12", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert (
        "! Lunar Gateway Resupply is pending approval. Editing it sends it back to Draft and "
        "clears its approvals." in result.stderr
    )
    assert result.asked == [("Continue? [y/N]", False)]
    assert api.sent("PATCH", "/missions/1")[0].body == {"end_date": "2027-03-12"}
    assert result.stdout == "✓ Updated Lunar Gateway Resupply. It's back in Draft.\n"


def test_c4_declining_the_prompt_changes_nothing(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))

    result = mc("missions", "edit", "1", "--name", "New", answers=["n"])

    assert result.exit_code == 1
    assert "Nothing was changed." in result.stderr
    assert api.writes() == []


def test_c4_without_a_terminal_the_change_needs_yes(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))

    result = mc("missions", "edit", "1", "--name", "New")

    assert result.exit_code == 2
    assert "Re-run with --yes to go ahead." in result.stderr
    assert api.writes() == []


def test_c4_yes_skips_the_prompt(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
    api.on("PATCH", "/missions/1", ok(gateway()))

    result = mc("missions", "edit", "1", "--name", "New", "--yes")

    assert result.exit_code == 0, result.stderr
    assert result.asked == []


def test_c4_editing_a_draft_does_not_ask(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("PATCH", "/missions/1", ok(gateway()))

    result = mc("missions", "edit", "1", "--name", "New")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Updated Lunar Gateway Resupply.\n"


def test_m16_edit_with_nothing_to_change_is_a_usage_error(mc, api):
    mc.login_as()

    result = mc("missions", "edit", "1")

    assert result.exit_code == 2
    assert "Nothing to change" in result.stderr
    assert api.calls == []


def test_ac6_cancelling_says_how_many_assignments_were_cancelled_too(mc, api):
    mc.login_as()
    rows = [
        {"id": 21, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,
         "crew_name": "Chen Wu", "status": "cancelled", "reason": None},
        {"id": 22, "slot_id": 2, "slot_name": "Mission Specialist", "crew_profile_id": 9,
         "crew_name": "Dana Reyes", "status": "cancelled", "reason": None},
        {"id": 23, "slot_id": 3, "slot_name": "Commander", "crew_profile_id": 6,
         "crew_name": "Ana Okafor", "status": "declined", "reason": None},
    ]  # fmt: skip
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("POST", "/missions/1/cancel", ok(gateway("cancelled", rows)))

    result = mc("missions", "cancel", "1", "--reason", "Budget cut", "--yes")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Cancelled Lunar Gateway Resupply and its 2 open assignments.\n"


def test_c4_cancelling_asks_the_owner_and_sends_the_reason(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("POST", "/missions/1/cancel", ok(gateway("cancelled")))

    result = mc("missions", "cancel", "1", "--reason", "Budget cut", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert result.stderr == (
        "! Cancelling Lunar Gateway Resupply can't be undone. Its open assignments will be "
        "cancelled too.\n"
    )
    assert result.asked == [("Cancel Lunar Gateway Resupply? [y/N]", False)]
    assert api.sent("POST", "/missions/1/cancel")[0].body == {"reason": "Budget cut"}
    assert result.stdout == "✓ Cancelled Lunar Gateway Resupply.\n"


RUTH_ME = LEE_ME | {"id": 1, "email": "ruth@aurora.example", "name": "Ruth Adeyemi",
                    "role": "director"}  # fmt: skip
NORA_ME = LEE_ME | {"id": 5, "email": "nora@aurora.example", "name": "Nora Quinn"}
SURVEY = gateway() | {"id": 2, "name": "Asteroid Survey", "owner_id": 5, "owner_name": "Nora Quinn"}


def test_c4_a_director_cancelling_is_asked(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/me", ok(RUTH_ME))
    api.on("GET", "/missions/2", ok(SURVEY))
    api.on("POST", "/missions/2/cancel", ok(SURVEY | {"status": "cancelled"}))

    result = mc("missions", "cancel", "2", "--reason", "Budget cut", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert result.asked == [("Cancel Asteroid Survey? [y/N]", False)]


def test_c4_no_confirmation_for_a_cancel_the_server_will_refuse(mc, api):
    mc.login_as()  # Lee, who doesn't own Asteroid Survey and isn't a Director
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/missions/2", ok(SURVEY))
    api.on(
        "POST",
        "/missions/2/cancel",
        error(403, "not_owner", "Only the owner or a Director can cancel this mission"),
    )

    result = mc("missions", "cancel", "2", "--reason", "x", answers=[])

    assert result.exit_code == 1
    assert result.asked == []
    assert result.stderr == (
        "✗ Only the owner or a Director can cancel this mission.\n"
        "  See who owns it: mc missions show 2\n"
    )
    assert len(api.sent("POST", "/missions/2/cancel")) == 1


def test_c4_no_confirmation_for_an_edit_by_someone_other_than_the_owner(mc, api):
    mc.login_as("tok-nora", "nora@aurora.example")
    api.on("GET", "/me", ok(NORA_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
    api.on(
        "PATCH",
        "/missions/1",
        error(403, "not_owner", "Only the mission's owner can edit this mission"),
    )

    result = mc("missions", "edit", "1", "--name", "New")  # no terminal and no --yes

    assert result.exit_code == 1
    assert "pending approval" not in result.stderr
    assert result.stderr.startswith("✗ Only the mission's owner can edit this mission.\n")


def test_c4_a_director_editing_is_not_asked_either(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/me", ok(RUTH_ME))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
    api.on("PATCH", "/missions/1", error(403, "role_forbidden", "Directors can't edit missions"))

    result = mc("missions", "edit", "1", "--name", "New", answers=[])

    assert result.exit_code == 1
    assert result.asked == []
    assert result.stderr == "✗ Directors can't edit missions.\n"


def test_c4_transferring_a_pending_mission_asks_a_director(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/me", ok(RUTH_ME))
    api.on("GET", "/users", ok(USERS))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))

    result = mc("missions", "transfer", "1", "--owner", "nora@aurora.example", answers=["n"])

    assert result.exit_code == 1
    assert result.asked == [("Continue? [y/N]", False)]
    assert api.writes() == []


def test_c4_no_confirmation_for_a_transfer_by_a_lead(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))
    api.on("GET", "/users", ok(USERS))
    api.on("GET", "/missions/1", ok(gateway("pending_approval")))
    api.on(
        "POST",
        "/missions/1/owner",
        error(403, "role_forbidden", "Leads can't transfer mission ownership"),
    )

    result = mc("missions", "transfer", "1", "--owner", "nora@aurora.example", answers=[])

    assert result.exit_code == 1
    assert result.asked == []
    assert result.stderr == "✗ Leads can't transfer mission ownership.\n"


def test_ac6_cancel_needs_a_reason_flag(mc, api):
    mc.login_as()

    result = mc("missions", "cancel", "1", "--yes")

    assert result.exit_code == 2
    assert "--reason" in result.stderr
    assert api.calls == []


# Slots: by name or position


def test_m16_slot_edit_finds_the_slot_by_position(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("GET", "/skills", ok(SKILLS))
    api.on("PATCH", "/missions/1/slots/3", ok(gateway()))

    result = mc("missions", "slot", "edit", "1", "3", "--headcount", "2",
                "--requires", "Piloting>=5")  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("PATCH", "/missions/1/slots/3")[0].body == {
        "headcount": 2,
        "requirements": [{"skill_id": 1, "min_level": 5}],
    }
    assert result.stdout == "✓ Updated Commander on Lunar Gateway Resupply.\n"


def test_m16_slot_remove_finds_the_slot_by_name_ignoring_case(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("DELETE", "/missions/1/slots/2", ok(gateway()))

    result = mc("missions", "slot", "remove", "1", "mission specialist")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Removed Mission Specialist from Lunar Gateway Resupply.\n"


def test_m16_unknown_slot_lists_the_ones_that_exist(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))

    by_name = mc("missions", "slot", "remove", "1", "Pilot")
    by_position = mc("missions", "slot", "remove", "1", "7")

    expected_hint = "  Its slots: 1 Flight Engineer, 2 Mission Specialist, 3 Commander\n"
    assert by_name.exit_code == 1
    assert (
        by_name.stderr == "✗ Lunar Gateway Resupply has no slot called 'Pilot'.\n" + expected_hint
    )
    assert by_position.stderr == "✗ Lunar Gateway Resupply has no slot 7.\n" + expected_hint
    assert api.writes() == []


def test_m16_slot_add_uses_the_slot_spec(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("GET", "/skills", ok(SKILLS))
    api.on("POST", "/missions/1/slots", ok(gateway(), status=201))

    result = mc("missions", "slot", "add", "1", "--slot", "Geologist:1:Geology>=4")

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/missions/1/slots")[0].body == {
        "name": "Geologist",
        "headcount": 1,
        "requirements": [{"skill_id": 5, "min_level": 4}],
    }
    assert result.stdout == "✓ Added Geologist to Lunar Gateway Resupply.\n"


def test_m7_slot_change_that_would_invalidate_crew_lists_them(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    message = (
        "Can't remove Flight Engineer from Lunar Gateway Resupply while Chen Wu is assigned to it. "
        "Remove them from the mission first."
    )
    api.on(
        "DELETE",
        "/missions/1/slots/1",
        error(
            409,
            "rule_violation",
            message,
            [problem("slot_has_open_assignments", "Chen Wu is assigned to Flight Engineer",
                     assignment_id=21, crew_profile_id=8, slot_id=1)],
        ),
    )  # fmt: skip

    result = mc("missions", "slot", "remove", "1", "Flight Engineer")

    assert result.exit_code == 1
    assert result.stderr == (
        f"✗ {message}\n"
        "  • Chen Wu is assigned to Flight Engineer\n"
        "  Remove crew first: mc missions remove-crew 1 21\n"
    )


# Crew on a mission


def test_s1_propose_resolves_slot_by_name_and_crew_by_email(mc, api):
    mc.login_as()
    _skills_and_crew(api)
    api.on("GET", "/missions/1", ok(gateway()))
    api.on(
        "POST",
        "/missions/1/assignments",
        ok({"id": 21, "mission_id": 1, "slot_id": 1, "crew_profile_id": 8, "status": "proposed",
            "reason": None}, status=201),
    )  # fmt: skip

    result = mc("missions", "propose", "1", "--slot", "Flight Engineer",
                "--crew", "Chen@Aurora.example")  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/missions/1/assignments")[0].body == {
        "slot_id": 1,
        "crew_profile_id": 8,
    }
    assert result.stdout == (
        "✓ Proposed Chen Wu for Flight Engineer on Lunar Gateway Resupply (assignment 21). "
        "They need to accept.\n"
    )


def test_m16_propose_unknown_email_is_refused_before_writing(mc, api):
    mc.login_as()
    _skills_and_crew(api)
    api.on("GET", "/missions/1", ok(gateway()))

    result = mc("missions", "propose", "1", "--slot", "1", "--crew", "zed@aurora.example")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ There's no crew member with the email zed@aurora.example.\n"
        "  See the crew: mc crew list\n"
    )
    assert api.writes() == []


def test_m16_remove_crew_checks_the_assignment_is_on_that_mission(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))

    result = mc("missions", "remove-crew", "1", "99")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ Assignment 99 isn't on Lunar Gateway Resupply.\n  See its crew: mc missions show 1\n"
    )
    assert api.writes() == []


def test_ac4_remove_crew_from_a_pending_mission_confirms(mc, api):
    mc.login_as()
    row = {"id": 21, "slot_id": 1, "slot_name": "Flight Engineer", "crew_profile_id": 8,
           "crew_name": "Chen Wu", "status": "accepted", "reason": None}  # fmt: skip
    api.on("GET", "/missions/1", ok(gateway("pending_approval", [row])))
    api.on("POST", "/assignments/21/remove", ok({"id": 21, "mission_id": 1, "slot_id": 1,
           "crew_profile_id": 8, "status": "removed", "reason": None}))  # fmt: skip

    result = mc("missions", "remove-crew", "1", "21", "--yes")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == (
        "✓ Removed Chen Wu from Flight Engineer on Lunar Gateway Resupply. It's back in Draft.\n"
    )


# Lifecycle


def test_s1_submit_reports_the_approvals_needed(mc, api):
    mc.login_as()
    api.on("POST", "/missions/1/submit", ok(gateway("pending_approval")))

    result = mc("missions", "submit", "1")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == (
        "✓ Submitted Lunar Gateway Resupply for approval. It needs 2 approvals.\n"
    )


def test_ac3_approval_before_the_last_leaves_it_pending(mc, api):
    mc.login_as("tok-marco", "marco@aurora.example")
    approvals = [{"director_id": 2, "director_name": "Marco Bianchi", "decision": "approve",
                  "reason": None}]  # fmt: skip
    api.on("POST", "/missions/1/approve", ok(gateway("pending_approval", approvals=approvals)))

    result = mc("missions", "approve", "1")

    assert result.exit_code == 0
    assert result.stdout == (
        "✓ Approved Lunar Gateway Resupply. It's pending approval (1 of 2 approvals).\n"
    )


def test_ac3_final_approval_makes_it_active(mc, api):
    mc.login_as("tok-ingrid", "ingrid@aurora.example")
    api.on("POST", "/missions/1/approve", ok(gateway("active")))

    result = mc("missions", "approve", "1")

    assert result.stdout == "✓ Approved Lunar Gateway Resupply. It's now active.\n"


def test_ac8_creator_cannot_approve(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on(
        "POST",
        "/missions/1/approve",
        error(403, "approver_is_creator", "You can't approve a mission you created"),
    )

    result = mc("missions", "approve", "1")

    assert result.exit_code == 1
    assert result.stderr == "✗ You can't approve a mission you created.\n"


def test_ac10_reject_sends_the_reason(mc, api):
    mc.login_as("tok-ingrid", "ingrid@aurora.example")
    api.on(
        "POST", "/missions/6/reject", ok(gateway() | {"id": 6, "name": "Deep Space Comms Upgrade"})
    )

    result = mc("missions", "reject", "6", "--reason", "Roster too thin")

    assert result.exit_code == 0
    assert api.sent("POST", "/missions/6/reject")[0].body == {"reason": "Roster too thin"}
    assert result.stdout == "✓ Rejected Deep Space Comms Upgrade. It's back in Draft.\n"


def test_ac7_transfer_resolves_the_new_owner_by_email(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("POST", "/missions/1/owner", ok(gateway() | {"owner_id": 5, "owner_name": "Nora Quinn"}))

    result = mc("missions", "transfer", "1", "--owner", "nora@aurora.example")

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/missions/1/owner")[0].body == {"owner_id": 5}
    assert result.stdout == "✓ Lunar Gateway Resupply now belongs to Nora Quinn.\n"


def test_s1_complete(mc, api):
    mc.login_as()
    api.on("POST", "/missions/1/complete", ok(gateway("completed")))

    result = mc("missions", "complete", "1")

    assert result.exit_code == 0
    assert result.stdout == (
        "✓ Completed Lunar Gateway Resupply. Its accepted assignments are completed too.\n"
    )


def test_m16_action_json_prints_the_api_body(mc, api):
    mc.login_as()
    api.on("POST", "/missions/1/submit", ok(gateway("pending_approval")))

    result = mc("missions", "submit", "1", "--json")

    assert json.loads(result.stdout)["status"] == "pending_approval"
