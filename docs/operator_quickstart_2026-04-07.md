# Operator Quickstart — 2026-04-07

Resume work fast. Do these in order.

---

1. **Windows:** Hotspot ON. ESP32 plugged in. `usbipd attach --wsl --busid <ID>` in PowerShell (admin).

2. **WSL:** `. ~/esp-idf-v5.5.3/export.sh` — source IDF environment.

3. **WSL:** Confirm ESP32 visible: `ls /dev/ttyUSB0` — fix perms if needed: `sudo chmod 666 /dev/ttyUSB0`

4. **WSL:** Start cloud emulator:
   ```bash
   cd /home/iot_onboarding/iot_onboarding/cloud_emulator/api && python3 app.py &
   ```

5. **WSL:** Find laptop hotspot IP (`172.20.10.<X>`):
   ```bash
   for ip in $(seq 2 14); do curl -s --connect-timeout 1 http://172.20.10.$ip:5000/health && echo " <- at $ip" & done; wait
   ```

6. **Pi** (`ssh pi@172.20.10.4`): Start gateway (replace `<X>`):
   ```bash
   UPSTREAM_HOST=http://172.20.10.<X>:5000 python3 ~/gateway/pi/iot_gateway_proposed.py &
   ```

7. **WSL:** Confirm stack: `curl -s http://172.20.10.4:8090/health` → HTTP 200.

8. **WSL:** Open monitor **before** resetting ESP32:
   ```bash
   cd /home/iot_onboarding/iot_onboarding/esp32_firmware/proposed_gateway && idf.py monitor
   ```

9. **ESP32:** Press EN. Watch for `result=PASS` in monitor output.

10. **If PASS:** Proceed. **If FAIL:** Check gateway (step 6), emulator (step 4), then `docs/another_laptop_migration_checklist_2026-04-07.md` section 8.

---

**Full docs:**
- Migration: `docs/another_laptop_migration_checklist_2026-04-07.md`
- Session values: `docs/runtime_values_worksheet_2026-04-07.md`
- Gateway restart: `docs/gateway_restart_runbook_2026-04-07.md`
- New chat prompt: `docs/new_chat_handoff_prompt_m4_portability_2026-04-07.md`
