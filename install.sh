#!/bin/bash

# Wireless WiFi Security Lab - Ubuntu Installation Script
# Auto-Deauth System with Signal Detection & SDR Support

set -e

echo "================================================"
echo "Wireless WiFi Security Lab - Ubuntu Setup"
echo "================================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use: sudo bash install.sh)"
   exit 1
fi

echo "[*] Updating system packages..."
apt-get update && apt-get upgrade -y

echo "[*] Installing core wireless tools..."
apt-get install -y \
    aircrack-ng \
    airsnort \
    airodump-ng \
    aireplay-ng \
    mdk3 \
    mdk4 \
    kismet \
    wireshark \
    wireless-tools \
    wpasupplicant \
    hostapd \
    dnsmasq \
    iptables \
    ethtool

echo "[*] Installing Python dependencies..."
apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential

echo "[*] Installing MAC address changer..."
apt-get install -y macchanger

echo "[*] Creating necessary directories..."
mkdir -p /opt/wifi-security-lab/{logs,captures,config,firmware}
chmod 755 /opt/wifi-security-lab

echo "[*] Setting up auto-deauth script..."
cp src/auto_deauth.py /opt/wifi-security-lab/
chmod +x /opt/wifi-security-lab/auto_deauth.py

echo "[*] Copying configuration..."
cp config/auto-deauth.conf /opt/wifi-security-lab/

echo "[*] Installation complete!"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Check wireless adapter: iwconfig"
echo "2. List adapters: ip link show"
echo "3. Run auto-deauth:"
echo "   sudo python3 src/auto_deauth.py wlan0"
echo ""
echo "Replace 'wlan0' with your adapter name if different"
echo "Logs: tail -f /var/log/wifi-auto-deauth.log"
echo "================================================"
