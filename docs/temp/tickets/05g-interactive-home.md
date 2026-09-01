# 05g: Use the essential workflow from interactive home

**What to build:** A user can run bare `habit` to see today's state and use the essential add, done, list, stats, and settings flow without memorizing commands, while non-interactive use remains prompt-free.

**Blocked by:** 05c: Complete a habit by name or ID; 05f: Inspect progress through stats and XP.

**Status:** done

- [x] Bare `habit` detects whether an interactive terminal is available.
- [x] Interactive use renders the shared today snapshot and offers Mark a habit done, Add a habit, View habits, View stats, Settings, and Exit.
- [x] Edit, archive, restore, delete, XP history, and seed remain outside the basic home menu.
- [x] Each menu action uses the same persisted behavior and presentation as its explicit command rather than duplicating rules.
- [x] The single profile stores a display name and an after-action preference with home as the safe default.
- [x] Settings can be viewed and updated explicitly, while the home menu offers an editor for the same values.
- [x] Returning home refreshes the snapshot after a persisted action.
- [x] The exit preference performs one selected action and then ends the session.
- [x] Cancelling a picker returns to the previous menu without changing data.
- [x] Ctrl+C exits cleanly without an application traceback.
- [x] Non-interactive bare `habit` prints the read-only today snapshot and exits successfully without prompting.
- [x] Missing command information prompts only in an interactive terminal and otherwise fails with an actionable explicit form.
- [x] Existing profiles receive the home default without losing habits, completions, or XP history.
- [x] Root CLI journey tests cover home and exit preferences, refreshed actions, cancellation, Ctrl+C, empty state, and non-interactive fallback.
