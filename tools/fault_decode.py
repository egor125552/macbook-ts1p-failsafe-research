#!/usr/bin/env python3
"""Decode exported SMC input-fault bit masks.

For the first exported word, bit N corresponds to input index N.  This tiny
helper is intentionally independent of Apple binaries so the bit-order claim
can be tested in CI.
"""
from __future__ import annotations
import argparse


def set_bits(mask: int) -> list[int]:
    if mask < 0:
        raise ValueError("mask must be non-negative")
    return [bit for bit in range(mask.bit_length()) if mask & (1 << bit)]


def raw_hex_bytes_to_numeric(raw: str) -> int:
    """Decode the byte string as returned by this SMC hex_ read path.

    Example: raw ``00001000`` represents bytes 00 00 10 00 and the numerical
    little-endian word 0x00001000, so input bit 12 is set.
    """
    raw = raw.strip().replace(" ", "")
    b = bytes.fromhex(raw)
    return int.from_bytes(b, "big")


def main() -> None:
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--mask", help="numeric mask, e.g. 0x1000")
    group.add_argument("--raw", help="raw bytes printed by the helper, e.g. 00001000")
    args = p.parse_args()
    mask = int(args.mask, 0) if args.mask is not None else raw_hex_bytes_to_numeric(args.raw)
    print(f"mask=0x{mask:08x}")
    print("bits=" + ",".join(map(str, set_bits(mask))))


if __name__ == "__main__":
    main()
