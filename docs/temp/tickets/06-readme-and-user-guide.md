# 06 — Document the happy path and fuller user guide

**What to build:** A new user can install, run, and evaluate the tracker from the README, then consult a focused guide for the full lifecycle and troubleshooting without reading source code.

**Blocked by:** 04 — Deliver a correct four-week evaluation fixture; 05 — Make the core CLI guided and visually consistent.

**Status:** ready

- [ ] The README contains a concise, verified quick start covering installation, first run, fixture seeding, core commands, tests, and quality checks.
- [ ] `docs/USER_GUIDE.md` explains setup, adding and completing daily/weekly habits, icons and editing, due habits, archive/restore/permanent-delete behavior, today/XP, stats, fixture data, and common errors.
- [ ] Quick start prints the visible GitHub URL for `docs/USER_GUIDE.md`, and the URL is verified after the guide is added.
- [ ] Examples use the final command names and are verified against an isolated database.
- [ ] Documentation explains the local-time period rule and clearly labels deferred features rather than promising unsupported behaviour.
