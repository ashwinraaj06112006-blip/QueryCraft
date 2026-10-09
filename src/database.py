"""SQLite demonstration layer for the QueryCraft Phase 2 prototype."""

import sqlite3


SAMPLE_STUDENTS = [
    (1, "Ananya", "cse", 8.8, 20),
    (2, "Bharath", "ece", 7.4, 19),
    (3, "Charan", "cse", 9.1, 21),
    (4, "Divya", "mech", 8.0, 20),
    (5, "Esha", "cse", 7.9, 18),
]


def create_demo_database() -> sqlite3.Connection:
    """Create a fresh in-memory database with safe, repeatable demonstration data."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE students (student_id INTEGER, name TEXT, department TEXT, cgpa REAL, age INTEGER)"
    )
    connection.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?)", SAMPLE_STUDENTS)
    return connection


def execute_generated_sql(sql: str) -> tuple[list[str], list[dict[str, object]]]:
    """Execute generated SELECT SQL only against the fixed demonstration schema."""
    if not sql.lstrip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements can run in the Phase 2 demonstration.")
    connection = create_demo_database()
    try:
        cursor = connection.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = [dict(row) for row in cursor.fetchall()]
        return columns, rows
    finally:
        connection.close()
