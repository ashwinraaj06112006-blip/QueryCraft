"""Deterministic, schema-aware help for compiler diagnostics."""

from .errors import LexicalError, SemanticError, SyntaxError
from .semantic import SCHEMA


def suggestion_for(error: Exception) -> str:
    attributes = ", ".join(SCHEMA["students"])
    if isinstance(error, LexicalError):
        return "Use only supported words, numbers, quoted text, and comparison operators such as >, <, or =."
    if isinstance(error, SyntaxError):
        return "Try a supported form such as: Show students whose CGPA is greater than 8."
    if isinstance(error, SemanticError):
        return f"Valid attributes are: {attributes}. Numeric attributes are student_id, cgpa, and age."
    return "Check the controlled QueryCraft grammar and try again."
