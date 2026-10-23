# Samsung UN55TU700DFXZA (2020, Tizen 5.5) — privacy and declutter checklist

Samsung TVs don't expose their settings to the network API, so `tools/tv.py` can't help here. This checklist is done entirely with the remote. It takes about ten minutes.

Model: UN55TU700DFXZA (TU7000 family), software T-KSU2EAKUC-2301.1. On other 2020–2021 Tizen models the menu names are the same, but entries can sit one level higher or lower.

## 1. Privacy agreements

Settings → Terms & Privacy → Terms & Policies (confirmed on this TV):

- [ ] **Viewing Information Services** → off. This is Samsung's automatic content recognition (ACR): it identifies what's on screen, including from HDMI inputs, and sends it to Samsung.
- [ ] **Interest-Based Advertisement** → disable, then choose **Reset** for the ad ID if offered.
- [ ] **Voice Recognition Services** → off, unless you use Bixby or Alexa on the TV.
- [ ] Leave **Smart Hub Terms & Conditions** and the **Privacy Notice** agreed. Without them Smart Hub and all apps stop working.

## 2. Power-on behaviour

Settings → General → Smart Features:

- [ ] **Autorun Smart Hub** → off. The TV powers on to your last input instead of opening Smart Hub and its promoted rows.
- [ ] **Autorun Last App** → your choice. On reopens the app you were in when you turned the TV off.

## 3. Unused apps

Home → Apps → settings (gear icon, top right) → select an app → **Delete**. Deleted apps can be reinstalled from Apps.

| Group | Typical preloads on 2020 models |
| --- | --- |
| Delete if unused | Games and promo apps, shopping apps, and streaming services you don't subscribe to |
| Keep | Apps (the store), Internet, Gallery, SmartThings if you use it |
| Can't remove | Samsung TV Plus, Universal Guide on some firmware. They stay, but deleting the rest keeps them out of the way. |

You can also reorder: on the home bar, highlight an app → press down → **Move**.

## 4. Software updates

Settings → Support → Software Update:

- [ ] Leave **Auto Update** on. Updates carry security fixes, and blocking them isn't worth it.

## 5. Ad-blocking DNS (optional)

Use [`dns/samsung-ads.txt`](../../dns/samsung-ads.txt) on a Pi-hole, AdGuard Home or NextDNS (see [`dns/README.md`](../../dns/README.md)). Then point the TV at it, either:

- on your router, so every device uses it, or
- on the TV: Settings → General → Network → Network Status → **IP Settings** → DNS Setting → **Enter manually**.

## What this can't do

- **No app disabling or custom home screen.** Tizen doesn't allow either without rooting the TV.
- **No automation or verification.** Samsung's network API can press keys and launch apps, but can't read or change settings. The only check is looking at each menu again.
- **Firmware updates may reset some of these.** After a big update, go through sections 1 and 2 again.
