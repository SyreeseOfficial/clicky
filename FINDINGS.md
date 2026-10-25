# Clicky: Improvement Ideas

50 ideas, grouped by theme. Each has a size: **S** (<30 min), **M** (an hour or two), **L** (half a day+).
Ideas that conflict with the PRD non-goals are marked **(PRD change)**.

## Top 5 picks (best value for effort)

1. **#1 Global stop hotkey**: stop without focus on the terminal. **M**
2. **#2 Pause/resume**: don't lose the session to a quick interruption. **S**
3. **#12 Fix `time.sleep(0.1)` inside `click()`**: the press hold eats into the interval. **S**
4. **#21 CLI flags** (`--interval 80 --button right --start`): skip the menu. **S**
5. **#31 Presets**: one-key switch between "fishing", "farming", etc. **M**

---

## A. Control and safety

| # | Idea | Size |
|---|---|---|
| 1 | **Global stop hotkey.** Today Ctrl+C only works if the terminal has focus, but the user is in the game. Read a key (e.g. `F8`) from a second `uinput`-sibling: open `/dev/input/event*` keyboards with `evdev`, listen in a thread, set a stop flag. Same `input` group already grants read access. **(PRD change: removes "global hotkeys" non-goal.)** | M |
| 2 | **Pause/resume hotkey.** Same listener as #1; toggles a `paused` flag. Counter and elapsed freeze while paused. | S |
| 3 | **Panic stop on real mouse movement.** If the physical mouse moves or a real button is pressed, stop. Needs the evdev listener from #1, and must ignore its own `clicky` device. | M |
| 4 | **Focus guard (opt-in).** Query `hyprctl activewindow -j` each N clicks; pause when the target window class (e.g. `steam_app_413150`) is not focused. Prevents clicking into a chat window after alt-tab. **(PRD change.)** | M |
| 5 | **Lock-screen guard.** Detect `hyprlock` running (`pgrep`) and stop, so clicks aren't sent into the lock prompt. | S |
| 6 | **Stop on keyboard activity.** Any real keypress (WASD, Esc) stops clicking. Useful when the user returns to the PC. | S (after #1) |
| 7 | **Confirm before unlimited runs with right button.** Right-click spam can be destructive in some apps. Warn once. | S |
| 8 | **Safe-exit on SIGTERM/SIGHUP.** `finally` covers Ctrl+C only. Closing the terminal window leaves the button state to the kernel. Add a `signal` handler that raises `KeyboardInterrupt`. | S |
| 9 | **Idle-inhibit while running.** Wrap the loop with `systemd-inhibit --what=idle` (or a `Popen` of it) so the screen doesn't dim/lock during an AFK session. The PRD defers this; one subprocess line covers it. | S |
| 10 | **Max-clicks "soft landing".** Option to finish the current click and release before exiting on a limit, then ring the terminal bell. | S |

## B. Click engine and accuracy

| # | Idea | Size |
|---|---|---|
| 11 | **Configurable hold time** (`hold_ms`, default 100). The 0.1 s is hard-coded in `click()` after a comment says 40 ms failed. Other games want less. | S |
| 12 | **Fix interval drift.** `click()` sleeps 100 ms, then the loop sleeps `interval_ms` on top, so the real rate is `interval + 100`. At the default 100 ms that's 5 clicks/s, not 10. Subtract the hold from the sleep (or schedule against a monotonic deadline). Also make `interval_ms` mean click-to-click. | S |
| 13 | **Deadline-based scheduling.** Compute `next = t0 + n*interval` so slow iterations don't accumulate error. | S |
| 14 | **Hold-down mode.** Press and hold the button for N seconds (cast charge, mining, tool use). Not just rapid taps. | M |
| 15 | **Double/triple click option.** `clicks_per_burst` with a short gap. | S |
| 16 | **Burst-and-rest pattern.** e.g. click for 30 s, rest 5 s. Looks more natural and cools laggy games. | M |
| 17 | **Middle-click and side buttons.** Declare `BTN_MIDDLE`, `BTN_SIDE`, `BTN_EXTRA` on the device. Trivial, widens use. | S |
| 18 | **Better jitter distribution.** Uniform jitter looks mechanical. Use `random.gauss` clipped to bounds. Also optionally jitter the hold time. | S |
| 19 | **Tiny pointer wobble.** Optional ±1 px motion between clicks to avoid "no movement" detection and keep hover states fresh. | S |
| 20 | **Scroll-wheel mode.** The device already declares `REL_WHEEL`. Offer scroll up/down as an action (list scrolling, zoom). | S |

## C. CLI and UX

| # | Idea | Size |
|---|---|---|
| 21 | **CLI flags.** `clicky --interval 80 --button right --delay 3 --start`. Skips the menu; makes it scriptable and bindable to a Hyprland key. Use `argparse` (stdlib). | S |
| 22 | **Direct-launch shortcut.** `clicky --start` reuses saved config and begins immediately. A one-liner alias for the AFK routine. | S |
| 23 | **Installable command.** `pyproject.toml` with an entry point, or a `~/.local/bin/clicky` symlink step in Setup. Right now it's `python clicky.py` from the repo dir. | S |
| 24 | **Live rate display.** Show actual clicks/s next to the counter. This would have exposed #12 immediately. | S |
| 25 | **Progress toward limits.** If `max_clicks` or `max_duration_s` is set, show `1,204 / 5,000` or a time-remaining countdown. | S |
| 26 | **Beep/notify on finish.** Terminal bell (`\a`) plus `notify-send` when a limit hits or the run stops, since the user is AFK. | S |
| 27 | **Settings: edit-in-place loop.** `settings()` returns after one change; re-entering for each of 7 settings is tedious. Loop until Enter. | S |
| 28 | **Show current settings on the Start screen.** One dim line: `100ms · left · jitter 10% · ∞`. Confirms what's about to run. | S |
| 29 | **Reject bad input with the reason.** "Invalid value." doesn't say why. Show the allowed range from the label. Also `int("1.5")` falls into the same generic error. | S |
| 30 | **Restart last session.** Menu key `R` repeats the previous Start without the countdown prompt re-reading. Handy after a limit stop. | S |

## D. Presets and profiles

| # | Idea | Size |
|---|---|---|
| 31 | **Named presets.** Store a dict of profiles in config (`fishing`, `farming`, `menu-spam`). Menu item to pick one. Config schema: `{"presets": {...}, "active": "fishing"}`. | M |
| 32 | **Per-preset hotkey or flag.** `clicky --preset fishing --start`. Combines #21 and #31. | S (after both) |
| 33 | **Config schema versioning.** Add `"version": 1`. Lets future key renames migrate instead of silently falling back to defaults. | S |
| 34 | **Validate on load.** `load()` merges any JSON verbatim. A hand-edited `"interval_ms": 0` or `"button": "middle"` crashes or misbehaves in the loop. Run the `SETTINGS` validators on load and fall back per-key. | S |
| 35 | **Atomic config save.** Write to a temp file and `os.replace`, so a crash mid-write can't corrupt the config (which currently resets everything silently). | S |
| 36 | **Import/export profile.** `--export fishing.json` / `--import`. Share setups between machines. | S |

## E. Observability

| # | Idea | Size |
|---|---|---|
| 37 | **Session log.** Append start time, duration, clicks, stop reason to `~/.local/share/clicky/history.log`. | S |
| 38 | **Lifetime stats screen.** Total clicks, total time, longest session. Reads the log from #37. | S |
| 39 | **Stop reason in the final line.** `Stopped (Ctrl+C)` vs `Stopped (max clicks)` vs `Stopped (hotkey)`. Currently all say "Stopped." | S |
| 40 | **`--verbose` / `--dry-run`.** Dry-run prints would-be clicks without touching `uinput`. Lets you test settings and CI without permissions. The PRD marked it optional. | S |

## F. Setup and portability

| # | Idea | Size |
|---|---|---|
| 41 | **Distro-aware install.** Setup hard-codes `pacman`. Detect `apt`/`dnf`/`zypper` from `/etc/os-release`, or print the package name when unknown. | M |
| 42 | **Setup dry-run / preview.** Print all `sudo` commands first and ask `y/N`, since the menu entry runs root commands immediately. | S |
| 43 | **Setup status page.** Show a checklist (evdev ✓, udev rule ✓, module loaded ✓, in group ✓, group active in session ✗) before changing anything. Most of the checks already exist in `setup()`. | S |
| 44 | **Detect "group added but not active".** `grp` reads `/etc/group`, not the session. Compare against `os.getgroups()` and tell the user to re-login, instead of letting Start fail with a vague message. | S |
| 45 | **Use `newgrp`/`sg` fallback.** Offer to run the session under `sg input` so first-run works without logging out. | M |
| 46 | **Uninstall step.** Setup has no inverse: remove udev rule, modules-load file, optionally group. Good hygiene. | S |
| 47 | **Fallback backend.** If `/dev/uinput` is blocked but `ydotool` exists, shell out to it. Widens compatibility. | M |

## G. Quality and maintenance

| # | Idea | Size |
|---|---|---|
| 48 | **Move `from evdev import ecodes as e` to one place.** It's imported 4 times inside functions. Lazy import is deliberate (so `--selftest` works without evdev), so use one module-level `try/except ImportError` setting `e = None`. | S |
| 49 | **Test the loop with a fake device.** `click()`/`start()` have no coverage. Inject `ui` (a tiny class with `write/syn/close`) and assert press/release order and that the button is released on interrupt. Keeps the single-file, no-framework style. | M |
| 50 | **Theme cleanup.** The `THEMES` table remaps raw ANSI codes via magic strings (`"1;31"`...). Name the roles (`err`, `warn`, `ok`, `accent`) instead; call sites become readable and themes become 8-line dicts. Also respect `NO_COLOR`. | M |

---

## Suggested order

1. **Correctness first:** #12, #13, #34, #35, #8 (small, fix real bugs).
2. **AFK safety:** #1, #2, #9, #4.
3. **Convenience:** #21, #22, #31, #27.
4. **Everything else** as needed.

## Notes

- #12 is the only finding that makes the tool behave differently from its documentation: the README says "Delay between clicks", but the real period is `interval_ms + 100 ms`.
- #1, #3, #4, #6 all depend on a shared input-listener thread. Build it once.
- Items marked **(PRD change)** contradict stated non-goals; confirm before building.

---

# Round 2 (ideas 51 to 100)

No overlap with round 1. Same size and **(PRD change)** conventions.

## Top 5 picks (round 2)

1. **#51 `uaccess` udev rule**: no `input` group, no re-login. **S**
2. **#64 `clicky toggle` via signal**: bind to a Hyprland key, no input listener needed. **M**
3. **#57 Release both buttons in `finally`**: safety gap today. **S**
4. **#60 Catch `OSError` on write**: clean exit if the compositor restarts. **S**
5. **#91 `.gitignore` for `__pycache__`**: it shows as untracked right now. **S**

## H. Setup and permissions

| # | Idea | Size |
|---|---|---|
| 51 | **`uaccess` rule instead of the `input` group.** Use `KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"`. logind grants the active session access, so no `usermod`, no logout. Removes the biggest first-run hurdle. | S |
| 52 | **`sudo -v` up front.** Setup prompts for the password mid-sequence (and again after a timeout). Authenticate once, then run steps. | S |
| 53 | **Narrow `udevadm trigger`.** Use `--subsystem-match=misc --sysname-match=uinput` instead of re-triggering every device. | S |
| 54 | **Verify the device registered.** After `UInput(...)`, check `clicky` appears in `/proc/bus/input/devices`. If not, print "device created but compositor ignored it" instead of silently clicking nothing. | S |
| 55 | **Rootless Wayland fallback.** Use the virtual-pointer protocol (e.g. `wlrctl pointer click`) when `/dev/uinput` is unavailable. No setup at all on wlroots compositors. | L |
| 56 | **Packaging.** AUR `PKGBUILD` or `pipx`-installable `pyproject.toml`, so `clicky` is a command and `python-evdev` comes as a dependency. | M |

## I. Engine robustness

| # | Idea | Size |
|---|---|---|
| 57 | **Release both buttons on exit.** `finally` only releases the configured button. Release `BTN_LEFT` and `BTN_RIGHT` so a settings mismatch can never leave one stuck. | S |
| 58 | **Persistent virtual device.** Create the `UInput` once per process, not per Start. Skips the 0.3 s wait and stops each run adding a new device to the compositor. | S |
| 59 | **Configurable nudge.** The pointer wiggle is hard-coded (±2 px). Add `nudge_px` (0 = off) for apps where moving the cursor is unwanted. | S |
| 60 | **Handle `OSError` mid-run.** If the device vanishes (compositor restart, suspend/resume), `ui.write` raises and prints a traceback. Catch, report "device lost after N clicks", return to menu. | S |
| 61 | **Throttle the status line.** `print(..., flush=True)` runs every click. At 1-5 ms intervals the terminal becomes the bottleneck. Redraw at about 10 Hz. | S |
| 62 | **Hide the cursor while running.** `\033[?25l` at start, `\033[?25h` in `finally`. Removes the blinking block on the status line. | S |
| 63 | **Precise short intervals.** `time.sleep` overshoots by about 0.1 to 1 ms. For intervals under about 20 ms, sleep coarse then spin the last millisecond. | S |

## J. Remote control without terminal focus

| # | Idea | Size |
|---|---|---|
| 64 | **`clicky toggle` via pidfile + `SIGUSR1`.** A running instance writes `$XDG_RUNTIME_DIR/clicky.pid`; `clicky toggle` signals it. Bind that command to a Hyprland key. Gives a global start/stop with no evdev listener and no new permissions. **(PRD change: global hotkeys.)** | M |
| 65 | **`clicky stop` and `clicky status`.** Same pidfile mechanism. `status` prints running/stopped plus click count. | S |
| 66 | **Hyprland keybind snippet in the README.** `bind = SUPER, F8, exec, clicky toggle`. Depends on #64. | S |
| 67 | **State file for Waybar.** Write `{"clicking": true, "clicks": N}` to the runtime dir so a bar module can show an "autoclicker on" indicator. Prevents forgetting it is running. | M |
| 68 | **Arm mode.** Instead of the countdown, wait for the toggle key, then start. Removes guesswork about the start delay. | M |

## K. Smarter triggers (all PRD changes: screen/focus reading)

| # | Idea | Size |
|---|---|---|
| 69 | **Pixel-color trigger.** Sample the pixel under the cursor with `grim -g` and click only when it matches or changes. A bite indicator becomes a trigger. | L |
| 70 | **Audio trigger.** Watch the PipeWire monitor level (`pw-record` + peak) and click on a loud spike (fish-bite sound). | L |
| 71 | **Frozen-screen watchdog.** Hash a small screenshot region every 30 s. If it never changes, the game likely crashed or disconnected, so stop. | L |
| 72 | **Stop when the game window closes.** Poll `hyprctl clients -j` for the target class; exit cleanly when it is gone. | M |
| 73 | **Per-window profile auto-select.** Map window class to preset (needs #31) so Stardew picks the fishing preset automatically. | M |
| 74 | **Cast-cycle mode.** Hold N s, release, wait M s, tap; repeat. Matches Stardew's cast-then-reel loop better than constant mashing. Builds on #14. | M |

## L. Patterns and macros

| # | Idea | Size |
|---|---|---|
| 75 | **Rate ramp-up.** Start slow and ease to the target interval over N seconds. Gentler on laggy games. | S |
| 76 | **Random micro-breaks.** With small probability, insert a 1 to 5 s pause. Breaks perfectly regular patterns; complements jitter. | S |
| 77 | **Return-to-position.** Record `hyprctl cursorpos` at start and move back before each click, so a bump of the mouse does not move the target. **(PRD change: positioning.)** | M |
| 78 | **Multi-point cycle.** Click a list of positions in turn. Needs #77's absolute positioning. | M |
| 79 | **Macro file.** A tiny text format: `click left`, `wait 500`, `scroll -1`, repeated N times. | M |
| 80 | **Key steps in macros.** Hold or tap keyboard keys (hold W to walk). **(PRD change: keyboard.)** | M |
| 81 | **Scheduling.** `--at 23:30` to start and `--until 07:00` to stop. Pairs well with AFK use. | S |

## M. CLI and UX

| # | Idea | Size |
|---|---|---|
| 82 | **`--help` and `--version`.** Today unknown flags are silently ignored and go to the menu. | S |
| 83 | **Interval units.** Accept `10cps`, `0.1s`, `100ms`. Humans think in clicks per second. | S |
| 84 | **Show effective CPS in Settings.** `Interval: 100 ms (about 10 cps)`. Makes the #12 drift visible. | S |
| 85 | **Enter = Start.** Make an empty menu entry start clicking. Fastest path for the common case. | S |
| 86 | **Enter skips the countdown.** Use `select` on stdin during the delay, so a ready user does not wait 5 s. | S |
| 87 | **Non-interactive `set key=value`.** `clicky set interval_ms=80`, validated by the existing `SETTINGS` validators. | S |
| 88 | **Reset to defaults.** One menu item. A typo in a setting currently needs a hand edit of the JSON file. | S |
| 89 | **Honor `XDG_CONFIG_HOME` and `CLICKY_CONFIG`.** The path is hard-coded to `~/.config`. Useful for tests and dotfile setups. | S |
| 90 | **Timing summary on stop.** Show average interval, min/max and achieved CPS. Confirms jitter and drift behave as configured. | S |

## N. Repo and maintenance

| # | Idea | Size |
|---|---|---|
| 91 | **Add `.gitignore`.** `__pycache__/` is untracked in `git status` now. | S |
| 92 | **CI: run `--selftest`.** One GitHub Action step. The test needs no evdev, so it runs anywhere. | S |
| 93 | **`--doctor` diagnostics.** Print kernel, compositor, evdev version, uinput perms, group state and the device list in a paste-ready block for bug reports. | M |
| 94 | **Factor Setup decisions into a pure function.** `missing_steps(have_evdev, rule_ok, mod_ok, in_group)` returns the list. Selftest can then assert it without sudo. | S |
| 95 | **Python version guard.** Fail with a clear message on old Python instead of a syntax error. | S |
| 96 | **Add a LICENSE.** The README invites cloning but states no terms. | S |
| 97 | **Tag releases and keep a CHANGELOG.** Four commits in, easy to start now. | S |
| 98 | **Remove the global `theme`.** `c()` reads a module global that `main()` and `settings()` both set. Pass it or set it in one place. | S |
| 99 | **Uniform `steps` shape in Setup.** Steps are a mix of lists and tuples with an `isinstance` branch. Use `(cmd, stdin_or_None)` for all. | S |
| 100 | **Document the XWayland caveat.** The pointer nudge and 100 ms hold exist because of game quirks. Put the reasons in the README troubleshooting so future edits don't undo them. | S |

## Suggested order (round 2)

1. **Safety and bugs:** #57, #60, #91.
2. **Friction:** #51, #52, #85, #86.
3. **Global control:** #64, #65, #66.
4. **Everything else** as needed.

## Notes (round 2)

- #51 may make Setup's `usermod` step and the whole re-login warning obsolete. Test it on this machine first.
- #64 gives most of what #1 gives, with far less code. Build one, not both.
- Section K needs screen access. All five contradict the PRD non-goals, so decide before investing.
