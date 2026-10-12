"""M16: the PRD scenarios S1 (golden path) and S4 (overlaps) driven through `mc`, one user after
another, against a small stateful stand-in for the API (PRD §9.3, AC-1, AC-3, AC-8, AC-14, AC-15).

The stand-in only keeps the state these flows touch, and answers with the design's response and
error shapes. Business rules are the server's; here they're scripted to the PRD's expected
outcomes, so the tests check what the CLI sends and how it reports each step.
"""

import json
from dataclasses import dataclass, field

import httpx2
from cli_fakes import CREW, SKILLS, USERS, FakeApi, error, gateway, ok, problem

PEOPLE = {
    "ruth@aurora.example": (1, "Ruth Adeyemi", "director", None),
    "marco@aurora.example": (2, "Marco Bianchi", "director", 2),
    "ingrid@aurora.example": (3, "Ingrid Holm", "director", None),
    "lee@aurora.example": (4, "Lee Park", "lead", None),
    "nora@aurora.example": (5, "Nora Quinn", "lead", None),
    "ana@aurora.example": (6, "Ana Okafor", "lead", 6),
    "chen@aurora.example": (8, "Chen Wu", "crew", 8),
    "dana@aurora.example": (9, "Dana Reyes", "crew", 9),
}
SLOT_NAMES = {1: "Flight Engineer", 2: "Mission Specialist", 3: "Commander"}


@dataclass
class Server:
    """Just enough of the API for S1 and S4."""

    api: FakeApi
    tokens: dict[str, str] = field(default_factory=dict)
    status: str = "draft"
    assignments: dict[int, dict] = field(default_factory=dict)
    approvals: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    accepted_reboost: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        on = self.api.on
        on("POST", "/auth/login", self.login)
        on("GET", "/me", self.authed(self.me))
        on("GET", "/skills", self.authed(lambda r, u: ok(SKILLS)))
        on("GET", "/crew", self.authed(lambda r, u: ok(CREW)))
        on("GET", "/users", self.authed(lambda r, u: ok(USERS)))
        on("GET", "/missions/1", self.authed(lambda r, u: ok(self.mission())))
        on("GET", "/missions/1/match", self.authed(self.match))
        on("POST", "/missions/1/match/apply", self.authed(self.apply))
        on("GET", "/assignments", self.authed(self.mine))
        for aid in (21, 22, 23):
            on("POST", f"/assignments/{aid}/accept", self.authed(self.accept(aid)))
        on("POST", "/missions/1/submit", self.authed(self.submit))
        on("POST", "/missions/1/approve", self.authed(self.approve))
        on("POST", "/missions/1/complete", self.authed(self.complete))
        on("GET", "/missions/1/history", self.authed(lambda r, u: ok(self.history)))

    # plumbing

    def authed(self, handler):
        def wrapped(request: httpx2.Request) -> httpx2.Response:
            auth = request.headers.get("authorization", "")
            email = self.tokens.get(auth.removeprefix("Bearer "))
            if email is None:
                return error(401, "unauthenticated", "Your session has ended")
            return handler(request, PEOPLE[email])

        return wrapped

    def login(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        if body["email"] not in PEOPLE or body["password"] != "orbital launch window":
            return error(401, "invalid_credentials", "Email or password is incorrect")
        token = f"tok-{body['email'].split('@')[0]}"
        self.tokens[token] = body["email"]
        return ok({"token": token, "expires_at": "2099-01-01T00:00:00Z"})

    def me(self, request, user) -> httpx2.Response:
        uid, name, role, cpid = user
        email = next(e for e, p in PEOPLE.items() if p == user)
        return ok({"id": uid, "email": email, "name": name, "role": role, "active": True,
                   "crew_profile_id": cpid,
                   "organisation": {"id": 1, "name": "Aurora Space Agency"}})  # fmt: skip

    def log(self, user, event, from_status=None, to_status=None) -> None:
        self.history.append(
            {"id": len(self.history) + 1,
             "created_at": f"2027-01-05T09:{len(self.history):02d}:00Z",
             "actor_id": user[0], "actor_name": user[1], "event": event,
             "from_status": from_status, "to_status": to_status, "reason": None, "data": {}}
        )  # fmt: skip

    def mission(self) -> dict:
        open_places = {
            slot: 1 - sum(1 for a in self.assignments.values()
                          if a["slot_id"] == slot and a["status"] in ("proposed", "accepted"))
            for slot in SLOT_NAMES
        }  # fmt: skip
        m = gateway(self.status, list(self.assignments.values()), self.approvals, open_places)
        m["approvals_required"] = None if self.status == "draft" else 2
        return m

    # endpoints

    def match(self, request, user) -> httpx2.Response:
        from cli_fakes import S2_PREVIEW

        return ok(S2_PREVIEW | {"can_apply": user[0] == 4})

    def apply(self, request, user) -> httpx2.Response:
        for aid, slot, cpid, name in ((21, 3, 6, "Ana Okafor"), (22, 1, 8, "Chen Wu"),
                                      (23, 2, 9, "Dana Reyes")):  # fmt: skip
            self.assignments[aid] = {"id": aid, "slot_id": slot, "slot_name": SLOT_NAMES[slot],
                                     "crew_profile_id": cpid, "crew_name": name,
                                     "status": "proposed", "reason": None}  # fmt: skip
            self.log(user, "assignment.proposed")
        return ok(
            [{k: a[k] for k in ("id", "slot_id", "crew_profile_id", "status")}
             for a in self.assignments.values()],
            status=201,
        )  # fmt: skip

    def mine(self, request, user) -> httpx2.Response:
        rows = [
            {"assignment_id": a["id"], "mission_id": 1, "mission_name": "Lunar Gateway Resupply",
             "start_date": "2027-03-01", "end_date": "2027-03-10", "mission_status": self.status,
             "slot_name": a["slot_name"], "status": a["status"], "reason": None}
            for a in self.assignments.values() if a["crew_profile_id"] == user[3]
        ]  # fmt: skip
        if request.url.params.get("pending") == "true":
            rows = [r for r in rows if r["status"] == "proposed"]
        return ok(rows)

    def accept(self, aid):
        def handler(request, user) -> httpx2.Response:
            a = self.assignments.get(aid)
            if a is None or a["crew_profile_id"] != user[3]:
                return error(404, "not_found", "Assignment not found")
            a["status"] = "accepted"
            self.log(user, "assignment.accepted", "proposed", "accepted")
            return ok({"id": aid, "mission_id": 1, "slot_id": a["slot_id"],
                       "crew_profile_id": a["crew_profile_id"], "status": "accepted",
                       "reason": None})  # fmt: skip

        return handler

    def submit(self, request, user) -> httpx2.Response:
        waiting = [a for a in self.assignments.values() if a["status"] != "accepted"]
        if waiting:
            return error(409, "rule_violation", "Mission can't be submitted", [
                problem("proposal_unanswered",
                        f"{a['slot_name']}: {a['crew_name']} hasn't responded to the proposal",
                        assignment_id=a["id"]) for a in waiting
            ])  # fmt: skip
        self.status = "pending_approval"
        self.log(user, "mission.submitted", "draft", "pending_approval")
        return ok(self.mission())

    def approve(self, request, user) -> httpx2.Response:
        if user[0] == 1:
            return error(403, "approver_is_creator", "You can't approve a mission you created")
        self.approvals.append({"director_id": user[0], "director_name": user[1],
                               "decision": "approve", "reason": None})  # fmt: skip
        self.log(user, "mission.approved")
        if len(self.approvals) == 2:
            self.status = "active"
            self.log(user, "mission.activated", "pending_approval", "active")
        return ok(self.mission())

    def complete(self, request, user) -> httpx2.Response:
        self.status = "completed"
        for a in self.assignments.values():
            a["status"] = "completed"
        self.log(user, "mission.completed", "active", "completed")
        return ok(self.mission())


def _login(mc, email):
    result = mc("login", "--email", email, input="orbital launch window\n")
    assert result.exit_code == 0, result.stderr
    return result


def test_s1_golden_path_through_the_cli(mc, api):
    server = Server(api)

    _login(mc, "lee@aurora.example")
    preview = mc("missions", "match", "1")
    assert preview.exit_code == 0
    assert "Commander            Ana" in preview.stdout
    applied = mc("missions", "match", "1", "--apply")
    assert applied.exit_code == 0, applied.stderr
    assert "Proposed 3 crew for Lunar Gateway Resupply" in applied.stdout

    early = mc("missions", "submit", "1")
    assert early.exit_code == 1  # AC-2: proposals still unanswered
    assert "  • Commander: Ana Okafor hasn't responded to the proposal\n" in early.stderr

    for email, aid in (("ana", 21), ("chen", 22), ("dana", 23)):
        _login(mc, f"{email}@aurora.example")
        pending = mc("assignments", "list", "--pending", "--json")
        assert [row["assignment_id"] for row in json.loads(pending.stdout)] == [aid]
        accepted = mc("assignments", "accept", str(aid))
        assert accepted.exit_code == 0, accepted.stderr
        assert accepted.stdout.startswith("✓ Accepted ")

    _login(mc, "lee@aurora.example")
    submitted = mc("missions", "submit", "1")
    assert submitted.stdout == (
        "✓ Submitted Lunar Gateway Resupply for approval. It needs 2 approvals.\n"
    )

    _login(mc, "ruth@aurora.example")
    ruth = mc("missions", "approve", "1")
    assert ruth.exit_code == 1  # AC-8: the creator can't approve
    assert ruth.stderr == "✗ You can't approve a mission you created.\n"

    _login(mc, "marco@aurora.example")
    marco = mc("missions", "approve", "1")
    assert marco.stdout == (
        "✓ Approved Lunar Gateway Resupply. It's pending approval (1 of 2 approvals).\n"
    )

    _login(mc, "ingrid@aurora.example")
    ingrid = mc("missions", "approve", "1")
    assert ingrid.stdout == "✓ Approved Lunar Gateway Resupply. It's now active.\n"

    _login(mc, "lee@aurora.example")
    completed = mc("missions", "complete", "1")
    assert completed.exit_code == 0

    shown = json.loads(mc("missions", "show", "1", "--json").stdout)
    assert shown["status"] == "completed"
    assert {a["status"] for a in shown["assignments"]} == {"completed"}

    history = mc("missions", "history", "1").stdout.splitlines()  # AC-1: who did what, when
    for who, what in (
        ("Lee Park", "Submitted for approval"),
        ("Marco Bianchi", "Approved"),
        ("Ingrid Holm", "Mission became active"),
        ("Lee Park", "Completed"),
    ):
        assert any(who in line and what in line and "Jan 2027" in line for line in history)
    assert server.status == "completed"


def test_s4_overlaps_and_unavailability_through_the_cli(mc, api):
    tokens = {"tok-lee": "lee", "tok-nora": "nora", "tok-chen": "chen"}
    proposals: list[tuple[str, dict]] = []

    def who(request):
        return tokens[request.headers["authorization"].removeprefix("Bearer ")]

    reboost = gateway() | {
        "id": 3,
        "name": "Station Reboost",
        "start_date": "2027-02-25",
        "end_date": "2027-03-02",
        "owner_id": 5,
        "owner_name": "Nora Quinn",
    }
    reboost["slots"] = [{"id": 6, "position": 1, "name": "Engineer", "headcount": 2,
                         "open_places": 1, "requirements": []}]  # fmt: skip
    api.on("GET", "/skills", ok(SKILLS))
    api.on("GET", "/crew", ok(CREW))
    api.on("GET", "/missions/1", ok(gateway()))
    api.on("GET", "/missions/3", ok(reboost))

    def propose_gateway(request):
        body = json.loads(request.content)
        if body["crew_profile_id"] == 12:
            return error(409, "rule_violation", "Can't propose Gus Patel for Flight Engineer", [
                problem("overlap", "Gus Patel has an accepted assignment on Station Reboost "
                        "overlapping 1–2 Mar", crew_profile_id=12, mission_id=3,
                        mission_name="Station Reboost")])  # fmt: skip
        if body["crew_profile_id"] == 11:
            return error(409, "rule_violation", "Can't propose Fay Moreau for Commander", [
                problem("unavailable", "Fay Moreau is unavailable 5–8 Mar",
                        crew_profile_id=11, slot_id=3)])  # fmt: skip
        proposals.append((who(request), body))
        return ok({"id": 25, "mission_id": 1, "slot_id": 1, "crew_profile_id": 8,
                   "status": "proposed", "reason": None}, status=201)  # fmt: skip

    def propose_reboost(request):
        proposals.append((who(request), json.loads(request.content)))
        return ok({"id": 24, "mission_id": 3, "slot_id": 6, "crew_profile_id": 8,
                   "status": "proposed", "reason": None}, status=201)  # fmt: skip

    api.on("POST", "/missions/1/assignments", propose_gateway)
    api.on("POST", "/missions/3/assignments", propose_reboost)
    api.on("GET", "/assignments", ok([]))
    api.on("POST", "/assignments/24/accept", ok({"id": 24, "status": "accepted"}))
    api.on(
        "POST",
        "/assignments/25/accept",
        error(409, "overlap", "You have an accepted assignment on Station Reboost overlapping "
              "1–2 Mar"),
    )  # fmt: skip

    mc.login_as("tok-lee")
    gus = mc(
        "missions", "propose", "1", "--slot", "Flight Engineer", "--crew", "gus@aurora.example"
    )
    fay = mc("missions", "propose", "1", "--slot", "Commander", "--crew", "fay@aurora.example")

    assert gus.exit_code == fay.exit_code == 1  # AC-14
    assert gus.stderr == (
        "✗ Can't propose Gus Patel for Flight Engineer.\n"
        "  • Gus Patel has an accepted assignment on Station Reboost overlapping 1–2 Mar\n"
        "  See who is free: mc missions match 1\n"
    )
    assert "  • Fay Moreau is unavailable 5–8 Mar\n" in fay.stderr

    mc.login_as("tok-nora", "nora@aurora.example")
    assert mc("missions", "propose", "3", "--slot", "Engineer", "--crew",
              "chen@aurora.example").exit_code == 0  # fmt: skip
    mc.login_as("tok-lee")
    assert mc("missions", "propose", "1", "--slot", "1", "--crew",
              "chen@aurora.example").exit_code == 0  # fmt: skip
    assert proposals == [
        ("nora", {"slot_id": 6, "crew_profile_id": 8}),
        ("lee", {"slot_id": 1, "crew_profile_id": 8}),
    ]

    mc.login_as("tok-chen", "chen@aurora.example")
    first = mc("assignments", "accept", "24")
    second = mc("assignments", "accept", "25")

    assert first.exit_code == 0
    assert second.exit_code == 1  # AC-15: names the conflicting mission
    assert second.stderr.startswith(
        "✗ You have an accepted assignment on Station Reboost overlapping 1–2 Mar.\n"
    )
