#!/usr/bin/env python3
"""Send a raw protocol command to the bridge and print the machine's reply.

The bridge exposes this as an ESPHome API action rather than an entity, so it
creates nothing in Home Assistant. The reply is not a return value - the
firmware logs it - so this subscribes to the log stream and prints what comes
back.

Give the command WITHOUT its checksum; the firmware appends it.

    ./raw_cmd.py r00050010            # read 16 bytes at offset 5
    ./raw_cmd.py w0029000105          # write 0x05 to offset 41
    ./raw_cmd.py --host 10.0.0.5 r00050010

Needs aioesphomeapi, which ships with esphome:
    $(dirname $(readlink -f $(which esphome)))/python raw_cmd.py ...
"""
import argparse
import asyncio
import sys

from aioesphomeapi import APIClient, LogLevel

DEFAULT_HOST = "gicar-bridge.local"
ACTION = "raw_command"


async def run(host: str, port: int, command: str, wait: float) -> int:
    client = APIClient(host, port, password="")
    await client.connect(login=True)
    try:
        _, services = await client.list_entities_services()
        action = next((s for s in services if s.name == ACTION), None)
        if action is None:
            names = ", ".join(s.name for s in services) or "(none)"
            print(f"error: no '{ACTION}' action on {host}; found: {names}", file=sys.stderr)
            return 2

        replies: list[str] = []
        done = asyncio.Event()

        def on_log(msg) -> None:
            line = msg.message.decode(errors="replace") if isinstance(msg.message, bytes) else str(msg.message)
            if "Raw:" not in line:
                return
            replies.append(line)
            print(line.rstrip())
            # "sending ..." is the echo; anything after it is the outcome.
            if "Raw: sending " not in line:
                done.set()

        # Without an explicit level the device sends nothing.
        client.subscribe_logs(on_log, log_level=LogLevel.LOG_LEVEL_DEBUG)
        await client.execute_service(action, {"command": command})

        try:
            await asyncio.wait_for(done.wait(), timeout=wait)
        except asyncio.TimeoutError:
            if not replies:
                print("no reply seen - is the bridge connected to the machine?", file=sys.stderr)
                return 1
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", help="protocol command without its checksum, e.g. r00050010")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=6053)
    ap.add_argument("--wait", type=float, default=15.0, help="seconds to wait for the reply")
    args = ap.parse_args()
    return asyncio.run(run(args.host, args.port, args.command, args.wait))


if __name__ == "__main__":
    sys.exit(main())
