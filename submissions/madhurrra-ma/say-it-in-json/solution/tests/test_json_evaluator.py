from __future__ import annotations

from pathlib import Path

from pipelineforge_json.convert import convert_file
from pipelineforge_json.json_evaluator import evaluate_json
from pipelineforge_json.legacy.evaluator import evaluate_file

ROOT = Path(__file__).resolve().parents[5]
STARTER_ROOT = ROOT / "starter" / "configs"


def _fixture_paths() -> list[Path]:
    return [
        STARTER_ROOT / "customers" / "acme-corp" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "globex" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "initech" / "pipeline.pfcfg",
        STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg",
    ]


def test_json_evaluator_matches_legacy_for_ci_env() -> None:
    env = {"CI": "true", "CACHE_NAMESPACE": "shared", "GLOBEX_ENV": "prod"}
    for path in _fixture_paths():
        legacy = evaluate_file(path, env=env)
        converted = convert_file(path)
        json_evaluated = evaluate_json(converted, env=env)
        assert legacy == json_evaluated


def test_json_evaluator_matches_legacy_for_non_ci_env() -> None:
    env = {"CI": "", "GLOBEX_ENV": "dev"}
    for path in _fixture_paths():
        legacy = evaluate_file(path, env=env)
        converted = convert_file(path)
        json_evaluated = evaluate_json(converted, env=env)
        assert legacy == json_evaluated


def test_json_evaluator_handles_interpolation_cascade_and_conditional_include() -> None:
    cascade_path = STARTER_ROOT / "edge-cases" / "interpolation-cascade.pfcfg"
    cascade_json = convert_file(cascade_path)
    try:
        evaluate_json(cascade_json, env={"CI": ""})
    except ValueError as exc:
        assert "Circular reference" in str(exc)
    else:
        raise AssertionError("Expected circular interpolation to raise ValueError")

    conditional_path = STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg"
    conditional_json = convert_file(conditional_path)
    assert evaluate_json(conditional_json, env={"CI": "", "FEATURE_BETA": "true"}) == evaluate_file(conditional_path, env={"CI": "", "FEATURE_BETA": "true"})
