# Cloud Emulator API

Flask service for device enrollment simulation. It exposes:
- `GET /health`
- `POST /enroll` (signs incoming CSR with local CA)
- `POST /provision` (Baseline 2 — single-use token provisioning)

## Paths Used
- CA certificate: `cloud_emulator/pki/ca.crt`
- CA private key: `cloud_emulator/pki/ca.key`
- Request log file: `cloud_emulator/api/logs/enroll_log.jsonl`
- Provision log file: `cloud_emulator/api/logs/provision_log.jsonl`
- Token file (session, not committed): `cloud_emulator/api/b2_tokens.json`
- Token template (committed): `cloud_emulator/api/b2_tokens.example.json`

## Setup
```bash
cd cloud_emulator/api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Start Server
```bash
python app.py
```

The server listens on `http://127.0.0.1:5000` by default.

## Test Endpoints
Health:
```bash
curl -s http://127.0.0.1:5000/health
```

Enroll (replace placeholder CSR with a real PEM CSR):
```bash
curl -s -X POST http://127.0.0.1:5000/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run-001",
    "device_id": "esp32-001",
    "csr_pem": "-----BEGIN CERTIFICATE REQUEST-----\n<PASTE_CSR_BASE64_LINES>\n-----END CERTIFICATE REQUEST-----\n"
  }'
```

Provision (Baseline 2 — token must be present in b2_tokens.json or b2_tokens.example.json):
```bash
curl -s -X POST http://127.0.0.1:5000/provision \
  -H "Content-Type: application/json" \
  -d '{"run_id":"1","device_id":"esp32_01","token":"a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4"}'
# First call: 200 {"provisioning_status":"ok"}
# Repeat same token: 401 {"error":"invalid or expired token"}
```

Before running B2 experiments, copy the example token file and populate with
freshly generated tokens:
```bash
cp b2_tokens.example.json b2_tokens.json
python3 -c "import secrets; [print(secrets.token_hex(16)) for _ in range(10)]"
# paste generated tokens into b2_tokens.json
```
