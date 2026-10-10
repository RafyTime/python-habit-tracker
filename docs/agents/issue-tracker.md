# Local issue tracker

Specs and tasks live as Markdown files under `docs/.work/<feature>/`. Use this tracker when a skill asks to publish or fetch an issue; the GitHub remote does not change this convention.

## Conventions

- Use a descriptive feature slug for each directory.
- Store new specs at `docs/.work/<feature>/spec.md`.
- Store one task per file at `docs/.work/<feature>/tasks/<NN>-<slug>.md`, numbered from `01`.
- Read a task by its path or by its identifier within the specified feature. Existing identifiers such as `05a` remain valid.
- Record `Status:` near the top. Use [the triage vocabulary](triage-labels.md).
- Record dependencies as `Blocked by: <id>, <id>` within the same feature, or use a relative path for another feature. Use `Blocked by: none` when there are no dependencies.
- Append discussion under `## Comments` rather than overwriting earlier comments.
- Mark completed tasks `Status: done`. Existing bold metadata headings remain valid.

## Wayfinding

- Store the effort's map at `docs/.work/<feature>/map.md` and its child tasks in `tasks/`.
- Record each child's `Type:` as `research`, `prototype`, `grilling`, or `task`.
- Choose the first task in identifier order that is ready, unclaimed, and has no unfinished blockers. A blocker is finished when its status is `done` or legacy `resolved`.
- Claim a task by recording `Status: claimed` before starting work.
- Resolve a task by appending its answer under `## Answer`, setting `Status: done`, and adding a summary and link to the map's decisions.
