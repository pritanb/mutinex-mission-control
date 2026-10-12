"""M15: each endpoint over HTTP: status codes, response shapes and that the call reaches its
service. Business rules are tested at the service level; here one representative refusal per
area shows the mapping (PRD §4 workflows 2–7, P1, P4, P7, P9, M1, M2, M7, S1–S3; design §7).

Seed ids: Ruth 1 · Marco 2 · Ingrid 3 · Lee 4 · Nora 5 · Ana 6 · Ben 7 · Chen 8 · Dana 9 ·
Eli 10 · Fay 11 · Gus 12 · Hana 13. Missions: Gateway 1 (Lee) · Asteroid 2 (Nora) · Reboost 3 ·
Medical 4 · Telescope 5 (Active) · Comms 6 (Pending) · Mars 7 (Completed). Gateway slots: Flight
Engineer 1 · Mission Specialist 2 · Commander 3. Skills: Piloting 1 · Leadership 2 · Systems
Engineering 3 · EVA 4 · Geology 5 · Flight Medicine 6. Fay's unavailability is id 1. Seeded
assignments: Gus on Reboost 1 · Ben on Comms 7.
"""

API = "/api/v1"


# --- Organisation -------------------------------------------------------------------------


def test_org_view_and_set_required_approvals(client, login, db):
    ruth = login("ruth")
    assert client.get(f"{API}/org", headers=ruth).json() == {
        "id": 1,
        "name": "Aurora Space Agency",
        "slug": "aurora",
        "required_approvals": 2,
    }
    response = client.patch(f"{API}/org", headers=ruth, json={"required_approvals": 3})
    assert response.status_code == 200
    assert response.json()["required_approvals"] == 3
    assert (
        db.execute("SELECT required_approvals FROM organisations WHERE id = 1").fetchone()[0] == 3
    )


def test_a1_required_approvals_below_one_is_422(client, login):
    response = client.patch(f"{API}/org", headers=login("ruth"), json={"required_approvals": 0})
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "At least one approval must be required"


# --- Users --------------------------------------------------------------------------------


def test_users_list_is_the_organisations_users(client, login):
    users = client.get(f"{API}/users", headers=login("ruth")).json()
    assert [u["id"] for u in users] == list(range(1, 14))
    assert users[0] == {
        "id": 1,
        "email": "ruth@aurora.example",
        "name": "Ruth Adeyemi",
        "role": "director",
        "active": True,
    }


def test_p10_create_user_with_initial_password_who_can_then_sign_in(client, login):
    response = client.post(
        f"{API}/users",
        headers=login("ruth"),
        json={
            "email": "zoe@aurora.example",
            "name": "Zoe Lund",
            "role": "crew",
            "password": "a fine initial passphrase",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "zoe@aurora.example" and body["role"] == "crew" and body["active"]
    zoe = login("zoe@aurora.example", password="a fine initial passphrase")
    assert client.get(f"{API}/me", headers=zoe).json()["crew_profile_id"] is not None


def test_create_user_duplicate_email_is_409_already_exists(client, login):
    response = client.post(
        f"{API}/users",
        headers=login("ruth"),
        json={"email": "kai@helix.example", "name": "K", "role": "crew", "password": "x" * 15},
    )
    assert response.status_code == 409
    assert response.json()["error"]["problems"][0]["code"] == "already_exists"


def test_create_user_with_unknown_role_is_422(client, login):
    response = client.post(
        f"{API}/users",
        headers=login("ruth"),
        json={"email": "a@aurora.example", "name": "A", "role": "captain", "password": "x" * 15},
    )
    assert response.status_code == 422
    assert response.json()["error"]["problems"][0]["message"] == (
        "role must be one of: director, lead, crew"
    )


def test_change_role_and_p9_crew_profile_on_demotion(client, login):
    response = client.patch(f"{API}/users/3", headers=login("ruth"), json={"role": "crew"})
    assert response.status_code == 200
    assert response.json()["role"] == "crew"


def test_p7_role_change_refused_while_owning_open_missions(client, login):
    response = client.patch(f"{API}/users/4", headers=login("ruth"), json={"role": "crew"})
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert error["problems"][0]["code"] == "owns_open_missions"


def test_ac26_deactivating_someone_with_open_assignments_is_409(client, login):
    response = client.patch(f"{API}/users/12", headers=login("ruth"), json={"active": False})
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert [p["code"] for p in error["problems"]] == ["has_open_assignments"]


def test_patch_user_with_no_fields_changes_nothing(client, login, snap):
    ruth = login("ruth")
    before = snap()
    response = client.patch(f"{API}/users/3", headers=ruth, json={})
    assert response.status_code == 200 and response.json()["id"] == 3
    assert snap() == before


def test_patch_user_refuses_role_and_deactivation_together(client, login, snap):
    ruth = login("ruth")
    before = snap()
    response = client.patch(f"{API}/users/3", headers=ruth, json={"role": "lead", "active": False})
    assert response.status_code == 422
    assert response.json()["error"]["message"] == (
        "Change a user's role and deactivate them in separate requests"
    )
    assert snap() == before


def test_users_cannot_be_reactivated(client, login):
    response = client.patch(f"{API}/users/3", headers=login("ruth"), json={"active": True})
    assert response.status_code == 422


def test_give_a_lead_a_crew_profile(client, login):
    response = client.post(
        f"{API}/users/4/crew-profile", headers=login("ruth"), json={"display_name": "Lee"}
    )
    assert response.status_code == 201
    assert response.json() == {
        "crew_profile_id": response.json()["crew_profile_id"],
        "user_id": 4,
        "name": "Lee",
        "bio": None,
    }
    again = client.post(f"{API}/users/4/crew-profile", headers=login("ruth"), json={})
    assert again.status_code == 409


def test_crew_profile_body_is_optional(client, login):
    response = client.post(f"{API}/users/5/crew-profile", headers=login("ruth"))
    assert response.status_code == 201
    assert response.json()["name"] == "Nora"


# --- Skills -------------------------------------------------------------------------------


def test_skills_list_add_rename_delete(client, login, db):
    ruth = login("ruth")
    skills = client.get(f"{API}/skills", headers=login("lee")).json()
    assert [s["name"] for s in skills][:2] == ["EVA", "Flight Medicine"]
    assert skills[0] == {"id": 4, "name": "EVA", "category": None}

    added = client.post(f"{API}/skills", headers=ruth, json={"name": "Robotics", "category": "Eng"})
    assert added.status_code == 201
    skill_id = added.json()["id"]
    assert added.json() == {"id": skill_id, "name": "Robotics", "category": "Eng"}

    renamed = client.patch(f"{API}/skills/{skill_id}", headers=ruth, json={"name": "Robotic Arm"})
    assert renamed.json() == {"id": skill_id, "name": "Robotic Arm", "category": "Eng"}
    cleared = client.patch(f"{API}/skills/{skill_id}", headers=ruth, json={"category": None})
    assert cleared.json()["category"] is None

    assert client.delete(f"{API}/skills/{skill_id}", headers=ruth).status_code == 204
    assert db.execute("SELECT count(*) FROM skills WHERE id = ?", (skill_id,)).fetchone()[0] == 0


def test_p1_deleting_a_used_skill_is_409(client, login):
    response = client.delete(f"{API}/skills/1", headers=login("ruth"))
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert [p["code"] for p in error["problems"]] == ["skill_in_use"]


# --- Crew ---------------------------------------------------------------------------------


def test_crew_list_and_view(client, login):
    lee = login("lee")
    crew = client.get(f"{API}/crew", headers=lee).json()
    assert [c["crew_profile_id"] for c in crew] == [2, 6, 7, 8, 9, 10, 11, 12, 13]
    fay = client.get(f"{API}/crew/11", headers=lee).json()
    assert fay == {
        "crew_profile_id": 11,
        "user_id": 11,
        "name": "Fay",
        "email": "fay@aurora.example",
        "active": True,
        "bio": None,
        "skills": [
            {"skill_id": 2, "skill_name": "Leadership", "level": 4},
            {"skill_id": 1, "skill_name": "Piloting", "level": 4},
        ],
        "unavailability": [
            {"id": 1, "start_date": "2027-03-05", "end_date": "2027-03-08", "reason": None}
        ],
    }


def test_p4_edit_own_details(client, login):
    response = client.patch(
        f"{API}/crew/7", headers=login("ben"), json={"display_name": "Benji", "bio": "EVA nerd"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "crew_profile_id": 7,
        "user_id": 7,
        "name": "Benji",
        "bio": "EVA nerd",
    }


def test_p3_set_and_remove_a_skill_level(client, login, db):
    lee = login("lee")
    response = client.put(f"{API}/crew/13/skills/5", headers=lee, json={"level": 4})
    assert response.status_code == 200
    assert response.json() == {"skill_id": 5, "skill_name": "Geology", "level": 4}
    assert client.delete(f"{API}/crew/13/skills/5", headers=lee).status_code == 204
    row = db.execute("SELECT 1 FROM crew_skills WHERE crew_profile_id = 13 AND skill_id = 5")
    assert row.fetchone() is None


def test_p2_skill_level_outside_1_to_5_is_422(client, login):
    response = client.put(f"{API}/crew/13/skills/5", headers=login("lee"), json={"level": 6})
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Skill level must be between 1 and 5"


def test_p5_unavailability_list_add_remove(client, login):
    fay = login("fay")
    listed = client.get(f"{API}/crew/11/unavailability", headers=fay).json()
    assert listed == [
        {"id": 1, "start_date": "2027-03-05", "end_date": "2027-03-08", "reason": "Medical"}
    ]
    added = client.post(
        f"{API}/crew/11/unavailability",
        headers=fay,
        json={"start_date": "2027-08-01", "end_date": "2027-08-03", "reason": "Leave"},
    )
    assert added.status_code == 201
    new_id = added.json()["id"]
    assert added.json() == {
        "id": new_id,
        "start_date": "2027-08-01",
        "end_date": "2027-08-03",
        "reason": "Leave",
    }
    assert client.delete(f"{API}/crew/11/unavailability/{new_id}", headers=fay).status_code == 204
    assert len(client.get(f"{API}/crew/11/unavailability", headers=fay).json()) == 1


def test_ac16_unavailability_overlapping_an_accepted_assignment_is_409(client, login):
    response = client.post(
        f"{API}/crew/12/unavailability",
        headers=login("gus"),
        json={"start_date": "2027-03-02", "end_date": "2027-03-04", "reason": "Dentist"},
    )
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert [p["code"] for p in error["problems"]] == ["overlap"]
    assert "Station Reboost" in error["problems"][0]["message"]


def test_v2_crew_assignment_history(client, login):
    history = client.get(f"{API}/crew/8/assignments", headers=login("chen")).json()
    assert [(h["mission_name"], h["status"]) for h in history] == [
        ("Orbital Telescope Service", "accepted"),
        ("Mars Analog Habitat", "completed"),
    ]
    assert set(history[0]) == {
        "assignment_id",
        "mission_id",
        "mission_name",
        "start_date",
        "end_date",
        "mission_status",
        "slot_name",
        "status",
        "reason",
    }


# --- Missions -----------------------------------------------------------------------------


NEW_MISSION = {
    "name": "Polar Relay",
    "start_date": "2027-06-01",
    "end_date": "2027-06-05",
    "slots": [
        {"name": "Pilot", "headcount": 1, "requirements": [{"skill_id": 1, "min_level": 3}]},
        {
            "name": "Engineer",
            "headcount": 2,
            "requirements": [{"skill_id": 3, "min_level": 2}, {"skill_id": 4, "min_level": 1}],
        },
    ],
}


def test_m1_lead_creates_a_mission_for_themselves(client, login):
    response = client.post(f"{API}/missions", headers=login("lee"), json=NEW_MISSION)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Polar Relay" and body["status"] == "draft"
    assert (body["owner_id"], body["owner_name"]) == (4, "Lee Park")
    assert (body["created_by_id"], body["created_by_name"]) == (4, "Lee Park")
    assert [
        (s["name"], s["position"], s["headcount"], s["open_places"]) for s in body["slots"]
    ] == [
        ("Pilot", 1, 1, 1),
        ("Engineer", 2, 2, 2),
    ]
    assert body["slots"][1]["requirements"] == [
        {"skill_id": 3, "skill_name": "Systems Engineering", "min_level": 2},
        {"skill_id": 4, "skill_name": "EVA", "min_level": 1},
    ]
    assert body["assignments"] == [] and body["approvals"] == []


def test_m1_director_creates_for_a_named_lead(client, login):
    response = client.post(
        f"{API}/missions", headers=login("ruth"), json={**NEW_MISSION, "owner_id": 5}
    )
    assert response.status_code == 201
    assert (response.json()["owner_id"], response.json()["created_by_id"]) == (5, 1)


def test_m1_director_must_name_the_owner(client, login):
    response = client.post(f"{API}/missions", headers=login("ruth"), json=NEW_MISSION)
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Name the Lead who will own the mission"


def test_m2_a_skill_listed_twice_in_one_slot_is_422(client, login):
    slot = {
        "name": "Pilot",
        "headcount": 1,
        "requirements": [{"skill_id": 1, "min_level": 3}, {"skill_id": 1, "min_level": 4}],
    }
    response = client.post(
        f"{API}/missions", headers=login("lee"), json={**NEW_MISSION, "slots": [slot]}
    )
    assert response.status_code == 422
    assert response.json()["error"]["problems"][0]["message"] == (
        "slots[0].requirements lists skill 1 more than once"
    )


def test_missions_list_shows_visible_missions(client, login):
    missions = client.get(f"{API}/missions", headers=login("lee")).json()
    assert [m["id"] for m in missions] == [7, 5, 3, 1, 2, 4, 6]  # by start date
    assert set(missions[0]) == {
        "id",
        "name",
        "start_date",
        "end_date",
        "status",
        "owner_id",
        "created_by_id",
        "approval_round",
        "approvals_required",
    }


def test_mission_show_includes_roster_and_current_approvals(client, login):
    comms = client.get(f"{API}/missions/6", headers=login("nora")).json()
    assert comms["status"] == "pending_approval"
    assert (comms["approval_round"], comms["approvals_required"]) == (1, 2)
    assert comms["assignments"] == [
        {
            "id": 7,
            "slot_id": 10,
            "slot_name": "Engineer",
            "crew_profile_id": 7,
            "crew_name": "Ben",
            "status": "accepted",
            "reason": None,
        }
    ]
    assert comms["approvals"] == [
        {"director_id": 2, "director_name": "Marco Bianchi", "decision": "approve", "reason": None}
    ]
    assert comms["slots"][0]["open_places"] == 0


def test_m3_edit_mission_name_and_dates(client, login):
    response = client.patch(
        f"{API}/missions/1",
        headers=login("lee"),
        json={"name": "Gateway Resupply", "end_date": "2027-03-11"},
    )
    assert response.status_code == 200
    assert (response.json()["name"], response.json()["end_date"]) == (
        "Gateway Resupply",
        "2027-03-11",
    )


def test_ac4_editing_dates_of_a_pending_mission_returns_it_to_draft(client, login):
    response = client.patch(
        f"{API}/missions/6", headers=login("nora"), json={"end_date": "2027-04-21"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert response.json()["approvals"] == []


def test_slots_add_edit_requirements_remove(client, login):
    lee = login("lee")
    added = client.post(
        f"{API}/missions/1/slots",
        headers=lee,
        json={
            "name": "Geologist",
            "headcount": 1,
            "requirements": [{"skill_id": 5, "min_level": 2}],
        },
    )
    assert added.status_code == 201
    slot = next(s for s in added.json()["slots"] if s["name"] == "Geologist")
    assert slot["position"] == 4

    renamed = client.patch(
        f"{API}/missions/1/slots/{slot['id']}",
        headers=lee,
        json={"name": "Field Geologist", "headcount": 2},
    )
    assert renamed.status_code == 200
    edited = next(s for s in renamed.json()["slots"] if s["id"] == slot["id"])
    assert (edited["name"], edited["headcount"]) == ("Field Geologist", 2)

    required = client.patch(
        f"{API}/missions/1/slots/{slot['id']}",
        headers=lee,
        json={"requirements": [{"skill_id": 5, "min_level": 3}, {"skill_id": 4, "min_level": 1}]},
    )
    assert required.status_code == 200
    edited = next(s for s in required.json()["slots"] if s["id"] == slot["id"])
    assert [(r["skill_name"], r["min_level"]) for r in edited["requirements"]] == [
        ("EVA", 1),
        ("Geology", 3),
    ]

    removed = client.delete(f"{API}/missions/1/slots/{slot['id']}", headers=lee)
    assert removed.status_code == 200
    assert slot["id"] not in [s["id"] for s in removed.json()["slots"]]


def test_slot_patch_refuses_requirements_with_name_or_headcount(client, login, snap):
    lee = login("lee")
    before = snap()
    response = client.patch(
        f"{API}/missions/1/slots/1",
        headers=lee,
        json={"name": "Engineer", "requirements": [{"skill_id": 3, "min_level": 3}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["message"] == (
        "Change a slot's required skills separately from its name and headcount"
    )
    assert snap() == before


def test_m2_removing_the_only_slot_is_409(client, login):
    response = client.delete(f"{API}/missions/3/slots/6", headers=login("nora"))
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert [p["code"] for p in error["problems"]] == ["mission_needs_a_slot"]


def test_m7_removing_a_slot_with_open_assignments_names_the_crew(client, login):
    lee = login("lee")
    client.post(
        f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 3, "crew_profile_id": 6}
    )
    response = client.delete(f"{API}/missions/1/slots/3", headers=lee)
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "rule_violation"
    assert error["message"] == (
        "Can't remove Commander from Lunar Gateway Resupply while Ana is assigned to it. "
        "Remove them from the mission first."
    )
    assert [p["code"] for p in error["problems"]] == ["slot_has_open_assignments"]


def test_m1_transfer_ownership(client, login):
    response = client.post(f"{API}/missions/1/owner", headers=login("ruth"), json={"owner_id": 5})
    assert response.status_code == 200
    assert (response.json()["owner_id"], response.json()["owner_name"]) == (5, "Nora Quinn")


def test_m1_transfer_to_a_non_lead_is_409(client, login):
    response = client.post(f"{API}/missions/1/owner", headers=login("ruth"), json={"owner_id": 7})
    assert response.status_code == 409
    assert response.json()["error"]["problems"][0]["code"] == "owner_not_active_lead"


# --- Matching -----------------------------------------------------------------------------


def test_ac18_s2_match_preview_over_http(client, login, snap):
    lee = login("lee")
    before = snap()
    response = client.get(f"{API}/missions/1/match", headers=lee)
    assert response.status_code == 200
    assert response.json() == {
        "mission": {
            "id": 1,
            "name": "Lunar Gateway Resupply",
            "start_date": "2027-03-01",
            "end_date": "2027-03-10",
        },
        "can_apply": True,
        "open_places": 3,
        "unfilled_places": 0,
        "slots": [
            {
                "slot_id": 1,
                "name": "Flight Engineer",
                "open_places": 1,
                "unfilled": 0,
                "suggested": [
                    {
                        "crew_profile_id": 8,
                        "name": "Chen",
                        "workload": 5,
                        "proficiency": 3,
                        "pick": 2,
                    }
                ],
            },
            {
                "slot_id": 2,
                "name": "Mission Specialist",
                "open_places": 1,
                "unfilled": 0,
                "suggested": [
                    {
                        "crew_profile_id": 9,
                        "name": "Dana",
                        "workload": 5,
                        "proficiency": 4,
                        "pick": 3,
                    }
                ],
            },
            {
                "slot_id": 3,
                "name": "Commander",
                "open_places": 1,
                "unfilled": 0,
                "suggested": [
                    {
                        "crew_profile_id": 6,
                        "name": "Ana",
                        "workload": 0,
                        "proficiency": 9,
                        "pick": 1,
                    }
                ],
            },
        ],
    }
    assert snap() == before  # AC-22: a preview changes nothing


def test_ac19_s3_unfilled_geologist(client, login):
    body = client.get(f"{API}/missions/2/match", headers=login("nora")).json()
    assert (body["open_places"], body["unfilled_places"]) == (2, 1)
    geologist = body["slots"][1]
    assert (geologist["name"], geologist["unfilled"], geologist["suggested"]) == (
        "Geologist",
        1,
        [],
    )


def test_match_preview_for_a_director_cannot_apply(client, login):
    assert client.get(f"{API}/missions/1/match", headers=login("ruth")).json()["can_apply"] is False


# --- Assignments --------------------------------------------------------------------------


def test_s1_propose_returns_the_assignment(client, login):
    response = client.post(
        f"{API}/missions/1/assignments",
        headers=login("lee"),
        json={"slot_id": 3, "crew_profile_id": 6},
    )
    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "mission_id": 1,
        "slot_id": 3,
        "crew_profile_id": 6,
        "status": "proposed",
        "reason": None,
    }


def test_my_assignments_and_the_pending_filter(client, login):
    lee = login("lee")
    client.post(
        f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 1, "crew_profile_id": 8}
    )
    chen = login("chen")
    mine = client.get(f"{API}/assignments", headers=chen).json()
    assert [(a["mission_name"], a["status"]) for a in mine] == [
        ("Lunar Gateway Resupply", "proposed"),
        ("Orbital Telescope Service", "accepted"),
        ("Mars Analog Habitat", "completed"),
    ]
    pending = client.get(f"{API}/assignments", headers=chen, params={"pending": "true"}).json()
    assert [a["mission_name"] for a in pending] == ["Lunar Gateway Resupply"]


def test_my_assignments_without_a_crew_profile_is_empty(client, login):
    assert client.get(f"{API}/assignments", headers=login("lee")).json() == []


def test_accept_decline_remove(client, login):
    lee = login("lee")

    def propose(slot, crew):
        r = client.post(
            f"{API}/missions/1/assignments",
            headers=lee,
            json={"slot_id": slot, "crew_profile_id": crew},
        )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    chen, dana = propose(1, 8), propose(2, 9)
    accepted = client.post(f"{API}/assignments/{chen}/accept", headers=login("chen"))
    assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"

    declined = client.post(
        f"{API}/assignments/{dana}/decline", headers=login("dana"), json={"reason": "Busy"}
    )
    assert declined.status_code == 200
    assert (declined.json()["status"], declined.json()["reason"]) == ("declined", "Busy")

    removed = client.post(f"{API}/assignments/{chen}/remove", headers=lee)
    assert removed.status_code == 200 and removed.json()["status"] == "removed"


def test_decline_body_is_optional(client, login):
    lee = login("lee")
    made = client.post(
        f"{API}/missions/1/assignments", headers=lee, json={"slot_id": 2, "crew_profile_id": 9}
    ).json()
    declined = client.post(f"{API}/assignments/{made['id']}/decline", headers=login("dana"))
    assert declined.status_code == 200 and declined.json()["reason"] is None


def test_s5_withdraw_needs_a_reason_then_returns_the_mission_to_draft(client, login, db):
    ben = login("ben")
    refused = client.post(f"{API}/assignments/7/withdraw", headers=ben)
    assert refused.status_code == 422
    assert refused.json()["error"]["message"] == (
        "Withdrawing from Deep Space Comms Upgrade needs a reason"
    )
    blank = client.post(f"{API}/assignments/7/withdraw", headers=ben, json={"reason": " "})
    assert blank.status_code == 422

    done = client.post(f"{API}/assignments/7/withdraw", headers=ben, json={"reason": "Family"})
    assert done.status_code == 200
    assert (done.json()["status"], done.json()["reason"]) == ("withdrawn", "Family")
    assert db.execute("SELECT status FROM missions WHERE id = 6").fetchone()[0] == "draft"


def test_s5_withdrawing_from_an_active_mission_is_409(client, login):
    hana = login("hana")
    response = client.post(f"{API}/assignments/6/withdraw", headers=hana, json={"reason": "Ill"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "mission_frozen"
