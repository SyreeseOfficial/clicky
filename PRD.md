# Clicky PRD

## Goal
Terminal autoclicker for Omarchy (Arch, Hyprland/Wayland) so the user can go AFK while fishing in Stardew Valley.

## Environment (verified)
- Wayland session, Hyprland 0.56.2
- No ydotool/xdotool installed; `/dev/uinput` is `root:root 600`; user `sy` is not in `input` group
- `python3` present; `python-evdev` not installed; `wtype` present (keyboard only, unused)
- Game: Stardew Valley, borderless windowed, launch method unknown (irrelevant to tool)

## Decisions (from interview)
| Area | Decision |
|---|---|
| Interface | CLI only, numbered text menu, Ctrl+C stops |
| Language | Python, stdlib + `python-evdev` only |
| Backend | `python-evdev` writing to `/dev/uinput`, access via udev rule |
| Button | Left default; right selectable in settings |
| Target | Wherever the cursor is now (no positioning) |
| Click style | Rapid discrete press+release |
| Interval | Configurable in menu (default 100 ms) |
| Start delay | Configurable in menu (default 5 s) |
| Jitter | Optional, off by default (percent of interval) |
| Limits | Optional max duration and optional max clicks; default unlimited |
| Persistence | Config file `~/.config/clicky/config.json` |
| Live output | One updating line: click count + elapsed time |
| Focus guard | None, always clicks |
| Idle lock | Not handled; uinput events count as input. Revisit if screen locks |
| Use case | Fishing; plain rapid clicks, no cast-hold, no minigame logic |
| Keyboard | Out of scope |
| Kill switch | Ctrl+C only |
| Missing perms | `setup` menu item runs the sudo steps |
| Testing | One small self-check, no frameworks |
| Location | `~/Documents/Code/clicky` |

## Functional requirements
1. `clicky` launches a menu: **1 Start**, **2 Settings**, **3 Setup**, **4 Quit**.
2. **Settings** edits: interval (ms), button (left/right), start delay (s), jitter (% , 0 = off), max duration (s, 0 = none), max clicks (0 = none). Saved to config on change.
3. **Start**: countdown for start delay (user alt-tabs to game), then clicks at cursor until Ctrl+C or a limit hits. Prints `clicks: N  elapsed: HH:MM:SS` on one line, updated in place.
4. **Setup**: installs `python-evdev` (pacman), writes a udev rule granting access to `/dev/uinput` (e.g. `KERNEL=="uinput", GROUP="input", MODE="0660"`), adds user to `input` group, loads `uinput` module. Prints that logout/login is needed.
5. On Start, if `/dev/uinput` is not writable or `evdev` is missing, print a clear message pointing to Setup and return to the menu.
6. Ctrl+C always exits the click loop cleanly (button released, device closed).

## Non-goals
Screen reading, fishing minigame logic, cast-hold timing, keyboard keys, global hotkeys, focus detection, GUI, tray widget.

## Structure
Single file `clicky.py` (+ `PRD.md`). Self-check via `python clicky.py --selftest` (config load/save round-trip, interval-with-jitter bounds, limit logic). Optional `--dry-run` not required.

## Acceptance
- After Setup and re-login, Start clicks left button at the cursor at the configured rate inside Stardew.
- Settings survive restart.
- Ctrl+C stops within one interval, no stuck button.
- `--selftest` passes.

## Risks
- Group change needs re-login; Setup must say so.
- Plain mashing will fail many fishing minigames (accepted).
- Wayland compositors may ignore uinput devices lacking proper capabilities; device must declare `BTN_LEFT`/`BTN_RIGHT`.
