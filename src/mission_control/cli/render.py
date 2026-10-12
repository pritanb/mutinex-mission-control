"""Everything the CLI prints. Data goes to stdout, messages and next steps to stderr. Colour only
marks a symbol, never carries meaning alone, and appears only on a terminal. With `NO_COLOR`,
`TERM=dumb` or a non-UTF-8 terminal the symbols become plain words."""

import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, TextIO

from rich.cells import cell_len

_GAP = "   "
_INDENT = "  "

_GREEN, _YELLOW, _RED, _RESET = "\x1b[32m", "\x1b[33m", "\x1b[31m", "\x1b[0m"

MISSION_STATUS = {
    "draft": "Draft",
    "pending_approval": "Pending approval",
    "active": "Active",
    "completed": "Completed",
    "cancelled": "Cancelled",
}
ASSIGNMENT_STATUS = {
    "proposed": "Proposed",
    "accepted": "Accepted",
    "declined": "Declined",
    "withdrawn": "Withdrawn",
    "removed": "Removed",
    "completed": "Completed",
    "cancelled": "Cancelled",
}
ROLE = {"director": "Director", "lead": "Mission Lead", "crew": "Crew Member"}


@dataclass(frozen=True)
class Style:
    color: bool
    unicode: bool


def detect_style(stream: TextIO, environ: Mapping[str, str]) -> Style:
    """Colour needs a terminal, no `NO_COLOR` and a `TERM` that isn't dumb. Symbols need UTF-8
    and the same opt-outs."""
    term = environ.get("TERM", "")
    opted_out = "NO_COLOR" in environ or term == "dumb"
    is_tty = _isatty(stream)
    encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
    return Style(
        color=is_tty and not opted_out and bool(term),
        unicode=encoding == "utf8" and not opted_out,
    )


def _isatty(stream: TextIO) -> bool:
    try:
        return stream.isatty()
    except (AttributeError, ValueError):
        return False


# Dates


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def format_range(start: date, end: date, *, plain: bool = False) -> str:
    """`1–10 Mar 2027`, `25 Feb – 2 Mar 2027`, `30 Dec 2026 – 2 Jan 2027`, or one day."""
    dash = "-" if plain else "–"
    if start == end:
        return _day(end, year=True)
    if (start.year, start.month) == (end.year, end.month):
        return f"{start.day}{dash}{_day(end, year=True)}"
    left = _day(start, year=start.year != end.year)
    return f"{left} {dash} {_day(end, year=True)}"


def _day(d: date, *, year: bool) -> str:
    text = f"{d.day} {d.strftime('%b')}"
    return f"{text} {d.year}" if year else text


def format_timestamp(value: str) -> str:
    """A UTC timestamp from the server as `5 Jan 2027 09:03`."""
    moment = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return f"{moment.day} {moment.strftime('%b %Y %H:%M')}"


# Tables


@dataclass(frozen=True)
class Span:
    """A row whose first cell lines up with the column and whose text runs across the rest."""

    first: str
    rest: str


def table_lines(
    headers: Sequence[str], rows: Iterable[Sequence[str] | Span], indent: str = _INDENT
) -> list[str]:
    """Columns padded by display width, three spaces apart, with no trailing spaces."""
    rows = list(rows)
    widths = [cell_len(h) for h in headers]
    for row in rows:
        cells = [row.first] if isinstance(row, Span) else row
        for i, cell in enumerate(cells):
            widths[i] = max(widths[i], cell_len(cell))

    def line(cells: Sequence[str]) -> str:
        padded = [c + " " * (widths[i] - cell_len(c)) for i, c in enumerate(cells)]
        return (indent + _GAP.join(padded)).rstrip()

    lines = [line(headers)]
    for row in rows:
        if isinstance(row, Span):
            pad = " " * (widths[0] - cell_len(row.first))
            lines.append((indent + row.first + pad + _GAP + row.rest).rstrip())
        else:
            lines.append(line(row))
    return lines


def field_lines(pairs: Sequence[tuple[str, str]]) -> list[str]:
    width = max(cell_len(k) for k, _ in pairs)
    return [f"{k}{' ' * (width - cell_len(k))}{_GAP}{v}".rstrip() for k, v in pairs]


# Words


def join_names(names: Sequence[str]) -> str:
    """`Ana`, `Ana and Chen`, `Ana, Chen and Dana`."""
    if len(names) <= 1:
        return "".join(names)
    return f"{', '.join(names[:-1])} and {names[-1]}"


def plural(count: int, word: str, many: str | None = None) -> str:
    return f"{count} {word if count == 1 else many or word + 's'}"


def sentence(text: str) -> str:
    """End a server message with a full stop unless it already has one."""
    text = text.strip()
    return text if not text or text[-1] in ".!?" else text + "."


class Terminal:
    """Writes data to stdout and messages to stderr, each styled for its own stream."""

    def __init__(self, out: TextIO, err: TextIO, out_style: Style, err_style: Style) -> None:
        self.out = out
        self.err = err
        self.out_style = out_style
        self.err_style = err_style

    @classmethod
    def for_streams(cls, out: TextIO, err: TextIO, color: bool | None = None) -> "Terminal":
        out_style, err_style = detect_style(out, os.environ), detect_style(err, os.environ)
        if color is not None:
            out_style = Style(color, out_style.unicode)
            err_style = Style(color, err_style.unicode)
        return cls(out, err, out_style, err_style)

    # Plain-text forms of the separators

    @property
    def sep(self) -> str:
        return " · " if self.out_style.unicode else " - "

    def dates(self, start: str, end: str) -> str:
        return format_range(parse_date(start), parse_date(end), plain=not self.out_style.unicode)

    def heading(self, *parts: str) -> str:
        return self.sep.join(p for p in parts if p)

    # stdout

    def line(self, text: str = "") -> None:
        self.out.write(text + "\n")

    def lines(self, lines: Iterable[str]) -> None:
        for text in lines:
            self.line(text)

    def table(self, headers: Sequence[str], rows: Iterable[Sequence[str] | Span]) -> None:
        self.lines(table_lines(headers, rows))

    def fields(self, pairs: Sequence[tuple[str, str]]) -> None:
        self.lines(field_lines(pairs))

    def json(self, data: Any) -> None:
        self.line(json.dumps(data, indent=2, ensure_ascii=False))

    def ok(self, message: str) -> None:
        self.line(self._marker("✓", "OK:", _GREEN, self.out_style) + " " + message)

    def note(self, message: str) -> None:
        self.line(self._marker("!", "Note:", _YELLOW, self.out_style) + " " + message)

    # stderr

    def say(self, text: str = "") -> None:
        self.out.flush()  # keep data and messages in order when stdout is a pipe
        self.err.write(text + "\n")
        self.err.flush()

    def warn(self, message: str) -> None:
        self.say(self._marker("!", "Note:", _YELLOW, self.err_style) + " " + message)

    def error(
        self, message: str, bullets: Sequence[str] = (), hint: str | Sequence[str] | None = None
    ) -> None:
        self.say(self._marker("✗", "Error:", _RED, self.err_style) + " " + message)
        bullet = "•" if self.err_style.unicode else "-"
        for text in bullets:
            self.say(f"{_INDENT}{bullet} {text}")
        hints = [hint] if isinstance(hint, str) else list(hint or ())
        for text in hints:
            self.say(_INDENT + text)

    def next_steps(self, steps: Sequence[str]) -> None:
        for i, step in enumerate(steps):
            self.say(("Next: " if i == 0 else "      ") + step)

    @staticmethod
    def _marker(symbol: str, word: str, colour: str, style: Style) -> str:
        if not style.unicode:
            return word
        return f"{colour}{symbol}{_RESET}" if style.color else symbol
