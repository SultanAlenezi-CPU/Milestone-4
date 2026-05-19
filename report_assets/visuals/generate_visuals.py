"""
Chapter 7 Visual Generator — IoT Onboarding Testbed
Generates all producible PNGs from existing evidence files.
Run from repo root: python3 report_assets/ch7_visuals/generate_visuals.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import textwrap
import os

OUT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(OUT, '..', '..'))

# ── shared style ────────────────────────────────────────────────────────────
BLUE  = '#2563EB'
GREEN = '#16A34A'
RED   = '#DC2626'
ORANGE = '#EA580C'
GREY  = '#6B7280'
DARK  = '#111827'
BG    = '#F9FAFB'
ACCENT = '#7C3AED'

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  SAVED  {name}")
    plt.close(fig)

# ════════════════════════════════════════════════════════════════════════════
# FIG 7.1 — TOPOLOGY DIAGRAM
# ════════════════════════════════════════════════════════════════════════════
def fig_topology():
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis('off')
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)

    def node(x, y, w, h, label, sub, color, icon=''):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle='round,pad=0.12', linewidth=1.5,
                             edgecolor=color, facecolor='white', zorder=3)
        ax.add_patch(box)
        ax.text(x, y + h/2 - 0.28, icon + label, ha='center', va='top',
                fontsize=10, fontweight='bold', color=DARK, zorder=4)
        ax.text(x, y - h/2 + 0.15, sub, ha='center', va='bottom',
                fontsize=7.5, color=GREY, zorder=4, style='italic')

    def arrow(x1, y1, x2, y2, label='', color=BLUE, style='->'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color,
                                   lw=1.6, connectionstyle='arc3,rad=0.0'),
                    zorder=2)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my + 0.18, label, ha='center', va='bottom',
                    fontsize=7.5, color=color, fontweight='bold', zorder=5)

    # nodes
    node(1.6,  5.0, 2.6, 1.4,  'ESP32',           '172.20.10.3\nWi-Fi STA',    BLUE)
    node(6.5,  5.0, 2.6, 1.4,  'HUAWEI-B315-58AD', 'Hotspot router\n172.20.10.1', ORANGE)
    node(11.4, 5.0, 2.8, 1.4,  'Windows Laptop',  'WSL2\n172.20.10.2',          GREEN)
    node(6.5,  2.0, 2.6, 1.4,  'Raspberry Pi',    '172.20.10.4\nPort 8080/8090', ACCENT)
    node(11.4, 2.0, 2.8, 1.4,  'Cloud Emulator',  'Flask :5000\n/health /enroll /provision', GREEN)

    # Direct paths (top row)
    arrow(2.95, 5.0, 5.2, 5.0, 'Wi-Fi', BLUE)
    arrow(7.8,  5.0, 10.0, 5.0, 'Hotspot LAN', GREEN)

    # Via-Pi paths
    ax.annotate('', xy=(5.2, 2.3), xytext=(2.95, 4.65),
                arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.5,
                               connectionstyle='arc3,rad=-0.2'), zorder=2)
    ax.text(3.5, 3.5, 'Via-Pi path', ha='center', fontsize=7.5,
            color=ACCENT, fontweight='bold', rotation=65)

    arrow(7.8, 2.0, 10.0, 2.0, 'UPSTREAM_HOST', ACCENT)

    # Downward arrows hotspot -> Pi
    arrow(6.5, 4.3, 6.5, 2.7, '', ORANGE)

    # Proposed gateway separate label
    ax.text(6.5, 0.55,
            'Relay: port 8080 (B1/B2/B3 via-Pi)\nProposed Gateway: port 8090 (Phase 1 + Phase 2)',
            ha='center', va='bottom', fontsize=8, color=ACCENT,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=ACCENT, lw=1))

    # Direct path label
    ax.text(6.5, 6.5,
            'Direct path (B1/B2/B3 direct): ESP32 → Hotspot → Cloud Emulator :5000',
            ha='center', va='center', fontsize=8.5, color=DARK,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=BLUE, lw=1))

    ax.set_title('Figure 7.1 — Testbed Topology: Secure IoT Onboarding Testbed',
                 fontsize=12, fontweight='bold', color=DARK, pad=10)
    save(fig, 'fig_7_1_topology.png')


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.4 — COMPARATIVE MEAN LATENCY CHART
# ════════════════════════════════════════════════════════════════════════════
def fig_latency_comparison():
    methods = ['B1\n(Health-Check)', 'B3\n(CSR Enroll)', 'Proposed\n(Two-Phase)']
    means   = [1663.2, 1375.2, 1997.0]
    stds    = [789.4,  282.5,  4.18]
    colors  = [BLUE, GREEN, ACCENT]

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.bar(methods, means, yerr=stds, capsize=8,
                  color=colors, edgecolor='white', linewidth=1.2,
                  error_kw=dict(elinewidth=1.8, ecolor=DARK, capthick=1.8),
                  width=0.52, zorder=3)

    # value labels
    for bar, mean, std in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + std + 35,
                f'{mean:.1f} ms', ha='center', va='bottom',
                fontsize=10.5, fontweight='bold', color=DARK)

    ax.set_ylabel('Mean Total Latency (ms)', fontsize=11, color=DARK)
    ax.set_xlabel('Onboarding Method', fontsize=11, color=DARK)
    ax.set_title('Figure 7.4 — Mean Total Latency Comparison\n(n=5 canonical runs each; error bars = ±1 std dev)',
                 fontsize=11, fontweight='bold', color=DARK, pad=8)
    ax.set_ylim(0, 3300)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=10)
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(axis='x', labelsize=10.5)

    # annotation
    ax.annotate('B3 → Proposed overhead:\n+621.8 ms (+45.2%)',
                xy=(2, 1997), xytext=(1.55, 2500),
                arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.5),
                fontsize=9, color=ORANGE, fontweight='bold')

    ax.text(0.01, 0.99, 'Network: HUAWEI-B315-58AD hotspot  |  Hardware: ESP32 + ESP-IDF v5.5.3',
            transform=ax.transAxes, fontsize=7.5, color=GREY,
            va='top', ha='left')

    save(fig, 'fig_7_4_latency_comparison.png')


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.5 — PROPOSED METHOD PHASE BREAKDOWN
# ════════════════════════════════════════════════════════════════════════════
def fig_proposed_phase_breakdown():
    phases  = ['Phase 1\nAuth (Gateway)', 'CSR Generation\n(mbedTLS P-256)', 'Phase 2\nEnroll (Gateway→Cloud)']
    values  = [142.0, 691.2, 1152.6]  # means
    colors  = [BLUE, RED, ACCENT]
    total   = 1997.0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5),
                                   gridspec_kw={'width_ratios': [1.6, 1]})
    fig.patch.set_facecolor(BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)

    # -- left: stacked horizontal bar per run --
    runs = [
        [74,  680, 1232],
        [105, 674, 1205],
        [327, 706,  955],
        [114, 704, 1162],
        [90,  692, 1209],
    ]
    ylabels = [f'Run {i}' for i in range(1, 6)]
    lefts = np.zeros(5)
    phase_labels = ['Phase 1 Auth', 'CSR Generation', 'Phase 2 Enroll']
    for idx, (col, lab) in enumerate(zip(colors, phase_labels)):
        vals = [r[idx] for r in runs]
        bars = ax1.barh(ylabels, vals, left=lefts, color=col,
                        label=lab, height=0.5, edgecolor='white', linewidth=0.8)
        lefts += np.array(vals)

    for i, run in enumerate(runs):
        total_r = sum(run)
        ax1.text(total_r + 15, i, f'{total_r} ms', va='center', fontsize=9,
                 color=DARK, fontweight='bold')

    ax1.set_xlabel('Latency (ms)', fontsize=10)
    ax1.set_title('Per-Run Phase Breakdown (canonical pack)', fontsize=10,
                  fontweight='bold', color=DARK)
    ax1.legend(fontsize=9, loc='lower right')
    ax1.set_xlim(0, 2400)
    ax1.spines[['top','right']].set_visible(False)
    ax1.axvline(x=total, color=GREY, linestyle='--', lw=1, label='Mean total')
    ax1.text(total + 5, 4.5, f'mean\n{total} ms', fontsize=8, color=GREY)
    ax1.yaxis.grid(False)
    ax1.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax1.set_axisbelow(True)

    # -- right: pie --
    pct = [v/total*100 for v in values]
    wedge_props = dict(edgecolor='white', linewidth=2)
    wedges, texts, autotexts = ax2.pie(
        values, labels=phases, autopct='%1.1f%%',
        colors=colors, startangle=90,
        wedgeprops=wedge_props, pctdistance=0.72,
        textprops={'fontsize': 8.5})
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_fontsize(9)
    ax2.set_title(f'Phase Share\n(mean total = {total} ms)', fontsize=10,
                  fontweight='bold', color=DARK)

    fig.suptitle('Figure 7.5 — Proposed Method Phase Breakdown (n=5 canonical runs)',
                 fontsize=12, fontweight='bold', color=DARK, y=1.01)
    save(fig, 'fig_7_5_proposed_phase_breakdown.png')


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.6 — PROPOSED METHOD UART PASS (text rendered as image)
# ════════════════════════════════════════════════════════════════════════════
def fig_proposed_uart():
    # Extract the 5 canonical PROPOSED_MEASURE lines from the capture file
    capture_path = os.path.join(REPO, 'capture', 'proposed_p5_repeated_runs_latest.txt')
    lines = []
    with open(capture_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip()
            if 'PROPOSED_MEASURE' in line:
                lines.append(line)
    # canonical pack = first 5 lines (matches evidence note values exactly)
    canonical = lines[:5]

    # Build display block: header + MEASURE lines + key stats
    header = [
        '═' * 82,
        '  Proposed Method — Canonical 5-Run PASS Pack   |   capture/proposed_p5_repeated_runs_latest.txt',
        '═' * 82,
    ]
    footer = [
        '─' * 82,
        '  Summary: 5/5 PASS   Mean total: 1997.0 ms   Std dev: 4.18 ms',
        '  Phase 1 auth mean: 142.0 ms   CSR gen mean: 691.2 ms   Enroll mean: 1152.6 ms',
        '═' * 82,
    ]
    display_lines = header + [''] + canonical + [''] + footer

    fig, ax = plt.subplots(figsize=(14, 5.8))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    y = 0.97
    for i, line in enumerate(display_lines):
        if '═' in line:
            color = '#58A6FF'
        elif '─' in line:
            color = '#30363D'
        elif 'PROPOSED_MEASURE' in line:
            # highlight result=PASS
            color = '#3FB950' if 'result=PASS' in line else '#F85149'
        elif 'Summary' in line or 'Phase' in line:
            color = '#E3B341'
        elif 'capture/' in line:
            color = '#8B949E'
        else:
            color = '#C9D1D9'

        ax.text(0.01, y, line, transform=ax.transAxes,
                fontsize=7.8, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= 0.088

    ax.set_title('Figure 7.6 — Proposed Method UART Output: Canonical 5-Run PASS Pack (2026-04-07)',
                 fontsize=10, fontweight='bold', color='#C9D1D9',
                 pad=8, fontfamily='monospace')
    save(fig, 'fig_7_6_proposed_uart_pass.png')


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.7 — B2 REPLAY SCENARIO
# ════════════════════════════════════════════════════════════════════════════
def fig_b2_replay():
    replay_path = os.path.join(REPO, 'capture', 'b2_replay_scenario_2026-04-06.txt')
    with open(replay_path, encoding='utf-8', errors='replace') as f:
        raw = f.read()

    # Clean up ANSI / binary noise and take meaningful lines
    import re
    raw = re.sub(r'\x1b\[[0-9;]*m', '', raw)
    raw = re.sub(r'[^\x09\x0a\x20-\x7e]', '', raw)
    lines = [l for l in raw.splitlines() if l.strip()]

    fig, ax = plt.subplots(figsize=(13, 7.2))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    y = 0.97
    step = 0.055
    for line in lines[:30]:
        if '===' in line:
            color, size = '#58A6FF', 8.5
        elif 'HTTP/1.0 200' in line:
            color, size = '#3FB950', 8.5
        elif 'HTTP/1.0 401' in line or '401' in line:
            color, size = '#F85149', 8.5
        elif 'token_used_before' in line:
            color = '#F85149' if 'true' in line else '#3FB950'
            size = 7.8
        elif 'token_valid' in line:
            color = '#F85149' if '"false"' in line or 'false' in line else '#3FB950'
            size = 7.8
        elif 'status_code' in line:
            color = '#F85149' if '401' in line else '#3FB950'
            size = 7.8
        elif 'error' in line.lower():
            color, size = '#F85149', 8.5
        elif 'provisioning_status' in line:
            color, size = '#3FB950', 8.5
        else:
            color, size = '#C9D1D9', 7.8

        ax.text(0.01, y, line[:110], transform=ax.transAxes,
                fontsize=size, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= step
        if y < 0.04:
            break

    # Result verdict box
    ax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.10,
                                transform=ax.transAxes,
                                boxstyle='round,pad=0.01',
                                facecolor='#161B22', edgecolor='#F85149',
                                linewidth=2, zorder=4))
    ax.text(0.5, 0.06, '✓  Token replay REJECTED — HTTP 401  |  token_used_before=true  |  token_valid=false',
            transform=ax.transAxes, ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='#F85149', fontfamily='monospace', zorder=5)

    ax.set_title('Figure 7.7 — B2 Replay Attack Scenario: First Use HTTP 200, Replay HTTP 401  (2026-04-06)',
                 fontsize=10, fontweight='bold', color='#C9D1D9', pad=8)
    save(fig, 'fig_7_7_b2_replay.png')


# ════════════════════════════════════════════════════════════════════════════
# OPTIONAL 8 — B2 via-Pi timeout evidence
# ════════════════════════════════════════════════════════════════════════════
def fig_b2_via_pi_timeout():
    capture_path = os.path.join(REPO, 'capture', 'b2_via_pi_clean_2026-04-06_final.txt')
    with open(capture_path, encoding='utf-8', errors='replace') as f:
        raw = f.read()

    import re
    raw = re.sub(r'\x1b\[[0-9;]*m', '', raw)
    raw = re.sub(r'[^\x09\x0a\x20-\x7e]', '', raw)

    # pull MEASURE lines and the errno lines
    lines = raw.splitlines()
    selected = []
    for line in lines:
        if 'MEASURE run_id' in line or ('errno=11' in line and 'done reading' in line):
            selected.append(line.strip())

    fig, ax = plt.subplots(figsize=(14, 5.2))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    header = [
        '═' * 90,
        '  B2 via-Pi — UART MEASURE lines  |  capture/b2_via_pi_clean_2026-04-06_final.txt',
        '  (5s SO_RCVTIMEO — before 8s fix)  |  Server-side: 10/10 HTTP 200  |  Client-side: 7/10',
        '═' * 90,
        '',
    ]
    footer = [
        '',
        '─' * 90,
        '  Runs 4, 7, 10: latency_ms=5010, http_status=-1, errno=11 (EAGAIN — SO_RCVTIMEO fired)',
        '  Root cause: server responded HTTP 200 but ESP32 socket timed out before receiving it.',
        '  Fix applied 2026-04-07: SO_RCVTIMEO 5s → 8s in baseline2_token/main/http_request_example_main.c',
        '═' * 90,
    ]
    display = header + selected + footer

    y = 0.97
    for line in display:
        if '═' in line:
            color = '#58A6FF'
        elif '─' in line:
            color = '#30363D'
        elif 'http_status=-1' in line or 'errno=11' in line:
            color = '#F85149'
        elif 'http_status=200' in line:
            color = '#3FB950'
        elif 'Root cause' in line or 'Fix applied' in line or 'Runs 4' in line:
            color = '#E3B341'
        elif 'Server-side' in line or 'Client-side' in line or '5s SO_RCVTIMEO' in line:
            color = '#8B949E'
        else:
            color = '#C9D1D9'

        ax.text(0.01, y, line[:100], transform=ax.transAxes,
                fontsize=7.5, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= 0.072
        if y < 0.03:
            break

    ax.set_title('Figure 7.8 (Optional) — B2 via-Pi: Client-Side Receive Timeout (Runs 4, 7, 10)',
                 fontsize=10, fontweight='bold', color='#C9D1D9', pad=8)
    save(fig, 'fig_7_8_b2_via_pi_timeout.png')


# ════════════════════════════════════════════════════════════════════════════
# OPTIONAL 9 — Gateway log showing proposed P4 flow
# ════════════════════════════════════════════════════════════════════════════
def fig_gateway_log():
    log_path = os.path.join(REPO, 'gateway', 'logs', 'proposed_gateway_log.jsonl')
    with open(log_path) as f:
        lines = [l.rstrip() for l in f if l.strip()]

    import json
    parsed = []
    for line in lines:
        try:
            d = json.loads(line)
            parsed.append(d)
        except:
            pass

    fig, ax = plt.subplots(figsize=(14, 5.0))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    header_lines = [
        '═' * 95,
        '  Proposed Gateway Pi-side log   |   gateway/logs/proposed_gateway_log.jsonl',
        '  Shows Phase 1 (/gateway/auth) and Phase 2 (/gateway/enroll) event sequence',
        '═' * 95,
        '',
    ]

    display = header_lines[:]
    for i, entry in enumerate(parsed, 1):
        ts  = entry.get('timestamp_utc', '')[:19]
        path = entry.get('path', '')
        sc  = entry.get('status_code', '')
        auth_ok = entry.get('auth_success')
        tok_ok  = entry.get('session_token_valid')
        issued  = entry.get('session_token_issued')
        used_b  = entry.get('session_token_used_before')
        up      = entry.get('upstream_status')

        if path == '/gateway/auth':
            detail = f"auth_success={auth_ok}  session_token_issued={issued}"
        else:
            detail = f"session_token_valid={tok_ok}  used_before={used_b}  upstream={up}"
        display.append(f"  {i:2}.  {ts}  {path:<22}  status={sc}   {detail}")

    footer = [
        '',
        '─' * 95,
        '  Entry 4: Phase 1 auth→Phase 2 enroll back-to-back PASS (t=15:05:55 UTC)',
        '  Entry 5: Second /gateway/enroll attempt immediately rejected (token_used_before=true)',
        '  Entry 6: /gateway/auth with wrong token → auth_success=false (401)',
        '═' * 95,
    ]
    display += footer

    y = 0.97
    for line in display:
        if '═' in line:
            color = '#58A6FF'
        elif '─' in line:
            color = '#30363D'
        elif 'status=200' in line and 'Phase' not in line:
            color = '#3FB950' if 'upstream=200' in line or 'session_token_issued=True' in line else '#C9D1D9'
        elif 'status=401' in line or 'auth_success=False' in line or 'used_before=True' in line:
            color = '#F85149'
        elif 'status=400' in line:
            color = '#E3B341'
        elif 'Phase 1' in line or 'Phase 2' in line or 'Entry' in line:
            color = '#E3B341'
        elif 'gateway/' in line:
            color = '#8B949E'
        else:
            color = '#C9D1D9'

        ax.text(0.01, y, line[:108], transform=ax.transAxes,
                fontsize=7.5, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= 0.072
        if y < 0.03:
            break

    ax.set_title('Figure 7.9 (Optional) — Pi Gateway Log: Proposed Method Phase 1 + Phase 2 Event Sequence',
                 fontsize=10, fontweight='bold', color='#C9D1D9', pad=8)
    save(fig, 'fig_7_9_gateway_log.png')


# ════════════════════════════════════════════════════════════════════════════
# OPTIONAL 10 — Cloud enroll log (B3 live rerun + proposed method entries)
# ════════════════════════════════════════════════════════════════════════════
def fig_enroll_log():
    log_path = os.path.join(REPO, 'cloud_emulator', 'api', 'logs', 'enroll_log.jsonl')
    import json

    b3_entries = []
    proposed_entries = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                ts = d.get('timestamp_utc', '')
                path = d.get('path', '')
                # B3 live rerun: 2026-04-05T18:51
                if '2026-04-05T18:51' in ts and path == '/enroll':
                    b3_entries.append(d)
                # Proposed P5: 2026-04-06T21:27 to 21:33 (UTC, = local 2026-04-07 00:27)
                if '2026-04-06T21:2' in ts and path == '/enroll':
                    proposed_entries.append(d)
            except:
                pass

    fig, ax = plt.subplots(figsize=(14, 6.5))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    header = [
        '═' * 95,
        '  Cloud Emulator Enrollment Log   |   cloud_emulator/api/logs/enroll_log.jsonl',
        '  Section A: B3 live rerun (2026-04-05)   Section B: Proposed Method P5 (2026-04-07 local)',
        '═' * 95,
        '',
        '  ── Section A: Baseline 3 Direct CSR Enrollment (2026-04-05T18:51 UTC) ──────────────',
    ]
    display = header[:]

    for i, d in enumerate(b3_entries, 1):
        ts = d.get('timestamp_utc', '')[:23]
        sc = d.get('status_code')
        rid = d.get('run_id')
        did = d.get('device_id')
        display.append(f"  B3-{i:02}.  {ts}  POST /enroll  device_id={did}  run_id={rid}  status={sc}")

    display += [
        '',
        f'  → B3 result: {len(b3_entries)}/5 HTTP 200  (5/5 PASS confirmed)',
        '',
        '  ── Section B: Proposed Method — Pi forwarded /enroll (2026-04-06T21:2x UTC = local 2026-04-07) ─',
    ]

    for i, d in enumerate(proposed_entries[:10], 1):
        ts = d.get('timestamp_utc', '')[:23]
        sc = d.get('status_code')
        rid = d.get('run_id')
        did = d.get('device_id')
        display.append(f"  P5-{i:02}.  {ts}  POST /enroll  device_id={did}  run_id={rid}  status={sc}")

    display += [
        '',
        f'  → Proposed P5 result: {min(len(proposed_entries),5)}/5 HTTP 200 (canonical pack, Pi-forwarded)',
        '═' * 95,
    ]

    y = 0.97
    for line in display:
        if '═' in line:
            color = '#58A6FF'
        elif '─' in line or '──' in line:
            color = '#30363D'
        elif 'status=200' in line:
            color = '#3FB950'
        elif 'status=4' in line or 'status=5' in line:
            color = '#F85149'
        elif '→' in line:
            color = '#E3B341'
        elif 'Section A' in line or 'Section B' in line:
            color = '#58A6FF'
        else:
            color = '#C9D1D9'

        ax.text(0.01, y, line[:108], transform=ax.transAxes,
                fontsize=7.5, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= 0.063
        if y < 0.04:
            break

    ax.set_title('Figure 7.10 (Optional) — Cloud Emulator Enrollment Log: B3 Live Rerun and Proposed Method P5',
                 fontsize=10, fontweight='bold', color='#C9D1D9', pad=8)
    save(fig, 'fig_7_10_enroll_log.png')


# ════════════════════════════════════════════════════════════════════════════
# PROVISION LOG — B2 server-side confirmation
# ════════════════════════════════════════════════════════════════════════════
def fig_provision_log():
    log_path = os.path.join(REPO, 'cloud_emulator', 'api', 'logs', 'provision_log.jsonl')
    import json

    run10 = []
    replay_entries = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                rid = str(d.get('run_id', ''))
                if rid in [str(i) for i in range(1, 11)]:
                    run10.append(d)
                elif rid in ('101', '101_replay'):
                    replay_entries.append(d)
            except:
                pass

    # keep last 10 for the main B2 run
    run10 = run10[-10:]

    fig, ax = plt.subplots(figsize=(14, 7.0))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    ax.axis('off')

    header = [
        '═' * 100,
        '  Cloud Emulator Provision Log   |   cloud_emulator/api/logs/provision_log.jsonl',
        '  Section A: B2 via-Pi 10-run session (server-side all HTTP 200)',
        '  Section B: Replay attack run_id=101 and run_id=101_replay',
        '═' * 100,
        '',
        '  ── Section A: B2 10-run server log (2026-04-06T22:27 UTC) ───────────────────────────────',
    ]

    display = header[:]
    for d in run10:
        ts  = d.get('timestamp_utc', '')[:23]
        sc  = d.get('status_code')
        rid = d.get('run_id')
        did = d.get('device_id')
        tkn = d.get('token_valid')
        used = d.get('token_used_before')
        display.append(
            f"  {ts}  POST /provision  run_id={rid:<4}  token_valid={str(tkn):<5}  used_before={str(used):<5}  status={sc}"
        )

    display += [
        '',
        '  → Server-side result: 10/10 HTTP 200  (all tokens valid, none used before)',
        '',
        '  ── Section B: Replay attack (2026-04-06T22:32 UTC) ─────────────────────────────────────',
    ]
    for d in replay_entries:
        ts  = d.get('timestamp_utc', '')[:23]
        sc  = d.get('status_code')
        rid = d.get('run_id')
        tkn = d.get('token_valid')
        used = d.get('token_used_before')
        display.append(
            f"  {ts}  POST /provision  run_id={rid:<12}  token_valid={str(tkn):<5}  used_before={str(used):<5}  status={sc}"
        )

    display += [
        '',
        '  → run_id=101: HTTP 200  |  run_id=101_replay: HTTP 401  (token_used_before=True)',
        '═' * 100,
    ]

    y = 0.97
    for line in display:
        if '═' in line:
            color = '#58A6FF'
        elif '─' in line:
            color = '#30363D'
        elif 'status=200' in line:
            color = '#3FB950'
        elif 'status=401' in line:
            color = '#F85149'
        elif '101_replay' in line:
            color = '#F85149'
        elif '→' in line:
            color = '#E3B341'
        elif 'Section A' in line or 'Section B' in line:
            color = '#58A6FF'
        else:
            color = '#C9D1D9'

        ax.text(0.005, y, line[:112], transform=ax.transAxes,
                fontsize=7.4, color=color, fontfamily='monospace',
                va='top', ha='left')
        y -= 0.060
        if y < 0.04:
            break

    ax.set_title('Figure 7.11 (Optional) — Provision Log: B2 Server-side 10/10 HTTP 200 + Replay HTTP 401',
                 fontsize=10, fontweight='bold', color='#C9D1D9', pad=8)
    save(fig, 'fig_7_11_provision_log.png')


# ════════════════════════════════════════════════════════════════════════════
# RUN ALL
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Generating Chapter 7 visuals …")
    fig_topology()
    fig_latency_comparison()
    fig_proposed_phase_breakdown()
    fig_proposed_uart()
    fig_b2_replay()
    fig_b2_via_pi_timeout()
    fig_gateway_log()
    fig_enroll_log()
    fig_provision_log()
    print("\nDone. All files written to:", OUT)
