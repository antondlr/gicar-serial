# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

gicar-serial is a reverse-engineered serial protocol implementation for the Ascaso Baby T espresso machine. It enables direct communication with the Gicar 3D5 Maestro control board via serial (or Bluetooth-to-serial bridge) to read and write machine settings.

## Running the Python POC

```bash
# Read machine state from cached file
python3 python-poc/ascaso_read.py

# Read from serial port
python3 python-poc/ascaso_read.py --serial-port /dev/ttyUSB0

# Read with JSON output
python3 python-poc/ascaso_read.py --json

# Write settings (dry-run mode, shows command without sending)
python3 python-poc/ascaso_write.py --read-only power on

# Write to serial port
python3 python-poc/ascaso_write.py --serial-port /dev/ttyUSB0 coffee-temp 93.5
```

**Dependencies**: `pip install -r requirements.txt` (pyserial)

## Architecture

### Core Modules

- **`python-poc/lib/ascaso_common.py`** - Utilities: checksum calculation, hex conversion, payload serialization, memory I/O operations
- **`python-poc/lib/ascaso_offsets.py`** - Memory map with 50+ parameters, machine model definitions, and `DEFAULT_RESPONSE` for testing

### CLI Tools

- **`python-poc/ascaso_read.py`** - `AscasoReader` class parses payloads and extracts values. Subcommands: default (all values), `custom <offset> [size]`
- **`python-poc/ascaso_write.py`** - `AscasoWriter` class modifies payloads. Subcommands: `power`, `steam`, `coffee-temp`, `steam-temp`, `standby-temp`, `unit`, `dose`, `pre-infusion`, `autotimer`, `custom`

### Protocol (115200/8N1)

```
Read:  r[OFFSET:4hex][LENGTH:4hex][CHECKSUM:2hex]
Write: w[OFFSET:4hex][LENGTH:4hex][DATA:hex][CHECKSUM:2hex]
Checksum: sum(ASCII values) % 256
```

## Memory Map Conventions

Values in `MEMORY_MAP` dict include:
- `offset`: Memory address
- `type`: u8, u16le, u32le
- `multiplier`: e.g., temperature stored as value×10
- `values`: Enum mappings (e.g., power: 4=off, 6=on)
- `readonly`: True for counters

Key offsets: power state (132), coffee temp (53-54), steam temp (63-64), doses (91-97)

## Documentation

- `docs/protocol.md` - Serial protocol specification
- `docs/memory_map.md` - Complete address table

## Known Issues

1. Offset adjustment logic is inconsistent between read/write (see comment "## this is wrong" in ascaso_offsets.py:102)
2. Multi-group machines (Barista T, Big Dream) have offset differences not fully implemented
3. No input validation for temperature ranges or time values
