"""M15: tenant isolation sweep over HTTP (S9; PRD T1, T2, AC-27 to AC-29, AC-31; design §4
Tenant isolation, TR-10).

Each role in each organisation calls every endpoint with the other organisation's ids:
- the response is identical to the one for an id that doesn't exist;
- it is 404, except where the caller's role is refused before anything is looked up, in which
  case the foreign and missing ids both get the same 403;
- nothing in either organisation changes.
Every list holds only the caller's organisation's records.

A route inventory makes any new endpoint fail here until it's added to the sweep.

Seed ids. Aurora (org 1): users 1–13, skills 1–6, missions 1–7, Gateway 1 (Lee) with slots 1–3,
Hana 13, Fay's unavailability 1, Gus's Reboost assignment 1. Helix (org 2): users 14–19, skills
7–10, Payload Demo 8 (Priya) with slots 12–13, Priya 15 (no crew profile), Kai 16, Tess 19,
Lena's Payload assignment 9. Kai gets an unavailability (id 2) in the fixture below.
"""

import re

import pytest

API = "/api/v1"
MISSING = 999_999


class Ids:
    """One organisation's records the sweep points at."""

    def __init__(self, **ids):
        self.__dict__.update(ids)


AURORA = Ids(
    org=1,
    user=7,  # Ben
    no_profile_user=4,  # Lee
    crew=7,  # Ben
    other_crew=13,  # Hana: someone a Director or Lead may rate
    skill=1,
    mission=1,  # Gateway, owned by the Lead below
    slot=1,
    lead=4,  # Lee
    assignment=1,
    unavailability=1,
    users=set(range(1, 14)),
    skills=set(range(1, 7)),
    missions=set(range(1, 8)),
)
HELIX = Ids(
    org=2,
    user=16,  # Kai
    no_profile_user=15,  # Priya
    crew=16,  # Kai
    other_crew=19,  # Tess
    skill=7,
    mission=8,  # Payload Demo, owned by Priya
    slot=12,
    lead=15,  # Priya
    assignment=9,
    unavailability=2,
    users=set(range(14, 20)),
    skills=set(range(7, 11)),
    missions={8},
)

# (first name, org, role letter, own crew profile id or None)
CALLERS = [
    ("ruth", "aurora", "D", None),
    ("lee", "aurora", "L", None),
    ("ben", "aurora", "C", 7),
    ("sam", "helix", "D", None),
    ("priya", "helix", "L", None),
    ("kai", "helix", "C", 16),
]


def _slot(skill):
    return {"name": "Probe", "headcount": 1, "requirements": [{"skill_id": skill, "min_level": 1}]}


def _mission(skill, owner=None):
    body = {
        "name": "Probe",
        "start_date": "2027-09-01",
        "end_date": "2027-09-02",
        "slots": [_slot(skill)],
    }
    if owner is not None:
        body["owner_id"] = owner
    return body


# Each variant: (method, path, body, roles answered 403 before any lookup). `o` is the other
# organisation's ids, `me` the caller's, and `x(...)` swaps in the other organisation's id or a
# missing one. Every other role must get 404.
def variants(me, o, own_crew, x):
    v = [
        ("PATCH", f"/users/{x(o.user)}", {"role": "lead"}, "LC"),
        ("POST", f"/users/{x(o.no_profile_user)}/crew-profile", {}, "LC"),
        ("PATCH", f"/skills/{x(o.skill)}", {"name": "Renamed"}, "LC"),
        ("DELETE", f"/skills/{x(o.skill)}", None, "LC"),
        ("GET", f"/crew/{x(o.crew)}", None, ""),
        ("PATCH", f"/crew/{x(o.crew)}", {"bio": "Hi"}, ""),
        ("PUT", f"/crew/{x(o.crew)}/skills/{me.skill}", {"level": 3}, ""),
        ("PUT", f"/crew/{me.other_crew}/skills/{x(o.skill)}", {"level": 3}, ""),
        ("DELETE", f"/crew/{x(o.crew)}/skills/{me.skill}", None, ""),
        ("DELETE", f"/crew/{me.other_crew}/skills/{x(o.skill)}", None, ""),
        ("GET", f"/crew/{x(o.crew)}/unavailability", None, ""),
        (
            "POST",
            f"/crew/{x(o.crew)}/unavailability",
            {"start_date": "2027-09-01", "end_date": "2027-09-02", "reason": "x"},
            "",
        ),
        ("DELETE", f"/crew/{x(o.crew)}/unavailability/{x(o.unavailability)}", None, ""),
        ("GET", f"/crew/{x(o.crew)}/assignments", None, ""),
        ("POST", "/missions", _mission(x(o.skill), me.lead), "C"),
        ("POST", "/missions", _mission(x(o.skill)), "C"),
        ("POST", "/missions", _mission(me.skill, x(o.lead)), "LC"),  # a Lead names only themselves
        ("GET", f"/missions/{x(o.mission)}", None, ""),
        ("PATCH", f"/missions/{x(o.mission)}", {"name": "Renamed"}, ""),
        ("POST", f"/missions/{x(o.mission)}/slots", _slot(me.skill), ""),
        ("POST", f"/missions/{me.mission}/slots", _slot(x(o.skill)), "D"),
        ("PATCH", f"/missions/{x(o.mission)}/slots/{x(o.slot)}", {"headcount": 2}, ""),
        ("PATCH", f"/missions/{me.mission}/slots/{x(o.slot)}", {"headcount": 2}, ""),
        ("DELETE", f"/missions/{x(o.mission)}/slots/{x(o.slot)}", None, ""),
        ("DELETE", f"/missions/{me.mission}/slots/{x(o.slot)}", None, ""),
        ("POST", f"/missions/{x(o.mission)}/owner", {"owner_id": me.lead}, ""),
        ("POST", f"/missions/{me.mission}/owner", {"owner_id": x(o.lead)}, "L"),
        ("GET", f"/missions/{x(o.mission)}/match", None, ""),
        (
            "POST",
            f"/missions/{x(o.mission)}/assignments",
            {"slot_id": x(o.slot), "crew_profile_id": x(o.crew)},
            "",
        ),
        (
            "POST",
            f"/missions/{me.mission}/assignments",
            {"slot_id": me.slot, "crew_profile_id": x(o.crew)},
            "D",
        ),
        (
            "POST",
            f"/missions/{me.mission}/assignments",
            {"slot_id": x(o.slot), "crew_profile_id": me.other_crew},
            "",
        ),
        ("POST", f"/assignments/{x(o.assignment)}/accept", None, ""),
        ("POST", f"/assignments/{x(o.assignment)}/decline", {"reason": "x"}, ""),
        ("POST", f"/assignments/{x(o.assignment)}/withdraw", {"reason": "x"}, ""),
        ("POST", f"/assignments/{x(o.assignment)}/remove", None, ""),
        ("POST", f"/missions/{x(o.mission)}/match/apply", None, ""),
        ("POST", f"/missions/{x(o.mission)}/submit", None, ""),
        ("POST", f"/missions/{x(o.mission)}/approve", None, ""),
        ("POST", f"/missions/{x(o.mission)}/reject", {"reason": "x"}, ""),
        ("POST", f"/missions/{x(o.mission)}/complete", None, ""),
        ("POST", f"/missions/{x(o.mission)}/cancel", {"reason": "x"}, ""),
        ("GET", f"/missions/{x(o.mission)}/history", None, ""),
    ]
    if own_crew is not None:
        v.append(("DELETE", f"/crew/{own_crew}/unavailability/{x(o.unavailability)}", None, ""))
    return v


# Endpoints that take no id at all, so there is nothing foreign to name. Lists are checked below.
NO_ID = {
    ("GET", "/health"),
    ("POST", f"{API}/auth/login"),
    ("POST", f"{API}/auth/logout"),
    ("GET", f"{API}/me"),
    ("GET", f"{API}/me/inbox"),  # only ever the caller's own items
    ("POST", f"{API}/me/password"),
    ("PATCH", f"{API}/org"),  # changes only the caller's own organisation
    ("POST", f"{API}/users"),  # creates in the caller's own organisation
    ("POST", f"{API}/skills"),  # likewise
}
LISTS = {
    ("GET", f"{API}/org"),
    ("GET", f"{API}/users"),
    ("GET", f"{API}/skills"),
    ("GET", f"{API}/crew"),
    ("GET", f"{API}/missions"),
    ("GET", f"{API}/assignments"),
}


def _template(path: str) -> str:
    """'/missions/8/slots/12' -> '/missions/{}/slots/{}', to match against the app's routes."""
    return "/".join("{}" if part.isdigit() else part for part in path.split("/"))


def _route_templates(app) -> set[tuple[str, str]]:
    """Every endpoint the app serves, from its OpenAPI schema (which lists included routers'
    routes; none of ours are hidden from it)."""
    return {
        (method.upper(), re.sub(r"\{[^}]+\}", "{}", path))
        for path, operations in app.openapi()["paths"].items()
        for method in operations
    }


@pytest.fixture
def kai_unavailable(db):
    """A Helix unavailability for Aurora callers to point at."""
    db.execute(
        "INSERT INTO unavailability(id, org_id, crew_profile_id, start_date, end_date, reason)"
        " VALUES (2, 2, 16, '2027-05-01', '2027-05-02', 'Training')"
    )


def test_s9_route_inventory_every_endpoint_is_in_the_sweep(client):
    swept = {
        (method, _template(f"{API}{path}"))
        for method, path, _, _ in variants(AURORA, HELIX, 7, lambda i: i)
    }
    covered = swept | {(m, _template(p)) for m, p in NO_ID | LISTS}
    assert _route_templates(client.app) == covered


@pytest.mark.parametrize(("who", "org", "role", "own_crew"), CALLERS, ids=[c[0] for c in CALLERS])
def test_s9_ac27_ac29_foreign_ids_look_missing_and_change_nothing(
    client, login, snap, kai_unavailable, who, org, role, own_crew
):
    me, other = (AURORA, HELIX) if org == "aurora" else (HELIX, AURORA)
    headers = login(who)
    foreign = variants(me, other, own_crew, lambda i: i)
    missing = variants(me, other, own_crew, lambda i: MISSING)
    before = snap()
    for (method, path, body, gated), (_, missing_path, missing_body, _) in zip(
        foreign, missing, strict=True
    ):
        response = client.request(method, f"{API}{path}", headers=headers, json=body)
        expected = client.request(
            method, f"{API}{missing_path}", headers=headers, json=missing_body
        )
        label = f"{who} {method} {path}"
        assert response.status_code == (403 if role in gated else 404), f"{label}: {response.text}"
        assert response.json() == expected.json(), label
        assert response.status_code == expected.status_code, label
        assert snap() == before, f"{label} changed the database"


@pytest.mark.parametrize(("who", "org", "role", "own_crew"), CALLERS, ids=[c[0] for c in CALLERS])
def test_s9_ac28_every_list_holds_only_the_callers_organisation(
    client, login, who, org, role, own_crew
):
    me = AURORA if org == "aurora" else HELIX
    headers = login(who)

    def get(path):
        return client.get(f"{API}{path}", headers=headers)

    org_view = get("/org")
    users = get("/users")
    skills = get("/skills")
    if role == "D":
        assert org_view.json()["id"] == me.org
        assert {u["id"] for u in users.json()} == me.users
    else:
        assert org_view.status_code == users.status_code == 403
    if role == "C":
        assert skills.status_code == 403
    else:
        assert {s["id"] for s in skills.json()} == me.skills

    crew = {c["crew_profile_id"] for c in get("/crew").json()}
    missions = {m["id"] for m in get("/missions").json()}
    assignments = {a["mission_id"] for a in get("/assignments").json()}
    assert crew and crew <= me.users
    assert missions <= me.missions
    assert assignments <= me.missions
    if role != "C":
        assert missions == me.missions


def test_ac31_s9_helix_kai_is_never_suggested_for_an_aurora_piloting_slot(client, login):
    """Kai has Piloting 5 (Helix's own skill) and no commitments."""
    for mission in (1, 2):  # Gateway's Commander and Asteroid's Pilot need Aurora Piloting
        body = client.get(f"{API}/missions/{mission}/match", headers=login("ruth")).json()
        names = [p["name"] for s in body["slots"] for p in s["suggested"]]
        ids = [p["crew_profile_id"] for s in body["slots"] for p in s["suggested"]]
        assert "Kai" not in names and 16 not in ids
        assert set(ids) <= AURORA.users
