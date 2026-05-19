#!/usr/bin/env bash
# print_session_ips.sh
# Read-only. Prints current configured firmware targets and relay upstream,
# plus guidance for discovering the live laptop and Pi IPs.
# No changes are made by this script.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

B1_SRC="$REPO_ROOT/esp32_firmware/baseline1_http/main/http_request_example_main.c"
B3_SRC="$REPO_ROOT/esp32_firmware/baseline3_enroll/main/http_request_example_main.c"
RELAY_SRC="$REPO_ROOT/gateway/pi/iot_gateway_relay.py"

echo "===== IoT Onboarding Testbed — Session IP Reference ====="
echo ""

# --- Laptop IP guidance ---
echo "--- Current laptop IP (run this in WSL) ---"
LAPTOP_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1 || true)
if [ -n "$LAPTOP_IP" ]; then
    echo "  Detected: $LAPTOP_IP"
else
    echo "  Could not detect on eth0. Try:"
    echo "    hostname -I | awk '{print \$1}'"
    echo "    ip addr show   (look for the hotspot interface)"
fi
echo ""

# --- Pi IP guidance ---
echo "--- Pi IP (must be discovered manually) ---"
echo "  From WSL:  nmap -sn <subnet>/28   (e.g. nmap -sn 172.20.10.0/28)"
echo "  From Pi:   ip addr show wlan0 | grep 'inet '"
echo "  Or check hotspot admin page for connected clients."
echo ""

# --- B1 firmware target ---
echo "--- B1 firmware target (currently compiled in) ---"
if [ -f "$B1_SRC" ]; then
    grep -E "^#define WEB_SERVER|^#define WEB_PORT|^#define WEB_PATH" "$B1_SRC" | \
        awk '{printf "  %-20s %s\n", $2, $3}'
else
    echo "  NOT FOUND: $B1_SRC"
fi
echo ""

# --- B3 firmware target ---
echo "--- B3 firmware target (currently compiled in) ---"
if [ -f "$B3_SRC" ]; then
    grep -E "^#define WEB_SERVER|^#define WEB_PORT|^#define WEB_PATH" "$B3_SRC" | \
        awk '{printf "  %-20s %s\n", $2, $3}'
else
    echo "  NOT FOUND: $B3_SRC"
fi
echo ""

# --- Pi relay upstream ---
echo "--- Pi relay upstream (repo-side script) ---"
if [ -f "$RELAY_SRC" ]; then
    UPSTREAM=$(grep "^UPSTREAM_HOST" "$RELAY_SRC" | head -1)
    echo "  $UPSTREAM"
    echo "  (file: gateway/pi/iot_gateway_relay.py)"
else
    echo "  NOT FOUND: $RELAY_SRC"
    echo "  (relay script has not been copied into the repo yet)"
fi
echo ""

echo "--- To update targets, use ---"
echo "  bash scripts/handoff/update_b1_target.sh <server_ip> <port> <path>"
echo "  bash scripts/handoff/update_b3_target.sh <server_ip> <port> <path>"
echo "  bash scripts/handoff/update_pi_relay_upstream.sh <laptop_ip> <port>"
echo ""
echo "  See docs/handoff/network_rebind.md for the full rebind workflow."
