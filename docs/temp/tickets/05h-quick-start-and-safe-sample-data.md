# 05h: Finish Quick start and safe sample-data guidance

**What to build:** A beginner can use Quick start to personalize the tracker, create and complete a first habit or explore deterministic sample data on an empty database, then reach home with a visible link to deeper guidance.

**Blocked by:** 05d: Edit, archive, and restore habits; 05g: Use the essential workflow from interactive home.

**Status:** ready

- [ ] `habit start` welcomes the user and sets or retains the display name without exposing profile management.
- [ ] An empty database offers a personal first habit or the five predefined sample habits.
- [ ] The personal path collects a name, daily or weekly repetition, and an optional suggested, custom, or absent icon.
- [ ] The personal path offers one completion and shows the resulting routine XP and streak feedback.
- [ ] The sample path loads deterministic four-week histories with predefined icons and XP consistent with completions.
- [ ] Existing active or archived habits prevent Quick start from offering sample data automatically.
- [ ] Repeating Quick start never resets or deletes existing data.
- [ ] Explicit seeding warns before mixing fixture and personal data and requires confirmation unless forced.
- [ ] Forced and confirmed seeding remain deterministic and idempotent for the predefined habits.
- [ ] Cancelling any Quick start choice leaves completed earlier choices intact and returns or exits cleanly.
- [ ] Quick start opens the home screen after the chosen path.
- [ ] The ending prints the visible GitHub user-guide URL even when terminal hyperlinks are unsupported.
- [ ] Root CLI journey tests cover personal setup, sample setup, existing data, repeated guidance, seed warning and force behavior, cancellation, icons, and the guide URL.
