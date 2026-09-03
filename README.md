# WiFi Security Lab - Auto-Deauth System

**Automatic WiFi Deauthentication Testing Environment for Ubuntu**

A comprehensive wireless security testing tool that automatically detects WiFi signals (BSSID/SSID) and triggers deauthentication attacks using MDK3/MDK4. Works with standard WiFi routers - **no extra hardware needed**.

## ⚡ Features

✅ **Automatic Signal Detection** - Scans and detects WiFi networks in real-time
✅ **Auto-Deauth Trigger** - Automatically triggers deauthentication when signals detected
✅ **MDK3/MDK4 Support** - Uses most effective wireless attack tools
✅ **MAC Address Randomization** - Changes MAC after each attack to avoid detection
✅ **Aireplay Fallback** - Multiple deauth methods for reliability
✅ **Logging & Monitoring** - Comprehensive logs of all activities
✅ **Works Anywhere** - Standard WiFi router, no SDR/microcontroller needed
✅ **Signal Strength Monitoring** - Detects by BSSID, SSID, and signal power (dBm)

## 📋 Requirements

- **Ubuntu 20.04+** (64-bit)
- **Wireless Adapter** with monitor mode support
- **Root/Sudo Access**
- **Internet Connection** (for initial setup)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/ghost4715/wifi-security-testlab.git
cd wifi-security-testlab
```

### 2. Install Dependencies
```bash
sudo bash install.sh
```

### 3. Check Your Wireless Interface
```bash
iwconfig
ip link show
```

### 4. Run Auto-Deauth System
```bash
sudo python3 src/auto_deauth.py wlan0
```

**Replace `wlan0` with your actual wireless interface name**

## 📖 Usage

### Basic Usage
```bash
# Using default interface (wlan0)
sudo python3 src/auto_deauth.py

# Using specific interface
sudo python3 src/auto_deauth.py wlan1
```

### Monitor Logs
```bash
# Real-time log monitoring
tail -f /var/log/wifi-auto-deauth.log

# View detected networks
cat /tmp/deauth_networks.json
```

### Stop the System
```bash
# Press CTRL+C in the terminal running the script
# System will automatically restore interface to normal mode
```

## 🔧 Configuration

Edit `config/auto-deauth.conf` to customize behavior:

```ini
[INTERFACE]
interface = wlan0              # Your wireless interface

[SCAN]
scan_interval = 5              # Scan every 5 seconds
signal_threshold = -75         # Trigger on strong signals

[DEAUTH]
packet_count = 10              # Number of deauth packets
methods = mdk3, mdk4, aireplay # Methods to use

[LOGGING]
level = INFO                   # Log level
```

## 🎯 How It Works

1. **Monitor Mode** - Enables monitor mode on wireless adapter
2. **Network Scanning** - Continuously scans for WiFi networks using airodump-ng
3. **Signal Detection** - Detects networks by BSSID, SSID, and signal strength
4. **Deauth Trigger** - When signal detected, triggers automatic deauthentication
5. **Multi-Method Attack** - Uses MDK3 → MDK4 → Aireplay for reliability
6. **MAC Randomization** - Changes MAC address after each attack
7. **Logging** - Records all activities for analysis

## 🛡️ Safety & Legal Notice

⚠️ **IMPORTANT - READ BEFORE USE:**

- ✅ Only use on networks you **OWN** or have **explicit written permission** to test
- ✅ Unauthorized network interference is **ILLEGAL** in most countries
- ✅ Use in **controlled lab environments** only
- ✅ This tool is for **educational and authorized security testing** purposes
- ✅ Never use against networks you don't own or haven't been authorized to test

**Violating network security laws can result in:**
- Criminal prosecution
- Heavy fines
- Imprisonment
- Civil liability

## 📊 Troubleshooting

### Issue: "Missing tools" error
```bash
# Reinstall dependencies
sudo apt-get install aircrack-ng mdk3 mdk4 macchanger
```

### Issue: "No networks found"
- Ensure wireless adapter is plugged in
- Check adapter is in range of networks
- Run: `iwconfig` to verify adapter is present
- Try different location with stronger signals

### Issue: "Permission denied"
- Must run with sudo: `sudo python3 src/auto_deauth.py`
- Check user has sudo access

### Issue: Interface not in monitor mode
```bash
# Manually enable monitor mode
sudo airmon-ng check kill
sudo airmon-ng start wlan0
```

### Check Logs for Details
```bash
tail -f /var/log/wifi-auto-deauth.log
```

## 📁 Directory Structure

```
wifi-security-testlab/
├── src/
│   └── auto_deauth.py         # Main auto-deauth script
├── config/
│   └── auto-deauth.conf       # Configuration file
├── install.sh                 # Installation script
├── README.md                  # This file
└── docs/
    └── MANUAL.md              # Detailed manual
```

## 🔍 Detection Methods

The system automatically detects:

1. **BSSID** - MAC address of router (XX:XX:XX:XX:XX:XX)
2. **SSID** - Network name (WiFi network name)
3. **Signal Strength** - Power level in dBm (-80 to -20)
4. **Channels** - WiFi channels (1-13)
5. **Hidden Networks** - Networks not broadcasting SSID

## 📈 Output Example

```
[2026-09-03 10:30:45] - INFO - ============================================================
[2026-09-03 10:30:45] - INFO - AUTO-DEAUTH SYSTEM STARTED
[2026-09-03 10:30:45] - INFO - Interface: wlan0mon
[2026-09-03 10:30:45] - INFO - Scan Interval: 5s
[2026-09-03 10:30:45] - INFO - Status: LISTENING FOR SIGNALS...
[2026-09-03 10:30:50] - INFO - [Scan #1] Checking for networks...
[2026-09-03 10:30:55] - INFO - [+] NEW NETWORK DETECTED: MyRouter (AA:BB:CC:DD:EE:FF) | Power: -65dBm
[2026-09-03 10:31:00] - INFO - ============================================================
[2026-09-03 10:31:00] - INFO - [!] DEAUTH TRIGGERED
[2026-09-03 10:31:00] - INFO -     BSSID: AA:BB:CC:DD:EE:FF
[2026-09-03 10:31:00] - INFO -     SSID:  MyRouter
[2026-09-03 10:31:03] - INFO - [*] MDK3 Deauth → BSSID: AA:BB:CC:DD:EE:FF | SSID: MyRouter
[2026-09-03 10:31:03] - INFO - ✓ MDK3 deauth sent to AA:BB:CC:DD:EE:FF
```

## 📚 Commands Reference

| Command | Purpose |
|---------|----------|
| `sudo python3 src/auto_deauth.py wlan0` | Start auto-deauth on wlan0 |
| `iwconfig` | Show wireless interfaces |
| `sudo airmon-ng start wlan0` | Enable monitor mode manually |
| `sudo airmon-ng stop wlan0mon` | Disable monitor mode manually |
| `sudo macchanger -r wlan0` | Change MAC address |
| `tail -f /var/log/wifi-auto-deauth.log` | View live logs |

## 🤝 Contributing

To contribute improvements:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/improvements`
3. Commit changes: `git commit -am 'Add improvements'`
4. Push to branch: `git push origin feature/improvements`
5. Submit pull request

## 📜 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This project is provided for **educational and authorized security testing purposes only**. Users are responsible for ensuring they have proper authorization before using this tool. Unauthorized use against networks you don't own is illegal.

---

**Repository:** https://github.com/ghost4715/wifi-security-testlab
**Author:** ghost4715
**Created:** 2026-09-03
