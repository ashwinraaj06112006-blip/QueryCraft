from .errors import SemanticError
from .model import Query


SCHEMA = {
    "students": {"student_id": "INTEGER", "name": "TEXT", "department": "TEXT", "cgpa": "REAL", "age": "INTEGER"}
}


def validate(query: Query) -> Query:
    if query.source not in SCHEMA:
        raise SemanticError(f"Unknown entity '{query.source}'.")
    columns = SCHEMA[query.source]
    for attribute in (query.projection or []):
        if attribute not in columns:
            raise SemanticError(f"Unknown attribute '{attribute}' in projection.")
    for condition in query.conditions:
        if condition.attribute not in columns:
            raise SemanticError(f"Unknown attribute '{condition.attribute}'.")
        data_type = columns[condition.attribute]
        if data_type in {"INTEGER", "REAL"}:
            try:
                float(str(condition.value))
            except ValueError as exc:
                raise SemanticError(f"Attribute '{condition.attribute}' requires a numeric value.") from exc
        elif condition.operator not in {"=", "!="}:
            raise SemanticError(f"Text attribute '{condition.attribute}' supports only '=' or '!='.")
    if query.order_by and query.order_by not in columns:
        raise SemanticError(f"Unknown attribute '{query.order_by}' in ordering.")
    if query.limit is not None and query.limit <= 0:
        raise SemanticError("Limit must be a positive integer.")
    return query
