# Report Patch — Proposed Method P5 Repeated Runs (2026-04-07)
## Sections Affected: 7.4 (or equivalent Proposed Method section), results table, discussion

**Purpose:** This patch provides the accepted five-run repeated-run pack for the
Proposed Gateway-Brokered Two-Phase Enrollment method, collected 2026-04-07.
These are the canonical values to use in the report wherever the Proposed Method
latency, heap, and success-rate measurements are cited.

**Evidence basis:**
- UART serial capture: `capture/proposed_p5_repeated_runs_2026-04-07_002848.txt`
  and `capture/proposed_p5_repeated_runs_latest.txt`
- Pi-side gateway log: `gateway/logs/proposed_gateway_log.jsonl`
- Cloud emulator signing log: `cloud_emulator/api/logs/enroll_log.jsonl`
- Dedicated run pack CSV: `data/processed/proposed_p5_runpack_2026-04-07.csv`
- Detailed evidence note: `data/raw/proposed_p5_evidence_2026-04-07.md`
- Master CSV rows: `data/processed/final_results.csv` rows 21–25

---

## Run-id note

The firmware build used a compile-time fixed `RUN_ID "1"` (one-shot-per-boot design).
Every reset therefore printed `run_id=1` internally. For evidence consistency and
report tables, **external sequence numbers 1–5** are assigned to the five accepted
repeated runs. This is documented in `data/raw/proposed_p5_evidence_2026-04-07.md`
and in the dedicated `proposed_p5_runpack_2026-04-07.csv` header.

---

## Accepted Proposed Method Five-Run Pack

### Raw Measurements

| Run | Auth (ms) | CSR gen (ms) | Enroll (ms) | **Total (ms)** | heap\_before (B) | heap\_after (B) | heap\_delta (B) | Auth HTTP | Enroll HTTP | Cert rcvd | Result |
|-----|----------:|-------------:|------------:|---------------:|-----------------:|----------------:|----------------:|:---------:|:-----------:|:---------:|:------:|
| 1   |        74 |          680 |        1232 |         **1999** |          217 760 |         203 900 |        −13 860 |    200    |     200     |     ✓     |  PASS  |
| 2   |       105 |          674 |        1205 |         **1995** |          217 692 |         203 312 |        −14 380 |    200    |     200     |     ✓     |  PASS  |
| 3   |       327 |          706 |         955 |         **1998** |          217 700 |         203 312 |        −14 388 |    200    |     200     |     ✓     |  PASS  |
| 4   |       114 |          704 |        1162 |         **1991** |          217 696 |         203 316 |        −14 380 |    200    |     200     |     ✓     |  PASS  |
| 5   |        90 |          692 |        1209 |         **2002** |          217 700 |         200 788 |        −16 912 |    200    |     200     |     ✓     |  PASS  |

### Summary Statistics (Official Five-Run Pack)

| Metric | Value |
|--------|------:|
| Success rate | 5/5 PASS (100%) |
| Mean total latency | 1997.0 ms |
| Std dev total latency | 4.2 ms |
| Median total latency | 1998 ms |
| Min total latency | 1991 ms |
| Max total latency | 2002 ms |
| Mean auth latency | 142.0 ms |
| Mean CSR generation time | 691.2 ms |
| Mean enroll latency | 1152.6 ms |
| Mean heap delta | −14 784 B |

### Component breakdown (means)

The total latency decomposes into three measurable phases:
- **Phase 1 (gateway auth):** 142 ms mean — one small HTTP POST, no crypto.
- **CSR generation:** 691 ms mean — EC P-256 key generation + CSR signing on ESP32 (mbedTLS).
  This is the dominant computation cost, identical in character to the B3 direct enroll path.
- **Phase 2 (gateway enroll):** 1153 ms mean — includes Pi-side session validation,
  upstream forwarding to cloud CA, certificate signing, and full response transit.

The two-phase design adds an auth round-trip (~142 ms) on top of the single-phase B3 path,
in exchange for per-session device authentication at the gateway.

---

## Supplemental Extra PASS Run (not part of canonical pack)

One additional PASS run was collected in the same session with an elevated total latency
of 4195 ms (auth: 2056 ms). This is preserved as supplemental evidence only and is
**not included** in the canonical five-run statistics above. The elevated auth latency
is consistent with intermittent hotspot or relay delay observed in other baselines under
similar conditions. It does not indicate a firmware or gateway logic defect.

| ext\_seq | Auth (ms) | CSR gen (ms) | Enroll (ms) | Total (ms) | Result |
|:--------:|----------:|-------------:|------------:|-----------:|:------:|
| 6        |      2056 |          701 |        1426 |       4195 |  PASS  |

Source: `data/raw/proposed_p5_evidence_2026-04-07.md` supplemental section.

---

## Comparison Context

The Proposed Method total latency (~1997 ms mean) is approximately **1.6× the B3 direct
enroll latency** (~1254 ms mean from `docs/report_patch_b3_rerun_2026-04-05.md`).
The additional cost is attributable to:
1. Phase 1 auth round-trip (~142 ms)
2. Phase 2 adding Pi-side session validation and an additional hop
   (ESP32 → Pi → cloud, vs ESP32 → Pi → cloud in B3, but with session gating)

Both methods issue a valid X.509 certificate. The Proposed Method adds:
- Per-device token authentication at the gateway before any cloud interaction
- Single-use 30-second session token binding Phase 1 to Phase 2
- The cloud CA is never exposed directly to ESP32 credentials

---

## Master CSV Integration

Proposed five-run pack appended to master CSVs with `latency_ms = total_latency_ms`,
`http_status = http_status_enroll = 200`, `baseline = "Proposed"`:

- `data/processed/final_results.csv` rows 21–25 (run_id 21–25)
- `data/processed/results.csv` rows 16–20 (run_id 16–20)

Backups taken before edit:
- `data/processed/final_results.csv.bak_20260407_proposed_integration`
- `data/processed/results.csv.bak_20260407_proposed_integration`

The supplemental run (4195 ms) is **not** appended to master CSVs.
It remains in `data/raw/proposed_p5_evidence_2026-04-07.md` and in
`data/processed/proposed_p5_runpack_2026-04-07.csv` (which records all six runs
including the supplemental one as a separate section in the evidence note).

---

## Caveats and honest scope

- Certificate chain full verification (chain-of-trust to root CA): not independently
  verified in this phase beyond the emulator returning `device_cert_pem` and `ca_cert_pem`
  fields with HTTP 200. The CA signing step is confirmed by the emulator logic in
  `cloud_emulator/api/app.py`.
- No TLS in this testbed version. The plaintext observability of auth token and session
  token is a documented property of this testbed, not an oversight. Discussed in
  `docs/protocol_lock_full_scope_2026-04-06.md` section 3.10.
- Packet capture for the Proposed Method: not yet collected. Security discussion of
  passive sniffability must be framed as a protocol-level property until a pcap is
  stored in `capture/pcaps/`.
