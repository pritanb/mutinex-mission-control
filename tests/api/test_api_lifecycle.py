"""Phase 4 reconciliation: the lifecycle commands, mission history, match apply, the inbox and
`GET /me` over HTTP (PRD §4, §5.4, §5.5, §6; AC-1, AC-3, AC-6, AC-8, AC-10, AC-12, AC-22, AC-30;
scenarios S1, S6, S7, S8; design §7).

Seed ids: Ruth 1 · Marco 2 · Ingrid 3 · Lee 4 · Nora 5 · Ana 6 · Ben 7 · Chen 8 · Dana 9.
Missions: Gateway 1 (Draft, Lee) · Station Reboost 3 (Nora, Gus accepted) · Medical Study 4
(Nora) · Telescope 5 (Active, Lee) · Deep Space Comms 6 (Pending, Nora, Marco approved) ·
Payload Demo 8 (Helix, Priya).
"""

API = "/api/v1"


def post(client, headers, path, body=None):
    return client.post(f"{API}{path}", headers=headers, json=body)


def accept_everything(client, login, mission_id):
    """Each crew member accepts their proposal on the mission, found through their inbox."""
    for who in ("ana", "chen", "dana"):
        headers = login(who)
        (item,) = client.get(f"{API}/me/inbox", headers=headers).json()["proposals"]
        assert item["mission_id"] == mission_id
        assert (
            post(client, headers, f"/assignments/{item['assignment_id']}/accept").status_code == 200
        )


# --- S1 end to end over HTTP --------------------------------------------------------------


def test_s1_golden_path_over_http(client, login):
    lee, ruth, marco, ingrid = login("lee"), login("ruth"), login("marco"), login("ingrid")

    applied = post(client, lee, "/missions/1/match/apply")
    assert applied.status_code == 201, applied.text
    assert sorted((a["slot_id"], a["crew_profile_id"]) for a in applied.json()) == [
        (1, 8),
        (2, 9),
        (3, 6),
    ]
    accept_everything(client, login, 1)

    submitted = post(client, lee, "/missions/1/submit")
    assert submitted.status_code == 200, submitted.text
    assert (submitted.json()["status"], submitted.json()["approvals_required"]) == (
        "pending_approval",
        2,
    )

    refused = post(client, ruth, "/missions/1/approve")
    assert (refused.status_code, refused.json()["error"]["code"]) == (403, "approver_is_creator")
    assert post(client, marco, "/missions/1/approve").json()["status"] == "pending_approval"
    assert post(client, ingrid, "/missions/1/approve").json()["status"] == "active"

    done = post(client, lee, "/missions/1/complete")
    assert done.json()["status"] == "completed"
    assert {a["status"] for a in done.json()["assignments"]} == {"completed"}

    history = client.get(f"{API}/missions/1/history", headers=lee).json()
    events = [(h["event"], h["actor_name"]) for h in history]
    assert events[0] == ("mission.created", "Ruth Adeyemi")
    assert ("mission.approved", "Marco Bianchi") in events
    assert events[-4] == ("mission.completed", "Lee Park")
    assert all(h["created_at"].endswith("Z") or "+" in h["created_at"] for h in history)


# --- Refusals ------------------------------------------------------------------------------


def test_ac2_submit_lists_every_problem_as_a_409(client, login):
    response = post(client, login("lee"), "/missions/1/submit")
    assert response.status_code == 409
    error = response.json()["error"]
    assert (error["code"], error["message"]) == (
        "rule_violation",
        "Lunar Gateway Resupply can't be submitted",
    )
    assert [p["code"] for p in error["problems"]] == ["slot_unfilled"] * 3


def test_s7_submit_with_too_few_approvers(client, login):
    error = post(client, login("nora"), "/missions/4/submit").json()["error"]
    assert [p["code"] for p in error["problems"]] == ["insufficient_approvers"]


def test_s6_ac10_approving_twice_and_rejecting_without_a_reason(client, login):
    again = post(client, login("marco"), "/missions/6/approve")
    assert (again.status_code, again.json()["error"]["code"]) == (409, "already_decided")

    ingrid = login("ingrid")
    no_reason = post(client, ingrid, "/missions/6/reject", {})
    assert (no_reason.status_code, no_reason.json()["error"]["code"]) == (422, "validation_error")
    rejected = post(client, ingrid, "/missions/6/reject", {"reason": "Budget not signed off"})
    assert (rejected.json()["status"], rejected.json()["approvals"]) == ("draft", [])


def test_s8_helix_activates_after_one_approval(client, login):
    assert post(client, login("priya"), "/missions/8/submit").json()["status"] == (
        "pending_approval"
    )
    assert post(client, login("sam"), "/missions/8/approve").json()["status"] == "active"


def test_ac6_cancel_needs_a_reason_and_cancels_open_assignments(client, login):
    nora = login("nora")
    assert post(client, nora, "/missions/3/cancel", {}).status_code == 422
    cancelled = post(client, nora, "/missions/3/cancel", {"reason": "Funding pulled"}).json()
    assert cancelled["status"] == "cancelled"
    assert {a["status"] for a in cancelled["assignments"]} == {"cancelled"}

    other_lead = post(client, login("lee"), "/missions/6/cancel", {"reason": "Not mine"})
    assert (other_lead.status_code, other_lead.json()["error"]["code"]) == (403, "not_owner")


def test_ac30_another_organisations_mission_is_not_found(client, login, snap):
    sam = login("sam")
    before = snap()
    for path, body in [
        ("/missions/6/approve", None),
        ("/missions/6/reject", {"reason": "No"}),
        ("/missions/5/complete", None),
        ("/missions/3/cancel", {"reason": "No"}),
        ("/missions/1/match/apply", None),
    ]:
        response = post(client, sam, path, body)
        assert (response.status_code, response.json()["error"]["code"]) == (404, "not_found")
    assert client.get(f"{API}/missions/6/history", headers=sam).status_code == 404
    assert snap() == before


# --- Inbox and me --------------------------------------------------------------------------


def test_inbox_shows_what_is_waiting_on_each_person(client, login):
    nora = client.get(f"{API}/me/inbox", headers=login("nora")).json()
    assert [(m["mission_name"], m["ready"]) for m in nora["missions"]] == [
        ("Station Reboost", False),
        ("Asteroid Survey", False),
        ("Lunar Surface Medical Study", True),
    ]
    assert nora["missions"][0]["unfilled"] == [
        {"slot_id": 6, "slot_name": "Engineer", "open_places": 1}
    ]

    ingrid = client.get(f"{API}/me/inbox", headers=login("ingrid")).json()
    assert ingrid["approvals"] == [
        {
            "mission_id": 6,
            "mission_name": "Deep Space Comms Upgrade",
            "start_date": "2027-04-01",
            "end_date": "2027-04-20",
            "approvals": 1,
            "required": 2,
        }
    ]
    assert ingrid["proposals"] == [] and ingrid["missions"] == []


def test_me_shows_the_account_organisation_and_crew_profile(client, login):
    me = client.get(f"{API}/me", headers=login("ana")).json()
    assert me == {
        "id": 6,
        "email": "ana@aurora.example",
        "name": "Ana Okafor",
        "role": "lead",
        "active": True,
        "crew_profile_id": 6,
        "organisation": {"id": 1, "name": "Aurora Space Agency", "slug": "aurora"},
    }
