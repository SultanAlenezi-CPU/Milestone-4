# Proposed Gateway — Dev Notes

Service file: `gateway/pi/iot_gateway_proposed.py`
Port: 8090
Upstream: configurable via `UPSTREAM_HOST` env var (default `http://127.0.0.1:5000`)

---

## Local development (WSL-only, no hardware)

```bash
# Start cloud emulator
cd cloud_emulator/api && source .venv/bin/activate && python app.py &

# Start proposed gateway (upstream = local emulator)
cd /path/to/iot_onboarding
python3 gateway/pi/iot_gateway_proposed.py &

# Health check
curl -s http://localhost:8090/health
# {"status":"ok","service":"gateway_proposed"}

# Phase 1 — auth
curl -s -X POST http://localhost:8090/gateway/auth \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32_01","device_token":"proposed_dev_token_esp32_01_a1b2c3d4e5f6"}'
# {"device_id":"esp32_01","session_token":"<hex>","expires_in_sec":30}

# Phase 2 — enroll (use session_token from Phase 1, supply a CSR)
# Generate test CSR:
#   openssl ecparam -name prime256v1 -genkey -noout -out /tmp/ec.key
#   openssl req -new -key /tmp/ec.key -out /tmp/test.csr -subj "/CN=esp32_01"
```

---

## Device registry

- Runtime file (gitignored): `gateway/pi/device_registry.json`
- Example / fallback: `gateway/pi/device_registry.example.json`
- Format:
  ```json
  {"devices": {"esp32_01": {"device_token": "<token>"}}}
  ```
- Loaded once at startup. Restart service to pick up changes.

---

## Session token lifecycle

1. Issued by Phase 1 (`/gateway/auth`) on successful device auth.
2. 32-char hex, random (`secrets.token_hex(16)`).
3. TTL: 30 seconds from issuance.
4. Single-use: marked `used=True` immediately when Phase 2 validation passes.
5. Stored in-memory (`SESSION_STORE` dict). All tokens reset on service restart.

---

## Upstream (UPSTREAM_HOST)

| Context | Value |
|---------|-------|
| Local WSL dev | `http://127.0.0.1:5000` (default) |
| Pi pointing at laptop | `http://<LAPTOP_IP>:5000` |

Set via env var:
```bash
UPSTREAM_HOST=http://172.20.10.3:5000 python3 iot_gateway_proposed.py
```

---

## Log

`gateway/logs/proposed_gateway_log.jsonl` — one JSONL line per request.

Key fields for experiment evidence:
- `/gateway/auth`: `auth_success`, `token_valid`, `session_token_issued`
- `/gateway/enroll`: `session_token_valid`, `session_token_used_before`, `session_token_expired`, `upstream_status`

---

## Verification status (2026-04-06)

Local WSL-only tests passed:
- [x] GET /health → 200
- [x] POST /gateway/auth valid → 200 + session_token
- [x] POST /gateway/enroll valid → 200 + device_cert_pem + ca_cert_pem
- [x] POST /gateway/enroll replay → 401 (single-use enforced)
- [x] POST /gateway/auth bad token → 401
