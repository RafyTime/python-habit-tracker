# 05k: Add focused Habit Stats details

**What to build:** A user inspecting one Habit through Stats can see how much XP it earned and when it was last completed, while overall Stats remain compact.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] `habit stats HABIT` retains Repetition, lifecycle Status, Completion count, and Longest streak.
- [ ] Focused Habit Stats show the total XP earned by that Habit across its retained XP events.
- [ ] Focused Habit Stats show the latest Completion in a readable form.
- [ ] A Habit without XP or Completion history receives clear zero and never-completed values.
- [ ] Numeric IDs and normalized exact Habit names continue to use the shared selection rules without fuzzy guessing.
- [ ] Archived Habits remain excluded by default and can be inspected only through the existing explicit archived inclusion contract.
- [ ] Archive and Restoration retain the XP and latest Completion shown for a Habit, while Permanent deletion removes their contribution with the Habit history.
- [ ] Overall `habit stats` remains a compact summary and does not add per-Habit rows.
- [ ] Feature services provide persisted XP and Completion facts to the command; presentation code does not query persistence directly.
- [ ] Root CLI tests verify XP totals and latest Completion against persisted records for Active, Archived, empty-history, and deleted-Habit cases.
- [ ] Existing overall Stats and XP behavior remains covered and unchanged.

