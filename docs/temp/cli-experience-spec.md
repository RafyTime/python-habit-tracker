# Guided CLI experience specification

The [CLI experience polish specification](./cli-polish-spec.md) records the final post-delivery refinements and is authoritative where it narrows or changes this contract.

## Problem Statement

The tracker contains most of its required business behavior, but the command line exposes that behavior through redundant executable names, nested command groups, technical vocabulary, duplicated rendering, and isolated outputs that do not form a clear journey. A beginner must learn commands before reaching the main habit loop, while a returning user receives little help understanding what is due or what to do next. Profile settings, XP, the daily overview, and sample data exist, but they do not yet feel like parts of one product.

The final Phase 2 experience needs a shorter command contract, a restrained interactive entrance, complete non-interactive commands, and one visual language. This work must improve the public interface without collapsing the feature modules or moving business rules into presentation code.

## Solution

Install one `habit` executable and expose frequent actions directly beneath it with plain language. Bare `habit` becomes a dual-mode entrance: it opens a small home screen and action menu in an interactive terminal, or prints a read-only daily snapshot when interaction is unavailable. A Quick start flow takes a beginner through their display name, first Habit or Sample data, first Completion, and a choice to enter the home screen or exit.

Keep explicit commands for every core action. Add optional habit icons, globally reliable name selection, safe editing, reversible archiving, specific permanent-delete warnings, compact stats, meaningful settings, grouped generated help, and shared presentation components. Keep lifecycle, analytics, home, XP, settings, seeding, interactive orchestration, and rendering in focused modules that call the existing services and pure analytics functions.

## User Stories

1. As a first-time user, I want to run one memorable executable, so that installation instructions do not give me competing entry points.
2. As a first-time user, I want bare `habit` to show me where to start, so that I do not need to read the full command reference before using the tracker.
3. As a returning user, I want bare `habit` to show my current progress, so that I can decide what to do next at a glance.
4. As a user in a non-interactive environment, I want bare `habit` to print a useful snapshot and exit, so that terminal capture and evaluation scripts do not hang on a prompt.
5. As a user, I want an explicit command for every core action, so that documentation and automation do not depend on an interactive menu.
6. As a user, I want missing information to open a prompt only in an interactive terminal, so that commands are helpful to people and predictable for scripts.
7. As a user, I want to cancel a picker without losing my whole interactive session, so that exploration is forgiving.
8. As a user, I want Ctrl+C to exit cleanly, so that cancelling the application does not show a traceback.
9. As a new user, I want Quick start to explain only the main habit loop, so that onboarding stays short.
10. As a new user, I want to choose between my own first habit and sample data on an empty database, so that I can either begin tracking or explore the finished project.
11. As a user with existing data, I want Quick start to preserve it, so that repeating guidance cannot reset my tracker.
12. As a user, I want Quick start to offer one completion, so that I see habit progress, XP, and streak feedback in context.
13. As a user, I want Quick start to point to the full user guide, so that advanced lifecycle and troubleshooting help remains available without lengthening onboarding.
14. As a user, I want to set a display name, so that greetings feel personal without introducing account management.
15. As a user, I want to choose whether an interactive action returns home or exits, so that the menu fits my preferred working style.
16. As a user, I want to add a habit with `day`, `daily`, `week`, or `weekly`, so that a natural wording choice does not cause an avoidable error.
17. As a user, I want repetition displayed as Daily or Weekly, so that internal terminology does not leak into ordinary output.
18. As a user, I want to add an optional icon, so that I can recognize habits quickly in lists and prompts.
19. As a user, I want to enter my own short Unicode icon or choose no icon, so that customization is not limited to a fixed catalog.
20. As a user, I want habit names to remain visible beside icons, so that output stays understandable when symbols do not render.
21. As a user, I want to change a habit's name or icon, so that small mistakes do not require deleting history.
22. As a user, I want to clear an icon explicitly, so that removal cannot be confused with a literal icon value.
23. As a user, I want completed history to retain its original daily or weekly meaning, so that editing cannot silently reinterpret old periods.
24. As a user, I want to select a habit by ID or name, so that both precise and readable command forms are available.
25. As a user, I want name matching to ignore capitalization, repeated whitespace, and underscores used in place of spaces, so that shell quoting and typing details do not get in my way.
26. As a user, I want commands to reject ambiguous guesses, so that the tracker never modifies the wrong habit.
27. As a user, I want active and archived habits to share one normalized name namespace, so that restoring a habit cannot create confusing duplicates.
28. As a user adding an archived habit's name, I want guidance to restore the existing habit or choose another name, so that old history is not accidentally abandoned.
29. As a user, I want to see the habits due today or this week, so that daily and weekly work is easy to distinguish.
30. As a user, I want routine completion feedback to show XP and relevant streak progress without excessive celebration, so that repeated use stays pleasant.
31. As a user, I want milestones to stand out from routine completions, so that meaningful progress feels different.
32. As a user, I want to archive a habit without losing its completions or XP, so that I can pause tracking safely.
33. As a user, I want to restore an archived habit, so that archive is reversible.
34. As a user, I want permanent deletion to state the actual completion and XP impact, so that confirmation is specific to my data.
35. As a user forcing permanent deletion, I want confirmation skipped but the result still reported, so that automation remains transparent.
36. As a user, I want active views to exclude archived habits by default, so that my current workflow stays focused.
37. As a user, I want archived history included only through an explicit labelled option, so that current and historical results are not confused.
38. As a user, I want a compact overall stats summary, so that active habit counts, completion counts, and the longest streak are available together.
39. As a user, I want stats for one habit, so that I can see its repetition, status, completion count, and longest streak.
40. As a user, I want XP status and recent XP history through one command, so that the old nested status and log commands are unnecessary.
41. As an evaluator, I want deterministic sample data to remain directly seedable, so that the four-week fixture can be inspected reliably.
42. As a user with personal data, I want seeding to warn before mixing sample habits into my tracker, so that fixture data is never added by surprise.
43. As a user, I want consistent headings, tables, progress, warnings, errors, and next steps, so that I can scan every command the same way.
44. As a user without color or reliable Unicode rendering, I want text to preserve the full meaning, so that the CLI remains accessible and testable.
45. As a user viewing help, I want flat commands grouped by purpose, so that shorter paths do not create an unstructured command list.
46. As a contributor, I want flat public commands to remain implemented in focused feature modules, so that better UX does not weaken encapsulation.
47. As a contributor, I want CLI tests to exercise persisted outcomes through the root application, so that the public contract is the main test seam.
48. As a contributor, I want pure analytics tested directly, so that functional logic remains deterministic and independent of rendering.

## Implementation Decisions

- The installed executable is `habit`. The obsolete `app` and `cli` entry points are removed without compatibility aliases because the project has not been released as a stable public tool.
- The public commands are `start`, `today`, `add`, `done`, `list`, `edit`, `archive`, `restore`, `delete`, `stats`, `xp`, `settings`, and `seed`. The former habit, overview, analytics, and XP command groups are removed.
- Typer remains responsible for generated help. Rich help panels group commands into Everyday, Progress, Manage, and Get started and evaluate sections.
- The main application module owns composition, initialization, version handling, and root registration. It does not absorb feature command implementations.
- Habit lifecycle, analytics, home and overview, XP, settings, seeding, interactive orchestration, and presentation remain focused modules.
- The basic interactive home menu contains Mark a habit done, Add a habit, View habits, View stats, Settings, and Exit. Edit, archive, restore, delete, XP history, and seeding remain explicit commands.
- Bare `habit` opens the home menu only when an interactive terminal is available. Otherwise it renders the same read-only snapshot as `habit today` and exits successfully.
- Interactive actions return to a refreshed home screen by default. The single persisted profile stores an after-action preference with `home` and `exit` values.
- Missing arguments prompt only in interactive use. Non-interactive omissions return a failed exit and a concrete command example.
- Cancelling a picker returns to the previous menu. Ctrl+C exits cleanly without an application traceback.
- `Periodicity`, `Analytics`, and `Test fixture` are the canonical domain and assignment terms. User-facing language uses `Repetition`, `Stats`, and `Sample data` for those same concepts, alongside add, done, every, and today.
- The repetition option accepts day, daily, week, and weekly. Output consistently displays Daily or Weekly.
- A habit's periodicity is immutable after creation because completion period keys encode the original Daily or Weekly meaning. The CLI presents Periodicity as Repetition.
- Habit selection accepts a numeric ID or an exact normalized name. Normalization trims outer whitespace, treats underscores as spaces, collapses repeated whitespace, and performs case-insensitive comparison.
- The application preserves the user's original habit spelling for display. Normalization applies only to identity comparison and lookup.
- Active and archived habits share global normalized-name uniqueness. Attempting to add an archived match recommends restoring it or choosing another name.
- Failed name lookup may show suggestions, but the application never silently chooses a prefix or fuzzy match.
- A habit has an optional short, single-line Unicode icon. The application does not attempt to classify whether the value is an emoji.
- The icon is nullable. The after-action preference defaults to home. Local SQLite files are disposable: a schema change may delete the file and start again. Do not add migration code to keep old databases.
- Explicit creation stores no icon unless the interactive `--icon` picker is requested. Interactive creation offers a small suggested set, custom input, and no icon. The picker flag fails actionably when interaction is unavailable, and seeded habits receive predefined icons.
- Editing changes only a habit's displayed name and icon. Interactive editing begins with a choice of mutation rather than assuming a rename. Archived editing requires explicit archived inclusion, and a dedicated clear-icon option remains available.
- Archive hides a habit from active and due views while preserving completions and XP. Restore returns the same habit and history to active tracking.
- Delete calculates the completion count and XP amount that will be removed before confirmation. Force skips the prompt but still prints the affected result. The service layer owns the destructive operation and its impact data.
- Active lists and stats exclude archived habits by default. Archived inclusion is explicit and labelled.
- Habit lists show ID, Habit, current-period Progress, Current streak, and Repetition. Progress uses Due, Done, or Archived without replacing lifecycle Status. Current streak is derived separately from historical Longest streak.
- `habit today` remains Due-only by default. `--done` includes completed Active habits after Due habits in the same Daily or Weekly group; Archived habits remain excluded, and bare `habit` keeps its Due-only snapshot.
- Overall stats show active daily and weekly counts, recorded completion count, and the Longest streak. Per-habit stats also show repetition, lifecycle Status, completion count, Longest streak, XP earned, and latest Completion.
- Pure analytics functions remain responsible for Current and Longest streak calculations. Simple persisted counts and dates do not introduce a second analytics rule set.
- XP status and recent history share one public command. XP remains secondary on the home screen.
- Bare settings displays the display name and after-action preference. Explicit options update them without prompts, while Settings from home shows the current values before offering individual changes or a return action.
- Quick start sets or retains the display name, teaches Habits and Repetition, offers a personal habit or Sample data on an empty database, and prints the explicit commands behind its guided actions. The personal path offers one Completion through the normal Done interaction, explains XP, Current streaks, Milestones, and focused Stats in context, then lets the user enter home or exit.
- Quick start never resets existing data and does not offer sample data automatically when habits already exist.
- Explicit seeding warns before mixing fixture data with existing active or archived habits. Force bypasses confirmation, and fixture creation remains deterministic and idempotent.
- A habit earns five bonus XP once when it first reaches each of the 3, 7, 14, and 30-period Milestones. Milestone claims belong to the habit identity, survive archive and restoration, and are removed by permanent deletion. Reusing a deleted habit name creates a new identity with its own possible claims. Level changes may receive stronger presentation but do not award XP.
- One shared presentation module owns semantic card headings, prompt spacing and styling, tables, progress, success, warnings, recoverable errors, confirmations, and contextual next steps.
- Output uses calm, supportive language. Routine completion feedback stays restrained, while Milestones and level changes may use stronger celebration.
- Icons, semantic symbols, and colors support written labels. The text remains complete without styling.
- Expected domain failures become actionable user messages with failed exits where the action failed. Unexpected exceptions are not broadly swallowed.

## Testing Decisions

- The primary test seam is the root CLI with an isolated SQLite database. Tests invoke public commands, inspect exit behavior and readable text, then verify persisted outcomes.
- Pure analytics functions remain the second test seam because they are already independent of persistence and presentation. Their existing direct tests remain prior art for streak behavior and archived inclusion.
- Existing command tests remain prior art for isolated database injection, interactive prompt mocking, completion and XP outcomes, lifecycle safety, seed determinism, and archived analytics labels. Tests that encode obsolete command paths are reorganized or replaced.
- Command-contract tests verify the single executable, flat commands, Rich help groups, long and short options, accepted repetition aliases, and absence of old command paths.
- Mode tests distinguish interactive prompting from non-interactive failure, including bare-command snapshot behavior, missing arguments, cancellation, Ctrl+C, and the after-action preference.
- Quick start tests cover a personal first habit, one Completion through the normal Done interaction, Sample data on an empty database, existing data, no Due habits, cancellation, visible explicit commands, focused Stats, home entry or exit, and the visible user guide URL.
- Name tests cover IDs, capitalization, outer and repeated whitespace, underscores, global active and archived uniqueness, archived restore guidance, edit collisions, and non-guessing lookup failures.
- Icon tests cover the interactive picker flag, suggested and custom values, no icon, seeded defaults, editing, keeping, clearing, cancellation, non-interactive failure, and rendering the habit name beside the icon.
- Lifecycle tests cover archive history retention, restoration, archived editing, delete impact preview, confirmed deletion, forced deletion, cancellation, and the records actually removed.
- Milestone tests cover the 3, 7, 14, and 30-period thresholds, each one-time five-XP award, rebuilding a claimed threshold without another award, retention through archive and restoration, removal through permanent deletion, and a new habit identity reusing a deleted name.
- Presentation tests assert stable meaning rather than terminal escape sequences or exact decorative styling. Text-only output must still identify statuses, warnings, names, and next actions.
- Current streak tests cover Daily and Weekly Habits, completed and pending current Periods, gaps, restarts, no history, and ISO week boundaries through pure Analytics. CLI tests cover the corresponding running, pending, Broken, and not-started List meanings.
- Today tests cover the Due-only default and `--done` inclusion in Daily and Weekly groups while continuing to exclude Archived Habits.
- Stats tests cover empty data, overall counts, per-habit counts, Longest streaks, XP earned, latest Completion, active defaults, and explicitly labelled archived inclusion.
- Seed tests cover empty and nonempty databases, warning and force behavior, deterministic reference time, idempotence, icons, complete four-week histories, and XP consistency.
- Error tests cover expected domain failures with actionable exits and verify that unexpected errors are not converted into generic recoverable messages.

## Out of Scope

- Multiple accounts, profile creation, profile switching, authentication, and cloud synchronization.
- Custom repetition intervals, negative habits, and changing a habit's daily or weekly repetition after creation.
- Week-start preferences. Period keys continue to use local calendar dates and ISO weeks unless a later timezone specification changes that contract.
- Reminders, notifications, scheduled background work, and calendar integrations.
- XP controls, penalties, or new reward mechanics beyond completion rewards and the retained 3, 7, 14, and 30-period Milestones.
- Completion rates, missed-period reports, monthly trends, charts, and a finalized extended-stats command.
- Web, REST, desktop GUI, and mobile interfaces.
- Compatibility aliases for the old executables or nested commands.
- Migrations or compatibility code for old local SQLite files. Delete the database file and start again after a schema change.
- Automatic emoji recognition, a large icon catalog, or automatic icon selection from habit names.
- Rewriting the submitted Phase 1 conception document.

## Further Notes

- The success path is `habit` to Quick start to add to done to stats without profile setup or memorized commands.
- The visible user guide URL is `https://github.com/RafyTime/python-habit-tracker/blob/main/docs/USER_GUIDE.md`.
- Timezone handling beyond the current local-calendar baseline remains undecided. A later specification may define a user-configured timezone, a system-derived default, or behavior when that timezone changes; this specification neither promises nor forbids that extension.
- Richer analytics remain a possible Phase 3 extension. Their eventual command shape should be chosen when those requirements are defined rather than reserved now.
- The specification deliberately treats the root CLI and pure analytics as the two observable testing seams. New presentation or orchestration helpers should be tested through those seams unless they contain independently meaningful pure logic.
- Local SQLite databases are disposable during development. Schema changes may replace the database instead of preserving historical migrations, provided the application code and schema remain aligned. Runtime commands still follow their documented data-safety rules.
- Agents working on user-facing CLI layout or copy may consult the optional [CLI output examples](./cli-output-examples.md). The examples illustrate the intended presentation but do not add requirements to this specification.
- Always check CONTEXT.md to make proper use of the stablished domain language.
