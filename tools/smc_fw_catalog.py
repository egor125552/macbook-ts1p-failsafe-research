#!/usr/bin/env python3
"""Enumerate the matching SMC firmware's key catalog in isolated memory."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_SP, UC_ARM64_REG_LR

ENUM = 0x2D0BC
OUT = 0x180000
STACK = 0x1F0000
STOP = 0x170000
COUNT = 2265


def enumerate_catalog(image: bytes) -> list[dict[str, object]]:
    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    u.mem_map(0, 0x200000)
    u.mem_write(0, image)
    rows = []
    for index in range(COUNT):
        u.reg_write(UC_ARM64_REG_X0, OUT)
        u.reg_write(UC_ARM64_REG_X1, index)
        u.reg_write(UC_ARM64_REG_SP, STACK)
        u.reg_write(UC_ARM64_REG_LR, STOP)
        u.mem_write(OUT, bytes(32))
        u.emu_start(ENUM, STOP, count=50000)
        r = bytes(u.mem_read(OUT, 24))
        key = struct.unpack_from("<I", r)[0]
        typ = struct.unpack_from("<I", r, 6)[0]
        ptr = struct.unpack_from("<Q", r, 10)[0]
        row: dict[str, object] = {
            "index": index,
            "key": key.to_bytes(4, "big").decode("ascii", errors="replace"),
            "size": r[4],
            "attributes": r[5],
            "type": typ.to_bytes(4, "big").decode("ascii", errors="replace"),
            "pointer": ptr,
        }
        rows.append(row)
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--firmware", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--live-key-list", type=Path,
                   help="optional text file containing one live SMC key per line")
    args = p.parse_args()
    rows = enumerate_catalog(args.firmware.read_bytes())
    args.output.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"catalog_count={len(rows)}")
    if args.live_key_list:
        live = [x.strip() for x in args.live_key_list.read_text().splitlines() if x.strip()]
        same = len(live) == len(rows) and all(a["key"] == b for a, b in zip(rows, live))
        print(f"live_count={len(live)} matching_order={same}")


if __name__ == "__main__":
    main()
