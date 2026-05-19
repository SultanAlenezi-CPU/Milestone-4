#!/usr/bin/env bash
# verify_runtime_chain.sh
# Checks that the full testbed chain is reachable BEFORE you flash the ESP32.
# Run after starting the cloud emulator and Pi gateway/relay.
#
# Usage: bash scripts/handoff/verify_runtime_chain.sh [PI_IP] [LAPTOP_HOTSPOT_IP]
# If IPs not given, the script tries to detect them.
#
# Example:
#   bash scripts/handoff/verify_runtime_chain.sh 172.20.10.4 172.20.10.2

set -uo pipefail

PASS=0
FAIL=0
WARN=0

ok()   { echo "  [OK]   $1"; PASS=$((PASS+1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
warn() { echo "  [WARN] $1"; WARN=$((WARN+1)); }
hdr()  { echo ""; echo "=== $1 ==="; }

TIMEOUT=3   # seconds per curl check

# ─── Resolve IPs ────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RELAY_SRC="$REPO_ROOT/gateway/pi/iot_gateway_relay.py"

# Pi IP: from argument or try the compiled relay upstream
if [ "${1:-}" != "" ]; then
    PI_IP="$1"
else
    # Try to read from relay source
    UPSTREAM_LINE=$(grep "^UPSTREAM_HOST" "$RELAY_SRC" 2>/dev/null | head -1 || true)
    # UPSTREAM_HOST = "http://172.20.10.2:5000" → extract 172.20.10.x
    PI_IP=""
    warn "PI_IP not provided — pass as first argument: $0 <PI_IP> [LAPTOP_IP]"
    warn "Skipping Pi-side checks"
fi

# Laptop hotspot IP: from argument or detect
if [ "${2:-}" != "" ]; then
    LAPTOP_IP="$2"
else
    LAPTOP_IP=$(ip addr show | grep "inet 172" | awk '{print $2}' | cut -d/ -f1 | head -1 || true)
fi

echo "Configuration:"
echo "  Laptop hotspot IP : ${LAPTOP_IP:-<not detected>}"
echo "  Pi IP             : ${PI_IP:-<not provided — Pi checks skipped>}"

# ─── 1. Cloud emulator (local) ───────────────────────────────────────────────

hdr "1. Cloud Emulator — localhost:5000"
HEALTH=$(curl -sf --max-time $TIMEOUT http://localhost:5000/health 2>/dev/null || true)
if echo "$HEALTH" | grep -q '"ok"'; then
    ok "GET /health → $HEALTH"
else
    fail "Cloud emulator not responding — start it: cd cloud_emulator/api && source .venv/bin/activate && python app.py"
fi

# ─── 2. Emulator reachable via hotspot IP ────────────────────────────────────

hdr "2. Cloud Emulator — ${LAPTOP_IP}:5000 (hotspot interface)"
if [ -n "${LAPTOP_IP:-}" ]; then
    HEALTH2=$(curl -sf --max-time $TIMEOUT "http://$LAPTOP_IP:5000/health" 2>/dev/null || true)
    if echo "$HEALTH2" | grep -q '"ok"'; then
        ok "GET http://$LAPTOP_IP:5000/health → $HEALTH2"
    else
        fail "Emulator not reachable on hotspot IP $LAPTOP_IP:5000 — check firewall or that emulator is bound to 0.0.0.0"
    fi
else
    warn "Laptop hotspot IP not detected — skipping hotspot reachability check"
fi

# ─── 3. Pi reachability ──────────────────────────────────────────────────────

if [ -n "${PI_IP:-}" ]; then

    hdr "3. Pi — SSH reachability"
    if ssh -o ConnectTimeout=$TIMEOUT -o BatchMode=yes "pi@$PI_IP" "echo PI_SSH_OK" 2>/dev/null | grep -q "PI_SSH_OK"; then
        ok "SSH to pi@$PI_IP works"
    else
        fail "SSH to pi@$PI_IP failed — is the Pi on the hotspot? Check IP."
    fi

    hdr "4. Pi Dumb Relay — $PI_IP:8080"
    RELAY_H=$(curl -sf --max-time $TIMEOUT "http://$PI_IP:8080/health" 2>/dev/null || true)
    if echo "$RELAY_H" | grep -q '"ok"'; then
        ok "GET http://$PI_IP:8080/health → $RELAY_H"
    else
        warn "Pi relay (port 8080) not responding — start it: ssh pi@$PI_IP 'python3 ~/iot_gateway_relay.py'"
    fi

    hdr "5. Pi Proposed Gateway — $PI_IP:8090"
    GW_H=$(curl -sf --max-time $TIMEOUT "http://$PI_IP:8090/health" 2>/dev/null || true)
    if echo "$GW_H" | grep -q '"ok"'; then
        ok "GET http://$PI_IP:8090/health → $GW_H"
    else
        warn "Pi proposed gateway (port 8090) not responding — start it: ssh pi@$PI_IP 'UPSTREAM_HOST=http://$LAPTOP_IP:5000 python3 ~/iot_gateway_proposed.py'"
    fi

    hdr "6. End-to-end — Pi relay → emulator"
    if [ -n "${LAPTOP_IP:-}" ]; then
        E2E=$(curl -sf --max-time $((TIMEOUT*2)) "http://$PI_IP:8080/health" 2>/dev/null || true)
        if echo "$E2E" | grep -q '"ok"'; then
            ok "GET http://$PI_IP:8080/health (via relay) → $E2E"
        else
            fail "End-to-end via relay failed — relay may be up but cannot reach emulator. Check UPSTREAM_HOST in iot_gateway_relay.py"
        fi
    fi

else
    hdr "3–6. Pi Checks — SKIPPED (no PI_IP provided)"
    warn "Re-run with PI_IP to check Pi relay and gateway: $0 <PI_IP>"
fi

# ─── 7. ESP32 USB ────────────────────────────────────────────────────────────

hdr "7. ESP32 USB"
if [ -e /dev/ttyUSB0 ]; then
    ok "/dev/ttyUSB0 present — ESP32 is ready to flash"
else
    warn "/dev/ttyUSB0 not found — attach via usbipd (Windows PowerShell: usbipd attach --wsl --busid <BUSID>)"
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "=============================="
echo "CHAIN CHECK: $PASS OK  |  $WARN WARN  |  $FAIL FAIL"
echo "=============================="

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "STOP. Fix FAIL items before flashing."
    echo "Flashing with a broken chain wastes a run and may corrupt token state."
    exit 1
elif [ $WARN -gt 0 ]; then
    echo ""
    echo "Review WARN items. Some may not matter for your current experiment."
    exit 0
else
    echo ""
    echo "Chain looks good. Safe to build and flash."
    exit 0
fi
