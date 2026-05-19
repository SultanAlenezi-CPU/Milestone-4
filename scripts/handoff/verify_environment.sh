#!/usr/bin/env bash
# verify_environment.sh
# Pre-session environment check for the IoT Onboarding Testbed.
# Run this before every session to catch setup problems before flashing.
#
# Usage: bash scripts/handoff/verify_environment.sh
# No arguments. Read-only — makes no changes.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

PASS=0
FAIL=0
WARN=0

ok()   { echo "  [OK]   $1"; PASS=$((PASS+1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
warn() { echo "  [WARN] $1"; WARN=$((WARN+1)); }
hdr()  { echo ""; echo "=== $1 ==="; }

# ─── IDF ────────────────────────────────────────────────────────────────────

hdr "ESP-IDF"
if command -v idf.py &>/dev/null; then
    IDF_VER=$(idf.py --version 2>/dev/null | head -1)
    if echo "$IDF_VER" | grep -q "v5.5.3"; then
        ok "ESP-IDF version: $IDF_VER"
    else
        warn "ESP-IDF found but version is not v5.5.3: $IDF_VER"
    fi
else
    fail "idf.py not found — source ~/esp-idf-v5.5.3/export.sh"
fi

# ─── Python + venv ──────────────────────────────────────────────────────────

hdr "Cloud Emulator Python Environment"
VENV="$REPO_ROOT/cloud_emulator/api/.venv"
if [ -d "$VENV" ]; then
    ok "venv exists: $VENV"
else
    fail "venv missing — run: cd cloud_emulator/api && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

REQ="$REPO_ROOT/cloud_emulator/api/requirements.txt"
if [ -f "$REQ" ]; then
    ok "requirements.txt found"
else
    warn "requirements.txt missing at $REQ"
fi

# Check Flask inside venv
FLASK_CHECK="$VENV/bin/python"
if [ -f "$FLASK_CHECK" ]; then
    if "$FLASK_CHECK" -c "import flask; print(flask.__version__)" &>/dev/null; then
        FLASK_VER=$("$FLASK_CHECK" -c "import flask; print(flask.__version__)")
        ok "Flask installed in venv: $FLASK_VER"
    else
        fail "Flask not installed in venv — activate venv and run: pip install -r requirements.txt"
    fi
fi

# ─── CA Key ─────────────────────────────────────────────────────────────────

hdr "PKI / CA Key"
CA_KEY="$REPO_ROOT/cloud_emulator/pki/ca.key"
CA_CRT="$REPO_ROOT/cloud_emulator/pki/ca.crt"

if [ -f "$CA_KEY" ]; then
    ok "ca.key present"
else
    fail "ca.key missing at $CA_KEY — restore from backup before running B3 or Proposed"
fi

if [ -f "$CA_CRT" ]; then
    ok "ca.crt present"
else
    fail "ca.crt missing at $CA_CRT"
fi

# ─── Token store ────────────────────────────────────────────────────────────

hdr "B2 Token Store"
TOKENS="$REPO_ROOT/cloud_emulator/api/b2_tokens.json"
TOKENS_EX="$REPO_ROOT/cloud_emulator/api/b2_tokens.example.json"
if [ -f "$TOKENS" ]; then
    ok "b2_tokens.json present"
elif [ -f "$TOKENS_EX" ]; then
    warn "b2_tokens.json missing — emulator will fall back to b2_tokens.example.json"
else
    fail "Neither b2_tokens.json nor b2_tokens.example.json found"
fi

# ─── Firmware source files ───────────────────────────────────────────────────

hdr "Firmware Source Files"
for FW in baseline1_http baseline2_token baseline3_enroll proposed_gateway; do
    SRC="$REPO_ROOT/esp32_firmware/$FW/main/http_request_example_main.c"
    if [ -f "$SRC" ]; then
        IP=$(grep -E '^#define WEB_SERVER' "$SRC" | head -1 | awk '{print $3}' | tr -d '"')
        PORT=$(grep -E '^#define WEB_PORT' "$SRC" | head -1 | awk '{print $3}' | tr -d '"')
        ok "$FW → target: $IP:$PORT"
    else
        fail "$FW source not found: $SRC"
    fi
done

# ─── Relay upstream ──────────────────────────────────────────────────────────

hdr "Pi Relay Configuration"
RELAY="$REPO_ROOT/gateway/pi/iot_gateway_relay.py"
if [ -f "$RELAY" ]; then
    UPSTREAM=$(grep "^UPSTREAM_HOST" "$RELAY" | head -1)
    ok "iot_gateway_relay.py found: $UPSTREAM"
else
    fail "iot_gateway_relay.py not found at $RELAY"
fi

GATEWAY="$REPO_ROOT/gateway/pi/iot_gateway_proposed.py"
if [ -f "$GATEWAY" ]; then
    ok "iot_gateway_proposed.py found"
else
    fail "iot_gateway_proposed.py not found at $GATEWAY"
fi

# ─── ESP32 USB ───────────────────────────────────────────────────────────────

hdr "ESP32 USB"
if [ -e /dev/ttyUSB0 ]; then
    ok "/dev/ttyUSB0 exists — ESP32 is attached to WSL"
else
    warn "/dev/ttyUSB0 not found — attach ESP32 via usbipd (Windows PowerShell: usbipd attach --wsl --busid <BUSID>)"
fi

# ─── Network ─────────────────────────────────────────────────────────────────

hdr "Network / Laptop IP"
LAPTOP_IP=$(ip addr show | grep "inet 172" | awk '{print $2}' | cut -d/ -f1 | head -1)
if [ -n "$LAPTOP_IP" ]; then
    ok "Laptop hotspot IP detected: $LAPTOP_IP"
else
    warn "Could not detect hotspot IP — check: ip addr show | grep 'inet 172'"
fi

# ─── Emulator liveness (optional) ────────────────────────────────────────────

hdr "Cloud Emulator Liveness"
if curl -sf http://localhost:5000/health &>/dev/null; then
    ok "Cloud emulator is running on localhost:5000"
else
    warn "Cloud emulator is NOT running — start it before flashing"
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "=============================="
echo "RESULT: $PASS OK  |  $WARN WARN  |  $FAIL FAIL"
echo "=============================="

if [ $FAIL -gt 0 ]; then
    echo "Fix FAIL items before proceeding."
    exit 1
elif [ $WARN -gt 0 ]; then
    echo "Check WARN items — they may not block your specific experiment."
    exit 0
else
    echo "Environment looks good."
    exit 0
fi
