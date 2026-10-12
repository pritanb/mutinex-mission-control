"""M16: everyone's own commands (inbox, assignments, profile and availability) and the crew,
users, skills and organisation commands (design §8; PRD §4, P1–P10, S2–S3, V2)."""

from cli_fakes import CREW, LEE_ME, SKILLS, USERS, error, ok, problem

GATEWAY_PROPOSAL = {
    "assignment_id": 21,
    "mission_id": 1,
    "mission_name": "Lunar Gateway Resupply",
    "start_date": "2027-03-01",
    "end_date": "2027-03-10",
    "mission_status": "draft",
    "slot_name": "Flight Engineer",
    "status": "proposed",
    "reason": None,
}
COMMS_ACCEPTED = {
    "assignment_id": 31,
    "mission_id": 6,
    "mission_name": "Deep Space Comms Upgrade",
    "start_date": "2027-04-01",
    "end_date": "2027-04-20",
    "mission_status": "pending_approval",
    "slot_name": "Engineer",
    "status": "accepted",
    "reason": None,
}
BEN_ME = LEE_ME | {"id": 7, "email": "ben@aurora.example", "name": "Ben Ito", "role": "crew",
                   "crew_profile_id": 7}  # fmt: skip


def _assignment(aid, status, reason=None):
    return ok({"id": aid, "mission_id": 1, "slot_id": 1, "crew_profile_id": 8, "status": status,
               "reason": reason})  # fmt: skip


# Inbox and assignments


def test_m16_inbox_groups_what_is_waiting(mc, api):
    mc.login_as("tok-chen", "chen@aurora.example")
    api.on(
        "GET",
        "/me/inbox",
        ok({"proposals": [GATEWAY_PROPOSAL], "approvals": [], "missions": []}),
    )

    result = mc("inbox")

    assert result.exit_code == 0
    assert result.stdout == (
        "Proposals waiting for your answer\n"
        "  Assignment   Mission                  Slot              Dates\n"
        "  21           Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027\n"
    )
    assert "Next: mc assignments accept 21" in result.stderr


def test_m16_empty_inbox(mc, api):
    mc.login_as()
    api.on("GET", "/me/inbox", ok({"proposals": [], "approvals": [], "missions": []}))

    result = mc("inbox")

    assert result.stdout == "✓ Nothing needs your attention.\n"


def _draft(mission_id, name, start, end, unfilled=(), unanswered=0, eligible=3, ready=False):
    return {
        "mission_id": mission_id,
        "mission_name": name,
        "start_date": start,
        "end_date": end,
        "unfilled": [
            {"slot_id": i, "slot_name": slot, "open_places": places}
            for i, (slot, places) in enumerate(unfilled, start=1)
        ],
        "unanswered": unanswered,
        "eligible_approvers": eligible,
        "approvals_required": 2,
        "ready": ready,
    }


def test_inbox_shows_approvals_and_what_each_draft_mission_is_waiting_on(mc, api):
    mc.login_as()
    approval = {
        "mission_id": 6,
        "mission_name": "Deep Space Comms Upgrade",
        "start_date": "2027-04-01",
        "end_date": "2027-04-20",
        "approvals": 1,
        "required": 2,
    }
    gateway = _draft(
        1,
        "Lunar Gateway Resupply",
        "2027-03-01",
        "2027-03-10",
        unfilled=[("Flight Engineer", 1), ("Mission Specialist", 1), ("Commander", 1)],
    )
    asteroid = _draft(
        2, "Asteroid Survey", "2027-03-05", "2027-03-12", [("Geologist", 1)], unanswered=2
    )
    medical = _draft(4, "Lunar Surface Medical Study", "2027-03-15", "2027-03-18", eligible=1)
    reboost = _draft(3, "Station Reboost", "2027-03-20", "2027-03-25", ready=True)
    api.on(
        "GET",
        "/me/inbox",
        ok(
            {
                "proposals": [],
                "approvals": [approval],
                "missions": [gateway, asteroid, medical, reboost],
            }
        ),
    )

    result = mc("inbox")

    assert result.exit_code == 0
    assert result.stdout == (
        "Missions waiting for your approval\n"
        "  ID   Mission                    Dates           Approvals\n"
        "  6    Deep Space Comms Upgrade   1–20 Apr 2027   1 of 2\n"
        "\n"
        "Your draft missions\n"
        "  ID   Mission                       Dates            Waiting on\n"
        "  1    Lunar Gateway Resupply        1–10 Mar 2027    3 places unfilled\n"
        "  2    Asteroid Survey               5–12 Mar 2027    "
        "1 place unfilled; 2 replies awaited\n"
        "  4    Lunar Surface Medical Study   15–18 Mar 2027   "
        "1 eligible approver, 2 required\n"
        "  3    Station Reboost               20–25 Mar 2027   Ready to submit\n"
    )
    assert "mc missions approve 6" in result.stderr
    assert "mc missions submit 3" in result.stderr
    assert "mc missions submit 4" not in result.stderr


def test_inbox_never_suggests_submitting_a_mission_short_of_approvers(mc, api):
    mc.login_as()
    medical = _draft(4, "Lunar Surface Medical Study", "2027-03-15", "2027-03-18", eligible=1)
    api.on("GET", "/me/inbox", ok({"proposals": [], "approvals": [], "missions": [medical]}))

    result = mc("inbox")

    assert result.exit_code == 0
    assert "1 eligible approver, 2 required" in result.stdout
    assert "mc missions submit" not in result.stderr


def test_inbox_lists_every_reason_a_draft_mission_is_waiting(mc, api):
    mc.login_as()
    short = _draft(
        2,
        "Asteroid Survey",
        "2027-03-05",
        "2027-03-12",
        [("Pilot", 1), ("Geologist", 2)],
        unanswered=1,
        eligible=0,
    )
    api.on("GET", "/me/inbox", ok({"proposals": [], "approvals": [], "missions": [short]}))

    result = mc("inbox")

    assert "3 places unfilled; 1 reply awaited; 0 eligible approvers, 2 required" in result.stdout
    assert "Next: mc missions match 2" in result.stderr


def test_s2_assignments_list_pending_only(mc, api):
    mc.login_as("tok-chen", "chen@aurora.example")
    api.on("GET", "/assignments", ok([GATEWAY_PROPOSAL]))

    result = mc("assignments", "list", "--pending")

    assert result.exit_code == 0
    assert api.calls[-1].params == {"pending": "true"}
    assert result.stdout == (
        "  ID   Mission                  Slot              Dates           Status\n"
        "  21   Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027   Proposed\n"
    )


def test_s2_accept_names_the_slot_and_mission(mc, api):
    mc.login_as("tok-chen", "chen@aurora.example")
    api.on("GET", "/assignments", ok([GATEWAY_PROPOSAL]))
    api.on("POST", "/assignments/21/accept", _assignment(21, "accepted"))

    result = mc("assignments", "accept", "21")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Accepted Flight Engineer on Lunar Gateway Resupply.\n"


def test_s3_decline_with_an_optional_reason(mc, api):
    mc.login_as("tok-chen", "chen@aurora.example")
    api.on("GET", "/assignments", ok([GATEWAY_PROPOSAL]))
    api.on("POST", "/assignments/21/decline", _assignment(21, "declined"))

    plain = mc("assignments", "decline", "21")
    reasoned = mc("assignments", "decline", "21", "--reason", "On leave")

    assert plain.exit_code == reasoned.exit_code == 0
    assert api.sent("POST", "/assignments/21/decline")[0].body is None
    assert api.sent("POST", "/assignments/21/decline")[1].body == {"reason": "On leave"}
    assert plain.stdout == "✓ Declined Flight Engineer on Lunar Gateway Resupply.\n"


def test_s5_withdraw_from_a_pending_mission_warns_then_sends_the_reason(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/assignments", ok([COMMS_ACCEPTED]))
    api.on("POST", "/assignments/31/withdraw", _assignment(31, "withdrawn", "Family matter"))

    result = mc("assignments", "withdraw", "31", "--reason", "Family matter", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert (
        "! Deep Space Comms Upgrade is pending approval. Withdrawing sends it back to Draft and "
        "clears its approvals." in result.stderr
    )
    assert api.sent("POST", "/assignments/31/withdraw")[0].body == {"reason": "Family matter"}
    assert result.stdout == (
        "✓ Withdrew from Engineer on Deep Space Comms Upgrade. It's back in Draft.\n"
    )


def test_s5_withdraw_from_an_active_mission_is_refused_by_the_server(mc, api):
    mc.login_as("tok-hana", "hana@aurora.example")
    telescope = COMMS_ACCEPTED | {"assignment_id": 41, "mission_id": 5,
                                  "mission_name": "Orbital Telescope Service",
                                  "mission_status": "active"}  # fmt: skip
    api.on("GET", "/assignments", ok([telescope]))
    api.on(
        "POST",
        "/assignments/41/withdraw",
        error(409, "mission_frozen", "Can't withdraw from an active mission"),
    )

    result = mc("assignments", "withdraw", "41", "--reason", "Sick")

    assert result.exit_code == 1
    assert result.stderr.startswith("✗ Can't withdraw from an active mission.\n")


def test_m16_someone_elses_assignment_looks_unknown(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/assignments", ok([]))
    api.on("POST", "/assignments/21/accept", error(404, "not_found", "Assignment not found"))

    result = mc("assignments", "accept", "21")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ Assignment 21 not found.\n  See your assignments: mc assignments list\n"
    )


# My profile and availability


def test_p4_me_show_includes_profile_skills_and_unavailability(mc, api):
    mc.login_as("tok-fay", "fay@aurora.example")
    fay = next(c for c in CREW if c["crew_profile_id"] == 11)
    fay = fay | {"unavailability": [{"id": 1, "start_date": "2027-03-05",
                                     "end_date": "2027-03-08", "reason": "Medical"}]}  # fmt: skip
    api.on("GET", "/me", ok(BEN_ME | {"name": "Fay Moreau", "email": "fay@aurora.example",
                                      "crew_profile_id": 11}))  # fmt: skip
    api.on("GET", "/crew/11", ok(fay))

    result = mc("me", "show")

    assert result.exit_code == 0
    assert result.stdout == (
        "Name           Fay Moreau\n"
        "Email          fay@aurora.example\n"
        "Role           Crew Member\n"
        "Organisation   Aurora Space Agency\n"
        "Bio            none\n"
        "\n"
        "  Skill        Level\n"
        "  Piloting     4\n"
        "  Leadership   4\n"
        "\n"
        "  ID   Unavailable    Reason\n"
        "  1    5–8 Mar 2027   Medical\n"
    )


def test_p4_me_update_sends_only_what_changed(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/me", ok(BEN_ME))
    api.on("PATCH", "/crew/7", ok({"crew_profile_id": 7, "user_id": 7, "name": "Ben Ito",
                                   "bio": "EVA and systems"}))  # fmt: skip

    result = mc("me", "update", "--bio", "EVA and systems")

    assert result.exit_code == 0, result.stderr
    assert api.sent("PATCH", "/crew/7")[0].body == {"bio": "EVA and systems"}
    assert result.stdout == "✓ Updated your profile.\n"


def test_m16_me_without_a_crew_profile_explains(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("me", "unavailable", "list")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ You don't have a crew profile.\n"
        "  A Director can give you one: mc users enable-crew EMAIL\n"
    )


def test_p5_add_unavailability(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/me", ok(BEN_ME))
    api.on(
        "POST",
        "/crew/7/unavailability",
        ok({"id": 4, "start_date": "2027-06-01", "end_date": "2027-06-03", "reason": "Leave"},
           status=201),
    )  # fmt: skip

    result = mc("me", "unavailable", "add", "--start", "2027-06-01", "--end", "2027-06-03",
                "--reason", "Leave")  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/crew/7/unavailability")[0].body == {
        "start_date": "2027-06-01",
        "end_date": "2027-06-03",
        "reason": "Leave",
    }
    assert result.stdout == "✓ Added unavailability 4: 1–3 Jun 2027 (Leave).\n"


def test_ac16_unavailability_overlapping_an_accepted_assignment_is_refused(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/me", ok(BEN_ME))
    message = "You have an accepted assignment on Deep Space Comms Upgrade overlapping 1–3 Apr"
    api.on(
        "POST",
        "/crew/7/unavailability",
        error(409, "rule_violation", message, [problem("overlap", message, crew_profile_id=7,
              mission_id=6, mission_name="Deep Space Comms Upgrade")]),
    )  # fmt: skip

    result = mc("me", "unavailable", "add", "--start", "2027-04-01", "--end", "2027-04-03",
                "--reason", "Leave")  # fmt: skip

    assert result.exit_code == 1
    assert result.stderr.startswith(f"✗ {message}.\n")


def test_p5_remove_unavailability(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/me", ok(BEN_ME))
    api.on("DELETE", "/crew/7/unavailability/4", ok(status=204))

    result = mc("me", "unavailable", "remove", "4")

    assert result.exit_code == 0
    assert result.stdout == "✓ Removed unavailability 4.\n"


# Crew


def test_ac24_lead_sees_busy_dates_without_reasons(mc, api):
    mc.login_as()
    api.on("GET", "/crew", ok(CREW))
    fay = next(c for c in CREW if c["crew_profile_id"] == 11)
    api.on("GET", "/crew/11", ok(fay))

    result = mc("crew", "show", "fay@aurora.example")

    assert result.exit_code == 0
    assert result.stdout == (
        "Name    Fay Moreau\n"
        "Email   fay@aurora.example\n"
        "Bio     none\n"
        "\n"
        "  Skill        Level\n"
        "  Piloting     4\n"
        "  Leadership   4\n"
        "\n"
        "  Unavailable\n"
        "  5–8 Mar 2027\n"
    )


def test_m16_crew_list(mc, api):
    mc.login_as()
    api.on("GET", "/crew", ok(CREW[:2]))

    result = mc("crew", "list")

    assert result.stdout == (
        "  Name         Email                Skills\n"
        "  Ana Okafor   ana@aurora.example   Piloting 5, Leadership 4\n"
        "  Ben Ito      ben@aurora.example   Systems Engineering 4, EVA 3\n"
    )


def test_ac23_set_skill_by_email_and_skill_name(mc, api):
    mc.login_as()
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/skills", ok(SKILLS))
    api.on("PUT", "/crew/6/skills/1", ok({"skill_id": 1, "skill_name": "Piloting", "level": 4}))

    result = mc("crew", "set-skill", "ana@aurora.example", "piloting", "4")

    assert result.exit_code == 0, result.stderr
    assert api.sent("PUT", "/crew/6/skills/1")[0].body == {"level": 4}
    assert result.stdout == "✓ Set Ana Okafor's Piloting to 4.\n"


def test_ac23_own_skills_are_refused_by_the_server(mc, api):
    mc.login_as("tok-ana", "ana@aurora.example")
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/skills", ok(SKILLS))
    api.on(
        "PUT",
        "/crew/6/skills/1",
        error(403, "self_skill_edit", "You can't change your own skill levels"),
    )

    result = mc("crew", "set-skill", "ana@aurora.example", "Piloting", "5")

    assert result.exit_code == 1
    assert result.stderr == "✗ You can't change your own skill levels.\n"


BEN_ONLY = [c for c in CREW if c["crew_profile_id"] == 7]  # Crew see only their own profile
SKILLS_FORBIDDEN = error(403, "role_forbidden", "Crew can't view the skill catalogue")


def test_ac23_crew_are_told_who_can_set_skill_levels(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/crew", ok(BEN_ONLY))
    api.on("GET", "/skills", SKILLS_FORBIDDEN)

    own = mc("crew", "set-skill", "ben@aurora.example", "Piloting", "5")
    other = mc("crew", "set-skill", "ana@aurora.example", "Piloting", "5")

    for result in (own, other):
        assert result.exit_code == 1
        assert result.stderr == "✗ Only Mission Leads and Directors can change skill levels.\n"
    assert api.writes() == []


def test_ac23_crew_are_told_who_can_remove_skill_levels(mc, api):
    mc.login_as("tok-ben", "ben@aurora.example")
    api.on("GET", "/crew", ok(BEN_ONLY))
    api.on("GET", "/skills", SKILLS_FORBIDDEN)

    result = mc("crew", "unset-skill", "ben@aurora.example", "EVA")

    assert result.exit_code == 1
    assert result.stderr == "✗ Only Mission Leads and Directors can change skill levels.\n"
    assert api.writes() == []


def test_p3_unset_skill(mc, api):
    mc.login_as()
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/skills", ok(SKILLS))
    api.on("DELETE", "/crew/6/skills/2", ok(status=204))

    result = mc("crew", "unset-skill", "ana@aurora.example", "Leadership")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Removed Leadership from Ana Okafor's skills.\n"


def test_m16_crew_history(mc, api):
    mc.login_as()
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/crew/8/assignments", ok([GATEWAY_PROPOSAL | {"status": "declined"}]))

    result = mc("crew", "history", "chen@aurora.example")

    assert result.exit_code == 0
    assert result.stdout == (
        "  Assignment   Mission                  Slot              Dates           Status\n"
        "  21           Lunar Gateway Resupply   Flight Engineer   1–10 Mar 2027   Declined\n"
    )


# Users, skills and the organisation (Directors)


def test_p10_add_user_asks_for_the_initial_password_twice(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    created = {"id": 20, "email": "zoe@aurora.example", "name": "Zoe Lin", "role": "crew",
               "active": True}  # fmt: skip
    api.on("POST", "/users", ok(created, status=201))

    result = mc(
        "users", "add", "--email", "zoe@aurora.example", "--name", "Zoe Lin", "--role", "crew",
        answers=["a long first passphrase", "a long first passphrase"],
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert result.asked == [("Initial password", True), ("Repeat initial password", True)]
    assert api.sent("POST", "/users")[0].body == {
        "email": "zoe@aurora.example",
        "name": "Zoe Lin",
        "role": "crew",
        "password": "a long first passphrase",
    }
    assert result.stdout == "✓ Added Zoe Lin (zoe@aurora.example) as a Crew Member.\n"
    assert result.stderr == "Next: mc login --email zoe@aurora.example    (for Zoe)\n"


def test_p10_add_user_without_a_terminal_reads_the_password_once(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    created = {"id": 20, "email": "zoe@aurora.example", "name": "Zoe Lin", "role": "crew",
               "active": True}  # fmt: skip
    api.on("POST", "/users", ok(created, status=201))

    result = mc(
        "users", "add", "--email", "zoe@aurora.example", "--name", "Zoe Lin", "--role", "crew",
        input="a long first passphrase\n",
    )  # fmt: skip

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/users")[0].body["password"] == "a long first passphrase"


def test_m16_role_must_be_one_of_the_three(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")

    result = mc("users", "set-role", "lee@aurora.example", "captain")

    assert result.exit_code == 2
    assert "director" in result.stderr and "lead" in result.stderr
    assert api.calls == []


def test_ac26_last_director_cannot_be_demoted(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))
    api.on(
        "PATCH",
        "/users/1",
        error(409, "rule_violation", "Ruth Adeyemi is the last active Director",
              [problem("last_director", "Ruth Adeyemi is the last active Director", user_id=1)]),
    )  # fmt: skip

    result = mc("users", "set-role", "ruth@aurora.example", "lead")

    assert result.exit_code == 1
    assert api.sent("PATCH", "/users/1")[0].body == {"role": "lead"}
    assert result.stderr.startswith("✗ Ruth Adeyemi is the last active Director.\n")


DEACTIVATE_WARNING = "! Deactivating Chen Wu can't be undone: they won't be able to log in.\n"


def test_p7_deactivate_user_asks_first(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))
    api.on("PATCH", "/users/8", ok(USERS[3] | {"active": False}))

    result = mc("users", "deactivate", "chen@aurora.example", answers=["y"])

    assert result.exit_code == 0, result.stderr
    assert result.stderr == DEACTIVATE_WARNING
    assert result.asked == [("Deactivate Chen Wu? [y/N]", False)]
    assert api.sent("PATCH", "/users/8")[0].body == {"active": False}
    assert result.stdout == "✓ Deactivated Chen Wu. They can no longer log in.\n"


def test_p7_declining_to_deactivate_changes_nothing(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))

    result = mc("users", "deactivate", "chen@aurora.example", answers=["n"])

    assert result.exit_code == 1
    assert "Nothing was changed." in result.stderr
    assert api.writes() == []


def test_p7_deactivate_without_a_terminal_needs_yes(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))

    result = mc("users", "deactivate", "chen@aurora.example")

    assert result.exit_code == 2
    assert result.stderr.startswith(DEACTIVATE_WARNING)
    assert "Re-run with --yes" in result.stderr
    assert api.writes() == []


def test_p7_deactivate_with_yes_does_not_ask(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))
    api.on("PATCH", "/users/8", ok(USERS[3] | {"active": False}))

    result = mc("users", "deactivate", "chen@aurora.example", "-y", answers=[])

    assert result.exit_code == 0, result.stderr
    assert result.asked == []
    assert result.stdout == "✓ Deactivated Chen Wu. They can no longer log in.\n"


def test_p9_enable_crew(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS))
    api.on(
        "POST",
        "/users/4/crew-profile",
        ok({"crew_profile_id": 4, "user_id": 4, "name": "Lee Park", "bio": None}, status=201),
    )

    result = mc("users", "enable-crew", "lee@aurora.example")

    assert result.exit_code == 0, result.stderr
    assert result.stdout == "✓ Lee Park now has a crew profile.\n"


def test_m16_users_list(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/users", ok(USERS[:2] + [USERS[3] | {"active": False}]))

    result = mc("users", "list")

    assert result.stdout == (
        "  ID   Name           Email                 Role           Status\n"
        "  1    Ruth Adeyemi   ruth@aurora.example   Director       active\n"
        "  4    Lee Park       lee@aurora.example    Mission Lead   active\n"
        "  8    Chen Wu        chen@aurora.example   Crew Member    deactivated\n"
    )


def test_ac25_lead_cannot_manage_users(mc, api):
    mc.login_as()
    api.on("GET", "/users", error(403, "role_forbidden", "Leads can't manage users"))

    result = mc("users", "deactivate", "chen@aurora.example")

    assert result.exit_code == 1
    assert result.stderr == "✗ Leads can't manage users.\n"


def test_p1_skills_add_rename_remove(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/skills", ok(SKILLS))
    api.on("POST", "/skills", ok({"id": 11, "name": "Robotics", "category": None}, status=201))
    api.on("PATCH", "/skills/5", ok({"id": 5, "name": "Planetary Geology", "category": None}))
    api.on("DELETE", "/skills/4", ok(status=204))

    added = mc("skills", "add", "Robotics")
    renamed = mc("skills", "rename", "geology", "Planetary Geology")
    removed = mc("skills", "remove", "EVA")

    assert added.stdout == "✓ Added skill Robotics.\n"
    assert api.sent("POST", "/skills")[0].body == {"name": "Robotics"}
    assert renamed.stdout == "✓ Renamed Geology to Planetary Geology.\n"
    assert api.sent("PATCH", "/skills/5")[0].body == {"name": "Planetary Geology"}
    assert removed.stdout == "✓ Removed skill EVA.\n"


def test_p1_used_skill_cannot_be_removed(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    api.on("GET", "/skills", ok(SKILLS))
    api.on(
        "DELETE",
        "/skills/4",
        error(409, "rule_violation", "EVA is still in use",
              [problem("skill_in_use", "EVA is still in use", skill_id=4)]),
    )  # fmt: skip

    result = mc("skills", "remove", "EVA")

    assert result.exit_code == 1
    assert result.stderr.startswith("✗ EVA is still in use.\n")


def test_m16_skills_list(mc, api):
    mc.login_as()
    api.on("GET", "/skills", ok(SKILLS[:2]))

    result = mc("skills", "list")

    assert result.stdout == "Piloting\nLeadership\n"


def test_a1_org_show_and_set_approvals(mc, api):
    mc.login_as("tok-ruth", "ruth@aurora.example")
    org = {"id": 1, "name": "Aurora Space Agency", "slug": "aurora", "required_approvals": 2}
    api.on("GET", "/org", ok(org))
    api.on("PATCH", "/org", ok(org | {"required_approvals": 3}))

    shown = mc("org", "show")
    changed = mc("org", "set-approvals", "3")

    assert shown.stdout == "Organisation         Aurora Space Agency\nApprovals required   2\n"
    assert api.sent("PATCH", "/org")[0].body == {"required_approvals": 3}
    assert changed.stdout == (
        "✓ Missions now need 3 approvals. Missions already pending keep the number they were "
        "submitted with.\n"
    )
