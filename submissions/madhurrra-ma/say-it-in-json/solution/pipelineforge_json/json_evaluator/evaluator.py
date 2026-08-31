from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

from pipelineforge_json.legacy.evaluator import EXPANSION_LIMIT
from pipelineforge_json.schema import validate_config_document

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")
_REF_PATTERN = re.compile(r"\$\(([^)]+)\)")


def evaluate_json(config: dict, env: Mapping[str, str] | None = None) -> dict[str, dict[str, object]]:
    """Evaluate a schema-valid JSON-encoded legacy config to effective settings."""
    validate_config_document(config)
    env_map = {
        str(key): "" if value is None else str(value)
        for key, value in (os.environ if env is None else env).items()
    }

    sections: dict[str, dict[str, str]] = {}
    include_history: set[str] = set()
    source_path = config.get("source", {}).get("path")

    for statement in config.get("statements", []):
        if statement.get("type") == "section":
            continue
        if statement.get("type") == "assignment":
            section_name = statement["section"]
            if section_name not in sections:
                sections[section_name] = {}
            sections[section_name][statement["key"]] = statement["value"]
            continue
        if statement.get("type") == "include":
            _apply_include_json(statement, sections, env_map, include_history, source_path)
            continue
        if statement.get("type") == "conditional":
            if _conditional_is_true(statement, env_map):
                _apply_conditional_json(statement["body"], sections, env_map, include_history, source_path)
            continue

    resolved: dict[str, dict[str, object]] = {}
    for section, values in sections.items():
        resolved[section] = {
            key: _resolve_key(section, key, sections, env_map, (), 0)
            for key in values
        }
    return resolved


def _apply_conditional_json(body: list[dict[str, Any]], sections: dict[str, dict[str, str]], env: Mapping[str, str], include_history: set[str], source_path: str | None) -> None:
    for item in body:
        if item.get("type") == "assignment":
            section_name = item["section"]
            sections.setdefault(section_name, {})[item["key"]] = item["value"]
        elif item.get("type") == "include":
            _apply_include_json(item, sections, env, include_history, source_path)
        elif item.get("type") == "conditional":
            if _conditional_is_true(item, env):
                _apply_conditional_json(item["body"], sections, env, include_history, source_path)


def _apply_include_json(include_item: dict[str, Any], sections: dict[str, dict[str, str]], env: Mapping[str, str], include_history: set[str], source_path: str | None) -> None:
    include_kind = include_item["kind"]
    include_path = _resolve_include_path(include_item, source_path)
    key = str(Path(include_path).resolve())
    if include_kind == "include_once":
        if key in include_history:
            return
        include_history.add(key)
    for statement in _resolve_include_statements(include_item, source_path):
        if statement.get("type") == "assignment":
            section_name = statement["section"]
            sections.setdefault(section_name, {})[statement["key"]] = statement["value"]
        elif statement.get("type") == "include":
            _apply_include_json(statement, sections, env, include_history, include_path)
        elif statement.get("type") == "conditional":
            if _conditional_is_true(statement, env):
                _apply_conditional_json(statement["body"], sections, env, include_history, include_path)


def _resolve_include_path(include_item: dict[str, Any], source_path: str | None) -> str:
    raw = include_item.get("resolved_path") or include_item.get("path") or ""
    if not raw:
        return raw
    if Path(raw).is_absolute():
        return raw
    base_dir = Path(source_path).resolve().parent if source_path else Path.cwd()
    return str((base_dir / raw).resolve(strict=False))


def _resolve_include_statements(include_item: dict[str, Any], source_path: str | None) -> list[dict[str, Any]]:
    path = _resolve_include_path(include_item, source_path)
    if not path:
        return []
    if not Path(path).exists():
        return []
    from pipelineforge_json.convert import convert_file

    converted = convert_file(path)
    return converted.get("statements", [])


def _condition_is_true(var_name: str, env: Mapping[str, str]) -> bool:
    value = env.get(var_name, "")
    return value is not None and str(value) != ""


def _conditional_is_true(conditional: Mapping[str, Any], env: Mapping[str, str]) -> bool:
    kind = conditional.get("kind", "ifdef")
    is_true = _condition_is_true(str(conditional["var"]), env)
    return is_true if kind == "ifdef" else not is_true


def _resolve_key(
    section: str,
    key: str,
    sections: Mapping[str, Mapping[str, str]],
    env: Mapping[str, str],
    stack: tuple[tuple[str, str], ...],
    depth: int,
) -> str:
    if depth >= EXPANSION_LIMIT:
        raise ValueError(f"Expansion limit exceeded ({EXPANSION_LIMIT}) while resolving {section}.{key}")

    target = (section, key)
    if target in stack:
        cycle = " -> ".join(f"{current_section}.{current_key}" for current_section, current_key in (*stack, target))
        raise ValueError(f"Circular reference detected: {cycle}")

    raw_value = sections.get(section, {}).get(key)
    if raw_value is None:
        return ""
    return _expand_string(raw_value, sections, env, stack + (target,), depth)


def _expand_string(
    text: str,
    sections: Mapping[str, Mapping[str, str]],
    env: Mapping[str, str],
    stack: tuple[tuple[str, str], ...],
    depth: int,
) -> str:
    current = text
    for iteration in range(EXPANSION_LIMIT + 1):
        matches = list(re.finditer(r"\$\{[^}]+\}|\$\([^)]*\)", current))
        if not matches:
            return current
        replacements: list[str] = []
        cursor = 0
        for match in matches:
            replacements.append(current[cursor:match.start()])
            token = match.group(0)
            if token.startswith("${"):
                expression = token[2:-1]
                replacement = _evaluate_env_expression(expression, sections, env, stack, depth + 1)
            else:
                ref_name = token[2:-1]
                replacement = _resolve_reference(ref_name, sections, env, stack, depth + 1)
            replacements.append(replacement)
            cursor = match.end()
        replacements.append(current[cursor:])
        updated = "".join(replacements)
        if updated == current:
            return updated
        current = updated
        if iteration >= EXPANSION_LIMIT:
            raise ValueError(f"Expansion limit exceeded ({EXPANSION_LIMIT}) while expanding {text!r}")
    raise ValueError(f"Expansion limit exceeded ({EXPANSION_LIMIT}) while expanding {text!r}")


def _resolve_reference(
    ref_name: str,
    sections: Mapping[str, Mapping[str, str]],
    env: Mapping[str, str],
    stack: tuple[tuple[str, str], ...],
    depth: int,
) -> str:
    if "." not in ref_name:
        return ""
    section, key = ref_name.rsplit(".", 1)
    if not section or not key:
        return ""
    return _resolve_key(section, key, sections, env, stack, depth)


def _evaluate_env_expression(
    expression: str,
    sections: Mapping[str, Mapping[str, str]],
    env: Mapping[str, str],
    stack: tuple[tuple[str, str], ...],
    depth: int,
) -> str:
    symbol = expression.strip()
    if ":+" in symbol:
        name, alternate = symbol.split(":+", 1)
        name = name.strip()
        if env.get(name, "") not in (None, ""):
            return _expand_string(alternate, sections, env, stack, depth)
        return ""

    if ":-" in symbol:
        name, default = symbol.split(":-", 1)
        name = name.strip()
        value = env.get(name, "")
        if value not in (None, ""):
            return _expand_string(str(value), sections, env, stack, depth)
        return _expand_string(default, sections, env, stack, depth)

    if not symbol:
        return ""
    return _expand_string(str(env.get(symbol, "")), sections, env, stack, depth)
