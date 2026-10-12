# Passive capture of the dongle serial link

Goal: record the inverter <-> dongle traffic on the UT3232G's 3.3 V side, then
decode baud, framing, and whether it is Modbus RTU. Capture is passive: the
Saleae only listens and never drives a line.

## 1. Check the chip with a meter first (dongle powered, Saleae disconnected)

The pin numbers below assume the standard MAX3232 16-pin pinout. Confirm it on
this board before clipping anything on:

| Measure (vs dongle GND) | Expect | Confirms |
|---|---|---|
| UT3232G pin 16 | ~3.3 V | chip orientation and VCC pin |
| UT3232G pin 15 | 0 V (continuity to GND) | GND pin |
| pin 2 / pin 6 | ~+5.5 V / ~-5.5 V | charge pump, so this really is a MAX3232-type part |

If pin 16 isn't 3.3 V, stop: the orientation or pinout is different. A 5 V
VCC also changes the threshold choice.

**Ground offset check:** measure DC and AC volts between dongle GND and the
laptop's USB shell before connecting the Saleae ground. The dongle is powered
from the inverter. If there's any offset, run the laptop on battery
(unplugged) while capturing.

## 2. Wiring

Continuity from the UT3232G to the 10-pin module header (pads labelled 1 and 6
on the carrier) showed:

| Header pad | UT3232G pin | Role |
|---|---|---|
| 6 | 15 | GND |
| 7 | 16 | VCC (should read ~3.3 V vs pad 6 when powered) |
| 8 | - | no continuity to anything on the carrier; unused |
| 9 | 12 (R1OUT) | inverter -> dongle |
| 10 | 11 (T1IN) | dongle -> inverter |
| 1-5 | - | probably Ethernet (toward the magnetics) |

UT3232G pin 9 (R2OUT) has no connection, so only channel 1 of the chip is used.

| Saleae | Clip to | Role |
|---|---|---|
| CH0 | header pad 9 | inverter -> dongle |
| CH1 | header pad 10 | dongle -> inverter |
| CH2 | ESP32 module G/T/R header **T** (next to the NET LED) | ESP32 console out (likely) |
| CH3 | ESP32 module G/T/R header **R** | ESP32 console in |
| GND | header pad 6 | |

CH2/CH3 are the same G/T/R header the original sketch tapped (compare
`../dongle_serial.jpg`). The old `MB_real data,seg_cnt:3` marker was most
likely the ESP32 firmware's debug log, not the inverter link itself, which
would explain why a dongle firmware update broke the parser. Capturing it
alongside the link lets us confirm that.

## 3. One-time setup on this machine

```bash
# Let non-root users access the Saleae (then unplug/replug the Logic Pro 8)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="21a9", MODE="0666"' | sudo tee /etc/udev/rules.d/99-SaleaeLogic.rules
sudo udevadm control --reload && sudo udevadm trigger

# Start Logic 2 with the automation server (libfuse2 isn't installed, so self-extract)
APPIMAGE_EXTRACT_AND_RUN=1 ~/Downloads/Logic-2.4.48-linux-x64.AppImage --automation &
```

Python deps live in `tools/.venv` (created with `uv venv` + `uv pip install logic2-automation`).

## 4. Capture and decode

```bash
cd tools
.venv/bin/python capture.py --seconds 10       # sanity: which channels toggle, idle-high?
.venv/bin/python analyze.py ../captures/<ts>
.venv/bin/python capture.py --seconds 180      # full run
.venv/bin/python analyze.py ../captures/<ts>
```

Defaults: 25 MS/s, 3.3 V threshold, channels 0-3. Each run saves
`capture.sal` (open it in Logic 2), `digital.csv`, and the analyzer's
`report.txt`, `frames.csv`, and `registers.csv`.

`analyze.py` measures baud from pulse widths, tries 8N1/8E1/8O1/8N2, splits
frames on t3.5 idle gaps, checks CRC-16/MODBUS, pairs requests with replies,
and lists the polled register blocks with interval and latency. It was
checked against synthetic 9600 8E1 Modbus plus 115200 ASCII traffic, not yet
against real dongle traffic.
