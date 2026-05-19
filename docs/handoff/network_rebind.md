# Network Rebind Guide — What Changes When IPs Change

IPs assigned by the phone hotspot DHCP are not persistent.
A different phone, a different laptop, or a DHCP lease renewal can change them.
This document is the authoritative reference for which files must be updated
and what commands to use.

---

## What Each IP Controls

### Laptop IP (cloud emulator host)

The laptop runs the cloud emulator on port 5000, bound to `0.0.0.0`. Its hotspot IP
must be known to:

1. **The Pi relay script** — `UPSTREAM_HOST` in `gateway/pi/iot_gateway_relay.py`
   tells the relay where to forward requests.
2. **ESP32 firmware** — when running in *direct mode* (no Pi), `WEB_SERVER` in
   the firmware points directly at the laptop.

### Pi IP (relay/gateway node)

The Pi runs the relay on port 8080. Its hotspot IP must be known to:

1. **ESP32 firmware** — when running in *via-Pi mode*, `WEB_SERVER` in the
   firmware points at the Pi.

---

## Change Matrix

| Component | File (repo-relative) | Setting | Update when |
|-----------|---------------------|---------|-------------|
| Pi relay upstream | `gateway/pi/iot_gateway_relay.py` | `UPSTREAM_HOST` (line 5) | Laptop IP changes |
| B1 firmware — direct | `esp32_firmware/baseline1_http/main/http_request_example_main.c` | `WEB_SERVER`, `WEB_PORT`, `WEB_PATH` | Switching to direct mode OR laptop IP changes in direct mode |
| B3 firmware — direct | `esp32_firmware/baseline3_enroll/main/http_request_example_main.c` | `WEB_SERVER`, `WEB_PORT`, `WEB_PATH` | Switching to direct mode OR laptop IP changes in direct mode |
| B1 firmware — via Pi | `esp32_firmware/baseline1_http/main/http_request_example_main.c` | `WEB_SERVER`, `WEB_PORT`, `WEB_PATH` | Pi IP changes |
| B3 firmware — via Pi | `esp32_firmware/baseline3_enroll/main/http_request_example_main.c` | `WEB_SERVER`, `WEB_PORT`, `WEB_PATH` | Pi IP changes |

**Ports are stable** — the emulator always listens on 5000, the Pi relay always on 8080.
Only the IP component changes between sessions.

---

## Current Configured Values (as of last commit)

```
B1 WEB_SERVER = "172.20.10.4"   (Pi IP — via-Pi mode)
B1 WEB_PORT   = "8080"
B1 WEB_PATH   = "/health"

B3 WEB_SERVER = "172.20.10.4"   (Pi IP — via-Pi mode)
B3 WEB_PORT   = "8080"
B3 WEB_PATH   = "/enroll"

Pi relay UPSTREAM_HOST = "http://172.20.10.2:5000"   (laptop IP)
```

These values are session-specific. Verify with:
```bash
bash scripts/handoff/print_session_ips.sh
```

---

## Rebind Workflow

### Step 1 — Discover current laptop IP (in WSL)

```bash
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
# or: hostname -I | awk '{print $1}'
```

### Step 2 — Discover current Pi IP

```bash
# Scan local subnet (adjust prefix to match your hotspot range):
nmap -sn 172.20.10.0/28 2>/dev/null | grep -A1 "Raspberry"

# Or from a direct Pi terminal session:
ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
```

### Step 3 — Update Pi relay upstream (if laptop IP changed)

```bash
bash scripts/handoff/update_pi_relay_upstream.sh <new_laptop_ip> 5000
```

Then re-deploy to Pi and restart relay:
```bash
scp gateway/pi/iot_gateway_relay.py pi@<PI_IP>:~/iot_gateway_relay.py
ssh pi@<PI_IP> "pkill -f iot_gateway_relay.py; python3 ~/iot_gateway_relay.py &"
```

### Step 4 — Update B1 target (if running via Pi and Pi IP changed)

```bash
bash scripts/handoff/update_b1_target.sh <new_pi_ip> 8080 /health
```

### Step 5 — Update B3 target (if running via Pi and Pi IP changed)

```bash
bash scripts/handoff/update_b3_target.sh <new_pi_ip> 8080 /enroll
```

### Step 6 — Rebuild firmware (only if a define changed)

```bash
cd esp32_firmware/baseline1_http  && idf.py build
cd esp32_firmware/baseline3_enroll && idf.py build
```

A rebuild is only needed if `WEB_SERVER`, `WEB_PORT`, or `WEB_PATH` changed.
If only the Pi relay upstream changed, only the relay script needs redeploying —
no firmware rebuild required.

### Step 7 — Flash (only if firmware was rebuilt)

```bash
idf.py -p /dev/ttyUSB0 flash
```

---

## Mode Reference

| Mode | B1/B3 WEB_SERVER | B1/B3 WEB_PORT | Pi relay needed |
|------|-----------------|----------------|-----------------|
| Direct (no Pi) | Laptop hotspot IP | 5000 | No |
| Via Pi (M4) | Pi hotspot IP | 8080 | Yes |

---

## Notes

- The cloud emulator is bound to `0.0.0.0:5000`, so it is reachable on all
  network interfaces including the hotspot interface — no extra binding needed.
- The Pi relay is bound to `0.0.0.0:8080`, same principle.
- WSL2 does NOT have a routable IP from the LAN by default (WSL2 NAT). The
  cloud emulator must run on the Windows host or on the Pi if direct ESP32
  access is needed from outside WSL. For the current setup, the emulator runs
  inside WSL but is reachable because Windows forwards ports from the hotspot
  interface to WSL automatically for `0.0.0.0`-bound services on port 5000.
  If it is not reachable, run the emulator on Windows directly:
  `python cloud_emulator/api/app.py` in a Windows terminal with Python installed.
