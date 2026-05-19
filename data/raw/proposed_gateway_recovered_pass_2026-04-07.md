# Proposed Gateway Recovered PASS Note — 2026-04-07

## Context
This note preserves a recovered successful support run after the Pi gateway had temporarily stopped listening on port 8090 and was restarted.

## Latest recovered PASS
- internal firmware run_id: 1
- auth_latency_ms: 115
- csr_gen_ms: 704
- enroll_latency_ms: 1133
- total_latency_ms: 1963
- heap_before: 217584
- heap_after: 202240
- heap_delta: -15344
- http_status_auth: 200
- http_status_enroll: 200
- cert_received: 1
- result: PASS

## Scope note
This run is supporting evidence only.
It does not replace the canonical proposed P5 five-run pack already frozen in:
- data/processed/proposed_p5_runpack_2026-04-07.csv
- data/raw/proposed_p5_evidence_2026-04-07.md

## Operational note
The successful rerun indicates that the protocol flow still works after gateway recovery.
The main operational instability observed in this phase is gateway process persistence on the Pi, not a confirmed firmware or protocol regression.
