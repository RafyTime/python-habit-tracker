"""Habit name identity comparison."""


def identity_key(name: str) -> str:
    """Return the comparison key for habit identity.

    Trims outer whitespace, treats underscores as spaces, collapses repeated
    whitespace, and ignores capitalization.
    """
    return ' '.join(name.strip().replace('_', ' ').split()).casefold()
