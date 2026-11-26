# 01. Install a working habit command with uv

Type: task
Status: ready
Blocked by: none

## What to build

Make the packaged `habit` command installable with uv and usable outside the checkout. A fresh installation can initialize a Profile and report the version of the package it is running.

## Acceptance criteria

- [ ] A wheel built with the existing packaging setup installs as `habit` in an isolated uv tool environment using only the wheel's dependency metadata.
- [ ] From outside the checkout, `habit --help` runs and `habit --version` matches the wheel's version.
- [ ] With an explicit temporary SQLite database, `habit today` initializes a Profile and displays the empty habit list.
- [ ] Relevant existing CLI checks pass.
