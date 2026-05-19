# Secure IoT Device Onboarding Testbed

Research testbed for evaluating the security of ESP32 device onboarding workflows
under controlled lab conditions. The project measures latency, memory overhead, and
security posture across multiple onboarding baselines, with planned attack scenarios.

## Purpose

This repository contains firmware source, a local cloud/PKI emulator, a gateway
scaffold, and all experiment evidence (raw UART logs, processed CSVs, packet captures)
for a structured comparison of onboarding methods ranging from plain HTTP to
certificate-based mutual authentication.

## Repository Layout

    esp32_firmware/          ESP-IDF firmware projects, one folder per baseline
    cloud_emulator/api/      Local Flask enrollment service (PKI/CA emulator)
    cloud_emulator/pki/      Local CA certificate (ca.crt) — private key excluded from VCS
    gateway/                 Raspberry Pi gateway service (planned, M4)
    attacks/                 MITM attack scenario definitions and test scripts
    capture/                 Packet capture guide and pcap evidence (capture/pcaps/)
    data/raw/                Verbatim UART serial logs from ESP32 hardware runs
    data/processed/          Per-run metric CSVs — source of truth for reported results
    analysis/                Plots and analysis scripts (M4+)
    docs/                    Architecture diagrams and screenshots

## Milestone Status

| Milestone | Description                                              | Status                                                       |
|-----------|----------------------------------------------------------|--------------------------------------------------------------|
| M1        | WSL/ESP-IDF environment, repo scaffold                   | Complete                                                     |
| M2        | Baseline 1 — plain HTTP health-check over Wi-Fi          | Complete                                                     |
| M3        | Baseline 3 — cloud PKI certificate enrollment (CSR/sign) | Software validation complete; evidence packaging in progress |
| M4        | Raspberry Pi gateway — first gateway success             | First checkpoint complete (2026-04-05); pcap/dataset/report integration pending |

M4 will introduce a headless Raspberry Pi 4 as a local gateway and stable emulator
host. Four authorized attack scenarios (passive sniff, active MITM, replay, rogue
enrollment) are defined in `attacks/scenarios.md`.

## Environment Setup

Requirements: WSL2 (Ubuntu 24.04.4), ESP-IDF v5.5.3 installed at `~/esp-idf-v5.5.3`.
ESP-IDF is sourced automatically from `~/.bashrc`. Verify with:

    idf.py --version   # expected: ESP-IDF v5.5.3

Start the cloud emulator for local testing:

    cd cloud_emulator/api
    source .venv/bin/activate
    python app.py      # listens on port 5000

For ESP32 Wi-Fi connectivity, run the emulator on your Windows host or Raspberry Pi,
not inside WSL, so the device can reach it over the LAN.

## sdkconfig and Credentials

`sdkconfig` files are excluded from version control as they contain Wi-Fi credentials
in plaintext. After cloning, configure each firmware project with your own credentials
via `idf.py menuconfig` before building.

## Evidence and Data

`data/raw/` contains verbatim UART logs from all ESP32 hardware runs, kept unmodified.

`data/processed/` contains `results.csv` and `final_results.csv` with per-run metrics
(latency, heap delta, HTTP status). These are the source of truth for reported results.

`cloud_emulator/api/logs/enroll_log.jsonl` is the server-side enrollment log with one
JSON record per request.

`capture/pcaps/` will hold packet capture files collected during live hardware runs.
This folder is currently empty.

## Portability and Handoff

To redeploy this testbed on a new laptop, see:

- `docs/handoff/new_laptop_setup.md` — full setup guide for a new machine
- `docs/handoff/session_checklist.md` — per-session runbook
- `docs/handoff/network_rebind.md` — what to update when IPs change
- `docs/handoff/validation_on_new_laptop.md` — first validation sequence

IPs assigned by the phone hotspot are session-specific and must be rediscovered
each time. Use `bash scripts/handoff/print_session_ips.sh` to review current
configured values, and the helper scripts under `scripts/handoff/` to update them.

## Security Note

This testbed uses a local self-signed CA for enrollment experiments. The CA certificate
(`cloud_emulator/pki/ca.crt`) is committed for reproducibility. The CA private key is
excluded from version control — store it in a secure location and restore it to
`cloud_emulator/pki/ca.key` when running the emulator.
