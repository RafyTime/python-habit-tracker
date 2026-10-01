# Completion and XP design session

Date: 2026-09-30

Shared understanding confirmed: 2026-10-01. No open design decisions remain.

Scope: candidate 01 from architecture-review-20260929-182508.html.

## Agreed decisions

- A completion, its completion XP, and all newly reached milestone awards succeed or roll back together.
- Preserve existing period, streak, and XP rules. This session concerns transaction ownership and the completion interface.
- Keep `HabitService.complete_habit()` as the public entry point and transaction owner. XP award helpers add records without committing.
- Every successful completion awards XP. Callers cannot opt out by omitting an XP collaborator.
- Preserve `(Completion, list[XPEvent])`, with the list containing newly awarded milestones. Returned fields remain readable after the producing session closes.
- Preserve the CLI's separate streak, level, and due-habit reads.

- Preserve caller-owned sessions for sample-data loading and tests. Each completion owns its commit and rollback; the caller owns the shared session's lifetime.
- Defer historical XP repair and stronger guarantees for concurrent milestone claims.

## Facts checked against the code

- Completion and XP award methods currently commit separately.
- Milestone awards use the longest historical streak. CLI feedback uses the current streak.
- Sample-data loading reuses a caller-owned session and passes backdated `when` values.
- Completion periods and completion XP have database uniqueness constraints. Milestone claims currently rely on lookup checks.

## Agreed validation criteria

- Failure during completion XP, milestone awards, or the final commit leaves no new completion or XP records.
- Retrying after rollback succeeds once; repeating a successful completion retains the existing duplicate-period error.
- Backdated sample history and returned-field access after session closure retain their existing behavior.

This records the design discussion. Implementation has not been authorized by this session.
