---
name: cli-ux
description: Design or review the user experience of a command-line tool (CLI) or terminal UI (TUI). Use when planning commands, flags, help text, output, prompts or errors, when writing a CLI UX spec or mock terminal sessions, when reviewing CLI code or a CLI diff for usability, or when building interactive or full-screen terminal features (spinners, progress bars, prompts, raw mode, alternate screen, colors, resizing). Triggers on "CLI", "command line", "terminal UI", "TUI", "help text", "error message", "flags", "--json", "progress bar", "spinner", "interactive prompt", "Ctrl+C", "colors in terminal".
---

# CLI and TUI UX

Make terminal tools that are easy to learn, safe to script, and that leave the terminal as they found it.

## Two modes

**Designing.** Start from the user's workflows, not the command list:
1. Write the main workflows as mock terminal sessions: the exact commands typed and the exact output.
2. Apply the core rules below to every command and message.
3. Check the terminal mechanics in [references/terminal-mechanics.md](references/terminal-mechanics.md) for anything interactive, coloured or full-screen.
4. Run the checklist in [references/checklist.md](references/checklist.md) before calling the design done.

**Reviewing.** Read the code or diff and, where possible, run the tool for real, in a terminal and piped (`| cat`), with bad input and with Ctrl+C.
- Walk [references/checklist.md](references/checklist.md).
- Report findings using the output format below.

## Core rules

1. **Follow conventions.** Behave like the tools users already know. Use standard flags: `--help`, `--version`, `-q`, `-v`, `--json`, `--yes`. Use standard exit codes.
2. **Help everywhere.** `tool --help` lists every command with a one-line description, and `tool <cmd> --help` shows usage, arguments, options and an example.
3. **React to every action.** Success says what happened ("Logged out."). Silence is reserved for scriptable and quiet modes.
4. **Errors say what went wrong and how to fix it.** Never show a raw stack trace or back-end error. Name the thing involved and give the next command to run.
5. **Suggest the next step** at the end of common sequences (after `login`, suggest `create`).
6. **Flags over positional arguments** once there is more than one value. Give short forms to frequent flags.
7. **Prompt for missing required input** only when attached to a terminal, and offer sensible defaults. When not interactive, fail with a clear error instead of hanging.
8. **Show progress** for anything over about a second: a spinner for unknown length, a bar or named steps for known length. Progress goes to stderr.
9. **Always an easy way out.** Ctrl+C stops cleanly, restores the terminal, and exits 130. Interactive screens say how to quit.
10. **Write for skimmers.** Paragraphs of at most 3 short sentences, lists over prose, and a few consistent icons or colours used only as markers.
11. **Pipe-safe output.** Data goes to stdout and messages to stderr. Colour, spinners and prompts only when stdout or stdin is a TTY. Honour `NO_COLOR`, and offer `--json` for machines.
12. **Never depend on colour alone** for meaning. Pair it with a word or symbol.

Details, rationale and source for each rule: [references/principles.md](references/principles.md). Before/after examples: [references/examples.md](references/examples.md).

## Review output format

Group findings by severity: **Blocker** (unsafe, or breaks scripts), **Major** (users get stuck), **Minor** (friction). Each finding gives:
- the command or file:line;
- what the user sees today (exact text);
- the rule it breaks;
- a concrete rewrite (exact text, or the code change).

End with what works well, so it isn't changed by accident.
