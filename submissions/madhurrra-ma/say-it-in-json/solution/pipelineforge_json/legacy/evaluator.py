from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

from .parser import Assignment, ConditionalBlock, Include, Program, parse_file

EXPANSION_LIMIT = 10
_TOKEN_PATTERN = re.compile(r"\$\{[^}]+\}|\$\([^)]*\)")


def evaluate_file(path: str | Path, env: Mapping[str, str] | None = None) -> dict[str, dict[str, object]]:
    """Evaluate a legacy .pfcfg file into an effective config mapping."""
    file_path = Path(path).resolve()
    env_map = {
        str(key): "" if value is None else str(value)
        for key, value in (os.environ if env is None else env).items()
    }
    state: dict[str, object] = {
        "env": env_map,
        "sections": {},
        "included": set(),
    }

    root_program = parse_file(file_path)
    _apply_statements(root_program.statements, file_path.parent, state)
    resolved: dict[str, dict[str, object]] = {}
    for section, values in state["sections"].items():
        resolved[section] = {
            key: _resolve_key(section, key, state["sections"], env_map, (), 0)
            for key in values
        }
    return resolved


def _apply_statements(statements: list[object], base_dir: Path, state: dict[str, object]) -> None:
    for statement in statements:
        if isinstance(statement, Include):
            _apply_include(statement, base_dir, state)
        elif isinstance(statement, ConditionalBlock):
            if statement.kind == "ifdef":
                should_run = _condition_is_true(statement.var, state["env"])
            elif statement.kind == "ifndef":
                should_run = not _condition_is_true(statement.var, state["env"])
            else:
                should_run = False
            if should_run:
                _apply_statements(statement.body, base_dir, state)
        elif isinstance(statement, Assignment):
            sections = state["sections"]
            section_map = sections.setdefault(statement.section, {})
            section_map[statement.key] = statement.value


def _apply_include(statement: Include, base_dir: Path, state: dict[str, object]) -> None:
    include_path = (base_dir / statement.path).resolve(strict=False)
    include_key = str(include_path)
    if statement.kind == "include_once":
        seen = state["included"]
        if include_key in seen:
            return
        seen.add(include_key)

    program = parse_file(include_path)
    _apply_statements(program.statements, include_path.parent, state)


def _condition_is_true(var_name: str, env: Mapping[str, str]) -> bool:
    value = env.get(var_name, "")
    return value is not None and str(value) != ""


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
        matches = list(_TOKEN_PATTERN.finditer(current))
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
