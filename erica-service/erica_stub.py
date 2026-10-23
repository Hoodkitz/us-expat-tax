"""Placeholder for the ERiC wrapper server.

The real ELSTER ERiC library is proprietary (download requires an ELSTER
developer account) and is NOT part of this repository. Until it is installed,
this stub answers /health and returns 501 for everything else, so that
`docker compose up` is honest about what is missing.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "eric": "not_installed"})
        else:
            self._send(501, {"detail": "ERiC library not installed"})

    do_POST = do_GET  # noqa: N815


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8443), Handler).serve_forever()
