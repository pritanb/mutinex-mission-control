# Review checklist

Run each item for real where you can: in a terminal, piped (`| cat`), with no TTY on stdin (`< /dev/null`), with `NO_COLOR=1`, with bad input, and with Ctrl+C. Mark each item ✓, ✗ (with a finding) or n/a.

## Discoverability
- [ ] `tool`, `tool --help` and `tool <cmd> --help` all work; each command has a one-line description and at least one example.
- [ ] `--version` works.
- [ ] Command and flag names are consistent: same verbs, same `noun verb` order, no near-synonyms.
- [ ] Unknown commands and flags give a suggestion, not just "invalid".

## Input
- [ ] More than one value means named flags, not positional order. Frequent flags have short forms.
- [ ] A missing required input prompts when interactive, and gives a clear error when not. It never hangs.
- [ ] Sensible defaults cover the common case.
- [ ] Secrets are never accepted as flags; they're prompted for with input hidden.
- [ ] Destructive actions ask for confirmation, and `--yes` skips it.
- [ ] Invalid input is rejected before any side effect, and the message says what's valid.

## Feedback and output
- [ ] Every command reports its result in words ("Mission 12 created"), and `--quiet` suppresses it.
- [ ] Anything over about 1 second shows a spinner, a bar or named steps, on stderr, and only on a TTY.
- [ ] The next likely command is suggested at the end of common flows.
- [ ] Text is skimmable: short paragraphs, aligned tables, values truncated by display width.
- [ ] Icons and colours are few, consistent, and never the only signal.

## Errors
- [ ] No raw stack traces or back-end errors without `--verbose` / `--debug`.
- [ ] Each error says what went wrong, names the objects involved, and says how to fix it (ideally the exact next command).
- [ ] Several problems are listed together, one per line.
- [ ] Errors go to stderr, with a documented non-zero exit code.

## Scripting
- [ ] stdout holds only data; messages and progress go to stderr.
- [ ] When piped, there are no colours, spinners or escape codes. `NO_COLOR` and `TERM=dumb` are honoured.
- [ ] `--json` output is stable, documented and complete.
- [ ] Exit codes are documented: 0 ok, 1 failed or refused, 2 usage, 130 interrupted.
- [ ] `tool list | head` exits quietly (no broken-pipe traceback).

## Exit and interruption
- [ ] Ctrl+C stops promptly, cleans up, restores the terminal and exits 130. A second Ctrl+C forces exit.
- [ ] Interactive and full-screen modes show how to quit.
- [ ] After any exit (normal, error, signal), the cursor is visible, echo works and the prompt isn't coloured.

## TUI-specific (if full-screen or raw mode)
- [ ] Uses the alternate screen and always leaves it. The final result is printed after leaving.
- [ ] Raw mode is restored on every exit path, including exceptions.
- [ ] Resizing (SIGWINCH) redraws correctly. Very small sizes degrade gracefully.
- [ ] Rendering doesn't flicker (only changed cells are drawn).
- [ ] Focus is visible and keyboard-movable. Mouse support, if any, is opt-in and copy/paste is still possible.
- [ ] Works with 16 colours. Truecolor only when detected.
