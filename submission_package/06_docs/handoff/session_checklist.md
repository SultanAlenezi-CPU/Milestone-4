# Per-Session Runbook — IoT Onboarding Testbed

Run through this checklist at the start of every experiment session.
IPs are NOT persistent — rediscover them every time.

---

## 1. Power and Boot Order

1. Start phone hotspot.
2. Boot Raspberry Pi — wait ~30 seconds for full boot.
3. Connect laptop to hotspot Wi-Fi.
4. Plug ESP32 into laptop USB.

---

## 2. Discover Current IPs

**Laptop IP inside WSL:**
```bash
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
# or: hostname -I | awk '{print $1}'
```

**Pi IP** — one of:
```bash
# From WSL, scan the /24 subnet (replace prefix if needed):
nmap -sn 172.20.10.0/28 2>/dev/null | grep -A1 "Raspberry"

# Or from Pi terminal directly:
ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d/ -f1

# Or check your hotspot admin page for connected clients
```

Print and compare current firmware/relay settings:
```bash
bash scripts/handoff/print_session_ips.sh
```

---

## 3. Update Targets If IPs Have Changed

**If laptop IP changed** (affects Pi relay upstream and direct-path firmware):
```bash
# Update Pi relay upstream in repo-side script:
bash scripts/handoff/update_pi_relay_upstream.sh <new_laptop_ip> 5000
# Then re-deploy relay script to Pi (manual scp + restart)

# If running B1 or B3 in direct mode (no Pi), update firmware target:
bash scripts/handoff/update_b1_target.sh <new_laptop_ip> 5000 /health
bash scripts/handoff/update_b3_target.sh <new_laptop_ip> 5000 /enroll
```

**If Pi IP changed** (affects via-Pi firmware targets):
```bash
bash scripts/handoff/update_b1_target.sh <new_pi_ip> 8080 /health
bash scripts/handoff/update_b3_target.sh <new_pi_ip> 8080 /enroll
```

**Rebuild firmware only if a target define changed:**
```bash
cd esp32_firmware/baseline1_http  && idf.py build
cd esp32_firmware/baseline3_enroll && idf.py build
```

See `docs/handoff/network_rebind.md` for the full change matrix.

---

## 4. Start Cloud Emulator (on Laptop, inside WSL)

```bash
cd cloud_emulator/api
source .venv/bin/activate
python app.py
# Listens on 0.0.0.0:5000 — reachable from Pi and ESP32 via laptop hotspot IP
```

Verify locally (new WSL tab):
```bash
curl http://localhost:5000/health
# Expected: {"status":"ok"}
```

---

## 5. Start Pi Relay (on Raspberry Pi)

```bash
ssh pi@<PI_IP>
python3 ~/iot_gateway_relay.py
# Listens on 0.0.0.0:8080 — relay only used for via-Pi (M4) runs
```

Leave this running in the SSH session. Open a separate terminal for other work.

---

## 6. Attach ESP32 USB to WSL

In Windows PowerShell/cmd (as admin):
```powershell
usbipd list                            # find CP210x, note BUSID
usbipd attach --wsl --busid <BUSID>
```

In WSL:
```bash
ls /dev/ttyUSB0   # confirm device is visible
```

---

## 7. Flash and Monitor

```bash
# Baseline 1 (health-check):
cd esp32_firmware/baseline1_http
idf.py -p /dev/ttyUSB0 flash
idf.py -p /dev/ttyUSB0 monitor | tee ../../capture/b1_<date>.txt

# Baseline 3 (enrollment via Pi):
cd esp32_firmware/baseline3_enroll
idf.py -p /dev/ttyUSB0 flash
idf.py -p /dev/ttyUSB0 monitor | tee ../../capture/b3_via_pi_<date>.txt
```

Ctrl+] to exit monitor.

---

## 8. Save Logs and Evidence

After a successful session:
- Confirm `capture/` files were written.
- Check emulator log: `cloud_emulator/api/logs/enroll_log.jsonl`
- Note the session date, IPs used, and any anomalies.

---

## 9. Stop and Clean Up

```bash
# Stop emulator (Ctrl+C in emulator terminal, then):
deactivate

# Stop Pi relay (Ctrl+C in SSH terminal)
exit  # close SSH

# Detach ESP32 from WSL (Windows PowerShell):
usbipd detach --busid <BUSID>
```

---

## Quick Reference

| Component | Runs on | Default port | Path |
|-----------|---------|-------------|------|
| Cloud emulator | Laptop (WSL) | 5000 | /health, /enroll |
| Pi relay | Raspberry Pi | 8080 | /health, /enroll |
| ESP32 B1 target | firmware define | per WEB_PORT | per WEB_PATH |
| ESP32 B3 target | firmware define | per WEB_PORT | per WEB_PATH |
