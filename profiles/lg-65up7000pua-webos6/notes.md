# LG 65UP7000PUA (webOS 6) — manual steps

`tv.py apply` covers what the TV lets the remote API change. These have to be done with the remote.

## User agreements (most important)

Settings → Support → Privacy & Terms → User Agreements.

Withdraw:

- **Viewing Information**: LG's ACR/viewing data, including from HDMI inputs.
- **Voice Information**: voice recordings sent to LG and partners.
- **Interest-Based Advertisement**: targeted ads.
- **Marketing**: promotional messages from LG. Nothing depends on it.

Keep **Terms of Use** agreed. Without it the LG Content Store, app updates and most streaming apps stop working.

`tv.py privacy` shows which of these are still accepted.

## Home screen clutter

webOS 6 doesn't let you disable preinstalled apps without root. You can:

- **Remove** apps you don't use: hold OK on the app in the home bar → Delete. Deleted apps can be reinstalled from the Apps store.
- **Reorder** the ones you use to the front: hold OK → Move.

On this TV (`tv.py apps`), these are safe to delete:

| Group | Apps |
| --- | --- |
| LG filler | LG Gaming Portal, LG Movies & TV, LG Radio+, LG Sports Playbook, LG Streaming Week, LG Travel+, ShopTime, Who.Where.What?, Sports Alert |
| Preloaded games | 8 Ball Pool, Weekend Games |
| Only if unused | FOX ONE, Fubo, Sling TV, YouTube TV, Amazon Alexa, Pluto TV, Tubi, Room to Room Share |
| Keep | Apps (the store), Media Player, Web Browser, Home Dashboard, LG Channels. These are system apps, and most can't be deleted. |
- **Home Settings** (Settings → General → System → Additional Settings → Home Settings) on firmware 03.53.45 has three entries:
  - **Power On Screen**: set to **Recent Input** so the TV opens on your last input instead of the home screen. (There's no "Home Auto Launch" entry on this firmware.)
  - **Home Promotion**: Off. `tv.py apply` does this; confirmed working on this TV.
  - **Content Recommendation**: **Off** (it was already off on this TV). Its settings key isn't known, so the tool doesn't touch it; check it by hand.

## LG Channels

LG Channels is the ad-supported free TV service. To stop it taking over Live TV, look for an LG Channels switch under Settings → Channels. Where it sits varies by firmware. It isn't exposed to the remote API on this model.

## Ad-blocking DNS

See [`dns/README.md`](../../dns/README.md). The simplest way is to set the DNS server on your router. The Wi‑Fi Connection screen on this TV only shows the on/off switch and the network list, so a per-TV DNS setting may not be reachable there.

## Firmware updates

Updates are kept on, for security. Big firmware updates sometimes reset the home promotion and Live Plus settings. Afterwards, run:

```
tools/venv/bin/python -I tools/tv.py check --fix
```

## Remote control from this Mac

For the tool to connect, the TV must be on, on the same network, and have Settings → General → Devices → External Devices → **TV On With Mobile** turned on. The first connection shows a pairing prompt on the TV. The key is saved in `~/.config/webos-declutter/keys.json`.
