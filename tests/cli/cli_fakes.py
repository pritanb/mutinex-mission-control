"""Test doubles for the CLI: a scripted API behind `httpx2.MockTransport`, and a runner that
invokes `mc` in-process with its config directory under `tmp_path`.

Responses are shaped like the design's HTTP contract: JSON bodies, and every error as
`{"error": {"code", "message", "problems": [...]}}`.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import api_contract
import httpx2
from typer.testing import CliRunner

from mission_control.cli.config import Credentials, CredentialStore
from mission_control.cli.env import Env
from mission_control.cli.main import app

BASE_URL = "http://mc.test"
PREFIX = "/api/v1"

Handler = Callable[[httpx2.Request], httpx2.Response]


def ok(body: Any = None, status: int = 200) -> httpx2.Response:
    if body is None and status == 204:
        return httpx2.Response(204)
    return httpx2.Response(status, json=body)


def problem(code: str, message: str, **refs: Any) -> dict[str, Any]:
    return {"code": code, "message": message, "refs": refs}


def error(
    status: int, code: str, message: str, problems: Sequence[Mapping[str, Any]] | None = None
) -> httpx2.Response:
    listed = list(problems) if problems else [problem(code, message)]
    return httpx2.Response(
        status, json={"error": {"code": code, "message": message, "problems": listed}}
    )


@dataclass
class Call:
    method: str
    path: str
    params: dict[str, str]
    body: Any
    token: str | None


@dataclass
class FakeApi:
    """Routes `(method, path)` to a fixed response or a handler. Unrouted calls fail the test
    loudly with a 599, so a missing route can't pass by accident.

    Every response it sends is checked against the real API's routes and response models, and
    any mismatch is kept in `drift`; the `api` fixture fails the test if there's any."""

    routes: dict[tuple[str, str], Handler | httpx2.Response] = field(default_factory=dict)
    calls: list[Call] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)

    def on(self, method: str, path: str, response: Handler | httpx2.Response) -> None:
        self.routes[(method.upper(), path)] = response

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        path = request.url.path.removeprefix(PREFIX)
        body = json.loads(request.content) if request.content else None
        auth = request.headers.get("authorization", "")
        token = auth.removeprefix("Bearer ") if auth.startswith("Bearer ") else None
        self.calls.append(Call(request.method, path, dict(request.url.params), body, token))
        route = self.routes.get((request.method, path))
        if route is None:
            return httpx2.Response(599, json={"unrouted": f"{request.method} {path}"})
        response = route(request) if callable(route) else route
        self.drift += api_contract.problems(request.method, path, response)
        return response

    def client(self) -> httpx2.Client:
        return httpx2.Client(transport=httpx2.MockTransport(self.handle), base_url=BASE_URL)

    def sent(self, method: str, path: str) -> list[Call]:
        return [c for c in self.calls if c.method == method and c.path == path]

    def writes(self) -> list[Call]:
        return [c for c in self.calls if c.method != "GET"]


@dataclass
class ScriptedPrompter:
    """Answers prompts from a list and records each one as (label, hidden). Running out of
    answers behaves like Ctrl+C."""

    answers: list[str]
    asked: list[tuple[str, bool]] = field(default_factory=list)

    def ask(self, label: str) -> str:
        self.asked.append((label, False))
        return self._next()

    def ask_hidden(self, label: str) -> str:
        self.asked.append((label, True))
        return self._next()

    def _next(self) -> str:
        if not self.answers:
            raise KeyboardInterrupt
        return self.answers.pop(0)


@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    exception: BaseException | None
    asked: list[tuple[str, bool]] = field(default_factory=list)


@dataclass
class Mc:
    """Runs `mc` in-process against a FakeApi, with credentials kept under a temp directory."""

    api: FakeApi
    config_dir: Path

    @property
    def store(self) -> CredentialStore:
        return CredentialStore(self.config_dir)

    def login_as(self, token: str = "tok-lee", email: str = "lee@aurora.example") -> None:
        self.store.save(Credentials(token=token, email=email, expires_at="2027-01-05T21:00:00Z"))

    def __call__(
        self,
        *args: str,
        input: str | None = None,
        answers: Sequence[str] | None = None,
        color: bool | None = False,
        http: httpx2.Client | None = None,
    ) -> Result:
        """`answers` makes the run interactive and answers its prompts in order. Without it
        there's no terminal, and `input` is what's piped to stdin."""
        prompter = ScriptedPrompter(list(answers or ()))
        env = Env(
            http=http or self.api.client(),
            config_dir=self.config_dir,
            interactive=answers is not None,
            color=color,
            prompter=prompter,
        )
        result = CliRunner().invoke(app, list(args), obj=env, input=input, prog_name="mc")
        return Result(
            result.exit_code, result.stdout, result.stderr, result.exception, prompter.asked
        )


# Seed-shaped records (PRD §9). A crew profile's id equals its user's id.

LEE_ME = {
    "id": 4,
    "email": "lee@aurora.example",
    "name": "Lee Park",
    "role": "lead",
    "active": True,
    "crew_profile_id": None,
    "organisation": {"id": 1, "name": "Aurora Space Agency", "slug": "aurora"},
}


def session(token: str, me: Mapping[str, Any], expires_at: str = "2027-01-05T21:00:00Z") -> dict:
    """A `POST /auth/login` body for the user `me` describes."""
    user = {k: me[k] for k in ("id", "email", "name", "role", "active")}
    return {"token": token, "expires_at": expires_at, "user": user}


SKILLS = [
    {"id": 1, "name": "Piloting", "category": None},
    {"id": 2, "name": "Leadership", "category": None},
    {"id": 3, "name": "Systems Engineering", "category": None},
    {"id": 4, "name": "EVA", "category": None},
    {"id": 5, "name": "Geology", "category": None},
]


def crew(cid: int, name: str, email: str, skills: Mapping[str, int] = (), **extra: Any) -> dict:
    ids = {s["name"]: s["id"] for s in SKILLS}
    record = {
        "crew_profile_id": cid,
        "user_id": cid,
        "name": name,
        "email": email,
        "active": True,
        "bio": None,
        "skills": [
            {"skill_id": ids[n], "skill_name": n, "level": lvl} for n, lvl in dict(skills).items()
        ],
        "unavailability": [],
    }
    record.update(extra)
    return record


CREW = [
    crew(6, "Ana Okafor", "ana@aurora.example", {"Piloting": 5, "Leadership": 4}),
    crew(7, "Ben Ito", "ben@aurora.example", {"Systems Engineering": 4, "EVA": 3}),
    crew(8, "Chen Wu", "chen@aurora.example", {"Systems Engineering": 3}),
    crew(9, "Dana Reyes", "dana@aurora.example", {"EVA": 4}),
    crew(
        11,
        "Fay Moreau",
        "fay@aurora.example",
        {"Piloting": 4, "Leadership": 4},
        unavailability=[
            {"id": 1, "start_date": "2027-03-05", "end_date": "2027-03-08", "reason": None}
        ],
    ),
    crew(12, "Gus Patel", "gus@aurora.example", {"Systems Engineering": 5}),
]

USERS = [
    {"id": 1, "email": "ruth@aurora.example", "name": "Ruth Adeyemi", "role": "director"},
    {"id": 4, "email": "lee@aurora.example", "name": "Lee Park", "role": "lead"},
    {"id": 5, "email": "nora@aurora.example", "name": "Nora Quinn", "role": "lead"},
    {"id": 8, "email": "chen@aurora.example", "name": "Chen Wu", "role": "crew"},
]
for _u in USERS:
    _u["active"] = True


def requirement(name: str, level: int) -> dict:
    ids = {s["name"]: s["id"] for s in SKILLS}
    return {"skill_id": ids[name], "skill_name": name, "min_level": level}


def gateway(
    status: str = "draft",
    assignments: Sequence[Mapping[str, Any]] = (),
    approvals: Sequence[Mapping[str, Any]] = (),
    open_places: Mapping[int, int] | None = None,
) -> dict:
    places = {1: 1, 2: 1, 3: 1} | dict(open_places or {})
    return {
        "id": 1,
        "name": "Lunar Gateway Resupply",
        "start_date": "2027-03-01",
        "end_date": "2027-03-10",
        "status": status,
        "owner_id": 4,
        "owner_name": "Lee Park",
        "created_by_id": 1,
        "created_by_name": "Ruth Adeyemi",
        "approval_round": 0,
        "approvals_required": None if status == "draft" else 2,
        "slots": [
            {
                "id": 1,
                "position": 1,
                "name": "Flight Engineer",
                "headcount": 1,
                "open_places": places[1],
                "requirements": [requirement("Systems Engineering", 3)],
            },
            {
                "id": 2,
                "position": 2,
                "name": "Mission Specialist",
                "headcount": 1,
                "open_places": places[2],
                "requirements": [requirement("EVA", 3)],
            },
            {
                "id": 3,
                "position": 3,
                "name": "Commander",
                "headcount": 1,
                "open_places": places[3],
                "requirements": [requirement("Piloting", 4), requirement("Leadership", 3)],
            },
        ],
        "assignments": list(assignments),
        "approvals": list(approvals),
    }


_SUMMARY_FIELDS = (
    "id", "name", "start_date", "end_date", "status", "owner_id", "owner_name",
    "created_by_id", "approval_round", "approvals_required",
)  # fmt: skip


def summary(mission: Mapping[str, Any]) -> dict:
    """The `GET /missions` row for a full mission record."""
    return {k: mission[k] for k in _SUMMARY_FIELDS}


S2_PREVIEW = {
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
                {"crew_profile_id": 8, "name": "Chen", "workload": 5, "proficiency": 3, "pick": 2}
            ],
        },
        {
            "slot_id": 2,
            "name": "Mission Specialist",
            "open_places": 1,
            "unfilled": 0,
            "suggested": [
                {"crew_profile_id": 9, "name": "Dana", "workload": 5, "proficiency": 4, "pick": 3}
            ],
        },
        {
            "slot_id": 3,
            "name": "Commander",
            "open_places": 1,
            "unfilled": 0,
            "suggested": [
                {"crew_profile_id": 6, "name": "Ana", "workload": 0, "proficiency": 9, "pick": 1}
            ],
        },
    ],
}

S3_PREVIEW = {
    "mission": {
        "id": 2,
        "name": "Asteroid Survey",
        "start_date": "2027-03-05",
        "end_date": "2027-03-12",
    },
    "can_apply": True,
    "open_places": 2,
    "unfilled_places": 1,
    "slots": [
        {
            "slot_id": 4,
            "name": "Pilot",
            "open_places": 1,
            "unfilled": 0,
            "suggested": [
                {"crew_profile_id": 6, "name": "Ana", "workload": 0, "proficiency": 5, "pick": 1}
            ],
        },
        {"slot_id": 5, "name": "Geologist", "open_places": 1, "unfilled": 1, "suggested": []},
    ],
}
