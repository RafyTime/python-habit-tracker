# 07 — Complete the final codebase cleanup and verification pass

**What to build:** The refactored tracker is internally coherent, free of obsolete multi-profile paths and duplicated presentation logic, and ready to be demonstrated as a polished course project.

**Blocked by:** 01 — Make the quality gates representative and green; 03 — Offer clear archive and permanent-delete habit lifecycles; 04 — Deliver a correct four-week evaluation fixture; 05 — Make the core CLI guided and visually consistent; 06 — Document the happy path and fuller user guide.

**Status:** ready-for-agent

- [ ] Obsolete multi-profile code, tests, and user-facing references are removed after migration support is no longer needed.
- [ ] Domain modules have concise docstrings and small, understandable interfaces; CLI presentation is not duplicated across commands.
- [ ] No deferred feature is exposed as if it were implemented.
- [ ] A clean-database smoke test covers the documented happy path and fixture flow.
- [ ] The full formatter, linter, type checker, test suite, and documentation command checks are green.

