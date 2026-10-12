# Terminal mechanics, as practical rules

Based on "How Terminals Work" (https://how-terminals-work.vercel.app/), marked **[T]**. Additions marked **[+]**. Read this before building anything coloured, interactive or full-screen.

## The stack [T]
- Data passes through these layers, inward for keystrokes and outward for output:
  - the terminal emulator (iTerm2, Ghostty, kitty) encodes keys and renders cells;
  - the PTY (pseudo-terminal, in the kernel) and its **line discipline**;
  - the shell (zsh, bash);
  - your program.
- A terminal is a grid of same-sized cells. Each cell holds one character plus style (colour, bold, underline). Everything else is escape sequences.

**Rule:** your program talks to a PTY, not a screen. Output can just as well go to a pipe or a file, so never assume a terminal is attached.

## Is anyone there? (TTY detection) [T][+]
- Check `isatty(stdin)` and `isatty(stdout)` separately.
- No TTY on stdout means no colour, spinners, cursor movement or alternate screen.
- No TTY on stdin means no prompts; fail with a clear message instead.
- `TERM` names the terminal type, and programs look up its capabilities in the **terminfo** database. It's only a string the terminal doesn't enforce, so treat it as a hint. [T]
- `TERM=dumb`, or an empty `TERM`, means plain text only. [+]
- Programs can also ask the terminal directly (e.g. the DA1 "what are you?" query), but only when attached to a TTY and with a timeout. [T]

## Escape codes [T]
- Control sequences start with ESC (byte `0x1B`). CSI sequences are `ESC [ … letter`. Common ones:
  - `ESC[0m` resets all styles;
  - `ESC[2J` clears the screen;
  - `ESC[H` moves the cursor to the home position, and `ESC[5;10H` to row 5, column 10;
  - `ESC[?25l` / `ESC[?25h` hide and show the cursor.
- **Rules:**
  - Always reset styles after styled text (`…ESC[0m`), or colour bleeds into the user's prompt.
  - If you hide the cursor, show it again on every exit path, including errors and Ctrl+C. [T][+]
  - Never write escape codes when not on a TTY; they show up as garbage in files and logs ("weird characters like `^[[34m`"). [T]

## Colour depth [T][+]
- **16 colours:** codes 30–37 normal, 90–97 bright (backgrounds 40–47, 100–107). They work everywhere and follow the user's theme, so they're the safe default.
- **256 colours:** `ESC[38;5;Nm`. Available when `TERM` contains `256color`.
- **Truecolor (24-bit):** `ESC[38;2;R;G;Bm`. Smooth gradients are only possible here. Detect it with `COLORTERM=truecolor` or `24bit`. [+]
- **Rules:**
  - Prefer the 16 named colours for meaning (red error, green success, yellow warning). Users' themes stay in charge, and contrast stays readable.
  - Degrade gracefully from truecolor to 256 to 16 to none.
  - `NO_COLOR` set means no colour at all. [+]

## Input: cooked vs raw mode [T]
- **Cooked (canonical) mode:** the line discipline buffers a whole line. Backspace edits it, and nothing reaches the program until Enter. Shells, `cat` and simple prompts use this.
- **Raw mode:** every key reaches the program immediately, with no editing. vim, htop, less and ssh use this.
- Arrow keys and function keys arrive as escape sequences of several bytes, e.g. `ESC [ A` for Up, and `CSI Z` for Shift+Tab. A program that doesn't decode them prints junk. [T]
- **Rules:**
  - Use cooked mode for simple prompts, so line editing comes free.
  - In raw mode you own everything: echo, editing, cursor and Ctrl+C. **Always restore cooked mode on exit, crash or signal**, or the user's shell is left broken (no echo; they need to run `reset`). [T][+]
  - Prefer a library (prompt_toolkit, Textual, Bubble Tea, Ink, crossterm) over hand-rolled raw mode.

## Signals [T]
- **Ctrl+C:** the terminal sends byte `0x03`. In cooked mode the line discipline turns it into **SIGINT** for the foreground process group before your program sees it. The default action is to terminate.
- **Ctrl+Z:** SIGTSTP, which suspends the process. `fg` resumes it in the foreground, `bg` in the background.
- **Window resize:** SIGWINCH. Query the new size (ioctl `TIOCGWINSZ` / `os.get_terminal_size`) and redraw.
- **In raw mode**, Ctrl+C arrives as plain byte `0x03`, and **your program must handle it itself**. [T]
- **Rules:**
  - Catch SIGINT only to clean up (restore terminal mode, show the cursor, leave the alternate screen, remove temp files, roll back), then exit 130. [+]
  - A second Ctrl+C during cleanup should exit immediately. [+]
  - If you support suspend (Ctrl+Z), restore the terminal before stopping, and re-enter raw mode and redraw on SIGCONT. [+]
  - When piped into something that exits early (`tool list | head`), handle SIGPIPE or a broken pipe quietly, without a traceback. [+]
  - Long-running non-interactive commands should respond to SIGTERM like SIGINT. [+]

## The alternate screen [T]
- Terminals have two buffers: the **normal screen**, with scrollback, and the **alternate screen**, a separate canvas.
  - `CSI ?1049h` enters the alternate screen; `CSI ?1049l` leaves it and restores the user's previous output.
  - vim, less, man, htop and tmux all use it.
- **Rules:**
  - Full-screen TUIs use the alternate screen, so they don't overwrite history, and **always leave it on exit**, including on crash or signal.
  - Plain CLIs (output the user wants to keep, copy or scroll back to) must **not** use it.
  - Things in the alternate screen vanish on exit, so print any final result after leaving it.

## Building TUIs [T]
- Lay the screen out as a tree of regions with bounds in cells, recomputed on resize. Exactly one region has focus and receives keys. Tab and arrows move focus, and unhandled events bubble up.
- Render to an in-memory buffer, then write only the changed cells in one go (double buffering). That prevents flicker.
- Hide the cursor while drawing and restore it afterwards.
- Mouse events are opt-in. Without mouse tracking, clicks belong to the terminal's own text selection. With it, clicks arrive as escape sequences with coordinates, and users lose easy copy/paste, so offer a way out (often holding Shift). [T]
- The app owns the cursor position. Clicking doesn't move it (Option+Click works only by faking arrow keys). Don't promise click-to-place behaviour. [T]
- The terminal stores no app state. Modes (e.g. Shift+Tab cycling) live in your program, which must redraw whenever state changes. [T]

## Character width [T]
- Most characters take 1 cell. CJK characters and many emoji take **2**. Nerd Font icons take 1, but render as boxes without the font.
- **Rules:**
  - Measure display width (`wcwidth`), not `len()`, when aligning tables or truncating.
  - Don't require Nerd Fonts. Offer plain fallbacks.
