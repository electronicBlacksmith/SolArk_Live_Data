#!/usr/bin/env python3
"""Passive capture of the dongle's serial lines with a Saleae Logic Pro 8.

Records digital inputs only. The Saleae never drives a line.

Run from the tools/ directory:
  .venv/bin/python capture.py --seconds 10      # sanity check
  .venv/bin/python capture.py --seconds 180     # full capture

Logic 2 must be running with automation enabled (see README_capture.md), or
pass --launch to start it.
"""
import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from saleae import automation

# Channel map: Saleae channel -> what it is clipped to. Keep in sync with README_capture.md.
# 10-pin module header pads were mapped to UT3232G pins by continuity: 6=GND(15), 7=VCC(16), 9=R1OUT(12), 10=T1IN(11). Pad 8 has no carrier-side connection.
CHANNELS = {
    0: "header pad 9  = U3232 pin12 R1OUT (inverter->dongle)",
    1: "header pad 10 = U3232 pin11 T1IN  (dongle->inverter)",
    2: "ESP32 module G/T/R header T",
    3: "ESP32 module G/T/R header R",
}

DEFAULT_APPIMAGE = Path.home() / "Downloads" / "Logic-2.4.48-linux-x64.AppImage"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--rate", type=int, default=25_000_000, help="digital sample rate (Hz)")
    ap.add_argument("--threshold", type=float, default=3.3, help="digital threshold volts (Pro 8: 1.2/1.8/3.3)")
    ap.add_argument("--channels", default=",".join(str(c) for c in CHANNELS))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "captures"))
    ap.add_argument("--launch", action="store_true", help="launch Logic 2 instead of connecting to a running one")
    ap.add_argument("--app", default=str(DEFAULT_APPIMAGE))
    ap.add_argument("--label", default="", help="short tag appended to the capture folder name and saved in meta.json")
    args = ap.parse_args()

    channels = [int(c) for c in args.channels.split(",") if c.strip()]
    label = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.label.strip())
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out) / (f"{stamp}-{label}" if label else stamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.launch:
        # No libfuse2 on this machine; the AppImage runtime can self-extract instead.
        os.environ.setdefault("APPIMAGE_EXTRACT_AND_RUN", "1")
        manager = automation.Manager.launch(application_path=args.app, connect_timeout_seconds=60)
    else:
        manager = automation.Manager.connect(connect_timeout_seconds=10)

    with manager:
        devices = [d for d in manager.get_devices() if not d.is_simulation]
        if not devices:
            sys.exit("No physical Saleae device visible to Logic 2 (check USB permissions / udev rule).")
        dev = devices[0]
        print(f"Device: {dev.device_type} id={dev.device_id}")

        dev_cfg = automation.LogicDeviceConfiguration(
            enabled_digital_channels=channels,
            digital_sample_rate=args.rate,
            digital_threshold_volts=args.threshold,
        )
        cap_cfg = automation.CaptureConfiguration(
            capture_mode=automation.TimedCaptureMode(duration_seconds=args.seconds)
        )

        print(f"Capturing {args.seconds:.0f}s on channels {channels} @ {args.rate/1e6:.0f} MS/s, {args.threshold} V threshold...")
        t0 = time.time()
        with manager.start_capture(device_id=dev.device_id, device_configuration=dev_cfg,
                                   capture_configuration=cap_cfg) as capture:
            try:
                capture.wait()
            except KeyboardInterrupt:
                # Otherwise Logic 2 keeps recording after this script exits.
                capture.stop()
                print("Interrupted; recording stopped, saving partial capture...")
            print(f"Capture done in {time.time()-t0:.1f}s; saving...")
            capture.save_capture(str(out_dir / "capture.sal"))
            capture.export_raw_data_csv(str(out_dir), digital_channels=channels)

    meta = {
        "started": datetime.now().isoformat(timespec="seconds"),
        "label": args.label,
        "seconds": args.seconds,
        "sample_rate": args.rate,
        "threshold_volts": args.threshold,
        "channels": {str(c): CHANNELS.get(c, "?") for c in channels},
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Saved to {out_dir}")
    print(f"Next: .venv/bin/python analyze.py {out_dir}")


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _raise_interrupt)  # treat kill/pkill like Ctrl-C
    main()
