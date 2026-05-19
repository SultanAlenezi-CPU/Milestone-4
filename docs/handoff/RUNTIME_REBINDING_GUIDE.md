# Runtime Rebinding Guide

**Read this at the start of every session, and whenever you switch phones or laptops.**

IPs assigned by the phone hotspot DHCP are not persistent. A different phone,
a different laptop, or simply a DHCP lease renewal can assign different addresses.
This guide tells you exactly which files to update and in what order.

---

## What IPs Control What

### Laptop IP (cloud emulator host)
The laptop runs `cloud_emulator/api/app.py` on port 5000, bound to `0.0.0.0`.
Its hotspot IP must be known to:

1. **`gateway/pi/iot_gateway_relay.py`** — `UPSTREAM_HOST` tells the relay where to forward traffic.
2. **`gateway/pi/iot_gateway_proposed.py`** — `UPSTREAM_HOST` env var (or hardcoded fallback) for the proposed gateway.
3. **ESP32 firmware** — only in **direct mode** (no Pi). If going direct, `WEB_SERVER` in the firmware must be the laptop hotspot IP.

> **WSL2 NAT caveat:** The Pi cannot reach the WSL internal IP (eth0, usually `172.x.x.x` inside WSL).
> Always use the **Windows hotspot IP** (visible on the hotspot adapter, or discovered from inside WSL with `ip route show | grep default`).
> The cloud emulator binds to `0.0.0.0` so it IS reachable on the Windows interface.

### Pi IP (gateway/relay host)
The Pi runs the relay (port 8080) and/or proposed gateway (port 8090).
Its hotspot IP must be known to:

1. **ESP32 firmware** — `WEB_SERVER` is the Pi IP when running via-Pi mode (the normal mode).

### ESP32 IP
The ESP32 IP is generally not needed by any other component. You do not configure it anywhere.
It is useful to know for debugging (check hotspot admin page or `nmap`).

---

## Step-by-Step Rebind Checklist

Run through this at the start of every session.

### 1. Discover current IPs

```bash
# Laptop IP in WSL (hotspot interface — look for the 172.20.10.x address)
ip addr show | grep "inet 172"
# or
hostname -I

# Also check the Windows hotspot IP (run in PowerShell or cmd.exe):
# ipconfig | findstr "172.20"
```

```bash
# Pi IP — scan the hotspot subnet
for i in $(seq 1 14); do
  ping -c1 -W1 172.20.10.$i &>/dev/null && echo "172.20.10.$i alive" &
done; wait
```

Or SSH to the Pi if you know an old IP that might still work:
```bash
ssh pi@172.20.10.4 "ip addr show wlan0 | grep inet"
```

Or from the Pi directly (if you have keyboard access):
```bash
ip addr show wlan0 | grep "inet "
```

### 2. Check current compiled values

```bash
bash scripts/handoff/print_session_ips.sh
```

This shows what IP is currently compiled into each firmware project and what the Pi relay points to.

### 3. Update Pi relay upstream (if laptop IP changed)

```bash
bash scripts/handoff/update_pi_relay_upstream.sh <NEW_LAPTOP_IP> 5000
```

This edits `gateway/pi/iot_gateway_relay.py` in place.
After editing, copy the updated file to the Pi:
```bash
scp gateway/pi/iot_gateway_relay.py pi@<PI_IP>:~/
```

For the proposed gateway, set the env var at start time instead of editing the file:
```bash
ssh pi@<PI_IP> "UPSTREAM_HOST=http://<NEW_LAPTOP_IP>:5000 python3 ~/iot_gateway_proposed.py"
```

### 4. Update firmware target (if Pi IP changed, or if switching direct/via-Pi)

**Via Pi (normal mode) — B1, B2, B3:**
```bash
bash scripts/handoff/update_b1_target.sh <PI_IP> 8080 /health
bash scripts/handoff/update_b3_target.sh <PI_IP> 8080 /enroll
# For B2: manually edit esp32_firmware/baseline2_token/main/http_request_example_main.c
# Change WEB_SERVER and WEB_PORT on lines 34–35
```

**Direct to emulator (no Pi) — B1, B3:**
```bash
bash scripts/handoff/update_b1_target.sh <LAPTOP_HOTSPOT_IP> 5000 /health
bash scripts/handoff/update_b3_target.sh <LAPTOP_HOTSPOT_IP> 5000 /enroll
```

**Proposed firmware — always targets Pi:8090:**
```bash
# Edit esp32_firmware/proposed_gateway/main/http_request_example_main.c
# Lines 43–44:
#   #define WEB_SERVER    "<PI_IP>"
#   #define WEB_PORT      "8090"
```

### 5. Rebuild affected firmware

You must rebuild firmware after any IP change. Flashing an old binary will use the old IP.

```bash
cd esp32_firmware/baseline1_http  && idf.py build
cd esp32_firmware/baseline2_token && idf.py build
cd esp32_firmware/baseline3_enroll && idf.py build
cd esp32_firmware/proposed_gateway && idf.py build
```

Only rebuild the projects whose target IP changed.

### 6. Verify the chain before flashing

```bash
bash scripts/handoff/verify_runtime_chain.sh
```

Or manually:
```bash
# Emulator up?
curl -s http://localhost:5000/health

# Pi reachable from WSL?
ssh pi@<PI_IP> "echo Pi OK"

# Pi relay reaches emulator?
ssh pi@<PI_IP> "curl -s http://<LAPTOP_HOTSPOT_IP>:5000/health"

# Pi relay up (port 8080)?
curl -s http://<PI_IP>:8080/health

# Pi proposed gateway up (port 8090)?
curl -s http://<PI_IP>:8090/health
```

All health checks must return `{"status":"ok"}` or `{"status":"ok","service":"..."}` before flashing.

---

## "Same Hotspot, Different Phone" Scenario

**This is a real and expected future use case.**

When the hotspot phone changes:
- The SSID and password stay the same (HUAWEI-B315-58AD).
- All devices (ESP32, Pi, laptop) rejoin the same Wi-Fi name.
- The DHCP server is different — IP addresses WILL change.
- The subnet may also change (e.g., from 172.20.10.x to 192.168.43.x).

**Procedure:**
1. Power everything off. Swap phone. Start new hotspot.
2. Connect laptop to new hotspot Wi-Fi.
3. Discover new laptop IP: `ip addr show | grep inet`
4. Discover new Pi IP: scan the new subnet.
5. Determine new subnet: `ip route show | grep default` to find the gateway, then derive the /24 or /28.
6. Update all IP references as in the checklist above.
7. If the **subnet** changed (not just the host part of the IP), you also need to update any IP ranges in documentation — but not in firmware (firmware only cares about the specific IP, not the subnet).
8. Rebuild all firmware. Redeploy relay script to Pi.

**Specific to subnet change:**
If the new subnet is different (e.g., 192.168.43.x), replace every occurrence of the old subnet in:
- `gateway/pi/iot_gateway_relay.py` (`UPSTREAM_HOST`)
- All four firmware `.c` files (`WEB_SERVER`)
- `docs/handoff/session_checklist.md` discovery examples (not functional, but keep accurate)

The `print_session_ips.sh` and `update_*.sh` scripts work regardless of subnet — just pass the new IPs.

---

## Files That Contain Hardcoded IPs (Full List)

| File | Line | Variable | Current value | Update with |
|---|---|---|---|---|
| `gateway/pi/iot_gateway_relay.py` | 5 | `UPSTREAM_HOST` | `http://172.20.10.2:5000` | `update_pi_relay_upstream.sh` |
| `esp32_firmware/baseline1_http/main/http_request_example_main.c` | 27 | `WEB_SERVER` | `"172.20.10.4"` | `update_b1_target.sh` |
| `esp32_firmware/baseline2_token/main/http_request_example_main.c` | 34 | `WEB_SERVER` | `"172.20.10.4"` | Edit manually |
| `esp32_firmware/baseline3_enroll/main/http_request_example_main.c` | 35 | `WEB_SERVER` | `"172.20.10.4"` | `update_b3_target.sh` |
| `esp32_firmware/proposed_gateway/main/http_request_example_main.c` | 43 | `WEB_SERVER` | `"172.20.10.4"` | Edit manually |
| `gateway/pi/iot_gateway_proposed.py` | env var | `UPSTREAM_HOST` | default `http://127.0.0.1:5000` | Set env var at start |

No other source files contain hardcoded IPs. Documentation files reference last-session IPs for illustration only — they are not functional.
