# New Laptop Setup Guide — IoT Onboarding Testbed

## Purpose

This guide explains how to redeploy the Secure IoT Device Onboarding Testbed on a
new or replacement laptop. It assumes you have physical access to the same devices
(ESP32, Raspberry Pi) and the same hotspot, but the new laptop may produce different
IP addresses. All steps treat IPs as session-specific and rediscoverable.

---

## Architecture

```
[ESP32 dev board]
   |  Wi-Fi (phone hotspot)
   v
[Raspberry Pi 4]        <-- optional relay/gateway node
   |  172.20.10.x:8080  (IP session-specific — rediscover each session)
   |  runs: gateway/pi/iot_gateway_relay.py
   v
[Laptop (Windows + WSL)]
   |  172.20.10.y:5000  (IP session-specific — rediscover each session)
   |  runs: cloud_emulator/api/app.py  (inside WSL, bound to 0.0.0.0)
   v
[Cloud/PKI Emulator]    <-- signs device CSRs, returns certificates
```

**Direct path (no Pi):**
ESP32 connects straight to laptop IP:5000.

**Via-Pi path (M4 gateway):**
ESP32 connects to Pi IP:8080 → Pi relay forwards to laptop IP:5000.

---

## Prerequisites on the New Laptop

### Windows side
- Windows 10/11 with WSL2 enabled
- [usbipd-win](https://github.com/dorssel/usbipd-win) installed — required to
  expose the ESP32 USB serial adapter (CP210x, USB ID `10c4:ea60`) into WSL
- Python 3.x (for running the cloud emulator natively on Windows if needed)
- Optional: Wireshark (for packet capture)

### WSL side (Ubuntu)
- WSL2 with Ubuntu 22.04 or 24.04
- `git`
- `python3`, `python3-venv`, `python3-pip`
- ESP-IDF v5.5.3 at `~/esp-idf-v5.5.3`
  - Install guide: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/
  - After install, add to `~/.bashrc`:
    ```
    source ~/esp-idf-v5.5.3/export.sh
    ```
  - Verify: `idf.py --version`  → expected: `ESP-IDF v5.5.3`
- `ssh` (standard, for Pi access)
- Optional: `tshark` / `tcpdump` (for captures from WSL)

### Raspberry Pi side
- Python 3 installed
- `gateway/pi/iot_gateway_relay.py` deployed to `~/iot_gateway_relay.py`
  - Copy from repo: `scp gateway/pi/iot_gateway_relay.py pi@<PI_IP>:~/`
- SSH access from laptop (`ssh pi@<PI_IP>`)

---

## Repo Placement

Place the repo inside the WSL filesystem, not under `/mnt/c/`. The ESP-IDF toolchain
performs significantly better on the native Linux filesystem.

Recommended path:
```
/home/<wsl_user>/iot_onboarding/
```

Clone or copy:
```bash
git clone <repo_url> /home/<wsl_user>/iot_onboarding
# or unpack the handoff archive into that path
```

---

## First-Time Setup Flow

### 1. Verify ESP-IDF
```bash
idf.py --version
# Expected: ESP-IDF v5.5.3
```
If not found, source the export script or re-run the installer.

### 2. Set up the cloud emulator Python environment
```bash
cd cloud_emulator/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```
Dependencies: Flask 3.0.3, cryptography 44.0.1

### 3. Restore the CA private key
The CA private key (`cloud_emulator/pki/ca.key`) is NOT in version control.
Without it the emulator cannot sign certificates. Restore it from your secure backup
before running enrollment experiments.

Verify:
```bash
ls cloud_emulator/pki/ca.crt   # committed — should exist
ls cloud_emulator/pki/ca.key   # NOT committed — must restore manually
```

### 4. Configure Wi-Fi credentials in firmware
`sdkconfig` files are excluded from VCS because they contain Wi-Fi passwords.
After cloning, configure each firmware project:
```bash
cd esp32_firmware/baseline1_http
idf.py menuconfig
# Example > Wi-Fi SSID, Example > Wi-Fi Password
```
Repeat for `esp32_firmware/baseline3_enroll`.

### 5. Verify usbipd-win (Windows, run in PowerShell/cmd as admin)
```powershell
usbipd list
# Look for: Silabs CP210x USB to UART Bridge  10c4:ea60
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```
Then in WSL:
```bash
ls /dev/ttyUSB0   # should appear after attach
```

### 6. Verify SSH to Pi
```bash
ssh pi@<PI_IP>
# Pi must be on the same hotspot network
```
Use `docs/handoff/network_rebind.md` to discover the current Pi IP.

---

## IP Addresses Are Session-Specific

**Every session**, the laptop and Pi may receive different IPs from the hotspot DHCP.
Do not trust IPs from a previous session. See `docs/handoff/session_checklist.md`
for the per-session rediscovery workflow and `docs/handoff/network_rebind.md` for
exactly which files to update when IPs change.

Quick rediscovery tool:
```bash
bash scripts/handoff/print_session_ips.sh
```

---

## Do Not Forget Checklist

- [ ] ESP-IDF sourced in `~/.bashrc`
- [ ] Cloud emulator `.venv` created inside `cloud_emulator/api/`
- [ ] `ca.key` restored to `cloud_emulator/pki/ca.key`
- [ ] Wi-Fi credentials set in `sdkconfig` for each firmware project (via `idf.py menuconfig`)
- [ ] usbipd-win installed on Windows and ESP32 USB attached to WSL before flashing
- [ ] Pi relay script deployed to `~/iot_gateway_relay.py` on the Pi
- [ ] IPs rediscovered before each session (see session checklist)
- [ ] Cloud emulator running before flashing (it must be reachable from ESP32)

---

## No Secrets in This File

Wi-Fi passwords, private keys, and hotspot credentials are not stored here.
