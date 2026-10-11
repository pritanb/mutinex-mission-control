from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Problem:
    """One reason an action can't go ahead. `refs` names the records involved."""

    code: str
    message: str
    refs: Mapping[str, int | str | list[int]] = field(default_factory=dict)
