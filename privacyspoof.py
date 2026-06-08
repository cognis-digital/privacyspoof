#!/usr/bin/env python3
"""privacyspoof — pick consistent spoofing presets and emit configs."""
import argparse, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent

def _load(p): return json.loads((HERE / p).read_text(encoding="utf-8"))

def cmd_ua(a):
    uas = _load("spoof/user-agents.json")["user_agents"]
    hits = [u for u in uas if (not a.browser or a.browser.lower() in u["browser"].lower())
            and (not a.os or a.os.lower() in u["os"].lower())]
    print(json.dumps(hits or uas, indent=2))

def cmd_geo(a):
    presets = _load("spoof/geolocation.json")["presets"]
    hit = next((p for p in presets if p["city"] == a.city), None)
    print(json.dumps(hit or presets, indent=2))

def cmd_filters(a):
    txt = (HERE / "filters/adguard-base.txt").read_text(encoding="utf-8")
    print(txt)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="privacyspoof")
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("ua"); u.add_argument("--os"); u.add_argument("--browser"); u.set_defaults(f=cmd_ua)
    g = sub.add_parser("geo"); g.add_argument("--city", default="new_york"); g.set_defaults(f=cmd_geo)
    fl = sub.add_parser("filters"); fl.add_argument("--format", default="adguard"); fl.set_defaults(f=cmd_filters)
    a = ap.parse_args(argv); return a.f(a)

if __name__ == "__main__":
    sys.exit(main())
