# 07a: Record Completion and XP atomically

**Parent:** 07 — Complete the final codebase cleanup and verification pass.

**What to build:** Marking a Habit done records its Completion, one completion XP, and every newly reached Milestone award as one operation. If any write fails, none of those new records remains, and the user can retry without losing rewards or creating duplicates. Existing CLI feedback and backdated Sample data behavior remain intact.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

## Acceptance criteria

- [ ] `HabitService.complete_habit()` remains the public entry point and owns one successful commit for the Completion and all associated XP awards.
- [ ] XP award helpers add records in that operation's session without committing independently. Completion creation, award checks, and Milestone calculation use the same session and see the pending Completion before the final commit.
- [ ] Every successful Completion earns one XP. Callers cannot silently omit awards by leaving out an XP collaborator, and existing callers and tests use this contract.
- [ ] An exception during Completion creation, completion XP, Milestone awards, or the final commit rolls back the operation and propagates the failure.
- [ ] Fault-injection tests verify persisted state through an independent session after failures during completion XP, partway through multiple Milestone awards, and the final commit. No new Completion or XP event remains; previously persisted history is unchanged.
- [ ] Retrying a rolled-back Completion succeeds once and awards the expected XP. Repeating a successful Completion retains the existing duplicate-Period error and adds no records.
- [ ] Existing ownership, Archived Habit, Daily Period, and ISO Weekly Period checks retain their behavior.
- [ ] Each Habit retains its once-only five-XP Milestone awards at the 3, 7, 14, and 30-Period thresholds. Milestone eligibility continues to use Longest streak, while CLI feedback continues to show Current streak.
- [ ] `when` continues to support backdated Completions and deterministic four-week Test fixture loading without changing the existing rules.
- [ ] Caller-owned sessions remain supported for Sample data and tests. Each Completion owns its commit and rollback, while the caller retains responsibility for the shared session's lifetime. Factory-owned session resources remain alive throughout the operation and are released afterward.
- [ ] The return contract remains `(Completion, list[XPEvent])`, with the list containing only newly awarded Milestones. Completion and Milestone fields remain readable after the producing session closes.
- [ ] The CLI retains its separate Current streak, Level, and Due habit reads, along with existing successful Completion, Milestone, and Level-up feedback.
- [ ] End-to-end checks cover a normal Completion, a Milestone-reaching Completion, a duplicate attempt, and backdated Sample data loading.
- [ ] Formatter, linter, type checker, and the full test suite pass.

## Scope limits

Preserve existing Period, streak, and XP rules and read-only XP behavior. Historical XP repair and stronger guarantees for concurrent Milestone claims are deferred. This ticket does not introduce a richer result object, a separate public Completion service, or an atomic transaction for the entire Sample data load.

## Design basis

Architecture review candidate 01, "Give Completion and XP one commit owner." Shared understanding was confirmed on 1 October 2026 after the design session.
