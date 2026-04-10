#!/usr/bin/env python3
"""Utility to detect connected PC/SC NFC readers.

Run on the HOST (not inside Docker) to find out which readers are available
and get the recommended docker-compose device mount configuration.

Usage:
    python detect_readers.py
"""

import subprocess
import sys

try:
    from smartcard.System import readers
    from smartcard.util import toHexString

    HAS_PCSCD = True
except ImportError:
    HAS_PCSCD = False


def main():
    print("=" * 60)
    print("PulseID — NFC Reader Detection Utility")
    print("=" * 60)
    print()

    if not HAS_PCSCD:
        print("[!] pyscard is not installed.")
        print("    Install it with: pip install pyscard")
        print("    You also need pcscd: sudo apt install pcscd (Linux)")
        sys.exit(1)

    try:
        available = readers()
    except Exception as e:
        print(f"[!] Could not list readers: {e}")
        print("    Make sure the pcscd service is running:")
        print("      Linux:  sudo systemctl start pcscd")
        print("      macOS:  pcscd runs automatically")
        sys.exit(1)

    if not available:
        print("[!] No PC/SC readers found.")
        print("    Make sure your NFC reader is connected via USB.")
        print()
        _print_usb_devices()
        sys.exit(1)

    print(f"[+] Found {len(available)} reader(s):\n")
    for i, r in enumerate(available):
        print(f"    {i}: {r}")

    print()
    print("-" * 60)
    print("Docker Compose configuration:")
    print("-" * 60)
    print()
    print("Add the following to the 'backend' service in docker-compose.yml:")
    print()
    print("    backend:")
    print("      privileged: true")
    print("      volumes:")
    print('        - /dev/bus/usb:/dev/bus/usb')
    print()
    print("Or for a more restrictive setup, mount only the specific USB device.")
    print()

    _print_usb_devices()

    print()
    print("Set the PULSEID_READER_FILTER env var to target a specific reader:")
    for r in available:
        name = str(r)
        short = name.split(" ")[0] if " " in name else name[:10]
        print(f'    PULSEID_READER_FILTER="{short}"')

    print()

    # Try to read a badge
    print("-" * 60)
    print("Quick test — hold a badge on the reader...")
    reader = available[0]
    conn = reader.createConnection()
    try:
        conn.connect()
        data, sw1, sw2 = conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
        if (sw1, sw2) == (0x90, 0x00):
            uid = toHexString(data).replace(" ", "").lower()
            print(f"[+] Badge UID: {uid}")
        else:
            print(f"[!] Reader responded but could not read UID (SW={sw1:02X}{sw2:02X}).")
            print("    Place a badge on the reader and run again.")
    except Exception as e:
        print(f"[!] No badge detected: {e}")
        print("    Place a badge on the reader and run again.")
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass


def _print_usb_devices():
    print("Connected USB devices:")
    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")
        else:
            print("    (lsusb not available)")
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.strip().split("\n")[:30]:
                print(f"    {line}")
        except Exception:
            print("    (Could not list USB devices)")
    except Exception:
        print("    (Could not list USB devices)")


if __name__ == "__main__":
    main()
