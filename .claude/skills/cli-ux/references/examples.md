# Before and after

## 1. Error message (rules 4, 5, 7)

Before:
```
$ mc missions propose 12 --slot Engineer --crew gus@aurora.example
Error: 409 Conflict {"error":{"code":"rule_violation"}}
```
After:
```
$ mc missions propose 12 --slot Engineer --crew gus@aurora.example
✗ Can't propose Gus Patel for Engineer on Lunar Gateway Resupply
  • Gus has an accepted assignment on Station Reboost overlapping 1–2 Mar 2027

  See who is free: mc missions match 12
```
It says what failed, names everyone involved, and gives the next command. Exit code 1, printed on stderr.

## 2. Flags over positional arguments (rule 6)

Before: `mc missions create "Europa Flyby" 2027-09-01 2027-09-20 lee@aurora.example`
(Which date is which? Is the email the owner or the creator?)

After: `mc missions create --name "Europa Flyby" --start 2027-09-01 --end 2027-09-20 --owner lee@aurora.example`

## 3. Missing required input (rule 7)

Before:
```
$ mc login
Error: --email is required
```
After (interactive):
```
$ mc login
Email: lee@aurora.example
Password: ••••••••••••••••
✓ Logged in as Lee Park (Mission Lead, Aurora Space Agency). Session lasts 12 hours.
  Next: mc inbox
```
After (no TTY, e.g. in CI):
```
$ mc login < /dev/null
✗ No email given and no terminal to prompt on. Pass --email and pipe the password on stdin.
```

## 4. Pipe-safe output (rule 11)

Before: `mc missions list > missions.txt` writes `^[[32mactive^[[0m` and spinner frames into the file.

After:
- On a TTY: a coloured table, with a spinner on stderr while loading.
- Piped: a plain table on stdout, with no escape codes.
- `--json`: a stable JSON array.

Detection: `sys.stdout.isatty()` and `"NO_COLOR" not in os.environ`.

## 5. Ctrl+C in an interactive screen (rule 9, terminal mechanics)

Before: pressing Ctrl+C during a full-screen picker kills the process in raw mode. The shell is left with no echo and a hidden cursor, and the user has to type `reset` blind.

After:
```python
try:
    enter_alt_screen(); hide_cursor(); set_raw()
    choice = run_picker()
except KeyboardInterrupt:
    choice = None
finally:
    restore_mode(); show_cursor(); leave_alt_screen()   # every exit path
if choice is None:
    print("Cancelled.", file=sys.stderr); sys.exit(130)
print(f"✓ Selected {choice.name}")                       # after leaving the alt screen
```

## 6. Reaction plus next step (rules 3, 7)

Before:
```
$ mc missions submit 12
$
```
After:
```
$ mc missions submit 12
✓ Lunar Gateway Resupply submitted for approval (needs 2 of Ruth, Marco, Ingrid).
  You'll see it in `mc missions show 12`; Directors see it in `mc inbox`.
```
