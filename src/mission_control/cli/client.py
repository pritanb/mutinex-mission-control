"""The CLI's only way into Mission Control: JSON requests to the HTTP API through an `httpx2`
client. Tests pass in a client with a mock transport, or the API's own test client, so no server
is needed."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx2

from mission_control.cli.errors import AUTHENTICATION, REFUSED, UNAVAILABLE

API_PREFIX = "/api/v1"
TIMEOUT = httpx2.Timeout(15.0, connect=5.0)  # the server may wait up to 5 s for a busy database


@dataclass(frozen=True)
class Problem:
    code: str
    message: str
    refs: Mapping[str, Any] = field(default_factory=dict)


class ApiError(Exception):
    """The server refused the request. Carries its error body: a code, a message and every
    problem. Commands may attach a `subject` (e.g. "Mission 5"), whether a state refusal should
    name it, and hints for known codes, which are used when the refusal is shown."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        problems: tuple[Problem, ...] = (),
        body: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.problems = problems
        self.body: Mapping[str, Any] = body or {}
        self.subject: str | None = None
        self.name_state = False
        self.hints: dict[str, str] = {}

    @property
    def exit_code(self) -> int:
        if self.status == 401:
            return AUTHENTICATION
        if self.status == 503:
            return UNAVAILABLE
        return REFUSED

    @property
    def has_error_body(self) -> bool:
        return isinstance(self.body.get("error"), Mapping)


class Unreachable(Exception):
    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.url = url


class Api:
    """Sends requests with the session token and turns error responses into `ApiError`.

    A 401 on a request that carried a token means the session is over, so
    `on_session_ended` runs (the CLI clears the saved token) before the error is raised."""

    def __init__(
        self,
        http: httpx2.Client,
        token: str | None = None,
        on_session_ended: Callable[[], None] | None = None,
    ) -> None:
        self._http = http
        self._token = token
        self._on_session_ended = on_session_ended

    def get(self, path: str, params: Mapping[str, str] | None = None) -> Any:
        return self._send("GET", path, params=params)

    def post(self, path: str, body: Any = None) -> Any:
        return self._send("POST", path, body=body)

    def put(self, path: str, body: Any = None) -> Any:
        return self._send("PUT", path, body=body)

    def patch(self, path: str, body: Any = None) -> Any:
        return self._send("PATCH", path, body=body)

    def delete(self, path: str) -> Any:
        return self._send("DELETE", path)

    def _send(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        params: Mapping[str, str] | None = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            response = self._http.request(
                method,
                API_PREFIX + path,
                json=body,
                params=dict(params) if params else None,
                headers=headers,
            )
        except httpx2.TransportError as exc:
            raise Unreachable(str(self._http.base_url).rstrip("/")) from exc

        if response.is_success:
            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                raise _unexpected(response) from None

        failure = _error(response)
        if response.status_code == 401 and self._token and self._on_session_ended:
            self._on_session_ended()
        raise failure


def _error(response: httpx2.Response) -> ApiError:
    try:
        body = response.json()
    except ValueError:
        return _unexpected(response)
    error = body.get("error") if isinstance(body, dict) else None
    if not (
        isinstance(error, dict)
        and isinstance(error.get("code"), str)
        and isinstance(error.get("message"), str)
    ):
        return _unexpected(response)
    problems = tuple(
        Problem(str(p.get("code", "")), str(p.get("message", "")), p.get("refs") or {})
        for p in error.get("problems") or ()
        if isinstance(p, dict)
    )
    return ApiError(response.status_code, error["code"], error["message"], problems, body)


def _unexpected(response: httpx2.Response) -> ApiError:
    return ApiError(
        response.status_code,
        "unexpected_response",
        f"The server sent an unexpected response (HTTP {response.status_code})",
    )
