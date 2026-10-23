# LG 65UP7000PUA (webOS 6) — manual steps

`tv.py apply` covers what the TV lets the remote API change. These have to be done with the remote.

## User agreements (most important)

Settings → General → System → Additional Settings → User Agreements.

Withdraw:

- **Viewing Information**: LG's ACR/viewing data, including from HDMI inputs.
- **Voice Information**: voice recordings sent to LG and partners.
- **Interest-Based Advertisement**: targeted ads.

Keep **Terms of Use** agreed. Without it the LG Content Store, app updates and most streaming apps stop working.

`tv.py privacy` shows which of these are still accepted.

## Home screen clutter

webOS 6 doesn't let you disable preinstalled apps without root. You can:

- **Remove** most partner apps: hold OK on the app in the home bar → Delete. LG's own apps (Live TV, LG Channels, Sports, Art Gallery) can't be removed.
- **Reorder** the ones you use to the front: hold OK → Move.
- **Turn off the recommendation row**: Settings → General → Home Settings → Home Promotion (also done by `tv.py apply`).

## LG Channels

LG Channels is the ad-supported free TV service. To stop it taking over Live TV, look for an LG Channels switch under Settings → Channels. Where it sits varies by firmware. It isn't exposed to the remote API on this model.

## Ad-blocking DNS

See [`dns/README.md`](../../dns/README.md). Set it on the TV under Settings → Network → (Wi‑Fi or Wired) → Advanced Settings → turn off "Set Automatically" for DNS and enter your resolver.

## Firmware updates

Updates are kept on, for security. Big firmware updates sometimes reset the home promotion and Live Plus settings. Afterwards, run:

```
tools/venv/bin/python -I tools/tv.py check --fix
```

## Remote control from this Mac

For the tool to connect, the TV must be on, on the same network, and have Settings → General → Devices → External Devices → **TV On With Mobile** turned on. The first connection shows a pairing prompt on the TV. The key is saved in `~/.config/cleanyourlgtv/keys.json`.
