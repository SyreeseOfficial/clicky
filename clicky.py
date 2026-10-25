#!/usr/bin/env python3
"""Clicky: terminal autoclicker via uinput. See PRD.md / BUILD.md."""
import grp
import json
import os
import random
import subprocess
import sys
import tempfile
import time

DEFAULTS = {"interval_ms": 100, "button": "left", "start_delay_s": 5,
            "jitter_pct": 0, "max_duration_s": 0, "max_clicks": 0}
CONFIG_PATH = os.path.expanduser("~/.config/clicky/config.json")
UDEV_RULE = "/etc/udev/rules.d/99-uinput.rules"
UDEV_LINE = 'KERNEL=="uinput", GROUP="input", MODE="0660"'
MODULES_CONF = "/etc/modules-load.d/uinput.conf"


def load(path=None):
    try:
        with open(path or CONFIG_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
    except (OSError, ValueError, TypeError):
        return dict(DEFAULTS)


def save(cfg, path=None):
    path = path or CONFIG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


def next_delay(cfg):
    base = cfg["interval_ms"]
    j = base * cfg["jitter_pct"] / 100
    return max(1, random.uniform(base - j, base + j)) / 1000


def limit_hit(cfg, clicks, elapsed_s):
    return bool((cfg["max_clicks"] and clicks >= cfg["max_clicks"])
                or (cfg["max_duration_s"] and elapsed_s >= cfg["max_duration_s"]))


def selftest():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "sub", "config.json")
        assert load(p) == DEFAULTS  # missing file
        cfg = {**DEFAULTS, "interval_ms": 50, "button": "right"}
        save(cfg, p)
        assert load(p) == cfg
        with open(p, "w") as f:
            f.write("{garbage")
        assert load(p) == DEFAULTS  # corrupt file
    for jit in (0, 50):
        c = {**DEFAULTS, "interval_ms": 100, "jitter_pct": jit}
        for _ in range(2000):
            assert 0.1 * (1 - jit / 100) - 1e-9 <= next_delay(c) <= 0.1 * (1 + jit / 100) + 1e-9
    assert next_delay({**DEFAULTS, "interval_ms": 1, "jitter_pct": 100}) >= 0.001
    base = dict(DEFAULTS)
    assert not limit_hit(base, 10**9, 10**9)  # 0 = unlimited
    assert limit_hit({**base, "max_clicks": 5}, 5, 0) and not limit_hit({**base, "max_clicks": 5}, 4, 0)
    assert limit_hit({**base, "max_duration_s": 3}, 0, 3) and not limit_hit({**base, "max_duration_s": 3}, 0, 2.9)
    print("selftest ok")


def check_backend():
    try:
        import evdev  # noqa: F401
    except ImportError:
        return "python-evdev is not installed."
    if not os.access("/dev/uinput", os.W_OK):
        return "/dev/uinput is not writable."
    return None


def make_device():
    from evdev import UInput, ecodes as e
    # both buttons declared: Wayland ignores devices without them
    # REL axes make libinput/SDL classify it as a real mouse, not a button-only device
    return UInput({e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
                   e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL]}, name="clicky")


def click(ui, btn):
    from evdev import ecodes as e
    code = e.BTN_LEFT if btn == "left" else e.BTN_RIGHT
    ui.write(e.EV_KEY, code, 1)
    ui.syn()
    time.sleep(0.1)  # laggy games (SDV + mods) miss short presses; 40ms was too short
    ui.write(e.EV_KEY, code, 0)
    ui.syn()


def c(code, text):  # ANSI color; plain when piped
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def hms(s):
    s = int(s)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def start(cfg):
    err = check_backend()
    if err:
        print(c("1;31", err) + c("33", " Run 3 Setup (then log out/in if it adds you to the input group)."))
        return
    ui = None
    clicks = 0
    t0 = time.monotonic()
    try:
        for n in range(cfg["start_delay_s"], 0, -1):
            print("\r" + c("1;33", f"Starting in {n}s") + c("2", " (Ctrl+C to cancel) "), end="", flush=True)
            time.sleep(1)
        print("\r" + " " * 40 + "\r", end="")
        from evdev import ecodes as e
        ui = make_device()
        time.sleep(0.3)  # let the compositor pick up the new device
        # nudge the pointer: games under XWayland only get clicks after a pointer-enter/motion event
        for dx in (2, -2):
            ui.write(e.EV_REL, e.REL_X, dx)
            ui.syn()
            time.sleep(0.05)
        t0 = time.monotonic()
        while True:
            click(ui, cfg["button"])
            clicks += 1
            elapsed = time.monotonic() - t0
            print(f"\r{c('36', 'clicks:')} {c('1;32', clicks)}  {c('36', 'elapsed:')} {c('1;35', hms(elapsed))}", end="", flush=True)
            if limit_hit(cfg, clicks, elapsed):
                break
            time.sleep(next_delay(cfg))
    except KeyboardInterrupt:
        pass
    finally:
        if ui:
            from evdev import ecodes as e
            ui.write(e.EV_KEY, e.BTN_LEFT if cfg["button"] == "left" else e.BTN_RIGHT, 0)
            ui.syn()
            ui.close()
        print(f"\n{c('1;31', 'Stopped.')} {c('36', 'clicks:')} {c('1;32', clicks)}  {c('36', 'elapsed:')} {c('1;35', hms(time.monotonic() - t0))}")


SETTINGS = [  # key, label, validator
    ("interval_ms", "Interval (ms, >=1)", lambda v: int(v) >= 1),
    ("button", "Button (left/right)", lambda v: v in ("left", "right")),
    ("start_delay_s", "Start delay (s)", lambda v: int(v) >= 0),
    ("jitter_pct", "Jitter (%, 0-100)", lambda v: 0 <= int(v) <= 100),
    ("max_duration_s", "Max duration (s, 0 = none)", lambda v: int(v) >= 0),
    ("max_clicks", "Max clicks (0 = none)", lambda v: int(v) >= 0),
]


def settings(cfg):
    for i, (k, label, _) in enumerate(SETTINGS, 1):
        print(f"  {c('1;33', i)} {label}: {c('1;32', cfg[k])}")
    pick = input("Change which (Enter = back)? ").strip()
    if not pick:
        return
    if not (pick.isdigit() and 1 <= int(pick) <= len(SETTINGS)):
        print(c("1;31", "Invalid choice."))
        return
    k, label, ok = SETTINGS[int(pick) - 1]
    raw = input(f"New {label}: ").strip()
    try:
        if not ok(raw):
            raise ValueError
    except ValueError:
        print(c("1;31", "Invalid value."))
        return
    cfg[k] = raw if k == "button" else int(raw)
    save(cfg)
    print(c("1;32", "Saved."))


def sh(cmd, **kw):
    print(c("2;36", "$ " + " ".join(cmd)))
    return subprocess.run(cmd, **kw).returncode == 0


def setup():
    user = os.environ.get("USER") or os.getlogin()
    try:
        import evdev  # noqa: F401
        have_evdev = True
    except ImportError:
        have_evdev = False
    rule_ok = os.path.exists(UDEV_RULE) and UDEV_LINE in open(UDEV_RULE).read()
    mod_ok = os.path.exists(MODULES_CONF)
    # ponytail: group check reads /etc/group, not the session; re-login still needed
    try:
        in_group = user in grp.getgrnam("input").gr_mem
    except KeyError:
        in_group = False
    steps = []
    if not have_evdev:
        steps.append(["sudo", "pacman", "-S", "--needed", "--noconfirm", "python-evdev"])
    if not rule_ok:
        steps.append(("sudo", "tee", UDEV_RULE, UDEV_LINE + "\n"))
    if not mod_ok:
        steps.append(("sudo", "tee", MODULES_CONF, "uinput\n"))
    steps.append(["sudo", "modprobe", "uinput"])
    if not in_group:
        steps.append(["sudo", "usermod", "-aG", "input", user])
    steps.append(["sudo", "udevadm", "control", "--reload"])
    steps.append(["sudo", "udevadm", "trigger"])
    for s in steps:
        if isinstance(s, tuple):  # tee with content on stdin
            ok = sh(list(s[:3]), input=s[3], text=True, stdout=subprocess.DEVNULL)
        else:
            ok = sh(s)
        if not ok:
            print(c("1;31", "Failed: " + " ".join(s[:3] if isinstance(s, tuple) else s)))
            return
    print(c("1;33", "Log out and back in for the input group to apply."))


def main():
    if "--selftest" in sys.argv:
        return selftest()
    cfg = load()
    while True:
        try:
            choice = input("\n" + "  ".join(c("1;33", n) + " " + c("1;36", t) for n, t in (("1", "Start"), ("2", "Settings"), ("3", "Setup"), ("4", "Quit"))) + "\n" + c("1;32", "> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            start(cfg)
        elif choice == "2":
            settings(cfg)
        elif choice == "3":
            setup()
        elif choice == "4":
            return


if __name__ == "__main__":
    main()
