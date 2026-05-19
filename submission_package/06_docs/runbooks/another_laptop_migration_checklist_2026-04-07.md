# Another-Laptop Migration Checklist — 2026-04-07

## Purpose
Step-by-step checklist for reproducing the working testbed on a new Windows laptop.
Complete sections in order. Do not skip the pre-flight sequence.

---

## 1. Physical items to carry / keep the same

- [ ] Raspberry Pi (same unit — static IP `172.20.10.4` is tied to MAC address on the hotspot)
- [ ] ESP32 dev board (same unit — firmware is already flashed)
- [ ] USB-A to micro-USB cable for ESP32 ↔ laptop
- [ ] HUAWEI-B315-58AD mobile hotspot router (or know the new hotspot SSID/password)
- [ ] Hotspot login credentials (SSID + Wi-Fi password)
- [ ] Pi SSH credentials (`pi@172.20.10.4`, password or SSH key)

**Critical:** If you use a different hotspot, the Pi IP `172.20.10.4` may change. You must then update the firmware `WEB_SERVER` define and reflash. Use the same hotspot if possible.

---

## 2. Windows checks

- [ ] Windows hotspot is **ON** and broadcasting. Confirm SSID matches what Pi expects.
- [ ] Pi is connected to the hotspot. (SSH from Windows: `ssh pi@172.20.10.4` — if this fails, Pi is not on the network.)
- [ ] WSL2 is installed: `wsl --list --verbose` in PowerShell shows a running distro.
- [ ] `usbipd` is installed: `usbipd list` in PowerShell (admin). If missing, install from GitHub: `winget install usbipd`.
- [ ] ESP32 is plugged in via USB. Confirm it appears in `usbipd list` (look for "CP210x" or "CH340").
- [ ] Attach ESP32 to WSL:
  ```powershell
  # PowerShell (admin)
  usbipd attach --wsl --busid <BUSID>
  ```
  Replace `<BUSID>` with the value from `usbipd list` (e.g., `2-3`).
- [ ] Confirm attach succeeded: `usbipd list` should show the device as "Attached".

---

## 3. WSL checks

Run all of the following inside WSL (Ubuntu).

- [ ] Confirm ESP32 is visible:
  ```bash
  ls /dev/ttyUSB*
  ```
  Expected: `/dev/ttyUSB0`. If missing, the usbipd attach step failed or the cable is bad.

- [ ] Fix USB permissions if needed:
  ```bash
  ls -l /dev/ttyUSB0
  # If not crw-rw-rw-, run:
  sudo chmod 666 /dev/ttyUSB0
  ```

- [ ] Confirm repo is present:
  ```bash
  ls /home/iot_onboarding/iot_onboarding/
  ```
  Expected: `cloud_emulator/`, `data/`, `docs/`, `esp32_firmware/`, `gateway/`, etc.

- [ ] Source ESP-IDF environment:
  ```bash
  . ~/esp-idf-v5.5.3/export.sh
  ```
  Expected: "Done! You can now compile ESP-IDF projects."
  If `~/esp-idf-v5.5.3` is missing: the IDF was not transferred. Copy it from the old laptop or reinstall.

- [ ] Start the cloud emulator:
  ```bash
  cd /home/iot_onboarding/iot_onboarding/cloud_emulator/api
  python3 app.py &
  ```

- [ ] Confirm emulator is responding on localhost:
  ```bash
  curl -s http://localhost:5000/health
  ```
  Expected: HTTP 200 with a JSON body (e.g., `{"status": "ok"}`). If no response, emulator failed to start — check for Python errors.

- [ ] Discover the current Windows hotspot IP (the IP the Pi must use to reach the emulator):
  ```bash
  for ip in $(seq 2 14); do
    curl -s --connect-timeout 1 http://172.20.10.$ip:5000/health && echo " <- EMULATOR at $ip" &
  done
  wait
  ```
  Note the `<X>` value — you will need it for the Pi gateway start command.

---

## 4. Pi checks

SSH to the Pi: `ssh pi@172.20.10.4`

- [ ] Confirm gateway script is present:
  ```bash
  ls ~/gateway/pi/iot_gateway_proposed.py
  ls ~/gateway/pi/device_registry.json
  ```
  If missing: copy from repo — see `docs/portability_handoff_draft_2026-04-07.md` "Files that must be copied" section.

- [ ] Confirm logs directory exists:
  ```bash
  ls ~/gateway/logs/
  # If missing:
  mkdir -p ~/gateway/logs
  ```

- [ ] Check if gateway is already running:
  ```bash
  ss -tlnp | grep 8090
  ```
  If listening: already up, verify with health check below. If not listening: start it.

- [ ] Start gateway (replace `<X>` with the laptop IP found in step 3):
  ```bash
  UPSTREAM_HOST=http://172.20.10.<X>:5000 python3 ~/gateway/pi/iot_gateway_proposed.py &
  ```
  Leave this running. (Use `nohup ... &` to keep it alive after SSH disconnect — see gateway runbook.)

- [ ] Verify gateway is reachable from Pi:
  ```bash
  curl -s http://localhost:8090/health
  ```
  Expected: HTTP 200.

- [ ] Verify gateway is reachable from WSL (run in WSL):
  ```bash
  curl -s http://172.20.10.4:8090/health
  ```
  Expected: HTTP 200. If this fails but Pi-local works, it is a hotspot routing issue.

---

## 5. ESP32 checks

- [ ] ESP32 is visible in WSL at `/dev/ttyUSB0` (confirmed in step 3).
- [ ] Open monitor **before** any reset:
  ```bash
  cd /home/iot_onboarding/iot_onboarding/esp32_firmware/proposed_gateway
  idf.py monitor
  ```
  Do not reset the ESP32 until the monitor says "--- idf_monitor on /dev/ttyUSB0 ---".
  **Monitor-before-reset discipline:** always start monitor first, then reset, so you capture boot output from the very first line.
- [ ] Perform reset: press EN button on ESP32 (or Ctrl-T Ctrl-R in the monitor window).
- [ ] Confirm firmware output starts with boot messages followed by `PROPOSED_MEASURE`.

---

## 6. First-boot pre-flight

Complete steps 1–5, then run this sequence exactly once to confirm the full stack works before collecting any data runs:

```
WSL terminal 1:   cloud emulator running (python3 app.py)
Pi SSH terminal:  gateway running with correct UPSTREAM_HOST
WSL terminal 2:   idf.py monitor watching /dev/ttyUSB0
ESP32:            press EN to reset
```

Expected output in monitor:
```
PROPOSED_MEASURE run_id=1 ... result=PASS
```

If `result=FAIL`, diagnose before proceeding to data collection. Common causes are in section 8.

---

## 7. First proposed-method test sequence (after pre-flight PASS)

1. Reset ESP32 (EN button). Confirm `result=PASS` in monitor.
2. Wait for the task to complete and the monitor to go quiet (chip enters sleep or loops).
3. Reset again. Confirm second `result=PASS`.
4. Repeat for 5 total resets. Record each `PROPOSED_MEASURE` line.
5. On 5/5 PASS: data is valid for a new five-run pack.
6. If a run produces a high auth_latency (>1000 ms) but still PASS: note it as a supplemental run, do not include in the canonical pack mean/stddev without flagging it.
7. Save UART capture: `capture/proposed_<date>_<time>.txt`.

---

## 8. Common failure points

| Symptom | Where to look | Fix |
|:---|:---|:---|
| `/dev/ttyUSB0` missing in WSL | usbipd attach not done | `usbipd attach --wsl --busid <ID>` in PowerShell (admin) |
| `idf.py monitor` hangs or garbled | Wrong baud or IDF not sourced | Source IDF first; use `idf.py monitor` (reads baud from sdkconfig) |
| ESP32 `errno=111` Connection refused | Gateway not running | Check `ss -tlnp | grep 8090` on Pi; restart gateway |
| Auth HTTP 401 | Wrong device token in firmware | Firmware `DEVICE_TOKEN` must match `device_registry.json` |
| Enroll HTTP 502 | UPSTREAM_HOST wrong | Re-scan subnet; restart gateway with correct IP |
| Enroll HTTP 401 | Session token expired | Phase 1→2 took >30 s; reboot ESP32 |
| Enroll HTTP 409 | Token already used | Reboot ESP32 |
| Emulator not responding on :5000 | Emulator not started / port conflict | `python3 app.py` in `cloud_emulator/api/`; check for port-in-use error |
| Pi IP not `172.20.10.4` | Different hotspot / DHCP changed | `arp -a` on Windows to find Pi MAC; update firmware if IP changed and reflash |
| `idf.py monitor` says "Could not exclusively lock port" | Another process holds ttyUSB0 | `lsof /dev/ttyUSB0` → `kill <PID>` |
