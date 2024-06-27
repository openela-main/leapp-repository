**Before doing anything, please read
[Leapp framework documentation](https://leapp.readthedocs.io/).**

---

## Details:
- This repository is based on upstream tag https://github.com/oamg/leapp-repository/tree/v0.17.0
- Oracle patches were mostly applied as is
- Patches that updated upstream references were mostly squashed into a single patch
- Oracle specific mappings ( repositories, events ) were added as additional files, reference upstream files are kept as is.

## Troubleshooting

### Where can I report an issue or RFE related to the framework or other actors?

- GitHub issues are preferred:
  - Leapp framework: [https://github.com/oamg/leapp/issues/new/choose](https://github.com/oamg/leapp/issues/new/choose)
  - Leapp actors: [https://github.com/oamg/leapp-repository/issues/new/choose](https://github.com/oamg/leapp-repository/issues/new/choose)

- When filing an issue, include:
  - Steps to reproduce the issue
  - *All files in /var/log/leapp*
  - */var/lib/leapp/leapp.db*
  - *journalctl*
  - If you want, you can optionally send anything else would you like to provide (e.g. storage info)

**For your convenience you can pack all logs with this command:**

`# tar -czf leapp-logs.tgz /var/log/leapp /var/lib/leapp/leapp.db`

Then you may attach only the `leapp-logs.tgz` file.

### Where can I seek help?
We’ll gladly answer your questions and lead you to through any troubles with the
actor development.

You can reach us at IRC: `#leapp` on Libera.Chat.
