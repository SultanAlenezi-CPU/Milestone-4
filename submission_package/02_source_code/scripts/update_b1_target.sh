#!/usr/bin/env bash
# update_b1_target.sh
# Updates WEB_SERVER, WEB_PORT, WEB_PATH in the B1 firmware source.
# Does NOT build or flash. Run `idf.py build` manually after this.
#
# Usage: ./scripts/handoff/update_b1_target.sh <server_ip> <port> <path>
# Example (direct):  ./scripts/handoff/update_b1_target.sh 172.20.10.3 5000 /health
# Example (via Pi):  ./scripts/handoff/update_b1_target.sh 172.20.10.5 8080 /health

set -euo pipefail

if [ $# -ne 3 ]; then
    echo "Usage: $0 <server_ip> <port> <path>"
    echo "  server_ip : IP address of target (laptop or Pi)"
    echo "  port      : TCP port (e.g. 5000 for direct, 8080 for via Pi)"
    echo "  path      : URL path (e.g. /health)"
    echo ""
    echo "Example: $0 172.20.10.3 5000 /health"
    exit 1
fi

NEW_IP="$1"
NEW_PORT="$2"
NEW_PATH="$3"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET_FILE="$REPO_ROOT/esp32_firmware/baseline1_http/main/http_request_example_main.c"

if [ ! -f "$TARGET_FILE" ]; then
    echo "ERROR: Target file not found:"
    echo "  $TARGET_FILE"
    exit 1
fi

echo "--- B1 firmware target update ---"
echo "File: $TARGET_FILE"
echo ""

# Print current values
echo "Current values:"
grep -E "^#define WEB_SERVER|^#define WEB_PORT|^#define WEB_PATH" "$TARGET_FILE" | \
    awk '{printf "  %-20s %s\n", $2, $3}'
echo ""

# Apply changes
sed -i "s|^#define WEB_SERVER .*|#define WEB_SERVER \"$NEW_IP\"|" "$TARGET_FILE"
sed -i "s|^#define WEB_PORT   .*|#define WEB_PORT   \"$NEW_PORT\"|" "$TARGET_FILE"
sed -i "s|^#define WEB_PATH   .*|#define WEB_PATH   \"$NEW_PATH\"|" "$TARGET_FILE"

# Print new values
echo "New values:"
grep -E "^#define WEB_SERVER|^#define WEB_PORT|^#define WEB_PATH" "$TARGET_FILE" | \
    awk '{printf "  %-20s %s\n", $2, $3}'
echo ""

echo "Done. Rebuild required before flashing:"
echo "  cd esp32_firmware/baseline1_http && idf.py build"
