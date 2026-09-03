# WiFi Auto-Deauth - Complete Usage Guide

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Running the System](#running-the-system)
3. [Configuration](#configuration)
4. [Monitoring](#monitoring)
5. [Advanced Usage](#advanced-usage)

## Initial Setup

### Step 1: Verify Ubuntu Installation
```bash
lsb_release -a
# Should be Ubuntu 20.04 or newer
```

### Step 2: Install Dependencies
```bash
cd wifi-security-testlab
sudo bash install.sh
```

### Step 3: Identify Your Wireless Interface
```bash
# Method 1: Using iwconfig
iwconfig

# Method 2: Using ip command
ip link show

# Look for: wlan0, wlan1, wlp3s0, etc.
# Example output:
# wlan0: flags=UP,BROADCAST,RUNNING,MULTICAST...
#        inet 192.168.1.100
```

## Running the System

### Quick Start (Default Interface)
```bash
sudo python3 src/auto_deauth.py
# Uses wlan0 by default
```

### Specify Interface
```bash
# If your interface is wlan1
sudo python3 src/auto_deauth.py wlan1

# If your interface is wlp3s0
sudo python3 src/auto_deauth.py wlp3s0
```

### Expected Output
```
2026-09-03 10:30:45,123 - INFO - ============================================================
2026-09-03 10:30:45,123 - INFO - AUTO-DEAUTH SYSTEM STARTED
2026-09-03 10:30:45,123 - INFO - ============================================================
2026-09-03 10:30:45,123 - INFO - [*] Enabling monitor mode on wlan0...
2026-09-03 10:30:47,234 - INFO - ✓ Monitor mode enabled: wlan0mon
2026-09-03 10:30:47,234 - INFO - Interface: wlan0mon
2026-09-03 10:30:47,234 - INFO - Scan Interval: 5s
2026-09-03 10:30:47,234 - INFO - Status: LISTENING FOR SIGNALS...
```

### Stop the System
```bash
# Press CTRL+C
# System will automatically:
# - Disable monitor mode
# - Restore interface to normal
# - Close all connections
```

## Configuration

### Edit Configuration File
```bash
sudo nano config/auto-deauth.conf
```

### Key Configuration Options

#### Interface Settings
```ini
[INTERFACE]
interface = wlan0              # Your wireless interface name
```

#### Scan Settings
```ini
[SCAN]
scan_interval = 5              # Seconds between scans (1-60)
signal_threshold = -75         # dBm threshold (-80 to -20)
randomize_mac = true           # Change MAC after each attack
```

**Signal Strength Reference:**
- `-80 dBm` = Very strong signal
- `-75 dBm` = Strong signal  
- `-70 dBm` = Good signal
- `-60 dBm` = Excellent signal
- `-50 dBm` = Extremely strong (very close)

#### Deauthentication Settings
```ini
[DEAUTH]
packet_count = 10              # Number of deauth packets (5-50)
methods = mdk3, mdk4, aireplay # Attack methods in order
cycle_delay = 10               # Seconds between cycles
max_attempts = 5               # Max attempts per network
```

#### Logging Settings
```ini
[LOGGING]
level = INFO                   # DEBUG, INFO, WARNING, ERROR
logfile = /var/log/wifi-auto-deauth.log
save_json = true              # Save network list as JSON
```

## Monitoring

### View Live Logs
```bash
# Real-time log monitoring
tail -f /var/log/wifi-auto-deauth.log

# Last 50 lines
tail -50 /var/log/wifi-auto-deauth.log

# Follow and search
tail -f /var/log/wifi-auto-deauth.log | grep "TRIGGERED"
```

### View Detected Networks
```bash
# JSON format
cat /tmp/deauth_networks.json

# Pretty print
jq . /tmp/deauth_networks.json
```

### Monitor System Resources
```bash
# Check CPU/Memory usage
watch -n 1 'ps aux | grep auto_deauth'

# Check wireless adapter status
iwconfig wlan0

# Monitor network traffic
sudo wireshark
```

## Advanced Usage

### Run as Background Service
```bash
# Create systemd service
sudo tee /etc/systemd/system/wifi-auto-deauth.service > /dev/null <<EOF
[Unit]
Description=WiFi Auto-Deauth System
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/wifi-security-testlab/auto_deauth.py wlan0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable wifi-auto-deauth
sudo systemctl start wifi-auto-deauth

# Check status
sudo systemctl status wifi-auto-deauth

# View service logs
sudo journalctl -u wifi-auto-deauth -f
```

### Multiple Interfaces
```bash
# Terminal 1 - Interface 1
sudo python3 src/auto_deauth.py wlan0

# Terminal 2 - Interface 2  
sudo python3 src/auto_deauth.py wlan1
```

### Custom Log Rotation
```bash
# Create logrotate config
sudo tee /etc/logrotate.d/wifi-auto-deauth > /dev/null <<EOF
/var/log/wifi-auto-deauth.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
}
EOF
```

### Enable Debug Mode
```bash
# Edit config for debug logging
sudo sed -i 's/level = INFO/level = DEBUG/' config/auto-deauth.conf

# Run with debug output
sudo python3 src/auto_deauth.py
```

## Troubleshooting Guide

### Issue: "Module not found: subprocess"
```bash
# Shouldn't happen, but reinstall Python3
sudo apt-get install --reinstall python3
```

### Issue: Wireless interface not detected
```bash
# List all interfaces
ip link show
iwconfig

# If no wireless adapter:
# 1. Check if adapter is plugged in/enabled
# 2. Check BIOS for hardware enable
# 3. Run: sudo rfkill list (check if blocked)
# 4. Unblock if needed: sudo rfkill unblock wifi
```

### Issue: Permission denied errors
```bash
# Must use sudo
sudo python3 src/auto_deauth.py

# Add user to sudo group (optional)
sudo usermod -aG sudo $USER
newgrp sudo
```

### Issue: Monitor mode won't enable
```bash
# Kill interfering processes
sudo airmon-ng check kill

# Try manual enable
sudo ifconfig wlan0 down
sudo iwconfig wlan0 mode Monitor
sudo ifconfig wlan0 up

# Verify
iwconfig wlan0
```

### Issue: No networks detected
```bash
# Check if there are networks to detect
wifi scan  # Some systems

# Try different location with stronger signals
# Move closer to a router

# Increase scan time in config
sudo sed -i 's/scan_interval = 5/scan_interval = 10/' config/auto-deauth.conf
```

## Performance Tips

1. **Faster Detection**: Decrease `scan_interval` (but increases CPU)
2. **Better Reliability**: Increase `deauth_count` (but slower attacks)
3. **Stealthy Mode**: Increase MAC randomization frequency
4. **Lower CPU**: Increase `scan_interval` (but slower detection)

## Safety Reminders

✅ **Only test on authorized networks**
✅ **Use in controlled lab environments**
✅ **Keep proper documentation**
✅ **Get written permission before testing**
✅ **Never test against networks you don't own**

---

For more information, see README.md
