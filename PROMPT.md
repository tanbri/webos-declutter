# Clean up my LG TV

You're helping me remove ads and tracking from my LG webOS TV with the tools in this repo. Read `README.md`, `CLAUDE.md` and `profiles/lg-65up7000pua-webos6/notes.md` first.

My TV model: **[fill in, e.g. 65UP7000PUA]**

Work through these steps in order. Stop and ask me before anything that changes the TV.

1. **Setup.** Create the venv and install `tools/requirements.txt` if it isn't there yet. Ask me for the TV's IP address. Remind me to turn on Settings → General → Devices → External Devices → TV On With Mobile.
2. **Probe.** Run `tools/venv/bin/python -I tools/tv.py --host <ip> probe`, and tell me to accept the pairing prompt on the TV. Show me the model, the firmware, and which profile settings the TV reports.
3. **If my model isn't the 65UP7000PUA**, copy the profile to `profiles/<my-model>/` and drop keys the probe showed as `n/a`.
4. **Ask me** these before applying:
   - Turn off tips/toast pop-ups and Quick Start+ too (`--optional`)? Quick Start+ off saves standby power but makes power-on a few seconds slower.
   - Do I use Google Assistant or Alexa on the TV? If yes, I'll keep the Voice Information agreement.
5. **Dry run.** Run `apply --dry-run` and show me the changes.
6. **Apply.** After I say yes, run `apply` (plus `--optional` if I said so). Report anything that didn't stick.
7. **Privacy.** Run `privacy`. Walk me through withdrawing each accepted agreement on the TV, one menu at a time, then run `privacy` again to confirm.
8. **Home bar.** Run `apps`, help me decide which partner apps to delete, and tell me how to delete them with the remote (hold OK → Delete).
9. **DNS (optional).** Ask whether I have Pi-hole, AdGuard Home, NextDNS or none, and walk me through `dns/README.md` for that option.
10. **Wrap up.** Tell me the backup file's name, how to undo (`restore`), and to run `check --fix` after firmware updates.
