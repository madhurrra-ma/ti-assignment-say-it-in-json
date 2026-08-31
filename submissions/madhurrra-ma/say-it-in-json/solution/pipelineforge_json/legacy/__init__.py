"""Legacy .pfcfg parser and evaluator components."""

from .evaluator import evaluate_file
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
    "evaluate_file",
    "parse_file",
    "parse_text",
]
