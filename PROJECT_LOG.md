# Project Log

## Decisions Log (2026-02-25)
- Repository initialized with standard structure: firmware/, gateway/, cloud_emulator/, attacks/, capture/, data/, analysis/, docs/.
- Gateway logging approach selected: JSONL logs (`gateway/logs/experiment_log.jsonl`) with `run_start` and `run_end` events.
- Results dataset schema frozen: `data/processed/results.csv` includes latency, crypto timings, heap usage, bytes, MITM success, and notes.
- MITM evaluation frozen at scenario-definition level (pass/fail criteria documented). Active MITM tooling will only be used in authorized lab conditions.

## Next Actions
- [ ] Add README.md to repo root.
- [ ] Create attacks/scenarios.md and capture/capture_guide.md.
- [ ] Create results.csv header in data/processed/.
- [ ] Run gateway service locally and confirm /health endpoint works.
- [ ] Prepare SD card image for Raspberry Pi OS (when SD arrives).
- [ ] When hardware arrives: flash Baseline 1 firmware first, do 1 dry-run + capture pcap + log run.

## Issues / Corrections

## Corrections (2026-02-25)
- Corrected status reporting: implementation artifacts (ESP32 firmware, gateway deployment on Raspberry Pi, cloud/PKI integration, and MITM experimental runs) are NOT completed yet. Hardware is still in shipping/arrival phase. Only planning, repository scaffolding, and documentation preparation are in progress.

## Decisions/Implementation Prep (2026-02-25)
- Cloud emulator API implementation added at `cloud_emulator/api/app.py` with `GET /health` and `POST /enroll`.
- Enrollment flow decision: sign device CSR using local CA files at `cloud_emulator/pki/ca.crt` and `cloud_emulator/pki/ca.key`, returning device certificate PEM and CA certificate PEM in JSON response.
- Request logging decision: append one JSONL record per incoming request to `cloud_emulator/api/logs/enroll_log.jsonl`.
- Runtime/dependency prep decision: pinned API dependencies in `cloud_emulator/api/requirements.txt` and documented setup/run/test steps in `cloud_emulator/api/README.md`.

## Implementation Prep (2026-02-25) — Baseline 3 Cloud/PKI Emulator
- Implemented and validated a local Cloud/PKI emulator (Flask) for Baseline 3 (cloud-only certificate onboarding).
- Endpoints:
  - GET `/health` -> 200 OK
  - POST `/enroll` accepts `{run_id, device_id, csr_pem}` and returns `{run_id, device_id, device_cert_pem, ca_cert_pem}`.
- Local CA stored at: `cloud_emulator/pki/ca.crt` and `cloud_emulator/pki/ca.key`.
- Validation evidence:
  - Generated a test CSR using OpenSSL and successfully received signed certificate via `/enroll` (HTTP 200).
- Note: During real ESP32 experiments, this emulator will run on Raspberry Pi or Windows host (not WSL) to ensure network reachability from the DUT.

## Milestone 3 Results (2026-02-25)
- Environment readiness verified (Windows + WSL2 Ubuntu + Python venv).
- Baseline 3 (Cloud-only certificate onboarding) service validated:
  - `/health` returned HTTP 200 with JSON status OK.
  - `/enroll` successfully signed a test CSR and returned certificate PEM data (HTTP 200).
- Logging evidence prepared (enrollment JSONL logs available for audit/reproducibility).
- Issue encountered: port 5000 conflict (“Address already in use”); documented as an operational setup issue for M3 and resolved by stopping the existing listener or using an alternate port.
- Performance metrics (latency/crypto overhead) and MITM experimental results are deferred to Milestone 4 pending hardware arrival.
