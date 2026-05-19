# Runtime Values Worksheet — 2026-04-07

## Purpose
Fill this in at the start of each session. Keeps all session-specific values in one place.
Copy the template block below and fill in the blanks before running anything.

---

## Session template (copy and fill in)

```
SESSION DATE/TIME  : ____________________________  (e.g., 2026-04-07 14:30 UTC+3)

--- NETWORK ---
Hotspot SSID       : ____________________________  (e.g., HUAWEI-B315-58AD)
Hotspot password   : ____________________________  (or "same as before" if unchanged)
Laptop hotspot IP  : 172.20.10.____               (discovered via subnet scan)
Pi IP              : 172.20.10.____               (usually .4 if static; confirm via SSH)
WSL internal IP    : 172.__.__.____               (ip addr show eth0 | grep inet)

--- SERVICES ---
Cloud emulator URL : http://172.20.10.____:5000   (laptop hotspot IP : 5000)
Pi gateway URL     : http://172.20.10.____:8090   (Pi IP : 8090)
UPSTREAM_HOST used : http://172.20.10.____:5000   (set when starting gateway on Pi)

--- ESP32 ---
Serial device      : /dev/ttyUSB____              (usually ttyUSB0)
usbipd BUSID       : ____-____                    (from usbipd list on Windows)

--- CAPTURE / LOGS ---
UART capture file  : capture/____________________________
Pi gateway log     : gateway/logs/proposed_gateway_log.jsonl  (fixed path)
Cloud emulator log : cloud_emulator/api/logs/enroll_log.jsonl (fixed path)

--- RUN RESULTS ---
Run 1 total_ms     : ________  result: PASS / FAIL
Run 2 total_ms     : ________  result: PASS / FAIL
Run 3 total_ms     : ________  result: PASS / FAIL
Run 4 total_ms     : ________  result: PASS / FAIL
Run 5 total_ms     : ________  result: PASS / FAIL
Pack verdict       : ____/5 PASS

--- NOTES ---
(Hotspot stability, gateway restarts, anomalous latency, anything unexpected)
________________________________________________________________
________________________________________________________________
________________________________________________________________
```

---

## Reference: known stable values (2026-04-07 session)

These do not change unless hardware or config changes.

| Item | Value |
|:---|:---|
| Pi static IP | `172.20.10.4` |
| Pi gateway port | `8090` |
| Cloud emulator port | `5000` |
| Device ID | `esp32_01` |
| Device token | `proposed_dev_token_esp32_01_a1b2c3d4e5f6` |
| Firmware WEB_SERVER | `172.20.10.4` |
| Firmware WEB_PORT | `8090` |
| Session token TTL | 30 seconds |
| ESP-IDF version | v5.5.3 at `~/esp-idf-v5.5.3` |

---

## Commands to fill in the blanks (run at session start)

**Laptop hotspot IP (from WSL):**
```bash
for ip in $(seq 2 14); do
  curl -s --connect-timeout 1 http://172.20.10.$ip:5000/health && echo " <- LAPTOP at $ip" &
done; wait
```

**WSL internal IP:**
```bash
ip addr show eth0 | grep "inet " | awk '{print $2}'
```

**Pi IP (if unsure):**
```bash
# From WSL — ping sweep
for ip in $(seq 2 14); do ping -c1 -W1 172.20.10.$ip &>/dev/null && echo "172.20.10.$ip alive" & done; wait
```

**ESP32 serial device:**
```bash
ls /dev/ttyUSB*
```

**Current UART capture filename convention:**
```
capture/proposed_<YYYYMMDD>_<HHMMSS>.txt
```
