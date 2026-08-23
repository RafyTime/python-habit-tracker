# 06 — Document the happy path and fuller user guide

**What to build:** A new user can install, run, and evaluate the tracker from the README, then consult a focused guide for the full lifecycle and troubleshooting without reading source code.

**Blocked by:** 04 — Deliver a correct four-week evaluation fixture; 05 — Make the core CLI guided and visually consistent.

**Status:** ready

- [ ] The README contains a concise, verified quick start covering installation, first run, fixture seeding, core commands, tests, and quality checks.
- [ ] `docs/USER_GUIDE.md` explains setup, adding and completing daily/weekly habits, icons and editing, due habits, archive/restore/permanent-delete behavior, today/XP, stats, fixture data, and common errors.
- [ ] Quick start prints the visible GitHub URL for `docs/USER_GUIDE.md`, and the URL is verified after the guide is added.
- [ ] Examples use the final command names and are verified against an isolated database.
- [ ] Assignment-facing explanations use the glossary's canonical terms `Periodicity`, `Analytics`, and `Test fixture`; CLI guidance uses the accepted user-facing terms `Repetition`, `Stats`, and `Sample data` and explains their mapping where an evaluator needs it.
- [ ] Documentation explains that the machine's local system time determines the current Daily or Weekly period and makes no promise that period boundaries remain stable after the machine timezone changes.
- [ ] Documentation defines a Milestone as a one-time five-XP award when a Habit first reaches a seven-period Streak; archive and restoration retain the claim, while permanent deletion removes it with the Habit.
- [ ] Current documentation limits the product to positive Daily and Weekly Habits and clearly labels custom periodicities, negative Habits, stored timezone preferences, and other deferred features rather than promising unsupported behaviour.
- [ ] Phase 1 conception material remains available as historical context, while current documentation plainly identifies the Phase 2 scope refinements that supersede it.
