# 05j: Show accurate current progress

**What to build:** A user can scan each Habit's current Progress in `habit list`, distinguish Current streak from Longest streak, and optionally include completed Active Habits in `habit today` without weakening the Due-only default.

**Blocked by:** None.

**Status:** done

- [x] A pure Current streak calculation handles Daily and Weekly Periods relative to an explicit reference time.
- [x] Completing the current Period counts consecutive Completions backward from that Period.
- [x] When the current Period is Due, an unbroken streak through the immediately preceding Period remains pending until the current Period ends.
- [x] A missed preceding Period makes Current streak zero even when the Habit has older Completion history, while completing after a gap starts a new Current streak of one.
- [x] Current streak distinguishes a broken history from a Habit that has never recorded a Completion.
- [x] Archived Habits have no Current streak, while their historical Longest streak remains available through Stats.
- [x] Completion feedback reports Current streak rather than reusing Longest streak.
- [x] `habit list` displays ID, Habit, Progress, Streak, and Repetition in that order.
- [x] Progress uses written Due, Done, or Archived values and does not replace lifecycle Status.
- [x] Running, pending, broken, and not-started streaks use the agreed symbols and retain readable meaning without color or reliable Unicode rendering.
- [x] Default List and Today views continue to exclude Archived Habits.
- [x] `habit today` remains Due-only by default.
- [x] `habit today --done` adds completed Active Habits after Due Habits in the matching Daily or Weekly group, with dimmed styling and a written Done label.
- [x] Today headings remain Due today and Due this week by default, then become Today and This week when completed Habits are included.
- [x] Bare `habit` keeps its Due-only snapshot and does not expose the completed-Habit variation through home.
- [x] Direct pure Analytics tests cover current and pending Daily and Weekly streaks, gaps, restarts, no history, duplicate period keys, and ISO year boundaries.
- [x] Root CLI tests cover the List contract, Current streak feedback, Today defaults, `--done`, ordering, Archived exclusion, and readable text without asserting terminal escape sequences.
