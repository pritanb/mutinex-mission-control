"""M15: PRD scenarios over HTTP, as far as the services that exist allow (S1 up to acceptance,
S3b, S4; AC-14, AC-15, AC-22). Submission, approval and completion follow once those endpoints
exist.

Seed ids: Lee 4 owns Gateway 1 (slots Flight Engineer 1, Mission Specialist 2, Commander 3) ·
Nora 5 owns Asteroid 2 and Reboost 3 (slot Engineer 6) · Ana 6 · Chen 8 · Dana 9 · Eli 10 ·
Fay 11 · Gus 12.
"""

API = "/api/v1"


def propose(client, headers, mission, slot, crew):
    return client.post(
        f"{API}/missions/{mission}/assignments",
        headers=headers,
        json={"slot_id": slot, "crew_profile_id": crew},
    )


def test_s1_lee_matches_proposes_the_suggestion_and_crew_accept(client, login, db):
    lee = login("lee")
    preview = client.get(f"{API}/missions/1/match", headers=lee).json()
    picks = {(s["slot_id"], p["crew_profile_id"]) for s in preview["slots"] for p in s["suggested"]}
    assert picks == {(3, 6), (1, 8), (2, 9)}  # Commander Ana, Flight Engineer Chen, Specialist Dana

    made = {}
    for slot, crew in sorted(picks):
        response = propose(client, lee, 1, slot, crew)
        assert response.status_code == 201, response.text
        made[crew] = response.json()["id"]

    for crew, who in ((6, "ana"), (8, "chen"), (9, "dana")):
        accepted = client.post(f"{API}/assignments/{made[crew]}/accept", headers=login(who))
        assert accepted.status_code == 200, accepted.text

    gateway = client.get(f"{API}/missions/1", headers=lee).json()
    assert gateway["status"] == "draft"
    assert [s["open_places"] for s in gateway["slots"]] == [0, 0, 0]
    assert sorted((a["crew_name"], a["status"]) for a in gateway["assignments"]) == [
        ("Ana", "accepted"),
        ("Chen", "accepted"),
        ("Dana", "accepted"),
    ]
    events = [
        r[0]
        for r in db.execute(
            "SELECT event FROM audit_events WHERE mission_id = 1 AND assignment_id IS NOT NULL"
            " ORDER BY id"
        )
    ]
    assert events == ["assignment.proposed"] * 3 + ["assignment.accepted"] * 3


def test_s3b_an_accepted_assignment_changes_the_asteroid_suggestion(client, login):
    lee = login("lee")
    made = propose(client, lee, 1, 3, 6).json()["id"]
    client.post(f"{API}/assignments/{made}/accept", headers=login("ana"))
    body = client.get(f"{API}/missions/2/match", headers=login("nora")).json()
    pilot, geologist = body["slots"]
    assert [p["name"] for p in pilot["suggested"]] == ["Eli"]
    assert geologist["unfilled"] == 1


def test_s4_ac14_ac15_refusals_name_the_reason_and_the_conflicting_mission(client, login):
    lee, nora = login("lee"), login("nora")

    gus = propose(client, lee, 1, 1, 12)
    assert gus.status_code == 409
    assert gus.json()["error"]["code"] == "rule_violation"
    assert [p["code"] for p in gus.json()["error"]["problems"]] == ["overlap"]
    assert "Station Reboost" in gus.json()["error"]["problems"][0]["message"]

    fay = propose(client, lee, 1, 3, 11)
    assert fay.status_code == 409
    assert fay.json()["error"]["code"] == "rule_violation"
    assert [p["code"] for p in fay.json()["error"]["problems"]] == ["unavailable"]

    reboost = propose(client, nora, 3, 6, 8)
    gateway = propose(client, lee, 1, 1, 8)
    assert reboost.status_code == gateway.status_code == 201  # overlapping proposals are fine

    chen = login("chen")
    first = client.post(f"{API}/assignments/{reboost.json()['id']}/accept", headers=chen)
    assert first.status_code == 200
    second = client.post(f"{API}/assignments/{gateway.json()['id']}/accept", headers=chen)
    assert second.status_code == 409
    error = second.json()["error"]
    assert error["code"] == "rule_violation"
    assert [p["code"] for p in error["problems"]] == ["overlap"]
    assert "Station Reboost" in error["problems"][0]["message"]
    assert error["problems"][0]["refs"]["mission_name"] == "Station Reboost"
