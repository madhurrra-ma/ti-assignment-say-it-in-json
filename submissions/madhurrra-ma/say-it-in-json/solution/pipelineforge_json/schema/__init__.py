from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).with_name("legacy_config.schema.json")


def load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_config_document(document: object) -> None:
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(document), key=lambda item: item.path)
    if errors:
        message = "; ".join(f"{'.'.join(str(p) for p in error.path) or '<root>'}: {error.message}" for error in errors)
        raise ValueError(f"Invalid JSON config: {message}")
