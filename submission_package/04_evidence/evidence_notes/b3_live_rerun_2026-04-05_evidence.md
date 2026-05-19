# Baseline 3 Live Rerun Evidence — 2026-04-05

## Status

This note documents the accepted controlled rerun of Baseline 3 (cloud PKI certificate
enrollment over plain HTTP) conducted on 2026-04-05. It is based on the live rerun summary
provided by the project author.

**Raw UART log for this rerun:** Not preserved in the repo. No `capture/b3_serial_live.txt`
or equivalent file was saved during this session. The closest prior UART log is
`data/raw/b3_uart_5runs.log` (Mar 4, 2026), which contains different run values and is
from a separate earlier session.

**Corroborating server-side evidence:** The cloud emulator's request log at
`cloud_emulator/api/logs/enroll_log.jsonl` contains 5 POST /enroll entries on 2026-04-05
between 18:51:10–18:51:21 UTC (run_id 1–5, device_id esp32_01, all HTTP 200). This
confirms the server received and signed 5 enrollment requests during this session. This
file is untracked in git and should be committed alongside this evidence note.

**Packet capture (pcap/screenshot):** Pending — not collected during this phase.
Phase A/C/D focused on live rerun evidence and dataset reconciliation only. Do not cite
"plaintext HTTP confirmed by pcap" for this rerun until a pcap is stored in
`capture/pcaps/`.

---

## Run Configuration

| Item | Value |
|------|-------|
| Date | 2026-04-05 |
| Baseline | B3 — plain HTTP CSR enrollment (no TLS, cloud PKI cert issuance) |
| Firmware | `esp32_firmware/baseline3_enroll` built with ESP-IDF v5.5.3 |
| Target endpoint | `http://172.20.10.2:5000/enroll` |
| Cloud emulator | Flask/Werkzeug, `cloud_emulator/api/app.py`, signing with local CA |
| SSID used by ESP32 | HUAWEI-B315-58AD |
| Network context | Phone hotspot / local network path (2026-04-05) |
| device_id | esp32_01 |
| Raw UART log | Not preserved for this rerun |
| Server-side log | `cloud_emulator/api/logs/enroll_log.jsonl` (5 /enroll entries, 18:51 UTC) |
| Pcap evidence | Not collected in this phase — pending |

> **Wi-Fi password not stored** in this repo per project security policy.

---

## Accepted Run Data (5/5 PASS)

All five runs reached `172.20.10.2:5000/enroll` and received HTTP 200 OK.
The emulator response included `device_cert_pem` and `ca_cert_pem` fields for each run,
confirming the CA signed a device certificate for each enrollment request.

| run_id | latency_ms | heap_before | heap_after | heap_delta | http_status | result |
|--------|-----------|-------------|------------|------------|-------------|--------|
| 1      | 1,782     | 200,908     | 204,656    | +3,748     | 200         | PASS   |
| 2      | 1,142     | 205,088     | 204,660    | −428       | 200         | PASS   |
| 3      | 1,554     | 205,088     | 204,672    | −416       | 200         | PASS   |
| 4      | 1,147     | 205,088     | 204,672    | −416       | 200         | PASS   |
| 5      | 1,251     | 205,088     | 204,672    | −416       | 200         | PASS   |

Source: accepted live rerun summary provided by project author, corroborated by
`cloud_emulator/api/logs/enroll_log.jsonl` (server-side 5/5 HTTP 200 on 2026-04-05).

---

## Summary Statistics (Latency)

| Statistic            | Value      |
|----------------------|------------|
| Mean                 | 1,375.2 ms |
| Median               | 1,251 ms   |
| Std Dev (sample, n=5)| 282.5 ms   |
| Min                  | 1,142 ms   |
| Max                  | 1,782 ms   |
| Success rate         | 5/5 (100%) |

> **Notes on distribution:** Run 1 (1,782 ms) is the high outlier — consistent with
> initial DNS resolution + TCP setup + CSR generation overhead on first cycle. Runs 2–5
> cluster between 1,142–1,554 ms. The standard deviation (282.5 ms, ~21% of mean) is
> moderate and primarily driven by the run 1 outlier; steady-state spread across runs 2–5
> is tighter (1,142–1,554 ms range).

---

## Heap Memory Notes

| run_id | heap_delta |
|--------|-----------|
| 1      | +3,748 B  |
| 2–5    | −416 to −428 B |

Run 1 shows a positive delta (+3,748 B) due to Wi-Fi/TCP/TLS stack initialisation
completing during the first request cycle. Runs 2–5 show a small consistent negative
delta (~−416 B per cycle), indicating a minor allocation not freed within the measurement
window. At ~205 KB available heap and −416 B per cycle, this is not a meaningful leak
concern at 5 runs.

---

## Emulator Log Corroboration (server-side, 2026-04-05)

From `cloud_emulator/api/logs/enroll_log.jsonl`:

```
{"timestamp_utc": "2026-04-05T18:51:10.586280+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "1", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T18:51:13.395390+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "2", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T18:51:16.423524+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "3", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T18:51:19.128039+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "4", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T18:51:21.792342+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "5", "device_id": "esp32_01"}
```

5 successful enrollments in ~11 seconds wall-clock time.

---

## Dataset Reconciliation Note

The processed CSVs store only `heap_delta` (not `heap_before`/`heap_after`). Full per-cycle
heap values are available only via the accepted rerun summary above and this evidence note.
New CSV rows appended in Phase C use heap_delta consistent with the existing schema.

Earlier B3 rows in `results.csv` (run_id 1–5, Mar 4 session, latencies 1075–1654 ms) and
in `final_results.csv` (run_id 6–10) are preserved as historical rows. The 2026-04-05
live rerun rows are appended with notes clearly identifying them.

---

## Environment Note

This rerun was conducted on 2026-04-05 using a phone hotspot (SSID: HUAWEI-B315-58AD) as
the local network path between the ESP32 and the cloud emulator running on the Windows host
at 172.20.10.2:5000. The emulator used the local CA (`cloud_emulator/pki/ca.crt` /
`ca.key`) to sign device CSRs. Latency values reflect a shared wireless medium; future
reruns under a stable wired LAN may yield lower and less variable latency. Network context
is noted here for reproducibility.
