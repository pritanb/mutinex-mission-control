"""M16: signing in and out, who am I, and changing a password (PRD §4.1, P10; design §8).

Passwords are only ever asked for with a hidden prompt, never taken as a flag. When stdin isn't a
terminal they're read from it, one line per password, so scripts can pipe them in. A new password
is asked twice only on a terminal; a piped one is read once.
"""

import stat
from datetime import UTC, datetime, timedelta

import httpx2
from cli_fakes import LEE_ME, error, ok, session


def _login_ok(request):
    expires = datetime.now(UTC) + timedelta(hours=12)
    return ok(session("tok-new", LEE_ME, expires.isoformat().replace("+00:00", "Z")))


def test_m16_login_prompts_for_email_and_hidden_password_then_stores_the_token(mc, api):
    api.on("POST", "/auth/login", _login_ok)
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("login", answers=["lee@aurora.example", "orbital launch window"])

    assert result.exit_code == 0, result.stderr
    assert result.asked == [("Email", False), ("Password", True)]  # the password is hidden
    assert "orbital launch window" not in result.stdout + result.stderr
    assert api.sent("POST", "/auth/login")[0].body == {
        "email": "lee@aurora.example",
        "password": "orbital launch window",
    }
    assert result.stdout == (
        "✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts 12 hours.\n"
    )
    assert "Next: mc inbox" in result.stderr
    saved = mc.store.load()
    assert saved.token == "tok-new" and saved.email == "lee@aurora.example"
    assert stat.S_IMODE(mc.store.path.stat().st_mode) == 0o600
    assert api.sent("GET", "/me")[0].token == "tok-new"


def test_m16_login_with_email_flag_asks_only_for_the_password(mc, api):
    api.on("POST", "/auth/login", _login_ok)
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("login", "--email", "lee@aurora.example", answers=["pw"])

    assert result.exit_code == 0
    assert result.asked == [("Password", True)]


def test_m16_login_reads_the_password_from_a_pipe_when_not_on_a_terminal(mc, api):
    api.on("POST", "/auth/login", _login_ok)
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("login", "--email", "lee@aurora.example", input="orbital launch window\n")

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/auth/login")[0].body["password"] == "orbital launch window"
    assert "Password" not in result.stderr


def test_m16_login_without_a_terminal_or_email_fails_clearly_instead_of_hanging(mc, api):
    result = mc("login", input="")

    assert result.exit_code == 2
    assert "Pass --email" in result.stderr
    assert api.calls == []


def test_m16_login_without_a_terminal_or_piped_password_fails_clearly(mc, api):
    result = mc("login", "--email", "lee@aurora.example", input="")

    assert result.exit_code == 2
    assert "pipe it on stdin" in result.stderr
    assert api.calls == []


def test_m16_login_again_ends_the_previous_session_on_the_server(mc, api):
    mc.login_as("tok-old")
    api.on("POST", "/auth/login", _login_ok)
    api.on("POST", "/auth/logout", ok(status=204))
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("login", "--email", "lee@aurora.example", input="orbital launch window\n")

    assert result.exit_code == 0, result.stderr
    assert [c.token for c in api.sent("POST", "/auth/logout")] == ["tok-old"]
    assert [(c.method, c.path) for c in api.calls][:2] == [
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
    ]
    assert mc.store.load().token == "tok-new"


def test_m16_login_again_ignores_a_previous_session_the_server_already_ended(mc, api):
    mc.login_as("tok-old")
    api.on("POST", "/auth/login", _login_ok)
    api.on("POST", "/auth/logout", error(401, "unauthenticated", "Your session has ended"))
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("login", "--email", "lee@aurora.example", input="orbital launch window\n")

    assert result.exit_code == 0, result.stderr
    assert result.stderr == "Next: mc inbox\n"
    assert mc.store.load().token == "tok-new"


def test_m16_a_failed_login_keeps_the_previous_session(mc, api):
    mc.login_as("tok-old")
    api.on(
        "POST", "/auth/login", error(401, "invalid_credentials", "Email or password is incorrect")
    )

    result = mc("login", "--email", "lee@aurora.example", input="typo\n")

    assert result.exit_code == 3
    assert api.sent("POST", "/auth/logout") == []
    assert mc.store.load().token == "tok-old"


def test_m16_password_is_never_a_flag(mc):
    result = mc("login", "--email", "lee@aurora.example", "--password", "x")

    assert result.exit_code == 2
    assert "No such option" in result.stderr


def test_p7_wrong_or_deactivated_login_exits_3_and_saves_nothing(mc, api):
    api.on(
        "POST",
        "/auth/login",
        error(401, "invalid_credentials", "Email or password is incorrect"),
    )

    result = mc("login", "--email", "lee@aurora.example", input="nope\n")

    assert result.exit_code == 3
    assert result.stderr.startswith("✗ Email or password is incorrect.\n")
    assert "•" not in result.stderr  # the single reason isn't repeated as a bullet
    assert mc.store.load() is None


def test_m16_logout_revokes_the_token_and_clears_the_file(mc, api):
    mc.login_as("tok-lee")
    api.on("POST", "/auth/logout", ok(status=204))

    result = mc("logout")

    assert result.exit_code == 0
    assert result.stdout == "✓ Logged out.\n"
    assert api.sent("POST", "/auth/logout")[0].token == "tok-lee"
    assert not mc.store.path.exists()


def test_m16_logout_when_the_session_already_ended_still_clears_the_file(mc, api):
    mc.login_as("tok-old")
    api.on("POST", "/auth/logout", error(401, "unauthenticated", "Your session has ended"))

    result = mc("logout")

    assert result.exit_code == 0
    assert result.stdout == "✓ Logged out.\n"
    assert not mc.store.path.exists()


def test_m16_logout_with_the_server_unreachable_still_forgets_the_session(mc):
    mc.login_as("tok-lee")

    def refuse(request):
        raise httpx2.ConnectError("connection refused", request=request)

    result = mc("logout", http=httpx2.Client(transport=httpx2.MockTransport(refuse)))

    assert result.exit_code == 4
    assert result.stdout == ""
    assert result.stderr == (
        "! Couldn't reach the server, so the session may stay valid until it expires. "
        "Removed it from this computer.\n"
    )
    assert not mc.store.path.exists()


def test_m16_logout_when_not_logged_in_says_so_without_calling_the_server(mc, api):
    result = mc("logout")

    assert result.exit_code == 0
    assert result.stdout == "✓ You're not logged in.\n"
    assert api.calls == []


def test_m16_whoami_shows_the_current_user(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("whoami")

    assert result.exit_code == 0
    assert result.stdout == (
        "Name           Lee Park\n"
        "Email          lee@aurora.example\n"
        "Role           Mission Lead\n"
        "Organisation   Aurora Space Agency\n"
        "Crew profile   none\n"
    )


def test_m16_whoami_json_prints_the_api_body(mc, api):
    mc.login_as()
    api.on("GET", "/me", ok(LEE_ME))

    result = mc("whoami", "--json")

    assert result.exit_code == 0
    assert '"email": "lee@aurora.example"' in result.stdout


def test_m16_commands_need_a_login_and_exit_3_without_one(mc, api):
    result = mc("whoami")

    assert result.exit_code == 3
    assert result.stderr == "✗ You're not logged in.\n  Log in: mc login\n"
    assert api.calls == []


def test_m16_a_401_clears_the_stored_session_and_exits_3(mc, api):
    mc.login_as("tok-expired")
    api.on("GET", "/me", error(401, "unauthenticated", "Your session has expired"))

    result = mc("whoami")

    assert result.exit_code == 3
    assert result.stderr == "✗ Your session has expired.\n  Log in: mc login\n"
    assert not mc.store.path.exists()


def test_p10_password_change_asks_current_then_new_twice_and_ends_the_session(mc, api):
    mc.login_as("tok-lee")
    api.on("POST", "/me/password", ok(status=204))

    result = mc(
        "password",
        answers=["old password here", "new passphrase is long", "new passphrase is long"],
    )

    assert result.exit_code == 0, result.stderr
    assert result.asked == [
        ("Current password", True),
        ("New password", True),
        ("Repeat new password", True),
    ]
    assert api.sent("POST", "/me/password")[0].body == {
        "current_password": "old password here",
        "new_password": "new passphrase is long",
    }
    assert result.stdout == (
        "✓ Password changed. All your sessions have ended, including this one.\n"
    )
    assert "Next: mc login" in result.stderr
    assert not mc.store.path.exists()


def test_p10_without_a_terminal_password_reads_current_then_new_from_stdin(mc, api):
    mc.login_as("tok-lee")
    api.on("POST", "/me/password", ok(status=204))

    result = mc("password", input="old password here\nnew passphrase is long\n")

    assert result.exit_code == 0, result.stderr
    assert api.sent("POST", "/me/password")[0].body == {
        "current_password": "old password here",
        "new_password": "new passphrase is long",
    }


def test_p10_without_a_terminal_a_missing_new_password_fails_clearly(mc, api):
    mc.login_as("tok-lee")

    result = mc("password", input="old password here\n")

    assert result.exit_code == 2
    assert "No password given" in result.stderr
    assert api.calls == []


def test_p10_mismatched_new_passwords_change_nothing(mc, api):
    mc.login_as()

    result = mc("password", answers=["old", "new one long enough", "typo one long enough"])

    assert result.exit_code == 2
    assert "The new passwords don't match. Nothing was changed." in result.stderr
    assert api.calls == []
    assert mc.store.path.exists()


def test_p10_short_password_is_refused_by_the_server_not_the_cli(mc, api):
    mc.login_as()
    api.on(
        "POST",
        "/me/password",
        error(422, "password_too_short", "Passwords must be at least 15 characters"),
    )

    result = mc("password", answers=["old", "short", "short"])

    assert result.exit_code == 1
    assert "✗ Passwords must be at least 15 characters." in result.stderr
    assert mc.store.path.exists()  # nothing changed, so the session is still good


def test_p10_wrong_current_password_keeps_the_session(mc, api):
    mc.login_as()
    api.on(
        "POST",
        "/me/password",
        error(403, "wrong_current_password", "Your current password is incorrect"),
    )

    result = mc("password", input="bad\nnew passphrase is long\n")

    assert result.exit_code == 1
    assert result.stderr.startswith("✗ Your current password is incorrect.\n")
    assert mc.store.path.exists()
