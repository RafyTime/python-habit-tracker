# 05 - Deliver the guided `habit` CLI experience

**What to build:** Replace the nested and inconsistent CLI with the agreed `habit` command contract, shared presentation system, small interactive home screen, and Quick start flow. Preserve complete explicit commands for documentation and automation.

**Sources:** [Guided CLI experience specification](../cli-experience-spec.md); [CLI experience polish specification](../cli-polish-spec.md)

**Blocked by:** 03 - Offer clear archive and permanent-delete habit lifecycles.

**Status:** ready

## Child tickets

- [x] [05a - Open the new CLI and see today](05a-open-habit-cli-and-see-today.md)
- [x] [05b - Add and list recognizable habits](05b-add-and-list-recognizable-habits.md)
- [x] [05c - Complete a habit by name or ID](05c-complete-habit-by-name-or-id.md)
- [x] [05d - Edit, archive, and restore habits](05d-edit-archive-and-restore-habits.md)
- [x] [05e - Permanently delete with a specific impact warning](05e-delete-with-impact-warning.md)
- [x] [05f - Inspect progress through stats and XP](05f-inspect-progress-stats-and-xp.md)
- [x] [05g - Use the essential workflow from interactive home](05g-interactive-home.md)
- [x] [05h - Finish Quick start and safe sample-data guidance](05h-quick-start-and-safe-sample-data.md)
- [x] [05i - Remove the legacy CLI and verify the final contract](05i-remove-legacy-cli.md)

### Post-delivery polish

- [ ] [05j - Show accurate current progress](05j-accurate-current-progress.md)
- [ ] [05k - Add focused Habit Stats details](05k-focused-habit-stats.md)
- [ ] [05l - Polish interactive presentation and editing](05l-polished-interactive-presentation.md)
- [ ] [05m - Teach the Habit journey in Quick start](05m-teach-the-habit-journey.md)

## Completion criteria

- [x] `habit` and `habits` are the only installed executables and the obsolete command hierarchy is gone.
- [x] Every core action has a tested explicit form, while prompts appear only in interactive use.
- [x] The home screen, habit lifecycle, stats, XP, settings, and seeding use one presentation convention.
- [x] Bare `habit` supports both interactive-terminal and read-only non-interactive behavior.
- [x] Quick start reaches the first completion without profile setup or memorized commands.
- [x] Feature code remains separated by domain and `main.py` remains an application-composition module.
- [x] Expected domain failures are actionable and unexpected exceptions are not silently hidden.
- [x] CLI journey tests cover persisted outcomes, cancellation, destructive warnings, and readable output.
