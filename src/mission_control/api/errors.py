"""Turning refusals into HTTP responses. Every error, whatever its status, has one shape:

    {"error": {"code": ..., "message": ..., "problems": [{"code", "message", "refs"}, ...]}}

`problems` always has at least one entry. A refusal with a single reason repeats its message
there, so clients only ever read one format.
"""

import logging
from collections.abc import Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from mission_control.domain.dates import InvalidDateRange
from mission_control.domain.errors import (
    Forbidden,
    InvalidInput,
    NotFound,
    Problem,
    RuleViolation,
    Unauthenticated,
)
from mission_control.domain.passwords import MIN_PASSWORD_LENGTH, PasswordTooShort
from mission_control.infra.db import DatabaseBusy

log = logging.getLogger(__name__)

VALIDATION_ERROR = "validation_error"
_SEVERAL_MISTAKES = "Some values aren't valid"


def error_response(
    status: int,
    code: str,
    message: str,
    problems: Sequence[Problem] = (),
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    listed = problems or (Problem(code, message),)
    body = {
        "error": {
            "code": code,
            "message": message,
            "problems": [
                {"code": p.code, "message": p.message, "refs": dict(p.refs)} for p in listed
            ],
        }
    }
    return JSONResponse(body, status_code=status, headers=headers)


def install(app: FastAPI) -> None:
    """Register a handler for every refusal the services raise, and for malformed requests."""

    @app.exception_handler(Unauthenticated)
    def _unauthenticated(_: Request, e: Unauthenticated) -> JSONResponse:
        return error_response(401, e.code, e.message, headers={"WWW-Authenticate": "Bearer"})

    @app.exception_handler(Forbidden)
    def _forbidden(_: Request, e: Forbidden) -> JSONResponse:
        return error_response(403, e.code, e.message)

    @app.exception_handler(NotFound)
    def _not_found(_: Request, e: NotFound) -> JSONResponse:
        return error_response(404, e.code, e.message)

    @app.exception_handler(RuleViolation)  # StateConflict included
    def _rule_violation(_: Request, e: RuleViolation) -> JSONResponse:
        return error_response(409, e.code, e.message, e.problems)

    @app.exception_handler(InvalidInput)
    def _invalid_input(_: Request, e: InvalidInput) -> JSONResponse:
        return error_response(422, VALIDATION_ERROR, e.message, e.problems)

    @app.exception_handler(PasswordTooShort)
    def _password_too_short(_: Request, e: PasswordTooShort) -> JSONResponse:
        message = f"Passwords must be at least {MIN_PASSWORD_LENGTH} characters"
        return error_response(422, "password_too_short", message)

    @app.exception_handler(InvalidDateRange)
    def _invalid_date_range(_: Request, e: InvalidDateRange) -> JSONResponse:
        text = str(e)
        return error_response(422, VALIDATION_ERROR, text[:1].upper() + text[1:])

    @app.exception_handler(DatabaseBusy)
    def _busy(_: Request, e: DatabaseBusy) -> JSONResponse:
        return error_response(503, "busy", "The database is busy; try again")

    @app.exception_handler(RequestValidationError)
    def _malformed(_: Request, e: RequestValidationError) -> JSONResponse:
        problems = [_validation_problem(err) for err in e.errors()]
        message = problems[0].message if len(problems) == 1 else _SEVERAL_MISTAKES
        return error_response(422, VALIDATION_ERROR, message, problems)

    @app.exception_handler(StarletteHTTPException)
    def _http(_: Request, e: StarletteHTTPException) -> JSONResponse:
        if e.status_code == 404:
            return error_response(404, NotFound.code, "Not found")
        phrase = HTTPStatus(e.status_code).phrase
        code = phrase.lower().replace(" ", "_")  # e.g. 405 method_not_allowed
        return error_response(e.status_code, code, phrase, headers=e.headers)

    @app.exception_handler(Exception)
    def _unexpected(request: Request, e: Exception) -> JSONResponse:
        """A bug, not a refusal. Only exceptions no handler above claims reach here. The
        details stay on the server, never in the response: this names the request, and Starlette
        re-raises the exception once the response is sent, so the server logs its traceback."""
        log.error("Unhandled %s on %s %s", type(e).__name__, request.method, request.url.path)
        return error_response(500, "internal_error", "Something went wrong on the server")


# Malformed requests. Pydantic's own wording is replaced for the common cases, so a refusal
# reads as a sentence about the field, e.g. "start_date must be a date (YYYY-MM-DD)".

_PHRASES = {
    "missing": "{field} is required",
    "int_parsing": "{field} must be a whole number",
    "int_type": "{field} must be a whole number",
    "int_from_float": "{field} must be a whole number",
    "string_type": "{field} must be text",
    "bool_parsing": "{field} must be true or false",
    "bool_type": "{field} must be true or false",
    "date_parsing": "{field} must be a date (YYYY-MM-DD)",
    "date_from_datetime_parsing": "{field} must be a date (YYYY-MM-DD)",
    "date_from_datetime_inexact": "{field} must be a date (YYYY-MM-DD)",
    "date_type": "{field} must be a date (YYYY-MM-DD)",
    "list_type": "{field} must be a list",
    "model_type": "{field} must be an object",
    "model_attributes_type": "{field} must be an object",
    "dict_type": "{field} must be an object",
    "greater_than_equal": "{field} must be at least {ge}",
    "less_than_equal": "{field} must be at most {le}",
    "extra_forbidden": "{field} isn't a known field",
}


def _validation_problem(err: dict[str, Any]) -> Problem:
    kind = err.get("type", "")
    if kind == "json_invalid":
        return Problem(VALIDATION_ERROR, "The request body isn't valid JSON")
    field = _field(err.get("loc", ()))
    ctx = err.get("ctx") or {}
    if field == "":  # about the request body as a whole
        if kind == "value_error" and "error" in ctx:
            return Problem(VALIDATION_ERROR, str(ctx["error"]))
        if kind == "missing":
            return Problem(VALIDATION_ERROR, "The request body is required")
        return Problem(VALIDATION_ERROR, "The request body must be a JSON object")
    if kind == "enum" and "expected" in ctx:
        choices = ctx["expected"].replace("'", "").replace(" or ", ", ")
        message = f"{field} must be one of: {choices}"
    elif kind == "value_error" and "error" in ctx:
        message = f"{field} {ctx['error']}"
    elif kind in _PHRASES:
        message = _PHRASES[kind].format(field=field, **ctx)
    else:
        message = f"{field}: {err.get('msg', 'is not valid')}"
    return Problem(VALIDATION_ERROR, message, {"field": field})


def _field(loc: Sequence[int | str]) -> str:
    """('body', 'slots', 0, 'headcount') -> 'slots[0].headcount'. The request part (body,
    path, query) is left out."""
    parts = list(loc[1:]) if loc and loc[0] in ("body", "path", "query", "header") else list(loc)
    text = ""
    for part in parts:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text
