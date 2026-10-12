# CLAUDE.md

Guidance for Claude Code (and humans) working in this repo.

## Project

Fork of `judasgutenberg/SolArk_Live_Data`. The goal is to read Sol-Ark 15K
inverter telemetry by passively tapping the Modbus RTU link inside the
WiFi/Ethernet dongle with a XIAO ESP32S3, and publish it to MQTT. The upstream
Arduino sketch (`SolArk_DataInterceptor.ino`) parsed the dongle's debug console
and broke after the Oct 2025 dongle firmware.

Start here:
- `docs/serial-link-findings.md`: verified pinout, protocol (Modbus RTU 9600
  8N1, dongle = master, slave 1), and poll list. **Verified versus inferred are
  kept separate. Keep it that way.**
- `docs/plans/2026-10-11-xiao-firmware-design.md`: approved firmware design
  (Rust, `esp-idf-svc`).
- `tools/README_capture.md`: Saleae Logic Pro 8 capture and decode workflow.

## Standing rules

1. **TDD.** Write a failing test first, then the code. No feature code without
   a test.
2. **No static values.** Anything that could change is configurable (runtime
   config persisted to storage, with defaults). Only protocol-defined constants
   (e.g. the Modbus CRC) and chip facts may be hardcoded. When writing a
   literal, ask "could this change?"
3. **Portable via our own HAL.** App logic lives in chip-independent crates
   (`no_std` where specified) behind our `solark-hal` traits. Board specifics
   live only in `boards/<name>`. Adding a microcontroller must not change the
   core crates.
4. **Security first.** Design against hostile LAN devices, physical access,
   malicious OTA and MQTT spoofing. No default credentials, HTTPS UI, signed
   OTA, MQTT TLS + ACLs, secrets never logged or committed, and
   `#![forbid(unsafe_code)]` in the core crates. **Never burn eFuses** (secure
   boot / flash encryption) without explicit user approval.
5. **Quality gates.** `rustfmt`, `clippy -D warnings`, `cargo-deny`,
   `cargo-audit`, 80% coverage on the core crates; `ruff`, `mypy --strict` and
   `pytest` for `tools/`; pre-commit and pre-push hooks; `make check` must pass
   before commit. Never bypass hooks.
6. **Passive only.** Never connect anything that can transmit on the
   inverter/dongle link (proxy mode is a future, explicitly approved change).
   Saleae captures are listen-only.

## Data handling

- `captures/` is gitignored and must stay out of git. Raw captures contain the
  inverter serial number (registers ~3-7). Committed test fixtures must scrub
  that range.
- **Console captures (`Channel_2_ascii.txt`, `.sal`, `digital.csv`) contain
  the Wi-Fi SSID and password**: the dongle prints them at every boot. Never
  print, grep-display, paste or commit boot-log lines; filter out
  `wifi_manager`/`spiffs_api` lines before showing console output.
- **Leak-check hook:** `tools/hooks/install.sh <repo>` installs a pre-commit
  hook (in this repo and the private data repo) that blocks commits containing
  any secret derived from the raw captures. Install it on every machine.
- Shareable capture data is produced only by `tools/scrub.py` and lives in the
  private `solark-telemetry-data` repo (scrubbed, raw encrypted with age).
- Nothing is posted upstream (issues/PRs) without the user approving the
  wording.

## Tools

```bash
cd tools
# One-time: uv venv .venv && uv pip install --python .venv/bin/python logic2-automation
APPIMAGE_EXTRACT_AND_RUN=1 ~/Downloads/Logic-2.4.48-linux-x64.AppImage --automation &
.venv/bin/python capture.py --seconds 180
.venv/bin/python analyze.py ../captures/<timestamp>
```

The Saleae udev rule is in `tools/99-SaleaeLogic.rules` (install to
`/etc/udev/rules.d/`).
