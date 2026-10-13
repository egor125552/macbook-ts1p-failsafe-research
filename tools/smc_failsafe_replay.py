#!/usr/bin/env python3
"""Replay the identified SMC fail-safe policy in isolated memory.

This tool never opens IOKit and never talks to the live SMC.  The user must
supply their own legally obtained matching firmware image.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import (
    UC_ARM64_REG_X19, UC_ARM64_REG_X22, UC_ARM64_REG_SP,
    UC_ARM64_REG_S8, UC_ARM64_REG_S9,
)

EXPECTED_SHA256 = "010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa"
IMAGE_NAME = "AppleSMCFirmware_H16_4-7372.1.3.j713.REL"
DESCRIPTOR_BASE = 0x840F0
FAULT_BYTE = 0x12
POLICY_START = 0x39B4C
POLICY_END = 0x39BA0
FAILSAFE_STATE = 0x9C424
FALLBACK_TABLE = 0x87130
STACK = 0x1F0000


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def write_fault_words(u: Uc, words: list[int]) -> None:
    for word, mask in enumerate(words):
        for bit in range(32):
            idx = word * 32 + bit
            addr = DESCRIPTOR_BASE + idx * 32 + FAULT_BYTE
            u.mem_write(addr, bytes([1 if mask & (1 << bit) else 0]))


def replay(image: bytes, words: list[int], clear_input: int | None) -> dict[str, object]:
    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    u.mem_map(0, 0x200000)
    u.mem_write(0, image)
    write_fault_words(u, words)
    if clear_input is not None:
        u.mem_write(DESCRIPTOR_BASE + clear_input * 32 + FAULT_BYTE, b"\x00")

    u.reg_write(UC_ARM64_REG_X19, FAILSAFE_STATE)
    u.reg_write(UC_ARM64_REG_X22, FALLBACK_TABLE)
    u.reg_write(UC_ARM64_REG_SP, STACK)
    u.reg_write(UC_ARM64_REG_S8, f32_bits(65.0))
    u.reg_write(UC_ARM64_REG_S9, f32_bits(30.0))
    u.emu_start(POLICY_START, POLICY_END, count=10000)

    fs0, fs1 = struct.unpack("<II", bytes(u.mem_read(FAILSAFE_STATE, 8)))
    return {
        "cleared_input": clear_input,
        "package_watts": bits_f32(u.reg_read(UC_ARM64_REG_S8)),
        "utility_watts": bits_f32(u.reg_read(UC_ARM64_REG_S9)),
        "failsafe_words": [fs0, fs1],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--firmware", required=True, type=Path)
    p.add_argument("--seb0", default="0x1000", help="persistent input fault word 0")
    p.add_argument("--extra-word", action="append", default=[],
                   help="additional SEB word values, in order starting at SEB1")
    p.add_argument("--allow-mismatch", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args()

    image = args.firmware.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256 and not args.allow_mismatch:
        raise SystemExit(
            f"firmware SHA-256 mismatch: {digest}\n"
            f"expected for documented offsets: {EXPECTED_SHA256}\n"
            "Refusing to execute build-specific offsets; use --allow-mismatch only after re-verifying them."
        )

    words = [int(args.seb0, 0), *[int(x, 0) for x in args.extra_word]]
    result = {
        "scope": "isolated replay; no live SMC access",
        "firmware": IMAGE_NAME,
        "sha256": digest,
        "policy_start": hex(POLICY_START),
        "policy_end": hex(POLICY_END),
        "fault_words": [hex(x) for x in words],
        "fault_present": replay(image, words, None),
        "input_12_cleared": replay(image, words, 12),
    }
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
