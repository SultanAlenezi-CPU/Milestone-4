# Setup on Another Laptop — IoT Onboarding Testbed

This guide covers everything needed to bring up the full testbed on a new machine.
It assumes the same ESP32, Raspberry Pi, and phone hotspot. IPs will differ.

---

## OS and Environment Requirements

| Requirement | Minimum | Verified with |
|---|---|---|
| OS | Windows 10 or 11 | Windows 11 |
| WSL version | WSL2 | WSL2 |
| WSL distro | Ubuntu 22.04 or 24.04 | Ubuntu 24.04.4 LTS |
| Python (in WSL) | 3.10+ | Python 3.12.3 |
| ESP-IDF | v5.5.3 exactly | v5.5.3 |
| usbipd-win | Any current release | Needed for ESP32 USB |
| SSH | Standard OpenSSH | Needed for Pi access |

**Do not use a different ESP-IDF version.** The firmware projects have `sdkconfig` files tuned for 5.5.3. A different version may silently change build options.

---

## Step 0 — Transfer the Repo

**Option A: Copy the full repo folder** (preferred — preserves all captures and logs)
```bash
# From original machine, make a tar (exclude venv and build artifacts)
cd /home/iot_onboarding
tar --exclude='iot_onboarding/cloud_emulator/api/.venv' \
    --exclude='iot_onboarding/venv' \
    --exclude='iot_onboarding/esp32_firmware/*/build' \
    --exclude='iot_onboarding/**/__pycache__' \
    -czf iot_onboarding_handoff.tar.gz iot_onboarding/
```
Then copy the archive to the new machine and unpack:
```bash
mkdir -p /home/<new_user>
tar -xzf iot_onboarding_handoff.tar.gz -C /home/<new_user>/
```

**Option B: Git clone** (loses untracked files — many captures and docs are untracked)
```bash
git clone <repo_url> /home/<new_user>/iot_onboarding
```
If cloning, check `git status` afterwards. Many files are marked `??` (untracked) and must be transferred separately. See `HANDOVER_EXPORT_NOTE.md` for the list.

**Repo must live inside the WSL filesystem** (e.g., `/home/<user>/`). Do not put it under `/mnt/c/`. The ESP-IDF build toolchain runs ~3–5× slower on the Windows mount.

---

## Step 1 — Install ESP-IDF v5.5.3

If not already installed:
```bash
cd ~
git clone --recursive https://github.com/espressif/esp-idf.git esp-idf-v5.5.3
cd esp-idf-v5.5.3
git checkout v5.5.3
git submodule update --init --recursive
./install.sh esp32
```

Add to `~/.bashrc`:
```bash
echo 'source ~/esp-idf-v5.5.3/export.sh' >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
idf.py --version
# Must output: ESP-IDF v5.5.3
```

---

## Step 2 — Set Up Cloud Emulator Python Environment

```bash
cd /home/<user>/iot_onboarding/cloud_emulator/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

Dependencies installed: Flask 3.0.3, cryptography 44.0.1, Werkzeug 3.1.6.

---

## Step 3 — Restore the CA Private Key

The CA key is NOT tracked in git. Without it, B3 and Proposed enrollment will fail (emulator cannot sign CSRs).

Copy `ca.key` from the original machine or your secure backup to:
```
cloud_emulator/pki/ca.key
```

Verify:
```bash
ls cloud_emulator/pki/ca.crt   # should exist (tracked)
ls cloud_emulator/pki/ca.key   # must exist (NOT tracked — restore manually)
openssl x509 -in cloud_emulator/pki/ca.crt -noout -subject
# Should show: subject=C=SA, ST=Riyadh, ... O=IoT
```

**Security note:** Do not commit `ca.key`. Do not copy it to a shared or public location.

---

## Step 4 — Configure Wi-Fi Credentials in Firmware

`sdkconfig` files are excluded from VCS. The repo includes them locally but they contain your hotspot password — never commit them.

On a new machine, configure each firmware project manually:
```bash
cd esp32_firmware/baseline1_http
idf.py menuconfig
# Navigate: Example Configuration → WiFi SSID → enter: HUAWEI-B315-58AD
# Navigate: Example Configuration → WiFi Password → enter: <hotspot password>
# Save and exit
```

Repeat for: `baseline2_token`, `baseline3_enroll`, `proposed_gateway`.

All four projects use the same hotspot SSID and password.

---

## Step 5 — Install usbipd-win (Windows)

Install from: https://github.com/dorssel/usbipd-win/releases

After installing, in Windows PowerShell (run as Administrator):
```powershell
usbipd list
# Find: Silabs CP210x USB to UART Bridge   10c4:ea60   BUSID=N-N
usbipd bind --busid <BUSID>   # one-time per device
```

Before each flash session:
```powershell
usbipd attach --wsl --busid <BUSID>
```

Then in WSL:
```bash
ls /dev/ttyUSB0   # must appear before running idf.py flash
```

If `/dev/ttyUSB0` is missing, the ESP32 USB is not attached to WSL. Re-run the `usbipd attach` command.

---

## Step 6 — Set Up Pi Relay Script

The Pi gateway scripts live in `gateway/pi/`. They must be copied to the Pi:

```bash
PI_IP=172.20.10.4   # replace with actual Pi IP after discovery
scp gateway/pi/iot_gateway_relay.py pi@$PI_IP:~/
scp gateway/pi/iot_gateway_proposed.py pi@$PI_IP:~/
scp gateway/pi/device_registry.example.json pi@$PI_IP:~/device_registry.json
```

The Pi does not need the full repo. Just these three files.

Python 3 is standard on Raspberry Pi OS. No additional packages needed (both scripts use stdlib only).

---

## Step 7 — Verify the Environment

Run the validation sequence from `validation_on_new_laptop.md` (existing file in `docs/handoff/`).

Quick smoke test:
```bash
# 1. IDF version
idf.py --version                                # expect: ESP-IDF v5.5.3

# 2. Emulator starts
cd cloud_emulator/api
source .venv/bin/activate
python app.py &
sleep 2
curl http://localhost:5000/health              # expect: {"status":"ok"}
kill %1
deactivate
cd -

# 3. ESP32 USB visible
ls /dev/ttyUSB0                                # expect: file exists

# 4. Pi reachable
ssh pi@<PI_IP> "echo Pi OK"                   # expect: Pi OK
```

---

## Stale Path Checklist

The following paths are hardcoded in source files and must match your session's actual IPs. Check them before every session:

| File | Hardcoded value | What it should be |
|---|---|---|
| `gateway/pi/iot_gateway_relay.py` line 5 | `UPSTREAM_HOST = "http://172.20.10.2:5000"` | Windows hotspot IP of new laptop |
| `esp32_firmware/*/main/http_request_example_main.c` | `WEB_SERVER "172.20.10.4"` | Pi IP (or direct laptop IP for direct mode) |
| `gateway/pi/iot_gateway_proposed.py` | `UPSTREAM_HOST` env var or hardcoded | Windows hotspot IP of new laptop |

Use `bash scripts/handoff/print_session_ips.sh` to see current compiled values, then use the `update_*.sh` scripts to change them.

---

## Avoiding Stale Paths When Moving Between Machines

The most common failure mode on a new laptop is a stale IP from the previous session still compiled into firmware. Firmware carries the IP at build time. If the IP changes but you flash an old binary, the ESP32 will try to reach the old IP and fail silently with `EHOSTUNREACH`.

Rule: **after any IP change, always rebuild the affected firmware before flashing**.

See `RUNTIME_REBINDING_GUIDE.md` for the full rebind workflow.
