#!/bin/bash

# RUSTDAMN - Auto WiFi Deauth System
# Fixed Ubuntu Installation Script
# Auto-installs ALL dependencies correctly

set -e

echo "╔═══════════════════════════════════════════════════╗"
echo "║  RUSTDAMN - WiFi Deauth System                    ║"
echo "║  Auto-Install All Dependencies                    ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ ERROR: Must run as root!"
   echo "Usage: sudo bash install.sh"
   exit 1
fi

echo "[1/6] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo "[2/6] Installing build tools..."
apt-get install -y -qq \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    curl \
    wget \
    software-properties-common

echo "[3/6] Installing wireless tools (CORRECT packages)..."
# These are the CORRECT package names for aircrack-ng suite
apt-get install -y -qq \
    aircrack-ng \
    wireless-tools \
    wpasupplicant \
    hostapd \
    dnsmasq \
    macchanger \
    net-tools \
    iw

# Install mdk3/mdk4 from source if not available
echo "[4/6] Installing MDK3/MDK4..."
apt-get install -y -qq mdk3 mdk4 2>/dev/null || {
    echo "Installing MDK3/MDK4 from source..."
    cd /tmp
    
    # MDK3
    if ! command -v mdk3 &> /dev/null; then
        echo "  → Compiling MDK3..."
        git clone https://github.com/aircrack-ng/mdk3.git -q 2>/dev/null || true
        if [ -d mdk3 ]; then
            cd mdk3
            make -j$(nproc) > /dev/null 2>&1 || true
            cp mdk3 /usr/local/bin/ 2>/dev/null || true
            cd ..
        fi
    fi
    
    # MDK4
    if ! command -v mdk4 &> /dev/null; then
        echo "  → Compiling MDK4..."
        git clone https://github.com/aircrack-ng/mdk4.git -q 2>/dev/null || true
        if [ -d mdk4 ]; then
            cd mdk4
            make -j$(nproc) > /dev/null 2>&1 || true
            [ -f mdk4 ] && cp mdk4 /usr/local/bin/ || true
            [ -f src/mdk4 ] && cp src/mdk4 /usr/local/bin/ || true
            cd ..
        fi
    fi
}

echo "[5/6] Installing Python3 dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-dev

# Install Python packages
pip3 install -q --upgrade pip 2>/dev/null || true
pip3 install -q \
    scapy \
    colorama \
    requests \
    paramiko 2>/dev/null || true

echo "[6/6] Creating directories and finalizing..."
mkdir -p /opt/rustdamn/{logs,captures,config,firmware}
mkdir -p /var/log/rustdamn

# Copy scripts
if [ -f src/auto_deauth.py ]; then
    cp src/auto_deauth.py /opt/rustdamn/
    chmod +x /opt/rustdamn/auto_deauth.py
fi

if [ -f config/auto-deauth.conf ]; then
    cp config/auto-deauth.conf /opt/rustdamn/
fi

chmod 755 /opt/rustdamn
chmod 777 /var/log/rustdamn

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                        ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "📋 Verify Installation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verify tools
echo "Checking installed tools:"
echo ""

for tool in airmon-ng airodump-ng aireplay-ng mdk3 mdk4 macchanger; do
    if command -v $tool &> /dev/null; then
        echo "  ✅ $tool"
    else
        echo "  ⚠️  $tool - (may need manual compilation)"
    fi
done

echo ""
echo "📚 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Check your wireless interface:"
echo "   $ iwconfig"
echo ""
echo "2. Run RUSTDAMN (replace wlan0 with your interface):"
echo "   $ sudo python3 src/auto_deauth.py wlan0"
echo ""
echo "3. Monitor logs in another terminal:"
echo "   $ tail -f /var/log/rustdamn/deauth.log"
echo ""
echo "4. Edit configuration:"
echo "   $ sudo nano config/auto-deauth.conf"
echo ""
echo "⚠️  LEGAL WARNING:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Only test on networks you OWN or have written"
echo "permission to test. Unauthorized use is ILLEGAL."
echo ""
