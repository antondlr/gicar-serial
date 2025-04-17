#!/usr/bin/env python3
"""
Ascaso Baby T Writer

This script generates write commands for an Ascaso Baby T espresso machine.
"""

import argparse
import os
import sys
import time
import serial
from typing import Dict, Any

# Import from our library
from lib.ascaso_common import (
    load_or_create_payload, build_write_command, set_value, 
    extract_value, dump_payload, build_request, load_payload_from_response
)
from lib.ascaso_offsets import MEMORY_MAP

class AscasoWriter:
    def __init__(self, payload, response_header=None):
        """
        Initialize the writer with a payload.
        
        Args:
            payload: Initial payload bytearray
            response_header: The header of the response (e.g., "r000500D7")
        """
        # Convert payload to bytearray if it's bytes to make it mutable
        if isinstance(payload, bytes):
            self.payload = bytearray(payload)
        else:
            self.payload = payload
        # Extract offset from response header if provided
        self.offset_adjustment = 0
        if response_header and response_header.startswith('r') and len(response_header) >= 9:
            try:
                self.offset_adjustment = int(response_header[1:5], 16)
                print(f"Using dynamic offset adjustment of {self.offset_adjustment} from response header")
            except ValueError:
                # Fallback to default if we can't parse the header
                self.offset_adjustment = 5
                print(f"Could not parse header offset, using default: {self.offset_adjustment}")
        else:
            # Use default offset adjustment if header not provided
            self.offset_adjustment = 5
            print(f"No response header provided, using default offset adjustment: {self.offset_adjustment}")
    
    def set_value_by_key(self, key, value):
        """
        Set a value in the payload based on a key from the memory map.
        
        Args:
            key: The key in MEMORY_MAP
            value: The value to set (will be transformed according to memory map)
            
        Returns:
            True if successful, False otherwise
        """
        if key not in MEMORY_MAP:
            print("Unknown key: {}".format(key), file=sys.stderr)
            return False
        
        entry = MEMORY_MAP[key]
        
        # Check if this is a readonly value
        if entry.get("readonly", False):
            print("Cannot write to readonly key: {}".format(key), file=sys.stderr)
            return False
        
        # For writing, use the absolute offset without adjustment
        offset = entry["offset"]  # No offset adjustment for writing
        value_type = entry["type"]
        
        # For values with predefined states
        if "values" in entry:
            values = entry["values"]
            # Handle string values like "on"/"off"
            if isinstance(value, str) and value in values.keys():
                # Get the actual value to write
                write_value = values[value]
                if isinstance(write_value, str):
                    print("Cannot write expression value: {}".format(write_value), file=sys.stderr)
                    return False
                
                # Set the value
                set_value(self.payload, offset, write_value, value_type)
                return True
        
        # For values with a multiplier
        if "multiplier" in entry:
            # Apply the multiplier (e.g., temperature * 10)
            write_value = int(value * entry["multiplier"])
        else:
            write_value = value
        
        # Set the value
        set_value(self.payload, offset, write_value, value_type)
        return True
    
    def generate_write_command(self, key):
        """
        Generate a write command for a specific key.
        
        Args:
            key: The key in MEMORY_MAP
            
        Returns:
            Command string or None if key not found
        """
        if key not in MEMORY_MAP:
            return None
            
        entry = MEMORY_MAP[key]
        # For writing, use absolute offset without adjustment
        offset = entry["offset"]  # No offset adjustment for writing
        value_type = entry["type"]
        
        # Determine length based on value type
        if value_type == "u8":
            length = 1
        elif value_type == "u16le":
            length = 2
        elif value_type == "u32le":
            length = 4
        else:
            return None
            
        # Generate the command
        return build_write_command(self.payload, offset, length)
    
    def get_current_value(self, key):
        """
        Get the current value for a key from the payload.
        
        Args:
            key: The key in MEMORY_MAP
            
        Returns:
            Current value or None if key not found
        """
        if key not in MEMORY_MAP:
            return None
            
        entry = MEMORY_MAP[key]
        # For reading, apply the offset adjustment
        offset = entry["offset"] - self.offset_adjustment  # Apply offset adjustment for reading only
        value_type = entry["type"]
        
        # Extract raw value
        raw_value = extract_value(self.payload, offset, value_type)
        if raw_value is None:
            return None
        
        # Apply any transformations
        if "multiplier" in entry:
            return raw_value / entry["multiplier"]
        
        # Check if this has predefined values
        if "values" in entry:
            values = entry["values"]
            for name, value in values.items():
                if isinstance(value, str):
                    # Handle expressions like "value > 0"
                    if eval(value.replace("value", str(raw_value))):
                        return name
                elif raw_value == value:
                    return name
        
        # No transformation needed
        return raw_value

def display_command(command):
    """
    Display a formatted write command.
    
    Args:
        command: Command string to display
    """
    print("Command: {}".format(command))
    
    # Break down the command
    if command.startswith('w'):
        offset = int(command[1:5], 16)
        length = int(command[5:9], 16)
        data = command[9:-2]
        checksum = command[-2:]
        
        print("Type: Write")
        print("Offset: 0x{:04X} ({})".format(offset, offset))
        print("Length: 0x{:04X} ({})".format(length, length))
        print("Data: {}".format(data))
        print("Checksum: {}".format(checksum))
        
        # Show byte values for short commands
        if length <= 16:
            bytes_values = [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
            print("Bytes: {}".format(bytes_values))

def send_command_to_serial(command, port, baudrate=115200, timeout=5):
    """
    Send a command to the Ascaso machine via serial connection.
    
    Args:
        command: Command string to send
        port: Serial port to use
        baudrate: Baud rate for serial communication
        timeout: Timeout in seconds for serial operations
        
    Returns:
        Response string or None if communication fails
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Connected to {} at {} baud".format(port, baudrate))
        
        # Give the device time to initialize
        time.sleep(1)
        
        print("Sending command: {}".format(command))
        
        # Convert ASCII string to bytes and send
        ser.write(command.encode('ascii'))
        
        # Wait for the response
        print("Waiting for response...")
        response = ""
        start_time = time.time()
        
        # Read until we get a complete response
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                byte_data = ser.read(ser.in_waiting)
                response += byte_data.decode('ascii', errors='replace')
                
                # Check if we have a complete response (typically starts with 'a' for acknowledge)
                if response and (len(response) > 5 or 'a' in response):
                    break
            
            time.sleep(0.1)
        
        ser.close()
        
        if response:
            print("Received response: {}".format(response))
            return response
        else:
            print("No response received from device")
            return None
    except Exception as e:
        print("Serial communication error: {}".format(e))
        if 'ser' in locals() and ser.is_open:
            ser.close()
        return None

def read_current_state_from_serial(port, baudrate=115200, timeout=5):
    """
    Read the current state from the machine via serial connection.
    
    Args:
        port: Serial port to use
        baudrate: Baud rate for serial communication
        timeout: Timeout in seconds for serial operations
        
    Returns:
        Tuple of (payload bytes, response header) or (None, None) if communication fails
    """
    try:
        # Build and send a standard read request
        request = build_request()
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Connected to {} at {} baud".format(port, baudrate))
        
        # Give the device time to initialize
        time.sleep(1)
        
        print("Sending read request: {}".format(request))
        ser.write(request.encode('ascii'))
        
        # Wait for the response
        print("Waiting for response...")
        response = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                byte_data = ser.read(ser.in_waiting)
                response += byte_data.decode('ascii', errors='replace')
                
                # Check if we have a complete response
                if response.startswith('r') and len(response) > 11:
                    break
            
            time.sleep(0.1)
        
        ser.close()
        
        if response:
            print("Received response: {}".format(response))
            payload, response_header = load_payload_from_response(response)
            if payload:
                print("Successfully extracted payload ({} bytes)".format(len(payload)))
                return payload, response_header
        
        print("No valid response received")
        return None, None
    except Exception as e:
        print("Serial communication error: {}".format(e))
        if 'ser' in locals() and ser.is_open:
            ser.close()
        return None, None

def main():
    # Set up the main argument parser
    parser = argparse.ArgumentParser(description="Generate write commands for Ascaso Baby T espresso machine")
    parser.add_argument("--file", type=str, help="File containing current machine state to use as base")
    parser.add_argument("--hex-dump", action="store_true", help="Show hex dump of the payload")
    parser.add_argument("--serial-port", type=str, help="Serial port to connect to the Ascaso machine")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate for serial connection")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds for serial operations")
    parser.add_argument("--read-only", action="store_true", help="Generate command but don't send it (even if serial port specified)")
    parser.add_argument("--skip-read", action="store_true", help="Skip reading current state from device before sending write command")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Power command
    power_parser = subparsers.add_parser("power", help="Set power state")
    power_parser.add_argument("state", choices=["on", "off"], help="Power state")
    
    # Steam command
    steam_parser = subparsers.add_parser("steam", help="Set steam state")
    steam_parser.add_argument("state", choices=["on", "off"], help="Steam state")
    
    # Temperature commands
    temp_parser = subparsers.add_parser("coffee-temp", help="Set coffee temperature")
    temp_parser.add_argument("value", type=float, help="Temperature value")
    
    steam_temp_parser = subparsers.add_parser("steam-temp", help="Set steam temperature")
    steam_temp_parser.add_argument("value", type=float, help="Temperature value")
    
    standby_temp_parser = subparsers.add_parser("standby-temp", help="Set standby temperature")
    standby_temp_parser.add_argument("value", type=float, help="Temperature value")
    
    # Unit command
    unit_parser = subparsers.add_parser("unit", help="Set temperature unit")
    unit_parser.add_argument("unit", choices=["C", "F"], help="C for Celsius, F for Fahrenheit")
    
    # Dose commands
    dose_parser = subparsers.add_parser("dose", help="Set dose value")
    dose_parser.add_argument("type", choices=["S1", "S2", "L1", "L2"], help="Dose type")
    dose_parser.add_argument("value", type=int, help="Dose value in ml")
    
    # Pre-infusion commands
    preinf_parser = subparsers.add_parser("pre-infusion", help="Set pre-infusion time")
    preinf_parser.add_argument("type", choices=["S1", "S2", "L1", "L2"], help="Dose type")
    preinf_parser.add_argument("value", type=float, help="Pre-infusion time in seconds (0.0-9.9)")
    
    # Autotimer command
    autotimer_parser = subparsers.add_parser("autotimer", help="Control autotimer feature")
    autotimer_parser.add_argument("action", choices=["enable", "disable", "set"], 
                                help="Action to perform with autotimer")
    autotimer_parser.add_argument("--on-time", type=str, help="Power on time in format 'hh:mm' (24h)", default=None)
    autotimer_parser.add_argument("--off-time", type=str, help="Power off time in format 'hh:mm' (24h)", default=None)
    
    # Custom command for direct value setting
    custom_parser = subparsers.add_parser("custom", help="Set custom byte value")
    custom_parser.add_argument("offset", type=int, help="Memory offset")
    custom_parser.add_argument("value", type=int, help="Value to write")
    custom_parser.add_argument("size", type=int, choices=[1, 2, 4], default=1, help="Value size in bytes (1, 2, or 4)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default payload and response header are None
    payload = None
    response_header = None
    
    # If serial port is specified and no file is given, try to read current state from device first
    if args.serial_port and not args.file and not args.read_only and not args.skip_read:
        print("Reading current state from device...")
        payload, response_header = read_current_state_from_serial(args.serial_port, args.baudrate, args.timeout)
    
    # If we couldn't get the payload from the device, try to load from file or create new
    if payload is None:
        if args.file and os.path.exists(args.file):
            payload, response_header = load_payload_from_file(args.file)
        else:
            # Create a new empty payload
            payload, response_header = load_or_create_payload(args.file)
    
    writer = AscasoWriter(payload, response_header)
    
    # Show hex dump if requested
    if args.hex_dump:
        dump_payload(payload)
    
    # Process command
    if args.command == "power":
        result = writer.set_value_by_key("power_state", args.state)
        if result:
            current = writer.get_current_value("power_state")
            command = writer.generate_write_command("power_state")
            print("Setting power state to {} (current: {})".format(args.state, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "steam":
        result = writer.set_value_by_key("steam_state", args.state)
        if result:
            current = writer.get_current_value("steam_state")
            command = writer.generate_write_command("steam_state")
            print("Setting steam state to {} (current: {})".format(args.state, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "coffee-temp":
        result = writer.set_value_by_key("coffee_temperature", args.value)
        if result:
            current = writer.get_current_value("coffee_temperature")
            command = writer.generate_write_command("coffee_temperature")
            print("Setting coffee temperature to {}°C (current: {}°C)".format(args.value, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "steam-temp":
        result = writer.set_value_by_key("steam_temperature", args.value)
        if result:
            current = writer.get_current_value("steam_temperature")
            command = writer.generate_write_command("steam_temperature")
            print("Setting steam temperature to {}°C (current: {}°C)".format(args.value, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "standby-temp":
        result = writer.set_value_by_key("standby_temperature", args.value)
        if result:
            current = writer.get_current_value("standby_temperature")
            command = writer.generate_write_command("standby_temperature")
            print("Setting standby temperature to {}°C (current: {}°C)".format(args.value, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "unit":
        unit_value = "celsius" if args.unit == "C" else "fahrenheit"
        result = writer.set_value_by_key("temperature_unit", unit_value)
        if result:
            current = writer.get_current_value("temperature_unit")
            command = writer.generate_write_command("temperature_unit")
            print("Setting temperature unit to {} (current: {})".format(args.unit, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "dose":
        key = "dose_{}".format(args.type)
        result = writer.set_value_by_key(key, args.value)
        if result:
            current = writer.get_current_value(key)
            command = writer.generate_write_command(key)
            print("Setting {} dose to {}ml (current: {}ml)".format(args.type, args.value, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "pre-infusion":
        key = "pre_infusion_{}".format(args.type)
        result = writer.set_value_by_key(key, args.value)
        if result:
            current = writer.get_current_value(key)
            command = writer.generate_write_command(key)
            print("Setting {} pre-infusion time to {}s (current: {}s)".format(args.type, args.value, current))
            display_command(command)
            
            # Send command if serial port is specified
            if args.serial_port and not args.read_only:
                print("\nSending command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "autotimer":
        if args.action == "enable":
            result = writer.set_value_by_key("autotimer_enabled", 1)
            if result:
                current = writer.get_current_value("autotimer_enabled")
                command = writer.generate_write_command("autotimer_enabled")
                print("Enabling autotimer (current: {})".format(current))
                display_command(command)
                
                if args.serial_port and not args.read_only:
                    print("\nSending command to device...")
                    response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
        
        elif args.action == "disable":
            # Set autotimer_enabled to 0 and all timer values to 100
            # Since the offsets are consecutive (126-130), we can do this in a single write
            
            # Calculate the actual memory locations with offset adjustment
            start_offset = MEMORY_MAP["autotimer_enabled"]["offset"] - writer.offset_adjustment
            
            # Set values directly in the payload - all are u8 (1 byte) type
            # autotimer_enabled = 0
            writer.payload[start_offset] = 0
            # autotimer_h_on = 100
            writer.payload[start_offset + 1] = 100
            # autotimer_m_on = 100
            writer.payload[start_offset + 2] = 100
            # autotimer_h_off = 100
            writer.payload[start_offset + 3] = 100
            # autotimer_m_off = 100
            
            # Create a single write command for all 5 bytes
            command = build_write_command(writer.payload, start_offset, 5)
            
            print("Disabling autotimer and setting all timer values to 100...")
            print("\nUsing single combined write command for all autotimer settings (5 bytes):")
            display_command(command)
            
            if args.serial_port and not args.read_only:
                print("\nSending combined command to device...")
                response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
        
        elif args.action == "set":
            # Determine which time values are being set
            set_on_time = args.on_time is not None
            set_off_time = args.off_time is not None
            
            # Parse the time strings if provided
            h_on, m_on = None, None
            h_off, m_off = None, None
            
            if set_on_time:
                try:
                    h_on, m_on = map(int, args.on_time.split(':'))
                    if h_on < 0 or h_on > 23 or m_on < 0 or m_on > 59:
                        print("Error: On-time must be in format 'hh:mm' with valid 24h time values", file=sys.stderr)
                        return
                except ValueError:
                    print("Error: On-time must be in format 'hh:mm'", file=sys.stderr)
                    return
            
            if set_off_time:
                try:
                    h_off, m_off = map(int, args.off_time.split(':'))
                    if h_off < 0 or h_off > 23 or m_off < 0 or m_off > 59:
                        print("Error: Off-time must be in format 'hh:mm' with valid 24h time values", file=sys.stderr)
                        return
                except ValueError:
                    print("Error: Off-time must be in format 'hh:mm'", file=sys.stderr)
                    return
            
            # Calculate the actual memory locations with offset adjustment
            start_offset = MEMORY_MAP["autotimer_enabled"]["offset"] - writer.offset_adjustment
            
            # Approach 1: Set both on and off times together (all 4 bytes + enable bit in one command)
            # In this case, we always enable the autotimer too
            if set_on_time and set_off_time:
                # Set values directly in the payload
                writer.payload[start_offset] = 1       # Enable autotimer
                writer.payload[start_offset + 1] = h_on
                writer.payload[start_offset + 2] = m_on
                writer.payload[start_offset + 3] = h_off
                writer.payload[start_offset + 4] = m_off
                
                # Create a single write command for all 5 bytes
                command = build_write_command(writer.payload, start_offset, 5)
                
                print(f"Setting autotimer: enabled, on at {h_on:02d}:{m_on:02d}, off at {h_off:02d}:{m_off:02d}")
                print("\nUsing combined write command for all autotimer settings (5 bytes):")
                display_command(command)
                
                if args.serial_port and not args.read_only:
                    print("\nSending combined command to device...")
                    response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
            
            # Approach 2: Set just on-time (without automatically enabling)
            elif set_on_time:
                # Set values directly in the payload
                writer.payload[start_offset + 1] = h_on
                writer.payload[start_offset + 2] = m_on
                
                # Create a write command for just the on-time (2 bytes)
                command = build_write_command(writer.payload, start_offset + 1, 2)
                
                print(f"Setting autotimer on-time to {h_on:02d}:{m_on:02d} (without changing enabled state)")
                print("\nUsing command for on-time only (2 bytes):")
                display_command(command)
                
                if args.serial_port and not args.read_only:
                    print("\nSending on-time command to device...")
                    response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
            
            # Approach 3: Set just off-time (without automatically enabling)
            elif set_off_time:
                # Set the off-time values (2 bytes)
                writer.payload[start_offset + 3] = h_off
                writer.payload[start_offset + 4] = m_off
                
                # Create command for just the off-time (2 bytes)
                off_time_command = build_write_command(writer.payload, start_offset + 3, 2)
                
                print(f"Setting autotimer off-time to {h_off:02d}:{m_off:02d} (without changing enabled state)")
                print("\nUsing command for off-time only (2 bytes):")
                display_command(off_time_command)
                
                if args.serial_port and not args.read_only:
                    print("\nSending off-time command to device...")
                    response = send_command_to_serial(off_time_command, args.serial_port, args.baudrate, args.timeout)
    
    elif args.command == "custom":
        if args.size == 1:
            value_type = "u8"
        elif args.size == 2:
            value_type = "u16le"
        else:  # size == 4
            value_type = "u32le"
        
        set_value(payload, args.offset, args.value, value_type)
        command = build_write_command(payload, args.offset, args.size)
        print("Setting custom value at offset {} to {} (size: {} bytes)".format(args.offset, args.value, args.size))
        display_command(command)
        
        # Send command if serial port is specified
        if args.serial_port and not args.read_only:
            print("\nSending command to device...")
            response = send_command_to_serial(command, args.serial_port, args.baudrate, args.timeout)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()