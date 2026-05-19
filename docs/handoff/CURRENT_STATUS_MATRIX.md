# Current Status Matrix — IoT Onboarding Testbed

**Last updated: 2026-04-08**
Source of truth: evidence files in `data/raw/`, captures in `capture/`, CSVs in `data/processed/`.

---

## Component Status

| Component / Method | Implementation | Build | Runtime | Evidence | Dataset | Notes |
|---|---|---|---|---|---|---|
| **B1 — plain HTTP health-check** | Complete | Builds cleanly | Verified 5/5 PASS (Apr 5) | Canonical: `capture/b1_serial_live.txt` | In CSVs (rows 11–15 of `final_results.csv`) | Firmware currently targets Pi:8080; re-point to direct if needed |
| **B2 — token provisioning** | Complete | Builds cleanly | **Partial**: server 10/10 PASS; client 7/10 (runs 4,7,10 timeout at 5010 ms) | Best capture: `capture/b2_via_pi_clean_2026-04-06_final.txt` | **NOT in CSVs** | 8 s timeout fix applied; clean re-run pending |
| **B3 — CSR enrollment** | Complete | Builds cleanly | Verified 5/5 PASS (Apr 5) | Server log: `cloud_emulator/api/logs/enroll_log.jsonl`; UART not preserved | In CSVs (rows 16–20 of `final_results.csv`) | No `capture/b3_serial_live.txt` — only server-side log for Apr 5 run |
| **Proposed — gateway two-phase** | Complete | Builds cleanly | Verified 5/5 PASS (Apr 7) | Canonical: `capture/proposed_p5_repeated_runs_latest.txt` | In CSVs (rows 21–25 of `final_results.csv`) | Each run requires Pi gateway restart (no auto-start); fw_run_id always prints "1" |
| **Cloud emulator** | Complete | N/A (Python) | Running (port 5000) | `cloud_emulator/api/logs/enroll_log.jsonl`, `provision_log.jsonl` | — | Flask + cryptography; `.venv` required; `ca.key` must be present |
| **Pi dumb relay** | Complete | N/A (Python) | Verified M4 Apr 5 | `gateway/logs/iot_gateway_relay_2026-04-05.log` | — | Deployed to Pi as `~/iot_gateway_relay.py`; start manually via SSH |
| **Pi proposed gateway** | Complete | N/A (Python) | Verified M4 Apr 7 | `gateway/logs/proposed_gateway_log.jsonl` | — | Port 8090; `UPSTREAM_HOST` env var must point to laptop hotspot IP |
| **B2 replay resistance** | Verified | — | Confirmed HTTP 401 on replay | `capture/b2_replay_scenario_2026-04-06.txt` | — | Token marked used before forwarding; replay returns 401 |
| **B2 MITM scenarios A, B, D** | Defined | — | Not executed | `attacks/scenarios.md` (design only) | — | Passive sniff (A), modification (B), rogue server (D) not yet run |
| **pcap / network captures** | — | — | Not collected | `capture/pcaps/` is empty | — | Figs 7.2/7.3 are programmatic renders, not real pcap files |
| **final_results.csv** | 25 rows | — | — | Rows 1–10: sim/early B1+B3; 11–15: B1 live; 16–20: B3 live; 21–25: Proposed | — | No B2 rows |
| **results.csv** | 20 rows | — | — | Overlapping schema; rows 1–10 live B1+B3, 11–20 B1+B3 live Apr 5 | — | No B2 rows; use `final_results.csv` as primary |
| **Report patches** | 4 files | — | — | See `docs/report_patch_*.md` | — | Known error: proposed patch cites B3 mean as "~1254 ms" — correct is 1375.2 ms |
| **Chapter 7 figures** | 11 PNGs | — | — | `report_assets/ch7_visuals/` | — | All 11 generated; figs 7.2/7.3 are programmatic (no real pcap) |
| **Final report DOCX/PDF** | Not started | — | — | — | — | Must be assembled from 4 markdown patches into university template |
| **Defense slides** | Not started | — | — | — | — | No .pptx exists anywhere |

---

## Data Integrity Notes

### B2 failing runs discrepancy
The session description at one point referred to "runs 7, 9, and 10" as timeout failures.
The authoritative capture file `capture/b2_via_pi_clean_2026-04-06_final.txt` shows runs **4, 7, and 10** as the timeouts. The capture file is authoritative.

### B3 mean conflict
`docs/report_patch_proposed_p5_2026-04-07.md` cites "~1254 ms" for B3 mean latency.
Verified arithmetic from `final_results.csv` rows 16–20: (1782+1142+1554+1147+1251)/5 = **1375.2 ms**.
The "~1254 ms" figure is incorrect and must not be cited.

### Proposed firmware run_id
The proposed firmware prints `run_id=1` on every EN-button reset because `RUN_ID` is compile-time fixed.
Evidence notes assign **external sequence numbers 1–5** to the canonical pack. These external numbers appear in `data/processed/proposed_p5_runpack_2026-04-07.csv` and must not be confused with the firmware's printed run_id.

---

## IP Snapshot (from last session — do not reuse)

| Device | Role | Last known IP | Note |
|--------|------|--------------|------|
| Laptop | Cloud emulator | 172.20.10.2 | DHCP — rediscover each session |
| Pi | Gateway/relay | 172.20.10.4 | DHCP — often stable on same hotspot |
| ESP32 | Firmware target | 172.20.10.3 | DHCP — rediscover if needed |

All firmware currently compiled with `WEB_SERVER "172.20.10.4"` (Pi).
