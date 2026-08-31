"""Placeholder CLI entry point for the PipelineForge JSON migration project."""

from __future__ import annotations

import argparse


def main() -> int:
    """Placeholder command-line entry for later implementation work."""
    parser = argparse.ArgumentParser(
        prog="pipelineforge-json",
        description="PipelineForge .pfcfg migration tooling",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display the package version and exit.",
    )
    args, _ = parser.parse_known_args()

    if args.version:
        from pipelineforge_json import __version__

        print(__version__)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
