"""Vercel Function adapter for the Tillpoint SQLite API."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tillpoint import db  # noqa: E402
from tillpoint.api import App, dumps  # noqa: E402
from tillpoint.catalog import Catalog  # noqa: E402


class handler(BaseHTTPRequestHandler):
    """Vercel's Python runtime calls this standard-library request handler."""

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def do_PUT(self):
        self._dispatch()

    def _dispatch(self):
        query = parse_qs(urlsplit(self.path).query)
        route = query.get("route", [urlsplit(self.path).path.removeprefix("/api")])[0]
        if not route.startswith("/"):
            route = "/" + route
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length)) if length else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, {"error": "invalid JSON body"})
            return

        # Vercel's writable /tmp is per-instance and temporary; see README.
        conn = db.connect(os.environ.get("TILLPOINT_DB", "/tmp/tillpoint.db"))
        try:
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                Catalog(conn).add_product("MUG", "Mug", 1200, 10)
            status, payload = App(conn).handle(self.command, route, body)
            self._send(status, payload)
        finally:
            conn.close()

    def _send(self, status, payload):
        data = dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
