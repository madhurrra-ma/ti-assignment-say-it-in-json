from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from pipelineforge_json.convert import convert_file
from pipelineforge_json.schema import load_schema

ROOT = Path(__file__).resolve().parents[5]
STARTER_ROOT = ROOT / "starter" / "configs"


def _iter_configs() -> list[Path]:
    return [
        STARTER_ROOT / "customers" / "acme-corp" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "globex" / "pipeline.pfcfg",
        STARTER_ROOT / "customers" / "initech" / "pipeline.pfcfg",
        STARTER_ROOT / "edge-cases" / "interpolation-cascade.pfcfg",
        STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg",
    ]


def test_starter_configs_convert_and_validate() -> None:
    schema = load_schema()
    validator = Draft202012Validator(schema)

    for path in _iter_configs():
        document = convert_file(path)
        validator.validate(document)
        assert document["version"] == 1
        assert document["source"]["path"] == str(path.resolve())
        assert isinstance(document["sections"], list)
        assert isinstance(document["includes"], list)
        assert isinstance(document["conditionals"], list)
        assert isinstance(document["unmigratable"], list)


def test_converter_records_includes_and_conditionals() -> None:
    path = STARTER_ROOT / "edge-cases" / "conditional-includes.pfcfg"
    document = convert_file(path)

    assert any(item["kind"] == "ifdef" for item in document["conditionals"])
    assert any(item["kind"] == "ifndef" for item in document["conditionals"])
    nested_includes = [
        item
        for conditional in document["conditionals"]
        for item in conditional["body"]
        if isinstance(item, dict) and item.get("kind") in {"include", "include_once"}
    ]
    assert nested_includes


def test_converter_preserves_reference_metadata() -> None:
    path = STARTER_ROOT / "customers" / "initech" / "pipeline.pfcfg"
    document = convert_file(path)

    refs = [
        assignment
        for section in document["sections"]
        for assignment in section["assignments"]
        if assignment["key"] in {"compiler_path", "effective_toolchain", "public_key_url", "version", "bundle_name"}
    ]
    assert any(ref["references"] for ref in refs)
    assert any(tok["kind"] == "env" for ref in refs for tok in ref["interpolation"])
