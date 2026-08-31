# PipelineForge JSON migration skeleton

This directory contains the minimal project skeleton for the PipelineForge "Say It in JSON" take-home assignment.

It is intentionally a scaffold only. Semantic implementation work is intentionally deferred.

## Structure

- `pipelineforge_json/` — package root
  - `legacy/` — legacy .pfcfg parser and evaluator modules
  - `schema/` — JSON Schema and schema helpers
  - `convert/` — converter and module generation
  - `json_evaluator/` — JSON evaluator for migrated configs
  - `verify/` — equivalence verification and reporting
  - `cli.py` — placeholder CLI entry point
- `tests/` — test skeletons

## Python and uv

This project targets Python 3.12 and uses `uv` for environment and dependency management.

## Dependency rationale

- `jsonschema` is used for formal JSON Schema validation. It is a small, widely used, well-maintained library that matches the requirement for explicit schema validation without introducing a large framework.
- `pytest` is included as a development dependency for later tests, but no semantic behavior is implemented yet.

## Usage

The CLI is intentionally a placeholder and is not yet connected to implementation behavior.

```bash
uv sync
uv run pipelineforge-json --help
```
