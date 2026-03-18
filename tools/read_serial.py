#!/usr/bin/env python3
"""
Read serial console from MIDI Captain device.
Shows any errors or output from code.py.
"""

import sys
import time
import glob

def find_serial_port():
    """Find the MIDI Captain serial port."""
    ports = glob.glob('/dev/tty.usbmodem*')
    if ports:
        return ports[0]
    return None

def read_serial(port):
    """Read from serial port without pyserial dependency."""
    import os
    import termios
    
    # Open serial port
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    
    # Configure for 115200 baud
    attrs = termios.tcgetattr(fd)
    attrs[4] = attrs[5] = termios.B115200  # Set baud rate
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL  # 8N1
    attrs[0] = 0  # Input flags
    attrs[1] = 0  # Output flags
    attrs[3] = 0  # Local flags
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    
    print(f"Connected to {port}")
    print("Waiting for output... (press Ctrl+C to exit, Ctrl+D on device to reload)")
    print("-" * 60)
    
    buffer = b""
    try:
        while True:
            try:
                data = os.read(fd, 1024)
                if data:
                    buffer += data
                    # Print complete lines
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        try:
                            print(line.decode('utf-8', errors='replace'))
                        except:
                            print(line)
                else:
                    time.sleep(0.1)
            except OSError:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n" + "-" * 60)
        print("Disconnected")
    finally:
        os.close(fd)

if __name__ == '__main__':
    port = find_serial_port()
    if not port:
        print("No MIDI Captain device found!")
        print("Make sure it's plugged in and check /dev/tty.usbmodem*")
        sys.exit(1)
    
    read_serial(port)
