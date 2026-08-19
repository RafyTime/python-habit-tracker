# 05g: Use the essential workflow from interactive home

**What to build:** A user can run bare `habit` to see today's state and use the essential add, done, list, stats, and settings flow without memorizing commands, while non-interactive use remains prompt-free.

**Blocked by:** 05c: Complete a habit by name or ID; 05f: Inspect progress through stats and XP.

**Status:** ready

- [ ] Bare `habit` detects whether an interactive terminal is available.
- [ ] Interactive use renders the shared today snapshot and offers Mark a habit done, Add a habit, View habits, View stats, Settings, and Exit.
- [ ] Edit, archive, restore, delete, XP history, and seed remain outside the basic home menu.
- [ ] Each menu action uses the same persisted behavior and presentation as its explicit command rather than duplicating rules.
- [ ] The single profile stores a display name and an after-action preference with home as the safe default.
- [ ] Settings can be viewed and updated explicitly, while the home menu offers an editor for the same values.
- [ ] Returning home refreshes the snapshot after a persisted action.
- [ ] The exit preference performs one selected action and then ends the session.
- [ ] Cancelling a picker returns to the previous menu without changing data.
- [ ] Ctrl+C exits cleanly without an application traceback.
- [ ] Non-interactive bare `habit` prints the read-only today snapshot and exits successfully without prompting.
- [ ] Missing command information prompts only in an interactive terminal and otherwise fails with an actionable explicit form.
- [ ] Existing profiles receive the home default without losing habits, completions, or XP history.
- [ ] Root CLI journey tests cover home and exit preferences, refreshed actions, cancellation, Ctrl+C, empty state, and non-interactive fallback.
