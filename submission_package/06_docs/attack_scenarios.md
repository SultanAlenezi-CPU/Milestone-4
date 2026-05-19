# MITM Test Scenarios (Authorized Lab Only)

These scenarios are ONLY for testing on your own lab network with explicit authorization.

## Common Definitions
- **Secret material:** Wi-Fi credentials, tokens, long-term keys, certificates/private keys, session keys.
- **MITM success (general):** attacker achieves confidentiality breach, integrity breach, or unauthorized enrollment.

## Scenario A — Passive Sniffing
**Goal:** Determine if secrets can be observed in plaintext during onboarding.

### Steps (high-level)
1) Start onboarding normally.
2) Capture traffic at attacker node (pcap).
3) Inspect payloads for plaintext credentials/tokens.

### Pass/Fail
- **Success (attack succeeds):** any secret material appears in plaintext in the capture.
- **Fail (attack fails):** secrets are protected (encrypted / not present).

## Scenario B — Active Modification
**Goal:** Determine if an attacker can modify onboarding messages without detection.

### Steps (high-level)
1) Place attacker logically “in path” between DUT and gateway/cloud.
2) Attempt to modify onboarding parameters (e.g., SSID, token, key material).
3) Observe whether onboarding completes and whether logs show integrity/auth failures.

### Pass/Fail
- **Success:** modified values are accepted AND onboarding completes without detection.
- **Fail:** onboarding aborts, integrity check fails, or mutual auth blocks.

## Scenario C — Replay
**Goal:** Determine if previously captured onboarding messages can be replayed to achieve enrollment.

### Steps (high-level)
1) Capture a legitimate onboarding session.
2) Re-inject the same messages in a new session context.
3) Check if onboarding is accepted.

### Pass/Fail
- **Success:** replay leads to enrollment or credential acceptance.
- **Fail:** nonce/timestamp/session binding prevents replay.

## Scenario D — Rogue Enrollment
**Goal:** Determine if DUT can be enrolled by a fake gateway/cloud.

### Steps (high-level)
1) Attempt onboarding with a non-authorized enrollment endpoint.
2) Observe if DUT accepts the fake identity.

### Pass/Fail
- **Success:** DUT accepts fake gateway/cloud and stores credentials.
- **Fail:** identity verification blocks the attempt.

## Evidence Required Per Run
- pcap filename
- gateway log entry (JSON/CSV)
- DUT serial log snippet (timestamps + heap/crypto timings if available)
- outcome: mitm_success = 0/1 + notes
