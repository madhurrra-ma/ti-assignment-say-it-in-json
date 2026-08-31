from __future__ import annotations

from pipelineforge_json.legacy import parse_text, ParseError


def test_section_and_assignments_are_parsed() -> None:
    text = "[build]\ntimeout_minutes = 45\nparallel = false\n"

    program = parse_text(text)

    assert len(program.statements) == 3
    assert program.statements[0].__class__.__name__ == "SectionDecl"
    assert program.statements[1].__class__.__name__ == "Assignment"
    assert program.statements[2].__class__.__name__ == "Assignment"
    assert program.statements[1].key == "timeout_minutes"
    assert program.statements[1].value == "45"


def test_include_is_parsed() -> None:
    text = "@include ../_base/defaults.pfcfg\n[build]\nsteps = compile,test\n"

    program = parse_text(text)

    assert program.statements[0].__class__.__name__ == "Include"
    assert program.statements[0].path == "../_base/defaults.pfcfg"
    assert program.statements[0].kind == "include"


def test_include_once_is_parsed() -> None:
    text = "@include_once shared/base.pfcfg\n"

    program = parse_text(text)

    assert program.statements[0].__class__.__name__ == "Include"
    assert program.statements[0].kind == "include_once"


def test_ifdef_is_parsed_preserving_body() -> None:
    text = "@ifdef CI\n[build]\nparallel = true\n@endif\n"

    program = parse_text(text)
    assert len(program.statements) == 1
    assert program.statements[0].__class__.__name__ == "ConditionalBlock"
    assert program.statements[0].kind == "ifdef"
    assert program.statements[0].var == "CI"
    assert len(program.statements[0].body) == 2
    assert program.statements[0].body[0].__class__.__name__ == "SectionDecl"
    assert program.statements[0].body[1].__class__.__name__ == "Assignment"


def test_ifndef_is_parsed_preserving_body() -> None:
    text = "@ifndef DEPLOY_KEY\n[deploy]\nskip = true\n@endif\n"

    program = parse_text(text)
    assert len(program.statements) == 1
    assert program.statements[0].kind == "ifndef"
    assert program.statements[0].var == "DEPLOY_KEY"
    assert len(program.statements[0].body) == 2


def test_conditional_include_is_parsed() -> None:
    text = "@ifdef FEATURE_BETA\n@include ../templates/node-build.pfcfg\n@endif\n"

    program = parse_text(text)
    assert len(program.statements) == 1
    assert program.statements[0].kind == "ifdef"
    assert len(program.statements[0].body) == 1
    assert program.statements[0].body[0].__class__.__name__ == "Include"
    assert program.statements[0].body[0].path == "../templates/node-build.pfcfg"


def test_comments_and_blank_lines_are_preserved() -> None:
    text = "# comment\n\n[build]\n; another comment\ntimeout_minutes = 45\n"

    program = parse_text(text)
    assert program.statements[0].__class__.__name__ == "Comment"
    assert program.statements[1].__class__.__name__ == "BlankLine"
    assert program.statements[2].__class__.__name__ == "SectionDecl"
    assert program.statements[3].__class__.__name__ == "Comment"


def test_multiple_assignments_preserve_order() -> None:
    text = """
    [build]
    retry_count = 1
    retry_count = 2
    timeout_minutes = 30
    """

    program = parse_text(text)
    keys = [stmt.key for stmt in program.statements if hasattr(stmt, "key")]
    assert keys == ["retry_count", "retry_count", "timeout_minutes"]


def test_malformed_input_raises_parse_error() -> None:
    try:
        parse_text("[build\nparallel = true\n")
        raise AssertionError("ParseError was not raised")
    except ParseError:
        pass


def test_source_locations_are_tracked() -> None:
    text = "[build]\nparallel = true\n"
    program = parse_text(text)

    section = program.statements[0]
    assignment = program.statements[1]

    assert section.location.line == 1
    assert assignment.location.line == 2
    assert assignment.location.file == "<memory>"
