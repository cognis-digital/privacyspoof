"""Tests for privacyspoof hardening: edge cases and error paths."""
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure repo root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "integrations"))

import privacyspoof  # noqa: E402
from webhook import _validate_url, _parse_header, main as webhook_main  # noqa: E402


# ---------------------------------------------------------------------------
# privacyspoof.py — _load helper
# ---------------------------------------------------------------------------

def test_load_missing_file_exits_2(tmp_path, monkeypatch):
    """_load should exit with code 2 when the data file is absent."""
    monkeypatch.setattr(privacyspoof, "HERE", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof._load("does_not_exist.json")
    assert exc_info.value.code == 2


def test_load_malformed_json_exits_2(tmp_path, monkeypatch):
    """_load should exit with code 2 for invalid JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }", encoding="utf-8")
    monkeypatch.setattr(privacyspoof, "HERE", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof._load("bad.json")
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# cmd_ua — filter and fallback
# ---------------------------------------------------------------------------

def test_cmd_ua_no_match_returns_all(capsys, monkeypatch):
    """When no UA matches the filter, the full list is returned."""
    fake_data = {
        "user_agents": [
            {"id": "a", "os": "Windows", "browser": "Chrome"},
            {"id": "b", "os": "macOS", "browser": "Safari"},
        ]
    }
    monkeypatch.setattr(privacyspoof, "_load", lambda p: fake_data)

    class Args:
        browser = "nonexistent_browser_xyz"
        os = None

    privacyspoof.cmd_ua(Args())
    out = capsys.readouterr().out
    result = json.loads(out)
    assert len(result) == 2


def test_cmd_ua_filter_works(capsys, monkeypatch):
    """browser filter should narrow results."""
    fake_data = {
        "user_agents": [
            {"id": "a", "os": "Windows", "browser": "Chrome"},
            {"id": "b", "os": "macOS", "browser": "Safari"},
        ]
    }
    monkeypatch.setattr(privacyspoof, "_load", lambda p: fake_data)

    class Args:
        browser = "chrome"
        os = None

    privacyspoof.cmd_ua(Args())
    out = capsys.readouterr().out
    result = json.loads(out)
    assert len(result) == 1
    assert result[0]["id"] == "a"


def test_cmd_ua_missing_key_exits_2(monkeypatch):
    """cmd_ua exits 2 when user_agents key is absent."""
    monkeypatch.setattr(privacyspoof, "_load", lambda p: {})
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof.cmd_ua(type("A", (), {"browser": None, "os": None})())
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# cmd_geo — city lookup and fallback
# ---------------------------------------------------------------------------

def test_cmd_geo_known_city(capsys, monkeypatch):
    """A known city key returns exactly that preset."""
    fake_data = {
        "presets": [
            {"city": "new_york", "lat": 40.7, "lon": -74.0},
            {"city": "london", "lat": 51.5, "lon": -0.1},
        ]
    }
    monkeypatch.setattr(privacyspoof, "_load", lambda p: fake_data)

    class Args:
        city = "new_york"

    privacyspoof.cmd_geo(Args())
    out = capsys.readouterr().out
    result = json.loads(out)
    assert result["city"] == "new_york"


def test_cmd_geo_unknown_city_returns_all(capsys, monkeypatch):
    """An unknown city falls back to all presets."""
    fake_data = {
        "presets": [
            {"city": "new_york"},
            {"city": "london"},
        ]
    }
    monkeypatch.setattr(privacyspoof, "_load", lambda p: fake_data)

    class Args:
        city = "atlantis"

    privacyspoof.cmd_geo(Args())
    out = capsys.readouterr().out
    result = json.loads(out)
    assert isinstance(result, list)
    assert len(result) == 2


def test_cmd_geo_missing_key_exits_2(monkeypatch):
    """cmd_geo exits 2 when presets key is absent."""
    monkeypatch.setattr(privacyspoof, "_load", lambda p: {})
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof.cmd_geo(type("A", (), {"city": "x"})())
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# cmd_filters — file read errors
# ---------------------------------------------------------------------------

def test_cmd_filters_missing_file_exits_2(tmp_path, monkeypatch):
    """cmd_filters exits 2 when adguard-base.txt is not present."""
    monkeypatch.setattr(privacyspoof, "HERE", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof.cmd_filters(type("A", (), {"format": "adguard"})())
    assert exc_info.value.code == 2


def test_cmd_filters_empty_file_exits_2(tmp_path, monkeypatch):
    """cmd_filters exits 2 when adguard-base.txt is empty."""
    filters_dir = tmp_path / "filters"
    filters_dir.mkdir()
    (filters_dir / "adguard-base.txt").write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(privacyspoof, "HERE", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof.cmd_filters(type("A", (), {"format": "adguard"})())
    assert exc_info.value.code == 2


def test_cmd_filters_valid_file(tmp_path, monkeypatch, capsys):
    """cmd_filters prints filter content when file is valid."""
    filters_dir = tmp_path / "filters"
    filters_dir.mkdir()
    content = "||example.com^\n||tracker.net^"
    (filters_dir / "adguard-base.txt").write_text(content, encoding="utf-8")
    monkeypatch.setattr(privacyspoof, "HERE", tmp_path)
    privacyspoof.cmd_filters(type("A", (), {"format": "adguard"})())
    out = capsys.readouterr().out
    assert "||example.com^" in out


# ---------------------------------------------------------------------------
# main() — CLI integration
# ---------------------------------------------------------------------------

def test_main_no_subcommand_exits_nonzero():
    """No subcommand should exit non-zero (argparse handles this)."""
    with pytest.raises(SystemExit) as exc_info:
        privacyspoof.main([])
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# webhook.py — _validate_url
# ---------------------------------------------------------------------------

def test_validate_url_rejects_ftp():
    with pytest.raises(SystemExit) as exc_info:
        _validate_url("ftp://example.com/data")
    assert exc_info.value.code == 2


def test_validate_url_rejects_no_host():
    with pytest.raises(SystemExit) as exc_info:
        _validate_url("https://")
    assert exc_info.value.code == 2


def test_validate_url_accepts_https():
    # Should not raise
    _validate_url("https://hooks.example.com/webhook")


# ---------------------------------------------------------------------------
# webhook.py — _parse_header
# ---------------------------------------------------------------------------

def test_parse_header_valid():
    k, v = _parse_header("Authorization: Bearer token123")
    assert k == "Authorization"
    assert v == "Bearer token123"


def test_parse_header_no_colon_exits_2():
    with pytest.raises(SystemExit) as exc_info:
        _parse_header("BadHeaderWithoutColon")
    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# webhook.py — main() stdin validation
# ---------------------------------------------------------------------------

def test_webhook_main_empty_stdin_returns_2(monkeypatch):
    with patch("sys.argv", ["webhook.py", "--url", "https://example.com"]):
        monkeypatch.setattr("sys.stdin", StringIO("   "))
        result = webhook_main()
    assert result == 2


def test_webhook_main_invalid_json_stdin_returns_2(monkeypatch):
    with patch("sys.argv", ["webhook.py", "--url", "https://example.com"]):
        monkeypatch.setattr("sys.stdin", StringIO("not valid json {{{"))
        result = webhook_main()
    assert result == 2
