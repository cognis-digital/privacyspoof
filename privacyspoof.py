#!/usr/bin/env python3
"""privacyspoof — pick consistent spoofing presets and emit configs."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(p):
    path = HERE / p
    if not path.exists():
        print(f"error: data file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: malformed JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def cmd_ua(a):
    data = _load("spoof/user-agents.json")
    uas = data.get("user_agents")
    if not uas:
        print("error: user-agents.json has no 'user_agents' list", file=sys.stderr)
        sys.exit(2)
    hits = [
        u for u in uas
        if (not a.browser or a.browser.lower() in u.get("browser", "").lower())
        and (not a.os or a.os.lower() in u.get("os", "").lower())
    ]
    print(json.dumps(hits if hits else uas, indent=2))


def cmd_geo(a):
    data = _load("spoof/geolocation.json")
    presets = data.get("presets")
    if not presets:
        print("error: geolocation.json has no 'presets' list", file=sys.stderr)
        sys.exit(2)
    hit = next((p for p in presets if p.get("city") == a.city), None)
    print(json.dumps(hit if hit is not None else presets, indent=2))


def cmd_filters(a):
    path = HERE / "filters/adguard-base.txt"
    if not path.exists():
        print(f"error: filter file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read filter file: {exc}", file=sys.stderr)
        sys.exit(2)
    if not txt.strip():
        print("error: filter file is empty", file=sys.stderr)
        sys.exit(2)
    print(txt)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="privacyspoof")
    sub = ap.add_subparsers(dest="cmd", required=True)

    u = sub.add_parser("ua")
    u.add_argument("--os")
    u.add_argument("--browser")
    u.set_defaults(f=cmd_ua)

    g = sub.add_parser("geo")
    g.add_argument("--city", default="new_york")
    g.set_defaults(f=cmd_geo)

    fl = sub.add_parser("filters")
    fl.add_argument("--format", default="adguard")
    fl.set_defaults(f=cmd_filters)

    a = ap.parse_args(argv)
    try:
        return a.f(a)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
