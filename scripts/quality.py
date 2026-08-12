"""Run the complete local and CI quality-gate suite."""

import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LINT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ('ruff', 'format', 'src', 'tests', 'scripts/quality.py', '--check'),
    ('ruff', 'check', 'src', 'tests', 'scripts/quality.py'),
    ('ty', 'check', 'src'),
)
TEST_COMMANDS: tuple[tuple[str, ...], ...] = (
    ('coverage', 'run', '-m', 'pytest', 'tests/'),
    ('coverage', 'report'),
)
QUALITY_COMMANDS = LINT_COMMANDS + TEST_COMMANDS
FORMAT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ('ruff', 'check', 'src', 'tests', 'scripts/quality.py', '--fix'),
    ('ruff', 'format', 'src', 'tests', 'scripts/quality.py'),
)


def _commands_for(workflow: str) -> tuple[tuple[str, ...], ...]:
    return {
        'quality': QUALITY_COMMANDS,
        'format': FORMAT_COMMANDS,
        'lint': LINT_COMMANDS,
        'test': TEST_COMMANDS,
    }[workflow]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'workflow',
        choices=('quality', 'format', 'lint', 'test'),
        default='quality',
        nargs='?',
    )
    arguments = parser.parse_args()

    for command in _commands_for(arguments.workflow):
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


if __name__ == '__main__':
    main()
