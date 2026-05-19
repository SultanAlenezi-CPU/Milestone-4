#!/usr/bin/env bash
# update_pi_relay_upstream.sh
# Updates UPSTREAM_HOST in the repo-side Pi relay script.
# Does NOT SSH to the Pi or restart the relay automatically.
# After running this, manually scp the updated script to the Pi and restart.
#
# Usage: ./scripts/handoff/update_pi_relay_upstream.sh <laptop_ip> <port>
# Example: ./scripts/handoff/update_pi_relay_upstream.sh 172.20.10.3 5000

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <laptop_ip> <port>"
    echo "  laptop_ip : current hotspot IP of the laptop running the cloud emulator"
    echo "  port      : cloud emulator port (normally 5000)"
    echo ""
    echo "Example: $0 172.20.10.3 5000"
    exit 1
fi

NEW_IP="$1"
NEW_PORT="$2"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RELAY_FILE="$REPO_ROOT/gateway/pi/iot_gateway_relay.py"

if [ ! -f "$RELAY_FILE" ]; then
    echo "ERROR: Repo-side relay script not found:"
    echo "  $RELAY_FILE"
    echo ""
    echo "The relay script has not been copied into the repo yet."
    echo "See docs/handoff/network_rebind.md for the rebind workflow."
    exit 1
fi

echo "--- Pi relay upstream update ---"
echo "File: $RELAY_FILE"
echo ""

# Print current value
echo "Current value:"
grep "^UPSTREAM_HOST" "$RELAY_FILE" | awk '{printf "  %s\n", $0}'
echo ""

# Apply change
NEW_UPSTREAM="http://$NEW_IP:$NEW_PORT"
sed -i "s|^UPSTREAM_HOST = .*|UPSTREAM_HOST = \"$NEW_UPSTREAM\"|" "$RELAY_FILE"

# Print new value
echo "New value:"
grep "^UPSTREAM_HOST" "$RELAY_FILE" | awk '{printf "  %s\n", $0}'
echo ""

echo "Done. The repo-side script has been updated."
echo ""
echo "Next steps (manual):"
echo "  1. Copy to Pi:"
echo "       scp gateway/pi/iot_gateway_relay.py pi@<PI_IP>:~/iot_gateway_relay.py"
echo "  2. Restart relay on Pi:"
echo "       ssh pi@<PI_IP> 'pkill -f iot_gateway_relay.py; python3 ~/iot_gateway_relay.py'"
echo ""
echo "  See docs/handoff/network_rebind.md for full context."
