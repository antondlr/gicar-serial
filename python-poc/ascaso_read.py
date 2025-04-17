#!/usr/bin/env python3
"""
Ascaso Baby T Reader

This script reads and parses data from an Ascaso Baby T espresso machine.
"""

import argparse
import json
import sys
import time
import serial
from typing import Dict, Any, List

# Import from our library
from lib.ascaso_common import (
    build_request, load_payload_from_file, load_payload_from_response,
    extract_value, dump_payload, hex_ascii_to_bytes, bytes_to_hex_ascii
)
from lib.ascaso_offsets import MEMORY_MAP, MACHINE_MODELS, DEFAULT_RESPONSE

class AscasoReader:
    def __init__(self, payload, response_header=None):
        """
        Initialize the reader with a payload.
        
        Args:
            payload: Raw payload bytes from the machine
            response_header: The header of the response (e.g., "r000500D7")
        """
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
        
    def get_value(self, key):
        """
        Get a parsed value from the payload based on the memory map.
        
        Args:
            key: The key of the value in MEMORY_MAP
            
        Returns:
            Parsed value or None if key not found
        """
        if key not in MEMORY_MAP:
            return None
            
        # Get memory map entry
        entry = MEMORY_MAP[key]
        offset = entry["offset"]
        offset = offset - self.offset_adjustment # Use dynamic offset adjustment
        value_type = entry["type"]
        
        # Extract raw value
        raw_value = extract_value(self.payload, offset, value_type)
        if raw_value is None:
            return None
        
        # Apply any transformations specified in the memory map
        if "multiplier" in entry:
            # For values stored with a multiplier (e.g. temperature = value/10)
            return raw_value / entry["multiplier"]
        
        # Check if this is a value with predefined mappings
        if "values" in entry:
            # For values with predefined states (e.g. on/off)
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
    
    def get_value_at_offset(self, offset, size):
        """
        Get a raw value from a specific offset with specified size.
        
        Args:
            offset: Memory offset to read from
            size: Size in bytes (1, 2, or 4)
            
        Returns:
            Raw value from the specified offset
        """
        # Apply the same offset adjustment as in get_value
        adjusted_offset = offset - self.offset_adjustment
        
        if size == 1:
            value_type = "u8"
        elif size == 2:
            value_type = "u16le"
        elif size == 4:
            value_type = "u32le"
        else:
            return None
        
        return extract_value(self.payload, adjusted_offset, value_type)
    
    def get_model_name(self):
        """
        Get the machine model name.
        
        Returns:
            Model name string
        """
        model_value = extract_value(self.payload, MEMORY_MAP["model"]["offset"], MEMORY_MAP["model"]["type"])
        if model_value in MACHINE_MODELS:
            return MACHINE_MODELS[model_value]
        return "Unknown Model"
    
    def parse_all(self):
        """
        Parse all values from the payload.
        
        Returns:
            Dictionary of parsed values
        """
        result = {}
        
        # Special handling for model
        result["model"] = self.get_model_name()
        
        # Get values for all keys in the memory map
        for key in MEMORY_MAP:
            if key != "model":  # Already handled model specially
                value = self.get_value(key)
                if value is not None:
                    result[key] = value
        
        return result

def print_value(key, value, indent=0):
    """
    Print a formatted value with description.
    
    Args:
        key: The key from the memory map
        value: The value to print
        indent: Indentation level
    """
    prefix = " " * indent
    if key in MEMORY_MAP:
        desc = MEMORY_MAP[key]["description"]
        print("{}{}: {} ({})".format(prefix, key, value, desc))
    else:
        print("{}{}: {}".format(prefix, key, value))

def print_custom_value(offset, value, size, adjustment=5):
    """
    Print a formatted custom value from a specific memory address.
    
    Args:
        offset: Memory offset
        value: The raw value
        size: Size in bytes
        adjustment: The offset adjustment that was applied
    """
    print("Memory offset 0x{:04X} ({}):".format(offset, offset))
    print("  Adjusted offset: 0x{:04X} ({})".format(offset - adjustment, offset - adjustment))
    print("  Value: {} (0x{:X})".format(value, value))
    print("  Size: {} bytes".format(size))
    
    # Check if this offset corresponds to any known key in the memory map
    matching_keys = []
    for key, entry in MEMORY_MAP.items():
        if entry["offset"] == offset:
            matching_keys.append(key)
    
    if matching_keys:
        print("  Matches known key(s): {}".format(", ".join(matching_keys)))

def print_result(result, verbose=False, json_output=False):
    """
    Print the parsed result.
    
    Args:
        result: The parsed result dictionary
        verbose: Whether to print all values or just important ones
        json_output: Whether to output as JSON
    """
    if json_output:
        print(json.dumps(result, indent=2))
        return
    
    # Define groups for organized output
    groups = {
        "Machine Info": ["model", "power_state"],
        "Temperature Settings": ["temperature_unit", "coffee_temperature", "steam_temperature", 
                               "offset_temperature", "standby_temperature", "standby_time"],
        "Dose Settings": ["dose_S1", "dose_S2", "dose_L1", "dose_L2", "flush_enabled"],
        "Pre-infusion Settings": ["pre_infusion_enabled", "pre_infusion_S1", "pre_infusion_S2", 
                                "pre_infusion_L1", "pre_infusion_L2"],
        "Counter Values": ["counter_S1", "counter_S2", "counter_L1", "counter_L2", 
                         "counter_XL", "counter_total"],
        "Auto Timer Settings": ["autotimer_enabled", "autotimer_h_on", "autotimer_m_on", 
                               "autotimer_h_off", "autotimer_m_off"],
        "Other Settings": ["language", "water_connection", "coffee_group_state", "steam_state"]
    }
    
    # For non-verbose mode, just show most important values
    if not verbose:
        print("Ascaso Baby T Status:")
        print("  Model: {}".format(result.get('model', 'Unknown')))
        print("  Power: {}".format(result.get('power_state', 'Unknown')))
        print("  Coffee Group: {}".format(result.get('coffee_group_state', 'Unknown')))
        print("  Steam: {}".format(result.get('steam_state', 'Unknown')))
        print("  Coffee Temperature: {}°C".format(result.get('coffee_temperature', 'Unknown')))
        print("  Steam Temperature: {}°C".format(result.get('steam_temperature', 'Unknown')))
        
        print("\nCounters:")
        print("  S1: {}, S2: {}".format(result.get('counter_S1', 0), result.get('counter_S2', 0)))
        print("  L1: {}, L2: {}".format(result.get('counter_L1', 0), result.get('counter_L2', 0)))
        print("  XL: {}".format(result.get('counter_XL', 0)))
        print("  Total: {}".format(result.get('counter_total', 0)))
        
        print("\nUse --verbose for complete information")
        return
    
    # Verbose output - show all values grouped by category
    for group_name, keys in groups.items():
        print("\n{}:".format(group_name))
        for key in keys:
            if key in result:
                print_value(key, result[key], indent=2)

def read_from_serial(port, baudrate=115200, timeout=5):
    """
    Read data from a serial port using the Ascaso protocol.
    
    Args:
        port: Serial port name
        baudrate: Baud rate for serial communication
        timeout: Timeout in seconds for serial operations
        
    Returns:
        Tuple of (payload bytes, response header) or (None, None) if communication fails
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Connected to {} at {} baud".format(port, baudrate))
        
        # Give the device time to initialize
        time.sleep(1)
        
        # Build and send the request
        request = build_request()
        print("Sending request: {}".format(request))
        
        # Convert ASCII string to bytes and send
        ser.write(request.encode('ascii'))
        
        # Wait for the response
        print("Waiting for response...")
        response = ""
        start_time = time.time()
        
        # Read until we get a complete response
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                byte_data = ser.read(ser.in_waiting)
                response += byte_data.decode('ascii', errors='replace')
                
                # Check if we have a complete response (starts with 'r' and has a checksum)
                if response.startswith('r') and len(response) > 11:  # Minimum valid response length
                    break
            
            time.sleep(0.1)
        
        ser.close()
        
        if response:
            print("Received response: {}".format(response))
            # Extract payload from response
            payload, response_header = load_payload_from_response(response)
            if payload:
                print("Successfully extracted payload ({} bytes)".format(len(payload)))
                return payload, response_header
            else:
                print("Failed to extract valid payload from response")
        else:
            print("No response received from device")
        
        return None, None
    except Exception as e:
        print("Serial communication error: {}".format(e))
        if 'ser' in locals() and ser.is_open:
            ser.close()
        return None, None

def main():
    parser = argparse.ArgumentParser(description="Read and parse data from Ascaso Baby T espresso machine")
    parser.add_argument("--file", type=str, help="File containing response data to parse")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed information")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--filter", type=str, help="Filter results to show only keys containing this string")
    parser.add_argument("--hex-dump", action="store_true", help="Show hex dump of the payload")
    parser.add_argument("--serial-port", type=str, help="Serial port to connect to the Ascaso machine")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baud rate for serial connection")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds for serial operations")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Custom command for direct value reading
    custom_parser = subparsers.add_parser("custom", help="Read value at custom memory offset")
    custom_parser.add_argument("offset", type=int, help="Memory offset")
    custom_parser.add_argument("size", type=int, choices=[1, 2, 4], default=1, help="Value size in bytes (1, 2, or 4)")
    
    args = parser.parse_args()
    
    # Default payload is None
    payload = None
    
    try:
        if args.serial_port:
            # Read payload from serial port
            payload, response_header = read_from_serial(args.serial_port, args.baudrate, args.timeout)
            
            if not payload:
                print("Failed to read data from serial port. Using default response as fallback.")
                payload, response_header = load_payload_from_response(DEFAULT_RESPONSE)
                
            # Save the received data to the states/latest.txt file
            if payload:
                with open("states/latest.txt", "w") as f:
                    # Create a full response string from the payload
                    payload_hex = bytes_to_hex_ascii(payload)
                    base_response = "r000500D7{}".format(payload_hex)
                    # Calculate checksum
                    checksum = sum(ord(c) for c in base_response) % 256
                    full_response = "{}{:02X}".format(base_response, checksum)
                    f.write(full_response)
                print("Saved response to states/latest.txt")
                
        elif args.file:
            # Load from file if specified
            payload, response_header = load_payload_from_file(args.file)
            if not payload:
                print("Could not load payload from {}, using default response".format(args.file), file=sys.stderr)
                payload, response_header = load_payload_from_response(DEFAULT_RESPONSE)
        else:
            # Default to last received data
            try:
                payload, response_header = load_payload_from_file("states/latest.txt")
            except:
                print("No file specified and couldn't load from states/latest.txt. Using default response.")
                payload, response_header = load_payload_from_response(DEFAULT_RESPONSE)
        
        if payload:
            reader = AscasoReader(payload, response_header)
            
            if args.command == "custom":
                # Handle custom command to read specific memory offset
                value = reader.get_value_at_offset(args.offset, args.size)
                if value is not None:
                    print_custom_value(args.offset, value, args.size, reader.offset_adjustment)
                else:
                    print("Error: Could not read value at offset {} with size {}".format(args.offset, args.size))
            else:
                # Regular operation - parse and display all values
                result = reader.parse_all()
                
                if args.filter:
                    filtered_result = {k: v for k, v in result.items() if args.filter in k}
                    print_result(filtered_result, args.verbose, args.json)
                else:
                    print_result(result, args.verbose, args.json)
            
            if args.hex_dump:
                dump_payload(payload)
    except Exception as e:
        print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()