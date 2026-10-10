# 05d: Edit, archive, and restore habits

**What to build:** A user can correct a habit's name or icon, pause it without losing history, and later restore the same habit to active tracking through explicit and guided root commands.

**Blocked by:** 05c: Complete a habit by name or ID (complete).

**Status:** done

- [x] `habit edit`, `habit archive`, and `habit restore` work through the new root CLI with ID, normalized-name, and interactive selection forms.
- [x] Editing can change a displayed name or replace and explicitly clear an icon.
- [x] Supplying replacement and clear-icon choices together fails with an actionable message.
- [x] Editing does not offer repetition changes because existing completion period keys retain their original daily or weekly meaning.
- [x] Archived habits remain outside default selection and require explicit archived inclusion for editing.
- [x] Archiving removes a habit from active lists, due selection, and today while retaining its completions and XP.
- [x] Restoring returns the same habit, creation date, completions, and XP to active tracking.
- [x] Adding a globally matching archived name now directs the user to `habit restore` or a different name.
- [x] A normalized-name collision blocks edit or restore without silently renaming either habit.
- [x] Confirmation, force, cancellation, and expected failure output use the shared presentation conventions.
- [x] Root CLI and persistence tests cover active and archived editing, icon clearing, collisions, archive retention, restoration, cancellation, and refreshed active views.
