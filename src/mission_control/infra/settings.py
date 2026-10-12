"""Runtime settings, read from the environment once at startup.

- `MC_DATABASE_PATH`: the SQLite file (default `mission_control.db` in the working directory)
- `MC_DB_BUSY_TIMEOUT_MS`: how long a request waits for the write lock (default 5000)
- `MC_TOKEN_TTL_HOURS`: how long a session lasts (default 12)
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("mission_control.db")
    busy_timeout_ms: int = 5000
    token_ttl_hours: int = 12

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        defaults = cls()
        return cls(
            database_path=Path(env.get("MC_DATABASE_PATH") or defaults.database_path),
            busy_timeout_ms=_whole(env, "MC_DB_BUSY_TIMEOUT_MS", defaults.busy_timeout_ms, 0),
            token_ttl_hours=_whole(env, "MC_TOKEN_TTL_HOURS", defaults.token_ttl_hours, 1),
        )


def _whole(env: Mapping[str, str], name: str, default: int, minimum: int) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, not {raw!r}") from None
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, not {value}")
    return value
