#!/usr/bin/env python3
"""Fetch or verify the exact Apple restore image used by this case study.

The repository intentionally does not redistribute Apple firmware. This helper
pins the official Apple CDN object, size, and checksums so reproduction remains
one command away without mirroring proprietary binaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

MANIFEST = {
    "device": "Mac16,12",
    "board": "J713AP",
    "soc": "T8132 / M4",
    "version": "27.0",
    "build": "26A428",
    "filename": "UniversalMac_27.0_26A428_Restore.ipsw",
    "size": 26626436228,
    "sha256": "2a5d3c695d501022b7fad9adaffcf2627bcb867d993fb5662dcd41bac99a2836",
    "sha1": "2d17f2fe0d7726dd66f0522fdb9ad162942c3f3d",
    "url": "https://updates.cdn-apple.com/2026FallFCS/afcfc88e-bbe6-44bf-a5da-07c56eebc06c/UniversalMac_27.0_26A428_Restore.ipsw",
}

CHUNK = 8 * 1024 * 1024
PROGRESS_STEP = 256 * 1024 * 1024


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("restore URL must use HTTPS")
    if parsed.hostname != "updates.cdn-apple.com":
        raise ValueError("restore URL is not the pinned Apple CDN host")
    if Path(parsed.path).name != MANIFEST["filename"]:
        raise ValueError("restore URL filename does not match the pinned image")


def hash_file(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    return hash_file(path, "sha256")


def verify(path: Path) -> None:
    size = path.stat().st_size
    if size != MANIFEST["size"]:
        raise ValueError(
            "size mismatch: got %d bytes, expected %d" % (size, MANIFEST["size"])
        )
    digest = sha256_file(path)
    if digest != MANIFEST["sha256"]:
        raise ValueError(
            "SHA-256 mismatch: got %s, expected %s" % (digest, MANIFEST["sha256"])
        )


def _open_download(offset: int):
    validate_url(MANIFEST["url"])
    headers = {"User-Agent": "macbook-ts1p-failsafe-research/1.0"}
    if offset:
        headers["Range"] = "bytes=%d-" % offset
    req = urllib.request.Request(MANIFEST["url"], headers=headers)
    return urllib.request.urlopen(req, timeout=60)


def download(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / MANIFEST["filename"]
    part = output_dir / (MANIFEST["filename"] + ".part")

    if final.exists():
        print("existing restore image found; verifying...", file=sys.stderr)
        verify(final)
        return final

    offset = part.stat().st_size if part.exists() else 0
    if offset > MANIFEST["size"]:
        raise ValueError("partial file is larger than the pinned restore image")

    response = _open_download(offset)
    status = getattr(response, "status", response.getcode())
    if offset and status != 206:
        response.close()
        print("server did not resume; restarting download from byte 0", file=sys.stderr)
        part.unlink()
        offset = 0
        response = _open_download(0)

    mode = "ab" if offset else "wb"
    downloaded = offset
    next_report = ((downloaded // PROGRESS_STEP) + 1) * PROGRESS_STEP
    total = MANIFEST["size"]

    print(
        "downloading Apple restore image: %.2f GiB total%s"
        % (total / (1024 ** 3), " (resuming)" if offset else ""),
        file=sys.stderr,
    )
    with response, part.open(mode) as out:
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if downloaded >= next_report or downloaded == total:
                print(
                    "%.2f / %.2f GiB (%.1f%%)"
                    % (
                        downloaded / (1024 ** 3),
                        total / (1024 ** 3),
                        downloaded * 100.0 / total,
                    ),
                    file=sys.stderr,
                )
                next_report += PROGRESS_STEP

    if part.stat().st_size != total:
        raise ValueError(
            "download incomplete: got %d bytes, expected %d"
            % (part.stat().st_size, total)
        )

    print("download complete; verifying SHA-256...", file=sys.stderr)
    verify(part)
    part.replace(final)
    print("verified: %s" % final, file=sys.stderr)
    return final


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch or verify the exact official Apple IPSW for this research case."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--download",
        metavar="DIR",
        type=Path,
        help="download/resume the pinned Apple IPSW into DIR and verify SHA-256",
    )
    group.add_argument(
        "--verify",
        metavar="FILE",
        type=Path,
        help="verify an already-downloaded IPSW against the pinned size and SHA-256",
    )
    group.add_argument(
        "--url-only",
        action="store_true",
        help="print only the official Apple CDN URL",
    )
    args = parser.parse_args()

    validate_url(MANIFEST["url"])
    if args.url_only:
        print(MANIFEST["url"])
    elif args.verify:
        verify(args.verify)
        print("OK: %s" % args.verify)
    elif args.download:
        print(download(args.download))
    else:
        print(json.dumps(MANIFEST, indent=2))


if __name__ == "__main__":
    main()
