"""Run the API: python3 server.py [db-file] [port]"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from tillpoint import db
from tillpoint.api import App, dumps

WEB_ROOT = Path(__file__).resolve().parent
WEB_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/assets/styles.css": ("assets/styles.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("assets/app.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def _serve(self):
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length)) if length else None
            request_path = urlsplit(self.path).path
            if self.command == "GET" and request_path in WEB_ROUTES:
                filename, content_type = WEB_ROUTES[request_path]
                data = (WEB_ROOT / filename).read_bytes()
                status = 200
            else:
                api_path = request_path[4:] if request_path.startswith("/api/") else request_path
                status, payload = app.handle(self.command, api_path, body)
                data = dumps(payload).encode()
                content_type = "application/json; charset=utf-8"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_PUT = _serve
    return Handler


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "tillpoint.db"
    port = int(os.environ.get("PORT") or (sys.argv[2] if len(sys.argv) > 2 else 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    HTTPServer((host, port), make_handler(App(db.connect(path)))).serve_forever()
