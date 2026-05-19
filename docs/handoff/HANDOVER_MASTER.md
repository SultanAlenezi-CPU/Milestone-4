# HANDOVER MASTER — Secure IoT Device Onboarding Testbed

**Entry point for all new operators. Read this file first.**

---

## Project Summary

This project builds and evaluates four IoT device onboarding methods on an ESP32 + Raspberry Pi + laptop testbed:

| Method | Name | What it does |
|--------|------|-------------|
| B1 | Plain HTTP baseline | ESP32 sends GET /health with no auth or encryption |
| B2 | Token provisioning | ESP32 presents a pre-loaded single-use token to POST /provision |
| B3 | Certificate enrollment | ESP32 generates a CSR, cloud CA signs it, device receives cert |
| Proposed | Gateway-brokered two-phase | ESP32 authenticates to Pi gateway → gateway requests cloud cert on device's behalf |

All traffic is intentionally plaintext (no TLS). The insecurity of plaintext is the research subject, not an omission.

---

## Authoritative Repository Root

```
/home/iot_onboarding/iot_onboarding
```

All paths in handoff documents are relative to this root unless stated otherwise.

Windows path: `\\wsl$\Ubuntu\home\iot_onboarding\iot_onboarding\`

---

## Hardware

| Device | Role | Fixed address in testbed |
|--------|------|--------------------------|
| ESP32 DevKit | Firmware target | 172.20.10.3 (DHCP — may change) |
| Raspberry Pi 4 | Local gateway node | 172.20.10.4 (DHCP — often stable on same hotspot) |
| Laptop (Windows + WSL2) | Cloud emulator host, flash station | 172.20.10.2 (DHCP — may change) |
| Phone hotspot | Network backbone | SSID: HUAWEI-B315-58AD — password not stored in repo |

**Important:** IPs are DHCP-assigned by the phone hotspot. They are NOT static. Rediscover every session. See `RUNTIME_REBINDING_GUIDE.md`.

---

## Physical Component Map

```
[ESP32]  ──Wi-Fi──▶  [Pi :8080 relay  ]  ──HTTP──▶  [Laptop :5000 emulator]
                   or [Pi :8090 gateway]
         ──Wi-Fi──▶  [Laptop :5000 emulator]   ← direct mode (no Pi)
```

| Component | Source file | Default port | Runs on |
|-----------|------------|-------------|---------|
| Cloud emulator | `cloud_emulator/api/app.py` | 5000 | Laptop (WSL) |
| Pi dumb relay | `gateway/pi/iot_gateway_relay.py` | 8080 | Raspberry Pi |
| Pi proposed gateway | `gateway/pi/iot_gateway_proposed.py` | 8090 | Raspberry Pi |
| B1 firmware | `esp32_firmware/baseline1_http/` | → Pi:8080 | ESP32 |
| B2 firmware | `esp32_firmware/baseline2_token/` | → Pi:8080 | ESP32 |
| B3 firmware | `esp32_firmware/baseline3_enroll/` | → Pi:8080 | ESP32 |
| Proposed firmware | `esp32_firmware/proposed_gateway/` | → Pi:8090 | ESP32 |

---

## Current Real Status (as of 2026-04-08)

### What is complete and has canonical evidence

| Method | Result | Evidence |
|--------|--------|---------|
| B1 — direct to emulator | 5/5 PASS, mean 1663.2 ms | `capture/b1_serial_live.txt` + `data/raw/b1_live_rerun_2026-04-05_evidence.md` |
| B3 — direct to emulator | 5/5 PASS, mean 1375.2 ms | `cloud_emulator/api/logs/enroll_log.jsonl` + `data/raw/b3_live_rerun_2026-04-05_evidence.md` |
| Proposed — via Pi gateway | 5/5 PASS, mean 1997.0 ms | `capture/proposed_p5_repeated_runs_latest.txt` + `data/raw/proposed_p5_evidence_2026-04-07.md` |
| B2 replay resistance | HTTP 200 → HTTP 401 replay confirmed | `capture/b2_replay_scenario_2026-04-06.txt` + `data/raw/b2_replay_mitm_2026-04-06_evidence.md` |

### In progress / pending

| Item | State | Note |
|------|-------|------|
| B2 clean 10/10 run | Server: 10/10 PASS. Client: 7/10 PASS (runs 4,7,10 timed out at ~5010 ms, errno=11) | 8 s receive timeout fix already applied to firmware; clean re-run needed after reflash |
| B2 rows in CSVs | No B2 rows in `data/processed/final_results.csv` or `results.csv` | Depends on clean B2 run above |
| pcap/network captures | `capture/pcaps/` is empty. Figs 7.2/7.3 are programmatic renders, not real pcap files | Can be collected from loopback with tcpdump without hardware |
| Report assembly | Content exists as four markdown patches in `docs/report_patch_*.md` | Final DOCX/PDF must be assembled into university template |
| B2 MITM scenarios A, B, D | Scenario C (replay) confirmed empirically; A/B/D defined in `attacks/scenarios.md` | Not yet executed; available as extension work |

### Known unstable areas

- **Pi gateway process persistence**: `gateway/pi/iot_gateway_proposed.py` must be started manually via SSH each session. It does not auto-restart after crash or Pi reboot. If port 8090 stops responding mid-run, restart the process — the firmware recovers cleanly on the next EN button press.
- **B3 canonical UART not preserved**: The `capture/b3_serial_live.txt` file does not exist. B3 evidence relies on server-side `enroll_log.jsonl`. Raw UART for the Apr 5 rerun was not saved.
- **WSL2 NAT caveat**: The Pi cannot reach the WSL internal IP directly. The Pi's `UPSTREAM_HOST` must point to the **Windows hotspot IP** (e.g., `172.20.10.2:5000`), not the WSL eth0 IP. The cloud emulator binds to `0.0.0.0:5000` so it is reachable from the Windows interface.

### Known data inconsistency

`docs/report_patch_proposed_p5_2026-04-07.md` cites "~1254 ms" as the B3 mean. The correct value from `data/raw/b3_live_rerun_2026-04-05_evidence.md` and `final_results.csv` is **1375.2 ms**. Do not use 1254 ms. This must be corrected before the report is finalized.

---

## What to Read First (in order)

1. **This file** — overview and status
2. `CURRENT_STATUS_MATRIX.md` — one-page component table
3. `NEXT_EXECUTION_PATH.md` — what to do next and in what order
4. `SETUP_ON_ANOTHER_LAPTOP.md` — if setting up on a new machine
5. `RUNTIME_REBINDING_GUIDE.md` — every session before running anything
6. `COMPONENT_RUNBOOKS.md` — how to start/stop each component
7. `EVIDENCE_INDEX.md` — where all logs and captures live

---

## What to Run First (after setup)

```bash
# 1. Discover current IPs
bash scripts/handoff/print_session_ips.sh

# 2. Start cloud emulator
cd cloud_emulator/api && source .venv/bin/activate && python app.py

# 3. Verify emulator is reachable from WSL
curl http://localhost:5000/health

# 4. Test emulator is reachable from Pi
ssh pi@<PI_IP> "curl http://<LAPTOP_HOTSPOT_IP>:5000/health"

# 5. Start Pi relay (for B1/B2/B3 via-Pi experiments)
ssh pi@<PI_IP> "python3 ~/iot_gateway_relay.py"
```

Then: update firmware targets → build → attach ESP32 via usbipd → flash → monitor.

---

## Recommended Next Steps

1. **Reflash B2 firmware** (8 s fix already applied) and collect a clean 10/10 run
2. **Integrate B2 results** into `data/processed/final_results.csv` after clean run
3. **Correct "~1254 ms" → "1375.2 ms"** in `docs/report_patch_proposed_p5_2026-04-07.md` before finalising the report
4. **Assemble final report DOCX** from the four markdown patches in `docs/report_patch_*.md`

See `NEXT_EXECUTION_PATH.md` for the detailed ordered list with done criteria.

---

## Warnings

- **Do not commit `cloud_emulator/pki/ca.key`**. This file is present locally but must not appear in public VCS. It signs device certificates. Store separately.
- **Do not commit `esp32_firmware/*/sdkconfig`**. Contains Wi-Fi password in plaintext. Already in `.gitignore` but verify before pushing.
- **Do not commit `cloud_emulator/api/b2_tokens.json`**. Contains session token state.
- **IPs change every session.** Never hardcode a session IP into a permanent document.
