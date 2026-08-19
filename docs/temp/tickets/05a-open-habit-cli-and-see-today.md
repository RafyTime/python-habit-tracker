# 05a: Open the new CLI and see today

**What to build:** A user can launch the new `habit` executable and request a readable snapshot of their current daily and weekly work while the legacy command paths remain temporarily available during migration.

**Blocked by:** None (Ticket 03 is complete, so this ticket can start immediately).

**Status:** ready

- [ ] Installing the project exposes the new `habit` executable without removing the legacy entry points yet.
- [ ] `habit today` works through the root application and initializes a usable single profile on a fresh database.
- [ ] The snapshot greets the display name and distinguishes habits due today from habits due this week.
- [ ] Completed versus active habit progress and current XP progress are readable in one compact result.
- [ ] Archived habits do not appear in the current snapshot.
- [ ] A fresh database shows an empty state with one useful next action instead of an empty table.
- [ ] The new root application composes existing feature behavior without copying due, profile, or XP rules into command code.
- [ ] The output establishes reusable presentation conventions for headings, progress, success, warnings, and next steps.
- [ ] Root CLI tests verify fresh and populated persisted outcomes through an isolated SQLite database.
- [ ] The existing test suite remains green while the temporary legacy paths coexist with the new entry point.
