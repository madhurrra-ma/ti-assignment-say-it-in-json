from __future__ import annotations

from pathlib import Path

import pytest

from pipelineforge_json.legacy.evaluator import evaluate_file
from pipelineforge_json.verify import compare_effective_settings, verify_file


def test_missing_and_empty_environment_values_are_handled(tmp_path: Path) -> None:
    main = tmp_path / "missing-empty-values.pfcfg"
    main.write_text(
        "@ifdef MISSING_VAR\n[build]\nmode = set\n@endif\n"
        "@ifndef MISSING_VAR\n[build]\nmode = missing\n@endif\n"
        "@ifdef EMPTY_VAR\n[build]\nempty_mode = set\n@endif\n"
        "@ifndef EMPTY_VAR\n[build]\nempty_mode = empty\n@endif\n"
        "[runtime]\nvalue = ${MISSING_VAR:-fallback}\nempty_value = ${EMPTY_VAR:-fallback}\n",
        encoding="utf-8",
    )

    result = evaluate_file(main, env={"EMPTY_VAR": ""})

    assert result["build"]["mode"] == "missing"
    assert result["build"]["empty_mode"] == "empty"
    assert result["runtime"]["value"] == "fallback"
    assert result["runtime"]["empty_value"] == "fallback"


def test_nested_conditionals_select_expected_branch(tmp_path: Path) -> None:
    main = tmp_path / "nested-conditionals.pfcfg"
    main.write_text(
        "@ifdef OUTER\n"
        "@ifdef INNER\n[build]\nmode = both\n@endif\n"
        "@ifndef INNER\n[build]\nmode = outer-only\n@endif\n"
        "@endif\n",
        encoding="utf-8",
    )

    assert evaluate_file(main, env={"OUTER": "1", "INNER": "1"})["build"]["mode"] == "both"
    assert evaluate_file(main, env={"OUTER": "1"})["build"]["mode"] == "outer-only"


def test_include_once_prevents_duplicate_loads(tmp_path: Path) -> None:
    shared = tmp_path / "include-once-shared.pfcfg"
    shared.write_text("[build]\nvalue = shared\n", encoding="utf-8")
    main = tmp_path / "include-once-main.pfcfg"
    main.write_text(
        f"@include_once {shared}\n"
        f"@include_once {shared}\n"
        f"@include {shared}\n",
        encoding="utf-8",
    )

    assert evaluate_file(main)["build"]["value"] == "shared"


def test_last_assignment_wins_in_section(tmp_path: Path) -> None:
    main = tmp_path / "repeated-assignment.pfcfg"
    main.write_text("[build]\nvalue = first\nvalue = second\n", encoding="utf-8")

    assert evaluate_file(main)["build"]["value"] == "second"


def test_interpolation_cascade_and_circular_reference_raise_errors(tmp_path: Path) -> None:
    path = tmp_path / "interpolation-cascade.pfcfg"
    path.write_text("[loop]\na = $(loop.b)\nb = $(loop.a)\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Circular reference"):
        evaluate_file(path)

    cascade = tmp_path / "cascade.pfcfg"
    cascade.write_text("[chain]\nvalue = ${MISSING:-$(chain.value)}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Circular reference|Expansion limit"):
        evaluate_file(cascade)


def test_expansion_limit_failure_is_reported(tmp_path: Path) -> None:
    main = tmp_path / "expansion-limit.pfcfg"
    lines = ["[chain]"]
    for index in range(1, 13):
        lines.append(f"k{index} = $(chain.k{index + 1})")
    lines.append("k13 = final")
    main.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expansion limit"):
        evaluate_file(main)


def test_deliberate_legacy_json_mismatch_diagnostics_are_clear() -> None:
    result = compare_effective_settings({"build": {"image": "legacy-image"}}, {"build": {"image": "json-image"}})

    assert result["status"] == "MISMATCH"
    assert any(item["section"] == "build" and item["key"] == "image" for item in result["differences"])


def test_verify_file_reports_error_for_circular_reference_fixture() -> None:
    root = Path(__file__).resolve().parents[5]
    path = root / "starter" / "configs" / "edge-cases" / "interpolation-cascade.pfcfg"

    result = verify_file(path, env={"CI": ""})

    assert result["status"] == "ERROR"
    assert "Circular reference" in result["error"]
