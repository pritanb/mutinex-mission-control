"""M15: signing in and out over HTTP, who am I, changing your password (PRD §4 workflow 1, P7,
P10, AC-26; design §4 Authentication).

Seed ids: Ruth 1 · Lee 4 · Ana 6 (Lead with a crew profile) · Ben 7 · Gus 12 · Sam 14 (Helix).
"""

from datetime import UTC, datetime, timedelta

API = "/api/v1"
PASSWORD = "orbital launch window"


def test_login_returns_a_token_and_the_user(client):
    response = client.post(
        f"{API}/auth/login", json={"email": "lee@aurora.example", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"token", "expires_at", "user"}
    assert len(body["token"]) >= 40
    assert body["user"] == {
        "id": 4,
        "email": "lee@aurora.example",
        "name": "Lee Park",
        "role": "lead",
        "active": True,
    }
    expires = datetime.fromisoformat(body["expires_at"])
    assert timedelta(hours=11, minutes=59) < expires - datetime.now(UTC) <= timedelta(hours=12)


def test_login_unknown_email_and_wrong_password_look_the_same(client):
    unknown = client.post(
        f"{API}/auth/login", json={"email": "nobody@x.example", "password": PASSWORD}
    )
    wrong = client.post(
        f"{API}/auth/login", json={"email": "lee@aurora.example", "password": "x" * 20}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_me_returns_the_current_user_role_and_crew_profile(client, login):
    me = client.get(f"{API}/me", headers=login("ana")).json()
    assert (me["id"], me["role"], me["crew_profile_id"], me["organisation"]["id"]) == (
        6,
        "lead",
        6,
        1,
    )
    assert client.get(f"{API}/me", headers=login("lee")).json()["crew_profile_id"] is None


def test_logout_revokes_the_token(client, login):
    lee = login("lee")
    assert client.post(f"{API}/auth/logout", headers=lee).status_code == 204
    assert client.get(f"{API}/me", headers=lee).status_code == 401


def test_logout_ends_only_that_session(client, login):
    first, second = login("lee"), login("lee")
    client.post(f"{API}/auth/logout", headers=first)
    assert client.get(f"{API}/me", headers=second).status_code == 200


def test_p10_change_password_ends_every_session_and_the_new_one_works(client, login):
    first, second = login("lee"), login("lee")
    response = client.post(
        f"{API}/me/password",
        headers=first,
        json={"current_password": PASSWORD, "new_password": "a brand new passphrase"},
    )
    assert response.status_code == 204
    assert client.get(f"{API}/me", headers=first).status_code == 401
    assert client.get(f"{API}/me", headers=second).status_code == 401
    login("lee", password="a brand new passphrase")
    old = client.post(
        f"{API}/auth/login", json={"email": "lee@aurora.example", "password": PASSWORD}
    )
    assert old.status_code == 401


def test_p10_new_password_must_be_15_characters(client, login):
    response = client.post(
        f"{API}/me/password",
        headers=login("lee"),
        json={"current_password": PASSWORD, "new_password": "fourteen chars"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "password_too_short"


def test_role_is_read_fresh_on_every_request(client, login):
    """Ruth demotes Ana to Crew; Ana's existing token acts as Crew on the very next request."""
    ana = login("ana")
    assert client.get(f"{API}/skills", headers=ana).status_code == 200
    changed = client.patch(f"{API}/users/6", headers=login("ruth"), json={"role": "crew"})
    assert changed.status_code == 200
    assert client.get(f"{API}/me", headers=ana).json()["role"] == "crew"
    assert client.get(f"{API}/skills", headers=ana).status_code == 403


def test_ac26_deactivated_user_loses_sessions_and_cannot_sign_in(client, login):
    """Ingrid (one of three Directors, no commitments) is deactivated by Ruth: her session ends
    at once and she can't sign in again."""
    ingrid = login("ingrid")
    response = client.patch(f"{API}/users/3", headers=login("ruth"), json={"active": False})
    assert response.status_code == 200
    assert response.json()["active"] is False
    assert client.get(f"{API}/me", headers=ingrid).status_code == 401
    again = client.post(
        f"{API}/auth/login", json={"email": "ingrid@aurora.example", "password": PASSWORD}
    )
    assert again.status_code == 401
    assert again.json()["error"]["code"] == "invalid_credentials"
