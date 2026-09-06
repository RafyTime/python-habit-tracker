# 05l: Polish interactive presentation and editing

**What to build:** A user sees clearer card headings and consistent prompts, can inspect Settings before changing them, and can choose or edit a Habit Icon without pasting Unicode directly into a command.

**Blocked by:** None (can start immediately).

**Status:** complete

- [x] Cards use a prominent heading with a semantic symbol and written title supplied through the shared presentation system.
- [x] Symbols and color support written labels rather than carrying required meaning by themselves.
- [x] Interactive prompt groups receive consistent spacing and one shared selection style.
- [x] Prompt polish retains the existing Rich prompts, confirmations, Questionary selections, and live home menu instead of rebuilding every interaction as a live in-card view.
- [x] Selecting Settings from home first displays the current display name and after-action preference.
- [x] Interactive Settings then offers Change display name, Change after-action behavior, and Back without mutating values merely by opening the screen.
- [x] Interactive Edit with no requested mutation offers Change name, Change Icon, Clear Icon, and Back instead of starting with a rename prompt.
- [x] `--icon` acts as an interactive picker flag for Add and Edit and no longer accepts an inline value.
- [x] Calling `--icon` without an interactive terminal fails with an actionable message and does not change data.
- [x] The Add picker offers eight to twelve curated symbols, Custom symbol, No Icon, and cancellation.
- [x] The Edit picker also offers Keep current Icon and Clear Icon.
- [x] Explicit Add without `--icon` continues to store no Icon unless the command has already entered its guided interactive flow.
- [x] `--clear-icon` remains an explicit Edit shortcut.
- [x] Combining `--icon` with `--clear-icon` fails actionably without changing the Habit.
- [x] Habit names remain visible beside Icons in every output and picker.
- [x] Cancellation and Ctrl+C preserve the established clean return and exit behavior.
- [x] Root CLI tests cover semantic headings, readable labels, prompt separation, Settings view-before-edit behavior, the Edit action menu, every Icon outcome, conflicts, cancellation, and non-interactive failure.
- [x] Presentation tests assert meaning rather than exact borders, widths, colors, symbols, or terminal escape sequences.
