#!/usr/bin/env python3
"""Extract selected SMC series from a PowerLog SQLite database, read-only."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import sqlite3
from pathlib import Path

LOOKUP = "SMC_InstantLookUpTable_2_2"
VALUES = "SMC_InstantKeyValues_1_2"


def extract(db: Path, keys: list[str], tz_hours: int) -> list[list[object]]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        mapping = {name: column for column, name in con.execute(
            f"SELECT KeyIndex, KeyName FROM {LOOKUP} ORDER BY ID"
        )}
        missing = [key for key in keys if key not in mapping]
        if missing:
            raise SystemExit(f"missing keys in {db}: {', '.join(missing)}")
        cols = [mapping[k] for k in keys]
        quoted = ",".join('"' + c.replace('"', '""') + '"' for c in cols)
        zone = dt.timezone(dt.timedelta(hours=tz_hours))
        out: list[list[object]] = []
        for row in con.execute(f"SELECT timestamp,{quoted} FROM {VALUES} ORDER BY timestamp"):
            stamp = dt.datetime.fromtimestamp(row[0], zone).isoformat()
            out.append([db.name, stamp, *row[1:]])
        return out
    finally:
        con.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("databases", nargs="+", type=Path)
    p.add_argument("--keys", nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--tz-hours", type=int, default=3,
                   help="timezone offset used for rendered timestamps; default +3")
    args = p.parse_args()

    rows: list[list[object]] = []
    for db in args.databases:
        rows.extend(extract(db, args.keys, args.tz_hours))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["database", "time", *args.keys])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
