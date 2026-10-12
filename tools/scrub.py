#!/usr/bin/env python3
"""Make a shareable, scrubbed copy of an analyzed capture.

Removes identifying data so the result is safe even if the data repo is ever
made public:
  * frames.csv / registers.csv: values of the scrubbed registers (default 3-7,
    the inverter serial) are zeroed and CRCs recomputed. Unpaired replies and
    CRC-failed frames have all data zeroed, since we can't tell what they hold.
  * console: only allowlisted log lines are kept (the dongle prints Wi-Fi
    credentials at boot); IPs, MACs and logged values are redacted.
  * report.txt: example frame dumps and console excerpts are dropped.
Then every output file is checked for the secrets found in the *raw* inputs
(Wi-Fi SSID/password, serial as text and as hex). Any hit deletes the output
and exits non-zero. Secrets are never printed.

Optionally encrypts the raw capture (capture.sal, meta.json and the unscrubbed
registers/frames/console text, which leakcheck.py needs) with age.

Usage: .venv/bin/python scrub.py <capture_dir> <out_dir> [--scrub-registers 3-7]
                                 [--console-allow scrub_console_allow.txt]
                                 [--age-recipient age1...]
"""
import argparse
import csv
import io
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from analyze import classify, crc16_modbus, crc_ok

HERE = Path(__file__).resolve().parent
DEFAULT_ALLOW = HERE / "scrub_console_allow.txt"
MIN_SECRET_LEN = 4

ANSI = re.compile(r"\x1b\[[0-9;]*m")
REDACTIONS = [
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "<IP>"),
    (re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b"), "<MAC>"),
    (re.compile(r"0x[0-9A-Fa-f]{2}(?:,\s*0x[0-9A-Fa-f]{2}){5}"), "<MAC>"),
    (re.compile(r"value = \([^)]*\)"), "value = (<redacted>)"),
]
SECRET_FIELDS = re.compile(r"(?i)\b(ssid|password)\s*:\s*(\S+)")


def parse_registers(spec: str) -> set[int]:
    regs: set[int] = set()
    for part in filter(None, (p.strip() for p in spec.split(","))):
        lo, _, hi = part.partition("-")
        regs.update(range(int(lo), int(hi or lo) + 1))
    return regs


def _with_crc(body: bytes) -> bytes:
    c = crc16_modbus(body)
    return body + bytes([c & 0xFF, c >> 8])


def _zero_regs(data: bytearray, offset: int, first_reg: int, count: int, scrub: set[int]) -> None:
    for k in range(count):
        if first_reg + k in scrub:
            data[offset + 2 * k: offset + 2 * k + 2] = b"\x00\x00"


def _scrub_frame(fb: bytes, pending: tuple[int, int] | None, scrub: set[int]) -> bytes:
    if not crc_ok(fb):
        return fb[:3] + bytes(len(fb) - 3) if len(fb) > 3 else fb
    kind, info = classify(fb)
    body = bytearray(fb[:-2])
    if kind == "read_req" or kind == "writeN_resp":
        return fb
    if kind == "read_resp":
        if pending and pending[1] == len(info["values"]):
            _zero_regs(body, 3, pending[0], pending[1], scrub)
        else:
            body[3:] = bytes(len(body) - 3)
    elif kind == "writeN_req":
        _zero_regs(body, 7, info["reg"], info["count"], scrub)
    elif kind == "write1":
        _zero_regs(body, 4, info["reg"], 1, scrub)
    else:  # exceptions and unknown function codes: keep addr/fc only
        body[2:] = bytes(len(body) - 2)
    return _with_crc(bytes(body))


def scrub_frames(rows: list[dict], scrub: set[int]) -> list[dict]:
    out, pending = [], None
    for r in rows:
        fb = bytes.fromhex(r["hex"])
        new = _scrub_frame(fb, pending, scrub)
        if crc_ok(fb):
            kind, info = classify(fb)
            if kind == "read_req":
                pending = (info["reg"], info["count"])
            elif kind in ("read_resp", "exception"):
                pending = None
        nr = dict(r)
        nr.update(hex=new.hex(" "), len=str(len(new)), crc_ok=str(int(crc_ok(new))))
        out.append(nr)
    return out


def scrub_registers(rows: list[dict], scrub: set[int]) -> list[dict]:
    return [dict(r, value_u16="0") if int(r["register"]) in scrub else dict(r) for r in rows]


def scrub_console(text: str, allow: list[str]) -> str:
    pats = [re.compile(a) for a in allow]
    kept = []
    for line in ANSI.sub("", text).replace("\r", "\n").split("\n"):
        if line.strip() and any(p.search(line) for p in pats):
            for rx, repl in REDACTIONS:
                line = rx.sub(repl, line)
            kept.append(line)
    return "\n".join(kept) + ("\n" if kept else "")


def scrub_report(text: str) -> str:
    return "".join(l for l in text.splitlines(keepends=True)
                   if not l.lstrip().startswith(("e.g.", "|")))


def find_secrets(console: str, registers: dict[int, int], scrub: set[int]) -> list[str]:
    secrets = {m.group(2) for m in SECRET_FIELDS.finditer(ANSI.sub("", console))}
    raw = b"".join(registers[i].to_bytes(2, "big") for i in sorted(scrub) if i in registers)
    text = raw.decode("latin-1").strip("\x00 ")
    if text:
        secrets.add(text)
        secrets.add(raw.hex(" "))
    return sorted(s for s in secrets if len(s) >= MIN_SECRET_LEN)


def collect_secrets(captures_root: Path, scrub: set[int]) -> list[str]:
    """Secrets from every raw capture under captures_root (console + serial registers)."""
    secrets: set[str] = set()
    if not Path(captures_root).is_dir():
        return []
    for cdir in sorted(p for p in Path(captures_root).iterdir() if p.is_dir()):
        console = "".join(p.read_text(errors="replace") for p in sorted(cdir.glob("*_ascii.txt")))
        regs: dict[int, int] = {}
        if (cdir / "registers.csv").exists():
            for r in _read_csv(cdir / "registers.csv")[1]:
                regs[int(r["register"])] = int(r["value_u16"])
        secrets.update(find_secrets(console, regs, scrub))
    return sorted(secrets)


def verify_clean(out_dir: Path, secrets: list[str]) -> list[str]:
    hits = []
    for f in sorted(p for p in Path(out_dir).rglob("*") if p.is_file() and p.suffix != ".age"):
        data = f.read_bytes().decode("latin-1")
        low = data.lower()
        if any(s in data or s.lower() in low for s in secrets):
            hits.append(str(f.relative_to(out_dir)))
    return hits


def _read_csv(p: Path) -> tuple[list[str], list[dict]]:
    with open(p, newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), list(rd)


def _write_csv(p: Path, fields: list[str], rows: list[dict]) -> None:
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def encrypt_raw(cdir: Path, out: Path, recipient: str) -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        names = ["capture.sal", "meta.json", "registers.csv", "frames.csv"]
        names += sorted(p.name for p in cdir.glob("*_ascii.txt"))
        for name in names:  # text files let leakcheck derive secrets after decrypting
            if (cdir / name).exists():
                tar.add(cdir / name, arcname=name)
    subprocess.run(["age", "-r", recipient, "-o", str(out)], input=buf.getvalue(), check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--scrub-registers", default="3-7")
    ap.add_argument("--console-allow", type=Path, default=DEFAULT_ALLOW)
    ap.add_argument("--age-recipient", help="age public key; encrypts the raw capture (sal, meta, unscrubbed csv/console) to raw.tar.gz.age")
    args = ap.parse_args()

    cdir, out = args.capture_dir, args.out_dir
    scrub = parse_registers(args.scrub_registers)
    allow = [l.strip() for l in args.console_allow.read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    out.mkdir(parents=True, exist_ok=True)

    raw_console = "".join(p.read_text(errors="replace") for p in sorted(cdir.glob("*_ascii.txt")))
    regs: dict[int, int] = {}
    if (cdir / "registers.csv").exists():
        fields, rows = _read_csv(cdir / "registers.csv")
        for r in rows:
            regs[int(r["register"])] = int(r["value_u16"])
        _write_csv(out / "registers.csv", fields, scrub_registers(rows, scrub))
    if (cdir / "frames.csv").exists():
        fields, rows = _read_csv(cdir / "frames.csv")
        _write_csv(out / "frames.csv", fields, scrub_frames(rows, scrub))
    if (cdir / "report.txt").exists():
        (out / "report.txt").write_text(scrub_report((cdir / "report.txt").read_text()))
    if raw_console:
        (out / "console.txt").write_text(scrub_console(raw_console, allow))
    if (cdir / "meta.json").exists():
        shutil.copy(cdir / "meta.json", out / "meta.json")

    secrets = find_secrets(raw_console, regs, scrub)
    hits = verify_clean(out, secrets)
    if hits:
        shutil.rmtree(out)
        print(f"LEAK CHECK FAILED in {hits}; output deleted.", file=sys.stderr)
        return 1
    if args.age_recipient:
        encrypt_raw(cdir, out / "raw.tar.gz.age", args.age_recipient)
    print(f"Scrubbed {cdir.name} -> {out} (checked {len(secrets)} secret patterns, 0 hits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
