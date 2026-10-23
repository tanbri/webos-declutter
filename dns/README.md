# Ad-blocking DNS for an LG TV

Turning settings off stops most ads. Blocking LG's ad and tracking domains at the DNS level catches the rest and keeps working if a firmware update turns a setting back on.

| File | Use |
| --- | --- |
| [`lg-ads.txt`](lg-ads.txt) | Default. Ads, home promotions, telemetry and ACR. Safe for the Content Store, apps and firmware updates. |
| [`lg-ads-aggressive.txt`](lg-ads-aggressive.txt) | Extras that can break parts of webOS. Add one at a time and test. |

Never block `snu.lge.com` or `lgtvsdp.com` as a whole. They deliver firmware and app updates.

## Pick a resolver

**Pi-hole or AdGuard Home on your network** (most control, nothing leaves your house)
- Pi-hole: Group Management → Domains → add each line as an exact deny. Or put this file on a web server and add it as an Adlist.
- AdGuard Home: Filters → Custom filtering rules, one `||domain^` per line:
  ```
  grep -v '^#' dns/lg-ads.txt | grep . | sed 's/.*/||&^/'
  ```

**NextDNS** (hosted, free tier)
- Denylist → paste the domains.
- NextDNS sees every DNS lookup the TV makes. That's the trade-off for not running your own server.

**AdGuard DNS public resolver** (no account; generic ad list, not LG-specific)
- `94.140.14.14` / `94.140.15.15`

## Point the TV at it

webOS 6 has no "Private DNS" (DNS-over-TLS) option, only a plain DNS server:

Settings → Network → Wi‑Fi Connection (or Wired) → Advanced Wi‑Fi Settings → Edit → uncheck **Set Automatically** → DNS Server: your resolver's IP.

Or set the DNS server on your router so every device uses it.

## Check it works

- The home screen shows no promoted tile or banner after a restart.
- In Pi-hole / NextDNS logs, the TV's lookups to the domains above show as blocked.
- The Content Store, Netflix, YouTube and **Settings → Support → Software Update → Check for updates** still work.
