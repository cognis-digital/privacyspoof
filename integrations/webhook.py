#!/usr/bin/env python3
"""Minimal, dependency-free webhook forwarder for Cognis findings.

Reads JSON findings on stdin and POSTs them to a URL (SIEM/Slack/Jira bridge).
Usage:  <tool> scan . --format json | python integrations/webhook.py --url URL
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.parse


def _validate_url(url: str) -> None:
    """Reject obviously invalid or non-HTTP(S) URLs early."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as exc:
        print(f"error: cannot parse URL: {exc}", file=sys.stderr)
        sys.exit(2)
    if parsed.scheme not in ("http", "https"):
        print(
            f"error: URL scheme must be http or https, got {parsed.scheme!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    if not parsed.netloc:
        print("error: URL has no host", file=sys.stderr)
        sys.exit(2)


def _parse_header(raw: str) -> tuple[str, str]:
    """Split a 'Key: Value' header string, exiting cleanly on bad input."""
    k, sep, v = raw.partition(":")
    if not sep or not k.strip():
        print(
            f"error: malformed --header {raw!r}; expected 'Key: Value'",
            file=sys.stderr,
        )
        sys.exit(2)
    return k.strip(), v.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--header", action="append", default=[], help="Key: Value")
    args = ap.parse_args()

    _validate_url(args.url)

    raw_stdin = sys.stdin.read()
    if not raw_stdin.strip():
        print("error: no input received on stdin", file=sys.stderr)
        return 2

    # Validate the payload is valid JSON before sending.
    try:
        json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        print(f"error: stdin is not valid JSON: {exc}", file=sys.stderr)
        return 2

    payload = raw_stdin.encode("utf-8")
    req = urllib.request.Request(args.url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    for h in args.header:
        k, v = _parse_header(h)
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"posted {len(payload)} bytes -> {r.status}")
        return 0
    except Exception as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
