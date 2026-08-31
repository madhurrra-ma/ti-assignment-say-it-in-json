"""Legacy .pfcfg parser components."""

from .parser import (
    Assignment,
    BlankLine,
    Comment,
    ConditionalBlock,
    Include,
    ParseError,
    Program,
    SectionDecl,
    SourceLocation,
    parse_file,
    parse_text,
)

__all__ = [
    "Assignment",
    "BlankLine",
    "Comment",
    "ConditionalBlock",
    "Include",
    "ParseError",
    "Program",
    "SectionDecl",
    "SourceLocation",
    "parse_file",
    "parse_text",
]
