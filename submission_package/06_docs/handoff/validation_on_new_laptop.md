# First Validation Sequence — New Laptop

Run these checks in order after initial setup. Each step has a clear expected output.
Stop and fix before continuing if a step fails — later steps depend on earlier ones.

---

## 1. Verify WSL

```bash
uname -a
```
Expected: Linux kernel line mentioning `WSL2` or `microsoft`.

```bash
lsb_release -a 2>/dev/null | grep Description
```
Expected: Ubuntu 22.04 or 24.04.

---

## 2. Verify ESP-IDF

```bash
idf.py --version
```
Expected output:
```
ESP-IDF v5.5.3
```

If not found: `source ~/esp-idf-v5.5.3/export.sh` or re-run the installer.

---

## 3. Verify Cloud Emulator (local, no network required)

```bash
cd cloud_emulator/api
source .venv/bin/activate
python app.py &
sleep 2
curl http://localhost:5000/health
kill %1
deactivate
```

Expected:
```json
{"status":"ok"}
```

If `ca.key` is missing, the emulator starts but `/enroll` will fail. Restore
`ca.key` to `cloud_emulator/pki/ca.key` before enrollment experiments.

---

## 4. Verify Pi SSH

Ensure Pi is on the same hotspot network, then:
```bash
ssh pi@<PI_IP> echo "Pi SSH OK"
```
Expected:
```
Pi SSH OK
```

If connection refused: verify Pi is booted and joined the hotspot. Check the hotspot
admin page or use `nmap -sn <subnet>` to rediscover the Pi IP.

---

## 5. Verify Pi Relay Reachability

Start the relay on the Pi first:
```bash
ssh pi@<PI_IP> "python3 ~/iot_gateway_relay.py &"
sleep 2
```

With cloud emulator running on laptop:
```bash
curl http://<PI_IP>:8080/health
```
Expected:
```json
{"status":"ok"}
```

This confirms the full relay path: WSL → Pi → emulator → Pi → WSL.
If it fails, check: emulator running? Pi relay running? Correct `UPSTREAM_HOST` in
`gateway/pi/iot_gateway_relay.py`? See `docs/handoff/network_rebind.md`.

---

## 6. Verify ESP32 Serial Visibility in WSL

In Windows PowerShell/cmd (as admin):
```powershell
usbipd list                           # find CP210x entry, note BUSID
usbipd attach --wsl --busid <BUSID>
```

In WSL:
```bash
ls /dev/ttyUSB0
```
Expected: file exists (no "No such file" error).

If not visible: confirm usbipd-win is installed, the bind+attach sequence was run,
and the ESP32 is plugged in. Only one WSL terminal should have the device open at a time.

---

## 7. Quick B1 Run (end-to-end validation)

Ensure:
- Cloud emulator is running at `<LAPTOP_IP>:5000`
- B1 firmware `WEB_SERVER` points at the correct target (laptop direct or Pi via-Pi)
- `sdkconfig` has correct Wi-Fi credentials

```bash
cd esp32_firmware/baseline1_http
idf.py build                          # only if target changed since last build
idf.py -p /dev/ttyUSB0 flash monitor
```

Expected serial output (key lines):
```
I (...) example_connect: Got IPv4 event: Interface "example_netif_sta" address: 172.20.10.x
I (...) example: DNS lookup succeeded. IP=<target_ip>
I (...) example: ... connected
I (...) example: ... socket send success
HTTP/1.0 200 OK
...
MEASURE run_id=1 ... latency_ms=<N> http_status=200
...
MEASURE run_id=5 ... http_status=200
I (...) example: MEASURE runs_done=5
```

All 5 runs must show `http_status=200`. If any show `-1`, check:
- Is the target reachable from ESP32? (ping from another device on the hotspot)
- Is the correct `WEB_SERVER` compiled in? (`scripts/handoff/print_session_ips.sh`)
- Has firmware been rebuilt and reflashed after any target change?

---

## Summary Table

| Check | Command | Pass indicator |
|-------|---------|---------------|
| WSL | `uname -a` | Contains `microsoft` |
| ESP-IDF | `idf.py --version` | `ESP-IDF v5.5.3` |
| Emulator (local) | `curl localhost:5000/health` | `{"status":"ok"}` |
| Pi SSH | `ssh pi@<PI_IP> echo OK` | `Pi SSH OK` |
| Pi relay | `curl <PI_IP>:8080/health` | `{"status":"ok"}` |
| ESP32 in WSL | `ls /dev/ttyUSB0` | File exists |
| B1 full run | `idf.py flash monitor` | 5/5 `http_status=200` |
