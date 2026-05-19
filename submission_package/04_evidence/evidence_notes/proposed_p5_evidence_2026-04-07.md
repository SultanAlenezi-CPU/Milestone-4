# Proposed Method P5 Evidence Note — 2026-04-07

## Status
This note freezes the official five-run repeated PASS pack for the proposed gateway-assisted onboarding method collected on 2026-04-07.

## Important note on run numbering
The firmware log printed `run_id=1` on every reset because the internal firmware run identifier is compile-time fixed in the current build.
For evidence and later CSV integration, this note assigns **external sequence numbers 1–5** to the official repeated-run pack.

## Official five-run pack
| ext_seq | fw_run_id | auth_ms | csr_ms | enroll_ms | total_ms | heap_before | heap_after | heap_delta | auth_http | enroll_http | cert_received | result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 1 | 74 | 680 | 1232 | 1999 | 217760 | 203900 | -13860 | 200 | 200 | 1 | PASS |
| 2 | 1 | 105 | 674 | 1205 | 1995 | 217692 | 203312 | -14380 | 200 | 200 | 1 | PASS |
| 3 | 1 | 327 | 706 | 955 | 1998 | 217700 | 203312 | -14388 | 200 | 200 | 1 | PASS |
| 4 | 1 | 114 | 704 | 1162 | 1991 | 217696 | 203316 | -14380 | 200 | 200 | 1 | PASS |
| 5 | 1 | 90 | 692 | 1209 | 2002 | 217700 | 200788 | -16912 | 200 | 200 | 1 | PASS |


## Summary statistics for official five-run pack
- Mean total latency: 1997.0 ms
- Sample standard deviation (total latency): 4.18 ms
- Median total latency: 1998.0 ms
- Min total latency: 1991 ms
- Max total latency: 2002 ms
- Success rate: 5/5 PASS

## Component means
- Mean auth latency: 142.0 ms
- Mean CSR generation time: 691.2 ms
- Mean enroll latency: 1152.6 ms

## Supplemental extra PASS run
This extra PASS run is preserved as supplemental evidence and is **not** part of the canonical five-run repeated pack.

| ext_seq | fw_run_id | auth_ms | csr_ms | enroll_ms | total_ms | heap_before | heap_after | heap_delta | auth_http | enroll_http | cert_received | result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 6 | 1 | 2056 | 701 | 1426 | 4195 | 217692 | 203320 | -14372 | 200 | 200 | 1 | PASS |


## Environment note
- Method: proposed gateway-assisted two-phase onboarding
- ESP32 target: Pi gateway at 172.20.10.4:8090
- Pi upstream host during successful runs: http://172.20.10.2:5000
- Cloud emulator endpoint reached through gateway enroll forwarding
- Result for official pack: 5/5 PASS

## Integration note
This phase creates a dedicated proposed-method run pack CSV and evidence note only.
Master consolidated CSV integration should be done in a separate controlled step after inspecting the target schema.

---

## Recovered support run (not part of canonical pack)

After the P5 session the Pi gateway process stopped (port 8090 no longer listening).
The gateway was restarted and one additional PASS run was collected as a liveness check.
This run is **supporting operational evidence only** and is **not part of the canonical five-run pack** and is **not included in master CSVs**.

| run_type | auth_ms | csr_ms | enroll_ms | total_ms | heap_before | heap_after | heap_delta | auth_http | enroll_http | cert_received | result |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| recovered_support | 115 | 704 | 1133 | 1963 | 217584 | 202240 | -15344 | 200 | 200 | 1 | PASS |

Source: `data/raw/proposed_gateway_recovered_pass_2026-04-07.md`

**Operational interpretation:** The successful rerun after gateway restart confirms the protocol flow is intact. The instability observed in this phase is gateway *process persistence* on the Pi (the service must be manually restarted after reboot or crash), not a firmware or protocol regression.

---

## Packet capture status

A Windows-side Wireshark capture was taken during the P5 session. Its status is:

- **Provisional artifact only.** The capture has not been validated against the canonical five-run timestamps.
- It is **not cited as canonical pcap evidence** in any report section.
- Until a capture is stored in `capture/pcaps/` and cross-referenced to the five-run ext_seq timestamps, all security discussion of passive sniffability must be framed as a protocol-level property of the no-TLS testbed, not as empirically demonstrated pcap evidence.
- See `docs/protocol_lock_full_scope_2026-04-06.md` section 3.10 for the documented no-TLS scope note.

---

## Evidence classification summary

| Item | Status | In canonical pack | In master CSVs |
|:---|:---|:---:|:---:|
| Five-run pack (ext_seq 1–5) | Canonical | Yes | Yes (final_results rows 21–25, results rows 16–20) |
| Supplemental extra PASS (ext_seq 6, 4195 ms) | Supplemental evidence | No | No |
| Recovered support PASS (post-restart) | Operational evidence | No | No |
| Windows-side pcap artifact | Provisional, unvalidated | No | No |
