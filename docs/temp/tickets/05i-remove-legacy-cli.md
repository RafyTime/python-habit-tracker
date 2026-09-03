# 05i: Remove the legacy CLI and verify the final contract

**What to build:** A user receives one finished `habit` interface with grouped generated help, no obsolete executable or nested command paths, consistent output and error behavior, and verified first-use and everyday journeys.

**Blocked by:** 05d: Edit, archive, and restore habits; 05e: Permanently delete with a specific impact warning; 05f: Inspect progress through stats and XP; 05h: Finish Quick start and safe sample-data guidance.

**Status:** done

- [x] The temporary `app` and `cli` executable aliases are removed, leaving only `habit` & `habits`.
- [x] The former habit, overview, analytics, and XP command groups and their obsolete tests are removed rather than retained as hidden aliases.
- [x] The final public commands match the approved CLI experience specification.
- [x] Typer continues to generate help, with commands grouped into Everyday, Progress, Manage, and Get started and evaluate panels.
- [x] Long and short options match the approved contract, including force rather than yes for confirmation bypass.
- [x] Version output remains available through its eager root option.
- [x] Every final command uses the shared presentation conventions and keeps complete meaning without color or decorative symbols.
- [x] Expected domain failures produce actionable messages and failed exits where the action failed.
- [x] Broad exception swallowing is removed, and unexpected errors are not disguised as recoverable user mistakes.
- [x] Root CLI journey tests cover fresh Quick start, add to done to stats, returning interactive use, advanced lifecycle commands, and non-interactive automation.
- [x] Pure analytics tests remain direct and independent of the CLI.
- [x] All formatter, lint, type, test, and coverage gates pass after legacy contraction.
