"""M8: passwords, sessions and request authentication (design §4 Authentication, PRD P7, P10)."""

import hashlib
from datetime import UTC, datetime, timedelta, timezone

import pytest

from mission_control.domain.enums import Role
from mission_control.domain.errors import Forbidden, Unauthenticated
from mission_control.domain.passwords import PasswordTooShort
from mission_control.infra import security
from mission_control.seed.data import DEMO_PASSWORD
from mission_control.seed.loader import load_seed
from mission_control.services import auth

NOW = datetime(2027, 1, 5, 9, 0, tzinfo=UTC)
LEE, BEN, ANA, RUTH = 4, 7, 6, 1


@pytest.fixture
def db(conn):
    """The PRD seed with a real Argon2 hash of the demo passphrase."""
    load_seed(conn, password_hash=security.hash_password(DEMO_PASSWORD))
    return conn


def login(db, email="lee@aurora.example", password=DEMO_PASSWORD, now=NOW):
    return auth.login(db, email, password, now=now)


# --- Password hashing ---------------------------------------------------------------------


def test_passwords_are_hashed_with_argon2id_and_verify():
    hashed = security.hash_password("correct horse battery staple")
    assert hashed.startswith("$argon2id$")
    assert security.verify_password(hashed, "correct horse battery staple")
    assert not security.verify_password(hashed, "correct horse battery stapler")


def test_the_same_password_hashes_differently_each_time():
    assert security.hash_password("a" * 15) != security.hash_password("a" * 15)


def test_verify_handles_a_malformed_hash_as_a_mismatch():
    assert not security.verify_password("not-a-hash", "anything at all here")


# --- Login --------------------------------------------------------------------------------


def test_login_returns_a_token_valid_for_12_hours(db):
    session = login(db)
    assert session.user.id == LEE and session.user.role == Role.LEAD
    assert session.expires_at == NOW + timedelta(hours=12)
    assert len(session.token) >= 40


def test_login_email_is_case_insensitive(db):
    assert login(db, email="LEE@Aurora.Example").user.id == LEE


@pytest.mark.parametrize(
    "email, password",
    [
        ("lee@aurora.example", "wrong passphrase entirely"),
        ("nobody@aurora.example", DEMO_PASSWORD),
    ],
)
def test_wrong_password_and_unknown_email_get_the_same_refusal(db, email, password):
    with pytest.raises(Unauthenticated) as err:
        login(db, email=email, password=password)
    assert err.value.code == "invalid_credentials"
    assert err.value.message == "Email or password is incorrect"


def test_ac26_deactivated_user_cannot_log_in(db):
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
    with pytest.raises(Unauthenticated) as err:
        login(db)
    assert err.value.code == "invalid_credentials"
    assert err.value.message == "Email or password is incorrect"


def test_only_the_token_hash_is_stored(db):
    session = login(db)
    stored = [r[0] for r in db.execute("SELECT token_hash FROM auth_tokens")]
    assert stored == [hashlib.sha256(session.token.encode()).hexdigest()]
    assert session.token not in stored


def test_each_login_creates_a_separate_session(db):
    a, b = login(db), login(db)
    assert a.token != b.token
    assert auth.authenticate(db, a.token, now=NOW).user_id == LEE
    assert auth.authenticate(db, b.token, now=NOW).user_id == LEE


def test_login_upgrades_an_outdated_hash(db, monkeypatch):
    old = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
    login(db)
    new = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    assert new != old and security.verify_password(new, DEMO_PASSWORD)


# --- Authenticating a request -------------------------------------------------------------


def test_a_valid_token_resolves_to_the_actor(db):
    session = login(db, email="ana@aurora.example")
    actor = auth.authenticate(db, session.token, now=NOW + timedelta(hours=1))
    assert (actor.user_id, actor.org_id, actor.role, actor.crew_profile_id) == (
        ANA,
        1,
        Role.LEAD,
        ANA,
    )


def test_actor_without_a_crew_profile_has_none(db):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    assert actor.crew_profile_id is None


@pytest.mark.parametrize("token", ["", "made-up-token", None])
def test_missing_or_unknown_token_is_unauthenticated(db, token):
    with pytest.raises(Unauthenticated) as err:
        auth.authenticate(db, token, now=NOW)
    assert err.value.code == "unauthenticated"


def test_token_expires_after_12_hours(db):
    token = login(db).token
    auth.authenticate(db, token, now=NOW + timedelta(hours=11, minutes=59))
    with pytest.raises(Unauthenticated):
        auth.authenticate(db, token, now=NOW + timedelta(hours=12))


def test_token_expiry_works_with_a_non_utc_login_time(db):
    sydney = timezone(timedelta(hours=10))
    token = login(db, now=datetime(2027, 1, 5, 19, 0, tzinfo=sydney)).token  # 09:00 UTC
    auth.authenticate(db, token, now=datetime(2027, 1, 5, 20, 59, tzinfo=UTC))
    with pytest.raises(Unauthenticated):
        auth.authenticate(db, token, now=datetime(2027, 1, 5, 21, 0, tzinfo=UTC))


def test_role_is_read_fresh_on_every_request(db):
    token = login(db).token
    assert auth.authenticate(db, token, now=NOW).role == Role.LEAD
    db.execute("UPDATE users SET role = 'director' WHERE id = ?", (LEE,))
    assert auth.authenticate(db, token, now=NOW).role == Role.DIRECTOR


def test_a_deactivated_user_is_refused_even_with_a_live_token(db):
    token = login(db).token
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
    with pytest.raises(Unauthenticated):
        auth.authenticate(db, token, now=NOW)


# --- Revocation ---------------------------------------------------------------------------


def test_logout_revokes_only_that_session(db):
    first, second = login(db), login(db)
    auth.logout(db, first.token, now=NOW)
    with pytest.raises(Unauthenticated):
        auth.authenticate(db, first.token, now=NOW)
    assert auth.authenticate(db, second.token, now=NOW).user_id == LEE


def test_logout_with_an_unknown_token_is_harmless(db):
    auth.logout(db, "not-a-real-token", now=NOW)


def test_revoking_all_sessions_ends_every_session_of_that_user_only(db):
    lee_a, lee_b, ben = login(db), login(db), login(db, email="ben@aurora.example")
    auth.revoke_all_sessions(db, LEE, now=NOW)
    for token in (lee_a.token, lee_b.token):
        with pytest.raises(Unauthenticated):
            auth.authenticate(db, token, now=NOW)
    assert auth.authenticate(db, ben.token, now=NOW).user_id == BEN


# --- Changing a password (P10) ------------------------------------------------------------


def test_p10_password_change_revokes_every_session_including_the_current_one(db):
    current, other = login(db), login(db)
    actor = auth.authenticate(db, current.token, now=NOW)
    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    for token in (current.token, other.token):
        with pytest.raises(Unauthenticated):
            auth.authenticate(db, token, now=NOW)
    assert login(db, password="a brand new passphrase").user.id == LEE
    with pytest.raises(Unauthenticated):
        login(db)


def test_p10_wrong_current_password_is_refused_and_nothing_changes(db):
    session = login(db)
    actor = auth.authenticate(db, session.token, now=NOW)
    with pytest.raises(Forbidden) as err:
        auth.change_password(
            db, actor, "not my passphrase at all", "a brand new passphrase", now=NOW
        )
    assert err.value.code == "wrong_current_password"
    assert auth.authenticate(db, session.token, now=NOW).user_id == LEE
    assert login(db).user.id == LEE


def test_p10_new_password_must_be_at_least_15_characters(db):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    with pytest.raises(PasswordTooShort):
        auth.change_password(db, actor, DEMO_PASSWORD, "too short", now=NOW)
    assert login(db).user.id == LEE


def test_password_change_is_audited_without_the_password(db):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    event, data = db.execute(
        "SELECT event, data FROM audit_events WHERE actor_id = ? ORDER BY id DESC LIMIT 1", (LEE,)
    ).fetchone()
    assert event == "user.password_changed"
    assert "passphrase" not in data and DEMO_PASSWORD not in data


# Regression: an unknown email costs the same Argon2 work as a real one (no timing leak)


def test_unknown_email_still_runs_a_password_verification(db, monkeypatch):
    calls = []
    real_verify = security.verify_password

    def counting_verify(password_hash, password):
        calls.append(password_hash)
        return real_verify(password_hash, password)

    monkeypatch.setattr(security, "verify_password", counting_verify)
    with pytest.raises(Unauthenticated):
        login(db, email="nobody@aurora.example")
    assert len(calls) == 1
    assert calls[0].startswith("$argon2id$")  # a real Argon2 hash, so the work is the same


def test_the_dummy_hash_never_matches_a_password(db):
    assert not security.verify_password(security.dummy_hash(), DEMO_PASSWORD)
    assert not security.verify_password(security.dummy_hash(), "")


# Regression: production Argon2 settings stay in place; tests use cheap ones for speed


@pytest.mark.real_argon2
def test_production_hashes_use_the_libraries_recommended_argon2id_settings():
    hashed = security.hash_password("correct horse battery staple")
    assert hashed.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert security.verify_password(hashed, "correct horse battery staple")


def test_tests_run_with_cheap_but_still_argon2id_hashes():
    hashed = security.hash_password("correct horse battery staple")
    assert hashed.startswith("$argon2id$")
    assert "m=65536,t=3,p=4" not in hashed


# Regression: no Argon2 work runs while the write lock is held


def _record_transaction_state(db, monkeypatch):
    """Wrap the Argon2 calls to record whether a transaction was open at call time."""
    seen = []
    real_verify, real_hash = security.verify_password, security.hash_password

    def verify(password_hash, password):
        seen.append(("verify", db.in_transaction))
        return real_verify(password_hash, password)

    def hash_password(password):
        seen.append(("hash", db.in_transaction))
        return real_hash(password)

    monkeypatch.setattr(security, "verify_password", verify)
    monkeypatch.setattr(security, "hash_password", hash_password)
    return seen


@pytest.mark.parametrize(
    "email, password, refused",
    [
        ("lee@aurora.example", DEMO_PASSWORD, False),
        ("lee@aurora.example", "wrong passphrase entirely", True),
        ("nobody@aurora.example", DEMO_PASSWORD, True),
    ],
)
def test_login_runs_argon2_outside_the_write_transaction(db, monkeypatch, email, password, refused):
    seen = _record_transaction_state(db, monkeypatch)
    if refused:
        with pytest.raises(Unauthenticated):
            login(db, email=email, password=password)
    else:
        login(db, email=email, password=password)
    assert seen == [("verify", False)]


def test_login_rehash_runs_argon2_outside_the_write_transaction(db, monkeypatch):
    old = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    monkeypatch.setattr(security, "needs_rehash", lambda h: True)
    seen = _record_transaction_state(db, monkeypatch)
    login(db)
    assert seen == [("verify", False), ("hash", False)]
    new = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    assert new != old


def test_change_password_runs_argon2_outside_the_write_transaction(db, monkeypatch):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    seen = _record_transaction_state(db, monkeypatch)
    auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    assert seen == [("verify", False), ("hash", False)]


def _change_hash_during_verify(db, monkeypatch):
    """Simulate another request changing the stored hash between the verify and the write."""
    real_verify = security.verify_password

    def verify(password_hash, password):
        result = real_verify(password_hash, password)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (security.hash_password("someone else's new passphrase"), LEE),
        )
        return result

    monkeypatch.setattr(security, "verify_password", verify)


def test_login_is_refused_if_the_password_changed_after_it_was_verified(db, monkeypatch):
    _change_hash_during_verify(db, monkeypatch)
    with pytest.raises(Unauthenticated) as err:
        login(db)
    assert err.value.code == "invalid_credentials"
    assert err.value.message == "Email or password is incorrect"
    assert db.execute("SELECT count(*) FROM auth_tokens").fetchone()[0] == 0


def test_login_is_refused_if_the_user_was_deactivated_after_the_verify(db, monkeypatch):
    real_verify = security.verify_password

    def verify(password_hash, password):
        db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (LEE,))
        return real_verify(password_hash, password)

    monkeypatch.setattr(security, "verify_password", verify)
    with pytest.raises(Unauthenticated) as err:
        login(db)
    assert err.value.code == "invalid_credentials"
    assert db.execute("SELECT count(*) FROM auth_tokens").fetchone()[0] == 0


def test_change_password_is_refused_if_the_password_changed_after_it_was_verified(db, monkeypatch):
    session = login(db)
    actor = auth.authenticate(db, session.token, now=NOW)
    _change_hash_during_verify(db, monkeypatch)
    with pytest.raises(Forbidden) as err:
        auth.change_password(db, actor, DEMO_PASSWORD, "a brand new passphrase", now=NOW)
    assert err.value.code == "wrong_current_password"
    assert err.value.message == "Your current password is incorrect"
    assert auth.authenticate(db, session.token, now=NOW).user_id == LEE
    stored = db.execute("SELECT password_hash FROM users WHERE id = ?", (LEE,)).fetchone()[0]
    assert security.verify_password(stored, "someone else's new passphrase")
    assert (
        db.execute(
            "SELECT count(*) FROM audit_events WHERE event = 'user.password_changed'"
        ).fetchone()[0]
        == 0
    )


# --- Who am I (GET /me) -------------------------------------------------------------------


def test_whoami_returns_the_callers_account_organisation_and_crew_profile(db):
    actor = auth.authenticate(db, login(db, "ana@aurora.example").token, now=NOW)
    me = auth.whoami(db, actor)
    assert (me.user.name, me.user.email, me.user.role) == (
        "Ana Okafor",
        "ana@aurora.example",
        Role.LEAD,
    )
    assert (me.organisation.name, me.crew_profile_id) == ("Aurora Space Agency", ANA)


def test_whoami_for_someone_without_a_crew_profile(db):
    actor = auth.authenticate(db, login(db).token, now=NOW)
    assert auth.whoami(db, actor).crew_profile_id is None
