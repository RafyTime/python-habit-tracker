"""Read a single keypress for in-card menus."""

from __future__ import annotations

import importlib.util
import select
import sys


def read_key() -> str:
    """Return 'up', 'down', 'enter', 'esc', or a single character."""
    if importlib.util.find_spec('termios') is None:
        return _read_key_windows()
    return _read_key_posix()


def _read_key_posix() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x03':
            raise KeyboardInterrupt
        if ch == '\x1b':
            if select.select([sys.stdin], [], [], 0.05)[0]:
                rest = sys.stdin.read(2)
                return {'[A': 'up', '[B': 'down'}.get(rest, 'esc')
            return 'esc'
        if ch in ('\r', '\n'):
            return 'enter'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_key_windows() -> str:
    import msvcrt

    ch = msvcrt.getwch()
    if ch == '\x03':
        raise KeyboardInterrupt
    if ch in ('\x00', '\xe0'):
        extra = msvcrt.getwch()
        return {'H': 'up', 'P': 'down'}.get(extra, '')
    if ch in ('\r', '\n'):
        return 'enter'
    if ch == '\x1b':
        return 'esc'
    return ch
