# M4 Evidence Note — Baseline 1 via Raspberry Pi Gateway (2026-04-05)

## Status

This note documents the first verified M4 success for Baseline 1 routed through the
Raspberry Pi gateway. It is based on the live rerun summary and terminal output
directly observed by the project author on 2026-04-05.

**Full raw UART log for B1 via Pi:** Not preserved in repo. No
`capture/b1_via_pi_serial_live.txt` file was saved during this session.

**Server-side corroboration:** `cloud_emulator/api/logs/enroll_log.jsonl` contains
a cluster of 5 consecutive GET /health responses at 19:22:40–19:22:48 UTC on 2026-04-05,
consistent with a 5-run B1 session relayed through the Pi.

**Packet capture (pcap):** Pending — not collected during this phase.

**Dataset/report integration:** Postponed — not performed in this pass.

---

## Network Path

```
ESP32  -->  Raspberry Pi gateway (172.20.10.4:8080)  -->  Cloud Emulator (172.20.10.2:5000)
```

| Component | Address |
|-----------|---------|
| ESP32 target | `172.20.10.4:8080/health` |
| Pi relay upstream | `172.20.10.2:5000/health` |
| Pi IP (observed) | 172.20.10.4 |
| Cloud emulator IP | 172.20.10.2 |

---

## Verified Outcome

- HTTP/1.0 200 OK returned to ESP32 from Pi relay
- Response body: `{"status":"ok"}`
- `MEASURE runs_done=5` confirmed in serial terminal
- Pi relay confirmed forwarding:
  `RELAY GET /health -> http://172.20.10.2:5000/health status=200`

---

## User-Observed Sample Run

The following MEASURE line was directly observed in the serial terminal:

```
MEASURE run_id=5 heap_before=226196 heap_after=225776 heap_delta=-420
        start_ms=30982 end_ms=31069 latency_ms=86 http_status=200
```

> **Latency note:** 86 ms is notably lower than the direct B1 runs (~965–2,980 ms).
> This reflects the ESP32 → Pi LAN hop (local network, no DNS resolution overhead
> per run after first cycle) rather than ESP32 → Windows host over hotspot.
> This is expected and confirms the Pi relay is on the same local network segment.

---

## Server-Side Corroboration (emulator log)

From `cloud_emulator/api/logs/enroll_log.jsonl`, a cluster of 5 consecutive
GET /health entries at 19:22:40–19:22:48 UTC on 2026-04-05:

```
{"timestamp_utc": "2026-04-05T19:22:40.246321+00:00", "method": "GET", "path": "/health", "status_code": 200, ...}
{"timestamp_utc": "2026-04-05T19:22:41.990567+00:00", "method": "GET", "path": "/health", "status_code": 200, ...}
{"timestamp_utc": "2026-04-05T19:22:43.821516+00:00", "method": "GET", "path": "/health", "status_code": 200, ...}
{"timestamp_utc": "2026-04-05T19:22:45.810136+00:00", "method": "GET", "path": "/health", "status_code": 200, ...}
{"timestamp_utc": "2026-04-05T19:22:48.454332+00:00", "method": "GET", "path": "/health", "status_code": 200, ...}
```

5 requests in ~8 seconds, consistent with 5-run B1 firmware behavior. All HTTP 200.

---

## Gateway Implementation Note

The Pi relay script ran on the Raspberry Pi outside the repo at the time of this
experiment. See `gateway/pi/README_m4_gateway_first_success_2026-04-05.md` for
details of the relay behavior and expected external paths.

---

## Environment Note

Experiment conducted 2026-04-05. ESP32 connected to phone hotspot (HUAWEI-B315-58AD).
Raspberry Pi on the same hotspot network at 172.20.10.4. Cloud emulator on Windows host
at 172.20.10.2:5000. Wi-Fi password not stored in this repo.
