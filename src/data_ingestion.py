"""Safe, streaming-friendly import of CSV, JSON and XLSX datasets into SQLite.

This module deliberately uses only the Python standard library.  CSV and JSON
are accepted directly; XLSX files are read from their Open XML package so the
prototype has no cloud service or third-party AI dependency.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import zipfile
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from xml.etree import ElementTree as ET


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
TABLE_NAME = "uploaded_data"
_IDENTIFIER = re.compile(r"[^a-zA-Z0-9_]+")
_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def normalise_identifier(value: object, fallback: str) -> str:
    name = _IDENTIFIER.sub("_", str(value).strip().lower()).strip("_")
    if not name or name[0].isdigit():
        name = fallback if not name else f"column_{name}"
    return name


def unique_columns(headers: list[object]) -> list[str]:
    used: set[str] = set()
    result: list[str] = []
    for index, header in enumerate(headers, start=1):
        base = normalise_identifier(header, f"column_{index}")
        name, count = base, 2
        while name in used:
            name = f"{base}_{count}"
            count += 1
        used.add(name)
        result.append(name)
    return result


def sqlite_type(values: list[object]) -> str:
    meaningful = [value for value in values if value not in (None, "")]
    if not meaningful:
        return "TEXT"
    def integer(value: object) -> bool:
        try:
            return float(str(value)).is_integer()
        except ValueError:
            return False
    def real(value: object) -> bool:
        try:
            float(str(value)); return True
        except ValueError:
            return False
    if all(integer(value) for value in meaningful): return "INTEGER"
    if all(real(value) for value in meaningful): return "REAL"
    return "TEXT"


def _csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        yield from reader


def _json_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not data:
        raise ValueError("JSON upload must be a non-empty list of objects.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Each JSON item must be an object with named fields.")
    headers = list(dict.fromkeys(key for item in data for key in item))
    yield headers
    for item in data:
        yield [item.get(header, "") for header in headers]


def _xlsx_rows(path: Path):
    """Read the first worksheet of a conventional .xlsx file without openpyxl."""
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{_XLSX_NS}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{_XLSX_NS}t")))
        sheet_names = sorted(name for name in book.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
        if not sheet_names:
            raise ValueError("The XLSX file contains no worksheet.")
        root = ET.fromstring(book.read(sheet_names[0]))
        for row in root.iter(f"{_XLSX_NS}row"):
            values: list[object] = []
            for cell in row.findall(f"{_XLSX_NS}c"):
                value = cell.findtext(f"{_XLSX_NS}v", default="")
                if cell.get("t") == "s" and value:
                    value = shared[int(value)]
                elif cell.get("t") == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iter(f"{_XLSX_NS}t"))
                values.append(value)
            yield values


def rows_for(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv": return _csv_rows(path)
    if suffix == ".json": return _json_rows(path)
    if suffix == ".xlsx": return _xlsx_rows(path)
    raise ValueError("Supported file types are CSV, XLSX and JSON.")


def import_dataset(path: Path, database_path: Path) -> dict:
    if path.stat().st_size > MAX_UPLOAD_BYTES:
        raise ValueError("Upload is larger than the 100 MB local safety limit.")
    iterator = iter(rows_for(path))
    try:
        headers = next(iterator)
    except StopIteration as error:
        raise ValueError("The uploaded file is empty.") from error
    if not headers:
        raise ValueError("The dataset must contain a header row.")
    columns = unique_columns(headers)
    sample: list[list[object]] = []
    for _ in range(200):
        try: sample.append(next(iterator))
        except StopIteration: break
    types = [sqlite_type([row[index] if index < len(row) else "" for row in sample]) for index in range(len(columns))]
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(f'DROP TABLE IF EXISTS "{TABLE_NAME}"')
        definition = ", ".join(f'"{column}" {kind}' for column, kind in zip(columns, types))
        connection.execute(f'CREATE TABLE "{TABLE_NAME}" ({definition})')
        placeholders = ", ".join("?" for _ in columns)
        insert = f'INSERT INTO "{TABLE_NAME}" VALUES ({placeholders})'
        count = 0
        def clean(row):
            return [row[index] if index < len(row) else None for index in range(len(columns))]
        batch = []
        for row in sample:
            batch.append(clean(row))
        for row in iterator:
            batch.append(clean(row))
            if len(batch) >= 1000:
                connection.executemany(insert, batch); count += len(batch); batch = []
        if batch:
            connection.executemany(insert, batch); count += len(batch)
        connection.commit()
        preview = [dict(zip(columns, row)) for row in connection.execute(f'SELECT * FROM "{TABLE_NAME}" LIMIT 5')]
    finally:
        connection.close()
    return {"table": TABLE_NAME, "columns": [{"name": col, "type": kind} for col, kind in zip(columns, types)], "row_count": count, "preview": preview, "file_name": path.name, "imported_at": datetime.now().isoformat(timespec="seconds")}
