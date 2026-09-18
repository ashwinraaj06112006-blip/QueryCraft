class QueryCraftError(Exception):
    """Base class for user-facing compiler diagnostics."""


class LexicalError(QueryCraftError):
    pass


class SyntaxError(QueryCraftError):
    pass


class SemanticError(QueryCraftError):
    pass
