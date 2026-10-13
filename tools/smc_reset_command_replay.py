#!/usr/bin/env python3
"""Replay the discovered input-reset diagnostic callback in isolated memory.

This is documentation of firmware behavior, not a live reset utility.  It does
not open AppleSMC or issue commands to real hardware.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_SP, UC_ARM64_REG_LR

EXPECTED_SHA256 = "010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa"
CALLBACK = 0x2B0B4
FAULT_CHECK = 0x3B4B4
STOP = 0x170000
CTX = 0x180000
PAYLOAD = 0x181000
DESC = 0x84270
STACK = 0x1F0000
NAME_SLOT = 0x9C628


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--firmware", required=True, type=Path)
    p.add_argument("--allow-mismatch", action="store_true")
    args = p.parse_args()

    image = args.firmware.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256 and not args.allow_mismatch:
        raise SystemExit(f"firmware mismatch: {digest}; expected {EXPECTED_SHA256}")

    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    u.mem_map(0, 0x200000)
    u.mem_write(0, image)
    u.mem_write(NAME_SLOT, b"Ts1P")
    # Synthetic faulted descriptor based on input 12, entirely inside emulator memory.
    u.mem_write(DESC, struct.pack("<IIII", 12, 23, 23, 24) + bytes([1, 0, 1, 0, 0, 0, 0, 0]))

    def state() -> dict[str, int]:
        v = bytes(u.mem_read(DESC, 24))
        return {
            "error_count": struct.unpack_from("<I", v)[0],
            "current_error": struct.unpack_from("<i", v, 4)[0],
            "debounce": struct.unpack_from("<i", v, 12)[0],
            "disabled": v[17],
            "fault": v[18],
        }

    def command(op: int) -> None:
        u.mem_write(PAYLOAD, bytes([op]))
        u.mem_write(CTX, struct.pack("<IIQ", 0x4D53464E, 0, PAYLOAD) + bytes([0x11]) + bytes(15))
        u.reg_write(UC_ARM64_REG_X0, CTX)
        u.reg_write(UC_ARM64_REG_SP, STACK)
        u.reg_write(UC_ARM64_REG_LR, STOP)
        u.emu_start(CALLBACK, STOP, count=1_000_000)

    result: dict[str, object] = {
        "scope": "isolated memory only",
        "sha256": digest,
        "before": state(),
    }
    command(11)
    result["after_reset_command_11"] = state()
    command(13)
    result["after_force_fault_command_13"] = state()

    u.reg_write(UC_ARM64_REG_X0, DESC)
    u.reg_write(UC_ARM64_REG_SP, STACK)
    u.reg_write(UC_ARM64_REG_LR, STOP)
    u.emu_start(FAULT_CHECK, STOP, count=1000)
    result["after_next_fault_check"] = state()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
