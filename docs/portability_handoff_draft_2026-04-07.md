# Portability Handoff Draft — Proposed Method Testbed (2026-04-07)

## Purpose
This document captures what changes per session versus what is fixed, and provides a pre-flight checklist for anyone resuming work on this testbed in a new environment.

---

## What stays fixed across sessions

| Item | Fixed value | Location |
|:---|:---|:---|
| Pi IP on hotspot | `172.20.10.4` | DHCP-reserved or static on HUAWEI-B315-58AD hotspot |
| Pi gateway port | `8090` | `iot_gateway_proposed.py` hardcoded |
| Cloud emulator port | `5000` | `cloud_emulator/api/app.py` |
| ESP32 firmware target | `172.20.10.4:8090` | `http_request_example_main.c` defines `WEB_SERVER` / `WEB_PORT` |
| Device ID | `esp32_01` | Firmware define `DEVICE_ID` + `device_registry.json` |
| Device token | `proposed_dev_token_esp32_01_a1b2c3d4e5f6` | Firmware define `DEVICE_TOKEN` + `device_registry.json` |
| Session token TTL | 30 seconds | `iot_gateway_proposed.py` `TOKEN_TTL_S` |
| Firmware build system | ESP-IDF v5.5.3 at `~/esp-idf-v5.5.3` | (WSL-side) |
| ESP32 serial port | `/dev/ttyUSB0` | WSL USB passthrough; must be re-attached after host reboot |

---

## What changes per session

| Item | Changes because | How to resolve |
|:---|:---|:---|
| Windows hotspot IP (laptop end) | DHCP may reassign `.2` → `.3` etc. | Run subnet scan (see gateway runbook). Update `UPSTREAM_HOST` accordingly. |
| WSL internal IP | Assigned by WSL2 NAT on each WSL start | Not directly relevant — Pi must always use Windows hotspot IP, not WSL IP |
| Pi gateway process | Not persistent; stops on Pi reboot/crash | Follow `docs/gateway_restart_runbook_2026-04-07.md` |
| Cloud emulator process | Must be started manually in WSL | `cd cloud_emulator/api && python3 app.py` (or `flask run`) |
| ESP-IDF environment | Must be sourced each WSL session | `. ~/esp-idf-v5.5.3/export.sh` |
| `/dev/ttyUSB0` permissions | May revert to `crw-rw-r--` after reconnect | `sudo chmod 666 /dev/ttyUSB0` or add user to `dialout` group |
| usbipd attachment | Detaches on ESP32 unplug or host reboot | `usbipd attach --wsl --busid <ID>` from Windows PowerShell (admin) |

---

## Pre-flight checklist (start of every session)

### Windows side
- [ ] Hotspot active (HUAWEI-B315-58AD or current hotspot SSID)
- [ ] WSL running, WSL2 NAT active
- [ ] ESP32 plugged in via USB
- [ ] `usbipd attach --wsl --busid <ID>` run in PowerShell (admin) — verify with `usbipd list`

### WSL side
- [ ] Source IDF: `. ~/esp-idf-v5.5.3/export.sh`
- [ ] Confirm `/dev/ttyUSB0` exists: `ls -l /dev/ttyUSB0`
- [ ] Fix permissions if needed: `sudo chmod 666 /dev/ttyUSB0`
- [ ] Start cloud emulator: `cd ~/iot_onboarding/cloud_emulator/api && python3 app.py`
- [ ] Confirm emulator health: `curl -s http://localhost:5000/health`
- [ ] Discover current Windows hotspot IP: scan subnet (see gateway runbook)

### Pi side (SSH to `pi@172.20.10.4`)
- [ ] Confirm gateway not already running: `ss -tlnp | grep 8090`
- [ ] Start gateway with correct upstream:
  ```bash
  UPSTREAM_HOST=http://172.20.10.<X>:5000 python3 ~/gateway/pi/iot_gateway_proposed.py
  ```
- [ ] Smoke test auth: `curl -s -X POST http://localhost:8090/gateway/auth ...`

### ESP32 side
- [ ] Firmware already flashed (no rebuild needed unless code changed)
- [ ] To run: reset ESP32 (EN button or `idf.py monitor` then Ctrl-T Ctrl-R)
- [ ] Capture UART output: connect via `idf.py monitor` or pyserial capture script

---

## Environment dependencies that are not portable without changes

1. **Pi static IP `172.20.10.4`:** If the hotspot changes (different router, different SSID), the Pi IP assignment may change. The firmware `WEB_SERVER` define must be updated and reflashed.

2. **Hotspot subnet `172.20.10.x`:** The full `WEB_SERVER`, UPSTREAM_HOST pattern, and subnet scan script all assume this subnet. A different hotspot may use a different range.

3. **Device token hardcoded in firmware:** `DEVICE_TOKEN` in `http_request_example_main.c` must match the token in `device_registry.json` on the Pi. If the Pi registry is regenerated, the firmware must be reflashed with the matching token.

4. **No TLS in this testbed version:** All traffic is plaintext HTTP on the hotspot LAN. This is a documented testbed property, not an oversight. Adding TLS would require certificate provisioning for the Pi gateway and changes to both the gateway and firmware.

5. **Gateway session tokens are in-memory only:** If the gateway process restarts, all outstanding session tokens are invalidated. Any ESP32 mid-flow at the time of a gateway restart will get a 401 on Phase 2 and must be rebooted.

---

## Files that must be copied to a new Pi

| Source (repo) | Pi destination | Notes |
|:---|:---|:---|
| `gateway/pi/iot_gateway_proposed.py` | `~/gateway/pi/iot_gateway_proposed.py` | Main gateway service |
| `gateway/pi/device_registry.json` | `~/gateway/pi/device_registry.json` | Device credentials (not in repo if sensitive) |
| `gateway/pi/device_registry.example.json` | `~/gateway/pi/device_registry.example.json` | Safe example for reference |
| *(none)* | `~/gateway/logs/` | `mkdir -p ~/gateway/logs` on Pi |

Python version requirement: standard library only (no pip installs needed). Python 3.7+ required for `secrets` module and f-strings.

---

## Known operational limitations (honest scope)

- **Gateway process persistence:** Must be manually restarted. See `docs/gateway_restart_runbook_2026-04-07.md`.
- **No pcap canonical evidence:** Windows-side capture exists but is not validated as canonical. See `data/raw/proposed_p5_evidence_2026-04-07.md` pcap status section.
- **Certificate chain not independently verified:** The emulator returns `device_cert_pem` and `ca_cert_pem` fields; chain-of-trust to root CA has not been verified with `openssl verify` in this testbed phase.
- **Single-device registry:** Current `device_registry.json` has two entries (`esp32_01`, `esp32_02`). Multi-device simultaneous enrollment not tested.
