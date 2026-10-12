"""How messages put names together, so every refusal lists people and records the same way."""

from collections.abc import Iterable, Sequence


def join_names(names: Iterable[str]) -> str:
    """'A', 'A and B', 'A, B and C'."""
    items = list(names)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def is_are(names: Sequence[str]) -> str:
    return "is" if len(names) == 1 else "are"
