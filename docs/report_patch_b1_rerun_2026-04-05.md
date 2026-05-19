# Report Patch — Baseline 1 Live Rerun (2026-04-05)
## Sections Affected: 7.3, 7.3.1, Table 7.5, Table 7.6, Figure 7.5 caption, 7.6 Discussion

**Purpose:** This patch supersedes earlier B1 values in the draft report with the accepted
controlled live rerun data from 2026-04-05. The prior draft contained B1 rows with latencies
of approximately 195–220 ms (simulation/dry-run artifact). Those values are replaced by the
values below throughout Sections 7.3, 7.3.1, Table 7.6, and relevant discussion paragraphs.

**Evidence basis:**
- Raw UART log: `capture/b1_serial_live.txt` (272 lines, verified)
- Processed dataset: `data/processed/final_results.csv` rows 11–15
- Evidence note: `data/raw/b1_live_rerun_2026-04-05_evidence.md`
- Packet capture for this specific rerun: **not yet collected** (pending). The security
  discussion of plaintext HTTP visibility must be framed as a known protocol-level property
  of plain HTTP, not as "confirmed by pcap for this rerun", until a pcap is stored in
  `capture/pcaps/`.

---

## Accepted B1 Rerun Values (use these everywhere in the report)

### Raw Measurements

| Run | Latency (ms) | heap_before (B) | heap_after (B) | heap_delta (B) | HTTP Status | Result |
|-----|-------------|-----------------|----------------|----------------|-------------|--------|
| 1   | 965         | 221,936         | 225,776        | +3,840         | 200         | PASS   |
| 2   | 1,765       | 226,208         | 225,772        | −436           | 200         | PASS   |
| 3   | 1,325       | 226,208         | 225,788        | −420           | 200         | PASS   |
| 4   | 1,281       | 226,208         | 225,592        | −616           | 200         | PASS   |
| 5   | 2,980       | 226,188         | 225,592        | −596           | 200         | PASS   |

### Summary Statistics

| Statistic              | Value      |
|------------------------|------------|
| Mean latency           | 1,663.2 ms |
| Median latency         | 1,325 ms   |
| Std Dev (sample, n=5)  | 789.4 ms   |
| Min latency            | 965 ms     |
| Max latency            | 2,980 ms   |
| Mean heap delta        | +354.4 B   |
| HTTP success rate      | 5/5 (100%) |
| Endpoint               | http://172.20.10.2:5000/health |
| Network context        | Phone hotspot (HUAWEI-B315-58AD), 2026-04-05 |

---

## Section 7.3 — Experimental Results (replacement paragraph)

> Replace the existing data-source sentence in Section 7.3 with the following:

Baseline 1 results are drawn from a controlled live rerun conducted on 2026-04-05 using
the ESP32 firmware built from `esp32_firmware/baseline1_http` (ESP-IDF v5.5.3) and the
cloud emulator running at `http://172.20.10.2:5000`. The experiment was performed over a
phone hotspot (SSID: HUAWEI-B315-58AD) acting as the local network path between the DUT
and the emulator host. All five runs completed successfully (5/5 PASS) with HTTP 200
responses. Full UART session data is preserved in `capture/b1_serial_live.txt`. Packet
capture evidence for this rerun is pending; plaintext HTTP observability is addressed as
a protocol-level property in Section 7.6.

---

## Table 7.5 — Evidence Reference Update

> If Table 7.5 lists evidence artifacts per baseline, update the B1 row as follows:

| Baseline | Evidence Artifact | Status |
|----------|------------------|--------|
| B1       | `capture/b1_serial_live.txt` (UART, 272 lines) | Captured 2026-04-05 |
| B1       | `data/raw/b1_live_rerun_2026-04-05_evidence.md` | Evidence note, 2026-04-05 |
| B1       | Packet capture (pcap) | **Pending** — not collected in this phase |

---

## Table 7.6 — B1 Raw Data Rows (replacement)

> Replace the B1 rows in Table 7.6 with the following. Delete the old rows with
> latencies ~195–220 ms entirely.

| Run | Baseline | Latency (ms) | Heap Δ (B) | HTTP Status | Result |
|-----|----------|-------------|------------|-------------|--------|
| 1   | B1       | 965         | +3,840     | 200         | PASS   |
| 2   | B1       | 1,765       | −436       | 200         | PASS   |
| 3   | B1       | 1,325       | −420       | 200         | PASS   |
| 4   | B1       | 1,281       | −616       | 200         | PASS   |
| 5   | B1       | 2,980       | −596       | 200         | PASS   |

*(B3 rows and any other baselines in Table 7.6 are unchanged by this patch.)*

---

## Section 7.3.1 — Baseline 1 Results Narrative (replacement)

> Replace the existing Section 7.3.1 narrative with the following:

**7.3.1 Baseline 1 — Plain HTTP Health-Check**

Baseline 1 implements the simplest possible onboarding interaction: the ESP32 connects
to a Wi-Fi network, resolves the server hostname, opens a raw TCP socket, and sends a
plain HTTP GET request to `/health`. No transport security, authentication, or
certificate material is involved. This baseline establishes the performance floor for
the comparative study.

The controlled live rerun (2026-04-05, n = 5) produced the following results. Mean
latency was **1,663 ms** (sample SD = 789 ms, median = 1,325 ms, range 965–2,980 ms).
All five runs returned HTTP 200 with `{"status":"ok"}`, giving a success rate of 100%.

The latency distribution was right-skewed. Run 1 (965 ms) likely benefited from a warm
DNS cache immediately following Wi-Fi association. Run 5 (2,980 ms) is the high outlier,
consistent with occasional DNS re-resolution or brief RF contention on a shared hotspot.
Runs 2–4 (1,281–1,765 ms) represent the typical steady-state range for this network
context. The high sample standard deviation (789 ms, approximately 47% of the mean) is
expected for a small sample over a shared wireless medium rather than a dedicated lab LAN.

Heap memory behaviour was stable. Run 1 showed a positive heap delta (+3,840 B) due to
Wi-Fi/TCP stack initialisation completing during the first cycle. Runs 2–5 showed small
negative deltas (−420 to −616 B), indicating a minor per-cycle allocation that is not
freed within the measurement window. The magnitude is negligible relative to the
available heap (~226 KB) and does not indicate a memory leak at this sample size.

No cryptographic operations are performed in Baseline 1. The HTTP request and response
are transmitted in plaintext, making all content—including the server response body—
visible to any observer on the same network segment. This property is a known consequence
of using plain HTTP and is used in this study as the unsecured reference point against
which Baselines 2 and 3 are compared.

---

## Figure 7.5 — Caption / Regeneration Note

> If Figure 7.5 shows a latency bar chart or box plot for Baseline 1, it must be
> regenerated from the accepted rerun values before final submission.

Updated values for regenerating Figure 7.5 (B1 series):

```
latencies_B1 = [965, 1765, 1325, 1281, 2980]   # ms, runs 1–5
mean_B1      = 1663.2
sd_B1        = 789.4
median_B1    = 1325
```

The old B1 bar height (~200–210 ms mean) must be removed. The new bar height is
~1,663 ms. Axis scaling for the B1 series will need to be reviewed relative to B3
(mean ~1,197 ms) to ensure the chart remains readable.

> **Note:** Do not regenerate Figure 7.5 from memory or estimated values. Use only
> `data/processed/final_results.csv` rows 11–15 (B1 rerun) as the data source.

---

## Section 7.6 — Discussion of Results (B1 paragraph update guidance)

> Locate any paragraph in Section 7.6 that makes claims dependent on B1 latency being
> "consistently low" or "sub-250 ms". Those claims were based on the earlier dry-run
> values (195–220 ms) and must be revised.

**Revised framing for B1 in the Discussion:**

Baseline 1 exhibited a mean latency of 1,663 ms over a shared wireless path, which is
substantially higher than the earlier simulation estimate. This is consistent with the
overhead of DNS resolution, TCP connection establishment, and HTTP round-trip over a
Wi-Fi medium with non-zero RF contention. Baseline 1 remains the lowest-overhead
baseline in terms of protocol complexity—it performs no TLS handshake, no certificate
processing, and no cryptographic operations—but its absolute latency on a real wireless
link is meaningfully higher than the sub-250 ms values that appeared in earlier
planning-phase estimates.

The comparison between B1 and B3 (mean ~1,197 ms) should note that B3 is actually
faster on average in this rerun, which warrants a brief discussion of measurement
conditions: B1 and B3 were run on different days and potentially under different RF
conditions, so a direct numerical comparison should be treated with caution. The key
security comparison remains valid: B1 transmits in plaintext while B3 achieves
certificate-based identity; the latency overhead of B3's TLS and PKI operations is
discussed relative to protocol complexity, not as a raw millisecond delta between
these two specific rerun samples.

> Any sentence in 7.6 that says B1 is "consistently fast" or implies a mean near
> 200 ms must be updated to reflect the 1,663 ms mean with 789 ms SD from the live
> rerun.

**On plaintext visibility (security argument):** The discussion of B1's plaintext
exposure remains valid as a protocol-level property of plain HTTP. However, the
specific claim "as confirmed by the packet capture" should NOT appear in the final
report unless a pcap from this rerun is stored in `capture/pcaps/`. The correct
framing is: "Baseline 1 uses plain HTTP, meaning all traffic is transmitted without
encryption. This is a known and inherent property of the protocol, consistent with
the threat model described in Section X." This framing does not depend on a specific
pcap file.

---

## Checklist Before Submission

- [ ] Table 7.6 B1 rows updated to accepted rerun values (latencies 965–2,980 ms)
- [ ] Section 7.3.1 narrative updated (mean 1,663 ms, SD 789 ms, median 1,325 ms)
- [ ] Section 7.3 data-source paragraph references 2026-04-05 live rerun
- [ ] Table 7.5 evidence row references `capture/b1_serial_live.txt`
- [ ] Figure 7.5 regenerated from `final_results.csv` rows 11–15
- [ ] Section 7.6 B1 discussion updated (no "consistently sub-250 ms" claim)
- [ ] Pcap for B1 rerun collected and stored OR plaintext claim qualified as protocol-level
- [ ] `capture/b1_serial_live.txt` committed to git
- [ ] `data/raw/b1_live_rerun_2026-04-05_evidence.md` committed to git
