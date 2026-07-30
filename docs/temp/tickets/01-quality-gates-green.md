# 01 — Make the quality gates representative and green

**What to build:** Contributors can run one documented quality command locally and receive the same meaningful result that CI receives. The formatter, linter, type checker, and existing automated tests all pass without hiding source-code problems.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [x] The project quality script checks application and test code consistently, including formatting, linting, and source type checking.
- [x] The linter passes with no source suppressions; test-only unused fixture parameters are handled by a narrow pytest-aware configuration.
- [x] The type checker reports no diagnostics in application code, including session lifecycle and persisted-ID handling.
- [x] The full test suite remains green and CI uses the same checks.
