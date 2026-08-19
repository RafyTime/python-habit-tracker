# 05f: Inspect progress through stats and XP

**What to build:** A user can inspect compact overall or per-habit progress and view current or recent XP through the flat root CLI, with archived history included only by an explicit labelled choice.

**Blocked by:** 05b: Add and list recognizable habits.

**Status:** ready

- [ ] `habit stats` shows active daily and weekly habit counts, recorded completion count, and the overall longest streak.
- [ ] A habit selector changes the result to that habit's repetition, status, completion count, and longest streak.
- [ ] Numeric IDs and normalized exact names follow the shared selection rules without fuzzy guessing.
- [ ] Archived habits and their history are excluded by default.
- [ ] Explicit archived inclusion is clearly labelled in both overall and per-habit results.
- [ ] Empty data and zero-completion states explain what the user can do next.
- [ ] Existing pure analytics functions continue to calculate streaks without presentation or persistence concerns.
- [ ] `habit xp` shows total XP, level, and progress to the next level.
- [ ] XP history is available through the same command and respects the requested event limit.
- [ ] Stats and XP output use the shared headings, progress, status, and next-step conventions.
- [ ] Root CLI tests verify persisted counts and rendered meaning, while direct pure-function tests remain the seam for streak edge cases.
