import argparse
import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("tv", ROOT / "tools" / "tv.py")
tv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tv)


class FakeTV:
    """In-memory TV. `locked` keys accept writes but keep their value, like a firmware that blocks them."""

    host = "10.0.0.2"

    def __init__(self, settings, locked=()):
        self.settings = {cat: dict(keys) for cat, keys in settings.items()}
        self.locked = set(locked)
        self.writes = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def info(self):
        return {"system": {"modelName": "65UP7000PUA"},
                "software": {"product_name": "webOSTV 6.0", "major_ver": "03", "minor_ver": "33.80"}}

    async def apps(self):
        return [{"id": "netflix", "title": "Netflix"}]

    async def get(self, category, keys):
        have = self.settings.get(category, {})
        return {k: have[k] for k in keys if k in have}

    async def set(self, category, settings):
        self.writes.append((category, dict(settings)))
        for key, value in settings.items():
            if (category, key) not in self.locked:
                self.settings.setdefault(category, {})[key] = value


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch, tmp_path):
    async def instant(_):
        pass
    monkeypatch.setattr(tv.asyncio, "sleep", instant)
    monkeypatch.setattr(tv, "BACKUP_DIR", tmp_path / "backups")


def stock_tv(**kw):
    return FakeTV({
        "general": {"homePromotion": "on", "homeAutoLaunch": "on", "customizedAd": "on",
                    "adCookie": "on", "lmt": "off", "doNotSellMyPersonalInformation": "off",
                    "screenSaverAd": "on", "aiNudge": "on", "welcomeFeature": "on"},
        # promotionStreamer missing: not every firmware reports every key.
        "option": {"livePlus": "on", "livePromotion": "on", "enableToastPopup": "on", "quickStartMode": "on"},
        "": {"eulaStatus": {"acrAllowed": True, "generalTermsAllowed": True, "voiceAllowed": False}},
    }, **kw)


def profile():
    return tv.load_profile(tv.DEFAULT_PROFILE)


def args(**kw):
    defaults = {"dry_run": False, "optional": False, "fix": False}
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def run(coro):
    return asyncio.run(coro)


def test_profile_parses_and_marks_optional():
    p = profile()
    assert p["option"]["livePlus"]["value"] == "off"
    assert p["option"]["quickStartMode"]["optional"]
    assert "quickStartMode" not in tv.targets(p)["option"]
    assert "quickStartMode" in tv.targets(p, include_optional=True)["option"]


def test_profile_rejects_key_without_value(tmp_path):
    bad = tmp_path / "p.json"
    bad.write_text(json.dumps({"settings": {"general": {"x": {"why": "no value"}}}}))
    with pytest.raises(ValueError):
        tv.load_profile(bad)


def test_diff_splits_changes_and_missing():
    changes, missing = tv.diff({"a": {"x": 1, "y": 2, "z": 3}}, {"a": {"x": 1, "y": 5}})
    assert changes == {"a": {"y": (5, 2)}}
    assert missing == [("a", "z")]


def test_parse_value():
    assert tv.parse_value("off") == "off"
    assert tv.parse_value("true") is True
    assert tv.parse_value('{"value": "off"}') == {"value": "off"}


def test_dry_run_writes_nothing():
    fake = stock_tv()
    run(tv.cmd_apply(fake, args(dry_run=True), profile()))
    assert fake.writes == []
    assert not tv.BACKUP_DIR.exists()


def test_apply_backs_up_then_applies_required_only():
    fake = stock_tv()
    assert run(tv.cmd_apply(fake, args(), profile())) is None
    assert fake.settings["option"]["livePlus"] == "off"
    assert fake.settings["general"]["lmt"] == "on"
    assert fake.settings["option"]["quickStartMode"] == "on"  # optional, untouched
    assert "promotionStreamer" not in fake.settings["option"]  # missing keys are skipped, not created
    backups = list(tv.BACKUP_DIR.glob("before-apply-*.json"))
    assert len(backups) == 1
    saved = json.loads(backups[0].read_text())
    assert saved["settings"]["option"]["livePlus"] == "on"
    assert saved["eula"]["eulaStatus"]["acrAllowed"] is True


def test_apply_reports_settings_that_dont_stick(capsys):
    fake = stock_tv(locked={("option", "livePlus")})
    assert run(tv.cmd_apply(fake, args(), profile())) == 1
    assert "option.livePlus" in capsys.readouterr().out


def test_backup_then_restore_round_trip():
    fake = stock_tv()
    original = json.loads(json.dumps(fake.settings))
    path = run(tv.write_backup(fake, profile()))
    run(tv.cmd_apply(fake, args(optional=True), profile()))
    assert fake.settings != original
    run(tv.cmd_restore(fake, argparse.Namespace(backup=str(path)), profile()))
    assert fake.settings == original


def test_check_flags_drift_and_fix_repairs_it():
    fake = stock_tv()
    run(tv.cmd_apply(fake, args(), profile()))
    fake.settings["option"]["livePlus"] = "on"  # a firmware update turned it back on
    assert run(tv.cmd_check(fake, args(), profile())) == 1
    assert run(tv.cmd_check(fake, args(fix=True), profile())) is None
    assert fake.settings["option"]["livePlus"] == "off"
    assert run(tv.cmd_check(fake, args(), profile())) is None


def test_check_ignores_optional_drift():
    fake = stock_tv()
    run(tv.cmd_apply(fake, args(), profile()))
    assert fake.settings["option"]["quickStartMode"] == "on"
    assert run(tv.cmd_check(fake, args(), profile())) is None


def test_privacy_lists_accepted_tracking_agreements(capsys):
    run(tv.cmd_privacy(stock_tv(), args(), profile()))
    out = capsys.readouterr().out
    assert "acrAllowed" in out
    assert "voiceAllowed" not in out
    assert "generalTermsAllowed" not in out


def test_set_command_writes_and_verifies():
    fake = stock_tv()
    a = argparse.Namespace(category="general", pairs=["homeEffect=off"])
    assert run(tv.cmd_set(fake, a, profile())) is None
    assert fake.settings["general"]["homeEffect"] == "off"


def test_key_store_round_trip(tmp_path):
    store = tv.JsonKeyStore(tmp_path / "cfg" / "keys.json")
    assert run(store.get_key("10.0.0.2")) is None
    run(store.set_key("10.0.0.2", "abc"))
    assert run(store.get_key("10.0.0.2")) == "abc"
    assert (tmp_path / "cfg" / "keys.json").stat().st_mode & 0o777 == 0o600


def test_main_requires_host(monkeypatch):
    monkeypatch.delenv("TV_HOST", raising=False)
    with pytest.raises(SystemExit):
        tv.main(["probe"])
