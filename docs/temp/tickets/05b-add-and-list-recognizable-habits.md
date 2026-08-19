# 05b: Add and list recognizable habits

**What to build:** A user can add and list daily or weekly habits through the new root CLI, using natural repetition words, globally reliable names, and optional icons that remain understandable as plain text.

**Blocked by:** 05a: Open the new CLI and see today.

**Status:** ready

- [ ] `habit add` and `habit list` work through the new root CLI with explicit forms suitable for documentation and automation.
- [ ] The repetition option accepts day, daily, week, and weekly and displays the stored value as Daily or Weekly.
- [ ] A habit can store an optional short, single-line Unicode icon without requiring emoji classification.
- [ ] Explicit creation adds no icon unless one is supplied, while interactive creation offers suggestions, custom input, and no icon.
- [ ] Listing always displays the habit name beside any icon and prioritizes name, repetition, and status over internal timestamps.
- [ ] Habit identity comparison trims outer whitespace, collapses repeated whitespace, treats underscores as spaces, and ignores capitalization while preserving the entered display name.
- [ ] Active and archived habits share global normalized-name uniqueness.
- [ ] Adding a name already used by an archived habit explains that the old record still exists and asks the user to choose another name until restoration lands in its lifecycle ticket.
- [ ] Active habits appear by default, while archived inclusion is explicit and labelled.
- [ ] Existing profiles and habits receive safe defaults for the new icon field without losing completion or XP history.
- [ ] Root CLI and persistence tests cover repetition aliases, icon and no-icon paths, name normalization, global collisions, filtering, and archived labels.
