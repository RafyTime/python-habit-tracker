# 04 — Deliver a correct four-week evaluation fixture

**What to build:** The seed command creates a demonstrably valid evaluation dataset that an assessor can inspect and the tests can rely on: five predefined habits, daily and weekly examples, and four weeks of consistent history for each habit.

**Blocked by:** 02 — Replace profile selection with an automatic single profile.

**Status:** ready

- [ ] Seeding creates exactly the required predefined habits for the single profile, including daily and weekly habits.
- [ ] Every predefined habit has completion history spanning four weeks and a creation date that precedes its first completion.
- [ ] The dataset visibly demonstrates a long streak, a broken streak, weekly periodicity, and calendar-week edge cases.
- [ ] A supplied reference time makes the fixture deterministic and repeatable; repeat seeding is idempotent.
- [ ] XP events, milestone behaviour retained by the scope, and analytics results are consistent with the stored fixture records.
- [ ] Automated tests validate the complete seeded outcome rather than only individual insertions.
