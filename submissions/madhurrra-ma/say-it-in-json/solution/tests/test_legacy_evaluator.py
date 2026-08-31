from __future__ import annotations

import pytest

from pipelineforge_json.legacy import evaluate_file


def test_include_loads_relative_file(tmp_path) -> None:
    base = tmp_path / "base.pfcfg"
    base.write_text("[build]\nimage = base-image\n", encoding="utf-8")
    main = tmp_path / "main.pfcfg"
    main.write_text("@include base.pfcfg\n[build]\nimage = main-image\n", encoding="utf-8")

    result = evaluate_file(str(main))

    assert result["build"]["image"] == "main-image"


def test_include_once_skips_duplicate_resolution(tmp_path) -> None:
    base = tmp_path / "shared.pfcfg"
    base.write_text("[build]\nvalue = shared-value\n", encoding="utf-8")
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "@include_once shared.pfcfg\n@include_once shared.pfcfg\n@include shared.pfcfg\n",
        encoding="utf-8",
    )

    result = evaluate_file(str(main))

    assert result["build"]["value"] == "shared-value"


def test_ifdef_and_ifndef_follow_environment(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "@ifdef FEATURE_ENABLED\n[build]\nmode = enabled\n@endif\n"
        "@ifndef FEATURE_ENABLED\n[build]\nmode = disabled\n@endif\n",
        encoding="utf-8",
    )

    assert evaluate_file(str(main), env={"FEATURE_ENABLED": "1"})["build"]["mode"] == "enabled"
    assert evaluate_file(str(main), env={})["build"]["mode"] == "disabled"


def test_env_interpolation_uses_default_and_empty_values(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "[build]\n"
        "defaulted = ${MISSING:-fallback}\n"
        "explicit = ${SET_VAR}\n"
        "alternate = ${SET_VAR:+alt}\n"
        "empty_default = ${EMPTY_VAR:-fallback}\n"
        "empty_alternate = ${EMPTY_VAR:+alt}\n",
        encoding="utf-8",
    )

    result = evaluate_file(str(main), env={"SET_VAR": "present", "EMPTY_VAR": ""})

    assert result["build"]["defaulted"] == "fallback"
    assert result["build"]["explicit"] == "present"
    assert result["build"]["alternate"] == "alt"
    assert result["build"]["empty_default"] == "fallback"
    assert result["build"]["empty_alternate"] == ""


def test_cross_key_references_are_resolved_after_includes(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "[build]\n"
        "base = release-v1\n"
        "tag = prefix-$(build.base)-suffix\n"
        "nested = ${ENV_TAG:-$(build.tag)}\n",
        encoding="utf-8",
    )

    result = evaluate_file(str(main), env={})

    assert result["build"]["tag"] == "prefix-release-v1-suffix"
    assert result["build"]["nested"] == "prefix-release-v1-suffix"


def test_later_assignments_override_earlier_values(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "[build]\n"
        "value = first\n"
        "value = second\n",
        encoding="utf-8",
    )

    result = evaluate_file(str(main))

    assert result["build"]["value"] == "second"


def test_circular_references_raise_clear_error(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    main.write_text(
        "[loop]\n"
        "a = $(loop.b)\n"
        "b = $(loop.a)\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Circular reference"):
        evaluate_file(str(main))


def test_expansion_limit_is_enforced(tmp_path) -> None:
    main = tmp_path / "main.pfcfg"
    lines = ["[chain]"]
    for index in range(1, 12):
        lines.append(f"k{index} = $(chain.k{index + 1})" if index < 11 else f"k11 = final")
    lines.insert(1, "k1 = $(chain.k2)")
    main.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expansion limit"):
        evaluate_file(str(main))
