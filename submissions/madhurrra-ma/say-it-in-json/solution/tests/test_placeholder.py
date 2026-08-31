"""Placeholder test file for the project skeleton.

This intentionally validates only that the package imports and the CLI entry point is wired up.
No semantic behavior is implemented yet.
"""

from pipelineforge_json import __version__
from pipelineforge_json.cli import main


def test_version_is_present() -> None:
    assert __version__


def test_cli_main_returns_zero() -> None:
    assert main() == 0
