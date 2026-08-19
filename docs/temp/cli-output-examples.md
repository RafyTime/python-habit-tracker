# CLI output examples

These mockups capture the intended information hierarchy, voice, and semantic labels. They are optional design references, not golden snapshots or additional requirements. Borders, widths, wrapping, spacing, choice markers, and colors may adapt to the terminal and the Rich components used. Tests should assert meaning, not artwork.

## Interactive home

```text
Good evening, Alex

Today       ██████░░  3 of 4 done
Level 4     ✦ 7/10 XP

○ 📚 Read 10 Pages              today
○ 🏋 Gym Session                this week

What would you like to do?
> Mark a habit done
  Add a habit
  View habits
  View stats
  Settings
  Exit
```

The greeting, current-period progress, due habits, and secondary XP progress matter more than the exact panel or table layout. Daily and weekly due wording must stay distinct.

## Routine completion

```text
✓ Read 10 Pages is done for today.
  +1 XP · 4-day streak

Next: 2 habits are still waiting. Run `habit today`.
```

Routine completion feedback stays concise. Milestones may add stronger celebratory copy, but ordinary check-ins should not feel noisy.

## Permanent-delete warning

```text
Permanently delete "Read 10 Pages"?

This removes:
  18 completions
  24 XP
  all contribution to historical stats

This cannot be undone. Continue? [y/N]
```

The real completion and XP impact must appear before confirmation. Forced deletion skips the question but still reports what was removed.

## Quick start ending

```text
You're ready, Alex.

✓ Read 10 Pages is set for every day.
✓ First completion recorded. +1 XP

Run `habit` whenever you want to check in.
Full user guide:
https://github.com/RafyTime/python-habit-tracker/blob/main/docs/USER_GUIDE.md
```

The ending confirms the saved result, names the next everyday action, and leaves the full URL visible when terminal hyperlinks are unavailable.
