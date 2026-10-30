"""Local web interface for the QueryCraft Phase 2 compiler workbench."""

import json
import zipfile
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from .database import execute_generated_sql
from .data_ingestion import MAX_UPLOAD_BYTES, import_dataset
from .dynamic_compiler import compile_uploaded_query, execute_uploaded_sql
from .errors import QueryCraftError
from .main import compile_query
from .suggestions import suggestion_for


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
DATA_ROOT = Path(__file__).resolve().parent.parent / ".querycraft_data"
DATABASE_PATH = DATA_ROOT / "uploaded.sqlite3"
ACTIVE_SCHEMA: dict | None = None


class QueryCraftHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_POST(self):
        if self.path == "/api/upload":
            return self.handle_upload()
        if self.path != "/api/compile":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            query = str(payload.get("query", "")).strip()
            mode = payload.get("mode", "demo")
            if mode == "uploaded":
                if not ACTIVE_SCHEMA:
                    raise ValueError("Upload a CSV, XLSX or JSON dataset before querying it.")
                compiled = compile_uploaded_query(query, ACTIVE_SCHEMA)
                tokens, ast, sql = compiled["tokens"], compiled["ast"], compiled["sql"]
                columns, rows = execute_uploaded_sql(sql, DATABASE_PATH)
                retrieval = compiled["retrieval"]
                message = "Retrieved relevant schema fields, compiled the query, and executed safe SELECT SQL on your uploaded dataset. Results are capped at 200 rows for the browser."
            else:
                tokens, ast, sql = compile_query(query)
                columns, rows = execute_generated_sql(sql)
                retrieval = []
                message = "Query passed syntax and semantic validation, then executed on the local SQLite demonstration database."
            self.send_json(HTTPStatus.OK, {
                "ok": True,
                "tokens": [asdict(token) if hasattr(token, "position") else token for token in tokens],
                "ast": asdict(ast) if not isinstance(ast, dict) else ast,
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "retrieval": retrieval,
                "message": message,
            })
        except QueryCraftError as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_type": type(error).__name__,
                "message": str(error),
                "suggestion": suggestion_for(error),
            })
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error_type": "RequestError", "message": str(error)})

    def handle_upload(self):
        global ACTIVE_SCHEMA
        try:
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type or "boundary=" not in content_type:
                raise ValueError("Upload must use multipart/form-data.")
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_UPLOAD_BYTES + 1024 * 1024:
                raise ValueError("Upload is larger than the 100 MB local safety limit.")
            boundary = content_type.split("boundary=", 1)[1].strip().strip('"').encode()
            body = self.rfile.read(length)
            parts = body.split(b"--" + boundary)
            file_name, file_data = None, None
            for part in parts:
                if (b'name="dataset"' not in part and b"name=dataset" not in part) or b"filename=" not in part: continue
                headers, _, data = part.partition(b"\r\n\r\n")
                match = __import__("re").search(br'filename=?"?([^";\r\n]+)', headers)
                if match:
                    file_name = match.group(1).decode("utf-8", "replace")
                    file_data = data.rsplit(b"\r\n", 1)[0]
                    break
            if not file_name or file_data is None: raise ValueError("Choose a dataset file before uploading.")
            suffix = Path(file_name).suffix.lower()
            if suffix not in {".csv", ".json", ".xlsx"}: raise ValueError("Supported file types are CSV, XLSX and JSON.")
            DATA_ROOT.mkdir(exist_ok=True)
            upload = DATA_ROOT / f"{uuid4().hex}{suffix}"
            upload.write_bytes(file_data)
            ACTIVE_SCHEMA = import_dataset(upload, DATABASE_PATH)
            ACTIVE_SCHEMA["file_name"] = Path(file_name).name
            for old in DATA_ROOT.glob("*.csv"): old.unlink(missing_ok=True)
            for old in DATA_ROOT.glob("*.json"): old.unlink(missing_ok=True)
            for old in DATA_ROOT.glob("*.xlsx"): old.unlink(missing_ok=True)
            self.send_json(HTTPStatus.OK, {"ok": True, "schema": ACTIVE_SCHEMA, "message": f"Imported {ACTIVE_SCHEMA['row_count']} rows from {ACTIVE_SCHEMA['file_name']}."})
        except (ValueError, OSError, zipfile.BadZipFile) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error_type": "UploadError", "message": str(error)})

    def send_json(self, status: HTTPStatus, payload: dict):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), QueryCraftHandler)
    print("QueryCraft Workbench is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
