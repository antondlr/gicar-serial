"""
Common utilities for Ascaso Baby T espresso machine communication

This module contains common functions used by both the read and write
scripts for the Ascaso Baby T espresso machine.
"""

import os
from typing import Dict, Any, Union, Optional

def calculate_checksum(ascii_str):
    """
    Calculate checksum for Ascaso protocol commands.
    
    Args:
        ascii_str: String to calculate checksum for
        
    Returns:
        Checksum value (0-255)
    """
    if len(ascii_str) > 0:
        return sum(ord(c) for c in ascii_str) % 256
    return 0

def hex_ascii_to_bytes(ascii_data):
    """
    Convert hex-encoded ASCII (e.g. "FF01") to raw bytes.
    
    Args:
        ascii_data: Hex-encoded ASCII string
        
    Returns:
        Raw bytes
    """
    return bytes(int(ascii_data[i:i+2], 16) for i in range(0, len(ascii_data), 2))

def bytes_to_hex_ascii(raw_bytes):
    """
    Convert raw bytes to hex-encoded ASCII.
    
    Args:
        raw_bytes: Raw bytes to convert
        
    Returns:
        Hex-encoded ASCII string
    """
    return ''.join(["{:02X}".format(b) for b in raw_bytes])

def load_payload_from_file(filename):
    """
    Load payload data from a response file.
    
    Args:
        filename: Path to the response file
        
    Returns:
        Tuple of (payload bytes, response header) or (None, None) if file can't be loaded
    """
    try:
        with open(filename, "r") as f:
            data_content = f.read()
            # Take the first line which should be the full response
            response = data_content.strip().split('\n')[0]
            
            # Get the response header (first 9 characters)
            response_header = response[:9] if len(response) >= 9 else None
            
            # Extract payload (remove header and last 2 checksum chars)
            payload_ascii = response[9:-2]
            payload_bytes = hex_ascii_to_bytes(payload_ascii)
            
            # Verify checksum
            full_string = response[:-2]  # everything except last 2 chars (the checksum)
            calculated = calculate_checksum(full_string)
            expected = int(response[-2:], 16)
            if calculated != expected:
                raise ValueError(
                    "Invalid checksum: expected {:02X}, got {:02X}".format(expected, calculated))

            print("Loaded payload from {}, length: {} bytes, checksums exp/calc: {} {}".format(filename, len(payload_bytes), expected, calculated))
            return payload_bytes, response_header
    except Exception as e:
        print("Error loading payload from {}: {}".format(filename, e))
        return None, None

def load_payload_from_response(response):
    """
    Extract payload bytes from a complete response string.
    
    Args:
        response: Complete response string from the machine
        
    Returns:
        Tuple of (payload bytes, response header) or (None, None) if response is invalid
    """
    try:
        if not response.startswith('r'):
            raise ValueError("Invalid response format")
            
        # Get the response header (first 9 characters)
        response_header = response[:9] if len(response) >= 9 else None
            
        # Extract payload (remove header and last 2 checksum chars)
        payload_ascii = response[9:-2]
        payload_bytes = hex_ascii_to_bytes(payload_ascii)
        
        # Verify checksum
        full_string = response[:-2]  # everything except last 2 chars (the checksum)
        calculated = calculate_checksum(full_string)
        expected = int(response[-2:], 16)
        
        if calculated != expected:
            raise ValueError("Invalid checksum: expected {:02X}, got {:02X}".format(expected, calculated))
            
        return payload_bytes, response_header
    except Exception as e:
        print("Error parsing response: {}".format(e))
        return None, None

def extract_value(payload, offset, value_type):
    """
    Extract a value from the payload based on the offset and type.
    
    Args:
        payload: Raw payload bytes
        offset: Memory offset to read from
        value_type: Type of value to read (u8, u16le, u32le)
        
    Returns:
        Extracted value
    """
    if offset >= len(payload):
        return None
        
    if value_type == "u8":
        return payload[offset]
    elif value_type == "u16le":
        if offset + 1 >= len(payload):
            return None
        return int.from_bytes(payload[offset:offset+2], "little")
    elif value_type == "u32le":
        if offset + 3 >= len(payload):
            return None
        return int.from_bytes(payload[offset:offset+4], "little")
    else:
        raise ValueError("Unsupported value type: {}".format(value_type))

def set_value(payload, offset, value, value_type):
    """
    Set a value in the payload at the specified offset.
    
    Args:
        payload: Payload bytearray to modify
        offset: Memory offset to write to
        value: Value to write
        value_type: Type of value to write (u8, u16le, u32le)
    """
    if offset >= len(payload):
        return
    
    if value_type == "u8":
        payload[offset] = value & 0xFF
    elif value_type == "u16le":
        if offset + 1 >= len(payload):
            return
        payload[offset] = value & 0xFF
        payload[offset + 1] = (value >> 8) & 0xFF
    elif value_type == "u32le":
        if offset + 3 >= len(payload):
            return
        payload[offset] = value & 0xFF
        payload[offset + 1] = (value >> 8) & 0xFF
        payload[offset + 2] = (value >> 16) & 0xFF
        payload[offset + 3] = (value >> 24) & 0xFF
    else:
        raise ValueError("Unsupported value type: {}".format(value_type))

def build_request():
    """
    Build a standard read request for the Ascaso machine.
    
    Returns:
        Request string with checksum
    """
    base = "r000500D7"
    checksum = calculate_checksum(base)
    return base + "{:02X}".format(checksum)

def build_write_command(payload, start_offset=0, length=None):
    """
    Build a write command for the specified payload section.
    
    Args:
        payload: Payload bytearray to write
        start_offset: Starting offset in the payload
        length: Length of data to write (None for full payload)
        
    Returns:
        Formatted command string ready to send to the machine
    """
    if length is None:
        length = len(payload) - start_offset
    
    # Ensure we're within bounds
    if start_offset + length > len(payload):
        length = len(payload) - start_offset
    
    # Format is "w" + offset (4 chars) + length (4 chars) + data + checksum
    offset_str = "{:04X}".format(start_offset)
    length_str = "{:04X}".format(length)
    
    # Extract the data to write
    data_bytes = payload[start_offset:start_offset + length]
    
    # Convert bytes to hex string
    data_str = bytes_to_hex_ascii(data_bytes)
    
    # Combine components
    command_without_checksum = "w{}{}{}".format(offset_str, length_str, data_str)
    
    # Calculate checksum
    checksum = calculate_checksum(command_without_checksum)
    
    # Add checksum
    return "{}{}".format(command_without_checksum, "{:02X}".format(checksum))

def dump_payload(payload, start_offset=0, end_offset=None):
    """
    Print a hex dump of the payload for debugging purposes.
    
    Args:
        payload: Payload bytes to dump
        start_offset: Starting offset (default 0)
        end_offset: Ending offset (default None for full payload)
    """
    if end_offset is None or end_offset > len(payload):
        end_offset = len(payload)
    
    line_len = 16
    print("\nHex dump of payload:")
    for i in range(start_offset, end_offset, line_len):
        chunk = payload[i:min(i+line_len, end_offset)]
        hex_values = ' '.join("{:02X}".format(b) for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print("{:04X}: {} | {}".format(i, hex_values.ljust(3*line_len), ascii_values))

def load_or_create_payload(filename=None, size=300):
    """
    Load a payload from a file or create a new empty payload.
    
    Args:
        filename: Filename to load from (optional)
        size: Size of payload if creating new (default 300)
        
    Returns:
        Tuple of (payload as bytearray, response header) or (bytearray, None) if creating new
    """
    if filename and os.path.exists(filename):
        payload_bytes, response_header = load_payload_from_file(filename)
        if payload_bytes:
            return bytearray(payload_bytes), response_header
    
    # Create empty payload if file doesn't exist or couldn't be loaded
    return bytearray(size), None

def save_payload_to_file(filename, payload):
    """
    Save a payload to a file.
    
    Args:
        filename: Target filename
        payload: Payload bytes to save
    """
    # Convert payload to hex string with header and checksum
    hex_data = bytes_to_hex_ascii(payload)
    base = "r000500D7" + hex_data
    checksum = calculate_checksum(base)
    response = "{}{}".format(base, "{:02X}".format(checksum))
    
    # Write to file
    with open(filename, 'w') as f:
        f.write(response)
    
    print("Saved payload to {}, length: {} bytes".format(filename, len(payload)))
