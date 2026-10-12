"""What every command runs with: the HTTP client, the saved session, the terminal and whether
there's anyone at the keyboard. Tests build one with a mock client and a temporary config
directory; a real run builds the defaults."""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import httpx2

from mission_control.cli.client import TIMEOUT, Api
from mission_control.cli.config import CredentialStore, api_url, default_config_dir
from mission_control.cli.errors import NotLoggedIn
from mission_control.cli.prompts import Prompter, TerminalPrompter
from mission_control.cli.render import Terminal


@dataclass
class Env:
    http: httpx2.Client | None = None
    config_dir: Path | None = None
    interactive: bool | None = None  # None: ask whether stdin is a terminal
    color: bool | None = None  # None: decide from the terminal and NO_COLOR
    prompter: Prompter = field(default_factory=TerminalPrompter)
    json_output: bool = False  # set by a command run with --json
    _terminal: Terminal | None = field(default=None, init=False, repr=False)

    @property
    def store(self) -> CredentialStore:
        return CredentialStore(self.config_dir or default_config_dir())

    @property
    def term(self) -> Terminal:
        # Built on first use, so it writes to the streams in place when the command runs.
        if self._terminal is None:
            self._terminal = Terminal.for_streams(sys.stdout, sys.stderr, self.color)
        return self._terminal

    @property
    def is_interactive(self) -> bool:
        if self.interactive is not None:
            return self.interactive
        try:
            return sys.stdin.isatty()
        except (AttributeError, ValueError):
            return False

    def client(self) -> httpx2.Client:
        if self.http is None:
            self.http = httpx2.Client(base_url=api_url(), timeout=TIMEOUT)
        return self.http

    def anonymous_api(self) -> Api:
        return Api(self.client())

    def api(self) -> Api:
        """An API client for the logged-in user. A 401 clears the saved session."""
        credentials = self.store.load()
        if credentials is None:
            raise NotLoggedIn()
        return Api(self.client(), credentials.token, on_session_ended=self.store.clear)
