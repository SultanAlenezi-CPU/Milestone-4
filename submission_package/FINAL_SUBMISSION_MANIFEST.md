# FINAL SUBMISSION MANIFEST
## Project: Secure IoT Device Onboarding for Smart Homes
## Prepared: 2026-04-08

---

## PACKAGE STRUCTURE OVERVIEW

```
submission_package/
  01_report/          — Canonical report content patches (no final DOCX/PDF yet — see §MISSING)
  02_source_code/     — All firmware, cloud emulator, gateway scripts
  03_data/            — Processed CSV datasets (source of truth for all reported numbers)
  04_evidence/        — Raw UART captures, evidence notes, server logs
  05_figures/         — All Chapter 7 PNG figures (11/11 complete)
  06_docs/            — README, protocol spec, handoff/runbook docs
  07_slides/          — PLACEHOLDER (slides not yet prepared — see §MISSING)
  08_admin/           — This manifest + admin checklist
```

---

## 01_report — Canonical Report Content

These are the authoritative data and narrative patches to insert into the final DOCX.
No final DOCX or PDF exists yet — see §MISSING.

| File | Purpose |
|------|---------|
| `report_patch_b1_rerun_2026-04-05.md` | Canonical B1 results: 5/5 PASS, mean 1663.2 ms, std 789.4 ms. Supersedes old simulation rows. |
| `report_patch_b3_rerun_2026-04-05.md` | Canonical B3 results: 5/5 PASS, mean 1375.2 ms, std 282.5 ms. Supersedes Mar 4 session rows. |
| `report_patch_proposed_p5_2026-04-07.md` | Canonical Proposed Method results: 5/5 PASS, mean 1997.0 ms, std 4.18 ms. Includes comparison context. **NOTE: the "~1254 ms" B3 reference in this file is a known error — correct value is 1375.2 ms (see report_patch_b3).** |
| `protocol_lock_full_scope_2026-04-06.md` | Full protocol design specification for B2 and Proposed Method. Authoritative reference for Chapter 4/5. |

---

## 02_source_code — All Project Source

### ESP32 Firmware (4 projects)

| Path | Baseline | Key file | Last modified |
|------|----------|----------|--------------|
| `esp32_firmware/baseline1_http/` | B1 — plain HTTP health-check | `main/http_request_example_main.c` | Apr 5 2026 |
| `esp32_firmware/baseline2_token/` | B2 — OOB token provisioning | `main/http_request_example_main.c` | Apr 7 2026 (8s timeout fix applied) |
| `esp32_firmware/baseline3_enroll/` | B3 — CSR enrollment | `main/http_request_example_main.c` | Apr 5 2026 |
| `esp32_firmware/proposed_gateway/` | Proposed — two-phase gateway | `main/http_request_example_main.c` | Apr 7 2026 |

**Build requirements:** ESP-IDF v5.5.3. Source IDF before building: `. ~/esp-idf-v5.5.3/export.sh`
**sdkconfig warning:** sdkconfig files contain Wi-Fi credentials. Do not share publicly. Each deployer must run `idf.py menuconfig` to configure credentials.

### Cloud Emulator

| File | Purpose |
|------|---------|
| `cloud_emulator/app.py` | Flask service. Endpoints: GET /health, POST /enroll, POST /provision. Port 5000. |
| `cloud_emulator/requirements.txt` | Python dependencies (Flask + cryptography). Install with `pip install -r requirements.txt`. |
| `cloud_emulator/README.md` | Setup and run instructions. |
| `cloud_emulator/b2_tokens.example.json` | Example token store for B2 sessions. Copy to `b2_tokens.json` and update before each B2 run. |
| `cloud_emulator/ca.crt` | Local CA certificate (public, safe to include). |
| `cloud_emulator/ca.key_KEEP_SECURE` | **CA private key. Store securely. Do not post publicly.** Required to run the emulator. |

### Pi Gateway Scripts

| File | Purpose |
|------|---------|
| `gateway_pi/iot_gateway_relay.py` | Transparent relay (port 8080). Routes /health, /enroll, /provision to UPSTREAM_HOST:5000. |
| `gateway_pi/iot_gateway_proposed.py` | Active gateway (port 8090). Implements Phase 1 auth + Phase 2 session-gated enroll. Standard library only. |
| `gateway_pi/device_registry.example.json` | Example device registry. Copy to `device_registry.json` on Pi and set real tokens. |
| `gateway_pi/requirements.txt` | Gateway Python requirements. |
| `gateway_pi/README_m4_gateway_first_success_2026-04-05.md` | Notes from first successful Pi gateway run. |

### Utility Scripts

| File | Purpose |
|------|---------|
| `scripts/print_session_ips.sh` | Prints current configured IP values across all firmware and gateway files. |
| `scripts/update_b1_target.sh` | Updates WEB_SERVER in B1 firmware for new session. |
| `scripts/update_b3_target.sh` | Updates WEB_SERVER in B3 firmware for new session. |
| `scripts/update_pi_relay_upstream.sh` | Updates UPSTREAM_HOST in Pi relay config. |
| `scripts/generate_ch7_visuals.py` | Regenerates all Chapter 7 PNG figures from existing evidence files. |

---

## 03_data — Processed Datasets (Source of Truth)

| File | Rows | Purpose | Status |
|------|------|---------|--------|
| `final_results.csv` | 25 data rows | Master dataset: B1×10, B3×10, Proposed×5. Schema: run_id, baseline, latency_ms, heap_delta, http_status, result, notes. | **CANONICAL — use for all report tables** |
| `results.csv` | 20 data rows | Secondary dataset: B1×5 live rerun, B3×5 live rerun, Proposed×5. Slightly different schema. | CANONICAL |
| `proposed_p5_runpack_2026-04-07.csv` | 5 data rows | Detailed Proposed Method run pack with per-phase breakdown (auth_ms, csr_ms, enroll_ms, total_ms, heap fields). | CANONICAL for Proposed Method detail table |

**Important:** B2 data is NOT yet in these CSVs. Server-side confirmed 10/10 HTTP 200. Client-side best run: 7/10 PASS (ESP32 timeout issue). 8s fix applied but clean re-run pending.

---

## 04_evidence — Raw Evidence

### Evidence Notes

| File | Covers |
|------|--------|
| `evidence_notes/b1_live_rerun_2026-04-05_evidence.md` | B1 canonical 5-run PASS with per-run values and source file verification |
| `evidence_notes/b3_live_rerun_2026-04-05_evidence.md` | B3 canonical 5-run PASS with server log corroboration |
| `evidence_notes/b2_replay_mitm_2026-04-06_evidence.md` | B2 Scenario C replay attack: HTTP 200 first use → HTTP 401 replay confirmed |
| `evidence_notes/proposed_p5_evidence_2026-04-07.md` | Proposed canonical 5-run PASS pack, supplemental run, recovered run, pcap status |
| `evidence_notes/proposed_gateway_recovered_pass_2026-04-07.md` | Gateway restart support run (operational evidence only, not in canonical pack) |
| `evidence_notes/m4_b1_via_pi_gateway_2026-04-05_evidence.md` | B1 via-Pi milestone: 5/5 HTTP 200 confirmed |
| `evidence_notes/m4_b3_via_pi_gateway_2026-04-05_evidence.md` | B3 via-Pi milestone: relay 5/5 confirmed, ESP32-side partial |

### Raw UART Captures

| File | Covers | Status |
|------|--------|--------|
| `raw_uart_captures/b1_serial_live.txt` | B1 live rerun: 5 MEASURE lines, all HTTP 200. Full 272-line session. | CANONICAL for B1 |
| `raw_uart_captures/proposed_p5_canonical.txt` | Proposed canonical 5-run pack: 5 PROPOSED_MEASURE lines + supplemental. | CANONICAL for Proposed |
| `raw_uart_captures/b2_replay_scenario_2026-04-06.txt` | B2 replay scenario: first use 200, replay 401, server log tail. | CANONICAL for security section |
| `raw_uart_captures/b2_via_pi_clean_2026-04-06_final.txt` | B2 via-Pi: 7/10 client-side PASS (runs 4,7,10 timed out at 5010ms, errno=11). Server confirmed 10/10. | Best available B2 via-Pi |
| `raw_uart_captures/b2_direct_clean_2026-04-06.txt` | B2 direct: multi-session file. Runs 3–10 HTTP 200; runs 1–2 HTTP 401 (token reuse from prior session). | Partial — verify before citing |
| `raw_uart_captures/b3_via_pi_serial_live.txt` | B3 via-Pi serial attempt. No clean 5/5 PASS ESP32-side; relay-side 5/5 confirmed separately. | Historical only |

### Server Logs

| File | Covers |
|------|--------|
| `server_logs/enroll_log.jsonl` | 379 entries: all POST /enroll requests to cloud emulator (B3 + Proposed via Pi) |
| `server_logs/provision_log.jsonl` | B2 token provisioning log: runs 1–10 all HTTP 200 + replay run 101 HTTP 200 + replay 401 |
| `server_logs/proposed_gateway_log.jsonl` | Pi proposed gateway log: Phase 1 auth + Phase 2 enroll sequence with P4 debug entries |
| `server_logs/iot_gateway_relay_2026-04-05.log` | Pi relay log from M4 first gateway session |

---

## 05_figures — Chapter 7 Figures

All generated from existing evidence files (no hardware needed).

| File | Figure | Section | Status |
|------|--------|---------|--------|
| `fig_7_1_topology.png` | 7.1 Testbed topology | §7.1 Architecture | READY |
| `fig_7_4_latency_comparison.png` | 7.4 Mean latency comparison B1/B3/Proposed | §7.5 Comparison | READY |
| `fig_7_5_proposed_phase_breakdown.png` | 7.5 Proposed phase breakdown (stacked + pie) | §7.4 Proposed | READY |
| `fig_7_6_proposed_uart_pass.png` | 7.6 Proposed UART canonical 5-run PASS | §7.4 Proposed | READY |
| `fig_7_7_b2_replay.png` | 7.7 B2 replay scenario HTTP 200 → HTTP 401 | §7.6 Security | READY |
| `fig_7_8_b2_via_pi_timeout.png` | 7.8 B2 via-Pi client-side timeout evidence | §7.3 B2 | READY (optional) |
| `fig_7_9_gateway_log.png` | 7.9 Pi gateway log event sequence | §7.4 Proposed | READY (optional) |
| `fig_7_10_enroll_log.png` | 7.10 Cloud enroll log B3 + Proposed | §7.3/§7.4 | READY (optional) |
| `fig_7_11_provision_log.png` | 7.11 Provision log B2 10-run + replay | §7.3/§7.6 | READY (optional) |
| `fig_7_2_b1_plaintext.png` | 7.2 B1 plaintext HTTP GET /health | §7.6 Security | READY — generated 2026-04-08 (gen_wireshark_figs.py) |
| `fig_7_3_b3_enroll.png` | 7.3 B3 POST /enroll with real P-256 CSR | §7.6 Security | READY — generated 2026-04-08 (gen_wireshark_figs.py) |

To regenerate any PNG: `python3 02_source_code/scripts/generate_ch7_visuals.py`
Windows path: `\\wsl$\Ubuntu\home\iot_onboarding\iot_onboarding\submission_package\05_figures\`

---

## 06_docs — Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main project README. Note: milestone table shows M4 as "in progress" — update before final submission. |
| `PROJECT_LOG.md` | Historical project decisions and milestone log. |
| `attack_scenarios.md` | Security scenario definitions (A/B/C/D) for MITM and replay attacks. |
| `capture_guide.md` | Guide for capturing pcap evidence. |
| `m4_checkpoint_2026-04-05.md` | M4 first gateway success checkpoint. |
| `b2_dev_tokens_and_first_run.md` | B2 token management and first-run procedure. |
| `proposed_gateway_dev_notes.md` | Proposed gateway development notes and design decisions. |
| `handoff/new_laptop_setup.md` | Full setup guide for new machine (ESP-IDF, WSL, hotspot, Pi). |
| `handoff/session_checklist.md` | Per-session start checklist. |
| `handoff/network_rebind.md` | What to update when IPs change between sessions. |
| `handoff/validation_on_new_laptop.md` | First validation sequence on a new machine. |
| `runbooks/portability_handoff_draft_2026-04-07.md` | Fixed vs. session-variable values. Pre-flight checklist. |
| `runbooks/gateway_restart_runbook_2026-04-07.md` | Step-by-step Pi gateway restart procedure. |
| `runbooks/another_laptop_migration_checklist_2026-04-07.md` | Complete another-laptop migration guide. |
| `runbooks/operator_quickstart_2026-04-07.md` | 10-step quick resume guide. |
| `runbooks/runtime_values_worksheet_2026-04-07.md` | Fill-in worksheet for session-specific values. |

---

## 07_slides

**EMPTY — slides not yet prepared. See §MISSING.**

---

## 08_admin

Contains this manifest and submission checklist.

---

## ⚠ MISSING / NEEDS MANUAL PREPARATION

These items are required for final submission but do not exist as files in the repo:

| # | Item | Type | Notes |
|---|------|------|-------|
| 1 | **Final report DOCX** | NON-FILE / ADMIN ITEM | The report must be assembled from the four `01_report/` patches inserted into the university report template. No .docx exists in the repo. |
| 2 | **Final report PDF** | NON-FILE / ADMIN ITEM | Export from final DOCX. Must be produced after DOCX is complete. |
| 3 | **Defense / presentation slides** | NON-FILE / ADMIN ITEM | No .pptx or equivalent file exists anywhere in the project. Must be created from scratch. |
| 4 | **Signed submission checklist / declaration form** | NON-FILE / ADMIN ITEM | University-specific form. Must be completed manually and signed. |
| 5 | **B2 clean 10/10 PASS capture** | FILE NEEDED | B2 via-Pi currently 7/10 ESP32-side. 8s timeout fix applied. A new run is needed after reflashing. No ESP32 session yet with 8s fix. |
| 6 | **B2 rows in master CSVs** | FILE NEEDED | `final_results.csv` and `results.csv` contain no B2 rows. Must be integrated after B2 clean run is collected. |
| 7 | **Cover page / title page** | NON-FILE / ADMIN ITEM | Not present. Standard for graduation project reports. |
| 8 | **README update** | FILE NEEDED | Current README shows M4 milestone status as incomplete/partial. Should reflect final state before submission. |

*(Fig 7.2 and Fig 7.3 were generated on 2026-04-08 using curl + programmatic rendering — no longer missing.)*

---

## ⚠ EXCLUDED FROM HANDOVER

These files/folders exist in the repo but should NOT be included in the submission package:

| Path | Reason |
|------|--------|
| `venv/` | Python virtual environment, 288 MB. Recipient installs with `pip install -r requirements.txt`. |
| `cloud_emulator/api/.venv/` | Second Python venv, 42 MB. Same reason. |
| `**/__pycache__/` | Python bytecode cache. Auto-generated. |
| `.claude/settings.local.json` | IDE tool settings file — machine-specific. |
| `ai/` | Internal session planning notes (NEXT_TASK_*.md). Not part of project deliverable. |
| `docs/new_chat_handoff_prompt_m4_portability_2026-04-07.md` | Session continuation reference. Internal tool, not a report appendix. |
| `data/raw/*.bak_*` | Backup files (e.g., `proposed_p5_evidence_2026-04-07.md.bak_*`). Superseded. |
| `data/processed/*.bak_*` | CSV backup files. Superseded. |
| `cloud_emulator/api/app.py.bak_20260406_a1_provision` | Old backup of app.py before /provision was added. Superseded. |
| `gateway/pi/iot_gateway_relay.py.bak_20260406_a2_provision` | Old backup of relay before /provision route. Superseded. |
| `gateway/app/main.py` | Early Feb 25 gateway scaffold. Superseded entirely by `gateway/pi/` files. |
| `capture/b2_direct_first_run_2026-04-06.txt` | First partial attempt. Superseded by clean version. |
| `capture/b2_direct_first_run_2026-04-06_retry.txt` | Retry of first attempt. Superseded. |
| `capture/b2_via_pi_clean_2026-04-06.txt` | Intermediate version. Superseded by `_final.txt`. |
| `capture/b2_via_pi_clean_2026-04-06_retry.txt` | Retry. Superseded. |
| `capture/b2_via_pi_retry_2026-04-06.txt` | Retry. Superseded. |
| `capture/proposed_first_run_2026-04-06.txt` | P4 first debug run (all FAIL). Not evidence, debugging artifact. |
| `capture/proposed_first_run_2026-04-07_000925.txt` | P4 intermediate (mostly FAIL). Superseded. |
| `capture/proposed_first_run_2026-04-07_001346.txt` | P4 intermediate. Superseded. |
| `capture/proposed_retry_after_pi_fix_2026-04-07_002649.txt` | Pre-canonical retry. Superseded by canonical pack. |
| `capture/proposed_pcap_support_run_2026-04-07_004824.txt` | Support run. Operational artifact only. |
| `capture/proposed_pi_pcap_support_run_2026-04-07_005231.txt` | Support run. Operational artifact only. |
| `data/raw/b1_uart_5runs_20260304_161053.log` | Duplicate of b1_uart_5runs.log from same session. Keep only one. |
| `data/raw/b3_uart_enroll_20260304_170807.log` | Short partial early session (672 bytes). |
| `data/raw/b3_uart_enroll_20260304_171047.log` | Short partial early session (672 bytes). |
| `data/raw/b3_uart_enroll_20260304_171250.log` | Zero bytes. Empty file. |
| `data/raw/b3_uart_enroll_20260304_190944.log` | Intermediate session. Superseded by b3_uart_enroll_final. |
| `data/raw/b3_uart_enroll_20260304_191754.log` | Intermediate session. Superseded. |
| `esp32_firmware/*/sdkconfig.old` | Old sdkconfig backup. Not needed. |
| `esp32_firmware/**/build/` (not present) | Build artifacts would be excluded if present. |
| `docs/diagrams/` | Empty directory. Nothing to submit. |
| `docs/screenshots/` | Empty directory. Nothing to submit. |
| `analysis/plots/` | Empty directory. Figures are in `report_assets/ch7_visuals/`. |
| `attacks/scripts/` | Empty directory. |
| `cloud_emulator/api/b2_tokens.json` | Contains session tokens (not real secrets, but session-specific). Submittable only as b2_tokens.example.json. The live file should not be committed to public repos. |

---

## BEST FINAL FILE SELECTIONS

| Purpose | Chosen File | Rejected Alternatives | Reason |
|---------|------------|----------------------|--------|
| Master dataset | `data/processed/final_results.csv` (25 rows) | `data/processed/results.csv` (20 rows) | More complete; includes both B1 simulation rows (for historical reference) and all live rerun rows |
| Proposed detailed pack | `data/processed/proposed_p5_runpack_2026-04-07.csv` | Rows 21–25 of final_results.csv | Richer schema with per-phase latency breakdown |
| Canonical Proposed UART | `capture/proposed_p5_repeated_runs_latest.txt` | `proposed_p5_repeated_runs_2026-04-07_002848.txt` | The `latest.txt` symlink/copy contains the 5 canonical values matching the evidence note exactly |
| B2 via-Pi best capture | `capture/b2_via_pi_clean_2026-04-06_final.txt` | All other b2_via_pi_*.txt files | Most recent clean attempt; explicitly labeled final |
| B2 direct best capture | `capture/b2_direct_clean_2026-04-06.txt` | `b2_direct_first_run*.txt` | Most complete multi-session file |
| B3 UART history | `data/raw/b3_uart_enroll_final_20260304_193449.log` | 5 other b3_uart_enroll_*.log | "final" in filename; largest file from that session |
| Cloud emulator source | `cloud_emulator/api/app.py` (216 lines) | `app.py.bak_20260406_a1_provision` (115 lines) | Current version includes /provision endpoint. Backup is superseded. |
| Pi relay source | `gateway/pi/iot_gateway_relay.py` (68 lines) | `iot_gateway_relay.py.bak_*` and `gateway/app/main.py` | Current version includes /provision route; bak and old scaffold are superseded. |
