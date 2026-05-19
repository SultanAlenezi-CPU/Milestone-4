# B2 Replay MITM Evidence — 2026-04-06

## Scenario
Replay attack against Baseline 2 token provisioning through the Pi relay path.

## Setup
- Method: B2 token provisioning via Pi relay
- Relay endpoint: http://172.20.10.4:8080/provision
- Device ID used: esp32_01
- Replay token used: a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4
- Fresh emulator token state was loaded before the scenario

## First request
- Request type: POST /provision
- run_id: 101
- Expected result: HTTP 200
- Observed result: HTTP 200
- Body: {"device_id":"esp32_01","provisioning_status":"ok","run_id":"101"}

## Replay request
- Request type: identical POST /provision replayed immediately
- run_id: 101_replay
- Expected result: HTTP 401
- Observed result: HTTP 401 Unauthorized
- Body: {"error":"invalid or expired token"}

## Server log confirmation
The server-side provision log recorded:
- first request: token_known=true, token_used_before=false, token_valid=true, status_code=200
- replay request: token_known=true, token_used_before=true, token_valid=false, status_code=401

## Conclusion
This practical replay scenario confirms that Baseline 2 rejects reuse of an already-consumed provisioning token.
The scenario demonstrates replay resistance for single-use tokens, while not changing the broader fact that B2 still relies on plaintext token transport and therefore remains weaker than stronger onboarding approaches.

## Supporting artifacts
- capture/b2_replay_scenario_2026-04-06.txt
- cloud_emulator/api/logs/provision_log.jsonl
- capture/b2_via_pi_minfix_2026-04-06.txt
- capture/b2_via_pi_clean_2026-04-06_final.txt
