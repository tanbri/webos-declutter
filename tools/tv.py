#!/usr/bin/env python3
"""Talk to an LG webOS TV over the local network and turn off its ads and tracking.

webOS has no ADB and no way to disable apps without root, so this tool works
through the TV's own remote-control API (SSAP, the WebSocket the LG ThinQ app
uses). It reads and writes system settings, lists apps, and backs up and
restores everything it touches.

Usage (TV_HOST=<tv ip> or --host <tv ip>):
    tv.py probe                      connect, pair, print model/firmware and profile state
    tv.py apps                       list installed apps
    tv.py get <category> <key>...    read settings
    tv.py set <category> key=value.. write settings (JSON values allowed)
    tv.py call <ssap uri> [json]     raw SSAP request, e.g. ssap://system/getSystemInfo
    tv.py backup                     save current values of every profile key
    tv.py apply [--dry-run]          back up, then apply the profile and verify
    tv.py restore <backup.json>      put backed-up values back
    tv.py check [--fix]              show drift from the profile (e.g. after a firmware update)
    tv.py privacy                    report ad/tracking settings and user agreements
"""

import argparse
import asyncio
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "profiles" / "lg-65up7000pua-webos6" / "settings.json"
BACKUP_DIR = ROOT / "backups"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "cleanyourlgtv"

# User agreements live in the unnamed ("") settings category on webOS 6.
EULA_CATEGORY = ""
EULA_KEY = "eulaStatus"
# Agreements that feed ads, ACR or profiling. Users can withdraw them on the TV:
# Settings > General > System > Additional Settings > User Agreements.
EULA_TRACKING = [
    "acrAllowed", "acrAdAllowed", "acrOnAllowed", "customAdAllowed", "customadsAllowed",
    "cookiesAllowed", "marketingOnAllowed", "thirdPartySharingAllowed",
    "additionalDataAllowed", "voiceAllowed", "voice2Allowed", "shoppingOnAllowed",
]


# ---------------------------------------------------------------- profiles

def load_profile(path):
    """Return {category: {key: {"value": v, "why": str, "optional": bool}}}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for category, keys in data["settings"].items():
        out[category] = {}
        for key, spec in keys.items():
            if not isinstance(spec, dict) or "value" not in spec:
                raise ValueError(f"{path}: {category}.{key} needs a \"value\"")
            out[category][key] = {
                "value": spec["value"],
                "why": spec.get("why", ""),
                "optional": bool(spec.get("optional", False)),
            }
    return out


def targets(profile, include_optional=False):
    """Return {category: {key: value}} for the keys to apply."""
    return {
        cat: {k: s["value"] for k, s in keys.items() if include_optional or not s["optional"]}
        for cat, keys in profile.items()
    }


def diff(want, have):
    """Compare {cat: {key: value}} maps. Returns (changes, missing).

    changes: {cat: {key: (current, wanted)}} for keys the TV reports with another value.
    missing: [(cat, key)] for keys this TV/firmware does not report at all.
    """
    changes, missing = {}, []
    for cat, keys in want.items():
        current = have.get(cat, {})
        for key, value in keys.items():
            if key not in current:
                missing.append((cat, key))
            elif current[key] != value:
                changes.setdefault(cat, {})[key] = (current[key], value)
    return changes, missing


def parse_value(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


# ---------------------------------------------------------------- TV access

class JsonKeyStore:
    """Stores the pairing key per TV in ~/.config/cleanyourlgtv/keys.json (bscpylgtv StorageProto)."""

    def __init__(self, path):
        self.path = Path(path)

    def _load(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    async def set_key(self, key, val):
        data = self._load()
        data[key] = val
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.chmod(self.path, 0o600)

    async def get_key(self, key):
        return self._load().get(key)

    async def list_keys(self):
        return self._load()


class LGTV:
    """Thin wrapper over bscpylgtv so the rest of the tool can be tested with a fake."""

    def __init__(self, host):
        self.host = host
        self.client = None

    async def __aenter__(self):
        from bscpylgtv import WebOsClient

        self.client = await WebOsClient.create(
            self.host,
            storage=JsonKeyStore(CONFIG_DIR / "keys.json"),
            states=[],
            timeout_connect=5,
            connect_retry_attempts=3,
        )
        if not self.client.is_registered():
            print(f"Connecting to {self.host}. First time: accept the pairing prompt on the TV with the remote.",
                  file=sys.stderr)
        await self.client.connect()
        return self

    async def __aexit__(self, *exc):
        await self.client.disconnect()

    async def info(self):
        system = await self.client.get_system_info()
        software = await self.client.get_software_info()
        return {"system": system, "software": software}

    async def apps(self):
        """Return [{"id", "title"}] for every app on the home bar."""
        points = await self.client.get_apps() or []
        return [{"id": a.get("id"), "title": a.get("title")} for a in points]

    async def get(self, category, keys):
        """Read keys; keys the TV doesn't know are simply absent from the result."""
        from bscpylgtv import PyLGTVCmdException

        try:
            res = await self.client.get_system_settings(category, list(keys))
            return dict(res.get("settings", {}))
        except PyLGTVCmdException:
            # One unknown key can fail the whole request; fall back to one at a time.
            out = {}
            for key in keys:
                try:
                    res = await self.client.get_system_settings(category, [key])
                    out.update(res.get("settings", {}))
                except PyLGTVCmdException:
                    pass
            return out

    async def set(self, category, settings):
        # Goes through the luna settings service; it returns no result, so callers re-read to verify.
        await self.client.set_settings(category, settings)

    async def call(self, uri, payload):
        return await self.client.request(uri.replace("ssap://", "", 1), payload)


async def read_all(tv, want):
    return {cat: await tv.get(cat, list(keys)) for cat, keys in want.items()}


# ---------------------------------------------------------------- commands

async def write_backup(tv, profile, label="backup"):
    want = targets(profile, include_optional=True)
    data = {
        "taken": dt.datetime.now().isoformat(timespec="seconds"),
        "host": tv.host,
        "settings": await read_all(tv, want),
        "eula": await tv.get(EULA_CATEGORY, [EULA_KEY]),
        "apps": await tv.apps(),
    }
    BACKUP_DIR.mkdir(exist_ok=True)
    path = BACKUP_DIR / f"{label}-{dt.datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Backed up {sum(len(v) for v in data['settings'].values())} settings to {path}")
    return path


async def apply_changes(tv, changes):
    """Write changes, re-read, and return {cat: {key: (now, wanted)}} for anything that didn't stick."""
    for cat, keys in changes.items():
        await tv.set(cat, {k: wanted for k, (_, wanted) in keys.items()})
    await asyncio.sleep(1)
    want = {cat: {k: wanted for k, (_, wanted) in keys.items()} for cat, keys in changes.items()}
    failed, _ = diff(want, await read_all(tv, want))
    return failed


def print_changes(changes, arrow="->"):
    for cat, keys in changes.items():
        label = cat or '""'
        for key, (cur, wanted) in keys.items():
            print(f"  {label}.{key}: {json.dumps(cur)} {arrow} {json.dumps(wanted)}")


async def cmd_probe(tv, args, profile):
    info = await tv.info()
    sw = info["software"] or {}
    print(f"Model:    {info['system'].get('modelName')}")
    print(f"webOS:    {sw.get('product_name')}")
    print(f"Firmware: {sw.get('major_ver')}.{sw.get('minor_ver')}")
    await cmd_check(tv, args, profile)


async def cmd_apps(tv, args, profile):
    apps = await tv.apps()
    for app in sorted(apps, key=lambda a: (a["title"] or "").lower()):
        print(f"{app['id'] or '':45} {app['title'] or ''}")


async def cmd_get(tv, args, profile):
    print(json.dumps(await tv.get(args.category, args.keys), indent=2, sort_keys=True))


async def cmd_set(tv, args, profile):
    settings = {}
    for pair in args.pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            sys.exit(f"expected key=value, got {pair!r}")
        settings[key] = parse_value(value)
    current = await tv.get(args.category, list(settings))
    changes = {args.category: {k: (current.get(k), v) for k, v in settings.items()}}
    failed = await apply_changes(tv, changes)
    print_changes(changes)
    if failed:
        print("Did not stick:")
        print_changes(failed, "!=")
        return 1


async def cmd_call(tv, args, profile):
    payload = json.loads(args.payload) if args.payload else None
    print(json.dumps(await tv.call(args.uri, payload), indent=2, sort_keys=True))


async def cmd_backup(tv, args, profile):
    await write_backup(tv, profile)


async def cmd_apply(tv, args, profile):
    want = targets(profile, args.optional)
    changes, missing = diff(want, await read_all(tv, want))
    for cat, key in missing:
        print(f"  skip {cat}.{key}: not reported by this TV/firmware")
    if not changes:
        print("Nothing to change: the TV already matches the profile.")
        return
    print("Changes:")
    print_changes(changes)
    if args.dry_run:
        return
    await write_backup(tv, profile, "before-apply")
    failed = await apply_changes(tv, changes)
    if failed:
        print("These did not stick (the TV may block them; change them on the TV instead):")
        print_changes(failed, "!=")
        return 1
    print("Done. Run `tv.py privacy` for the user agreements, which must be changed on the TV.")


async def cmd_restore(tv, args, profile):
    data = json.loads(Path(args.backup).read_text(encoding="utf-8"))
    want = data["settings"]
    changes, _ = diff(want, await read_all(tv, want))
    if not changes:
        print("Nothing to restore: the TV already matches the backup.")
        return
    print("Restoring:")
    print_changes(changes)
    failed = await apply_changes(tv, changes)
    if failed:
        print("Could not restore:")
        print_changes(failed, "!=")
        return 1


async def cmd_check(tv, args, profile):
    want = targets(profile, include_optional=True)
    have = await read_all(tv, want)
    changes, missing = diff(want, have)
    print(f"\n{'setting':40} {'now':>10} {'profile':>10}")
    for cat, keys in profile.items():
        for key, spec in keys.items():
            name = f"{cat}.{key}" + (" (optional)" if spec["optional"] else "")
            now = json.dumps(have.get(cat, {}).get(key)) if key in have.get(cat, {}) else "n/a"
            mark = "!" if key in changes.get(cat, {}) and not spec["optional"] else " "
            print(f"{mark} {name:38} {now:>10} {json.dumps(spec['value']):>10}")
    required = {
        cat: {k: v for k, v in keys.items() if not profile[cat][k]["optional"]}
        for cat, keys in changes.items()
    }
    required = {cat: keys for cat, keys in required.items() if keys}
    if missing:
        print(f"\n{len(missing)} key(s) not reported by this TV (n/a).")
    if not required:
        print("\nAll profile settings are in place.")
        return
    print(f"\n{sum(len(k) for k in required.values())} setting(s) differ from the profile (marked !).")
    if getattr(args, "fix", False):
        await write_backup(tv, profile, "before-fix")
        failed = await apply_changes(tv, required)
        if failed:
            print("Still differs after fixing:")
            print_changes(failed, "!=")
            return 1
        print("Fixed.")
        return
    return 1


async def cmd_privacy(tv, args, profile):
    await cmd_check(tv, args, profile)
    status = (await tv.get(EULA_CATEGORY, [EULA_KEY])).get(EULA_KEY)
    if not isinstance(status, dict):
        print("\nUser agreements: this TV did not report them; check them on the TV.")
        return
    agreed = [k for k in EULA_TRACKING if status.get(k)]
    if not agreed:
        print("\nUser agreements: none of the ad/tracking agreements are accepted.")
        return
    print("\nUser agreements still accepted (ads/tracking):")
    for key in agreed:
        print(f"  {key}")
    print("Withdraw them on the TV: Settings > General > System > Additional Settings > User Agreements.")
    print("Keep the general Terms of Use agreed or the Content Store and apps stop working.")


COMMANDS = {
    "probe": cmd_probe, "apps": cmd_apps, "get": cmd_get, "set": cmd_set, "call": cmd_call,
    "backup": cmd_backup, "apply": cmd_apply, "restore": cmd_restore, "check": cmd_check,
    "privacy": cmd_privacy,
}


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("TV_HOST"), help="TV IP address (or set TV_HOST)")
    p.add_argument("--profile", default=str(DEFAULT_PROFILE), help="profile settings.json")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("probe", "apps", "backup", "privacy"):
        sub.add_parser(name)
    g = sub.add_parser("get")
    g.add_argument("category", help='settings category, e.g. general, option ("" for the unnamed one)')
    g.add_argument("keys", nargs="+")
    s = sub.add_parser("set")
    s.add_argument("category")
    s.add_argument("pairs", nargs="+", metavar="key=value")
    c = sub.add_parser("call")
    c.add_argument("uri")
    c.add_argument("payload", nargs="?")
    a = sub.add_parser("apply")
    a.add_argument("--dry-run", action="store_true", help="show changes without writing")
    a.add_argument("--optional", action="store_true", help="also apply keys marked optional")
    r = sub.add_parser("restore")
    r.add_argument("backup")
    k = sub.add_parser("check")
    k.add_argument("--fix", action="store_true", help="reapply settings that drifted")
    return p


async def run(args, tv):
    profile = load_profile(args.profile)
    async with tv:
        return await COMMANDS[args.command](tv, args, profile)


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.host:
        sys.exit("Set TV_HOST=<tv ip> or pass --host. Find the IP on the TV: Settings > Network > Wi-Fi > Advanced.")
    try:
        return asyncio.run(run(args, LGTV(args.host))) or 0
    except (OSError, asyncio.TimeoutError) as e:
        sys.exit(f"Could not reach the TV at {args.host}: {str(e) or 'timed out'}\n"
                 "Is it on, on the same network, and is Settings > General > Devices > "
                 "External Devices > TV On With Mobile enabled?")


if __name__ == "__main__":
    sys.exit(main())
