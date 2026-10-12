#!/usr/bin/env python3
"""Offline decoder for a Saleae raw digital CSV export (from capture.py).

For each active channel it:
  1. measures the baud rate from pulse widths
  2. software-decodes UART as 8N1 / 8E1 / 8O1 / 8N2 and keeps the framing with fewest errors
  3. splits bytes into frames on idle gaps (Modbus t3.5)
  4. checks CRC-16/MODBUS on every frame
Then it pairs Modbus requests with replies across channels and lists the polled
register blocks and their intervals.

Usage: .venv/bin/python analyze.py captures/<timestamp> [--baud N] [--gap-ms X]
Outputs (into the capture dir): report.txt, frames.csv, registers.csv, ch<N>_ascii.txt
"""
import argparse
import bisect
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

STD_BAUDS = [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 76800, 115200,
             128000, 230400, 250000, 460800, 500000, 921600, 1000000]
FRAMINGS = {"8N1": (None, 1), "8E1": ("E", 1), "8O1": ("O", 1), "8N2": (None, 2)}


# ---------------------------------------------------------------- loading

def load_transitions(capture_dir):
    path = Path(capture_dir) / "digital.csv"
    if not path.exists():
        sys.exit(f"{path} not found")
    with open(path, newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        names = header[1:]
        times = {n: [] for n in names}
        levels = {n: [] for n in names}
        prev = [None] * len(names)
        for row in rd:
            t = float(row[0])
            for i, n in enumerate(names):
                v = int(row[i + 1])
                if v != prev[i]:
                    times[n].append(t)
                    levels[n].append(v)
                    prev[i] = v
        end_time = t
    return names, times, levels, end_time


# ---------------------------------------------------------------- UART

def deglitch(times, levels, min_width):
    """Drop pulses shorter than min_width (noise spikes); keeps levels alternating."""
    t_out, l_out = [], []
    for t, v in zip(times, levels):
        if l_out and t - t_out[-1] < min_width and len(t_out) > 1:
            t_out.pop()
            l_out.pop()
            continue
        t_out.append(t)
        l_out.append(v)
    return t_out, l_out


def idle_level(times, levels, end_time):
    """Level the line spends the most time in."""
    dur = [0.0, 0.0]
    for i, (t, v) in enumerate(zip(times, levels)):
        t_next = times[i + 1] if i + 1 < len(times) else end_time
        dur[v] += t_next - t
    return 1 if dur[1] >= dur[0] else 0


def estimate_baud(times):
    widths = [b - a for a, b in zip(times, times[1:]) if 0 < b - a < 0.02]
    if len(widths) < 20:
        return None, None
    widths.sort()
    w_min = widths[max(0, len(widths) // 100)]  # ~1st percentile, rejects rare glitches
    cluster = [w for w in widths if 0.7 * w_min <= w <= 1.4 * w_min]
    bit = statistics.median(cluster)
    measured = 1.0 / bit
    nearest = min(STD_BAUDS, key=lambda b: abs(b - measured) / b)
    return measured, nearest


def level_at(times, levels, t):
    i = bisect.bisect_right(times, t) - 1
    return levels[i] if i >= 0 else levels[0]


def uart_decode(times, levels, baud, parity, stop_bits):
    """Decode idle-high, LSB-first UART. Returns list of (t_start, t_end, byte, ok)."""
    bit = 1.0 / baud
    nbits = 1 + 8 + (1 if parity else 0) + stop_bits
    falls = [t for t, v in zip(times, levels) if v == 0]
    out = []
    next_ok = -1.0
    for t0 in falls:
        if t0 < next_ok:
            continue
        if level_at(times, levels, t0 + 0.5 * bit) != 0:
            continue  # glitch, not a start bit
        val = 0
        for k in range(8):
            val |= level_at(times, levels, t0 + (1.5 + k) * bit) << k
        ok = True
        pos = 9.5
        if parity:
            p = level_at(times, levels, t0 + pos * bit)
            ones = bin(val).count("1") + p
            ok &= (ones % 2 == 0) if parity == "E" else (ones % 2 == 1)
            pos += 1
        for s in range(stop_bits):
            ok &= level_at(times, levels, t0 + (pos + s) * bit) == 1
        out.append((t0, t0 + nbits * bit, val, ok))
        next_ok = t0 + (nbits - 0.5) * bit
    return out


# ---------------------------------------------------------------- Modbus

def crc16_modbus(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def crc_ok(frame):
    return len(frame) >= 4 and crc16_modbus(frame[:-2]) == (frame[-2] | frame[-1] << 8)


def split_frames(decoded, gap):
    frames, cur = [], []
    for b in decoded:
        if cur and b[0] - cur[-1][1] > gap:
            frames.append(cur)
            cur = []
        cur.append(b)
    if cur:
        frames.append(cur)
    return frames


def crc_resync(frame_bytes):
    """Split a run that failed CRC into back-to-back CRC-valid frames, if possible."""
    parts, start = [], 0
    while start < len(frame_bytes):
        for end in range(start + 4, len(frame_bytes) + 1):
            if crc_ok(frame_bytes[start:end]):
                parts.append((start, end))
                start = end
                break
        else:
            return None
    return parts


def classify(fb):
    """Return (kind, info) for a CRC-valid Modbus RTU frame."""
    addr, fc = fb[0], fb[1]
    n = len(fb)
    if fc & 0x80 and n == 5:
        return "exception", {"addr": addr, "fc": fc & 0x7F, "code": fb[2]}
    if fc in (3, 4):
        if n == 8:
            return "read_req", {"addr": addr, "fc": fc, "reg": fb[2] << 8 | fb[3], "count": fb[4] << 8 | fb[5]}
        if n == 5 + fb[2] and fb[2] % 2 == 0:
            regs = [fb[3 + 2 * i] << 8 | fb[4 + 2 * i] for i in range(fb[2] // 2)]
            return "read_resp", {"addr": addr, "fc": fc, "values": regs}
    if fc == 6 and n == 8:
        return "write1", {"addr": addr, "fc": fc, "reg": fb[2] << 8 | fb[3], "value": fb[4] << 8 | fb[5]}
    if fc == 0x10:
        if n == 8:
            return "writeN_resp", {"addr": addr, "fc": fc, "reg": fb[2] << 8 | fb[3], "count": fb[4] << 8 | fb[5]}
        if n >= 9 and n == 9 + fb[6]:
            return "writeN_req", {"addr": addr, "fc": fc, "reg": fb[2] << 8 | fb[3], "count": fb[4] << 8 | fb[5]}
    return "other", {"addr": addr, "fc": fc}


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir")
    ap.add_argument("--baud", type=int, help="force baud instead of measuring")
    ap.add_argument("--gap-ms", type=float, help="force inter-frame gap threshold")
    ap.add_argument("--glitch-us", type=float, default=0.5,
                    help="ignore pulses shorter than this (0 disables); 0.5us is below one bit at 921600 baud")
    args = ap.parse_args()
    cdir = Path(args.capture_dir)

    names, T, L, end_time = load_transitions(cdir)
    report = []
    say = lambda s="": (print(s), report.append(s))

    say(f"Capture: {cdir}  duration {end_time:.1f}s")
    if args.glitch_us > 0:
        for n in names:
            raw = len(T[n])
            T[n], L[n] = deglitch(T[n], L[n], args.glitch_us * 1e-6)
            if raw - len(T[n]):
                say(f"{n}: removed {raw - len(T[n])} glitch edges (< {args.glitch_us} us)")
    say("\n== Channel activity (measured) ==")
    all_frames = []  # (t_start, t_end, channel, bytes)
    for n in names:
        times, levels = T[n], L[n]
        edges = len(times) - 1
        if edges < 20:
            state = levels[0] if levels else "?"
            say(f"{n}: no activity ({edges} edges, static level {state})")
            continue
        idle = idle_level(times, levels, end_time)
        measured, nearest = (args.baud, args.baud) if args.baud else estimate_baud(times)
        say(f"{n}: {edges} edges, idles {'HIGH' if idle else 'LOW (inverted or not UART?)'}, "
            f"measured ~{measured:.0f} baud -> nearest standard {nearest}"
            f" ({(measured - nearest) / nearest * 100:+.1f}%)")
        if not idle:
            continue

        results = {}
        for fname, (par, stop) in FRAMINGS.items():
            dec = uart_decode(times, levels, nearest, par, stop)
            bad = sum(1 for d in dec if not d[3])
            results[fname] = (bad, dec)
            say(f"    {fname}: {len(dec)} bytes, {bad} framing/parity errors ({bad / max(1, len(dec)) * 100:.2f}%)")
        best = min(results, key=lambda k: (results[k][0] / max(1, len(results[k][1])), k != "8N1"))
        dec = results[best][1]
        par, stop = FRAMINGS[best]
        char_bits = 1 + 8 + (1 if par else 0) + stop
        gap = (args.gap_ms / 1000) if args.gap_ms else (
            3.5 * char_bits / nearest if nearest <= 19200 else 0.00175)
        say(f"    -> best framing {best}; frame gap threshold {gap * 1000:.2f} ms")

        data = bytes(d[2] for d in dec)
        printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(data))
        if printable > 0.85:
            txt = data.decode("ascii", "replace")
            out = cdir / f"{n.replace(' ', '_')}_ascii.txt"
            out.write_text(txt)
            say(f"    looks like ASCII text ({printable * 100:.0f}% printable) -> {out.name}")
            for line in [l for l in txt.replace("\r", "\n").split("\n") if l.strip()][:8]:
                say(f"      | {line[:150]}")
            continue

        frames = split_frames(dec, gap)
        good = resynced = 0
        for fr in frames:
            fb = bytes(d[2] for d in fr)
            if crc_ok(fb):
                good += 1
                all_frames.append((fr[0][0], fr[-1][1], n, fb))
                continue
            parts = crc_resync(fb)
            if parts:
                resynced += 1
                for s, e in parts:
                    all_frames.append((fr[s][0], fr[e - 1][1], n, fb[s:e]))
            else:
                all_frames.append((fr[0][0], fr[-1][1], n, fb))
        say(f"    {len(frames)} frames by gap; CRC-16/MODBUS pass {good}/{len(frames)} "
            f"({good / max(1, len(frames)) * 100:.1f}%), +{resynced} recovered by CRC resync")
        for fr in frames[:5]:
            say(f"      e.g. t={fr[0][0]:9.4f}s  " + " ".join(f"{d[2]:02X}" for d in fr[:40])
                + (" ..." if len(fr) > 40 else ""))

    all_frames.sort()
    with open(cdir / "frames.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_start", "t_end", "channel", "len", "crc_ok", "kind", "hex"])
        for t0, t1, ch, fb in all_frames:
            ok = crc_ok(fb)
            w.writerow([f"{t0:.6f}", f"{t1:.6f}", ch, len(fb), int(ok),
                        classify(fb)[0] if ok else "", fb.hex(" ")])

    valid = [(t0, t1, ch, fb, *classify(fb)) for t0, t1, ch, fb in all_frames if crc_ok(fb)]
    if not valid:
        say("\nNo CRC-valid Modbus RTU frames found. Not Modbus RTU at the measured settings "
            "(or wrong pins); inspect frames.csv / the .sal in Logic 2.")
        (cdir / "report.txt").write_text("\n".join(report) + "\n")
        return

    say("\n== Modbus (verified by CRC) ==")
    kinds_by_ch = defaultdict(lambda: defaultdict(int))
    for v in valid:
        kinds_by_ch[v[2]][v[4]] += 1
    for ch, k in kinds_by_ch.items():
        say(f"{ch}: " + ", ".join(f"{kk}={cnt}" for kk, cnt in sorted(k.items())))

    # Pair each read request with the first matching response on another channel.
    requests = [v for v in valid if v[4] == "read_req"]
    responses = [v for v in valid if v[4] in ("read_resp", "exception")]
    used = set()
    blocks = defaultdict(lambda: {"times": [], "latency": [], "answered": 0, "exceptions": 0, "req_ch": set()})
    reg_rows = []
    for t0, t1, ch, fb, kind, info in requests:
        key = (info["addr"], info["fc"], info["reg"], info["count"])
        b = blocks[key]
        b["times"].append(t0)
        b["req_ch"].add(ch)
        for j, r in enumerate(responses):
            if j in used or r[2] == ch or r[0] < t1:
                continue
            if r[0] - t1 > 2.0:
                break
            ri = r[5]
            if ri["addr"] != info["addr"] or ri["fc"] != info["fc"]:
                continue
            if r[4] == "exception":
                b["exceptions"] += 1
            elif len(ri["values"]) == info["count"]:
                b["answered"] += 1
                for k, val in enumerate(ri["values"]):
                    reg_rows.append((f"{r[0]:.4f}", info["addr"], info["fc"], info["reg"] + k, val))
            else:
                continue
            used.add(j)
            b["latency"].append(r[0] - t1)
            break

    say(f"\nPolled register blocks ({len(requests)} read requests, {len(used)} paired replies):")
    say(f"{'addr':>4} {'fc':>2} {'start':>6} {'(hex)':>7} {'count':>5} {'reqs':>5} {'ans':>4} {'exc':>3} "
        f"{'interval s (median)':>20} {'latency ms':>10}  req channel")
    for key in sorted(blocks):
        a, fc, reg, cnt = key
        b = blocks[key]
        iv = statistics.median([y - x for x, y in zip(b["times"], b["times"][1:])]) if len(b["times"]) > 1 else float("nan")
        lat = statistics.median(b["latency"]) * 1000 if b["latency"] else float("nan")
        say(f"{a:>4} {fc:>2} {reg:>6} {reg:>#7x} {cnt:>5} {len(b['times']):>5} {b['answered']:>4} {b['exceptions']:>3} "
            f"{iv:>20.2f} {lat:>10.1f}  {','.join(sorted(b['req_ch']))}")

    others = [v for v in valid if v[4] not in ("read_req", "read_resp", "exception")]
    if others:
        say(f"\nOther Modbus traffic ({len(others)} frames, e.g. writes):")
        for v in others[:20]:
            say(f"  t={v[0]:9.4f}s {v[2]} {v[4]} {v[5]}  {v[3].hex(' ')}")

    with open(cdir / "registers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "addr", "fc", "register", "value_u16"])
        w.writerows(reg_rows)
    say(f"\nWrote frames.csv, registers.csv ({len(reg_rows)} register samples), report.txt to {cdir}")
    (cdir / "report.txt").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
