# Next Execution Path

**What to do next, in what order, and what done looks like.**
This file is deliberately short. Read `HANDOVER_MASTER.md` for context.

---

## Priority Order

### Step 1 — Fix the known report error (5 minutes, no hardware needed)

File: `docs/report_patch_proposed_p5_2026-04-07.md`

Find: `~1254 ms`
Replace with: `1375.2 ms`

Find: `~1.6×`
Replace with: `~1.45×`

**Why:** The 1254 value is wrong. Correct B3 mean is 1375.2 ms (verified from `final_results.csv` rows 16–20). Every downstream report document that cites this comparison ratio is affected.

**Done when:** The string "1254" no longer appears in any report-facing document.

---

### Step 2 — Update README milestone table (5 minutes, no hardware needed)

File: `README.md`

Update M4 row status from `"First checkpoint complete (2026-04-05); pcap/dataset/report integration pending"` to `"Complete — 5/5 PASS for all baselines and Proposed Method; dataset integrated"`.

**Done when:** README accurately reflects that Proposed Method has canonical evidence and is in the CSVs.

---

### Step 3 — B2 clean 10/10 re-run (requires ESP32 + Pi + hotspot)

**Why:** B2 client-side currently shows 7/10 PASS. The 8 s receive timeout fix is already compiled into `esp32_firmware/baseline2_token/main/http_request_example_main.c`. A clean run is needed to confirm the fix works and produce canonical B2 data.

**Steps:**

1. Start hotspot. Boot Pi. Connect laptop to hotspot.
2. Discover IPs: `bash scripts/handoff/print_session_ips.sh`
3. Rebind if IPs changed: see `RUNTIME_REBINDING_GUIDE.md`
4. Start cloud emulator:
   ```bash
   cd cloud_emulator/api && source .venv/bin/activate && python app.py
   ```
5. Verify token store is reset (server restart resets in-memory tokens to unused):
   ```bash
   curl -s http://localhost:5000/health  # confirm emulator is up
   ```
   Tokens reset on every restart — 10 fresh tokens are available for each new run.
6. Start Pi relay via SSH:
   ```bash
   ssh pi@172.20.10.4 "python3 ~/iot_gateway_relay.py"
   ```
7. Attach ESP32 via usbipd (Windows PowerShell then WSL):
   ```
   usbipd attach --wsl --busid <BUSID>
   ls /dev/ttyUSB0
   ```
8. Build B2 firmware (only if IP has changed — no rebuild needed if target is still Pi:8080):
   ```bash
   cd esp32_firmware/baseline2_token
   idf.py build
   ```
9. Flash and monitor:
   ```bash
   idf.py -p /dev/ttyUSB0 flash monitor
   ```
10. Press EN button. Watch for 10 MEASURE lines. All 10 must show `http_status=200`.
11. Copy the UART output. Save it to `capture/b2_via_pi_clean_FINAL_<date>.txt`.

**Done when:** UART shows 10 consecutive MEASURE lines with `http_status=200 result=PASS`.

---

### Step 4 — Integrate B2 results into CSVs (no hardware needed)

After Step 3, add 10 rows to `data/processed/final_results.csv`.

Schema: `run_id,baseline,latency_ms,heap_delta,http_status,result,notes`

Use run_id 26–35. Baseline = `B2`. Notes = `b2_via_pi_FINAL_<date>`.

Also add matching rows to `data/processed/results.csv` if you want that file kept current.

**Done when:** `final_results.csv` has 35 rows (25 existing + 10 new B2 rows).

---

### Step 5 — Assemble final report DOCX (no hardware needed)

Source files (read in this order):
1. `docs/protocol_lock_full_scope_2026-04-06.md` → Ch. 4/5 protocol design
2. `docs/report_patch_b1_rerun_2026-04-05.md` → §7.3 B1 table
3. `docs/report_patch_b3_rerun_2026-04-05.md` → §7.3 B3 table
4. `docs/report_patch_proposed_p5_2026-04-07.md` (after Step 1 fix) → §7.4 Proposed

Figures: all 11 PNGs from `report_assets/ch7_visuals/`. Windows path:
`\\wsl$\Ubuntu\home\iot_onboarding\iot_onboarding\report_assets\ch7_visuals\`

**Done when:** DOCX has cover page, all chapter text, all 11 figures embedded, and exports cleanly to PDF.

---

### Step 6 — Create defense slides (no hardware needed)

No starting point exists. Build from scratch in PowerPoint or Google Slides.
Minimum 10 slides. Copy topology figure and latency chart directly from `report_assets/ch7_visuals/`.

**Done when:** `.pptx` file exists in the repo or submission package.

---

## What to Postpone

- **B2 MITM scenarios A, B, D** — passive sniff, modification, rogue server. These are defined in `attacks/scenarios.md` but not executed. Not required for graduation submission; document as future work.
- **Real pcap collection** — `capture/pcaps/` is empty. Figs 7.2/7.3 use programmatic renders. A real pcap would strengthen the evidence but is not on the critical path.

---

## What "Done" Looks Like for Submission

- [ ] `data/processed/final_results.csv` has B2 rows (or a written acknowledgment of the limitation)
- [ ] No report file cites "1254 ms" as B3 mean
- [ ] README milestone table is accurate
- [ ] Final report PDF exists and includes all 11 figures
- [ ] Defense slides PPTX exists
- [ ] Signed university submission form completed
- [ ] `submission_package/` is current (rerun the copy steps if any files changed)
