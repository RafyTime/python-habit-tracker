# 05 — Make the core CLI guided and visually consistent

**What to build:** A user can follow create, list, complete, due, archive/delete, overview, and analytics commands through consistent output and useful next-step guidance, whether they use arguments or optional interactive prompts.

**Blocked by:** 03 — Offer clear archive and permanent-delete habit lifecycles.

**Status:** ready-for-agent

- [ ] Core commands have non-interactive forms suitable for documentation and automation, with optional prompts only where they improve discovery.
- [ ] Headings, tables, confirmations, recoverable errors, warnings, and next-step messages follow one shared presentation convention.
- [ ] The daily overview, habit commands, XP output, and analytics communicate active versus historical data consistently.
- [ ] Broad exception swallowing is removed; expected domain errors give actionable messages and unexpected errors are not silently hidden.
- [ ] CLI tests demonstrate the first-use and everyday happy paths from command input to persisted outcome and readable output.

