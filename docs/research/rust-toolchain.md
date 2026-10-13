# Rust toolchain feasibility check (as of 2026-10-12)

Scope: the design in `docs/plans/2026-10-11-xiao-firmware-design.md` on a Seeed
XIAO ESP32S3 Plus, Rust, `esp-idf-svc` (std). Written before the implementation
plan.

**Evidence labels.** `[V]` = verified this session against a primary source (URL
given). `[K]` = from background knowledge of ESP-IDF, **not** re-verified; treat
as a hypothesis to confirm with a spike. `[E]` = my estimate; needs a benchmark.
No Rust toolchain was installed on the research machine, so nothing was
compiled; versions come from the crates.io API and GitHub raw files.

## 0. Headlines

1. **Stay on std `esp-idf-svc`.** It is the only stack with an off-the-shelf
   HTTPS server, MQTT-over-TLS, OTA and NVS. The `esp-hal` alternative is
   production-stable only for bare drivers; its Wi-Fi/TLS/OTA story is pre-1.0.
2. **The esp-idf-* repos moved.** `esp-idf-svc`, `-sys` and `-hal` are now one
   monorepo, `esp-rs/esp-idf`; the old repos are archived [V]. Pin crates.io
   versions and file issues in the monorepo.
3. **Pick ESP-IDF v5.5.5 for v1**, not v6.x. v6 is supported but moves `mqtt`
   (and some Ethernet drivers) to external components and has had churn [V].
4. **Design bug:** "Factory reset: hold BOOT at power-on" cannot work. BOOT is
   GPIO0, a strapping pin; held low at reset the chip enters the ROM download
   mode. Use "hold BOOT for N seconds after boot" (section 8, item 1).
5. **Everything that protects secrets against physical access needs eFuses**
   (NVS encryption, secure boot, flash encryption). Until the user approves a
   provisioning step, flash (including MQTT/Wi-Fi secrets and the TLS private
   key) is readable by anyone with USB access. State this in the design.
6. **PBKDF2 at OWASP-class iteration counts is too slow on this chip** (section
   7). Use roughly 20k-50k iterations plus lockout, and put the KDF behind the
   `Crypto` trait so the board can use mbedTLS.

## 1. Pinned versions

| Item | Version | Date | Source |
|---|---|---|---|
| `esp-idf-svc` | 0.53.0 | 2026-09-15 (crate) / changelog 2026-09-25 | crates.io API; https://github.com/esp-rs/esp-idf (`esp-idf-svc/CHANGELOG.md`) |
| `esp-idf-hal` | 0.47.0 | 2026-09-15 | crates.io API |
| `esp-idf-sys` | 0.38.1 | 2026-09-16 | crates.io API; `esp-idf-sys/CHANGELOG.md` |
| `embuild` | 0.33.5 | 2026-09-07 | crates.io API |
| `espup` | 0.18.0 | 2026-09-30 | crates.io API; https://github.com/esp-rs/espup |
| Rust `esp` toolchain (rust-build) | 1.99.0.0 | 2026-09-30 | https://github.com/esp-rs/rust-build/releases |
| ESP-IDF supported by template | v5.3.6, v5.4.4, v5.5.5, v6.0.3, v6.1 | n/a | https://github.com/esp-rs/esp-idf-template README |
| **ESP-IDF to use** | **v5.5.5** (revisit v6.0.3 after v1) | n/a | judgement, see section 1.2 |
| `esp-hal` (not used) | 1.2.2 | 2026-09-18 | crates.io API |
| `esp-radio` (not used) | 0.18.0 (pre-1.0) | 2026-09-17 | crates.io API |
| `ed25519-dalek` | 3.0.0 | 2026-07-06 | crates.io API |
| `ed25519-compact` | 2.6.0 | 2026-09-25 | crates.io API |
| `pbkdf2` | 0.13.0 | 2026-04-21 | crates.io API |
| `subtle` | 2.6.1 | 2024-06-24 | crates.io API |
| `serde-json-core` | 0.7.0 | 2026-10-08 | crates.io API |
| `rumqttc` | 0.25.1 | 2025-11-21 (stale ~11 months) | crates.io API |
| `axum` | 0.8.9 | 2026-04-14 | crates.io API |
| `rustls` | 0.23.45 | 2026-09-14 | crates.io API |
| `cargo-llvm-cov` | 0.9.1 | 2026-09-06 | crates.io API |
| `cargo-deny` | 0.20.2 | 2026-07-09 | crates.io API |
| `cargo-audit` | 0.22.2 | 2026-06-05 | crates.io API |
| `esp-rs/xtensa-toolchain` (GH Action) | v1.7.0 | 2026-04-20 | GitHub releases API |

Pin policy: exact versions in `Cargo.toml` for the three `esp-idf-*` crates
(they release in lockstep and break `MqttClientConfiguration`/server config
structs between minors; the 0.53.0 changelog lists several breaking additions),
`ESP_IDF_VERSION = "v5.5.5"` in the board's `.cargo/config.toml`, and
`espup install --toolchain-version 1.99.0.0` (the bare `esp` channel does not
pin the compiler).

### 1.1 Health of the esp-rs std crates

- Monorepo `esp-rs/esp-idf` is active (pushed 2026-09-19, crates released
  2026-09-15/16) and its CI builds `xtensa-esp32s3-espidf` against ESP-IDF
  v5.x and v6.x [V] (https://github.com/esp-rs/esp-idf `.github/workflows/ci.yml`).
- The README states the crates are "a community effort": Espressif "puts little
  to no paid developer time in these", they "might be a bit lagging behind the
  latest stable ESP-IDF", and "are (currently) missing HIL tests" [V]. Espressif
  points people to `esp-hal`, which is "`no_std`-only, does not use ESP-IDF and
  requires async programming" [V]. Risk: bus factor and slow fixes. Mitigation:
  our HAL traits isolate the dependency (this is exactly what the design does).
- `esp-idf-sys` still needs `ldproxy`, `espup` (Xtensa needs the forked `esp`
  Rust toolchain; stable/nightly cannot target Xtensa) and `build-std` [V]
  (https://github.com/esp-rs/esp-idf-template `cargo/.cargo/config.toml`).

### 1.2 Why ESP-IDF v5.5.5 rather than v6.x

`esp-idf-svc` 0.53.0 changelog [V]: "in ESP-IDF V6.0, some drivers have been
moved to external components (`mqtt`, ethernet PHY/SPI drivers). If the code
fails to build, you may need to enable extra components". Our v1 needs `mqtt`,
`esp_https_server`, OTA; v5.5.5 is the newest line the template lists as plain
"Stable" without extra component wiring, and v6 also changes the mbedTLS major
version and the UART pin API (`_uart_set_pin6` in esp-idf-hal [V]). Revisit v6
once v1 works; the HAL traits make that a board-crate change.

### 1.3 std esp-idf-svc vs `esp-hal` + embassy

| Need | `esp-idf-svc` (std) | `esp-hal` 1.x + `esp-radio` + embassy |
|---|---|---|
| HTTPS server | `EspHttpServer` over `esp_https_server` (mbedTLS) with `server_certificate` / `private_key` config [V] | none official; roll your own over `embedded-tls`/`esp-mbedtls` (TLS server support limited) |
| MQTT over TLS | `EspMqttClient` (esp-mqtt) with `server_certificate`, `client_certificate`, `crt_bundle_attach`, `skip_cert_common_name_check` [V] | `rust-mqtt`/`minimq` plus `embedded-tls` (TLS 1.3 only) |
| OTA | `EspOta` / `EspOtaUpdate` (`write`, `finish`, `activate`, `abort`), `mark_running_slot_valid`, `mark_running_slot_invalid_and_reboot` [V] | `esp-hal-ota` 0.6.0 (community, pre-1.0) |
| NVS | `EspNvs` (IDF NVS, wear-levelled, encryptable) | `esp-storage` 0.10 + `sequential-storage`; no NVS-encryption |
| Maturity | built on IDF, which is Espressif's tested stack | `esp-hal` 1.x is stable only for a subset; many APIs `unstable`; `esp-radio` is 0.x |

**Recommendation: keep esp-idf-svc.** Revisit only if Espressif or the
community ships a stable HTTPS server and an NVS-compatible store on `esp-hal`.
The sans-IO core/HAL split keeps that door open.

## 2. UART findings (answers to question 2)

All checked against `esp-idf-hal/src/uart.rs` on the monorepo master and the
ESP-IDF UART docs (https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/uart.html).

- **RX-only drivers: supported.** `UartRxDriver::new` exists and `new_common`
  passes `-1` for any absent pin [V]. `UartDriver::new` itself requires a TX pin
  argument, so use `UartRxDriver` (never `UartDriver`) so that no TX pin is ever
  claimed. The ESP32-S3 has three UARTs; use UART1 and UART2. Put the console on
  USB-Serial-JTAG (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`) so UART0 is not
  needed, and GPIO matrix routing allows any pin [K].
- **Hardware idle timeout (TOUT): supported.** `EventConfig.receive_timeout:
  Option<u8>` maps to `rx_timeout_thresh` and enables the RX-FIFO-timeout
  interrupt [V]. ESP-IDF docs: `uart_set_rx_timeout` max is 126, 0 disables
  [V]. **Unit ambiguity:** the header says "unit: time of sending one byte" and
  the docs page says "symbol periods"; I could not settle which. Verify against
  a Saleae capture in the first spike: 3.5 character times at 9600 8N1 is about
  3.65 ms, so granularity matters. The "derived from baud" default needs a
  tested conversion function.
- **Event-driven receive: yes.** `Config.queue_size > 0` creates the driver
  event queue; `UartRxDriver` exposes `event_queue()`, with events `Data {size,
  timeout}`, `FrameError`, `ParityError`, `RxFifoOverflow`, `RxBufferFull`,
  `Break`, `PatternDetected` [V]. An `AsyncUartDriver` exists as well [V].
  Important behaviour: `UART_DATA` events fire both on FIFO-full (partial
  chunk) and on timeout (`timeout=true`); per the ESP-IDF docs, if the event came
  from a FIFO-full interrupt, no timeout-flagged event fires until the next byte
  arrives [V]. So the framer must **accumulate chunks until a `timeout=true`
  event** and treat that as the idle marker.
- **Timestamps.** The IDF driver ISR pushes the event to a FreeRTOS queue; we
  timestamp when our task dequeues it (`esp_timer_get_time()`, 1 us
  resolution). Real accuracy is task-scheduling jitter: tens of microseconds if
  the reader task has high priority and nothing blocks, up to a few ms when
  Wi-Fi/TLS work runs [E]. A frame's *end* time is therefore "idle detected +
  jitter", and request/reply ordering across the two UARTs is only reliable if
  the inverter turnaround time exceeds that jitter. **Do not rely on sub-ms
  cross-line ordering.** Pair on address + function + byte-count and accept
  either arrival order within the reply timeout (a reply seen first stays
  pending for a short grace window). Run both readers at a high, equal task
  priority.
- **Trait consequence:** `SerialRx` should deliver `Chunk(bytes, t)` and
  `IdleGap(t)` events, not whole frames. The sans-IO framer then works
  identically with hardware idle (ESP), IDLE-line interrupts (embassy) and
  timestamp-gap detection (host replay).
- **RX glitch filter.** ESP-IDF's `uart_config_t` has `rx_glitch_filt_thresh`
  (nanoseconds, 0 = off) [V, master branch]; `uart.c` rejects it on chips
  where `UART_LL_GLITCH_FILT_ONLY_ON_AUTOBAUD` is set [V]. I did not confirm
  that the S3 accepts it, nor the first IDF release containing it (check it
  exists in v5.5.5 in the spike). `esp-idf-hal`'s `Config` has no field for it
  (grep found none), so it needs a raw `uart_param_config`/`sys` call in the
  board crate (allowed `unsafe`; core crates stay `forbid(unsafe_code)`).
  Make it an optional `SerialRx` capability.
- **Autobaud.** ESP-IDF exposes `uart_detect_bitrate_start()` /
  `uart_detect_bitrate_stop()`; docs recommend alternating-bit data (0x55/0xAA)
  and a measurement window of at least one byte [V]. It is not wrapped by
  `esp-idf-hal` (raw `sys` call in the board crate). Whether it can run while the
  RX driver is installed on the same port is unverified [K: it likely needs the
  driver uninstalled or reconfigured]. Treat "autobaud on framing failure" as a
  **moderately risky** feature: a bootloader-mode baud change is not guaranteed
  to start with an alternating-bit byte. Put it behind `SerialRx::measure_baud()
  -> Option<u32>` and defer if the spike is awkward.

## 3. Memory: HTTPS server + MQTT TLS + OTA (question 3)

Facts that are verified: ESP-IDF mbedTLS docs give a ~42 KB heap cost per TLS
connection with defaults, falling to ~22 KB with `CONFIG_MBEDTLS_DYNAMIC_BUFFER`
(+ free-config-data/free-CA-cert options) [V]
(https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/protocols/mbedtls.html;
figures are from the `https_request` example and "subject to change").
`CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC` ("External SPIRAM") exists as one choice of
the mbedTLS allocation-mode menu and `depends on SPIRAM_USE_CAPS_ALLOC ||
SPIRAM_USE_MALLOC` [V] (release/v5.5 `components/mbedtls/Kconfig`).

Budget (S3 has about 512 KB SRAM, roughly 300-350 KB free heap after Wi-Fi and
LWIP) [E]:

| Consumer | Internal RAM, defaults | Notes |
|---|---|---|
| Wi-Fi + LWIP + system | ~100-150 KB | Wi-Fi buffers must stay internal [K] |
| HTTPS server, per TLS session | ~40 KB (22 KB with dynamic buffers) | `max_open_sockets` caps it |
| MQTT TLS (1 session) | ~40 KB | long-lived |
| OTA over HTTPS upload | one TLS session + one 4 KB write buffer | same session as the HTTP POST |
| Rust: framing buffers, register store, ring buffer for the recorder | few KB; ring buffer in PSRAM | allocate once at boot |

**Recommendation.** Use the PSRAM: set `CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC=y`,
enable dynamic buffers, and cap concurrency. The XIAO ESP32S3 Plus has 16 MB flash
and 8 MB PSRAM [V] (https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/;
the page does not say octal vs quad; the S3R8 part is octal [K]. Confirm with
`esptool.py flash_id` and `idf.py` boot log, then match `CONFIG_SPIRAM_MODE_OCT`).
Cautions [K]:
- Keep **task stacks and anything touched during flash writes in internal RAM**.
  During OTA/NVS writes the flash cache is disabled; code/data in PSRAM that is
  needed by ISRs or by tasks flagged `IRAM_ATTR` must not be on external RAM.
  Do not enable `SPIRAM_ALLOW_STACK_EXTERNAL_MEMORY`.
- Hardware AES/SHA with PSRAM buffers works (the driver bounces/aligns) but
  costs throughput; irrelevant at our data rates.
- `esp-idf-svc`'s HTTP server `stack_size` default is 6144 [V]; the IDF's own
  `HTTPD_SSL_CONFIG_DEFAULT` uses 10240 [K]. TLS handshake with ECDSA needs more
  than 6 KB. Set 10-12 KB explicitly.
- Concurrency limits: `max_open_sockets = 2` (or 3), `lru_purge_enable = true`
  [fields exist: V], so a hostile LAN device holding sockets cannot starve the
  UI or the MQTT socket. Set `CONFIG_LWIP_MAX_SOCKETS` sensibly (default 10, the
  HTTP server reserves 3 of them) [K].
- No specific "HTTPS server and MQTT TLS simultaneously" bug was found in the
  sources I read; the practical failure mode is heap exhaustion at the second
  handshake. Test with `heap_caps_get_free_size` / minimum-ever-free exposed in the
  `health` topic (the design already reports free heap; add *minimum* free heap).
- **Time for certificate validation.** mbedTLS checks certificate validity
  dates. With no RTC the clock reads 1970 until SNTP syncs, so MQTT-TLS and any
  pinned certificate with `notBefore` set fail until then [K]. The firmware must
  run SNTP first and gate the MQTT connect on a valid clock (or the user
  chooses `CONFIG_MBEDTLS_HAVE_TIME_DATE=n`-style relaxed checking, which is a
  security trade-off). Add an `Sntp` capability and an NTP server setting.
- **Self-signed certificate generation on device** needs mbedTLS pk/x509
  *write* APIs reachable from Rust (via `esp-idf-sys` bindings plus unsafe in the
  board crate). Their sdkconfig availability is unverified. Use **ECDSA P-256**,
  not RSA-2048: RSA key generation on the S3 takes many seconds [E]. Fallback if
  it is painful: have the first-boot flow accept an uploaded cert/key over
  USB-provisioning (the design already allows uploads).

## 4. OTA, signing, rollback, partitions (question 4)

### 4.1 API shape [V] (`esp-idf-svc/src/ota.rs`)

`EspOta::new()`, `initiate_update()` / `initiate_update_with_known_size(n)` ->
`EspOtaUpdate { write(&[u8]), flush(), finish() -> EspOtaUpdateFinished,
complete(), abort() }`, then `EspOtaUpdateFinished::activate()` (sets the boot
partition). Slot queries: `get_running_slot`, `get_boot_slot`, `get_update_slot`,
`get_last_invalid_slot`; `mark_running_slot_valid()`;
`mark_running_slot_invalid_and_reboot()`; `factory_reset()`. The
`finish()`/`activate()` split is exactly the hook needed to verify *before*
switching.

### 4.2 Signature scheme: ESP-IDF native vs our ed25519

ESP-IDF "signed apps without hardware secure boot"
(https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/security/secure-boot-v2.html) [V]:
- RSA-PSS, RSA-3072 keys ("App Signing Scheme" must be RSA); the page does not
  mention ECDSA for the S3 [V as far as the page goes].
- The public key is read from the *running app's* signature block; a new image is
  checked against it. The running app's signature is not verified on boot [V].
  It "does not provide protection against an attacker with write access to
  flash" and only one key (the first) is used [V]; key revocation is only
  available with real secure boot [V].
- Anti-rollback by eFuse (`secure_version`) is the ESP-IDF mechanism and burns an
  eFuse [K]. Do not use it.

**Recommendation: use our own app-level ed25519, over a signed manifest.**
Reasons: matches the existing `Crypto`/`Ota` trait design; native verification
is RSA-only, ties the trust anchor to a signature block baked into the running
image, and gives no portability. Cost: more code to get right. Design:

1. Upload carries `manifest` + `image`. Manifest (fixed binary or canonical
   JSON): `{board, version, counter, size, sha256, min_compatible_config}`,
   ed25519-signed (signature over the manifest bytes, not the whole image, so
   verification is cheap and independent of image size).
2. Verify the manifest signature first; check `board`, `counter >= stored`,
   `size` fits the slot.
3. Stream the image into `EspOtaUpdate::write` while computing SHA-256; at the
   end compare with `manifest.sha256`; only then `finish()` -> `activate()`.
   On any mismatch `abort()`.
4. The trust anchor (ed25519 public key) lives **in the firmware image** (a
   compile-time constant), so a compromised admin session cannot install a new
   anchor. Interpretation of standing rule 2 needed: this is a deliberate
   exception (a trust anchor, like a CRC polynomial, is a security constant).
   Key rotation = a new firmware release signed with the old key that embeds the
   new one. **Decision for the user.**
5. Optionally also enable ESP-IDF native signed-app verification as a second
   layer; it is cheap (build option) but adds an RSA key to manage. I would
   skip it in v1.

Both schemes are software-only: an attacker with physical flash write access
defeats either, because the bootloader does not verify. Only Secure Boot v2
(eFuses) changes that. Say so explicitly in the design.

### 4.3 Rollback

`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y` (bootloader marks a newly written
image `PENDING_VERIFY`; if it resets before `mark_running_slot_valid()`, the
bootloader falls back) [K, standard IDF feature]. Call
`mark_running_slot_valid()` only after the design's health gate (Wi-Fi, MQTT, one
paired frame). `mark_running_slot_invalid_and_reboot()` for explicit failure
[V API]. A crash loop before the gate also rolls back because a reset while
pending counts as failure [K].

### 4.4 Anti-rollback without eFuses

Store `min_counter` in NVS. Commit it (raise it to the new image's counter)
**only when the new image calls `mark_running_slot_valid()`**; raising it at
upload time would block recovery if the new image fails to boot. Limit: an
attacker with flash access can reset NVS, and a downgrade through the *network
path* is blocked only because the old signed manifest has a lower counter.
Document this as best-effort.

### 4.5 NVS encryption without eFuses [V]
(https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/storage/nvs_encryption.html)

- Flash-encryption scheme: keys in the `nvs_keys` partition, "protected by
  Flash Encryption"; flash encryption is a prerequisite. That burns eFuses.
- HMAC scheme: keys derived at runtime from an HMAC key in an eFuse key block
  (`ESP_EFUSE_KEY_PURPOSE_HMAC_UP`); generated and burned automatically if absent.
  It does work "without enabling flash encryption" but **burns an eFuse key
  block, irreversibly.**

Both need explicit user approval (CLAUDE.md rule 4). **v1 therefore ships with
plaintext NVS.** Mitigate: store only the PBKDF2 hash for the admin password
(already planned); generate a per-device MQTT credential that the broker ACL
confines to `solark/<id>/#`; keep the self-signed TLS key non-exportable by the
UI. Also note USB-Serial-JTAG is enabled by default on the S3, so physical
access to the USB port allows flash read-out. The "physical access at the
inverter" threat is only addressed by the deferred production-provisioning step.
Do not create `nvs_keys` in the v1 table (an unused key partition suggests
protection that does not exist); add it in the provisioning plan.

### 4.6 Partition table (16 MB flash)

Proposed `partitions.csv` (two 3 MB OTA slots; Rust+TLS+HTTPS+MQTT images are
typically 1.5-2.5 MB [E]; confirm with a first build):

```
# Name,     Type, SubType, Offset,   Size,     Flags
nvs,        data, nvs,     0x9000,   0x10000,
otadata,    data, ota,     0x19000,  0x2000,
phy_init,   data, phy,     0x1B000,  0x1000,
coredump,   data, coredump,0x1C000,  0x10000,
factory,    app,  factory, 0x30000,  0x300000,
ota_0,      app,  ota_0,   0x330000, 0x300000,
ota_1,      app,  ota_1,   0x630000, 0x300000,
storage,    data, spiffs,  0x930000, 0x200000,
# remainder (~5.9 MB) reserved: recorder dump, future nvs_keys, larger images
```

Notes: `nvs` 64 KB is plenty for config + keys; the 16 MB flash allows keeping
`factory` as a known-good recovery image (needed so rollback has a target after
the first ever OTA). If `factory` is dropped the first image lives in `ota_0`.
`storage` is optional; the design embeds the web UI in the binary, so drop it
unless raw-capture spooling to flash is wanted. Add `nvs_keys` (4 KB, `encrypted`)
only in the eFuse provisioning plan.

## 5. Workspace layout, tooling and CI (question 5)

### 5.1 Known-good patterns and real repos

- `esp-rs/esp-idf` (the monorepo) is one Cargo workspace whose CI clippy-checks
  `--workspace` for `xtensa-esp32s3-espidf` with `-Zbuild-std=std,panic_abort`,
  installs the toolchain via `espup install --targets esp32,esp32s2,esp32s3`,
  uses `RUSTFLAGS="--cfg espidf_time64"`, and installs `ldproxy` [V]
  (https://github.com/esp-rs/esp-idf/blob/master/.github/workflows/ci.yml). Its
  comment notes that downloads in `esp-rs/xtensa-toolchain` and similar actions
  are flaky and are retried by hand [V].
- `esp-rs/esp-idf-template` (`cargo/`): `.cargo/config.toml` with `[build]
  target`, `[unstable] build-std = ["std","panic_abort"]`, `linker = "ldproxy"`,
  `runner = "espflash flash --monitor"`, `[env] MCU, ESP_IDF_VERSION`, plus
  `rust-toolchain.toml` and `sdkconfig.defaults` [V]
  (https://github.com/esp-rs/esp-idf-template).
- `ivmarkov/ruwm` (stale since 2024-05, but the pattern is exactly ours): a
  workspace of `ruwm` (portable core) + `ruwm-esp32` as members with the
  web/sim crates in `exclude` [V] (https://github.com/ivmarkov/ruwm).
- GitHub Action: `esp-rs/xtensa-toolchain` v1.7.0 (2026-04-20) [V].

### 5.2 Recommended structure

Cargo resolves `.cargo/config.toml` and `rust-toolchain.toml` by the **current
directory**, not by the package being built, and a root `[build] target` would
leak into host crates. Therefore:

- **Root workspace = host-testable crates only** (stable toolchain, no
  `build-std`): `solark-modbus`, `solark-core`, `solark-hal`, `solark-app`,
  `solark-webui`, `boards/host`.
- **Board crate = its own workspace root** with path dependencies on the core
  crates, its own `rust-toolchain.toml` (`channel = "esp"`), its own
  `.cargo/config.toml` and `Cargo.lock`. List it in the root workspace's
  `exclude`. Build from within `boards/xiao-esp32s3/`.
- Share lint policy via `[workspace.lints]` in the root and repeat the table in
  the board's manifest (a path crate cannot inherit from a workspace it is not
  in). Alternatively keep the board in the root workspace with `default-members`
  excluding it, but then one `cargo` invocation at the root picks up one set of
  config; I do not recommend it. Known costs of the split: two lockfiles, so
  `cargo-deny`/`cargo-audit` run twice.
- Core crates: `#![cfg_attr(not(test), no_std)]` plus `#![forbid(unsafe_code)]`
  so that `cargo test` and `cargo llvm-cov` run natively on the host.
- `embuild` quirk: if `CARGO_TARGET_DIR` is relocated, set `CARGO_WORKSPACE_DIR`
  (template comment) [V].

```
SolArk_Live_Data/
  Cargo.toml                 # [workspace] members = crates/*, boards/host ; exclude = boards/xiao-esp32s3
  rust-toolchain.toml        # channel = "stable" (pin exact, e.g. 1.9x)
  deny.toml  clippy.toml  rustfmt.toml
  Makefile                   # check, check-host, check-esp, coverage, audit
  crates/
    solark-modbus/  solark-core/  solark-hal/  solark-app/  solark-webui/
  boards/
    host/                    # Linux: replay serial, rumqttc, axum+rustls
    xiao-esp32s3/            # NOT in root workspace
      Cargo.toml             # [workspace] (own root), path deps on ../../crates/*
      Cargo.lock
      rust-toolchain.toml    # channel = "esp"
      .cargo/config.toml     # target xtensa-esp32s3-espidf, build-std, ldproxy, ESP_IDF_VERSION=v5.5.5, MCU=esp32s3
      sdkconfig.defaults
      partitions.csv
      build.rs               # embuild::espidf::sysenv::output()
      src/
  docs/  tools/  .github/workflows/{host.yml,esp.yml}
```

### 5.3 Tooling

- `cargo test --workspace` and `cargo clippy --workspace --all-targets -- -D
  warnings` at the root; `cargo clippy -Zbuild-std=std,panic_abort --target
  xtensa-esp32s3-espidf -- -D warnings` in the board dir (this is what upstream
  CI does) [V].
- Coverage: `cargo llvm-cov --workspace --exclude host-board --fail-under-lines
  80` (stable, host) on the core crates. Exclude `boards/*` from the gate; gate
  `solark-hal` only if it contains logic. Remember `solark-app` is generic over the
  traits and needs fake HAL implementations in tests.
- `cargo deny check` and `cargo audit` in the root *and* in
  `boards/xiao-esp32s3` (separate lockfiles). They do **not** see ESP-IDF itself
  (a C tree cloned by `esp-idf-sys` at build time) or IDF managed components:
  pin `ESP_IDF_VERSION` to a tag and record its commit; watch Espressif security
  advisories manually.
- CI: `host.yml` (stable; fmt, clippy, test, llvm-cov, deny, audit, ruff, mypy,
  pytest) on every push; `esp.yml` (espup 0.18.0 with a pinned `--toolchain-version`
  or `esp-rs/xtensa-toolchain@v1.7.0`, `cargo install ldproxy espflash`, cache
  `~/.cargo`, `boards/xiao-esp32s3/.embuild` and `target`) builds the image,
  runs clippy and uploads the `.bin` as an artifact. The first cold build
  compiles ESP-IDF and takes a long time; cache it. Retry the toolchain download
  as upstream does [V].

## 6. Crypto and web crates for the no_std core (question 6)

| Need | Recommendation | Notes |
|---|---|---|
| ed25519 verify | `ed25519-dalek` 3.0.0 (`default-features=false`, no `batch`) | `no_std`, and `forbid(unsafe_code)` unless the `batch`/test cfg is on [V: `src/lib.rs`]. Dependencies (curve25519-dalek) contain their own unsafe in some backends; our crate's `forbid` only covers our code. Alternative `ed25519-compact` 2.6.0: smaller, `no_std`-friendly, no explicit `forbid` found [V grep]. Dalek is the better-reviewed choice; verification cost on a 240 MHz LX7 is likely tens of ms [E]. |
| PBKDF2 | `pbkdf2` 0.13.0 (RustCrypto, `#![no_std]` [V]) plus `hmac`/`sha2` | Software only. See section 7. Core calls only the `Crypto` trait. |
| Constant-time compare | `subtle` 2.6.1 (`ConstantTimeEq`) | Stable, widely used, last release 2024. Uses volatile reads internally. |
| Random (CSRF token, salts) | `Crypto::fill_random(&mut [u8])` trait method | Board: `esp_fill_random`. The ESP32 RNG is only a true RNG while the RF subsystem is active (or bootloader_random is enabled) [K]; fine with Wi-Fi on, but do not generate the long-term TLS key before Wi-Fi starts. Host: OS RNG. |
| SHA-256 (image hash, HMAC) | via `Crypto::sha256_*` | Board: mbedTLS with hardware acceleration; host: `sha2`. |
| JSON | `serde` + `serde_json` with `alloc` (no std) | `serde-json-core` 0.7.0 is heapless but cannot represent dynamic documents; our config import/export, register-map editing and MQTT payloads are shaped by user data. We have PSRAM, so use alloc, enforce body-size limits before parsing, and cap nesting depth. |
| MQTT (host board) | `rumqttc` 0.25.1 | Works, but the last release is about 11 months old [V]; check issue activity before depending on TLS features. Fallback: `paho-mqtt`. |
| HTTPS (host board) | `axum` 0.8.9 + `axum-server`/`tokio-rustls` + `rustls` 0.23.45 | Host TLS (rustls) behaves differently from the device's mbedTLS: integration tests prove application logic only, not TLS config. |

`forbid(unsafe_code)` compatibility: fine for all of the above as dependencies.
The audit status of `ed25519-dalek`/RustCrypto `pbkdf2` is "widely reviewed,
no formal commissioned audit confirmed in this session"; I did not verify
audits, so do not claim it in documentation.

## 7. PBKDF2 cost on the ESP32-S3 (question 7)

All figures are **estimates [E]; benchmark in the first spike.**

PBKDF2-HMAC-SHA256 costs two SHA-256 compressions per iteration when the HMAC
inner/outer states are precomputed (RustCrypto does this). Software SHA-256 on
the Xtensa LX7 (no SHA instructions, 32-bit core) is roughly 2,500-4,000 cycles
per 64-byte block, so about 10-17 us per compression at 240 MHz, i.e.
**roughly 2-3.5 s per 100,000 iterations** pure Rust. That is 15-20 s at the
OWASP 600,000 figure, which blocks the single HTTP worker, trips watchdogs if the
task does not yield, and makes login a CPU-exhaustion vector.

The ESP32-S3 SHA peripheral (via mbedTLS `CONFIG_MBEDTLS_HARDWARE_SHA`, which
ESP-IDF recommends enabling) is faster in bulk but has per-call lock/setup
overhead; for two tiny blocks per iteration it may be only about 2-4x faster
rather than ten times, and it does not help pure-Rust crates at all [E].

Implications:
- Put the KDF in `Crypto::pbkdf2_hmac_sha256(password, salt, iterations, out)`;
  the ESP board implements it with `mbedtls_pkcs5_pbkdf2_hmac*` (available in
  mbedTLS 3.x; the v6 mbedTLS-4 migration changes the headers [K]) or an
  IDF hardware-backed HMAC loop; host and tests use the `pbkdf2` crate. Add a
  conformance test with fixed RFC 7914/6070-style vectors so both agree.
- Default iterations 20k-50k (about 0.4-1.5 s), stored per hash so it can be
  raised later; keep it configurable (rule 2) with a validated minimum and an
  upper bound that prevents an admin from bricking login.
- Run login hashing in a dedicated task with its own stack and a global "one
  hash at a time" semaphore; reject during lockout *before* hashing; apply the
  backoff before the KDF.
- Consider storing a time-boxed session token so the KDF runs only at login and
  password change.

## 8. Infeasible, risky, or harder than it looks

| # | Item in the design | Problem | Suggested change |
|---|---|---|---|
| 1 | "Factory reset: hold BOOT at power-on" | BOOT is GPIO0, a strapping pin; low at reset enters ROM download mode [K, standard ESP32 behaviour; confirm on the board]. | Poll BOOT after boot (e.g. hold 10 s while running, hold time configurable). Same for "setup AP after a physical BOOT press". |
| 2 | `SerialRx` yields frames | Hardware idle fires only after the FIFO is drained, and chunks arrive first; TOUT unit and max (126) uncertain [V/ambiguity]. | `SerialRx` yields `Chunk`/`IdleGap` events with µs timestamps; the framer is in `solark-modbus`. Spike: conversion from 3.5 chars to the TOUT value, verified on a Saleae capture. |
| 3 | Cross-line ordering by timestamp | Task-scheduling jitter can exceed the request-to-reply turnaround. | Pair without relying on sub-ms ordering; allow reply-before-request within a grace window; high equal priority reader tasks. |
| 4 | RX glitch filter and autobaud as config options | Not exposed by `esp-idf-hal`; filter unconfirmed on the S3 and in v5.5.5; autobaud needs raw `sys` calls and driver coexistence is unverified. | Make both optional trait capabilities, implemented in the board crate; do not make recorder behaviour depend on autobaud. |
| 5 | Physical-access threat vs plaintext NVS | NVS encryption and secure boot all need eFuses; USB-JTAG allows flash dump. | State the v1 limitation in the design; keep secrets minimal; revisit in the provisioning plan with explicit approval. |
| 6 | PBKDF2 "configurable iterations" at strong settings | 100k iterations is roughly 2-3.5 s on the S3 software path [E]. | Section 7: mbedTLS-backed `Crypto`, 20-50k default, lockout before hashing. |
| 7 | MQTT/HTTPS "certificate pinning" | esp-mqtt exposes `server_certificate` (trusts that PEM), not a fingerprint pin [V]; fingerprint pins need custom verify hooks. | Define pin = trust only the configured CA/self-signed cert PEM. Add SNTP and gate TLS on a valid clock. |
| 8 | On-device self-signed cert | Needs mbedTLS x509/pk write APIs; RSA keygen is very slow. | ECDSA P-256; spike the FFI; fall back to uploaded cert. |
| 9 | Trust anchor "no static values" | Public key must not be runtime-configurable or an admin compromise installs firmware. | Compile-time anchor; key rotation via a release signed by the old key. User decision. |
| 10 | Anti-rollback "counter" | NVS counter is resettable by flash access; committing too early blocks recovery. | Commit on `mark_valid`; document best-effort. |
| 11 | Concurrent TLS memory | ~40 KB per session internal RAM by default [V]; hostile LAN sockets. | PSRAM mbedTLS, dynamic buffers, `max_open_sockets` 2-3, `lru_purge_enable`, 10 KB+ httpd stack; track minimum free heap. |
| 12 | Cookie/CSRF headers | `CONFIG_HTTPD_MAX_REQ_HDR_LEN` default is small (512) [K]. | Raise to 1024-2048, raise `HTTPD_MAX_URI_LEN` only if needed; test `Secure; HttpOnly; SameSite=Strict`. |
| 13 | Capture streaming over MQTT | esp-mqtt `buffer_size`/`out_buffer_size` default to 0 in the svc config (use IDF defaults of 1024) [V]; large chunks fail silently. | Chunk size must be ≤ out buffer minus topic/header; make it a validated config limit; use QoS 0 or 1 with back-pressure and no backlog. |
| 14 | Recorder pre-allocated ring buffer | Large buffers in PSRAM are fine, but anything read in ISR context is not. | Ring buffer lives in PSRAM and is written from the reader task only. |
| 15 | Host vs device parity | rustls/axum/rumqttc on the host differ from mbedTLS/esp-mqtt. | Treat host integration tests as logic tests; add a hardware TLS checklist item (already in section 7.4 of the design). |
| 16 | CI cost | First ESP-IDF build is very slow; the upstream CI hand-retries toolchain downloads. | Cache `.embuild`, `target`, `~/.cargo`; run the esp job only on changes under `boards/xiao-esp32s3`, `crates/**` and nightly. |
| 17 | Supply chain | `cargo-audit`/`cargo-deny` do not cover ESP-IDF C code. | Pin the IDF tag; periodic manual advisory check. |
| 18 | Maintenance risk of `esp-idf-*` | Community-run; repos recently consolidated. | Keep the HAL boundary; pin versions; track `esp-rs/esp-idf` releases. |

## 9. `sdkconfig.defaults` (board crate)

Starting point; keys marked `[K]` were not re-verified for v5.5.5 and a build
will report any that do not exist.

```
# --- Rust/std task stacks (from esp-idf-template) [V]
CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192
CONFIG_ESP_SYSTEM_EVENT_TASK_STACK_SIZE=4096
CONFIG_FREERTOS_IDLE_TASK_STACKSIZE=4096
CONFIG_PTHREAD_TASK_STACK_SIZE_DEFAULT=4096

# --- Flash / PSRAM (XIAO ESP32S3 Plus: 16 MB flash, 8 MB PSRAM) [K]
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_ESPTOOLPY_FLASHMODE_QIO=y
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y          # confirm octal on the board
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_SPIRAM_USE_MALLOC=y
CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=4096   # small allocs stay internal
# do NOT set SPIRAM_ALLOW_STACK_EXTERNAL_MEMORY

# --- Console on native USB, UART0 stays free [K]
CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y

# --- mbedTLS memory [V: option names exist in v5.5 Kconfig]
CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC=y
CONFIG_MBEDTLS_DYNAMIC_BUFFER=y
CONFIG_MBEDTLS_DYNAMIC_FREE_CONFIG_DATA=y
CONFIG_MBEDTLS_DYNAMIC_FREE_CA_CERT=y
CONFIG_MBEDTLS_HARDWARE_SHA=y
CONFIG_MBEDTLS_HARDWARE_AES=y
CONFIG_MBEDTLS_HARDWARE_MPI=y     # [K]
# CONFIG_MBEDTLS_ASYMMETRIC_CONTENT_LEN=y  # only if the broker/browsers negotiate small fragments; leave off first

# --- HTTPS server [V: ESP_HTTPS_SERVER_ENABLE exists]
CONFIG_ESP_HTTPS_SERVER_ENABLE=y
CONFIG_HTTPD_MAX_REQ_HDR_LEN=1536   # [K] cookie + CSRF + CSP-era headers
CONFIG_LWIP_MAX_SOCKETS=12          # [K]

# --- OTA / rollback [K]
CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y
# Do NOT enable BOOTLOADER_APP_ANTI_ROLLBACK (eFuse), SECURE_BOOT*, or FLASH_ENCRYPTION*

# --- MQTT (IDF v5.x built-in; v6 needs the extra component)
CONFIG_MQTT_PROTOCOL_311=y
# CONFIG_MQTT_PROTOCOL_5 is optional (svc 0.53 supports it)

# --- Robustness [K]
CONFIG_ESP_TASK_WDT_EN=y
CONFIG_ESP_TASK_WDT_TIMEOUT_S=10
CONFIG_ESP_INT_WDT=y
CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH=y    # matches the coredump partition
CONFIG_LOG_DEFAULT_LEVEL_INFO=y
```

Board-crate Rust-side runtime settings (not Kconfig): `max_open_sockets`,
`lru_purge_enable`, httpd `stack_size` >= 10240, MQTT `buffer_size` and
`out_buffer_size` explicit.

## 10. Spikes to run before the plan is final

1. **UART spike (1 day):** two `UartRxDriver`s fed from a bench signal source
   (or a replayed Saleae pattern); measure TOUT unit, idle accuracy, event
   chunking at 100-register replies, event-to-timestamp jitter with Wi-Fi + TLS
   load; test `rx_glitch_filt_thresh` and `uart_detect_bitrate_start` on the S3.
2. **TLS memory spike:** HTTPS server + MQTT TLS + upload of a 2 MB image at once; read
   minimum-ever free heap with and without PSRAM mbedTLS.
3. **Crypto benchmark:** PBKDF2 (pure Rust vs mbedTLS) at 10k/50k/100k, ed25519
   verify, ECDSA P-256 keygen + self-signed certificate creation.
4. **OTA spike:** signed manifest verify, `finish()`/`activate()`, forced rollback
   by resetting before `mark_running_slot_valid()`.
5. **Toolchain spike:** workspace split, clippy and build in CI (cold and cached
   times).

## 11. Sources

- https://github.com/esp-rs/esp-idf (README, `esp-idf-svc/CHANGELOG.md`,
  `esp-idf-sys/CHANGELOG.md`, `esp-idf-hal/src/uart.rs`,
  `esp-idf-svc/src/ota.rs`, `esp-idf-svc/src/mqtt/client.rs`,
  `esp-idf-svc/src/http/server.rs`, `.github/workflows/ci.yml`)
- https://github.com/esp-rs/esp-idf-svc (archived; README redirect to the monorepo)
- https://github.com/esp-rs/esp-idf-template (README, `cargo/.cargo/config.toml`, `cargo/sdkconfig.defaults`)
- https://github.com/esp-rs/espup, https://github.com/esp-rs/rust-build/releases, https://github.com/esp-rs/xtensa-toolchain
- https://github.com/esp-rs/esp-hal (README on stable vs unstable APIs)
- https://github.com/ivmarkov/ruwm
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/uart.html
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/protocols/mbedtls.html
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/security/secure-boot-v2.html
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/storage/nvs_encryption.html
- https://github.com/espressif/esp-idf (`components/esp_driver_uart/include/driver/uart_types.h`, `.../uart.h`, `components/mbedtls/Kconfig` on release/v5.5)
- https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- crates.io API (versions in section 1); `ed25519-dalek` and `pbkdf2` `src/lib.rs` on GitHub
