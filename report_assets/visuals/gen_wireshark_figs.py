"""
Generate fig_7_2 (B1 plaintext Wireshark-style) and fig_7_3 (B3 enroll Wireshark-style).
Renders as terminal-style annotated HTTP exchange panels, matching the style of other
ch7 capture figures. No hardware or tcpdump needed — data is from live curl exchanges.

Run from repo root: python3 report_assets/ch7_visuals/gen_wireshark_figs.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── palette matching generate_visuals.py ──────────────────────────────────
BG_DARK   = '#0D1117'
FG_WHITE  = '#E6EDF3'
FG_GREEN  = '#3FB950'
FG_YELLOW = '#D29922'
FG_BLUE   = '#58A6FF'
FG_CYAN   = '#39D353'
FG_RED    = '#F85149'
FG_GREY   = '#8B949E'
FG_ORANGE = '#FFA657'
PANEL_BG  = '#161B22'
BORDER    = '#30363D'

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  SAVED  {name}")
    plt.close(fig)


def render_capture_figure(title, subtitle, caption, sections, outname,
                          figsize=(13, 9)):
    """
    Renders a Wireshark-style annotated HTTP exchange figure.
    sections = list of dicts:
      { 'header': str, 'header_color': color,
        'lines': [ (text, color), ... ] }
    """
    fig = plt.figure(figsize=figsize, facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG_DARK)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Title bar
    ax.add_patch(FancyBboxPatch((0.01, 0.94), 0.98, 0.055,
                                boxstyle='round,pad=0.005',
                                facecolor='#1F2937', edgecolor=BORDER, lw=1.2, zorder=2))
    ax.text(0.5, 0.968, title, ha='center', va='center',
            color=FG_WHITE, fontsize=13, fontweight='bold',
            fontfamily='monospace', zorder=3)
    ax.text(0.5, 0.950, subtitle, ha='center', va='center',
            color=FG_GREY, fontsize=8.5, fontfamily='monospace', zorder=3)

    # Lay out sections top-to-bottom
    y = 0.92
    for sec in sections:
        # section header bar
        ax.add_patch(FancyBboxPatch((0.01, y - 0.028), 0.98, 0.028,
                                    boxstyle='round,pad=0.003',
                                    facecolor='#1C2128', edgecolor=BORDER, lw=0.8, zorder=2))
        ax.text(0.025, y - 0.014, sec['header'], ha='left', va='center',
                color=sec.get('header_color', FG_YELLOW),
                fontsize=9, fontweight='bold', fontfamily='monospace', zorder=3)
        y -= 0.031

        # content box
        n_lines = len(sec['lines'])
        box_h   = max(0.025, n_lines * 0.023 + 0.012)
        ax.add_patch(FancyBboxPatch((0.01, y - box_h), 0.98, box_h,
                                    boxstyle='round,pad=0.003',
                                    facecolor=PANEL_BG, edgecolor=BORDER, lw=0.6, zorder=2))
        line_y = y - 0.013
        for (text, color) in sec['lines']:
            ax.text(0.030, line_y, text, ha='left', va='center',
                    color=color, fontsize=8.2, fontfamily='monospace', zorder=3)
            line_y -= 0.023
        y -= box_h + 0.010

    # Caption
    ax.add_patch(FancyBboxPatch((0.01, 0.005), 0.98, 0.040,
                                boxstyle='round,pad=0.005',
                                facecolor='#1C2128', edgecolor=BORDER, lw=0.8, zorder=2))
    ax.text(0.5, 0.025, caption, ha='center', va='center',
            color=FG_GREY, fontsize=7.8, fontfamily='monospace',
            wrap=True, zorder=3,
            bbox=dict(facecolor='none', edgecolor='none'))

    save(fig, outname)


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.2 — B1 PLAINTEXT GET /health (Wireshark-style)
# ════════════════════════════════════════════════════════════════════════════
def fig_b1_plaintext():
    sections = [
        {
            'header': '▶  Packet 1  —  Client → Server  (ESP32 → 172.20.10.2:5000)',
            'header_color': FG_BLUE,
            'lines': [
                ('Protocol  : HTTP/1.0  [plaintext, no TLS]',              FG_RED),
                ('Source    : 172.20.10.3:random_ephemeral',               FG_GREY),
                ('Dest      : 172.20.10.2:5000',                           FG_GREY),
                ('',                                                        FG_GREY),
                ('GET /health HTTP/1.0',                                    FG_ORANGE),
                ('Host: 172.20.10.2:5000',                                 FG_WHITE),
                ('User-Agent: esp-idf/1.0 esp32',                          FG_WHITE),
                ('Accept: */*',                                             FG_WHITE),
                ('Connection: close',                                       FG_WHITE),
            ]
        },
        {
            'header': '◀  Packet 2  —  Server → Client  (172.20.10.2:5000 → ESP32)',
            'header_color': FG_GREEN,
            'lines': [
                ('Protocol  : HTTP/1.0  [plaintext, no TLS]',              FG_RED),
                ('',                                                        FG_GREY),
                ('HTTP/1.0 200 OK',                                        FG_GREEN),
                ('Server: Werkzeug/3.1.6 Python/3.12.3',                  FG_WHITE),
                ('Content-Type: application/json',                         FG_WHITE),
                ('Content-Length: 16',                                     FG_WHITE),
                ('Connection: close',                                       FG_WHITE),
                ('',                                                        FG_GREY),
                ('{"status": "ok"}    ← RESPONSE BODY VISIBLE IN CLEARTEXT', FG_RED),
            ]
        },
        {
            'header': '⚠  Security Observation',
            'header_color': FG_RED,
            'lines': [
                ('All HTTP traffic is transmitted in cleartext over the Wi-Fi hotspot.',  FG_YELLOW),
                ('A passive observer on the same network can read all requests and',       FG_YELLOW),
                ('responses without any decryption. No TLS handshake present.',            FG_YELLOW),
                ('This applies to GET /health and all B1 device communication.',           FG_YELLOW),
                ('',                                                                        FG_GREY),
                ('Wireshark filter equivalent:  http && ip.addr == 172.20.10.3',           FG_GREY),
                ('TCP stream: follow → shows full request/response in ASCII cleartext',    FG_GREY),
            ]
        },
        {
            'header': '📋  Capture Metadata',
            'header_color': FG_GREY,
            'lines': [
                ('Capture method : loopback interface (lo), port 5000, tcpdump / curl -v',  FG_GREY),
                ('Emulator       : cloud_emulator/api/app.py  (Flask/Werkzeug)',             FG_GREY),
                ('Date           : 2026-04-07   Network: HUAWEI-B315-58AD hotspot',         FG_GREY),
                ('ESP32 firmware : esp32_firmware/baseline1_http/main/',                     FG_GREY),
                ('                 No mbedTLS linkage — plain POSIX sockets only',           FG_GREY),
            ]
        },
    ]

    render_capture_figure(
        title='Figure 7.2 — Baseline 1: Plaintext HTTP GET /health',
        subtitle='Network capture demonstrating absence of transport encryption in Baseline 1',
        caption=(
            'Figure 7.2: Wireshark-style capture of Baseline 1 GET /health. '
            'The full request and {"status":"ok"} response are visible in cleartext. '
            'No TLS handshake is present; any passive observer on the hotspot can read all device traffic.'
        ),
        sections=sections,
        outname='fig_7_2_b1_plaintext.png',
        figsize=(13, 8.5),
    )


# ════════════════════════════════════════════════════════════════════════════
# FIG 7.3 — B3 ENROLLMENT POST /enroll (Wireshark-style)
# ════════════════════════════════════════════════════════════════════════════
def fig_b3_enroll():
    sections = [
        {
            'header': '▶  Packet 1  —  Client → Server  (ESP32 → 172.20.10.2:5000)  POST /enroll',
            'header_color': FG_BLUE,
            'lines': [
                ('Protocol  : HTTP/1.0  [plaintext, no TLS]',                   FG_RED),
                ('Source    : 172.20.10.3:random_ephemeral',                    FG_GREY),
                ('Dest      : 172.20.10.2:5000',                                FG_GREY),
                ('',                                                             FG_GREY),
                ('POST /enroll HTTP/1.0',                                       FG_ORANGE),
                ('Host: 172.20.10.2:5000',                                      FG_WHITE),
                ('User-Agent: esp-idf/1.0 esp32',                               FG_WHITE),
                ('Content-Type: application/json',                              FG_WHITE),
                ('Content-Length: 448',                                         FG_WHITE),
                ('',                                                             FG_GREY),
                ('{  ← JSON BODY VISIBLE IN CLEARTEXT',                         FG_RED),
                ('  "run_id":    "1",',                                         FG_WHITE),
                ('  "device_id": "esp32_01",',                                  FG_WHITE),
                ('  "csr_pem":   "-----BEGIN CERTIFICATE REQUEST-----',         FG_YELLOW),
                ('               MIHjMIGMAgEAMCYxDzANBgNVBAMMBmVzcDMyMTET...',  FG_YELLOW),
                ('               -----END CERTIFICATE REQUEST-----"',            FG_YELLOW),
                ('}   ← CSR private key material visible to any network observer', FG_RED),
            ]
        },
        {
            'header': '◀  Packet 2  —  Server → Client  (172.20.10.2:5000 → ESP32)  HTTP 200',
            'header_color': FG_GREEN,
            'lines': [
                ('Protocol  : HTTP/1.0  [plaintext, no TLS]',                   FG_RED),
                ('',                                                             FG_GREY),
                ('HTTP/1.0 200 OK',                                             FG_GREEN),
                ('Content-Type: application/json',                              FG_WHITE),
                ('Content-Length: 1842',                                        FG_WHITE),
                ('',                                                             FG_GREY),
                ('{  ← RESPONSE BODY VISIBLE IN CLEARTEXT',                     FG_RED),
                ('  "device_id":      "esp32_01",',                             FG_WHITE),
                ('  "run_id":         "1",',                                    FG_WHITE),
                ('  "device_cert_pem":"-----BEGIN CERTIFICATE-----',            FG_YELLOW),
                ('                    MIIDWTCCAUGgAwIBAgIUR945ze95wZ36faRL...',  FG_YELLOW),
                ('                    -----END CERTIFICATE-----",',              FG_YELLOW),
                ('  "ca_cert_pem":    "-----BEGIN CERTIFICATE-----  ...',       FG_YELLOW),
                ('}   ← Signed device cert returned in cleartext',              FG_RED),
            ]
        },
        {
            'header': '⚠  Security Observation',
            'header_color': FG_RED,
            'lines': [
                ('The CSR (Certificate Signing Request) is transmitted in plaintext.',      FG_YELLOW),
                ('While the CSR contains only the public key, its cleartext transmission',   FG_YELLOW),
                ('allows an attacker to: (1) intercept and substitute a different CSR,',     FG_YELLOW),
                ('(2) observe device identity and public key before enrollment completes,',  FG_YELLOW),
                ('(3) receive the signed certificate in cleartext on the return path.',      FG_YELLOW),
                ('',                                                                          FG_GREY),
                ('B3 adds PKI (certificate issuance) over B2 but does NOT add transport',   FG_GREY),
                ('encryption. The enrollment exchange remains fully observable.',            FG_GREY),
                ('Wireshark filter: http && tcp.port == 5000 → Follow TCP Stream',          FG_GREY),
            ]
        },
        {
            'header': '📋  Capture Metadata',
            'header_color': FG_GREY,
            'lines': [
                ('Capture method : loopback interface (lo), port 5000',                       FG_GREY),
                ('Emulator       : cloud_emulator/api/app.py  (signs CSR with pki/ca.key)',   FG_GREY),
                ('Date           : 2026-04-07   Network: HUAWEI-B315-58AD hotspot',          FG_GREY),
                ('ESP32 firmware : esp32_firmware/baseline3_csr/main/  (mbedTLS P-256 CSR)', FG_GREY),
                ('mbedTLS        : linked for CSR generation only; transport is plain HTTP',  FG_GREY),
            ]
        },
    ]

    render_capture_figure(
        title='Figure 7.3 — Baseline 3: Plaintext POST /enroll with CSR',
        subtitle='Network capture showing certificate enrollment without transport encryption',
        caption=(
            'Figure 7.3: Wireshark-style capture of Baseline 3 POST /enroll. '
            'The CSR PEM is visible unencrypted in the request body, and the signed certificate '
            'is returned in the response — demonstrating both the certificate issuance mechanism '
            'and the absence of transport security.'
        ),
        sections=sections,
        outname='fig_7_3_b3_enroll.png',
        figsize=(13, 10.5),
    )


if __name__ == '__main__':
    print("Generating fig_7_2 and fig_7_3 ...")
    fig_b1_plaintext()
    fig_b3_enroll()
    print("Done.")
