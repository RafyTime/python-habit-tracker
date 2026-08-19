# 05e: Permanently delete with a specific impact warning

**What to build:** A user can permanently delete an active or archived habit only after seeing the real completion and XP impact, with confirmed, cancelled, and forced paths that accurately report the persisted result.

**Blocked by:** 05c: Complete a habit by name or ID.

**Status:** ready

- [ ] `habit delete` works through the new root CLI with ID, normalized-name, and interactive selection forms.
- [ ] Before confirmation, the warning names the habit and shows the completion count and XP amount that will be removed.
- [ ] The warning states that historical stats will change.
- [ ] Declining confirmation leaves the habit, completions, XP, and stats inputs unchanged and exits as an expected cancellation.
- [ ] Confirming deletion removes the habit and dependent completion and XP records atomically.
- [ ] Force skips confirmation but still prints the removed completion count and XP amount.
- [ ] Active and archived habits can both be deleted deliberately.
- [ ] Missing or ambiguous selection produces an actionable failed exit without changing data.
- [ ] Remaining XP and analytics inputs reflect only the records that were kept.
- [ ] Root CLI and persistence tests compare the preview and result with the records actually removed.
