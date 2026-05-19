# Handover Export Note

**What to copy to another machine, and what to exclude.**

---

## Preferred Transfer Method

Copy the entire repo as a tar archive, excluding venvs and build artifacts:

```bash
# Run from the parent directory of the repo (e.g., /home/iot_onboarding)
cd /home/iot_onboarding

tar \
  --exclude='iot_onboarding/cloud_emulator/api/.venv' \
  --exclude='iot_onboarding/venv' \
  --exclude='iot_onboarding/esp32_firmware/baseline1_http/build' \
  --exclude='iot_onboarding/esp32_firmware/baseline2_token/build' \
  --exclude='iot_onboarding/esp32_firmware/baseline3_enroll/build' \
  --exclude='iot_onboarding/esp32_firmware/proposed_gateway/build' \
  --exclude='iot_onboarding/**/__pycache__' \
  --exclude='iot_onboarding/.claude' \
  --exclude='iot_onboarding/ai' \
  -czf iot_onboarding_handoff_$(date +%Y%m%d).tar.gz iot_onboarding/

ls -lh iot_onboarding_handoff_*.tar.gz
```

Expected archive size: ~3–8 MB (excludes venvs which total ~330 MB and build artifacts).

Transfer the archive via USB drive, scp, or any file transfer method available.

---

## Unpack on the New Machine

```bash
# Place in the new user's home directory inside WSL
mkdir -p /home/<new_user>
tar -xzf iot_onboarding_handoff_YYYYMMDD.tar.gz -C /home/<new_user>/
cd /home/<new_user>/iot_onboarding
ls   # verify repo contents
```

---

## What is Included

- All source code (firmware, cloud emulator, gateway scripts)
- All UART captures (`capture/`)
- All server logs (`cloud_emulator/api/logs/`, `gateway/logs/`)
- All evidence notes (`data/raw/`)
- All processed CSVs (`data/processed/`)
- All report patches and documentation (`docs/`)
- All generated figures (`report_assets/ch7_visuals/`)
- Submission package (`submission_package/`)
- sdkconfig files (contain Wi-Fi password — do not share publicly)

---

## What is NOT Included (by the exclude flags above)

| Excluded | Why |
|---|---|
| `cloud_emulator/api/.venv/` | 42 MB Python venv — recipient recreates with `pip install -r requirements.txt` |
| `venv/` | 288 MB — unused root-level venv |
| `esp32_firmware/*/build/` | Build artifacts — recreated with `idf.py build` |
| `**/__pycache__/` | Python bytecode — auto-generated |
| `.claude/` | IDE tool settings — machine-specific |
| `ai/` | Internal session planning notes — not a project deliverable |

---

## What Must Be Transferred Separately (Sensitive)

These files are NOT in VCS and must be handled carefully:

| File | Sensitivity | How to transfer |
|---|---|---|
| `cloud_emulator/pki/ca.key` | **CA private key** — can sign device certs | Copy via encrypted channel only. Store offline. |
| `esp32_firmware/*/sdkconfig` | Contains Wi-Fi password | Included in the tar above — do not share the tar publicly |
| `cloud_emulator/api/b2_tokens.json` | Session token store | Included in tar; not a real secret but session-specific |

If sharing the archive publicly or with a third party, re-run the tar with additional excludes:
```bash
--exclude='iot_onboarding/cloud_emulator/pki/ca.key' \
--exclude='iot_onboarding/esp32_firmware/*/sdkconfig' \
--exclude='iot_onboarding/cloud_emulator/api/b2_tokens.json'
```

---

## Files That Are Untracked in Git

Many important files are untracked (marked `??` in `git status`). They exist on disk
but would NOT be included in a `git clone`. The tar archive method above includes them.

Key untracked files:
```
capture/b2_direct_clean_2026-04-06.txt
capture/b2_via_pi_clean_2026-04-06_final.txt
capture/b2_replay_scenario_2026-04-06.txt
capture/proposed_p5_repeated_runs_latest.txt
(+ all other capture/ files)
data/raw/proposed_p5_evidence_2026-04-07.md
data/raw/b2_replay_mitm_2026-04-06_evidence.md
data/processed/proposed_p5_runpack_2026-04-07.csv
cloud_emulator/api/logs/provision_log.jsonl
gateway/logs/proposed_gateway_log.jsonl
gateway/pi/iot_gateway_proposed.py
gateway/pi/device_registry.example.json
docs/handoff/HANDOVER_MASTER.md       ← this handover bundle
(+ all other docs/handoff/ files created in this pass)
esp32_firmware/baseline2_token/       ← entire B2 firmware project
esp32_firmware/proposed_gateway/      ← entire Proposed firmware project
report_assets/                        ← all generated figures
submission_package/                   ← submission package
```

If using `git clone` instead of the tar method, you must manually transfer all of the above after cloning.

---

## After Unpacking — First Steps

1. Set up the Python venv: `cd cloud_emulator/api && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. Restore `ca.key` to `cloud_emulator/pki/ca.key`
3. Re-configure Wi-Fi in firmware: `idf.py menuconfig` in each firmware project
4. Install ESP-IDF v5.5.3 if not already installed
5. Install usbipd-win on Windows
6. Follow `SETUP_ON_ANOTHER_LAPTOP.md` for the complete checklist

---

## No Assumptions About External Storage

This note does not assume USB drives, cloud storage, or any specific transfer mechanism.
Use whatever secure channel is available. The archive is self-contained once the sensitive
files are included.
