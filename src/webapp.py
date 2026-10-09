"""Local web interface for the QueryCraft Phase 2 compiler workbench."""

import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .database import execute_generated_sql
from .errors import QueryCraftError
from .main import compile_query
from .suggestions import suggestion_for


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class QueryCraftHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_POST(self):
        if self.path != "/api/compile":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            query = str(payload.get("query", "")).strip()
            tokens, ast, sql = compile_query(query)
            columns, rows = execute_generated_sql(sql)
            self.send_json(HTTPStatus.OK, {
                "ok": True,
                "tokens": [asdict(token) for token in tokens],
                "ast": asdict(ast),
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "message": "Query passed syntax and semantic validation, then executed on the local SQLite demonstration database.",
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
