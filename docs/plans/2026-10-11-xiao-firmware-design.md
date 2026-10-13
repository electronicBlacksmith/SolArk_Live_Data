# XIAO ESP32S3 Sol-Ark telemetry firmware: design

Status: approved design (2026-10-11). Next step: implementation plan.
Evidence: [`docs/serial-link-findings.md`](../serial-link-findings.md).
Standing rules: [`CLAUDE.md`](../../CLAUDE.md).

## Goal

A Seeed XIAO ESP32S3 Plus, installed inside the Sol-Ark 15K WiFi/Ethernet
dongle, passively decodes the Modbus RTU traffic between the dongle and the
inverter. It publishes near-real-time telemetry (about every 10 s) to MQTT. The
first consumer will be a Tesla charging controller (a separate, later project).
The device has an authenticated HTTPS management UI and signed OTA updates.

Non-goals for v1: sending anything on the inverter link (proxy mode is a
possible later step, see "Future"), the Tesla charging logic itself, and Home
Assistant discovery.

## 1. Hardware

```
Inverter DB9 ──12V──► Pololu D45V5F5 (5V 0.5A) ──5V──► XIAO 5V pin
           └─RS-232─► UT3232G ──TTL──┬─ header pad 9  (inverter→dongle) ──► XIAO UART RX "resp"
                                      └─ header pad 10 (dongle→inverter) ──► XIAO UART RX "req"
                                         header pad 6 GND ─────────────────► XIAO GND
```

- **Receive only.** No XIAO TX pin is connected to the link, so the firmware
  physically cannot disturb the dongle or the inverter.
- Both directions are captured. Requests on pad 10 give the start register for
  each reply. Reply length alone is ambiguous (two blocks are both 100
  registers).
- Pad numbers refer to the 10-pin module header ("1"/"6" silkscreen); see the
  findings doc.
- Before permanent install: measure the dongle's 12 V input and confirm the
  D45V5F5 input range and headroom.

## 2. Software architecture (portable by design)

Hardware is reached only through our own traits. The application logic is
sans-IO: it consumes bytes, timestamps and requests and returns actions, so it
runs the same way on threaded `esp-idf-svc`, bare-metal async (`embassy`), and a
PC.

| Crate | Chip-specific? | Responsibility |
|---|---|---|
| `crates/solark-modbus` | no, `no_std` | CRC-16/MODBUS, frame splitting by idle gap, CRC resync, request/reply pairing, register store |
| `crates/solark-core` | no, `no_std` + `alloc` | Config model, validation and migration; register-map decoding; burst detection; staleness; health counters; MQTT payloads; web API handlers; auth and session logic |
| `crates/solark-hal` | no | Our HAL traits: `SerialRx`, `Clock`, `KvStore`, `Network`, `MqttClient`, `HttpServer`, `Ota`, `Watchdog`, `Button`, `Reset`, `LogSink`, `Crypto` |
| `crates/solark-app` | no | Runtime generic over the `solark-hal` traits; wires the core to the I/O |
| `crates/solark-webui` | no | Static HTML/CSS/JS, gzipped and embedded |
| `boards/xiao-esp32s3` | yes | `esp-idf-svc` trait implementations plus board default pins |
| `boards/host` | no (Linux) | PC implementations: serial replayed from capture files, real MQTT and HTTPS; used for development and integration tests |

Adding a microcontroller means adding one `boards/<name>` crate. The core
crates must not change.

Repo layout: a Cargo workspace at the root of this fork, alongside the existing
upstream files (`SolArk_DataInterceptor.ino`, etc.) and `tools/`.

## 3. Data flow

1. **Framing.** Each RX UART uses the hardware RX-idle timeout. A frame ends
   after the configured gap (default 3.5 character times, derived from baud,
   about 3.6 ms at 9600). Frames are timestamped from a single monotonic
   `Clock` so the two directions can be ordered.
2. **Validation.** CRC-16/MODBUS on every frame. On failure, try splitting into
   back-to-back CRC-valid frames; otherwise drop the frame and count it.
3. **Pairing.** A valid read request (fc 03/04) on the request line becomes
   pending. The next valid reply on the response line pairs with it if the
   address and fc match, the byte count equals 2 × the requested count, and it
   arrives within the reply timeout. Matching values are stored at registers
   `start..start+count` with a timestamp.
4. **Publish trigger.** After a configured quiet period following the last
   reply of a burst, publish one consistent snapshot. Publishing follows the
   dongle's own schedule (currently 10 s), not a separate timer.

### MQTT topics (prefix and device id configurable)

| Topic | Payload | Retained |
|---|---|---|
| `solark/<id>/state` | Decoded JSON: `ts`, `soc`, `battery_w`, `battery_v`, `battery_a`, `pv1_w`, `pv2_w`, `pv_w`, `grid_w`, `load_w`, `inverter_w`, `grid_hz`, `age_s` (fields come from the register map) | yes |
| `solark/<id>/raw/<start>` | `{ts, start, values:[u16…]}` per block | no |
| `solark/<id>/status` | `online` / `offline` (LWT), `link_ok` / `link_stale` | yes |
| `solark/<id>/health` | frames OK, CRC errors, unpaired, timeouts, exceptions, last-frame age, uptime, RSSI, free heap, reset reason, firmware version | no |
| `solark/<id>/security` | security events (login failures, lockouts, OTA, config changes) | no |
| `solark/<id>/changes` | version change or settings diff: old and new versions, per-register before/after | no |
| `solark/<id>/capture/<session>` | chunked raw recording from the anomaly recorder | no |
| `solark/<id>/writes` | every Modbus write seen on the link (fc06/fc16): `ts`, register, values, acknowledged or exception, decoded where known (e.g. clock sync at registers 22-24) | no |

**Writes are observed, not just tolerated.** The dongle writes the inverter's
clock at boot (verified), and app-initiated setting changes presumably travel
the same way. Publishing them gives an audit trail of what the cloud changes on
the inverter. The pairing logic handles fc06/fc16 request/acknowledgement pairs
alongside reads.

The raw topics let server-side consumers fix register meanings without
reflashing.

**Consumer contract:** do not act on data when `status` is `link_stale` or
`age_s` exceeds the consumer's limit; fall back to a safe default.

### Change and update recorder

Goal: an audit trail of what the cloud changes on the inverter, including
inverter firmware updates (presumably delivered over this same link; the
method is unknown), so regressions can be traced.

- **Version tracking.** The firmware watches configurable "version"
  registers (candidates are in the boot-time 0-29 block; to be identified).
  On any change it publishes `solark/<id>/changes`: the old and new versions,
  plus a diff of every known register before and after (the last full snapshot
  vs the first full snapshot after the change).
- **Settings diffs.** Every write (fc06/fc16) is published on `writes`; the
  30 s settings blocks are also diffed, so changes made by any path show up.
- **Anomaly capture.** Triggers (all configurable):
  - writes beyond the known clock-sync pattern
  - unknown function codes
  - a run of CRC/framing failures (suggests a baud change, e.g. bootloader
    mode)
  - traffic volume well above the learned schedule
  - link silence followed by a different pattern

  When a trigger fires, the firmware records the raw timestamped bytes from
  both lines into a pre-allocated ring buffer, including a configurable
  pre-trigger window. It switches the RX UARTs to automatic baud detection if
  framing fails, and streams the recording to `solark/<id>/capture/<session>`
  in chunks. A server-side subscriber reassembles it for offline analysis with
  `tools/analyze.py`.
- **Limits (stated honestly).** This reveals *that* firmware changed, *what
  register-visible behavior* changed, and the raw update traffic. Interpreting
  the firmware contents is out of scope.
- **Privacy.** Recordings contain the inverter serial and are sensitive. They
  go only to the TLS-protected broker under the device ACL and must be
  scrubbed before archiving to a repo.

## 4. Configuration (standing rule: nothing changeable is hardcoded)

- One typed config struct, persisted in `KvStore` (NVS on ESP32), with a schema
  version and migrations.
- Firmware defaults, overridden by saved values. Each board crate supplies its
  own defaults (pins, etc.).
- Factory reset: hold BOOT at power-on (hold time configurable).
- JSON import and export (secrets excluded unless explicitly requested, with
  re-auth).
- Validated before save (for example, pin conflicts, or a frame gap longer than
  the reply timeout).
- Applied live where possible; the UI flags settings that need a reboot.

| Group | Settings (default) |
|---|---|
| Link | RX pin for each direction, baud (9600), framing (8N1), slave address filter (1), frame gap (3.5 chars, derived), RX glitch filter |
| Timing | reply timeout (500 ms), burst-end quiet (500 ms), stale threshold (30 s) |
| Recorder | version registers, anomaly triggers and thresholds, ring buffer size, pre-trigger window, chunk size, autobaud on/off |
| Register map | entries of name, register, words (1/2), signed, scale, offset, unit, `verified` flag; editable in the UI |
| MQTT | host, port, TLS, CA/cert pin, user, password, client id, topic prefix (`solark`), device id (from MAC), QoS, enabled topics, health interval (60 s) |
| Network | ordered Wi-Fi list, hostname, DHCP or static, setup AP SSID and password, AP timeout, no-Wi-Fi fallback delay, reconnect backoff base and cap |
| Management | admin user, password hash, PBKDF2 iterations, session timeout, login backoff and lockout, HTTPS cert, HTTP port mode (off or redirect), OTA enabled, log buffer size |

Only protocol-defined values (the Modbus CRC polynomial, frame layout) and
chip facts are constants.

### Initial register map (all `verified: false`)

Deye/Sunsynk single-phase hybrid lineage, checked for physical consistency
only (see the findings doc): 59 run state, 79 grid Hz (×0.01), 150 grid V
(×0.1), 167 grid L1 W (signed), 169 grid W (signed), 172 grid CT W (signed),
175 inverter W (signed), 178 load W (signed), 182 battery temp ((raw−1000)×0.1),
183 battery V (×0.01), 184 SOC %, 186 PV1 W, 187 PV2 W, 190 battery W (signed,
+discharge), 191 battery A (signed, ×0.01), 192 load Hz, 193 inverter Hz.
Register 90's meaning is unknown. Set `verified: true` per entry only after
comparing with the MySolArk app at the same moment.

## 5. Error handling and robustness

| Condition | Behavior |
|---|---|
| CRC failure | resync attempt, else drop; `crc_errors++` |
| Reply without request, or mismatch | drop; `unpaired++` |
| Request with no reply | expire after reply timeout; `timeouts++` |
| Modbus exception | record `last_exception`, `exceptions++`, keep old values |
| No valid traffic for the stale threshold | `status=link_stale`; `state` keeps publishing with a growing `age_s` |
| Wi-Fi loss | reconnect with backoff through the ordered list; setup AP after the fallback delay |
| Broker loss | reconnect with backoff; keep only the latest `state` (no backlog) |
| Hung task | hardware watchdog fed by the main loop and each RX reader; reset reason reported in `health` |
| Bad OTA | the image marks itself valid only after Wi-Fi, MQTT and one paired frame within a configured window; otherwise automatic rollback |
| Corrupt or incompatible config | boot on defaults plus setup AP; keep the corrupt blob for export |

Fixed-capacity buffers (register store, logs, frames); free heap is reported.

## 6. Security (standing rule: security first)

Threats considered: a hostile LAN device or guest, physical access at the
inverter, malicious firmware, spoofed MQTT data steering charging, and web
attacks.

- **HTTPS-only UI.** Self-signed certificate generated on the device at first
  boot (fingerprint shown in the UI), or upload a certificate from your own CA.
  Plain HTTP is off or redirect-only.
- **No default credentials.** The first login forces setting the admin
  password. PBKDF2-HMAC-SHA256 with a salt and configurable iterations.
- **Sessions.** Cookies are `HttpOnly; Secure; SameSite=Strict`, with a
  configurable timeout. A CSRF token is required on every state-changing
  request. Login backoff and lockout.
- **Strict CSP.** No inline scripts, no third-party origins. Typed,
  size-limited parsing of all inputs; request body limits.
- **Re-auth** for OTA, password change, config import/export with secrets, and
  factory reset.
- **Setup AP** opens only when there is no config or after a physical BOOT
  press; it auto-closes after a timeout. WPA2 with a password set during USB
  provisioning (no built-in default).
- **Signed OTA.** ed25519 signature verified against an on-device public key
  (behind the `Ota`/`Crypto` traits, so portable). Anti-rollback version
  counter. The private key never enters the repo.
- **MQTT.** TLS with broker certificate pinning, per-device credentials, and
  Mosquitto ACLs: the device may publish only under `solark/<id>/#`; consumers
  are read-only.
- **Secrets** are never logged and are excluded from exports by default.
  Security events go to the log and the `security` topic.
- **Code.** `#![forbid(unsafe_code)]` in all chip-independent crates;
  `cargo-audit` and `cargo-deny`; `gitleaks` in the pre-commit hook.
- **Network (recommended).** Put the XIAO on the UniFi IoT VLAN, with firewall
  rules allowing only the broker, NTP and the admin host.
- **Chip lockdown (Secure Boot v2 + flash encryption) is deferred.** These burn
  eFuses irreversibly. Develop in dev mode, then run a separate, explicit
  production-provisioning checklist on a spare XIAO first, and on the installed
  unit only with the user's approval.

## 7. Testing (standing rule: TDD)

Write the failing test first, every time.

1. **Unit (host):**
   - `solark-modbus`: CRC known vectors, framing (partial and concatenated
     frames), resync, pairing edge cases, property tests (random bytes never
     panic).
   - `solark-core`: config validation and migration, map decoding, burst and
     staleness logic, payload JSON schema, auth throttling, sessions, CSRF.
2. **Golden capture tests.** Fixtures derived from `captures/20261011-182712`
   (decoded frames plus a short raw excerpt, **with registers 3-7 scrubbed**).
   Replaying them must reproduce `analyze.py`: 102/102 CRC-valid on each line,
   the 11 blocks and intervals, and identical register values.
3. **Integration (`boards/host`).** Full app with replayed captures, a real
   Mosquitto in Docker, and HTTPS: topics, retain, LWT, the `link_stale`
   transition, login, CSRF, config round-trip, signed versus unsigned OTA (fake
   backend), brute-force lockout, oversized bodies, no secrets in logs or
   exports.
4. **On hardware (checklist plus scripts).** Bench replay into the XIAO RX
   pins; in-dongle comparison of MQTT values with a simultaneous Saleae capture
   and with the MySolArk app; failure drills (Wi-Fi, broker, link unplug, bad
   OTA rollback, watchdog).
5. **Coverage gate:** at least 80% on the chip-independent crates
   (`cargo-llvm-cov`).

## 8. Project hygiene

- Rust: `rustfmt`, `clippy -D warnings` (pedantic in the core crates),
  `cargo-deny`, `cargo-audit`, coverage gate.
- Python `tools/`: `ruff` (lint and format), `mypy --strict`, `pytest`; turn
  the synthetic-capture generator into tests.
- Hooks: pre-commit (format, lint, fast tests, `gitleaks`); pre-push (full
  `make check`). `make install-tools` sets them up.
- CI (GitHub Actions on the fork): `make check` for host crates, plus a XIAO
  firmware build job using `espup`.
- Conventional commits; feature branches with PRs into the fork's `main`.
- Raw captures stay out of git (`captures/` is gitignored; they contain the
  inverter serial number).

## 9. Upstream contribution (judasgutenberg/SolArk_Live_Data)

1. Open an issue thanking the author and sharing the key finding: the dongle
   link is plain Modbus RTU at 9600 8N1 on module header pads 9/10, which
   should be stable across dongle firmware updates, unlike the debug console
   the old sketch parsed. Ask whether he'd like a PR.
2. If yes: a PR from a branch based on **his** `main` with the findings doc and
   pinout, the Saleae `tools/`, and optionally a small Arduino Modbus-decoding
   example. Credit his original work. The Rust firmware stays in this fork.
3. Nothing is posted without the user approving the wording.

## Future (not in v1)

- **Proxy mode:** cut pads 9/10 and route both through the XIAO (a UART to each
  side) so it is the single master. It forwards the dongle's traffic and
  interleaves its own polls (for example, live registers every 1-2 s). It needs
  a bypass for when the XIAO is down.
- Home Assistant MQTT discovery.
- Production provisioning (secure boot, flash encryption).
- Tesla charging controller (subscribes to `solark/<id>/state`).

## Open items

- Measure pad 7 (VCC) and the dongle's 12 V input under power.
- Verify register meanings against the MySolArk app.
- Confirm the XIAO ESP32S3 Plus flash and PSRAM sizes, which affect OTA
  partition layout and TLS memory.
- A power-cycle capture showed the boot sequence: a one-off read of registers
  0-29, a clock-sync write (fc16, 22-24), and a truncated frame at power loss.
  Golden tests must include this capture (scrubbed: registers ~3-7 and
  nothing from the console).
- `op:2`/`op:3` (registers 42-47) are not periodic (absent from a 900 s
  capture). If needed, capture the dongle booting (start the capture, then
  plug the dongle in). Not needed for the MVP: the decoder handles any block
  generically.

## Pre-plan research decisions (2026-10-12)

Research notes live in [`docs/research/`](../research/).

- **ESP-IDF version: v6 spike first.** The first task in the implementation
  plan is a time-boxed (~1 day) board-crate spike on ESP-IDF v6.0.3. It must
  show (1) Wi-Fi + MQTT over TLS with the external `mqtt` component and
  mbedTLS in PSRAM, (2) an on-device self-signed P-256 certificate serving one
  HTTPS page, (3) PBKDF2 through mbedTLS, timed per 10k iterations, and (4)
  two RX-only UARTs with the RX idle timeout. All pass: use v6. Any blocker:
  fall back to v5.5.5 and record why. The ESP-IDF version is set only in the
  board crate's config. Rationale: [`rust-toolchain.md`](../research/rust-toolchain.md) §1.2;
  migrating later would rewrite the mbedTLS 3→4 security FFI code.
- **XIAO chip facts (read from the board with `esptool flash-id` and
  `espefuse summary`, read-only, 2026-10-12):** ESP32-S3 (QFN56) rev v0.2,
  40 MHz crystal, **16 MB quad flash (3.3 V)**, **8 MB embedded PSRAM**
  (vendor AP_3v3). That package and size are the ESP32-S3R8, whose embedded
  PSRAM is **octal** (Espressif ordering info; inferred from the part, not
  probed), so GPIO33-37 are taken by PSRAM. USB is USB-Serial/JTAG.
  eFuses are factory-clean: no secure boot, no flash encryption, all key
  blocks unused, JTAG and download mode enabled.
- **Database writes stay server-side.** The device speaks only MQTT. A
  separate server-side subscriber (Telegraf or a small `tools/` writer next
  to Mosquitto) writes to whatever database is chosen and stores `raw/<start>`
  too, so history can be re-decoded when register meanings are corrected. Why:
  no DB credentials on a physically exposed device (flash is readable until
  eFuse lockdown), one ACL-scoped outbound connection, DB choice changes
  without reflashing.
- **Store-and-forward backfill buffer (v1, user decision: "save as much as
  possible").** Replaces "keep only the latest `state`" on broker or Wi-Fi
  loss.
  - **Record:** every paired raw block (start, count, values, timestamp) in a
    compact binary form, about 185 KB/h (about 4.4 MB/day) at the current
    schedule. `state` can be re-derived from it.
  - **Tier 1:** a PSRAM ring (default about 4 MB, about 20 h).
  - **Tier 2:** when PSRAM fills, or periodically while offline, spill to a
    dedicated flash data partition (default about 5 MB, about 24 h). It
    survives reboot and power loss. The ring layout is naturally
    wear-leveling, and flash is written only while offline. Records carry a
    CRC and sequence number, and torn writes at power loss are detected and
    skipped.
  - **Overflow:** when both tiers are full, drop the oldest data, count it,
    and report it in `health`.
  - **Replay:** on reconnect, live data goes first. Backfill is published on
    `solark/<id>/backfill/<start>` (never on `state` or `raw`, so the charging
    controller can't act on old data) at QoS 1. A record is deleted only
    after PUBACK, and replay is rate-limited.
  - **Timestamps:** wall-clock (SNTP) when known. Records made before the
    first time sync carry boot id plus monotonic time and are corrected to
    wall-clock once sync happens.
  - **Config:** enabled, PSRAM size, flash spill on/off, replay rate,
    max age, chunk size.
  - **Partition table:** the 16 MB layout needs a `backfill` data partition
    (the size is a build-time partition choice; runtime config can use less
    of it).
