# cleanyourlgtv

Turn off the ads, tracking and promotions on an LG webOS TV from your computer, over Wi‑Fi. No root, no cable, no developer account.

This is an LG take on [cleanyourtv](https://github.com/Gathin23/cleanyourtv), which does the same for Android/Google TV. It's built for the **LG 65UP7000PUA (2021, webOS 6)**. Other webOS 5–6 sets should mostly work; `tv.py probe` tells you which settings your TV reports.

## What's different from the Android version

webOS has no ADB, and LG doesn't allow preinstalled apps to be disabled or the home screen to be replaced without rooting the TV. So instead of disabling packages, this tool:

1. **Backs up** every setting it's about to touch, plus your app list, to `backups/`.
2. **Turns off** ad and tracking settings over LG's own remote-control API (the same one the ThinQ app uses): Live Plus (ACR), home promotions, personalised ads, ad cookie, screen-saver ads, live-TV promotions, pop-up nudges and home auto-launch. See [the profile](profiles/lg-65up7000pua-webos6/settings.json) for the full list and why each one is there.
3. **Verifies** by reading every value back, where the TV allows it. On the 65UP7000PUA only Live Plus is readable. The TV refuses to read the other keys (`locked`), so those are written without verification, and `apply` tells you where to check them in the TV menus.
4. **Reports** which user agreements (Viewing Information, Interest-Based Ads, Voice) are still accepted. You withdraw those on the TV yourself; the API won't change them.
5. **Blocks** LG ad and ACR domains with an optional [DNS list](dns/).

Everything can be undone with `tv.py restore`.

## Setup

On the TV:
- Turn on Settings → General → Devices → External Devices → **TV On With Mobile**, so the TV accepts connections from your computer.
- Find its IP address: Settings → Network → Wi‑Fi Connection → Advanced Wi‑Fi Settings.

On your Mac (Python 3.9+):

```bash
python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt
export TV_HOST=192.168.1.50   # your TV's IP
```

## Use

```bash
tools/venv/bin/python -I tools/tv.py probe            # first run: accept the pairing prompt on the TV
tools/venv/bin/python -I tools/tv.py apply --dry-run  # see what would change
tools/venv/bin/python -I tools/tv.py apply            # back up, apply, verify
tools/venv/bin/python -I tools/tv.py privacy          # what's still on, incl. user agreements
```

| Command | What it does |
| --- | --- |
| `probe` | Pair, then show model, firmware, and each profile setting's current value |
| `apply [--dry-run] [--optional]` | Back up, then change everything that differs from the profile. `--optional` also turns off tips, toasts and Quick Start+ |
| `check [--fix]` | After a firmware update: show settings that drifted back; `--fix` reapplies them |
| `privacy` | `check`, plus which ad/tracking user agreements are still accepted |
| `backup` | Save the current values without changing anything |
| `restore backups/<file>.json` | Put a backup's values back |
| `apps` | List the apps on the home bar |
| `get <category> <key>...` / `set <category> key=value...` | Read or write any setting |
| `call ssap://<uri> [json]` | Send a raw request to the TV's API |

Then go through the [manual steps](profiles/lg-65up7000pua-webos6/notes.md): user agreements, deleting partner apps from the home bar, and LG Channels.

## Using it with Claude Code

Paste [PROMPT.md](PROMPT.md) into Claude Code (or another coding assistant) in this folder. It walks you through everything, asking before each change.

## How it works

`tools/tv.py` uses [bscpylgtv](https://github.com/chros73/bscpylgtv) to talk SSAP (a JSON WebSocket on port 3001). Reading settings is a normal API call. Writing goes through the TV's internal settings service, the way bscpylgtv does it for picture calibration. The TV doesn't confirm writes, which is why every write is followed by a read-back. The pairing key is stored in `~/.config/cleanyourlgtv/keys.json`.

## Limits

- No app disabling or custom launcher without root. Root exploits exist for some older webOS firmware, but they're patched on current firmware and out of scope here.
- LG locks most settings against reading, and the TV answers the same way for a locked key and one that doesn't exist. Writes to locked keys can't be confirmed by the tool. Check them on the TV, and `restore` can't undo them automatically (it lists them so you can switch them back by hand).
- The DNS lists only block what's listed. Watch your resolver's query log to find more.

## Tests

```bash
tools/venv/bin/pip install pytest && tools/venv/bin/python -m pytest
```

Tests run offline against a fake TV.

## License

MIT. DNS lists derived from [Perflyst/PiHoleBlocklist](https://github.com/Perflyst/PiHoleBlocklist) (MIT).
