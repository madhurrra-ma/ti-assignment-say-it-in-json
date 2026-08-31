"""Minimal parser for PipelineForge legacy .pfcfg files.

This module intentionally does not evaluate includes, conditionals, interpolation,
references, or environment values. It only parses source into a structured,
order-preserving intermediate representation (IR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(frozen=False)
class SourceLocation:
    file: str
    line: int
    column: int = 1


class ParseError(ValueError):
    def __init__(self, message: str, file: str | None = None, line: int | None = None, column: int | None = None):
        self.message = message
        self.file = file
        self.line = line
        self.column = column
        super().__init__(self._format())

    def _format(self) -> str:
        bits: list[str] = []
        if self.file is not None:
            bits.append(self.file)
        if self.line is not None:
            bits.append(str(self.line))
        if self.column is not None:
            bits.append(str(self.column))
        if bits:
            return f"{':'.join(bits)}: {self.message}"
        return self.message


@dataclass(frozen=True)
class Comment:
    text: str
    location: SourceLocation


@dataclass(frozen=True)
class BlankLine:
    location: SourceLocation


@dataclass(frozen=True)
class SectionDecl:
    name: str
    location: SourceLocation


@dataclass(frozen=True)
class Assignment:
    section: str
    key: str
    value: str
    location: SourceLocation


@dataclass(frozen=True)
class Include:
    path: str
    kind: str
    location: SourceLocation


@dataclass(frozen=True)
class ConditionalBlock:
    kind: str
    var: str
    body: list["Statement"]
    location: SourceLocation


Statement = Comment | BlankLine | SectionDecl | Assignment | Include | ConditionalBlock


@dataclass(frozen=True)
class Program:
    file: str
    statements: list[Statement] = field(default_factory=list)


def parse_file(path: str | Path) -> Program:
    """Parse a .pfcfg file and return its IR."""
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - thin error surface
        raise ParseError(f"unable to read file: {exc}", file=str(file_path)) from exc
    return parse_text(content, file=str(file_path))


def parse_text(text: str, file: str = "<memory>") -> Program:
    """Parse source text into an order-preserving intermediate representation.

    This parser intentionally does not resolve environment variables, interpolation,
    conditionals, includes, or cross-key references. The goal is to preserve an exact
    stream of statements with source locations so a later evaluator can decide how to
    execute them.
    """
    lines = text.splitlines()
    statements: list[Statement] = []
    current_section: str | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        line_number = index + 1

        if not stripped:
            statements.append(BlankLine(location=SourceLocation(file=file, line=line_number, column=1)))
            index += 1
            continue

        if stripped.startswith("#") or stripped.startswith(";"):
            statements.append(Comment(text=stripped, location=SourceLocation(file=file, line=line_number, column=1)))
            index += 1
            continue

        if stripped.startswith("@ifdef") or stripped.startswith("@ifndef"):
            block, next_index = _parse_conditional_block(lines, index, file, current_section)
            statements.append(block)
            index = next_index
            continue

        if stripped.startswith("@endif"):
            raise ParseError("unexpected @endif without matching @ifdef/@ifndef", file=file, line=line_number)

        if stripped.startswith("@include"):
            path = _parse_include_target(stripped, file, line_number)
            kind = "include_once" if stripped.startswith("@include_once") else "include"
            statements.append(Include(path=path, kind=kind, location=SourceLocation(file=file, line=line_number, column=1)))
            index += 1
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            if not section_name:
                raise ParseError("empty section header", file=file, line=line_number)
            current_section = section_name
            statements.append(SectionDecl(name=section_name, location=SourceLocation(file=file, line=line_number, column=1)))
            index += 1
            continue

        stmt = _parse_assignment(line, file, line_number, current_section)
        if stmt is None:
            raise ParseError(f"unrecognized line: {line}", file=file, line=line_number)
        statements.append(stmt)
        index += 1

    return Program(file=file, statements=statements)


def _parse_conditional_block(lines: Sequence[str], start_index: int, file: str, current_section: str | None) -> tuple[ConditionalBlock, int]:
    directive = lines[start_index].strip()
    if directive.startswith("@ifdef"):
        kind = "ifdef"
    elif directive.startswith("@ifndef"):
        kind = "ifndef"
    else:
        raise ParseError(f"unsupported conditional: {directive}", file=file, line=start_index + 1)

    var = _parse_directive_name(directive, kind, file, start_index + 1)
    body: list[Statement] = []
    local_section = current_section
    index = start_index + 1

    while index < len(lines):
        candidate = lines[index].strip()
        if candidate.startswith("@endif"):
            return (
                ConditionalBlock(
                    kind=kind,
                    var=var,
                    body=body,
                    location=SourceLocation(file=file, line=start_index + 1, column=1),
                ),
                index + 1,
            )

        if candidate.startswith("@ifdef") or candidate.startswith("@ifndef"):
            nested_block, next_index = _parse_conditional_block(lines, index, file, local_section)
            body.append(nested_block)
            index = next_index
            continue

        parsed = _parse_statement(lines[index], index + 1, file, local_section)
        if isinstance(parsed, SectionDecl):
            local_section = parsed.name
        body.append(parsed)
        index += 1

    raise ParseError(f"unterminated @'{kind}' block", file=file, line=start_index + 1)


def _parse_statement(raw_line: str, line_number: int, file: str, current_section: str | None) -> Statement:
    stripped = raw_line.strip()
    if not stripped:
        return BlankLine(location=SourceLocation(file=file, line=line_number, column=1))
    if stripped.startswith("#") or stripped.startswith(";"):
        return Comment(text=stripped, location=SourceLocation(file=file, line=line_number, column=1))
    if stripped.startswith("@endif"):
        raise ParseError("unexpected @endif without matching @ifdef/@ifndef", file=file, line=line_number)
    if stripped.startswith("@include"):
        path = _parse_include_target(stripped, file, line_number)
        kind = "include_once" if stripped.startswith("@include_once") else "include"
        return Include(path=path, kind=kind, location=SourceLocation(file=file, line=line_number, column=1))
    if stripped.startswith("[") and stripped.endswith("]"):
        name = stripped[1:-1].strip()
        if not name:
            raise ParseError("empty section header", file=file, line=line_number)
        return SectionDecl(name=name, location=SourceLocation(file=file, line=line_number, column=1))
    assignment = _parse_assignment(raw_line, file, line_number, current_section)
    if assignment is None:
        raise ParseError(f"unrecognized line: {raw_line}", file=file, line=line_number)
    return assignment


def _parse_directive_name(line: str, directive_name: str, file: str, line_number: int) -> str:
    if directive_name == "ifdef":
        prefix = "@ifdef"
    elif directive_name == "ifndef":
        prefix = "@ifndef"
    else:
        raise ParseError(f"unsupported directive: {directive_name}", file=file, line=line_number)
    body = line[len(prefix) :].strip()
    if not body:
        raise ParseError(f"missing variable name after {prefix}", file=file, line=line_number)
    return body


def _parse_include_target(line: str, file: str, line_number: int) -> str:
    if line.startswith("@include_once"):
        target = line[len("@include_once") :].strip()
    elif line.startswith("@include"):
        target = line[len("@include") :].strip()
    else:
        raise ParseError(f"invalid include directive: {line}", file=file, line=line_number)
    if not target:
        raise ParseError("include directive missing path", file=file, line=line_number)
    return target


def _parse_assignment(raw_line: str, file: str, line_number: int, current_section: str | None) -> Assignment | None:
    if "=" not in raw_line:
        return None
    left, right = raw_line.split("=", 1)
    left = left.strip()
    right = right.strip()
    if not left:
        raise ParseError("empty assignment key", file=file, line=line_number)
    if current_section is None:
        raise ParseError("assignment outside of section", file=file, line=line_number)
    return Assignment(
        section=current_section,
        key=left,
        value=right,
        location=SourceLocation(file=file, line=line_number, column=1),
    )
