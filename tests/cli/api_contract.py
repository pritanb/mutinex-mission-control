"""Checks a scripted response against the real API, so the CLI's test doubles can't drift from it.

Every route is read from the API's routers: its method, path, success status and response
model (`test_contract_covers_every_api_route` keeps that list in step with the app).

- A fake response must be for a route that exists and use that route's success status.
- Its body must be one the response model accepts, with no fields the model doesn't have.
- An error must have the design's error shape, with a code its status can carry.
- A plain 500 is allowed, as the real server sends one for an unhandled fault.
"""

import json
from collections.abc import Mapping
from typing import Any

import httpx2
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from mission_control.api.routers import admin, assignments, auth, crew, missions

ROUTES = [
    r
    for module in (auth, admin, crew, missions, assignments)
    for r in module.router.routes
    if isinstance(r, APIRoute)
]


# The top-level error codes each status may carry (design §7, Errors). A rule refusal's reasons are
# problem codes inside `problems`, never the top-level code.
_ERROR_CODES: Mapping[int, frozenset[str]] = {
    401: frozenset({"invalid_credentials", "unauthenticated"}),
    403: frozenset(
        {
            "role_forbidden",
            "not_owner",
            "approver_is_creator",
            "approver_is_rostered",
            "self_skill_edit",
            "wrong_current_password",
        }
    ),
    404: frozenset({"not_found"}),
    409: frozenset(
        {
            "mission_frozen",
            "mission_final",
            "invalid_transition",
            "already_decided",
            "rule_violation",
        }
    ),
    422: frozenset({"validation_error", "password_too_short"}),
    503: frozenset({"busy"}),
}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ProblemBody(_Strict):
    code: str
    message: str
    refs: dict[str, Any]


class _ErrorDetail(_Strict):
    code: str
    message: str
    problems: list[_ProblemBody]


class _ErrorBody(_Strict):
    error: _ErrorDetail


def _route(method: str, path: str) -> APIRoute | None:
    for route in ROUTES:
        if method in route.methods and route.path_regex.match(path):
            return route
    return None


def problems(method: str, path: str, response: httpx2.Response) -> list[str]:
    """What's wrong with a scripted response to `method path` (path without the /api/v1 prefix).
    Empty when it's a response the real API could send."""
    where = f"{method} {path}"
    route = _route(method, path)
    if route is None:
        return [f"{where}: the API has no such endpoint"]
    status = response.status_code
    if status == 500:
        return []  # an unhandled server fault: the real server sends plain text too
    try:
        body = json.loads(response.content) if response.content else None
    except ValueError:
        return [f"{where}: the body isn't JSON"]

    if status >= 400:
        try:
            _ErrorBody.model_validate(body)
        except ValidationError as exc:
            return [f"{where}: error body doesn't match the error shape: {exc}"]
        error = body["error"]
        if not error["problems"]:
            return [f"{where}: an error lists at least one problem"]
        if error["code"] not in _ERROR_CODES.get(status, ()):
            return [f"{where}: the API doesn't send {error['code']!r} with a {status}"]
        return []

    expected = route.status_code or 200
    if status != expected:
        return [f"{where}: answers {expected}, not {status}"]
    if expected == 204:
        return [] if body is None else [f"{where}: a 204 has no body"]

    adapter: TypeAdapter[Any] = TypeAdapter(route.response_model)
    try:
        parsed = adapter.validate_python(body)
    except ValidationError as exc:
        return [f"{where}: body doesn't match {_name(route)}: {exc}"]
    return [f"{where}: {p}" for p in _unknown(body, parsed, "body")]


def _name(route: APIRoute) -> str:
    model = route.response_model
    return getattr(model, "__name__", None) or str(model)


def _unknown(sent: Any, parsed: Any, at: str) -> list[str]:
    """Fields in `sent` that the parsed model doesn't have, anywhere in the tree."""
    found: list[str] = []
    if isinstance(parsed, BaseModel) and isinstance(sent, dict):
        fields = type(parsed).model_fields
        allowed = set(fields)
        for key, value in sent.items():
            if key not in allowed:
                found.append(f"{at}.{key} isn't in {type(parsed).__name__}")
            elif key in fields:
                found += _unknown(value, getattr(parsed, key), f"{at}.{key}")
    elif isinstance(parsed, list | tuple) and isinstance(sent, list):
        for i, (s, p) in enumerate(zip(sent, parsed, strict=False)):
            found += _unknown(s, p, f"{at}[{i}]")
    elif isinstance(parsed, Mapping) and isinstance(sent, dict):
        for key, value in sent.items():
            found += _unknown(value, parsed.get(key), f"{at}.{key}")
    return found
