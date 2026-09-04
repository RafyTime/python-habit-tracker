# 07 — Complete the final codebase cleanup and verification pass

**What to build:** The refactored tracker is internally coherent, free of obsolete multi-profile paths and duplicated presentation logic, and ready to be demonstrated as a polished course project.

**Blocked by:** 01 — Make the quality gates representative and green; 03 — Offer clear archive and permanent-delete habit lifecycles; 04 — Deliver a correct four-week evaluation fixture; 05 — Make the core CLI guided and visually consistent; 06 — Document the happy path and fuller user guide.

**Status:** ready

- [ ] Obsolete multi-profile code, tests, and user-facing references are removed after migration support is no longer needed.
- [ ] Domain modules have concise docstrings and small, understandable interfaces; CLI presentation is not duplicated across commands.
- [ ] Current source, tests, docstrings, CLI copy, and Phase 2 specifications are audited against the domain glossary, with every domain concept using its canonical term or an explicitly accepted user-facing synonym.
- [ ] Domain code and assignment-facing material prefer `Periodicity`, `Analytics`, and `Test fixture`; the CLI boundary consistently presents `Repetition`, `Stats`, and `Sample data` without changing their meaning.
- [ ] Runtime behaviour and tests agree that local system time determines the current Period and that each Habit can earn one five-XP Milestone on first reaching each of 3, 7, 14, and 30 consecutive Periods, retained through Archive and Restoration and removed by Permanent deletion.
- [ ] Current specifications state that the development database is disposable after schema changes and contain no continuing legacy-migration promise; runtime commands still preserve or remove data according to their documented lifecycle guarantees.
- [ ] Historical Phase 1 material remains intact, while current Phase 2 material contains no unresolved claim that custom periodicities, negative Habits, stored profile timezones, or multiple profiles are supported.
- [ ] No deferred feature is exposed as if it were implemented.
- [ ] A clean-database smoke test covers the documented happy path and fixture flow.
- [ ] The full formatter, linter, type checker, test suite, and documentation command checks are green.
