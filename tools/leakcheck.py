#!/usr/bin/env python3
"""Fail if any given file contains a secret found in the raw captures.

Secrets (Wi-Fi SSID/password from the dongle console, inverter serial as text
and hex) are derived from the raw captures, never stored. Matching files are
reported by name only.

Usage: leakcheck.py --captures <dir> [--scrub-registers 3-7] FILE...
"""
import argparse
import sys
from pathlib import Path

from scrub import collect_secrets, parse_registers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--captures", type=Path, required=True)
    ap.add_argument("--scrub-registers", default="3-7")
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args()

    secrets = collect_secrets(args.captures, parse_registers(args.scrub_registers))
    if not secrets:
        print(f"leakcheck: no raw captures under {args.captures}; nothing to check against", file=sys.stderr)
        return 0
    hits = []
    for f in args.files:
        if not f.is_file() or f.suffix == ".age":
            continue
        data = f.read_bytes().decode("latin-1")
        if any(s in data or s.lower() in data.lower() for s in secrets):
            hits.append(str(f))
    if hits:
        print("leakcheck: BLOCKED, secret found in: " + ", ".join(hits), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
