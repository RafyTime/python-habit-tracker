"""Contract tests for the local and CI quality-gate configuration."""

import tomllib
from pathlib import Path

from scripts.quality import (
    FORMAT_COMMANDS,
    LINT_COMMANDS,
    QUALITY_COMMANDS,
    TEST_COMMANDS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_COMMAND = 'uv run scripts/quality.py'


def _read_project_file(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding='utf-8')


def test_quality_script_runs_every_required_gate() -> None:
    assert LINT_COMMANDS == (
        ('ruff', 'format', 'src', 'tests', 'scripts/quality.py', '--check'),
        ('ruff', 'check', 'src', 'tests', 'scripts/quality.py'),
        ('ty', 'check', 'src'),
    )
    assert TEST_COMMANDS == (
        ('coverage', 'run', '-m', 'pytest', 'tests/'),
        ('coverage', 'report'),
        ('coverage', 'html', '--title', 'coverage'),
    )
    assert QUALITY_COMMANDS == LINT_COMMANDS + TEST_COMMANDS
    assert FORMAT_COMMANDS == (
        ('ruff', 'check', 'src', 'tests', 'scripts/quality.py', '--fix'),
        ('ruff', 'format', 'src', 'tests', 'scripts/quality.py'),
    )


def test_legacy_shell_helpers_delegate_to_the_quality_runner() -> None:
    assert 'python scripts/quality.py format' in _read_project_file('scripts/format.sh')
    assert 'python scripts/quality.py lint' in _read_project_file('scripts/lint.sh')
    assert 'python scripts/quality.py test' in _read_project_file('scripts/test.sh')


def test_ci_and_readme_use_the_same_quality_command() -> None:
    assert QUALITY_COMMAND in _read_project_file('.github/workflows/ci.yml')
    assert QUALITY_COMMAND in _read_project_file('README.md')


def test_unused_fixture_arguments_are_ignored_only_in_tests() -> None:
    with (PROJECT_ROOT / 'pyproject.toml').open('rb') as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    lint_config = pyproject['tool']['ruff']['lint']

    assert 'ARG001' in lint_config['select']
    assert lint_config['per-file-ignores'] == {'tests/**/*.py': ['ARG001']}
