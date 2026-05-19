#!/usr/bin/env python3
"""
Proposed Gateway Service — Gateway-Brokered Two-Phase Enrollment
Port 8090

Phase 1: POST /gateway/auth
  - Validates device_id + device_token against local device registry
  - Issues a short-lived (30 s) single-use session_token

Phase 2: POST /gateway/enroll
  - Validates session_token: exists, not expired, not used, device_id matches
  - Marks session_token used immediately (prevents concurrent replay)
  - Forwards CSR to cloud emulator POST /enroll on device's behalf
  - Returns certificate response transparently to caller

GET /health
  - {"status":"ok","service":"gateway_proposed"}

Run-id strategy:
  The caller (ESP32 firmware) includes run_id in the POST /gateway/enroll body.
  The gateway passes it through unchanged to the cloud emulator.  This keeps the
  gateway stateless with respect to run numbering and lets the firmware control
  the experiment run counter exactly as in B1/B3.

Upstream:
  Configurable via UPSTREAM_HOST env var (default: http://127.0.0.1:5000).
  On Pi hardware, set UPSTREAM_HOST=http://<laptop_ip>:5000 before starting.

Device registry:
  Loaded once at startup from gateway/pi/device_registry.json if present,
  else falls back to gateway/pi/device_registry.example.json.
  In-memory only — mutations do not persist.  Restart to reload.

Logging:
  Appends to gateway/logs/proposed_gateway_log.jsonl (JSONL, one entry per request).
"""

import json
import os
import secrets
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

PORT = 8090
UPSTREAM_HOST = os.environ.get("UPSTREAM_HOST", "http://127.0.0.1:5000")
SESSION_TTL_SEC = 30

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH         = os.path.join(BASE_DIR, "device_registry.json")
REGISTRY_EXAMPLE_PATH = os.path.join(BASE_DIR, "device_registry.example.json")

LOG_DIR  = os.path.normpath(os.path.join(BASE_DIR, "..", "logs"))
LOG_PATH = os.path.join(LOG_DIR, "proposed_gateway_log.jsonl")


# ---------------------------------------------------------------------------
# Startup — load registry, initialise in-memory session store
# ---------------------------------------------------------------------------

def _load_registry():
    path = REGISTRY_PATH if os.path.exists(REGISTRY_PATH) else REGISTRY_EXAMPLE_PATH
    if not os.path.exists(path):
        print(f"WARNING: no device registry found (checked {path})", flush=True)
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    devices = data.get("devices", {})
    print(f"  registry loaded from {os.path.basename(path)}: "
          f"{list(devices.keys())}", flush=True)
    return devices


DEVICE_REGISTRY = _load_registry()   # {device_id: {"device_token": "..."}}
SESSION_STORE   = {}                  # {session_token: {device_id, created_at,
                                      #                  expires_at, used}}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_log(entry):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _blank_log(now, path):
    return {
        "timestamp_utc":           now.isoformat(),
        "path":                    path,
        "device_id":               None,
        "auth_success":            None,
        "token_valid":             None,
        "session_token_issued":    None,
        "session_token_valid":     None,
        "session_token_used_before": None,
        "session_token_expired":   None,
        "status_code":             None,
        "upstream_status":         None,
    }


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    # ---- send / receive helpers -------------------------------------------

    def _send_json(self, status, body_dict):
        body = json.dumps(body_dict).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    # ---- routing ------------------------------------------------------------

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "gateway_proposed"})
            print("GET /health -> 200", flush=True)
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/gateway/auth":
            self._handle_auth()
        elif self.path == "/gateway/enroll":
            self._handle_enroll()
        else:
            self._send_json(404, {"error": "not found"})

    # ---- Phase 1 — device authentication -----------------------------------

    def _handle_auth(self):
        payload = self._read_json()
        now = datetime.now(timezone.utc)
        log = _blank_log(now, "/gateway/auth")

        if not isinstance(payload, dict):
            log["status_code"] = 400
            _append_log(log)
            self._send_json(400, {"error": "Expected JSON body"})
            return

        device_id    = payload.get("device_id")
        device_token = payload.get("device_token")
        log["device_id"] = device_id

        if not device_id or not device_token:
            log["status_code"] = 400
            _append_log(log)
            self._send_json(400, {
                "error": "Missing required fields",
                "required_fields": ["device_id", "device_token"],
            })
            return

        # Validate against registry
        entry = DEVICE_REGISTRY.get(device_id)
        token_valid = (entry is not None
                       and entry.get("device_token") == device_token)
        log["token_valid"] = token_valid

        if not token_valid:
            log["auth_success"]         = False
            log["session_token_issued"] = False
            log["status_code"]          = 401
            _append_log(log)
            print(f"POST /gateway/auth device_id={device_id} -> 401", flush=True)
            self._send_json(401, {"error": "invalid device credentials"})
            return

        # Issue session token
        session_token = secrets.token_hex(16)
        expires_at    = now + timedelta(seconds=SESSION_TTL_SEC)
        SESSION_STORE[session_token] = {
            "device_id":  device_id,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used":       False,
        }

        log["auth_success"]         = True
        log["session_token_issued"] = True
        log["status_code"]          = 200
        _append_log(log)
        print(f"POST /gateway/auth device_id={device_id} -> 200 "
              f"session_token={session_token[:8]}...", flush=True)

        self._send_json(200, {
            "device_id":      device_id,
            "session_token":  session_token,
            "expires_in_sec": SESSION_TTL_SEC,
        })

    # ---- Phase 2 — gateway-brokered enrollment -----------------------------

    def _handle_enroll(self):
        payload = self._read_json()
        now = datetime.now(timezone.utc)
        log = _blank_log(now, "/gateway/enroll")

        if not isinstance(payload, dict):
            log["status_code"] = 400
            _append_log(log)
            self._send_json(400, {"error": "Expected JSON body"})
            return

        device_id     = payload.get("device_id")
        session_token = payload.get("session_token")
        csr_pem       = payload.get("csr_pem")
        run_id        = str(payload.get("run_id", "1"))

        log["device_id"] = device_id

        if not device_id or not session_token or not csr_pem:
            log["status_code"] = 400
            _append_log(log)
            self._send_json(400, {
                "error": "Missing required fields",
                "required_fields": ["device_id", "session_token", "csr_pem"],
            })
            return

        # --- session token validation ---

        st_entry = SESSION_STORE.get(session_token)

        if st_entry is None:
            log["session_token_valid"]       = False
            log["session_token_used_before"] = False
            log["session_token_expired"]     = False
            log["status_code"]               = 401
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} -> 401 unknown token",
                  flush=True)
            self._send_json(401, {"error": "invalid or expired session token"})
            return

        if st_entry["device_id"] != device_id:
            log["session_token_valid"] = False
            log["status_code"]         = 401
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} -> 401 device_id mismatch",
                  flush=True)
            self._send_json(401, {"error": "invalid or expired session token"})
            return

        if st_entry["used"]:
            log["session_token_valid"]       = False
            log["session_token_used_before"] = True
            log["session_token_expired"]     = False
            log["status_code"]               = 401
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} -> 401 token already used",
                  flush=True)
            self._send_json(401, {"error": "invalid or expired session token"})
            return

        expires_at = datetime.fromisoformat(st_entry["expires_at"])
        if now > expires_at:
            log["session_token_valid"]       = False
            log["session_token_used_before"] = False
            log["session_token_expired"]     = True
            log["status_code"]               = 401
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} -> 401 token expired",
                  flush=True)
            self._send_json(401, {"error": "invalid or expired session token"})
            return

        # Mark used immediately — prevents concurrent replay
        SESSION_STORE[session_token]["used"] = True
        log["session_token_valid"]       = True
        log["session_token_used_before"] = False
        log["session_token_expired"]     = False

        # --- forward to cloud emulator /enroll ---

        upstream_url = f"{UPSTREAM_HOST}/enroll"
        upstream_body = json.dumps({
            "run_id":    run_id,
            "device_id": device_id,
            "csr_pem":   csr_pem,
        }).encode("utf-8")

        try:
            req = Request(upstream_url, data=upstream_body, method="POST")
            req.add_header("Content-Type", "application/json")
            with urlopen(req, timeout=30) as resp:
                resp_body   = resp.read()
                up_status   = resp.getcode()

            log["upstream_status"] = up_status
            log["status_code"]     = up_status
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} "
                  f"-> upstream={up_status} ok", flush=True)

            self.send_response(up_status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        except HTTPError as e:
            err_body = e.read()
            log["upstream_status"] = e.code
            log["status_code"]     = 502
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} "
                  f"-> upstream HTTPError {e.code}", flush=True)
            self._send_json(502, {"error": f"upstream error {e.code}"})

        except URLError as e:
            log["upstream_status"] = None
            log["status_code"]     = 502
            _append_log(log)
            print(f"POST /gateway/enroll device_id={device_id} "
                  f"-> upstream URLError: {e}", flush=True)
            self._send_json(502, {"error": f"upstream unreachable: {e}"})

    # ---- suppress default BaseHTTPServer access log -----------------------

    def log_message(self, format, *args):
        return


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Proposed Gateway Service ===", flush=True)
    print(f"Loading device registry...", flush=True)
    print(f"Upstream emulator: {UPSTREAM_HOST}", flush=True)
    print(f"Session TTL:       {SESSION_TTL_SEC}s", flush=True)
    print(f"Log:               {LOG_PATH}", flush=True)
    print(f"Listening on       0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
