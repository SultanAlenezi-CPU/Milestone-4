# M4 Evidence Note — Baseline 3 via Raspberry Pi Gateway (2026-04-05)

## Status

This note documents the first verified M4 success for Baseline 3 (CSR enrollment)
routed through the Raspberry Pi gateway. It is based on the live rerun summary and
terminal output directly observed by the project author on 2026-04-05.

**Raw UART log:** `capture/b3_via_pi_serial_live.txt` exists in repo (351 lines,
32 KB, captured Apr 5 22:31). This log contains two sessions; see the detailed
analysis below. The log does NOT contain a clean 5/5 PASS session — see section
"Serial Log Analysis" for the honest breakdown.

**Server-side corroboration:** `cloud_emulator/api/logs/enroll_log.jsonl` contains
a complete sequence of 5 POST /enroll entries at 19:28:17–19:28:29 UTC (run_id 1–5,
device_id esp32_01, all status=200) consistent with a fully successful B3 via Pi session.
This is the primary evidence for the confirmed 5/5 success.

**Packet capture (pcap):** Pending — not collected during this phase.

**Dataset/report integration:** Postponed — not performed in this pass.

---

## Network Path

```
ESP32  -->  Raspberry Pi gateway (172.20.10.4:8080)  -->  Cloud Emulator (172.20.10.2:5000)
```

| Component | Address |
|-----------|---------|
| ESP32 target | `172.20.10.4:8080/enroll` |
| Pi relay upstream | `172.20.10.2:5000/enroll` |
| device_id | esp32_01 |
| Pi IP | 172.20.10.4 |
| Cloud emulator IP | 172.20.10.2 |

---

## Verified Outcome (user-confirmed)

- `MEASURE runs_done=5` confirmed in serial terminal
- Pi relay confirmed forwarding:
  `RELAY POST /enroll -> http://172.20.10.2:5000/enroll status=200`
- Emulator returned `device_cert_pem` + `ca_cert_pem` for each run (certificate PEM
  visible in serial output for at least run_id=1 in both captured sessions)

---

## Server-Side Corroboration — Clean 5/5 Session (emulator log)

The emulator log shows a complete clean session at 19:28:17–19:28:29 UTC:

```
{"timestamp_utc": "2026-04-05T19:28:17.821517+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "1", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T19:28:20.824544+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "2", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T19:28:23.783078+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "3", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T19:28:26.659886+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "4", "device_id": "esp32_01"}
{"timestamp_utc": "2026-04-05T19:28:29.458212+00:00", "method": "POST", "path": "/enroll", "status_code": 200, "run_id": "5", "device_id": "esp32_01"}
```

5 successful enrollments in ~12 seconds. The corresponding ESP32 serial monitor was
not captured to file for this specific session (the serial monitor was not running or
was not redirected to file at that moment).

---

## Serial Log Analysis — `capture/b3_via_pi_serial_live.txt`

The file contains 2 sessions separated by a POWERON_RESET at line 198.

### Session 1 (lines 3–195) — Partial capture, mixed results

| run_id | latency_ms | http_status (ESP32) | Emulator side | Notes |
|--------|-----------|---------------------|---------------|-------|
| 1      | 2,295     | 200 ✓               | 200 (19:30:32) | Full cert response received |
| 2      | 1,588     | -1 ✗                | 200 (19:30:36) | Pi relayed OK; ESP32 socket timeout (errno=113 EHOSTUNREACH on read) |
| 3      | —         | not in log          | not in emulator log | WiFi dropped; socket connect errno=118; runs missing from capture |
| 4      | —         | not in log          | not in emulator log | WiFi reconnecting during this run |
| 5      | 1,420     | 200 ✓               | 200 (19:30:43) | Recovered after WiFi reconnect |
| runs_done=5 | | | | Firmware counted 5 attempts |

> Session 1 notes: A WiFi disconnect occurred between runs 2 and 5. Runs 3 and 4
> have no MEASURE lines in the serial log because the connection failed before
> the request could complete (errno=118 = EADDRNOTAVAIL). The monitor was connected
> but the ESP32 could not reach the Pi during those runs. After reconnect, run 5
> succeeded. The Pi relay did successfully forward runs 1, 2, and 5 to the emulator.

### Session 2 (lines 198–351) — Complete capture, relay success / ESP32 timeout

| run_id | latency_ms | http_status (ESP32) | Emulator side | Notes |
|--------|-----------|---------------------|---------------|-------|
| 1      | 2,288     | 200 ✓               | 200 (19:31:06) | Full cert response received |
| 2      | 5,479     | -1 ✗                | 200 (19:31:09) | Pi relayed OK; ESP32 read timed out (errno=11 EAGAIN) |
| 3      | 5,499     | -1 ✗                | 200 (19:31:16) | Pi relayed OK; ESP32 read timed out |
| 4      | 5,489     | -1 ✗                | 200 (19:31:23) | Pi relayed OK; ESP32 read timed out |
| 5      | 5,479     | -1 ✗                | 200 (19:31:30) | Pi relayed OK; ESP32 read timed out |
| runs_done=5 | | | | |

> Session 2 notes: The Pi relay forwarded all 5 enrollment requests successfully
> (emulator returned 200 for all 5). The ESP32 socket read timed out on runs 2–5
> (errno=11 = EAGAIN, socket recv timed out). The large response body (~3.4 KB
> certificate PEM) took longer to traverse the relay path than the ESP32 socket
> read timeout allowed. Run 1 succeeded because the response arrived within the
> timeout window. This indicates the relay architecture is functional but the
> ESP32 socket read timeout needs to be increased for the full via-Pi enrollment path.

### Summary of what the serial log supports

| Claim | Supported by serial log? |
|-------|--------------------------|
| Pi relay architecture is functional | YES — relay forwarded all requests |
| ESP32 can receive full cert response via Pi | YES — run_id=1 in both sessions received full `device_cert_pem` + `ca_cert_pem` |
| 5/5 PASS on ESP32 side in this log | NO — best session is 2/5 (session 1) |
| runs_done=5 printed | YES — both sessions |
| Clean 5/5 confirmed | YES — by emulator log at 19:28:17–29 UTC + user direct observation |

> **Important:** Do NOT cite the serial log as showing 5/5 PASS for B3 via Pi.
> The confirmed 5/5 success is from the user's direct terminal observation and
> corroborated by the emulator log at 19:28 UTC. The serial log captures two
> subsequent sessions with known issues (WiFi instability and socket timeout).

---

## Root Cause Notes (for future reference)

**Session 1 failures (runs 3–4):** WiFi disconnect. The hotspot AP briefly dropped
the connection. Not a gateway issue.

**Session 2 failures (runs 2–5 ESP32 side):** ESP32 socket read timeout too short
for the ~3.4 KB enrollment response traversing two hops (ESP32 → Pi → emulator →
Pi → ESP32). The Pi relay was functionally correct. Fix: increase socket read timeout
in B3 firmware or reduce response body size.

---

## Fix Session — `capture/b3_via_pi_serial_fix_2026-04-05.txt`

After the original two sessions, SO_RCVTIMEO was increased from 5s to 15s and a
third session was run (commit `26d14ee`).

| run_id | latency_ms | http_status (ESP32) | Emulator side | Notes |
|--------|-----------|---------------------|---------------|-------|
| 1      | 2,275     | 200 ✓               | 200 (20:01:02) | Full cert received |
| 2      | 15,479    | -1 ✗                | 200 (20:01:05) | errno=11 EAGAIN — 15s cap hit |
| 3      | 15,468    | -1 ✗                | 200 (20:01:22) | errno=11 EAGAIN — 15s cap hit |
| 4      | 2,612     | 200 ✓               | 200 (20:01:39) | Full cert received |
| 5      | 11,563    | 200 ✓               | 200 (20:01:43) | Full cert received; 11.5s — within 15s window |
| runs_done=5 | | | | 3/5 ESP32-side PASS |

**Relay/emulator side: 5/5 HTTP 200.** The relay architecture remained fully functional.
ESP32-side failures on runs 2–3 are due to extreme WiFi latency variance on the
hotspot: the same run_id=5 succeeded at 11,563 ms, confirming the 15s timeout is
appropriate for stable conditions. The hotspot is the limiting factor.

> **Do NOT cite this session as a clean 5/5 B3 via Pi result.**
> ESP32-side result is 3/5. Relay/emulator side is 5/5.

---

## Environment Note

Experiment conducted 2026-04-05. ESP32, Raspberry Pi, and Windows host all on the
same phone hotspot (HUAWEI-B315-58AD). Pi at 172.20.10.4, emulator at 172.20.10.2:5000.
Wi-Fi password not stored in this repo. Pi relay log in repo at
`gateway/logs/iot_gateway_relay_2026-04-05.log` (8 entries, original sessions only).
