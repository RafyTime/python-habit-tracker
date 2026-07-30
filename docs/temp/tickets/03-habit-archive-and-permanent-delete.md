# 03 — Offer clear archive and permanent-delete habit lifecycles

**What to build:** Users can safely remove a habit from their day-to-day workflow by archiving it, or intentionally erase it and its dependent history through a clearly warned permanent-delete action.

**Blocked by:** 02 — Replace profile selection with an automatic single profile.

**Status:** ready-for-agent

- [ ] Archiving removes a habit from active lists and due prompts while retaining completion records and XP events.
- [ ] Permanent deletion requires confirmation unless explicitly forced and plainly states that completion history, XP, and historical analytics will change.
- [ ] Permanent deletion removes the habit and all dependent completion and XP records atomically; remaining XP totals and analytics reflect only remaining data.
- [ ] Current views exclude archived habits, while any historical analytics inclusion is explicit and labelled.
- [ ] CLI and service-level tests cover archive, forced and confirmed deletion, cancellation, and dependent-history effects.

