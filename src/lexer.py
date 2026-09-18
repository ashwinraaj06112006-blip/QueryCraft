import re

from .errors import LexicalError
from .model import Token


WORDS = {
    "show": "ACTION", "display": "ACTION", "list": "ACTION", "count": "COUNT",
    "student": "ENTITY", "students": "ENTITY", "names": "ATTRIBUTE", "name": "ATTRIBUTE",
    "department": "ATTRIBUTE", "cgpa": "ATTRIBUTE", "age": "ATTRIBUTE", "student_id": "ATTRIBUTE",
    "all": "ALL", "whose": "CONDITION", "with": "CONDITION", "where": "CONDITION", "from": "FROM",
    "is": "FILLER", "greater": "COMPARISON_WORD", "less": "COMPARISON_WORD", "than": "THAN",
    "at": "AT", "least": "LEAST", "most": "MOST", "and": "LOGICAL", "or": "LOGICAL",
    "ordered": "ORDERED", "by": "BY", "ascending": "ASC", "descending": "DESC",
    "top": "TOP", "limit": "LIMIT",
}


def tokenize(source: str) -> list[Token]:
    """Recognize controlled-language tokens; reject unknown characters/words."""
    tokens: list[Token] = []
    pattern = re.compile(r'\s+|>=|<=|!=|=|>|<|"[^"]*"|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*')
    cursor = 0
    for match in pattern.finditer(source):
        if match.start() != cursor:
            raise LexicalError(f"Unrecognized character '{source[cursor]}' at position {cursor}.")
        cursor = match.end()
        text = match.group()
        if text.isspace():
            continue
        lower = text.lower()
        if text in {">", "<", ">=", "<=", "=", "!="}:
            kind = "OPERATOR"
        elif text.startswith('"'):
            kind = "STRING"
        elif text[0].isdigit():
            kind = "NUMBER"
        elif lower in WORDS:
            kind = WORDS[lower]
        else:
            # Unquoted words are allowed only as department values after 'from'.
            kind = "WORD"
        tokens.append(Token(kind, lower if kind != "STRING" else text[1:-1], match.start()))
    if cursor != len(source):
        raise LexicalError(f"Unrecognized character '{source[cursor]}' at position {cursor}.")
    if not tokens:
        raise LexicalError("Query cannot be empty.")
    return tokens
