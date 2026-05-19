# Evidence Index — IoT Onboarding Testbed

**All evidence files with their status, location, and what they prove.**
No invented files. Files listed as missing or empty are honestly marked.

---

## UART Capture Files

| File | Method | Session | Runs | Status | Notes |
|---|---|---|---|---|---|
| `capture/b1_serial_live.txt` | B1 | Apr 5 2026 | 5 | **CANONICAL** | 272 lines; all 5 MEASURE lines verified against `final_results.csv` rows 11–15 |
| `capture/b2_direct_clean_2026-04-06.txt` | B2 direct | Apr 6 2026 | Multi-session | Partial | Concatenated sessions; runs 1–2 are HTTP 401 (token reuse from prior session); runs 3–10 are HTTP 200 |
| `capture/b2_direct_first_run_2026-04-06.txt` | B2 direct | Apr 6 2026 | — | Superseded | First attempt; superseded by clean version |
| `capture/b2_direct_first_run_2026-04-06_retry.txt` | B2 direct | Apr 6 2026 | — | Superseded | Retry; superseded |
| `capture/b2_replay_scenario_2026-04-06.txt` | B2 replay | Apr 6 2026 | 2 (1+replay) | **CANONICAL** | First use HTTP 200; replay HTTP 401; confirms replay resistance |
| `capture/b2_via_pi_clean_2026-04-06.txt` | B2 via-Pi | Apr 6 2026 | — | Superseded | Intermediate; superseded by _final.txt |
| `capture/b2_via_pi_clean_2026-04-06_final.txt` | B2 via-Pi | Apr 6 2026/7 | 10 (7 PASS) | Best available B2 | Server: 10/10 PASS. Client: runs 4,7,10 timed out (errno=11, 5010 ms). 8 s fix not yet applied in this run |
| `capture/b2_via_pi_clean_2026-04-06_retry.txt` | B2 via-Pi | Apr 6 2026 | — | Superseded | |
| `capture/b2_via_pi_minfix_2026-04-06.txt` | B2 via-Pi | Apr 6/7 2026 | — | Intermediate | Binary/mixed content; pre-fix attempt |
| `capture/b2_via_pi_retry_2026-04-06.txt` | B2 via-Pi | Apr 6/7 2026 | — | Superseded | |
| `capture/b3_via_pi_serial_live.txt` | B3 via-Pi | Apr 5 2026 | Partial | Historical | No clean 5/5 client-side PASS; relay-side confirmed separately |
| `capture/b3_via_pi_serial_fix_2026-04-05.txt` | B3 via-Pi | Apr 5 2026 | Partial | Historical | Debug/fix attempts |
| `capture/proposed_first_run_2026-04-06.txt` | Proposed | Apr 6 2026 | All FAIL | Debug artifact | Pre-fix; all runs failed. Not evidence. |
| `capture/proposed_first_run_2026-04-07_000925.txt` | Proposed | Apr 7 00:09 | Mostly FAIL | Debug artifact | Pre-fix intermediate |
| `capture/proposed_first_run_2026-04-07_001346.txt` | Proposed | Apr 7 00:16 | Partial | Debug artifact | Pre-canonical |
| `capture/proposed_retry_after_pi_fix_2026-04-07_002649.txt` | Proposed | Apr 7 00:27 | Partial | Pre-canonical | Not the canonical pack |
| `capture/proposed_p5_repeated_runs_2026-04-07_002848.txt` | Proposed | Apr 7 00:30 | 3 PASS | Preliminary | Earlier values; does NOT match canonical pack |
| `capture/proposed_p5_repeated_runs_latest.txt` | Proposed | Apr 7 00:32 | 5+1 PASS | **CANONICAL** | 5 canonical runs + 1 supplemental. Values match `data/raw/proposed_p5_evidence_2026-04-07.md` exactly |
| `capture/proposed_pcap_support_run_2026-04-07_004824.txt` | Proposed | Apr 7 00:49 | 1 | Operational support | Post-gateway-restart liveness check; not in canonical pack |
| `capture/proposed_pi_pcap_support_run_2026-04-07_005231.txt` | Proposed | Apr 7 00:52 | 1 | Operational support | Same session; not in canonical pack |

> **B3 canonical UART missing:** There is no `capture/b3_serial_live.txt`. The Apr 5 B3 rerun UART was not saved. B3 canonical evidence relies on the server-side log (see below).

---

## Server Logs

| File | Covers | Entries | Status |
|---|---|---|---|
| `cloud_emulator/api/logs/enroll_log.jsonl` | All POST /enroll calls | 379+ | CANONICAL for B3 and Proposed |
| `cloud_emulator/api/logs/provision_log.jsonl` | All POST /provision calls | ~13 | CANONICAL for B2 token events (200s and 401s) |
| `gateway/logs/iot_gateway_relay_2026-04-05.log` | Pi relay events, Apr 5 | ~few lines | Historical |
| `gateway/logs/proposed_gateway_log.jsonl` | Pi proposed gateway events | ~20 entries | CANONICAL for Proposed Phase 1+2 sequence |

---

## Evidence Notes (data/raw/)

| File | Covers | Classification |
|---|---|---|
| `data/raw/b1_live_rerun_2026-04-05_evidence.md` | B1 canonical 5-run PASS; per-run values; source file verification | **Canonical** |
| `data/raw/b3_live_rerun_2026-04-05_evidence.md` | B3 canonical 5-run PASS; server log corroboration; UART missing note | **Canonical** |
| `data/raw/b2_replay_mitm_2026-04-06_evidence.md` | B2 replay attack scenario C; HTTP 200 → HTTP 401 confirmed | **Canonical** |
| `data/raw/proposed_p5_evidence_2026-04-07.md` | Proposed 5-run PASS pack; supplemental run; recovered run; pcap status; evidence classification table | **Canonical** (for 5-run pack) |
| `data/raw/proposed_gateway_recovered_pass_2026-04-07.md` | Single PASS run after gateway restart | Operational evidence only |
| `data/raw/m4_b1_via_pi_gateway_2026-04-05_evidence.md` | B1 via-Pi milestone: 5/5 HTTP 200 confirmed | Supplemental |
| `data/raw/m4_b3_via_pi_gateway_2026-04-05_evidence.md` | B3 via-Pi milestone: relay-side confirmed; client-side partial | Supplemental |

---

## Older Raw Logs (data/raw/)

These are from the Mar 4, 2026 session and are superseded by the Apr 5 live reruns:

| File | Session | Status |
|---|---|---|
| `data/raw/b1_uart_5runs.log` | Mar 4 2026 | Superseded by `capture/b1_serial_live.txt` |
| `data/raw/b1_uart_5runs_20260304_161053.log` | Mar 4 2026 | Duplicate; superseded |
| `data/raw/b3_uart_5runs.log` | Mar 4 2026 | Superseded by Apr 5 live run |
| `data/raw/b3_uart_enroll_20260304_170807.log` | Mar 4 2026 | 672 bytes; partial; superseded |
| `data/raw/b3_uart_enroll_20260304_171047.log` | Mar 4 2026 | 672 bytes; partial; superseded |
| `data/raw/b3_uart_enroll_20260304_171250.log` | Mar 4 2026 | 0 bytes; empty |
| `data/raw/b3_uart_enroll_20260304_190944.log` | Mar 4 2026 | Intermediate; superseded |
| `data/raw/b3_uart_enroll_20260304_191754.log` | Mar 4 2026 | Intermediate; superseded |
| `data/raw/b3_uart_enroll_final_20260304_193449.log` | Mar 4 2026 | Best Mar 4 capture; superseded by Apr 5 run |

---

## Processed Datasets (data/processed/)

| File | Rows | Covers | Status |
|---|---|---|---|
| `data/processed/final_results.csv` | 25 | B1 (sim 1–10) + B1 live (11–15) + B3 live (16–20) + Proposed (21–25) | **Primary canonical dataset** — use for all report tables |
| `data/processed/results.csv` | 20 | B1 live (1–5) + B3 live (6–10) + Proposed (11–20) | Secondary canonical; different schema |
| `data/processed/proposed_p5_runpack_2026-04-07.csv` | 5 | Proposed per-phase breakdown (auth/csr/enroll/total) | **Canonical for Proposed Method phase table** |
| `data/processed/final_results.csv.bak_20260407_proposed_integration` | — | Pre-integration backup | Stale; ignore |
| `data/processed/results.csv.bak_20260407_proposed_integration` | — | Pre-integration backup | Stale; ignore |

**B2 data is absent from all CSVs.** No B2 rows exist in any processed dataset.

---

## Packet Captures

| Location | Status |
|---|---|
| `capture/pcaps/` | **Empty** — only `.gitkeep`. No real pcap files collected. |

Figures 7.2 and 7.3 in `report_assets/ch7_visuals/` are programmatically rendered to show the *structure* of plaintext HTTP exchanges. They are not generated from real pcap files.

---

## Report Patches and Protocol Docs

| File | Purpose | Status |
|---|---|---|
| `docs/report_patch_b1_rerun_2026-04-05.md` | B1 canonical results section | Use as-is |
| `docs/report_patch_b3_rerun_2026-04-05.md` | B3 canonical results section | Use as-is |
| `docs/report_patch_proposed_p5_2026-04-07.md` | Proposed canonical results section | **Has known error: "~1254 ms" should be "1375.2 ms"** |
| `docs/protocol_lock_full_scope_2026-04-06.md` | Full protocol design specification | Use as-is |

---

## Missing Evidence (not collected)

| Missing Item | Why | Can it be collected without ESP32? |
|---|---|---|
| B3 canonical UART capture | UART session was not saved on Apr 5 | No — would require new B3 run |
| B2 clean 10/10 UART capture | 8 s fix applied but re-run pending | No — requires ESP32 reflash |
| Any real pcap from `capture/pcaps/` | No capture was validated/saved | Yes — loopback tcpdump for loopback traffic; real traffic requires hardware |
| B2 MITM scenarios A, B, D (passive sniff, modification, rogue server) | Not executed | Partial (A can be demonstrated with tcpdump) |
