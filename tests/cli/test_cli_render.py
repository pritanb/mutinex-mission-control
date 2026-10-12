"""M16: output building blocks. Friendlier dates, aligned tables, markers that never rely on
colour, and colour only on a terminal (design §8, docs/cli-ux.md)."""

import io
from datetime import date

import pytest

from mission_control.cli.render import (
    Span,
    Style,
    Terminal,
    detect_style,
    format_range,
    format_timestamp,
    table_lines,
)


class FakeTty(io.StringIO):
    def __init__(self, tty: bool = True, encoding: str = "utf-8"):
        super().__init__()
        self._tty = tty
        self._encoding = encoding

    def isatty(self) -> bool:
        return self._tty

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return self._encoding


@pytest.mark.parametrize(
    ("start", "end", "fancy", "plain"),
    [
        (date(2027, 3, 1), date(2027, 3, 10), "1–10 Mar 2027", "1-10 Mar 2027"),
        (date(2027, 3, 5), date(2027, 3, 5), "5 Mar 2027", "5 Mar 2027"),
        (date(2027, 2, 25), date(2027, 3, 2), "25 Feb – 2 Mar 2027", "25 Feb - 2 Mar 2027"),
        (
            date(2026, 12, 30),
            date(2027, 1, 2),
            "30 Dec 2026 – 2 Jan 2027",
            "30 Dec 2026 - 2 Jan 2027",
        ),
    ],
)
def test_m16_dates_read_naturally(start, end, fancy, plain):
    assert format_range(start, end) == fancy
    assert format_range(start, end, plain=True) == plain


def test_m16_timestamps_are_shown_in_utc_without_seconds():
    assert format_timestamp("2027-01-05T09:03:27.123Z") == "5 Jan 2027 09:03"


def test_m16_tables_align_columns_with_no_trailing_spaces():
    lines = table_lines(
        ["Slot", "Suggested", "Workload"],
        [["Flight Engineer", "Chen", "5 days"], ["Mission Specialist", "Dana", "5 days"]],
    )

    assert lines == [
        "  Slot                 Suggested   Workload",
        "  Flight Engineer      Chen        5 days",
        "  Mission Specialist   Dana        5 days",
    ]


def test_m16_a_spanning_row_does_not_widen_the_other_columns():
    lines = table_lines(
        ["Slot", "Suggested", "Pick"],
        [["Pilot", "Ana", "1"], Span("Geologist", "unfilled (1 place)")],
    )

    assert lines == [
        "  Slot        Suggested   Pick",
        "  Pilot       Ana         1",
        "  Geologist   unfilled (1 place)",
    ]


def test_m16_colour_only_on_a_terminal():
    assert detect_style(FakeTty(tty=True), {"TERM": "xterm-256color"}) == Style(True, True)
    assert detect_style(FakeTty(tty=False), {"TERM": "xterm-256color"}) == Style(False, True)


@pytest.mark.parametrize("environ", [{"NO_COLOR": "1", "TERM": "xterm"}, {"TERM": "dumb"}])
def test_m16_no_color_and_dumb_terminals_get_plain_words(environ):
    assert detect_style(FakeTty(tty=True), environ) == Style(color=False, unicode=False)


def test_m16_a_non_utf8_terminal_gets_plain_words_but_keeps_colour():
    assert detect_style(FakeTty(encoding="ascii"), {"TERM": "xterm"}) == Style(True, False)


def test_m16_markers_carry_meaning_without_colour():
    out, err = FakeTty(), FakeTty()
    term = Terminal(out, err, Style(False, True), Style(False, True))
    term.ok("Logged out.")
    term.note("Heads up.")
    term.error("Mission 5 not found.", hint="See your missions: mc missions list")

    assert out.getvalue() == "✓ Logged out.\n! Heads up.\n"
    assert err.getvalue() == "✗ Mission 5 not found.\n  See your missions: mc missions list\n"


def test_m16_plain_markers_use_words():
    out, err = FakeTty(), FakeTty()
    term = Terminal(out, err, Style(False, False), Style(False, False))
    term.ok("Done.")
    term.note("Careful.")
    term.error("Broken.", ["first", "second"])

    assert out.getvalue() == "OK: Done.\nNote: Careful.\n"
    assert err.getvalue() == "Error: Broken.\n  - first\n  - second\n"


def test_m16_colour_wraps_only_the_marker_and_always_resets():
    out, err = FakeTty(), FakeTty()
    term = Terminal(out, err, Style(True, True), Style(True, True))
    term.ok("Done.")
    term.error("Broken.")

    assert out.getvalue() == "\x1b[32m✓\x1b[0m Done.\n"
    assert err.getvalue() == "\x1b[31m✗\x1b[0m Broken.\n"


def test_m16_next_steps_go_to_stderr_one_per_line():
    out, err = FakeTty(), FakeTty()
    term = Terminal(out, err, Style(False, True), Style(False, True))
    term.next_steps(["mc missions match 1 --apply", "mc missions show 1"])

    assert out.getvalue() == ""
    assert err.getvalue() == "Next: mc missions match 1 --apply\n      mc missions show 1\n"
