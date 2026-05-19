# Report Patch — Baseline 3 Live Rerun (2026-04-05)
## Sections Affected: 7.3, 7.3.2, Table 7.5, Table 7.6, Table 7.7, Figure 7.6 caption, 7.6 Discussion

**Purpose:** This patch supersedes any earlier B3 values in the draft report with the
accepted controlled live rerun data from 2026-04-05. Earlier B3 rows in the draft may
have used values from the Mar 4, 2026 session (latencies 1,051–1,654 ms, from
`data/raw/b3_uart_5runs.log`). Those values are superseded by the accepted rerun below
throughout Sections 7.3, 7.3.2, Table 7.6, and relevant discussion paragraphs.

**Evidence basis:**
- Server-side log: `cloud_emulator/api/logs/enroll_log.jsonl` — 5 POST /enroll entries
  on 2026-04-05 18:51:10–21 UTC, run_id 1–5, device_id esp32_01, all HTTP 200
- Evidence note: `data/raw/b3_live_rerun_2026-04-05_evidence.md`
- Processed dataset: `data/processed/final_results.csv` rows 16–20
- Raw UART log for this rerun: **not preserved** — see evidence note for details
- Packet capture: **not yet collected** (pending). The security discussion of plaintext
  HTTP observability must be framed as a protocol-level property, not cited as
  "confirmed by pcap for this rerun", until a pcap is stored in `capture/pcaps/`.
- Certificate chain full verification (chain-of-trust to root): not independently
  verified in this phase beyond the emulator returning `device_cert_pem` and `ca_cert_pem`
  fields with HTTP 200. The CA signing step is confirmed by the emulator logic in
  `cloud_emulator/api/app.py`.

---

## Accepted B3 Rerun Values (use these everywhere in the report)

### Raw Measurements

| Run | Latency (ms) | heap_before (B) | heap_after (B) | heap_delta (B) | HTTP Status | Result |
|-----|-------------|-----------------|----------------|----------------|-------------|--------|
| 1   | 1,782       | 200,908         | 204,656        | +3,748         | 200         | PASS   |
| 2   | 1,142       | 205,088         | 204,660        | −428           | 200         | PASS   |
| 3   | 1,554       | 205,088         | 204,672        | −416           | 200         | PASS   |
| 4   | 1,147       | 205,088         | 204,672        | −416           | 200         | PASS   |
| 5   | 1,251       | 205,088         | 204,672        | −416           | 200         | PASS   |

### Summary Statistics

| Statistic              | Value      |
|------------------------|------------|
| Mean latency           | 1,375.2 ms |
| Median latency         | 1,251 ms   |
| Std Dev (sample, n=5)  | 282.5 ms   |
| Min latency            | 1,142 ms   |
| Max latency            | 1,782 ms   |
| Mean heap delta        | +414.4 B   |
| HTTP success rate      | 5/5 (100%) |
| Endpoint               | http://172.20.10.2:5000/enroll |
| device_id              | esp32_01   |
| Network context        | Phone hotspot (HUAWEI-B315-58AD), 2026-04-05 |

---

## Section 7.3 — Experimental Results (B3 data-source paragraph replacement)

> Locate the paragraph in Section 7.3 that identifies the data source for Baseline 3
> and replace with the following:

Baseline 3 results are drawn from a controlled live rerun conducted on 2026-04-05 using
the ESP32 firmware built from `esp32_firmware/baseline3_enroll` (ESP-IDF v5.5.3) and the
cloud emulator running at `http://172.20.10.2:5000`. The experiment was performed over a
phone hotspot (SSID: HUAWEI-B315-58AD) acting as the local network path between the DUT
and the emulator host. All five runs completed successfully (5/5 PASS) with HTTP 200
responses and certificate issuance confirmed in the emulator log
(`cloud_emulator/api/logs/enroll_log.jsonl`). The emulator response included
`device_cert_pem` and `ca_cert_pem` fields for each run, confirming CA signing of the
device CSR. Full UART session data was not captured for this rerun; the server-side log
and accepted run summary are the primary evidence. Packet capture evidence for this rerun
is pending; the plaintext HTTP observability argument is addressed as a protocol-level
property in Section 7.6.

---

## Table 7.5 — Evidence Reference Update (B3 row)

> Update the B3 row in Table 7.5 as follows:

| Baseline | Evidence Artifact | Status |
|----------|------------------|--------|
| B3       | `cloud_emulator/api/logs/enroll_log.jsonl` (5 /enroll entries, 2026-04-05 18:51 UTC) | Server-side log, 2026-04-05 |
| B3       | `data/raw/b3_live_rerun_2026-04-05_evidence.md` | Evidence note, 2026-04-05 |
| B3       | Raw UART log for this rerun | **Not preserved** |
| B3       | Packet capture (pcap) | **Pending** — not collected in this phase |

---

## Table 7.6 — B3 Raw Data Rows (replacement)

> Replace the B3 rows in Table 7.6 with the following.
> Delete or annotate the old B3 rows (Mar 4 session, latencies 1,051–1,654 ms).

| Run | Baseline | Latency (ms) | Heap Δ (B) | HTTP Status | Result |
|-----|----------|-------------|------------|-------------|--------|
| 1   | B3       | 1,782       | +3,748     | 200         | PASS   |
| 2   | B3       | 1,142       | −428       | 200         | PASS   |
| 3   | B3       | 1,554       | −416       | 200         | PASS   |
| 4   | B3       | 1,147       | −416       | 200         | PASS   |
| 5   | B3       | 1,251       | −416       | 200         | PASS   |

*(B1 rows and any other baselines in Table 7.6 are governed by the B1 patch
`docs/report_patch_b1_rerun_2026-04-05.md` and are unchanged by this patch.)*

---

## Section 7.3.2 — Baseline 3 Results Narrative (replacement)

> Replace the existing Section 7.3.2 narrative with the following:

**7.3.2 Baseline 3 — Plain HTTP CSR Enrollment with Cloud PKI**

Baseline 3 extends the onboarding flow with certificate-based device identity. The ESP32
generates a CSR on-device, sends it to the cloud emulator via a plain HTTP POST to
`/enroll`, and receives a CA-signed device certificate and CA certificate in response.
All communication remains unencrypted (plain HTTP); the security gain over Baseline 1 is
in device identity and certificate issuance, not in transport confidentiality.

The controlled live rerun (2026-04-05, n = 5) produced the following results. Mean
latency was **1,375 ms** (sample SD = 283 ms, median = 1,251 ms, range 1,142–1,782 ms).
All five runs returned HTTP 200 with `device_cert_pem` and `ca_cert_pem` fields, giving
a success rate of 100%.

The latency distribution was moderately right-skewed. Run 1 (1,782 ms) is the high
outlier, consistent with first-cycle overhead: DNS resolution, TCP connection
establishment, on-device CSR generation, and HTTP round-trip all occurring in sequence.
Runs 2–5 (1,142–1,554 ms) represent the steady-state range once the stack is
initialised. The sample standard deviation of 282.5 ms is approximately 21% of the mean,
indicating reasonable consistency in the steady-state runs.

Heap memory behaviour followed the same pattern seen in Baseline 1. Run 1 showed a
positive heap delta (+3,748 B) due to stack initialisation. Runs 2–5 showed a stable
negative delta of approximately −416 B per cycle — a minor allocation not freed within
the measurement window, consistent across all steady-state runs and not indicative of
a meaningful leak at this sample size.

The enrollment response included both a device certificate and CA certificate in PEM
format, confirming the emulator's CA signing step completed correctly for each run.
Full certificate chain verification (independent validation that the device certificate
chains to the CA root) was not performed as a separate step in this phase; this is
noted as a future verification item. The emulator's signing logic is implemented in
`cloud_emulator/api/app.py` using the local CA at `cloud_emulator/pki/`.

As with Baseline 1, all traffic in Baseline 3 is transmitted in plaintext. The
certificate material — including device CSR and issued certificates — is sent unencrypted
over the network, making it observable to any on-path party. This is a known and intended
property of Baseline 3 as the reference enrollment design before transport security
(TLS) is introduced.

---

## Figure 7.6 — Caption / Regeneration Note

> If Figure 7.6 shows a latency bar chart or box plot for Baseline 3, it must be
> regenerated from the accepted rerun values before final submission.

Updated values for regenerating Figure 7.6 (B3 series):

```
latencies_B3 = [1782, 1142, 1554, 1147, 1251]  # ms, runs 1–5
mean_B3      = 1375.2
sd_B3        = 282.5
median_B3    = 1251
```

The old B3 mean (from the Mar 4 session, approximately 1,197 ms) is replaced by 1,375 ms.
Axis scaling should be reviewed if B1 and B3 share the same figure, given that the new
B3 mean (1,375 ms) is now higher than the new B1 mean (1,663 ms) would suggest a
reversal — note this is within measurement uncertainty given different network conditions
on different days (see Section 7.6 note on cross-session comparison).

> **Note:** Do not regenerate Figure 7.6 from memory or estimated values. Use only
> `data/processed/final_results.csv` rows 16–20 (B3 rerun) as the data source.

---

## Table 7.7 — Evidence / Security Claims Update

> If Table 7.7 contains per-baseline evidence references or security claim status,
> update the B3 row as follows:

| Baseline | Transport | Auth Mechanism | Cert Issuance Confirmed | Pcap Evidence | UART Log |
|----------|-----------|----------------|------------------------|---------------|----------|
| B3       | Plain HTTP | CSR → CA-signed cert | Yes (emulator log, 2026-04-05) | Pending | Not preserved for rerun |

> Remove or qualify any cell in Table 7.7 that says "pcap confirmed" for B3 unless
> a pcap from this rerun exists in `capture/pcaps/`.

---

## Section 7.6 — Discussion of Results (B3 paragraph guidance)

> Locate paragraphs in Section 7.6 that discuss B3 latency, cryptographic overhead,
> or security comparison with B1. Apply the following guidance:

**Latency comparison (B1 vs B3):**
Using the 2026-04-05 live rerun values, B1 mean = 1,663 ms and B3 mean = 1,375 ms.
Numerically B3 appears faster in this comparison, which is counterintuitive given that
B3 adds CSR generation and a POST body parse. This apparent reversal is attributable to
measurement conditions: B1 and B3 were run on different network states on the same day,
and the B1 run 5 outlier (2,980 ms) disproportionately inflates the B1 mean. The correct
framing for the report is:

> "The mean latency difference between B1 (1,663 ms) and B3 (1,375 ms) is within the
> measurement uncertainty of these small-sample hotspot-based experiments (n=5 each) and
> should not be interpreted as B3 being categorically faster. The key comparative result
> is that B3 achieves certificate-based device identity with latency in the same order
> of magnitude as the plain health-check baseline, confirming that the overhead of
> on-device CSR generation and CA signing is not prohibitive at this sample size."

**Cryptographic overhead discussion:**
The absolute additional overhead of B3 over B1 cannot be precisely isolated from these
runs due to different network conditions. Future work with controlled back-to-back runs
on the same network state would better isolate the CSR+signing overhead. This limitation
should be noted in the discussion.

**Plaintext observability (B3 security argument):**
B3 transmits certificate material — device CSR, issued device certificate, and CA
certificate — in plain HTTP. Any on-path observer can read this material. This is a
known property of the Baseline 3 design and is used as the reference point before TLS
is introduced. Do NOT cite a specific pcap as confirming this for the 2026-04-05 rerun
unless `capture/pcaps/` contains that file. The correct framing is:

> "Baseline 3 uses plain HTTP for the enrollment transaction. The device CSR and the
> CA-issued certificate are transmitted without encryption. This is a known and inherent
> property of the plain HTTP transport, consistent with the threat model described in
> Section X, and is addressed in Baseline 2/4 by the introduction of TLS."

---

## Cross-Session Comparison Caveat (add to Section 7.3 or 7.6)

> Add a brief caveat paragraph if Section 7.3 or 7.6 makes direct numerical comparisons
> between B1 and B3:

Both the B1 and B3 controlled reruns were conducted on 2026-04-05 over the same phone
hotspot (SSID: HUAWEI-B315-58AD), but at different times of day and in separate firmware
flash sessions. RF conditions, DNS cache state, and TCP stack warm-up state may have
differed between sessions. Direct millisecond-level comparisons between the two baselines
should be treated as indicative rather than definitive; a back-to-back controlled
experiment on a stable wired LAN would provide more reliable comparative data.

---

## Checklist Before Submission

- [ ] Table 7.6 B3 rows updated to accepted rerun values (latencies 1,142–1,782 ms)
- [ ] Section 7.3.2 narrative updated (mean 1,375 ms, SD 283 ms, median 1,251 ms)
- [ ] Section 7.3 data-source paragraph references 2026-04-05 live rerun + emulator log
- [ ] Table 7.5 B3 evidence row references `enroll_log.jsonl` and notes UART log absent
- [ ] Table 7.7 B3 pcap cell qualified as pending
- [ ] Figure 7.6 regenerated from `final_results.csv` rows 16–20
- [ ] Section 7.6 B1 vs B3 comparison updated with cross-session caveat
- [ ] Pcap for B3 rerun collected and stored OR plaintext claim qualified as protocol-level
- [ ] `cloud_emulator/api/logs/enroll_log.jsonl` committed to git
- [ ] `data/raw/b3_live_rerun_2026-04-05_evidence.md` committed to git
- [ ] Certificate chain independent verification noted as future work item
