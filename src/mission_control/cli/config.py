"""Where the CLI finds the server, and where it keeps the session from `mc login`: a small JSON
file that only the user can read."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_API_URL = "http://127.0.0.1:8000"
_CREDENTIALS_FILE = "credentials.json"


def default_config_dir() -> Path:
    return Path.home() / ".config" / "mission-control"


def api_url() -> str:
    """The server's base URL. `MC_API_URL` overrides the local default."""
    return (os.environ.get("MC_API_URL") or "").strip().rstrip("/") or DEFAULT_API_URL


@dataclass(frozen=True)
class Credentials:
    token: str
    email: str
    expires_at: str | None = None


class CredentialStore:
    """The session token on disk. The file is written with mode 0600 inside a 0700 directory,
    and replaced atomically so a crash never leaves half a file."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    @property
    def path(self) -> Path:
        return self.directory / _CREDENTIALS_FILE

    def load(self) -> Credentials | None:
        """The saved session, or None when there isn't a usable one."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        token = data.get("token")
        if not isinstance(token, str) or not token:
            return None
        expires_at = data.get("expires_at")
        return Credentials(
            token=token,
            email=str(data.get("email") or ""),
            expires_at=expires_at if isinstance(expires_at, str) else None,
        )

    def save(self, credentials: Credentials) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.directory, 0o700)
        temporary = self.path.with_name(self.path.name + ".tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.fchmod(fd, 0o600)  # the mode given to open() is ignored if the file existed
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(asdict(credentials), file)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        os.replace(temporary, self.path)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
