# 05m: Teach the Habit journey in Quick start

**What to build:** A beginner can complete a short guided practice that explains Habits, Repetition, Today, Done, XP, Current streaks, Milestones, and focused Stats while teaching the explicit commands behind the same actions.

**Blocked by:** 05j: Show accurate current progress; 05k: Add focused Habit Stats details; 05l: Polish interactive presentation and editing.

**Status:** done

- [x] Quick start remains a single interactive session and requires no persisted tutorial state.
- [x] The opening explains that a Habit repeats once per Daily or Weekly Period before asking the user to create or explore one.
- [x] An empty tracker still offers a personal first Habit or the deterministic Sample data path.
- [x] The personal path uses the normal Add prompts and prints the equivalent explicit `habit add` command after the Habit is saved.
- [x] The personal path shows the current Today snapshot before offering a first Completion through the normal Done interaction.
- [x] After a Completion, Quick start explains routine XP and Current streak using the result the user just created.
- [x] Quick start explains that Milestones award five bonus XP once per Habit at 3, 7, 14, and 30 consecutive Periods.
- [x] Quick start offers focused Stats for the relevant Habit and shows the equivalent explicit `habit stats` command.
- [x] The guided journey displays useful explicit forms for Add, Today, Done, and focused Stats without requiring the user to leave and resume the tutorial through separate shell commands.
- [x] The Sample data path identifies generated history as Sample data and uses it to demonstrate Today and Stats without presenting fixture Completions as personal progress.
- [x] A tracker with existing Active or Archived Habits preserves all data, does not offer automatic Sample data, and adapts the tour to existing Habits.
- [x] When no Habit is Due, Quick start skips the Completion offer and continues with the read-only parts of the journey.
- [x] The ending lets the user enter interactive home or exit and keeps the visible full user-guide URL.
- [x] Cancelling a choice keeps previously completed actions, returns or exits cleanly, and never resets data.
- [x] Ctrl+C exits without an application traceback.
- [x] Root CLI journey tests cover personal setup, Sample data, existing data, no Due Habits, first Completion, focused Stats, command teaching, cancellation, home entry, exit, and the guide URL.
