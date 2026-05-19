# Secure IoT Device Onboarding Testbed

Research testbed for evaluating the security and performance of ESP32 device onboarding
workflows under controlled lab conditions. The project measures latency, heap overhead,
and security posture across four onboarding methods ranging from plain HTTP to a
gateway-brokered two-phase certificate enrollment scheme.

## Onboarding Methods

| Method | Label | Mechanism | Endpoint |
|--------|-------|-----------|----------|
| Plain HTTP health-check | B1 | Unauthenticated GET — no enrollment, no token | `/health` |
| Token provisioning | B2 | Pre-loaded single-use token, rejected on replay | `/provision` |
| Cloud PKI enrollment | B3 | ESP32 generates P-256 CSR; cloud CA signs and returns cert | `/enroll` |
| Gateway-brokered two-phase | Proposed | Phase 1: device authenticates to Pi gateway; Phase 2: gateway requests cert on device's behalf | `/gateway/auth` + `/gateway/enroll` |

All methods use intentionally plaintext HTTP — the absence of transport encryption is
the research subject, not an omission.

## Repository Layout

```
esp32_firmware/
  baseline1_http/        B1 firmware — plain HTTP health-check
  baseline2_token/       B2 firmware — single-use token provisioning
  baseline3_enroll/      B3 firmware — P-256 CSR enrollment via mbedTLS
  proposed_gateway/      Proposed firmware — two-phase gateway enrollment

cloud_emulator/api/      Flask enrollment service (GET /health, POST /enroll, POST /provision)
cloud_emulator/pki/      Local CA certificate (ca.crt); private key excluded from VCS

gateway/pi/              Raspberry Pi gateway scripts
  iot_gateway_relay.py     Transparent relay — forwards /health, /enroll, /provision (port 8080)
  iot_gateway_proposed.py  Active gateway — Phase 1 auth + Phase 2 session-gated enroll (port 8090)

attacks/                 MITM attack scenario definitions (scenarios.md)
capture/                 Raw UART session captures from ESP32 hardware runs
data/raw/                Evidence notes and verbatim serial logs
data/processed/          Per-run metric CSVs — source of truth for reported results
report_assets/ch7_visuals/  Chapter 7 PNG figures (11 generated)
docs/handoff/            Handover bundle — setup, rebinding, runbooks, status matrix
scripts/handoff/         Helper scripts for IP discovery, rebinding, and environment verification
submission_package/      Structured submission package with all deliverables
```

## Milestone Status

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | WSL/ESP-IDF environment, repo scaffold | Complete |
| M2 | Baseline 1 — plain HTTP health-check over Wi-Fi | Complete — 5/5 PASS, mean 1663 ms |
| M2b | Baseline 2 — token provisioning, replay resistance | Complete — server 10/10 PASS; replay correctly rejected (HTTP 401) |
| M3 | Baseline 3 — cloud PKI certificate enrollment (CSR/sign) | Complete — 5/5 PASS, mean 1375 ms |
| M4 | Raspberry Pi gateway — relay and proposed gateway | Complete — 5/5 PASS for Proposed method, mean 1997 ms |

## Testbed Architecture

```
[ESP32 DevKit]
   │  Wi-Fi (phone hotspot)
   ▼
[Raspberry Pi 4]          port 8080 — transparent relay
   │  or                  port 8090 — proposed two-phase gateway
   ▼
[Laptop : WSL2]           port 5000 — cloud emulator (Flask + local CA)
```

Direct mode (B1/B3 without Pi): ESP32 connects straight to laptop port 5000.

## Quick Start

### 1. Environment prerequisites

- WSL2 (Ubuntu 22.04 or 24.04)
- ESP-IDF v5.5.3 at `~/esp-idf-v5.5.3` — verify with `idf.py --version`
- usbipd-win installed on Windows (for ESP32 USB passthrough to WSL)
- Python 3.10+ in WSL

### 2. Set up cloud emulator

```bash
cd cloud_emulator/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py          # listens on 0.0.0.0:5000
```

Restore `cloud_emulator/pki/ca.key` from secure backup before running B3 or Proposed experiments.

### 3. Configure firmware Wi-Fi credentials

`sdkconfig` files are excluded from VCS. Configure each project before building:

```bash
cd esp32_firmware/baseline1_http
idf.py menuconfig      # set SSID and password under Example Configuration
```

Repeat for `baseline2_token`, `baseline3_enroll`, `proposed_gateway`.

### 4. Discover session IPs and rebind if needed

IPs assigned by the phone hotspot are not persistent. Run at the start of every session:

```bash
bash scripts/handoff/print_session_ips.sh
```

Then update only the files that need to change:

```bash
bash scripts/handoff/update_b1_target.sh   <PI_IP> 8080 /health
bash scripts/handoff/update_b3_target.sh   <PI_IP> 8080 /enroll
bash scripts/handoff/update_pi_relay_upstream.sh <LAPTOP_HOTSPOT_IP> 5000
```

See `docs/handoff/RUNTIME_REBINDING_GUIDE.md` for the full checklist including the
proposed gateway and the "different phone, same hotspot name" scenario.

### 5. Verify the chain before flashing

```bash
bash scripts/handoff/verify_environment.sh
bash scripts/handoff/verify_runtime_chain.sh <PI_IP> <LAPTOP_HOTSPOT_IP>
```

### 6. Build and flash

```bash
cd esp32_firmware/baseline1_http
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

## Data and Evidence

| File | Contents |
|------|----------|
| `data/processed/final_results.csv` | 25-row master dataset: B1 (×10) + B3 (×10) + Proposed (×5) |
| `data/processed/proposed_p5_runpack_2026-04-07.csv` | Per-phase breakdown for Proposed 5-run pack (auth/CSR/enroll/total) |
| `capture/b1_serial_live.txt` | Canonical B1 UART session — 5 MEASURE lines, all HTTP 200 |
| `capture/b2_via_pi_clean_2026-04-06_final.txt` | Best B2 via-Pi capture — 7/10 client PASS (8 s fix applied; clean re-run pending) |
| `capture/b2_replay_scenario_2026-04-06.txt` | B2 replay attack — first use HTTP 200, replay HTTP 401 |
| `capture/proposed_p5_repeated_runs_latest.txt` | Canonical Proposed 5-run PASS pack |
| `cloud_emulator/api/logs/enroll_log.jsonl` | Server-side enrollment log (all POST /enroll events) |
| `gateway/logs/proposed_gateway_log.jsonl` | Pi gateway event log for Proposed method runs |
| `data/raw/` | Evidence notes for each method with per-run tables and summary statistics |

## Handover Documentation

For full setup, runtime rebinding, component runbooks, and continuation path:

| Document | Purpose |
|----------|---------|
| `docs/handoff/HANDOVER_MASTER.md` | **Start here** — project overview, current status, warnings |
| `docs/handoff/CURRENT_STATUS_MATRIX.md` | Component × status table |
| `docs/handoff/NEXT_EXECUTION_PATH.md` | Ordered next steps with done criteria |
| `docs/handoff/SETUP_ON_ANOTHER_LAPTOP.md` | Full environment setup on a new machine |
| `docs/handoff/RUNTIME_REBINDING_GUIDE.md` | IP rebinding for every session and phone changes |
| `docs/handoff/COMPONENT_RUNBOOKS.md` | Start/stop/verify for each component |
| `docs/handoff/EVIDENCE_INDEX.md` | Every capture, log, and evidence file with status |
| `docs/handoff/HANDOVER_EXPORT_NOTE.md` | What to include/exclude when transferring the repo |

## Security Notes

- This testbed uses intentionally plaintext HTTP to demonstrate the security differences
  between the four onboarding methods. No TLS is present by design.
- The CA private key (`cloud_emulator/pki/ca.key`) is excluded from VCS. Restore it
  from a secure backup before running B3 or Proposed experiments.
- `sdkconfig` files contain Wi-Fi credentials. They are excluded from VCS and must be
  configured locally with `idf.py menuconfig`.
- `cloud_emulator/api/b2_tokens.json` contains session tokens. Use
  `b2_tokens.example.json` as a template; the live token file is not committed.
