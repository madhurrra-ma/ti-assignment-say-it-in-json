from __future__ import annotations

import json
from pathlib import Path

from pipelineforge_json.verify import generate_unmigratable_report


ROOT = Path(__file__).resolve().parents[5]
STARTER_ROOT = ROOT / "starter" / "configs"


def test_unmigratable_report_captures_real_env_var_case() -> None:
    path = STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg"
    report = generate_unmigratable_report([path])

    assert report
    assert any(
        item["section"] == "migration" and item["key"] == "api_endpoint" and "REQUIRED_API_ENDPOINT" in item["reason"]
        for item in report
    )


def test_unmigratable_report_has_required_fields() -> None:
    path = STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg"
    report = generate_unmigratable_report([path])

    first = report[0]
    assert set(first) >= {"file", "section", "key", "reason"}
    assert "file" in first
    assert "section" in first
    assert "key" in first
    assert "reason" in first


def test_starter_config_without_false_unmigratable_entries() -> None:
    path = STARTER_ROOT / "customers" / "acme-corp" / "pipeline.pfcfg"
    report = generate_unmigratable_report([path])
    assert report == []
