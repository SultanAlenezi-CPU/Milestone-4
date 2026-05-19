# Baseline 2 — Token Alignment and First Run Procedure

## Overview

Baseline 2 uses a pre-shared provisioning token per run. The token is placed
in the ESP32 firmware array and must match an entry in the emulator's token store
before each session. This document explains where the tokens live and how to keep
them aligned.

---

## Where Tokens Live

### 1. ESP32 firmware (source — must be rebuilt to change)

```
esp32_firmware/baseline2_token/main/http_request_example_main.c
```

Token array, lines ~46–56:
```c
static const char *TOKENS[RUNS] = {
    "a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4",  /* run 1  */
    "b2e8d1f4a7c3e9b0d5f2a1e7c4b9f3a2",  /* run 2  */
    ...
};
```

Each token is consumed exactly once. `run 1` uses `TOKENS[0]`, `run 2` uses `TOKENS[1]`, etc.

### 2. Cloud emulator token store (runtime — no rebuild needed to change)

Runtime file (NOT committed — generate each session):
```
cloud_emulator/api/b2_tokens.json
```

Template (committed — safe example values):
```
cloud_emulator/api/b2_tokens.example.json
```

Format:
```json
{
  "tokens": {
    "a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4": {"used": false},
    ...
  }
}
```

The emulator loads this file **once at startup** into memory. Tokens mark
themselves as used in memory; the file itself is not rewritten during a run.
Restart the emulator to reset all tokens to unused.

---

## Token Alignment Procedure

### Option A — Use the example tokens (quickest for dev/testing)

Both the firmware array and `b2_tokens.example.json` already have the same
10 tokens. No change needed if using the example file:

```bash
# On laptop (in cloud_emulator/api/):
cp b2_tokens.example.json b2_tokens.json
# start emulator normally — it loads b2_tokens.json automatically
```

Firmware already has the matching tokens compiled in. Just build and flash.

### Option B — Fresh tokens for a real experiment session

1. Generate 10 new tokens:
   ```bash
   python3 -c "import secrets; [print(secrets.token_hex(16)) for _ in range(10)]"
   ```

2. Create `b2_tokens.json` with the new tokens:
   ```json
   {
     "tokens": {
       "<token1>": {"used": false},
       "<token2>": {"used": false},
       ...
     }
   }
   ```

3. Update the firmware array to match (same 10 tokens in the same order):
   ```c
   static const char *TOKENS[RUNS] = {
       "<token1>",   /* run 1  */
       "<token2>",   /* run 2  */
       ...
   };
   ```

4. Rebuild firmware:
   ```bash
   cd esp32_firmware/baseline2_token
   idf.py build
   ```

5. Record the token set used in `data/raw/b2_token_session_<date>.txt`
   (for reproducibility — these are test tokens, not real secrets).

---

## IP Alignment Procedure

Before building, verify `WEB_SERVER` and `WEB_PORT` match the current session:

```bash
grep -E "#define WEB_SERVER|#define WEB_PORT" \
  esp32_firmware/baseline2_token/main/http_request_example_main.c
```

To update (use the handoff helper scripts):
```bash
# Direct path (laptop):
bash scripts/handoff/update_b2_target.sh <laptop_ip> 5000 /provision

# Via Pi relay:
bash scripts/handoff/update_b2_target.sh <pi_ip> 8080 /provision
```

*(Note: `update_b2_target.sh` does not yet exist — use `update_b1_target.sh` as
a reference or edit the define manually for the first run. A dedicated B2 script
can be added in the handoff scripts pass.)*

---

## Emulator Startup Sequence

```bash
cd cloud_emulator/api
cp b2_tokens.example.json b2_tokens.json   # or use Option B for fresh tokens
source .venv/bin/activate
python app.py
# Logs go to logs/provision_log.jsonl
```

Verify the emulator is up:
```bash
curl -s http://localhost:5000/health
# Expected: {"status":"ok"}
```

Test one provision call:
```bash
curl -s -X POST http://localhost:5000/provision \
  -H "Content-Type: application/json" \
  -d '{"run_id":"1","device_id":"esp32_01","token":"a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4"}'
# Expected: {"device_id":"esp32_01","provisioning_status":"ok","run_id":"1"}
```

---

## Expected Serial Output (PASS run)

```
I (...) example_connect: ...  address: 172.20.10.x
Generating token request for run 1...        ← (not printed by firmware; token is internal)
I (...) example: DNS lookup succeeded. IP=172.20.10.x
I (...) example: ... connected
I (...) example: ... socket send success
HTTP/1.0 200 OK
...
{"device_id":"esp32_01","provisioning_status":"ok","run_id":"1"}
MEASURE run_id=1 heap_before=... heap_after=... heap_delta=... start_ms=... end_ms=... latency_ms=... http_status=200
...
I (...) example: MEASURE runs_done=10
```

## Expected Serial Output (FAIL — token already used or wrong token)

```
HTTP/1.0 401 UNAUTHORIZED
...
{"error":"invalid or expired token"}
MEASURE run_id=1 ... http_status=401
```

A 401 on any run indicates token mismatch. Check that firmware TOKENS[] and
`b2_tokens.json` are aligned, and that the emulator was restarted to clear
the used-token state.
