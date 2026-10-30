"""Schema-adaptive controlled-English to SQL compiler for uploaded datasets."""

from __future__ import annotations

import re
import sqlite3

from .schema_retrieval import resolve_column, retrieve_columns


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def literal(value: str) -> str:
    try: return str(float(value)) if "." in value else str(int(value))
    except ValueError: return "'" + value.strip().strip('"').replace("'", "''") + "'"


def compile_uploaded_query(source: str, schema: dict) -> dict:
    query = " ".join(source.strip().split())
    lower = query.lower()
    columns = schema["columns"]
    tokens = [{"kind": "WORD", "value": word} for word in re.findall(r'[\w.]+|>=|<=|!=|=|>|<', lower)]
    count = bool(re.match(r"^(count|how many)\b", lower))
    aggregate = None
    aggregate_match = re.match(r"^(?:show\s+)?(average|avg|sum|total|min|minimum|max|maximum)\s+([\w ]+?)(?:\s+(?:group(?:ed)?\s+by|where|whose|with|having|ordered|sort|top|limit)\b|$)", lower)
    if aggregate_match:
        word, phrase = aggregate_match.groups()
        attribute = resolve_column(phrase.strip(), columns)
        if not attribute:
            raise ValueError(f"No uploaded column matches '{phrase.strip()}'.")
        function = {"average": "AVG", "avg": "AVG", "sum": "SUM", "total": "SUM", "min": "MIN", "minimum": "MIN", "max": "MAX", "maximum": "MAX"}[word]
        aggregate = {"function": function, "attribute": attribute, "alias": f"{function.lower()}_{attribute}"}
    group_match = re.search(r"\bgroup(?:ed)?\s+by\s+([\w ]+?)(?:\s+(?:where|whose|with|having|ordered|sort(?:ed)?|top|limit)\b|$)", lower)
    group_by = resolve_column(group_match.group(1).strip(), columns) if group_match else None
    if group_match and not group_by:
        raise ValueError(f"No uploaded column matches '{group_match.group(1).strip()}'.")
    limit_match = re.search(r"\b(?:top|first|limit)\s+(\d+)", lower)
    limit = int(limit_match.group(1)) if limit_match else None
    order_match = re.search(r"\b(?:ordered|sort(?:ed)?|ranked)\s+by\s+([\w ]+?)(?:\s+(ascending|descending|asc|desc))?(?:\s+(?:limit|top)\b|$)", lower)
    top_match = re.search(r"\btop\s+\d+\s+(?:\w+\s+)?by\s+([\w ]+)$", lower)
    order_by = resolve_column((order_match or top_match).group(1).strip(), columns) if (order_match or top_match) else None
    descending = bool(top_match or (order_match and (order_match.group(2) or "").startswith("desc")))
    projection = None
    select_match = re.match(r"^(?:show|display|list)\s+(.+?)(?:\s+(?:where|whose|with|having|ordered|sort|top|limit)\b|$)", lower)
    if select_match:
        phrase = select_match.group(1).strip()
        if phrase not in {"all", "all records", "records", "rows", "data"} and not phrase.startswith(("top ", "first ")):
            candidates = [resolve_column(part.strip(), columns) for part in re.split(r"\s*,\s*|\s+and\s+", phrase)]
            projection = [candidate for candidate in candidates if candidate]
            if not projection: projection = None
    conditions = []
    condition_text = re.split(r"\b(?:where|whose|with|having)\b", lower, maxsplit=1)
    if len(condition_text) == 2:
        tail = re.split(r"\b(?:ordered|sort(?:ed)?|top|limit)\b", condition_text[1], maxsplit=1)[0]
        for part in re.split(r"\s+(and|or)\s+", tail):
            if part in {"and", "or"}: continue
            match = re.match(r"\s*([\w ]+?)\s*(>=|<=|!=|=|greater than|more than|less than|is|equals?)\s*([\w.\-\"']+)\s*$", part)
            if not match: raise ValueError(f"Could not understand condition '{part.strip()}'. Use: column is value, column greater than value, or column less than value.")
            attribute = resolve_column(match.group(1).strip(), columns)
            if not attribute: raise ValueError(f"No uploaded column matches '{match.group(1).strip()}'.")
            raw = match.group(2)
            operator = {"greater than": ">", "more than": ">", "less than": "<", "is": "=", "equal": "=", "equals": "="}.get(raw, raw)
            conditions.append({"attribute": attribute, "operator": operator, "value": match.group(3).strip("'\"")})
    if aggregate:
        aggregate_sql = f"{aggregate['function']}({quote(aggregate['attribute'])}) AS {quote(aggregate['alias'])}"
        select = f"{quote(group_by)}, {aggregate_sql}" if group_by else aggregate_sql
    elif count:
        select = f"{quote(group_by)}, COUNT(*) AS count" if group_by else "COUNT(*) AS count"
    else:
        select = ", ".join(quote(item) for item in (projection or [column["name"] for column in columns]))
    sql = f"SELECT {select} FROM {quote(schema['table'])}"
    if conditions:
        sql += " WHERE " + " AND ".join(f"{quote(item['attribute'])} {item['operator']} {literal(item['value'])}" for item in conditions)
    if group_by: sql += f" GROUP BY {quote(group_by)}"
    if order_by: sql += f" ORDER BY {quote(order_by)} {'DESC' if descending else 'ASC'}"
    if limit: sql += f" LIMIT {limit}"
    sql += ";"
    return {"tokens": tokens, "ast": {"projection": projection or ["*"], "source": schema["table"], "conditions": conditions, "order_by": order_by, "descending": descending, "limit": limit, "count": count, "group_by": group_by, "aggregate": aggregate}, "sql": sql, "retrieval": retrieve_columns(query, columns)}


def execute_uploaded_sql(sql: str, database_path) -> tuple[list[str], list[dict]]:
    if not sql.lstrip().upper().startswith("SELECT"):
        raise ValueError("Only generated SELECT statements may run.")
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute(sql)
        return [item[0] for item in cursor.description or []], [dict(row) for row in cursor.fetchmany(200)]
    finally:
        connection.close()
