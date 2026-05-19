from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

UPSTREAM_HOST = "http://172.20.10.2:5000"

ROUTES = {
    "/health":    f"{UPSTREAM_HOST}/health",
    "/enroll":    f"{UPSTREAM_HOST}/enroll",
    "/provision": f"{UPSTREAM_HOST}/provision",
}

class Handler(BaseHTTPRequestHandler):
    def _proxy(self, method):
        if self.path not in ROUTES:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            print(f"RELAY {method} {self.path} -> 404", flush=True)
            return

        upstream = ROUTES[self.path]

        try:
            body = None
            if method == "POST":
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length > 0 else b""

            req = Request(upstream, data=body if method == "POST" else None, method=method)
            if method == "POST":
                req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))

            with urlopen(req, timeout=20) as resp:
                resp_body = resp.read()
                status = resp.getcode()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")

            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
            print(f"RELAY {method} {self.path} -> {upstream} status={status}", flush=True)

        except HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(err_body)
            print(f"RELAY {method} {self.path} -> HTTPError status={e.code}", flush=True)

        except URLError as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())
            print(f"RELAY {method} {self.path} -> URLError: {e}", flush=True)

    def do_GET(self):
        self._proxy("GET")

    def do_POST(self):
        self._proxy("POST")

    def log_message(self, format, *args):
        return

HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
