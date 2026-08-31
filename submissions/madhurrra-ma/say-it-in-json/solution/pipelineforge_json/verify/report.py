from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from pipelineforge_json.convert import convert_file


def generate_unmigratable_report(paths: Sequence[str | Path]) -> list[dict[str, Any]]:
    """Collect unmigratable entries for one or more .pfcfg files."""
    report: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, int | None, str]] = set()

    for raw_path in paths:
        document = convert_file(raw_path)
        for item in document.get("unmigratable", []):
            report_entry = _normalize_report_item(item)
            key = (
                report_entry.get("file"),
                report_entry.get("section"),
                report_entry.get("key"),
                report_entry.get("line"),
                report_entry.get("reason"),
            )
            if key in seen:
                continue
            seen.add(key)
            report.append(report_entry)

        for assignment in _iter_assignments(document):
            for token in assignment.get("interpolation", []):
                if token.get("kind") != "env":
                    continue
                if token.get("default") is not None:
                    continue
                name = token.get("name") or token.get("variable")
                if not name:
                    continue
                report_entry = {
                    "file": assignment.get("source", {}).get("file"),
                    "section": assignment.get("section"),
                    "key": assignment.get("key"),
                    "reason": f"environment variable '{name}' requires a runtime value and has no default; it cannot be safely converted automatically",
                    "line": assignment.get("source", {}).get("line"),
                }
                key = (
                    report_entry.get("file"),
                    report_entry.get("section"),
                    report_entry.get("key"),
                    report_entry.get("line"),
                    report_entry.get("reason"),
                )
                if key in seen:
                    continue
                seen.add(key)
                report.append(report_entry)

    return report


def _normalize_report_item(item: dict[str, Any]) -> dict[str, Any]:
    report_entry = {
        "file": item.get("file"),
        "section": item.get("section"),
        "key": item.get("key"),
        "reason": item.get("reason"),
    }
    if item.get("line") is not None:
        report_entry["line"] = item.get("line")
    return report_entry


def _iter_assignments(document: dict[str, Any]):
    for statement in document.get("statements", []):
        if statement.get("type") == "assignment":
            yield statement
        elif statement.get("type") == "conditional":
            yield from _iter_assignments_from_body(statement.get("body", []))


def _iter_assignments_from_body(body: list[dict[str, Any]]):
    for item in body:
        if item.get("type") == "assignment":
            yield item
        elif item.get("type") == "conditional":
            yield from _iter_assignments_from_body(item.get("body", []))


def write_unmigratable_report(paths: Sequence[str | Path], output_path: str | Path) -> Path:
    """Write a JSON report of unmigratable items to disk."""
    report = generate_unmigratable_report(paths)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return destination
