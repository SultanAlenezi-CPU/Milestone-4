# Component Runbooks — IoT Onboarding Testbed

Short, practical start/stop/verify for each component.
Assumes IPs have already been verified. See `RUNTIME_REBINDING_GUIDE.md` first.

---

## 1. Cloud Emulator

**Source:** `cloud_emulator/api/app.py`
**Port:** 5000 (all interfaces)
**Endpoints:** GET /health, POST /enroll, POST /provision

### Start
```bash
cd cloud_emulator/api
source .venv/bin/activate
python app.py
```

Output when ready:
```
* Serving Flask app 'app'
* Running on http://0.0.0.0:5000
```

Keep this terminal open. Ctrl+C to stop.

### Verify
```bash
curl http://localhost:5000/health
# Expected: {"status":"ok"}
```

### Background start (if you need the terminal)
```bash
cd cloud_emulator/api
source .venv/bin/activate
nohup python app.py > /tmp/emulator.log 2>&1 &
echo "Emulator PID: $!"
```

Stop: `kill <PID>`

### Important behavior
- Token store is loaded at startup from `b2_tokens.json`. **Restarting the emulator resets all tokens to unused.** This is intentional and allows repeatable B2 runs.
- Enrollment log appends to `cloud_emulator/api/logs/enroll_log.jsonl` on every /enroll call.
- Provision log appends to `cloud_emulator/api/logs/provision_log.jsonl` on every /provision call.
- If `ca.key` is missing, the emulator starts but /enroll will return a 500 error.

### Logs
```
cloud_emulator/api/logs/enroll_log.jsonl      ← all POST /enroll events
cloud_emulator/api/logs/provision_log.jsonl   ← all POST /provision events
```

---

## 2. Pi Dumb Relay

**Source:** `gateway/pi/iot_gateway_relay.py`
**Port:** 8080
**Routes:** /health → upstream/health, /enroll → upstream/enroll, /provision → upstream/provision
**Upstream:** hardcoded `UPSTREAM_HOST` at line 5 (must match laptop hotspot IP)

### Deploy to Pi (run from laptop WSL)
```bash
scp gateway/pi/iot_gateway_relay.py pi@<PI_IP>:~/
```

### Start (via SSH from laptop)
```bash
ssh pi@<PI_IP> "python3 ~/iot_gateway_relay.py"
```

Keep the SSH session open, or use nohup:
```bash
ssh pi@<PI_IP> "nohup python3 ~/iot_gateway_relay.py > ~/relay.log 2>&1 &"
```

### Verify
```bash
# From WSL on laptop:
curl http://<PI_IP>:8080/health
# Expected: {"status":"ok"}
```

### Stop
Ctrl+C in the SSH terminal, or:
```bash
ssh pi@<PI_IP> "pkill -f iot_gateway_relay.py"
```

### Check log
```bash
ssh pi@<PI_IP> "cat ~/relay.log"   # if started with nohup
# or
gateway/logs/iot_gateway_relay_2026-04-05.log   ← historical log from Apr 5 session
```

---

## 3. Pi Proposed Gateway

**Source:** `gateway/pi/iot_gateway_proposed.py`
**Port:** 8090
**Routes:** POST /gateway/auth, POST /gateway/enroll, GET /health
**Upstream:** set via `UPSTREAM_HOST` env var (must be laptop hotspot IP, NOT WSL IP)

### Deploy to Pi
```bash
scp gateway/pi/iot_gateway_proposed.py pi@<PI_IP>:~/
scp gateway/pi/device_registry.example.json pi@<PI_IP>:~/device_registry.json
```

Edit `device_registry.json` on the Pi if needed (device_id, token, allowed flag).
The default example file has `esp32_01` with a pre-set device_token.

### Start
```bash
ssh pi@<PI_IP> "UPSTREAM_HOST=http://<LAPTOP_HOTSPOT_IP>:5000 python3 ~/iot_gateway_proposed.py"
```

Replace `<LAPTOP_HOTSPOT_IP>` with the current Windows hotspot IP (e.g., 172.20.10.2).

**Do not use the WSL internal IP here.** The Pi cannot reach it.

### Verify
```bash
curl http://<PI_IP>:8090/health
# Expected: {"status":"ok","service":"gateway_proposed"}
```

### Stop
Ctrl+C in the SSH terminal. The gateway does NOT auto-restart.

### Important: process does not survive Pi reboot or crash
If the Pi reboots or the process crashes, you must re-SSH and restart it manually.
This is a known limitation documented in evidence notes. The ESP32 firmware recovers gracefully — press EN after restarting the gateway.

### Log
```bash
gateway/logs/proposed_gateway_log.jsonl   ← copied from Pi after sessions
```

To copy the live log from the Pi after a session:
```bash
scp pi@<PI_IP>:~/proposed_gateway_log.jsonl gateway/logs/proposed_gateway_log_<date>.jsonl
```

---

## 4. Baseline 1 Firmware (B1 — plain HTTP health-check)

**Source:** `esp32_firmware/baseline1_http/main/http_request_example_main.c`
**Current target:** `172.20.10.4:8080/health` (Pi relay)
**Runs:** 5 | **Gap:** 1500 ms | **Receive timeout:** 5 s

### Update target if IP changed
```bash
bash scripts/handoff/update_b1_target.sh <PI_IP> 8080 /health
# or for direct mode (no Pi):
bash scripts/handoff/update_b1_target.sh <LAPTOP_HOTSPOT_IP> 5000 /health
```

### Build
```bash
cd esp32_firmware/baseline1_http
idf.py build
```

### Flash and monitor
```bash
# Attach ESP32 first (Windows PowerShell):
#   usbipd attach --wsl --busid <BUSID>
# Then in WSL:
idf.py -p /dev/ttyUSB0 flash monitor
```

### What to watch for
5 lines matching:
```
MEASURE run_id=N latency_ms=NNN heap_before=NNN heap_after=NNN http_status=200 result=PASS
```
One line at the end: `MEASURE runs_done=5`

### Expected output pattern
Total latency: 600–3000 ms per run (hotspot-dependent). All 5 must show `http_status=200`.

---

## 5. Baseline 2 Firmware (B2 — token provisioning)

**Source:** `esp32_firmware/baseline2_token/main/http_request_example_main.c`
**Current target:** `172.20.10.4:8080/provision` (Pi relay)
**Runs:** 10 | **Gap:** 1500 ms | **Receive timeout:** 8 s (fixed from 5 s on 2026-04-07)
**Tokens:** 10 pre-loaded in `TOKENS[]` array in source

### Before each B2 run
1. Restart the cloud emulator (this resets all tokens to unused in memory).
2. Verify the Pi relay is running (POST /provision must route through it).
3. The token array in firmware (`TOKENS[]` at lines 49–60) must match the tokens in `b2_tokens.json`.

> **Token mismatch causes HTTP 401 on all 10 runs.** If you see 10 consecutive 401s,
> the firmware token array and the server token store are out of sync.
> Edit `b2_tokens.example.json`, copy it to `b2_tokens.json`, restart the emulator.

### Build and flash
```bash
cd esp32_firmware/baseline2_token
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### What to watch for
10 lines matching:
```
MEASURE run_id=N latency_ms=NNNN heap_before=NNN heap_after=NNN http_status=200 result=PASS
```

### Current status
Client-side best result is 7/10 PASS (runs 4, 7, 10 timed out at ~5010 ms with errno=11).
The 8 s timeout fix has been applied. A clean 10/10 run has not yet been collected.

---

## 6. Baseline 3 Firmware (B3 — CSR enrollment)

**Source:** `esp32_firmware/baseline3_enroll/main/http_request_example_main.c`
**Current target:** `172.20.10.4:8080/enroll` (Pi relay)
**Runs:** 5 | **Gap:** 1500 ms | **Receive timeout:** 15 s (longer — CSR signing takes time)

### Update target if IP changed
```bash
bash scripts/handoff/update_b3_target.sh <PI_IP> 8080 /enroll
```

### Build and flash
```bash
cd esp32_firmware/baseline3_enroll
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### What to watch for
5 lines matching:
```
MEASURE run_id=N latency_ms=NNNN heap_before=NNN heap_after=NNN http_status=200 result=PASS
```
Each MEASURE line also confirms the emulator returned a certificate (`cert_received=1` in some builds).

### Note on emulator
The cloud emulator must have `ca.key` present and `cloud_emulator/pki/` must be accessible. Without the CA key, the emulator returns 500 and the firmware logs `http_status=500`.

---

## 7. Proposed Gateway Firmware

**Source:** `esp32_firmware/proposed_gateway/main/http_request_example_main.c`
**Current target:** `172.20.10.4:8090` (Pi proposed gateway)
**Runs:** 1 per EN-button press (compile-time run_id=1, one-shot)
**Paths:** POST /gateway/auth, then POST /gateway/enroll

### Update target if Pi IP changed
Edit `esp32_firmware/proposed_gateway/main/http_request_example_main.c`:
```c
// Lines 43–44:
#define WEB_SERVER    "<PI_IP>"
#define WEB_PORT      "8090"
```

No update script exists for the proposed firmware. Edit manually.

### Build and flash
```bash
cd esp32_firmware/proposed_gateway
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### What to watch for
One `PROPOSED_MEASURE` line per EN-button press:
```
PROPOSED_MEASURE run_id=1 auth_ms=NNN csr_ms=NNN enroll_ms=NNNN total_ms=NNNN
  heap_before=NNN heap_after=NNN heap_delta=NNN
  http_status_auth=200 http_status_enroll=200 cert_received=1 result=PASS
```

### Repeated runs
Press EN button once per run. Each press: firmware boots, runs Phase 1 (auth) + Phase 2 (enroll), prints one PROPOSED_MEASURE line, then idles.

Session tokens on the Pi gateway are in-memory and expire after 30 seconds. Pressing EN too quickly after a failed run means the previous session_token may still be in the used-set. Restarting the gateway clears the session store.

---

## 8. Capture and Log Locations

| Type | Location | Format |
|---|---|---|
| B1 UART | `capture/b1_serial_live.txt` | Plain text, 272 lines |
| B2 via-Pi best capture | `capture/b2_via_pi_clean_2026-04-06_final.txt` | Plain text |
| B2 replay scenario | `capture/b2_replay_scenario_2026-04-06.txt` | Plain text |
| Proposed canonical | `capture/proposed_p5_repeated_runs_latest.txt` | Plain text, 5 PROPOSED_MEASURE lines |
| Cloud enroll log | `cloud_emulator/api/logs/enroll_log.jsonl` | JSONL |
| Cloud provision log | `cloud_emulator/api/logs/provision_log.jsonl` | JSONL |
| Pi relay log (historical) | `gateway/logs/iot_gateway_relay_2026-04-05.log` | Plain text |
| Pi gateway log | `gateway/logs/proposed_gateway_log.jsonl` | JSONL |
| pcap files | `capture/pcaps/` | **Empty — no real pcaps collected** |

### Saving new captures
When running `idf.py monitor`, pipe or copy the terminal output to a file:
```bash
idf.py -p /dev/ttyUSB0 flash monitor 2>&1 | tee capture/b1_new_$(date +%Y%m%d_%H%M%S).txt
```

Or use `idf.py monitor` alone and manually copy the terminal output after the run.
