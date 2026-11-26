# Install and update the habit CLI

Status: ready
Blocked by: none

## Problem Statement

To use `habit` today, a user typically clones the repository, sets up the project environment, and runs commands from the checkout. Someone who installs the existing package can appear to lose their Profile and Habit history when they switch directories because the default SQLite path is relative to the working directory. A fresh package install can also resolve newer dependencies that prevent the CLI from creating the first Profile.

## Solution

Users with repository access install a versioned wheel from a GitHub Release using uv. They can run `habit` from any directory and install a newer release when they choose. The CLI opens the same per-user database across directories and updates. Users who want to bring over an existing checkout database can follow a one-time copy procedure.

## User Stories

1. As a user with repository access, I want to install a GitHub Release with uv, so that I can use the tracker without cloning the repository.
2. As a reviewer, I want to install a specific release version, so that I can evaluate the same build as someone else.
3. As a first-time user, I want the installed `habit` command to initialize a fresh Profile, so that I can start tracking immediately.
4. As a user, I want to run the same `habit` commands after installation, so that the existing guide and workflows still apply.
5. As a user, I want to see my installed version with `habit --version`, so that I can verify which release I am running.
6. As a user, I want the same Profile and habits to open from different directories, so that I can track a Completion wherever I open a terminal.
7. As a user, I want to choose when to install a newer release, so that updates happen when I am ready.
8. As a user, I want my Profile preferences, active and archived habits, Completions, and XP to carry through an update, so that I can continue tracking without moving my data.
9. As an existing checkout user, I want instructions for copying my database once, so that I can keep my Habit history in the installed CLI.
10. As an existing checkout user, I want that copy to preserve my source file and any database already at the destination, so that I can protect both sets of data.
11. As a developer, I want to select the checkout database explicitly, so that development commands can use data separate from my installed CLI.
12. As a user with a custom database, I want `DATABASE_URL` to keep selecting it, so that I can continue using my setup.
13. As a release maintainer, I want the wheel to declare compatible runtime dependencies, so that a normal uv installation can start successfully.
14. As a release maintainer, I want to smoke-test the wheel I plan to attach to the release, so that I can catch failures that the checkout tests miss.

## Implementation Decisions

- Keep the existing Hatchling build and `habit` entry point. Build a wheel for each versioned GitHub Release. Start with manual publication and document uv installation and manual updates from release assets for users with repository access.
- Use package metadata as the source of the release version shown by `habit --version`.
- Declare compatible constraints for the affected runtime dependencies in package metadata. A normal uv tool install must work without a separate constraints file.
- Default to a stable absolute SQLite path in the platform's per-user application data directory. Store it outside the checkout and uv's tool environment. See [the database location ADR](../../adr/0001-stable-per-user-database.md).
- Keep `DATABASE_URL` overrides, including the checkout's explicit `.env` configuration for development. Document the default location and how to opt into a separate checkout database.
- Document an optional one-time copy of a checkout database while the tracker is closed. Retain the original and never overwrite an existing destination as part of the documented procedure.
- Keep the SQLite schema and existing habit, Profile, and XP behavior.

## Testing Decisions

- Use the installed `habit` executable as the main test entry point. Assert observable outputs and persisted data through documented commands. Reuse the approach of the existing clean-database subprocess smoke test and CLI journeys.
- Build the wheel and install it with uv in an isolated tool environment using the wheel's dependency metadata. Run from outside the checkout. Check that help runs, the version matches the release, and first launch initializes a new Profile.
- Isolate the per-user data location, then create and complete a habit from one directory. Read it from another directory and verify the same Completion and XP.
- Install a newer version into the same tool environment. Check that the reported version changes and the existing Profile and Habit history reopen automatically.
- Exercise the explicit database override through the installed CLI. Rehearse the documented one-time copy using temporary checkout data and verify that the source remains intact and an existing destination is protected.
- Run the existing source checks for the commands and behavior this change touches. Use temporary databases throughout.

## Out of Scope

- Public package-index publishing, standalone executables, automatic updates, and release publication automation.
- Automatic discovery, adoption, or merging of checkout databases.
- Database schema migrations, timestamp storage changes, and changes to habit workflows.

## Further Notes

The current wheel built and installed successfully. On a clean database, `habit today` failed during Profile creation with SQLModel 0.0.50 and SQLAlchemy 2.1.9 because a stored datetime lacked timezone information. The same wheel passed with the repository's locked dependencies, including SQLModel 0.0.42 and SQLAlchemy 2.0.44. Verify the chosen package constraints through a fresh wheel installation.
