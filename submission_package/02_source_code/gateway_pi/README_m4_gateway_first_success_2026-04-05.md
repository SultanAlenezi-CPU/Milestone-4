# M4 Gateway — First Verified Success (2026-04-05)

## Overview

This directory will hold the Raspberry Pi relay script once it is copied from the Pi
into the repo. As of the first verified M4 success (2026-04-05), the relay script
ran on the Pi outside this repository.

---

## Relay Script Location (external, on Pi)

| Item | Path |
|------|------|
| Pi relay script | `~/iot_gateway_relay.py` on the Raspberry Pi |
| Pi relay log | `~/gateway_logs/iot_gateway_relay_2026-04-05.log` on the Raspberry Pi |

> **Repo copy pending.** The script has NOT yet been copied into
> `gateway/pi/iot_gateway_relay.py`. Do not fabricate this file. Copy it explicitly
> from the Pi when ready (e.g. `scp pi@<pi_ip>:~/iot_gateway_relay.py gateway/pi/`).

---

## Verified Relay Behavior

The following relay behavior was confirmed during first M4 success on 2026-04-05:

| Request | Pi forwards to | Confirmed |
|---------|---------------|-----------|
| GET /health | http://172.20.10.2:5000/health | YES — `RELAY GET /health -> http://172.20.10.2:5000/health status=200` |
| POST /enroll | http://172.20.10.2:5000/enroll | YES — `RELAY POST /enroll -> http://172.20.10.2:5000/enroll status=200` |

The relay ran on the Pi at `172.20.10.4:8080`. The Pi and the Windows cloud emulator
host (`172.20.10.2:5000`) were both on the same hotspot network (HUAWEI-B315-58AD).
The relay received requests from the ESP32 and forwarded them upstream to the cloud emulator.

---

## Network Topology at First Success

```
[ESP32]
  |
  | Wi-Fi (HUAWEI-B315-58AD)
  v
[Raspberry Pi 4]  172.20.10.4:8080
  |  iot_gateway_relay.py
  | local network
  v
[Windows host — cloud emulator]  172.20.10.2:5000
  |  cloud_emulator/api/app.py
  v
[CA signing]  cloud_emulator/pki/ca.crt + ca.key
```

---

## Evidence files for this milestone

| File | Description |
|------|-------------|
| `data/raw/m4_b1_via_pi_gateway_2026-04-05_evidence.md` | B1 via Pi evidence note |
| `data/raw/m4_b3_via_pi_gateway_2026-04-05_evidence.md` | B3 via Pi evidence note |
| `capture/b3_via_pi_serial_live.txt` | B3 via Pi UART capture (2 sessions, partial) |
| `cloud_emulator/api/logs/enroll_log.jsonl` | Server-side enrollment log (includes B3 via Pi entries) |

---

## Next Steps for Gateway

1. Copy `~/iot_gateway_relay.py` from Pi into this directory.
2. Copy `~/gateway_logs/iot_gateway_relay_2026-04-05.log` from Pi into
   `gateway/logs/` or `data/raw/`.
3. Fix ESP32 socket read timeout for B3 via Pi (see evidence note for details).
4. Run a clean 5/5 B3 via Pi session and capture full UART log.
5. Packet capture for B1 and B3 via Pi (postponed from this phase).
