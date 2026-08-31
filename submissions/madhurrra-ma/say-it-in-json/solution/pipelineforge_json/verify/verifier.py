from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pipelineforge_json.convert import convert_file
from pipelineforge_json.json_evaluator import evaluate_json
from pipelineforge_json.legacy.evaluator import evaluate_file


def verify_file(path: str | Path, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Compare legacy and JSON effective settings for one .pfcfg file."""
    file_path = Path(path)
    try:
        legacy_effective = evaluate_file(file_path, env=env)
    except Exception as exc:  # pragma: no cover - exercised via tests
        return {
            "path": str(file_path),
            "status": "ERROR",
            "error": f"Legacy evaluation failed: {type(exc).__name__}: {exc}",
            "details": None,
        }

    try:
        converted = convert_file(file_path)
    except Exception as exc:  # pragma: no cover - exercised via tests
        return {
            "path": str(file_path),
            "status": "ERROR",
            "error": f"Conversion failed: {type(exc).__name__}: {exc}",
            "details": None,
        }

    try:
        json_effective = evaluate_json(converted, env=env)
    except Exception as exc:  # pragma: no cover - exercised via tests
        return {
            "path": str(file_path),
            "status": "ERROR",
            "error": f"JSON evaluation failed: {type(exc).__name__}: {exc}",
            "details": None,
        }

    result = compare_effective_settings(legacy_effective, json_effective)
    result["path"] = str(file_path)
    return result


def compare_effective_settings(
    legacy: Mapping[str, Any],
    json_effective: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a structured comparison report for two effective settings dicts."""
    differences: list[dict[str, Any]] = []

    all_sections = sorted(set(legacy) | set(json_effective))
    for section_name in all_sections:
        legacy_section = legacy.get(section_name, {})
        json_section = json_effective.get(section_name, {})
        all_keys = sorted(set(legacy_section) | set(json_section))

        for key in all_keys:
            legacy_value = legacy_section.get(key)
            json_value = json_section.get(key)
            if legacy_value != json_value:
                differences.append(
                    {
                        "section": section_name,
                        "key": key,
                        "legacy": legacy_value,
                        "json": json_value,
                    }
                )

    if differences:
        return {
            "status": "MISMATCH",
            "differences": differences,
            "error": None,
        }

    return {
        "status": "MATCH",
        "differences": [],
        "error": None,
    }
