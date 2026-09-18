from .model import Query


def sql_literal(value: object) -> str:
    try:
        float(str(value))
        return str(value)
    except ValueError:
        return "'" + str(value).replace("'", "''") + "'"


def generate(query: Query) -> str:
    select = "COUNT(*)" if query.count else ", ".join(query.projection or ["*"])
    sql = f"SELECT {select} FROM {query.source}"
    if query.conditions:
        parts = []
        for condition in query.conditions:
            prefix = f" {condition.connector} " if condition.connector else ""
            parts.append(f"{prefix}{condition.attribute} {condition.operator} {sql_literal(condition.value)}")
        sql += " WHERE " + "".join(parts)
    if query.order_by:
        sql += f" ORDER BY {query.order_by} {'DESC' if query.descending else 'ASC'}"
    if query.limit is not None:
        sql += f" LIMIT {query.limit}"
    return sql + ";"
