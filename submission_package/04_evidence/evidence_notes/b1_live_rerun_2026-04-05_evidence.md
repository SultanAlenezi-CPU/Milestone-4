# Baseline 1 Live Rerun Evidence — 2026-04-05

## Status

This note documents the accepted controlled rerun of Baseline 1 (plain HTTP health-check)
conducted on 2026-04-05. It is based on the live rerun summary provided by the project author
and confirmed against the raw UART serial capture saved at:

  `capture/b1_serial_live.txt`

That file contains the full 272-line UART session including bootloader output, Wi-Fi association,
and all five MEASURE lines. It is untracked in git at the time of this evidence note and should
be committed alongside this file.

A packet capture (pcap/screenshot) for this specific rerun is **pending** and was not collected
during this phase. Phase A/C/D focused on live rerun evidence and dataset reconciliation only.
Plaintext HTTP visibility is addressed in the report patch on a conceptual basis; it must not
be cited as "confirmed by pcap" for this specific rerun until a pcap is stored in
`capture/pcaps/`.

---

## Run Configuration

| Item | Value |
|------|-------|
| Date | 2026-04-05 |
| Baseline | B1 — plain HTTP health-check (no TLS, no auth) |
| Firmware | `esp32_firmware/baseline1_http` built with ESP-IDF v5.5.3 |
| Target endpoint | `http://172.20.10.2:5000/health` |
| Cloud emulator | Flask/Werkzeug 3.1.6, Python 3.12.3, `cloud_emulator/api/app.py` |
| SSID used by ESP32 | HUAWEI-B315-58AD |
| Network context | Phone hotspot / local network path (2026-04-05) |
| Raw UART log | `capture/b1_serial_live.txt` (existing, verified match) |
| Pcap evidence | Not collected in this phase — pending |

> **Wi-Fi password not stored** in this repo per project security policy.

---

## Accepted Run Data (5/5 PASS)

All five runs reached `172.20.10.2:5000/health` and received HTTP 200 OK
with `{"status":"ok"}`.

| run_id | latency_ms | heap_before | heap_after | heap_delta | http_status | result |
|--------|-----------|-------------|------------|------------|-------------|--------|
| 1      | 965       | 221,936     | 225,776    | +3,840     | 200         | PASS   |
| 2      | 1,765     | 226,208     | 225,772    | −436       | 200         | PASS   |
| 3      | 1,325     | 226,208     | 225,788    | −420       | 200         | PASS   |
| 4      | 1,281     | 226,208     | 225,592    | −616       | 200         | PASS   |
| 5      | 2,980     | 226,188     | 225,592    | −596       | 200         | PASS   |

Source MEASURE lines verified in `capture/b1_serial_live.txt` — all five match exactly.

---

## Summary Statistics (Latency)

| Statistic | Value |
|-----------|-------|
| Mean      | 1,663.2 ms |
| Median    | 1,325 ms |
| Std Dev (sample) | 789.4 ms |
| Min       | 965 ms |
| Max       | 2,980 ms |
| Success rate | 5/5 (100%) |

> **Notes on spread:** Run 1 (965 ms) is an outlier low — likely benefits from a warm DNS
> cache immediately post-WiFi association. Run 5 (2,980 ms) is the high outlier, consistent
> with occasional DNS re-resolution or brief RF contention on a shared hotspot.
> Runs 2–4 cluster between 1,281–1,765 ms and represent the typical steady-state range.
> The large sample standard deviation (789.4 ms) is primarily driven by these two outliers
> and is expected for a 5-run sample over a shared wireless medium.

---

## Dataset Reconciliation Note

The processed CSVs (`data/processed/results.csv`, `data/processed/final_results.csv`) store
only `heap_delta`, not `heap_before`/`heap_after`. Full per-cycle heap values are preserved
only in the raw UART log (`capture/b1_serial_live.txt`). The CSV rows appended in Phase C
use the `heap_delta` column consistent with the existing schema.

The earlier B1 rows in `final_results.csv` (run_id 1–5, latencies 210–220 ms) are from a
prior simulation/dry-run and are preserved as historical rows. The 2026-04-05 live rerun
rows are appended as run_id 11–15 with notes clearly identifying them.

---

## Environment Note

This rerun was conducted on 2026-04-05 using a phone hotspot (SSID: HUAWEI-B315-58AD) as
the local network path between the ESP32 and the cloud emulator running on the Windows host
at 172.20.10.2:5000. This is not a dedicated lab LAN — latency values reflect a shared
wireless medium and should be interpreted accordingly. The network context is noted here
for reproducibility; future reruns under a stable wired LAN may yield lower and less variable
latency.
