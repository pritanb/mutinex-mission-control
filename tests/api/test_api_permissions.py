"""M15: permissions over HTTP, a role × action table (PRD §5.7, M3, P3, P4, AC-7, AC-23,
AC-24, AC-25; design §4: 404 for anything not visible, 403 for visible but not allowed).

Each row: who calls, the request, and the status and code expected. Every row starts from a
fresh seed.

Seed ids: Ruth 1 (Director, created Gateway) · Lee 4 (owns Gateway 1) · Nora 5 (Lead) · Ana 6 ·
Ben 7 (Crew, on Comms 6 only) · Fay 11 · Gateway slots 1–3 · Ben's Comms assignment 7.
"""

import pytest

API = "/api/v1"
PW = "a perfectly long passphrase"

NEW_MISSION = {
    "name": "Polar Relay",
    "start_date": "2027-06-01",
    "end_date": "2027-06-05",
    "slots": [{"name": "Pilot", "headcount": 1, "requirements": [{"skill_id": 1, "min_level": 3}]}],
}

ROWS = [
    # Organisation, users, catalogue: Directors manage; Leads read the catalogue (AC-25)
    ("ruth", "GET", "/org", None, 200, None),
    ("lee", "GET", "/org", None, 403, "role_forbidden"),
    ("ben", "GET", "/org", None, 403, "role_forbidden"),
    ("lee", "PATCH", "/org", {"required_approvals": 1}, 403, "role_forbidden"),
    ("ruth", "GET", "/users", None, 200, None),
    ("lee", "GET", "/users", None, 403, "role_forbidden"),
    ("ben", "GET", "/users", None, 403, "role_forbidden"),
    (
        "lee",
        "POST",
        "/users",
        {"email": "z@aurora.example", "name": "Z", "role": "crew", "password": PW},
        403,
        "role_forbidden",
    ),
    ("lee", "PATCH", "/users/7", {"role": "lead"}, 403, "role_forbidden"),
    ("lee", "POST", "/users/4/crew-profile", {}, 403, "role_forbidden"),
    ("ruth", "GET", "/skills", None, 200, None),
    ("lee", "GET", "/skills", None, 200, None),
    ("ben", "GET", "/skills", None, 403, "role_forbidden"),
    ("lee", "POST", "/skills", {"name": "Robotics"}, 403, "role_forbidden"),
    ("lee", "PATCH", "/skills/1", {"name": "Flying"}, 403, "role_forbidden"),
    ("lee", "DELETE", "/skills/5", None, 403, "role_forbidden"),
    # Crew profiles: crew see only their own (AC-24); only you edit your details (P4)
    ("lee", "GET", "/crew/11", None, 200, None),
    ("ben", "GET", "/crew/7", None, 200, None),
    ("ben", "GET", "/crew/11", None, 404, "not_found"),
    ("ben", "GET", "/crew/11/unavailability", None, 404, "not_found"),
    ("ben", "GET", "/crew/11/assignments", None, 404, "not_found"),
    ("ben", "PATCH", "/crew/7", {"bio": "Hi"}, 200, None),
    ("lee", "PATCH", "/crew/7", {"bio": "Hi"}, 403, "not_owner"),
    ("ruth", "PATCH", "/crew/7", {"bio": "Hi"}, 403, "not_owner"),
    (
        "lee",
        "POST",
        "/crew/11/unavailability",
        {"start_date": "2027-09-01", "end_date": "2027-09-02", "reason": "x"},
        403,
        "not_owner",
    ),
    ("ruth", "DELETE", "/crew/11/unavailability/1", None, 403, "not_owner"),
    # Skill levels: Leads and Directors, never their own (P3, AC-23)
    ("lee", "PUT", "/crew/6/skills/1", {"level": 4}, 200, None),
    ("ruth", "PUT", "/crew/6/skills/1", {"level": 4}, 200, None),
    ("ana", "PUT", "/crew/6/skills/1", {"level": 4}, 403, "self_skill_edit"),
    ("ana", "DELETE", "/crew/6/skills/1", None, 403, "self_skill_edit"),
    ("ben", "PUT", "/crew/7/skills/4", {"level": 5}, 403, "role_forbidden"),
    ("ben", "DELETE", "/crew/7/skills/4", None, 403, "role_forbidden"),
    # Missions: everyone in the org reads; crew only those they're on; only the owner edits
    ("lee", "GET", "/missions/2", None, 200, None),
    ("ruth", "GET", "/missions/2", None, 200, None),
    ("ben", "GET", "/missions/6", None, 200, None),
    ("ben", "GET", "/missions/1", None, 404, "not_found"),
    ("lee", "POST", "/missions", NEW_MISSION, 201, None),
    ("ben", "POST", "/missions", NEW_MISSION, 403, "role_forbidden"),
    ("lee", "POST", "/missions", {**NEW_MISSION, "owner_id": 5}, 403, "not_owner"),
    ("lee", "PATCH", "/missions/1", {"name": "G"}, 200, None),
    ("nora", "PATCH", "/missions/1", {"name": "G"}, 403, "not_owner"),
    ("ruth", "PATCH", "/missions/1", {"name": "G"}, 403, "role_forbidden"),
    ("ben", "PATCH", "/missions/1", {"name": "G"}, 404, "not_found"),
    (
        "nora",
        "POST",
        "/missions/1/slots",
        {"name": "X", "headcount": 1, "requirements": [{"skill_id": 1, "min_level": 1}]},
        403,
        "not_owner",
    ),
    ("nora", "PATCH", "/missions/1/slots/1", {"headcount": 2}, 403, "not_owner"),
    ("nora", "DELETE", "/missions/1/slots/1", None, 403, "not_owner"),
    ("ruth", "POST", "/missions/1/owner", {"owner_id": 5}, 200, None),
    ("lee", "POST", "/missions/1/owner", {"owner_id": 5}, 403, "role_forbidden"),
    ("ben", "POST", "/missions/1/owner", {"owner_id": 5}, 404, "not_found"),
    # Matcher preview: owner or a Director
    ("lee", "GET", "/missions/1/match", None, 200, None),
    ("ruth", "GET", "/missions/1/match", None, 200, None),
    ("nora", "GET", "/missions/1/match", None, 403, "not_owner"),
    ("ben", "GET", "/missions/1/match", None, 404, "not_found"),
    # Assignments: only the owner proposes and removes; only the person responds
    ("lee", "POST", "/missions/1/assignments", {"slot_id": 3, "crew_profile_id": 6}, 201, None),
    (
        "nora",
        "POST",
        "/missions/1/assignments",
        {"slot_id": 3, "crew_profile_id": 6},
        403,
        "not_owner",
    ),
    (
        "ruth",
        "POST",
        "/missions/1/assignments",
        {"slot_id": 3, "crew_profile_id": 6},
        403,
        "role_forbidden",
    ),
    (
        "ben",
        "POST",
        "/missions/1/assignments",
        {"slot_id": 3, "crew_profile_id": 6},
        404,
        "not_found",
    ),
    ("lee", "POST", "/assignments/7/remove", None, 403, "not_owner"),
    ("chen", "POST", "/assignments/7/withdraw", {"reason": "x"}, 404, "not_found"),
    ("nora", "POST", "/assignments/7/withdraw", {"reason": "x"}, 403, "not_owner"),
    ("ruth", "POST", "/assignments/7/accept", None, 403, "not_owner"),
]


@pytest.mark.parametrize(
    ("who", "method", "path", "body", "status", "code"),
    ROWS,
    ids=[f"{r[0]}-{r[1]}-{r[2]}" for r in ROWS],
)
def test_role_action_table(client, login, who, method, path, body, status, code):
    response = client.request(method, f"{API}{path}", headers=login(who), json=body)
    assert response.status_code == status, response.text
    if code is not None:
        assert response.json()["error"]["code"] == code


def test_ac7_after_transfer_the_new_owner_can_edit_and_the_old_cannot(client, login):
    client.post(f"{API}/missions/1/owner", headers=login("ruth"), json={"owner_id": 5})
    assert (
        client.patch(f"{API}/missions/1", headers=login("nora"), json={"name": "N"}).status_code
        == 200
    )
    old = client.patch(f"{API}/missions/1", headers=login("lee"), json={"name": "L"})
    assert old.status_code == 403
    assert old.json()["error"]["code"] == "not_owner"


def test_ac24_unavailability_reason_is_hidden_from_leads_and_shown_to_directors(client, login):
    lee_view = client.get(f"{API}/crew/11", headers=login("lee")).json()
    ruth_view = client.get(f"{API}/crew/11", headers=login("ruth")).json()
    period = {"id": 1, "start_date": "2027-03-05", "end_date": "2027-03-08"}
    assert lee_view["unavailability"] == [{**period, "reason": None}]
    assert ruth_view["unavailability"] == [{**period, "reason": "Medical"}]
    lee_list = client.get(f"{API}/crew/11/unavailability", headers=login("lee")).json()
    assert lee_list == [{**period, "reason": None}]


def test_ac24_ben_sees_only_his_own_profile_and_missions_he_is_on(client, login):
    ben = login("ben")
    assert [c["crew_profile_id"] for c in client.get(f"{API}/crew", headers=ben).json()] == [7]
    assert [m["id"] for m in client.get(f"{API}/missions", headers=ben).json()] == [6]


def test_ac23_ben_edits_his_details_and_unavailability_but_not_skills(client, login):
    ben = login("ben")
    assert (
        client.patch(f"{API}/crew/7", headers=ben, json={"display_name": "Benny"}).status_code
        == 200
    )
    added = client.post(
        f"{API}/crew/7/unavailability",
        headers=ben,
        json={"start_date": "2027-09-01", "end_date": "2027-09-02", "reason": "Wedding"},
    )
    assert added.status_code == 201
    assert client.put(f"{API}/crew/7/skills/4", headers=ben, json={"level": 5}).status_code == 403
