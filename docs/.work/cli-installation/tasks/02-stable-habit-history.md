# 02. Open the same Habit history from any directory

Type: task
Status: ready
Blocked by: 01

## What to build

Give the installed CLI a stable per-user database so opening a new terminal in another directory keeps the same Profile and Habit history. Let developers and users select a different database explicitly. Document how checkout users can bring over their existing data once.

## Acceptance criteria

- [ ] With no override, the installed command initializes its SQLite database in the platform's per-user application data directory, outside the checkout and uv tool environment.
- [ ] With a temporary per-user data location, create and complete a Habit in one directory and verify the same Profile, Completion, and XP from another.
- [ ] An explicit `DATABASE_URL` still selects a separate database, including when configured through the checkout's `.env`.
- [ ] The guide identifies the default location and explains how to select a separate checkout database.
- [ ] Rehearse the documented one-time copy with temporary checkout data and the CLI closed during the copy. Verify that the installed CLI opens the copied history, the original stays intact, and an existing destination is protected.
- [ ] Relevant existing CLI checks pass with the existing SQLite schema.
