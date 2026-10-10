# 05c: Complete a habit by name or ID

**What to build:** A user can mark an active habit done through the new root CLI by choosing it interactively or addressing it reliably by numeric ID or normalized name, then see restrained XP and streak feedback reflected in today's state.

**Blocked by:** 05b: Add and list recognizable habits (complete).

**Status:** done

- [x] `habit done` accepts an active habit's numeric ID or exact normalized name.
- [x] Multiword names can use underscores in place of spaces without changing the stored display name.
- [x] Explicit lookup is case-insensitive but never silently chooses a prefix or fuzzy match.
- [x] Omitting the selector in an interactive terminal opens a due-habit picker.
- [x] Omitting the selector in non-interactive use fails with a concrete `habit done NAME_OR_ID` example instead of waiting for input.
- [x] A successful completion persists once for the current daily or weekly period and awards the existing XP behavior.
- [x] Routine success feedback shows the habit name, current period, XP reward, and relevant streak without excessive celebration.
- [x] Streak or level milestones may use stronger celebratory feedback than routine completions.
- [x] Duplicate-period completion, archived selection, and missing habit failures produce actionable messages and correct exit behavior.
- [x] `habit today` reflects the persisted completion immediately.
- [x] Root CLI tests verify explicit, interactive, duplicate, archived, XP, milestone, and snapshot outcomes through isolated persistence.
