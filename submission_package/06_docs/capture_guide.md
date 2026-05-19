# Packet Capture Guide (Wireshark / tcpdump)

## Where to Capture
- Preferred: Attacker laptop NIC connected to the same LAN/Wi-Fi.
- Secondary: Gateway interface (Pi) for cross-check.

## What to Record
For each run:
- pcap file named: `run_<run_id>_<method>_<scenario>.pcap`
- note DUT IP, Gateway IP, timestamps, firmware version

## Wireshark Notes
- Apply display filter examples:
  - `http`
  - `tls`
  - `mqtt`
  - `ip.addr == <DUT_IP>`

## tcpdump (Gateway or Laptop)
Capture everything (simple, later filter in Wireshark):
- Interface can be wlan0/eth0 depending on device.

Output folder:
- `capture/pcaps/`
