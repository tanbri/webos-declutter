# cleanyourlgtv

Make an LG webOS TV quieter and lighter from your computer, over Wi‑Fi: no screen fingerprinting, no promoted content on the home screen, no ad tracking, and fewer preinstalled apps. No root, no cable, no developer account.

Built for the **LG 65UP7000PUA (2021, webOS 6)**. Other webOS 5–6 sets should mostly work; `tv.py probe` shows which settings your TV reports.

## What it improves

| Change | Effect |
| --- | --- |
| **Live Plus off** | Stops automatic content recognition (ACR). With it on, the TV continuously fingerprints whatever is on screen, including HDMI inputs, and uploads it. Off, that background capture and network traffic stop. |
| **Home Promotion, live-TV promotions, promo streams, screen-saver ads off** | The home screen and screen saver stop fetching banners, promoted tiles and preview videos from LG's servers, so there's less to download and draw each time they open. |
| **Power On Screen: Recent Input** | The TV powers on straight to your last input instead of loading the home screen first. |
| **Personalised ads, ad cookie off; Limit Ad Tracking and Do Not Sell on** | Apps and LG stop targeting ads using the TV's ad ID and viewing history. |
| **Pop-up nudges off** | No suggestion overlays on top of what you're watching. |
| **User agreements withdrawn** (by hand) | Viewing Information, Interest-Based Advertisement, Voice and Marketing. LG's servers stop receiving the data those cover. |
| **Unused apps deleted** (by hand) | Frees storage, which is tight on entry-level models, and means fewer apps to check for updates in the background. |
| **Optional DNS blocklist** (set on your router) | Requests to LG ad, beacon and ACR servers fail immediately, and they stay blocked even if a firmware update turns a setting back on. |

These changes remove background work and network fetches; they don't overclock anything. The gains haven't been benchmarked, and how much faster the TV feels varies. Expect the home screen to open with less clutter and less loading, and no ACR running in the background.

## What it doesn't do

- **No app disabling or custom home screen.** webOS doesn't let anything do either without rooting the TV, and root is out of scope. You delete partner apps with the remote; LG's own apps (Live TV, LG Channels, Home Dashboard) stay.
- **Can't confirm most writes.** LG blocks apps from reading almost every setting on this model. Only Live Plus can be read back. The tool still writes the rest and tells you where to check them in the TV menus. On the 65UP7000PUA, Home Promotion and Limit Ad Tracking are confirmed to take effect this way.

## Setup

On the TV:
- Turn on Settings → General → Devices → External Devices → **TV On With Mobile**, so the TV accepts connections from your computer.
- Find its IP address in your router's device list, where it usually shows as `lgwebostv`. From a Mac on the same network you can also run `arp -a | grep -i lgwebostv` once the TV is on.

On your Mac (Python 3.9+):

```bash
python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt
export TV_HOST=192.168.1.50   # your TV's IP
```

## Use

Run these from the repo folder:

```bash
tools/venv/bin/python -I tools/tv.py probe            # first run: accept the pairing prompt on the TV
tools/venv/bin/python -I tools/tv.py apply --dry-run  # see what would change
tools/venv/bin/python -I tools/tv.py apply            # back up, apply, verify what can be read
tools/venv/bin/python -I tools/tv.py privacy          # what's still on, incl. user agreements
```

Then do the [manual steps](profiles/lg-65up7000pua-webos6/notes.md): withdraw user agreements, check Home Settings, and delete unused apps from the home bar.

After a firmware update, run `check --fix` to reapply anything the update reset.

| Command | What it does |
| --- | --- |
| `probe` | Pair, then show model, firmware, and each profile setting's current value (`locked` = the TV won't let it be read) |
| `apply [--dry-run] [--optional]` | Back up, then write the profile. `--optional` also turns off tips, toasts and Quick Start+ |
| `check [--fix]` | Show settings that drifted back; `--fix` reapplies them |
| `privacy` | `check`, plus which ad/tracking user agreements are still accepted |
| `backup` | Save the current values without changing anything |
| `restore backups/<file>.json` | Put a backup's readable values back, and list the locked ones to switch back by hand |
| `apps` | List the apps on the home bar |
| `get <category> <key>...` / `set <category> key=value...` | Read or write any setting |
| `call ssap://<uri> [json]` | Send a raw request to the TV's API |

About Quick Start+ (`--optional`): turning it off saves standby power and stops the TV keeping its network active overnight, but cold power-on takes a few seconds longer. Leave it on if fast power-on matters more to you.

## Using it with Claude Code

Paste [PROMPT.md](PROMPT.md) into Claude Code (or another coding assistant) in this folder. It walks you through everything, asking before each change.

## How it works

`tools/tv.py` uses [bscpylgtv](https://github.com/chros73/bscpylgtv) to talk SSAP, a JSON WebSocket on port 3001. It's the same local API the LG ThinQ app uses. Reading settings is a normal API call. Writing goes through the TV's internal settings service, which doesn't return a result, so every readable write is followed by a read-back. Before every change, the tool saves the current values to `backups/`. The pairing key is stored in `~/.config/cleanyourlgtv/keys.json`.

## Tests

```bash
tools/venv/bin/pip install pytest && tools/venv/bin/python -m pytest
```

Tests run offline against a fake TV.

## License

MIT. DNS lists derived from [Perflyst/PiHoleBlocklist](https://github.com/Perflyst/PiHoleBlocklist) (MIT).
