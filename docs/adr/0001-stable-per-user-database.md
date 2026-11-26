# Use a stable per-user database for the CLI

The CLI defaults to an absolute SQLite path in the platform's per-user application data directory so that switching directories or replacing the uv tool installation still opens the same Profile and Habit history. An explicit `DATABASE_URL` continues to select another database, including for checkout development. Existing checkout users can copy their database once because multiple working directories may contain different histories or sample data.
