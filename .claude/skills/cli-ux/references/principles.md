# Principles in detail

Sources:
- **[A]** Atlassian, "10 design principles for delightful CLIs" (https://www.atlassian.com/blog/jira-service-management/10-design-principles-for-delightful-clis).
- **[T]** "How Terminals Work" (https://how-terminals-work.vercel.app/).
- **[+]** A widely used convention that neither source covers, added for completeness.

## 1. Align with established conventions [A]
- Follow published style guides (Heroku CLI style guide, Microsoft style guide) and the tools your users already run.
- Use standard flags: `-h/--help`, `--version`, `-q/--quiet`, `-v/--verbose`, `-y/--yes`, `--json`, `--no-color`. [+]
- Exit codes [+]:
  - `0` success;
  - `1` general failure, or the request was refused;
  - `2` usage error (bad flags);
  - `130` interrupted by Ctrl+C (128 + SIGINT);
  - document any others.
- Command shape: `tool <noun> <verb>` or `tool <verb>`. Pick one and use it everywhere.

## 2. Build help into the tool [A]
- Top-level `--help` lists every command, subcommand and alias, each with a short description.
- `tool <cmd> --help` shows the full syntax: usage line, arguments, options with defaults, and at least one example.
- `tool` with no arguments shows short help, not an error. [+]
- An unknown command suggests the closest match ("Did you mean `missions`?"). [+]

## 3. Show progress visually [A]
- A text interface gives no other sign of life. Use a spinner for unknown durations and a progress bar for known ones.
- Split long jobs into named steps ("Seeding database… done", "Starting server…").
- Draw progress on stderr, and only on a TTY. When piped, print nothing or one line per step. [+][T]

## 4. A reaction for every action [A]
- Every command confirms what happened: `forge logout` gives "Logged out."
- Confirm with the result, not the verb: "Mission 12 submitted for approval (needs 2 approvals)", not "OK".
- `--quiet` suppresses confirmations. Scripts rely on exit codes. [+]

## 5. Human-readable errors [A]
- Never print a raw back-end error or stack trace. Show it only with `--verbose` or `--debug`.
- Each error says what went wrong and how to fix it. Link to more information if it exists.
- Name the objects involved, in the user's terms: "Gus has an accepted assignment on Station Reboost overlapping 1–2 Mar", not "constraint violation".
- When several things are wrong, list them all at once, one per line. [+]
- Errors go to stderr, with a non-zero exit code. [+]

## 6. Support skim-readers [A]
- Keep each paragraph to at most 3 sentences, or about 50–75 characters.
- Highlight the key fact with formatting or a list.
- Use a small, consistent set of icons, such as ✓ success, ✗ error, ! warning. They are markers, not decoration.
- Align tables, and truncate long values rather than wrapping them. [+]

## 7. Suggest the next best step [A]
- Find common command sequences and end each one with the likely next command: after `forge login`, suggest `forge create`.
- When something is refused, the hint is the fix ("Remove them first: `mc missions remove-crew 12 34`").

## 8. Consider your options [A]
- When a required option is missing, prompt for it instead of erroring, but only when stdin is a TTY. Without a TTY, error clearly and never block waiting for input. [+]
- Handle every case: no options, some options, and all options.
- Give sensible defaults so common cases need no flags: Forge defaults to the development environment.
- Never take secrets as flags (they end up in shell history and process lists). Prompt with input hidden, or read from stdin or a file. [+]

## 9. Provide an easy way out [A][T]
- Mark the exit paths. Interactive and full-screen modes say how to quit ("q to quit", "Ctrl+C to cancel").
- Ctrl+C must work. Catch SIGINT only to clean up (restore the terminal, remove temp files), then exit 130. [T][+]
- Destructive actions ask for confirmation, and `--yes` skips the prompt for scripts. [+]

## 10. Flags over arguments [A]
- Prefer labelled flags to positional arguments, so order needn't be memorised: `forge deploy --environment production --product jira`, not `forge deploy production jira`.
- Offer short forms for frequent flags: `-e production -p jira`.
- A single obvious argument (`tool show <id>`) is fine as a positional. Use flags from the second value onwards.

## 11. Pipe-safe output [+][T]
- stdout is for data, stderr for messages, progress and prompts. Then `tool list | grep x` and `tool list > file` work.
- Check `isatty(stdout)` before emitting colour, spinners or cursor movement.
- Honour `NO_COLOR` (any value disables colour) and a `--no-color` flag. `TERM=dumb` means no escape codes.
- `--json` prints stable, documented, machine-readable output, unchanged by colour or width.

## 12. Accessibility [+]
- Never use colour as the only signal; pair it with words or symbols.
- Avoid relying on Nerd Font or private-use icons, which show as boxes without the font. [T] Offer ASCII fallbacks.
- Keep wording plain. Screen readers read the raw text, so avoid decorative boxes made of characters.
