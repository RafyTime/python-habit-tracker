# 05f: Inspect progress through stats and XP

**What to build:** A user can inspect compact overall or per-habit progress and view current or recent XP through the flat root CLI, with archived history included only by an explicit labelled choice.

**Blocked by:** 05b: Add and list recognizable habits.

**Status:** done

- [x] `habit stats` shows active daily and weekly habit counts, recorded completion count, and the overall longest streak.
- [x] A habit selector changes the result to that habit's repetition, status, completion count, and longest streak.
- [x] Numeric IDs and normalized exact names follow the shared selection rules without fuzzy guessing.
- [x] Archived habits and their history are excluded by default.
- [x] Explicit archived inclusion is clearly labelled in both overall and per-habit results.
- [x] Empty data and zero-completion states explain what the user can do next.
- [x] Existing pure analytics functions continue to calculate streaks without presentation or persistence concerns.
- [x] `habit xp` shows total XP, level, and progress to the next level.
- [x] XP history is available through the same command and respects the requested event limit.
- [x] Stats and XP output use the shared headings, progress, status, and next-step conventions.
- [x] Root CLI tests verify persisted counts and rendered meaning, while direct pure-function tests remain the seam for streak edge cases.
