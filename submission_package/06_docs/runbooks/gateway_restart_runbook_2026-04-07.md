# Gateway Restart Runbook — Proposed Method Gateway (2026-04-07)

## Purpose
Quick reference for restarting the Pi-side proposed gateway service between sessions.
The gateway process is not persistent across reboots or crashes and must be manually restarted.

---

## Key paths and values

| Item | Value |
|:---|:---|
| Gateway script | `~/gateway/pi/iot_gateway_proposed.py` |
| Device registry | `~/gateway/pi/device_registry.json` |
| Log file | `~/gateway/logs/proposed_gateway_log.jsonl` |
| Listen port | 8090 |
| Upstream host (current) | `http://172.20.10.2:5000` |

**Note on UPSTREAM_HOST:** The Windows hotspot IP changes across sessions. `172.20.10.2` was correct for the 2026-04-07 P5 session. Verify before each session (see IP discovery below).

---

## Pre-start checklist

1. **Confirm cloud emulator is running** on the Windows/WSL side:
   ```
   curl -s http://172.20.10.2:5000/health
   ```
   Expected: `{"status": "ok"}` or similar. If this fails, start the emulator first.

2. **Discover current laptop hotspot IP** if unsure:
   ```bash
   for ip in $(seq 2 14); do
     curl -s --connect-timeout 1 http://172.20.10.$ip:5000/health && echo " <- EMULATOR at $ip" &
   done
   wait
   ```

3. **Check if gateway is already running** (port 8090 listening):
   ```bash
   ss -tlnp | grep 8090
   # or
   curl -s http://localhost:8090/health
   ```
   If listening: gateway is up, no restart needed.

4. **Kill any stale gateway process** if port is bound but unresponsive:
   ```bash
   pkill -f iot_gateway_proposed.py
   sleep 1
   ss -tlnp | grep 8090   # confirm port is free
   ```

---

## Start the gateway

### Foreground (recommended for monitoring / single session)
```bash
cd ~/gateway/pi
UPSTREAM_HOST=http://172.20.10.2:5000 python3 iot_gateway_proposed.py
```
Output appears in terminal. Kill with Ctrl-C.

### Background with nohup (for leaving running)
```bash
cd ~/gateway/pi
UPSTREAM_HOST=http://172.20.10.2:5000 nohup python3 iot_gateway_proposed.py \
  > ~/gateway/logs/gateway_stdout.log 2>&1 &
echo $! > ~/gateway/logs/gateway.pid
echo "Started PID $(cat ~/gateway/logs/gateway.pid)"
```
To stop:
```bash
kill $(cat ~/gateway/logs/gateway.pid)
```

---

## Post-start health check

```bash
# Health endpoint
curl -v http://172.20.10.4:8090/health

# Auth smoke test (from Pi or any device on the hotspot network)
curl -s -X POST http://172.20.10.4:8090/gateway/auth \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32_01","device_token":"proposed_dev_token_esp32_01_a1b2c3d4e5f6"}'
```
Expected auth response: `{"session_token": "<32-hex-chars>"}` with HTTP 200.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|:---|:---|:---|
| ESP32 gets `errno=111` (Connection refused) | Gateway not running or wrong port | Check `ss -tlnp | grep 8090`; restart gateway |
| Auth returns 401 | Wrong device_id or device_token in firmware | Verify firmware defines against `device_registry.json` |
| Enroll returns 502 | UPSTREAM_HOST wrong or emulator down | Re-scan subnet for emulator IP; restart with correct UPSTREAM_HOST |
| Enroll returns 401 | Session token expired (>30 s between Phase 1 and Phase 2) | Normal timeout behavior; reboot ESP32 to re-run |
| Enroll returns 409 | Session token already used (second use attempt) | Normal single-use behavior; reboot ESP32 |
| Log file missing | `~/gateway/logs/` dir doesn't exist | `mkdir -p ~/gateway/logs` |

---

## Operational note

The Pi gateway process is **not auto-started** on Pi boot. Every new SSH session should begin with the pre-start checklist above. This is a known operational property of the testbed, documented in `data/raw/proposed_gateway_recovered_pass_2026-04-07.md`. It is not a firmware or protocol defect.
