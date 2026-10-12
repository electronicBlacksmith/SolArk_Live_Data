# Sol-Ark 15K dongle serial link: capture findings (2026-10-11)

Captures: `captures/20261011-182536` (10 s), `captures/20261011-182712` (180 s).
Tools: `tools/capture.py`, `tools/analyze.py` (see `tools/README_capture.md`).

## Tap points (verified by continuity)

The UT3232G (MAX3232-type) uses only channel 1. On the 10-pin module header
(silkscreen "1" and "6" on the carrier):

| Header pad | UT3232G pin | Signal |
|---|---|---|
| 6 | 15 | GND |
| 7 | 16 | VCC (not yet measured under power) |
| 9 | 12 R1OUT | inverter -> dongle (TTL) |
| 10 | 11 T1IN | dongle -> inverter (TTL) |
| 8 | - | no carrier-side connection |

UT3232G pin 9 (R2OUT) is unconnected. The ESP32 module's G/T/R header **T** pad
is the ESP-IDF debug console (115200 8N1); **R** was idle.

## Measured

- Both link lines idle high and run at **9600 baud, 8N1**, with 0 framing errors
  over 180 s. 8E1/8O1/8N2 gave 79-95% errors, so they are ruled out.
- **Modbus RTU confirmed**: 102/102 frames on each line pass CRC-16/MODBUS.
- Pad 10 carries only requests and pad 9 only replies, so the **dongle is the
  master** and the inverter is slave **address 1**. Only **function 03** (read
  holding registers) was seen, with no writes and no exceptions in 180 s.
  Replies arrive 24-26 ms after each request.
- Polled blocks (start register, count, interval):

| Start | Hex | Count | Every |
|---|---|---|---|
| 0 | 0x000 | 19 | 30 s |
| 15 | 0x00F | 1 | 30 s |
| 20 | 0x014 | 5 | 30 s |
| 25 | 0x019 | 34 | 30 s |
| 59 | 0x03B | 66 | **10 s** |
| 150 | 0x096 | 50 | **10 s** |
| 200 | 0x0C8 | 100 | 30 s |
| 300 | 0x12C | 16 | 30 s |
| 312 | 0x138 | 8 | **10 s** |
| 320 | 0x140 | 100 | 30 s |
| 433 | 0x1B1 | 55 | 30 s |

- Signal quality: there are many glitches under 0.5 us on every channel
  (thousands per second), which `analyze.py` filters out (`--glitch-us`). These
  are probably from grounding or a loose clip, or switching-regulator noise.
  Real bits are 104 us wide, so the decode is unaffected.

## Inferred (not verified)

- Register meanings follow the Deye/Sunsynk single-phase hybrid map. The values
  are physically consistent:
  - 183 battery V = 52.45 and 191 battery A = 86.67, whose product (4546 W)
    matches 190 battery W = 4545.
  - 175 inverter W 5533 + 169 grid W 11 = 178 load W 5544.
  - 79/192/193 are 59.95 Hz, 150 is 124.8 V, 184 SOC is 87 %.
  - Register 90 did not decode sensibly with the assumed temperature formula,
    so not every register follows that map.
  - Not yet checked against the MySolArk app for the same moment.
- The console shows the cloud server pushes the poll list to the dongle
  (`tcp_client: Config item: N (op, at, fc, addr, rn)`) and can send commands
  (`recv server cmd`). So the poll set and intervals can change server-side, and
  a passive tap only sees what the cloud asks for.
- The poll list the cloud pushed (console, `Config version: 8`) has 12 items,
  `(op, at, fc, addr, rn)`:
  - `op:0` (10 s): 59x66, 150x50, 312x8
  - `op:1` (30 s): 15x1, 20x2, 25x34, 200x100, 300x16, 320x100, 433x55
  - `op:2`: 44x4, and `op:3`: 42x2. Neither appeared on the wire in 180 s, so
    `op` 2 and 3 are probably slower or event-driven schedules (unverified).
  - The list and the wire differ. The wire also shows 0x19 every 30 s, which
    isn't in the list (perhaps a built-in dongle poll), and the wire shows 20x5
    where the list says 20x2. Trust the wire.
- **Privacy:** registers ~3-7 contain an ASCII string, almost certainly the
  inverter serial number. Raw captures (`captures/`, gitignored) must not be
  committed, and any committed fixture must scrub that range.
- The old sketch's `MB_real data,seg_cnt:3` marker was almost certainly from
  this same debug console. The firmware's log format changed, not the Modbus
  link.

## Implication for the XIAO ESP32S3

Passive option: listen on pad 9 (and optionally pad 10) at 9600 8N1, split
frames on 3.5-character gaps, check CRC, pair each reply with the preceding
request to learn its start register, and decode. That gives 10 s updates for
registers 59-124, 150-199 and 312-319 without touching the bus.
