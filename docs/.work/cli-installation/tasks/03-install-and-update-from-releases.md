# 03. Install and update from GitHub Releases

Type: task
Status: ready
Blocked by: 02

## What to build

Make a versioned GitHub Release wheel the documented way for users with repository access to install and manually update `habit`. A user can check the new version and keep tracking from the same database after the update.

## Acceptance criteria

- [ ] Document how a maintainer builds and smoke-tests the exact wheel before attaching it to a versioned GitHub Release, with manual publication.
- [ ] Document how users obtain a release wheel, install it with uv, then install a newer wheel and verify the result with `habit --version`. The user steps work without a checkout.
- [ ] Rehearse the documented upgrade with two versioned wheels in the same isolated uv tool environment and a temporary per-user data location.
- [ ] The version changes after the upgrade. Running `habit` from another directory shows the existing Profile, active and archived Habits, Completions, and XP without copying or reconfiguring the database.
