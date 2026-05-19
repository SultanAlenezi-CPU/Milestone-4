# M4 Checkpoint — First Gateway Success (2026-04-05)

## Status

**FROZEN as of 2026-04-05. No further experiments in this pass.**

M4 is closed as a "first gateway success" checkpoint. The Raspberry Pi relay
architecture is verified functional. This is not a full clean statistical dataset
and is not claimed as such.

---

## What Succeeded

### Baseline 1 via Pi Gateway — Clean Success

- Path: ESP32 → 172.20.10.4:8080/health → 172.20.10.2:5000/health
- Outcome: 5/5 HTTP 200, runs_done=5 confirmed in serial terminal
- Sample run observed: run_id=5 latency_ms=86 http_status=200
- Pi relay confirmed: `RELAY GET /health -> http://172.20.10.2:5000/health status=200`
- Server-side corroboration: 5 GET /health at 19:22:40–48 UTC in enroll_log.jsonl
- UART log NOT preserved for this session (serial monitor was not redirected to file)
- Evidence note: `data/raw/m4_b1_via_pi_gateway_2026-04-05_evidence.md`

### Baseline 3 via Pi Gateway — Functional Success (relay/emulator level)

- Path: ESP32 → 172.20.10.4:8080/enroll → 172.20.10.2:5000/enroll
- The Pi relay architecture is fully functional: all enrollment requests in all
  recorded sessions were forwarded successfully and the emulator returned HTTP 200.
- Pi relay confirmed: `RELAY POST /enroll -> http://172.20.10.2:5000/enroll status=200`
- CA-signed certificate (`device_cert_pem` + `ca_cert_pem`) returned and received
  by ESP32 on run_id=1 in every recorded session.
- Clean 5/5 emulator-side session at 19:28:17–29 UTC (user-observed, corroborated
  by enroll_log.jsonl). The corresponding ESP32 serial monitor was not captured.
- Evidence note: `data/raw/m4_b3_via_pi_gateway_2026-04-05_evidence.md`

---

## What Did Not Become Clean Evidence

### B3 via Pi — No clean serial-side 5/5 run

Three B3 via Pi serial sessions were captured:

| Session | File | ESP32-side result | Relay-side result |
|---------|------|-------------------|-------------------|
| Live session 1 | `capture/b3_via_pi_serial_live.txt` lines 3–195 | 2/5 PASS (WiFi drop mid-session) | Partial (3/5 forwarded) |
| Live session 2 | `capture/b3_via_pi_serial_live.txt` lines 198–351 | 1/5 PASS (SO_RCVTIMEO=5s too short) | 5/5 forwarded |
| Fix session | `capture/b3_via_pi_serial_fix_2026-04-05.txt` | 3/5 PASS (SO_RCVTIMEO=15s, hotspot instability) | 5/5 forwarded |

**Root cause of serial-side failures:**

- Live session 1: WiFi instability (hotspot AP dropped ESP32 connection, errno=113
  EHOSTUNREACH and errno=118 EADDRNOTAVAIL). Not a firmware or relay issue.

- Live session 2: SO_RCVTIMEO=5s too short for the ~3.4KB enrollment response
  over the two-hop relay path. The relay was fully functional; the ESP32 socket
  read timed out (errno=11 EAGAIN) before receiving the response.

- Fix session: SO_RCVTIMEO increased to 15s. Improved result (3/5 vs 1/5) but
  still not clean. Runs 2 and 3 timed out at 15s due to extreme WiFi latency
  variance on the hotspot (the same run_id=5 succeeded at 11,563 ms, confirming
  the 15s window is appropriate for stable conditions). The hotspot is the
  limiting factor, not the firmware or the relay.

**Commit note:** Commit `26d14ee` is titled "confirm clean 5-run relay session".
The "clean 5-run" refers to the relay/emulator side (5/5 HTTP 200 at 20:01 UTC),
which is accurate. The ESP32 serial side was 3/5. This distinction is documented
here and in the B3 evidence note.

---

## Exact Scope of This M4 Claim

> **"First gateway success"**

This claim means:
- The Raspberry Pi relay architecture is operational.
- Enrollment requests are successfully relayed end-to-end (ESP32 → Pi → emulator → Pi → ESP32).
- CA-signed certificates are returned to the ESP32.
- The relay path adds latency relative to the direct path, as expected.

This claim does NOT mean:
- A clean 5/5 serial-side ESP32 PASS session on the via-Pi path has been achieved.
- The via-Pi latency distribution has been characterized statistically.
- The gateway path is production-ready or stable under current hotspot conditions.

---

## Firmware State at Checkpoint

`esp32_firmware/baseline3_enroll/main/http_request_example_main.c` line 259:

```c
struct timeval receiving_timeout = { .tv_sec = 15, .tv_usec = 0 };
```

Changed from 5s (M3 baseline) to 15s during M4 timeout fix experiment (commit
`26d14ee`). The 15s value is more appropriate for the two-hop relay path than the
original 5s, though it is not sufficient under poor hotspot conditions. This is
the current committed state. Not reverted — the 15s value is correct for the
relay path under stable network conditions.

---

## Explicitly Postponed Items

| Item | Status |
|------|--------|
| Packet capture (pcap) — B1 via Pi | Postponed |
| Packet capture (pcap) — B3 via Pi | Postponed |
| Dataset integration (results.csv, final_results.csv) | Postponed |
| Report figure regeneration | Postponed |
| Report section integration (.docx patches) | Postponed |
| Clean 5/5 B3 via Pi serial session | Postponed — requires stable network |

---

## Recommended Condition for Future Retry

To obtain a clean 5/5 serial-side B3 via Pi session:

1. **Use a more stable network.** Replace the phone hotspot with a router-backed
   WiFi network, or connect the Pi to the same LAN as the Windows host via
   Ethernet. The phone hotspot (HUAWEI-B315-58AD) introduces large, unpredictable
   RF latency that causes SO_RCVTIMEO to fire even with a 15s window.

2. **Capture the serial monitor to file from run 1.** Pipe `idf.py monitor` output
   to a file (e.g., `tee capture/b3_via_pi_stable_YYYY-MM-DD.txt`) before starting.

3. **Verify relay is up** before flashing: confirm Pi relay is listening at
   `172.20.10.4:8080` and emulator is running at `172.20.10.2:5000`.

4. **No firmware changes needed** before retry — the 15s SO_RCVTIMEO is
   appropriate for a stable relay path.

---

## Files in Repo for This Checkpoint

| File | Description |
|------|-------------|
| `capture/b3_via_pi_serial_live.txt` | 351 lines, 2 sessions, original live capture |
| `capture/b3_via_pi_serial_fix_2026-04-05.txt` | 1 session, fix experiment (3/5 ESP32, 5/5 relay) |
| `data/raw/m4_b1_via_pi_gateway_2026-04-05_evidence.md` | B1 via Pi evidence note |
| `data/raw/m4_b3_via_pi_gateway_2026-04-05_evidence.md` | B3 via Pi evidence note |
| `gateway/pi/iot_gateway_relay.py` | Pi relay script |
| `gateway/pi/README_m4_gateway_first_success_2026-04-05.md` | Relay topology and next steps |
| `gateway/logs/iot_gateway_relay_2026-04-05.log` | Pi relay log (8 entries, original sessions) |
| `cloud_emulator/api/logs/enroll_log.jsonl` | Server-side enrollment log with all sessions |

---

## No Secrets in This File

Wi-Fi passwords and private keys are not stored here.
