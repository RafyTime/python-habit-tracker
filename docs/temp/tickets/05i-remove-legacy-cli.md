# 05i: Remove the legacy CLI and verify the final contract

**What to build:** A user receives one finished `habit` interface with grouped generated help, no obsolete executable or nested command paths, consistent output and error behavior, and verified first-use and everyday journeys.

**Blocked by:** 05d: Edit, archive, and restore habits; 05e: Permanently delete with a specific impact warning; 05f: Inspect progress through stats and XP; 05h: Finish Quick start and safe sample-data guidance.

**Status:** ready

- [ ] The temporary `app` and `cli` executable aliases are removed, leaving only `habit`.
- [ ] The former habit, overview, analytics, and XP command groups and their obsolete tests are removed rather than retained as hidden aliases.
- [ ] The final public commands match the approved CLI experience specification.
- [ ] Typer continues to generate help, with commands grouped into Everyday, Progress, Manage, and Get started and evaluate panels.
- [ ] Long and short options match the approved contract, including force rather than yes for confirmation bypass.
- [ ] Version output remains available through its eager root option.
- [ ] Every final command uses the shared presentation conventions and keeps complete meaning without color or decorative symbols.
- [ ] Expected domain failures produce actionable messages and failed exits where the action failed.
- [ ] Broad exception swallowing is removed, and unexpected errors are not disguised as recoverable user mistakes.
- [ ] Root CLI journey tests cover fresh Quick start, add to done to stats, returning interactive use, advanced lifecycle commands, and non-interactive automation.
- [ ] Pure analytics tests remain direct and independent of the CLI.
- [ ] All formatter, lint, type, test, and coverage gates pass after legacy contraction.
