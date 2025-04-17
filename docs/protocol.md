# Ascaso Baby T Protocol Documentation

## Overview

The Ascaso Baby T uses a serial communication protocol where commands and responses are sent as ASCII strings. The protocol is used to read machine state and send configuration commands.


## Serial Communication Settings

- Baud rate: `115200`
- 8 data bits, no parity, 1 stop bit

## Protocol Format

### Read Request Format

```
r000500D7[CHECKSUM]
```

- `r` - Identifies this as a read request
- `000500D7` - read `00D7` (215) bytes, starting at offset `0005`
- `[CHECKSUM]` - Two-character hex checksum

### Read Response Format

```
r000500D7[PAYLOAD][CHECKSUM]
```


- `r000500D7` - Mirror the request, minus the checksum
- `[PAYLOAD]` - Hex-encoded machine state data (can be hundreds of bytes)
- `[CHECKSUM]` - Two-character hex checksum

### Write Command Format

```
w[OFFSET][LENGTH][DATA][CHECKSUM]
```

- `w` - Identifies this as a write command
- `[OFFSET]` - Four-character hex offset from memory position '5'
- `[LENGTH]` - Four-character hex length of data to write
- `[DATA]` - Hex-encoded data to write
- `[CHECKSUM]` - Two-character hex checksum

example for `steam on`: `w005600010164`

### Write Response Format

```
w[OFFSET][LENGTH][OK][CHECKSUM]
```
example for `steam on`: `w00560001OK9D`

## Checksum Calculation

Checksums are calculated as follows:  
1. Sum the ASCII values of each character in the string (excluding the checksum characters)  
2. Take the result modulo 256  
3. Format as a two-character hex value  
eg. `sum(ord(c) for c in response[:-2]) % 256`

## Memory Map

The machine's memory is organized with specific offsets for different settings:

- **0-35**: General settings
- **36-50**: Language and configuration settings
- **53-82**: Temperature settings
- **83-110**: Steam and dose settings
- **124-132**: Power state and timer settings
- **134-152**: Counters (read-only)
- **210-212**: Total counter

## Data Types

The protocol supports several data types:
- `u8`: 8-bit unsigned integer (1 byte)
- `u16le`: 16-bit unsigned integer, little-endian (2 bytes)
- `u32le`: 32-bit unsigned integer, little-endian (4 bytes)

## Value Transformations

Some values have specific transformations:  
1. **Multipliers**: Values like temperature are stored multiplied by 10 (e.g., 93.5°C is stored as 935)  
2. **Predefined states**: Values like power state use specific integers (e.g., 6 for "on", 4 for "off")  
3. **Expressions**: Some values are interpreted through expressions (e.g., "value > 0" for "on")

## Communication Flow

1. **Reading current state**:
   - Send a read request (`r000500D7[CHECKSUM]`)
   - Receive a response with the full machine state
   - Parse the response to extract specific values

2. **Writing a setting**:
   - Prepare the payload with the modified value
   - Build a write command with the appropriate offset and length
   - Send the command to the machine
   - Wait for acknowledgment

## Examples

### Example Read Request
```
r000500D7E7
```
### Example Read Response
```
r000500D7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0101020200010100011E1E1E1E002600282D000000A2031E000F0028000A00E30450000F006400050078000002D101000102F2032D00010101000068006A008E00680170176E00DC0096002C0170176E00DC0096002C017017080C100101016464646400060004000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009000000A41E0000A41E00000000E1
```

### Example Write Command (turn steam boiler on)
```
w005600010164
```
- Offset: `0056` (corresponds to steam_state offset: 0x56 = 86)
- Length: `0001` (1 byte)
- Data: `01` (value for "on")
- Checksum: `64`

