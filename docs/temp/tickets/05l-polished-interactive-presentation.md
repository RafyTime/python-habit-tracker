# 05l: Polish interactive presentation and editing

**What to build:** A user sees clearer card headings and consistent prompts, can inspect Settings before changing them, and can choose or edit a Habit Icon without pasting Unicode directly into a command.

**Blocked by:** None (can start immediately).

**Status:** ready

- [ ] Cards use a prominent heading with a semantic symbol and written title supplied through the shared presentation system.
- [ ] Symbols and color support written labels rather than carrying required meaning by themselves.
- [ ] Interactive prompt groups receive consistent spacing and one shared selection style.
- [ ] Prompt polish retains the existing Rich prompts, confirmations, Questionary selections, and live home menu instead of rebuilding every interaction as a live in-card view.
- [ ] Selecting Settings from home first displays the current display name and after-action preference.
- [ ] Interactive Settings then offers Change display name, Change after-action behavior, and Back without mutating values merely by opening the screen.
- [ ] Interactive Edit with no requested mutation offers Change name, Change Icon, Clear Icon, and Back instead of starting with a rename prompt.
- [ ] `--icon` acts as an interactive picker flag for Add and Edit and no longer accepts an inline value.
- [ ] Calling `--icon` without an interactive terminal fails with an actionable message and does not change data.
- [ ] The Add picker offers eight to twelve curated symbols, Custom symbol, No Icon, and cancellation.
- [ ] The Edit picker also offers Keep current Icon and Clear Icon.
- [ ] Explicit Add without `--icon` continues to store no Icon unless the command has already entered its guided interactive flow.
- [ ] `--clear-icon` remains an explicit Edit shortcut.
- [ ] Combining `--icon` with `--clear-icon` fails actionably without changing the Habit.
- [ ] Habit names remain visible beside Icons in every output and picker.
- [ ] Cancellation and Ctrl+C preserve the established clean return and exit behavior.
- [ ] Root CLI tests cover semantic headings, readable labels, prompt separation, Settings view-before-edit behavior, the Edit action menu, every Icon outcome, conflicts, cancellation, and non-interactive failure.
- [ ] Presentation tests assert meaning rather than exact borders, widths, colors, symbols, or terminal escape sequences.

