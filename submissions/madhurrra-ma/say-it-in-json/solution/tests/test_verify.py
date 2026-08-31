from __future__ import annotations

from pathlib import Path

from pipelineforge_json.legacy.evaluator import evaluate_file
from pipelineforge_json.verify import compare_effective_settings, verify_file


ROOT = Path(__file__).resolve().parents[5]
STARTER_ROOT = ROOT / "starter" / "configs"


def _starter_entry_configs() -> list[Path]:
    return [
        STARTER_ROOT / "customers" / "acme-corp" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "globex" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "initech" / "pipeline.pfcfg",
        STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg",
    ]


def test_verify_file_matches_starter_configs_for_ci_env() -> None:
    env = {"CI": "true", "CACHE_NAMESPACE": "shared", "GLOBEX_ENV": "prod"}
    for path in _starter_entry_configs():
        result = verify_file(path, env=env)
        assert result["status"] == "MATCH", result


def test_verify_file_matches_starter_configs_for_non_ci_env() -> None:
    env = {"CI": "", "GLOBEX_ENV": "dev"}
    for path in _starter_entry_configs():
        result = verify_file(path, env=env)
        assert result["status"] == "MATCH", result


def test_compare_effective_settings_reports_diagnostics_for_mismatch() -> None:
    legacy = {"build": {"image": "legacy-image", "parallel": "false"}}
    json_effective = {"build": {"image": "json-image", "parallel": "false"}}

    result = compare_effective_settings(legacy, json_effective)

    assert result["status"] == "MISMATCH"
    assert any(item["section"] == "build" and item["key"] == "image" for item in result["differences"])
    assert result["differences"][0]["legacy"] == "legacy-image"
    assert result["differences"][0]["json"] == "json-image"


def test_verify_file_reports_clear_error_for_circular_reference() -> None:
    path = STARTER_ROOT / "edge-cases" / "interpolation-cascade.pfcfg"
    result = verify_file(path, env={"CI": ""})
    assert result["status"] == "ERROR"
    assert "Circular reference" in result["error"]


def test_verify_file_handles_include_precedence_and_repeated_assignments(tmp_path: Path) -> None:
    shared = tmp_path / "shared.pfcfg"
    shared.write_text(
        "[build]\nimage = shared-image\nparallel = false\n",
        encoding="utf-8",
    )
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "@include shared.pfcfg\n[build]\nimage = local-image\nparallel = true\nimage = final-image\n",
        encoding="utf-8",
    )

    result = verify_file(main, env={})
    assert result["status"] == "MATCH", result
    assert evaluate_file(main, env={})["build"]["image"] == "final-image"


def test_verify_file_handles_conditional_precedence_and_include_once(tmp_path: Path) -> None:
    import pipelineforge_json.legacy.evaluator as legacy_evaluator

    base = tmp_path / "base.pfcfg"
    base.write_text(
        "[build]\nmode = base\n",
        encoding="utf-8",
    )
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "@include_once base.pfcfg\n@include_once base.pfcfg\n"
        "@ifdef CI\n[build]\nmode = ci\n@endif\n"
        "@ifndef CI\n[build]\nmode = nonci\n@endif\n",
        encoding="utf-8",
    )

    ci_result = verify_file(main, env={"CI": "true"})
    non_ci_result = verify_file(main, env={"CI": ""})

    assert ci_result["status"] == "MATCH", ci_result
    assert non_ci_result["status"] == "MATCH", non_ci_result
    assert legacy_evaluator.evaluate_file(main, env={"CI": "true"})["build"]["mode"] == "ci"
    assert legacy_evaluator.evaluate_file(main, env={"CI": ""})["build"]["mode"] == "nonci"
