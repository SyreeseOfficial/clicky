# Clicky Build Instructions

Source of truth: `PRD.md`. Single file: `clicky.py`. Stdlib + `python-evdev` only.

Do phases in order. Each ends with a **Done when** check. Don't start the next phase until it passes.

| # | Phase | Est. |
|---|---|---|
| 1 | Permissions bootstrap | 10 min |
| 2 | Config + selftest | 20 min |
| 3 | Click engine | 20 min |
| 4 | Menu + Settings | 20 min |
| 5 | Start loop | 30 min |
| 6 | Setup menu item | 15 min |
| 7 | Acceptance in Stardew | 15 min |

---

## Phase 1: Permissions bootstrap (manual, before any code)

Proves the backend works. Do this by hand first; Phase 6 automates it.

- [ ] `sudo pacman -S python-evdev`
- [ ] `echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules`
- [ ] `echo uinput | sudo tee /etc/modules-load.d/uinput.conf && sudo modprobe uinput`
- [ ] `sudo usermod -aG input $USER`
- [ ] `sudo udevadm control --reload && sudo udevadm trigger`
- [ ] Log out, log back in

**Done when:** `id` lists `input` and `ls -l /dev/uinput` shows `crw-rw---- root input`.

Keep the exact commands: Phase 6 reuses them.

---

## Phase 2: Config + selftest

Create `clicky.py` with:

- `DEFAULTS = {interval_ms: 100, button: "left", start_delay_s: 5, jitter_pct: 0, max_duration_s: 0, max_clicks: 0}`
- `CONFIG_PATH = ~/.config/clicky/config.json`
- `load()`: read file, merge over `DEFAULTS`; missing/corrupt file returns defaults.
- `save(cfg)`: `mkdir -p` the dir, write JSON.
- `next_delay(cfg)`: seconds to sleep; `interval_ms` ± `jitter_pct`% uniform, never below 1 ms.
- `limit_hit(cfg, clicks, elapsed_s)`: True if `max_clicks` or `max_duration_s` is non-zero and reached.
- `--selftest` arg: asserts config round-trip (use a temp path), `next_delay` bounds over many samples (jitter 0 and 50), `limit_hit` for each limit and for 0 = unlimited. Prints `selftest ok`, exits 0.

**Done when:** `python clicky.py --selftest` prints `selftest ok`.

---

## Phase 3: Click engine

- `make_device()`: `evdev.UInput({EV_KEY: [BTN_LEFT, BTN_RIGHT]}, name="clicky")`. Must declare both buttons (PRD risk: Wayland ignores devices without them).
- `click(ui, btn)`: write press, `syn`, write release, `syn`.
- Preflight `check_backend()`: returns an error string if `import evdev` fails or `/dev/uinput` is not writable (`os.access(..., os.W_OK)`); else `None`.

**Done when:** in a scratch script, `click` 3 times with cursor over a text editor: 3 clicks register (e.g. `wev` or `hyprctl` shows them, or a button click counter increments).

---

## Phase 4: Menu + Settings

- Main loop: print `1 Start  2 Settings  3 Setup  4 Quit`, read choice, dispatch. Invalid input re-prompts.
- Settings screen: list the 6 values with numbers; pick one, enter a new value, validate (ints >= 0, interval >= 1, button in {left,right}, jitter 0 to 100), `save()` immediately, return to the menu.
- Stub Start and Setup as "not implemented".

**Done when:** change interval to 50, quit, relaunch: Settings shows 50 and `~/.config/clicky/config.json` contains it.

---

## Phase 5: Start loop

1. Run `check_backend()`. On error: print the message, point to **Setup**, return to menu.
2. Countdown `start_delay_s` to 0, one updating line.
3. Open device. Loop: `click`, update `clicks: N  elapsed: HH:MM:SS` in place (`\r`), `sleep(next_delay(cfg))`, break if `limit_hit`.
4. Wrap in `try/finally`: catch `KeyboardInterrupt`, send a release for the button, `ui.close()`, print a final summary line, return to menu.
5. Use `time.monotonic()` for elapsed.

**Done when:**
- With `max_clicks=20` it stops at exactly 20.
- With `max_duration_s=5` it stops at ~5 s.
- Ctrl+C mid-run returns to the menu with no stuck button (mouse behaves normally after).

---

## Phase 6: Setup menu item

Run the Phase 1 commands via `subprocess.run` with `sudo`, printing each step before running it. Stop on first failure with the failing command shown. Skip steps already satisfied where cheap (e.g. rule file exists). Finish with: `Log out and back in for the input group to apply.`

**Done when:** on a clean state (remove the rule file, `sudo gpasswd -d $USER input`), Setup recreates everything and prints the re-login notice. Don't skip this test: it's the only coverage for this phase.

---

## Phase 7: Acceptance (matches PRD)

- [ ] Stardew running borderless; Start, alt-tab, cursor on the fishing target: clicks land at the configured rate.
- [ ] Settings survive restart.
- [ ] Ctrl+C stops within one interval, no stuck button.
- [ ] `python clicky.py --selftest` passes.

**Done when:** all four boxes are checked.

---

## Out of scope (don't build)

Screen reading, minigame logic, cast-hold, keyboard keys, global hotkeys, focus detection, GUI/tray, positioning, extra files or test frameworks.

## If something breaks

- Clicks do nothing in-game but work on desktop: check Hyprland input and the game window focus.
- `PermissionError` on `/dev/uinput`: re-login not done, or the udev rule didn't reload (Phase 1).
- Device ignored by the compositor: confirm both `BTN_LEFT` and `BTN_RIGHT` are declared (Phase 3).
