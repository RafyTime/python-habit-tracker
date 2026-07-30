# 02 — Replace profile selection with an automatic single profile

**What to build:** A user can open a fresh database and immediately create, complete, and analyse habits. One automatic profile supplies a customizable display name without account creation, switching, or deletion workflows.

**Blocked by:** 01 — Make the quality gates representative and green.

**Status:** done

- [x] A fresh installation has one usable profile automatically, with no profile command required before habit commands work.
- [x] Users can view and change the single profile's minimum customization through one simple settings interaction.
- [x] The normal CLI help and next-step guidance no longer direct users to create or switch profiles.
- [x] Existing data migrates conservatively to one profile without losing that profile's habits, completions, or XP history.
- [x] Command-level tests cover fresh startup, customization, and migration behaviour.
