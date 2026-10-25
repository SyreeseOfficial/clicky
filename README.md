# Clicky

Terminal autoclicker for Linux (Wayland/Hyprland). Sends clicks through a virtual `uinput` device, so it works in games and any window. Python stdlib + `python-evdev` only.

## Requirements

- Linux with `uinput` (tested on Arch/Hyprland)
- Python 3
- `python-evdev` (`sudo pacman -S python-evdev`)

## Start it

1. Clone and enter the repo:
   ```
   git clone https://github.com/SyreeseOfficial/clicky.git
   cd clicky
   ```
2. Run it:
   ```
   python clicky.py
   ```
3. First time only: pick **3 Setup** in the menu. It installs the udev rule, loads `uinput`, and adds you to the `input` group (uses `sudo`).
4. **Log out and back in** so the group applies.
5. Run `python clicky.py`, pick **1 Start**. After the countdown, switch to your target window and put the cursor where you want clicks.
6. **Ctrl+C** stops and returns to the menu.

## Menu

| Key | Action |
|---|---|
| 1 | Start clicking |
| 2 | Settings |
| 3 | Setup (permissions) |
| 4 | Quit |

## Settings

Saved to `~/.config/clicky/config.json`.

| Setting | Default | Meaning |
|---|---|---|
| `interval_ms` | 100 | Delay between clicks (min 1) |
| `button` | left | `left` or `right` |
| `start_delay_s` | 5 | Countdown before clicking |
| `jitter_pct` | 0 | Random ± % on the interval (0 to 100) |
| `max_duration_s` | 0 | Stop after N seconds (0 = unlimited) |
| `max_clicks` | 0 | Stop after N clicks (0 = unlimited) |

## Test

```
python clicky.py --selftest
```

Prints `selftest ok`.

## Troubleshooting

- `PermissionError` on `/dev/uinput`: re-login not done, or run **Setup** again.
- Clicks work on desktop but not in-game: check the game window has focus.

See `PRD.md` and `BUILD.md` for design and build notes.
