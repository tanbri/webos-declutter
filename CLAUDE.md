# Notes for coding assistants

This repo changes settings on a real TV in someone's home. Treat every write as user-visible.

- Always run `tools/venv/bin/python -I tools/tv.py ...` (the `-I` keeps the venv isolated).
- Never change the TV without the user's go-ahead. Show `apply --dry-run` output first.
- `apply`, `check --fix` and `set` must leave a backup in `backups/` before writing. `apply` and `check --fix` do this themselves. Run `backup` before using `set` directly.
- Never write to `eulaStatus`/`eulaInfo`, factory-reset, change network settings or trigger a reboot over the API. Users change agreements on the TV themselves.
- Writes aren't confirmed by the TV. Trust the read-back, not the call returning.
- `locked` (`?`) means the TV refuses to read the key. webOS gives the same answer for keys that don't exist, so locked keys are written blind and the user checks them in the TV menus. `missing` means the category doesn't have the key. Don't guess other key names; use `get` to explore, and ask before writing.
- Never block `snu.lge.com` or all of `lgtvsdp.com` in DNS lists. They deliver firmware updates.
- Python 3.9 compatible, standard library plus `bscpylgtv` only. Run `tools/venv/bin/python -m pytest` after changing `tools/tv.py`.
