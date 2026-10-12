"""M16: how refusals and failures reach the user. The message, one bullet per problem, a hint
for known codes, and the documented exit codes: 0 OK, 1 refused, 2 usage, 3 authentication,
4 unreachable or busy, 130 interrupted (design §7, §8; PRD C2)."""

import json

import httpx2
from cli_fakes import S2_PREVIEW, error, gateway, ok, problem


def test_c2_every_problem_is_listed_once_under_the_message(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1", ok(gateway()))
    api.on(
        "POST",
        "/missions/1/submit",
        error(
            409,
            "rule_violation",
            "Mission can't be submitted",
            [
                problem("slot_unfilled", "Flight Engineer: 1 place unfilled", slot_id=1),
                problem("slot_unfilled", "Commander: 1 place unfilled", slot_id=3),
                problem("insufficient_approvers", "1 eligible approver, 2 required"),
            ],
        ),
    )

    result = mc("missions", "submit", "1")

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == (
        "✗ Mission can't be submitted.\n"
        "  • Flight Engineer: 1 place unfilled\n"
        "  • Commander: 1 place unfilled\n"
        "  • 1 eligible approver, 2 required\n"
        "  Fill the open places: mc missions match 1\n"
    )


def test_m16_a_single_reason_refusal_prints_its_message_once(mc, api):
    mc.login_as()
    api.on("GET", "/missions/9", error(404, "not_found", "Mission not found"))

    result = mc("missions", "show", "9")

    assert result.exit_code == 1
    assert result.stderr == "✗ Mission 9 not found.\n  See your missions: mc missions list\n"


def test_m16_refusal_with_json_prints_the_error_body_on_stdout(mc, api):
    mc.login_as()
    body = error(409, "mission_frozen", "Can't suggest crew for an active mission")
    api.on("GET", "/missions/5/match", body)

    result = mc("missions", "match", "5", "--json")

    assert result.exit_code == 1
    assert json.loads(result.stdout) == {
        "error": {
            "code": "mission_frozen",
            "message": "Can't suggest crew for an active mission",
            "problems": [
                {
                    "code": "mission_frozen",
                    "message": "Can't suggest crew for an active mission",
                    "refs": {},
                }
            ],
        }
    }
    assert result.stderr == ""


def test_m16_usage_errors_exit_2_before_any_request(mc, api):
    mc.login_as()

    result = mc("missions", "match", "abc")

    assert result.exit_code == 2
    assert "Invalid value for 'MISSION_ID': 'abc' is not a valid int" in result.stderr
    assert api.calls == []


def test_m16_unknown_command_suggests_the_closest(mc):
    result = mc("missions", "mach", "1")

    assert result.exit_code == 2
    assert "Did you mean 'match'?" in result.stderr


def test_m16_unreachable_server_exits_4_and_says_how_to_start_it(mc):
    mc.login_as()

    def refuse(request):
        raise httpx2.ConnectError("connection refused", request=request)

    result = mc("whoami", http=httpx2.Client(transport=httpx2.MockTransport(refuse)))

    assert result.exit_code == 4
    assert "✗ Can't reach the Mission Control server at " in result.stderr
    assert "Is it running? Start it with: uv run mc-server" in result.stderr
    assert mc.store.path.exists()


def test_m16_busy_database_exits_4_with_a_retry_hint(mc, api):
    mc.login_as()
    api.on("GET", "/me", error(503, "busy", "The database is busy"))

    result = mc("whoami")

    assert result.exit_code == 4
    assert result.stderr == "✗ The database is busy.\n  Try again in a moment.\n"


def test_m16_an_unexpected_server_response_is_reported_without_a_traceback(mc, api):
    mc.login_as()
    api.on("GET", "/me", httpx2.Response(500, text="Internal Server Error"))

    result = mc("whoami")

    assert result.exit_code == 1
    assert result.stderr == (
        "✗ The server sent an unexpected response (HTTP 500).\n"
        "  Try again. If it keeps happening, check the server's log.\n"
    )
    assert "Traceback" not in result.stderr


def test_m16_ctrl_c_exits_130_quietly(mc):
    mc.login_as()

    def interrupt(request):
        raise KeyboardInterrupt

    result = mc("whoami", http=httpx2.Client(transport=httpx2.MockTransport(interrupt)))

    assert result.exit_code == 130
    assert result.stderr.strip() == "Cancelled."


def test_m16_ctrl_c_at_a_prompt_exits_130(mc):
    result = mc("login", answers=[])  # Ctrl+C at the first prompt

    assert result.exit_code == 130
    assert "Cancelled." in result.stderr


def test_m16_bare_mc_shows_help_and_exits_0(mc):
    result = mc()

    assert result.exit_code == 0
    assert "Usage: mc" in result.stdout
    for group in ("missions", "assignments", "crew", "users", "skills", "org", "me"):
        assert group in result.stdout


def test_m16_bare_group_shows_its_help_and_exits_0(mc):
    result = mc("missions")

    assert result.exit_code == 0
    assert "match" in result.stdout and "submit" in result.stdout


def test_m16_version_flag(mc):
    result = mc("--version")

    assert result.exit_code == 0
    assert result.stdout.startswith("mc ")


def test_m16_command_help_shows_usage_and_an_example(mc):
    result = mc("missions", "match", "--help")

    assert result.exit_code == 0
    assert result.stdout.startswith("Usage: mc missions match MISSION_ID [--apply] [--json]\n")
    assert "Suggest crew for a draft mission's open places. Nothing is changed." in result.stdout
    assert "Example:\n  mc missions match 1\n" in result.stdout


def test_m16_colour_escapes_appear_only_when_enabled(mc, api):
    mc.login_as()
    api.on("GET", "/missions/1/match", ok(S2_PREVIEW))

    plain = mc("missions", "match", "1")
    coloured = mc("missions", "match", "1", color=True)

    assert "\x1b[" not in plain.stdout + plain.stderr
    assert "\x1b[32m✓\x1b[0m" in coloured.stdout


def test_m16_no_color_env_gives_plain_words(mc, api, monkeypatch):
    mc.login_as()
    monkeypatch.setenv("NO_COLOR", "1")
    api.on(
        "GET",
        "/missions/5/match",
        error(409, "mission_frozen", "Can't suggest crew for an active mission"),
    )

    result = mc("missions", "match", "5", color=None)

    assert result.stderr.startswith("Error: Mission 5: Can't suggest crew for an active mission.\n")
