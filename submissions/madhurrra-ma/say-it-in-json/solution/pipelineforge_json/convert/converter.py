from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipelineforge_json.legacy.parser import (
    Assignment,
    ConditionalBlock,
    Include,
    Program,
    SectionDecl,
    parse_file,
)
from pipelineforge_json.schema import validate_config_document

_SECTION_RE = re.compile(r"^\[(.+)\]$")


def convert_file(path: str | Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Convert a legacy .pfcfg file into a schema-valid JSON representation."""
    file_path = Path(path)
    program = parse_file(file_path)
    document = _convert_program(program, str(file_path.resolve()))
    validate_config_document(document)
    return document


def convert_text(text: str, *, file: str = "<memory>", env: dict[str, str] | None = None) -> dict[str, Any]:
    """Convert in-memory .pfcfg text into a schema-valid JSON representation."""
    from pipelineforge_json.legacy.parser import parse_text

    document = _convert_program(parse_text(text, file=file), file)
    validate_config_document(document)
    return document


def _convert_program(program: Program, source_path: str) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    includes: list[dict[str, Any]] = []
    conditionals: list[dict[str, Any]] = []
    unmigratable: list[dict[str, Any]] = []
    section_map: dict[str, list[dict[str, Any]]] = {}
    statements: list[dict[str, Any]] = []

    def add_assignment(section_name: str, assignment: Assignment) -> None:
        item = {
            "key": assignment.key,
            "value": assignment.value,
            "source": {"file": assignment.location.file, "line": assignment.location.line},
            "interpolation": _extract_tokens(assignment.value),
            "references": _extract_references(assignment.value),
        }
        section_map.setdefault(section_name, []).append(item)
        statements.append({
            "type": "assignment",
            "section": section_name,
            **item,
        })

    def flush_section(section_name: str) -> None:
        if section_name not in section_map:
            return
        sections.append({"name": section_name, "assignments": section_map[section_name]})

    current_section: str | None = None

    for statement in program.statements:
        if isinstance(statement, SectionDecl):
            if current_section is not None:
                flush_section(current_section)
            current_section = statement.name
            statements.append({"type": "section", "name": statement.name})
            continue

        if isinstance(statement, Assignment):
            if current_section is None:
                unmigratable.append(
                    {
                        "file": statement.location.file,
                        "section": None,
                        "key": statement.key,
                        "reason": "assignment outside any section",
                        "line": statement.location.line,
                    }
                )
                continue
            add_assignment(current_section, statement)
            continue

        if isinstance(statement, Include):
            if current_section is not None:
                flush_section(current_section)
                current_section = None
            item = {
                "kind": statement.kind,
                "path": statement.path,
                "source": {"file": statement.location.file, "line": statement.location.line},
                "resolved_path": None,
            }
            includes.append(item)
            statements.append({"type": "include", **item})
            continue

        if isinstance(statement, ConditionalBlock):
            if current_section is not None:
                flush_section(current_section)
                current_section = None
            conditional = _convert_conditional(statement, unmigratable)
            conditionals.append(conditional)
            statements.append({"type": "conditional", **conditional})
            continue

    if current_section is not None:
        flush_section(current_section)

    return {
        "version": 1,
        "source": {"path": source_path, "resolved_path": None},
        "statements": statements,
        "sections": sections,
        "includes": includes,
        "conditionals": conditionals,
        "unmigratable": unmigratable,
    }


def _convert_conditional(statement: ConditionalBlock, unmigratable: list[dict[str, Any]]) -> dict[str, Any]:
    body: list[dict[str, Any]] = []
    for item in statement.body:
        if isinstance(item, SectionDecl):
            body.append({"type": "section", "name": item.name})
        elif isinstance(item, Assignment):
            entry = {
                "type": "assignment",
                "section": statement.var if False else None,
                "key": item.key,
                "value": item.value,
                "source": {"file": item.location.file, "line": item.location.line},
                "interpolation": _extract_tokens(item.value),
                "references": _extract_references(item.value),
            }
            if item.section is not None:
                entry["section"] = item.section
            body.append(entry)
        elif isinstance(item, Include):
            body.append(
                {
                    "type": "include",
                    "kind": item.kind,
                    "path": item.path,
                    "source": {"file": item.location.file, "line": item.location.line},
                    "resolved_path": None,
                }
            )
        elif isinstance(item, ConditionalBlock):
            body.append({"type": "conditional", **_convert_conditional(item, unmigratable)})
        else:
            unmigratable.append(
                {
                    "file": statement.location.file,
                    "section": None,
                    "key": None,
                    "reason": f"unsupported conditional body item: {type(item).__name__}",
                    "line": statement.location.line,
                }
            )
    return {
        "type": "conditional",
        "kind": statement.kind,
        "var": statement.var,
        "body": body,
        "source": {"file": statement.location.file, "line": statement.location.line},
    }


def _extract_tokens(value: str) -> list[dict[str, Any]]:
    tokens: list[dict[str, Any]] = []
    for match in re.finditer(r"\$\{([^}]+)\}|\$\(([^)]+)\)", value):
        raw = match.group(0)
        if raw.startswith("${"):
            expr = match.group(1)
            tokens.append({
                "kind": "env",
                "raw": raw,
                "start": match.start(),
                "end": match.end(),
                "name": expr.split(":-", 1)[0].split(":+", 1)[0].strip() if expr else None,
                "variable": expr.split(":-", 1)[0].split(":+", 1)[0].strip() if expr else None,
                "default": expr.split(":-", 1)[1] if ":-" in expr else None,
                "alternate": expr.split(":+", 1)[1] if ":+" in expr else None,
                "section": None,
                "key": None,
            })
        else:
            ref_name = match.group(2)
            section, key = ref_name.rsplit(".", 1) if "." in ref_name else (None, None)
            tokens.append({
                "kind": "ref",
                "raw": raw,
                "start": match.start(),
                "end": match.end(),
                "name": ref_name,
                "variable": None,
                "default": None,
                "alternate": None,
                "section": section,
                "key": key,
            })
    return tokens


def _extract_references(value: str) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for match in re.finditer(r"\$\(([^)]+)\)", value):
        ref_name = match.group(1)
        if "." not in ref_name:
            continue
        section, key = ref_name.rsplit(".", 1)
        refs.append({"section": section, "key": key})
    return refs
