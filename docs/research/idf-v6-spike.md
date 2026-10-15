# ESP-IDF v6.0.3 feasibility spike (2026-10-12): PARTIAL (steps 0, 3 pass; 1, 2, 4 blocked by board reset into download mode, see "Second run")

Code: `spikes/esp-idf-v6/` (standalone Cargo project, not in any workspace, nothing committed).
Result summary: **0 pass; 3 PBKDF2 pass; 1 (Wi-Fi/MQTT/HTTPS) and 4 (UART) NOT RUN to a verdict**
because the XIAO stopped answering over USB part-way through step 4 (see "Blocker").
All of the code for steps 1, 2 and 4 is written and compiles against v6.0.3; it just was not run to completion.

## Versions used
ESP-IDF v6.0.3 (mbedTLS 4.1.1 / TF-PSA-Crypto), esp-idf-svc 0.53.0, esp-idf-hal 0.47.0, esp-idf-sys 0.38.1,
embuild 0.33, Rust `esp` 1.99 (espup 0.18), espflash 4.6, `espressif/mqtt` managed component `1.*`.
Python **3.14** (Homebrew) used for the IDF python env (see friction 1).

## Results

### 0. Build and flash: PASS
- Boot log: `ESP-IDF: v6.0.3`, `esp_psram: Found 8MB PSRAM device`, `Speed: 80MHz`, **`octal_psram: ECC is enabled`**
  (`CONFIG_SPIRAM_ECC_ENABLE=y` accepted on chip rev v0.2). Heap pool added: 7680K of PSRAM
  (`heap_caps_get_total_size(SPIRAM)` = 7,864,320), i.e. ECC costs about 512 KB of the 8 MB.
- Internal heap at boot (240 MHz, PSRAM on): free 367,691 B, largest block 270,336 B.
- First-build time: about 3 min for the first (failed on Python) attempt incl. IDF clone with submodules
  (~4.4 GB `.embuild`), then ~1 min for the successful full IDF+Rust compile; incremental rebuilds 4 s.
  A cold CI build is therefore a few minutes of compile plus a large clone; cache `.embuild`.
- Image size: hello world app 385,200 B; spike with PBKDF2, UART, Wi-Fi, MQTT, HTTPS server and cert generation
  linked in: **545,536 B app (17.3% of a 3 MB slot)**. (The Rust binary is 998 KB ELF.)
  Note this build had no MQTT TLS traffic code paths trimmed; real firmware will be bigger, but a 3 MB slot looks
  generous; 2 MB slots would likely still fit. Confirm with the real image.
- sdkconfig check (final generated sdkconfig): no `CONFIG_SECURE_BOOT`, no `CONFIG_FLASH_ENCRYPTION_ENABLED`,
  no `CONFIG_NVS_ENCRYPTION`. grep for `^CONFIG_(SECURE_BOOT|FLASH_ENCRYPTION|NVS_ENCRYPTION|EFUSE_VIRTUAL)` matched only
  four capability constants (`SECURE_BOOT_V2_RSA_SUPPORTED`, `SECURE_BOOT_V2_PREFERRED`, `SECURE_BOOT_IMAGE_DIGEST_LEN`,
  `SECURE_BOOT_ROM_FAST_WAKE_RESERVE_SIZE`), none of which enable anything. No espefuse command was run.

### 3. PBKDF2-HMAC-SHA256 via PSA: PASS (but slow)
`psa_key_derivation_setup(PBKDF2_HMAC(SHA256))` + `input_integer(COST)` + `input_bytes(SALT, PASSWORD)` + `output_bytes`.
Both outputs match Python `hashlib.pbkdf2_hmac` ("correct horse battery" / "solark-salt-0001", 32 B):
```
[T3] pbkdf2 iters=10000 time=927 ms match=true
[T3] pbkdf2 iters=50000 time=4638 ms match=true
```
At 240 MHz that is about 93 us per iteration, roughly 3x slower than the toolchain-doc estimate (2-3.5 s per 100k).
**50k iterations = 4.6 s blocks a login**; 10k = 0.93 s. Not tried: `CONFIG_MBEDTLS_HARDWARE_SHA=n` (software SHA may beat
the peripheral for tiny blocks), or a hand-rolled HMAC loop with precomputed ipad/opad states. The default
iteration count in the plan should be 10k-20k, or the Crypto trait should be benchmarked on both paths.
`pkcs5.h` is still in the bindings list but PSA is the supported path in mbedTLS 4.

### 2. On-device ECDSA P-256 self-signed cert: COMPILES, NOT RUN
Written in `src/certgen.rs`. All needed mbedTLS 4 APIs exist and bind (`psa_generate_key`, `mbedtls_pk_copy_from_psa`,
`mbedtls_x509write_crt_*`, `mbedtls_pk_write_key_pem`). Needs `CONFIG_MBEDTLS_X509_CREATE_C=y` and
`CONFIG_MBEDTLS_X509_CRT_WRITE_C=y` (off by default, otherwise bindgen emits no `x509write` functions) and
`CONFIG_ESP_HTTPS_SERVER_ENABLE=y` (otherwise `httpd_ssl_start` and the svc `server_certificate` field are absent).
Timing, HTTPS serving, curl and heap-with-MQTT were not measured.

### 1. Wi-Fi + MQTT over TLS: NOT RUN
The Keychain credential arrived after the board was lost. Code is in `src/net.rs` (creds, broker URL and CA path come
from compile-time env vars `SPIKE_WIFI_SSID/PASS`, `SPIKE_BROKER_URL`, `SPIKE_MQTT_USER/PASS`, `SPIKE_CA_PEM`; nothing was
ever built with credentials in it). The Mosquitto/openssl setup was not started. `CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC`,
`DYNAMIC_BUFFER` and the `espressif/mqtt` component all configured and linked with no Kconfig renames needed.

### 4. UART RX-only + idle timeout: NOT RUN TO A VERDICT
The first run aborted at `UartTxDriver::new(uart0, GPIO1, ...)` (the `.unwrap()` at `uart_test.rs:144`; error text not captured
before the board went silent). So no TOUT unit result. Static findings from the v6.0.3 sources:
- `uart_config_t` in v6.0.3 has **no `rx_glitch_filt_thresh`** field (only `flags.allow_pd/backup_before_sleep`), so the glitch
  filter is not reachable through the public API. The `UART_RX_FILT_REG` register (base+0x18) is reachable by raw volatile
  access from Rust (written in the test, not run).
- `uart_detect_bitrate_start(uart, &cfg)` / `_stop` exist in the bindings (reachable from Rust). v6 doc: standalone API that
  acquires a free HP UART port; with all three UARTs in use it is expected to fail with "No free uart port" (untested).
- Reading the register back is the way to settle the TOUT unit (`UART_MEM_CONF_REG` bits [26:17]); test written, not run.
- TRM text (hardware-electrical.md) says bit times for the register; IDF's `uart_set_rx_timeout` is documented in symbols.

## Blocker
After flashing the 545 KB spike image, the board ran PBKDF2 correctly, then crash-looped at the UART0 TX driver
creation, and then **stopped responding on `/dev/cu.usbmodem2101`**: no serial output, and `espflash` fails with
"Failed to connect to the device" for `--before default-reset|usb-reset|no-reset`, with or without stub, even after a manual
DTR/RTS download-mode sequence and 45 s of waiting. macOS still lists "USB JTAG/serial debug unit". `lsof` shows no
other holder. Per the brief I did not attempt exotic recovery (no eFuse tools). Likely needs a physical re-plug or a
BOOT+RESET entry into ROM download mode, then a re-flash. Because of this, the cleanup `espflash erase-flash` **failed
(could not connect)**; the board still has the credential-free spike image on it (no Wi-Fi creds were ever built in, so there
is nothing to leak). `cargo clean` was run (removed 930 MiB); `.embuild` (the IDF clone, 4.4 GB, gitignored) was left in
place.

## Friction log (v6-specific unless stated)
1. **Python >= 3.10 required.** IDF v6 installer refuses the system Python 3.9.6 ("ESP-IDF supports Python 3.10 or newer").
   Workaround: put a `python3` -> Homebrew `python3.14` shim first on PATH for the build (3.14 worked).
2. **Custom partition table cannot be set via sdkconfig** (esp-idf-sys limitation, README "Known limitations"): setting
   `CONFIG_PARTITION_TABLE_CUSTOM*` makes ninja look for `out/partitions.csv` and the build fails. Workaround: leave them out
   and pass `espflash flash --partition-table partitions.csv --flash-size 16mb`.
3. **espflash 4.6 panics on numeric data subtypes** (`data, 0x40` and `64`; `Option::unwrap` in esp-idf-part). Workaround:
   use the named subtype `undefined` for the `backfill` partition (works). A custom subtype number would need another tool.
4. **External `mqtt` component:** added via `[[package.metadata.esp-idf-sys.extra_components]] remote_component = { name = "espressif/mqtt", version = "1.*" }`;
   builds and links. Registry has 1.0.0 and 1.1.0. This pulls from the Espressif component registry at build time (supply-chain
   note: pin the exact version and vendor it for CI).
5. **mbedTLS 4 changes seen:** version 4.1.1; legacy crypto headers (`aes.h`, `pkcs5.h`, ...) are private or dropped, so
   crypto goes through PSA. PSA macros with casts (`PSA_ALG_PBKDF2_HMAC`, key types, `PSA_KEY_USAGE_*`) are not exported by
   bindgen, so the constants are hard-coded from `crypto_values.h`. The `psa_set_key_*` static inlines are not bound, but
   `psa_key_attributes_t` fields are public so they are set directly. `mbedtls_x509write_crt_pem` has no RNG argument.
   x509 write APIs need the two `X509_*_C` Kconfig options. Kconfig names for external mem / dynamic buffer are unchanged.
6. **`embedded-svc` version split:** use `esp_idf_svc::io::Write` (embedded-io 0.7); `embedded-svc` 0.28 brings embedded-io 0.6 and the
   trait does not apply to the HTTP `Response`.
7. **Monitoring tooling:** `espflash monitor` needs a TTY (no `timeout` on macOS either); a pyserial script with an RTS pulse
   worked for log capture.
8. `cfg(espidf_time64)` rustflag from the toolchain doc was kept in `.cargo/config.toml`.

## sdkconfig.defaults that worked (steps 0 and 3 verified at runtime; the rest only configured and linked)
See `spikes/esp-idf-v6/sdkconfig.defaults`. Key lines: `CONFIG_SPIRAM=y`, `SPIRAM_MODE_OCT=y`, `SPIRAM_SPEED_80M=y`,
`SPIRAM_ECC_ENABLE=y`, `SPIRAM_USE_MALLOC=y`, `ESPTOOLPY_FLASHSIZE_16MB=y`, `ESPTOOLPY_FLASHMODE_QIO=y`,
`ESP_DEFAULT_CPU_FREQ_MHZ_240=y`, `FREERTOS_HZ=1000`, `ESP_CONSOLE_USB_SERIAL_JTAG=y`, `MBEDTLS_EXTERNAL_MEM_ALLOC=y`,
`MBEDTLS_DYNAMIC_BUFFER=y`, `MBEDTLS_DYNAMIC_FREE_CONFIG_DATA=y`, `MBEDTLS_DYNAMIC_FREE_CA_CERT=y`,
`MBEDTLS_X509_CREATE_C=y`, `MBEDTLS_X509_CRT_WRITE_C=y`, `ESP_HTTPS_SERVER_ENABLE=y`, `MQTT_PROTOCOL_311=y`,
main task stack 16384. Not in the file because of friction 2: the partition table lines.

## Partition table used (`spikes/esp-idf-v6/partitions.csv`, applied at flash time)
```
nvs 0x9000/0x10000; otadata 0x19000/0x2000; phy_init 0x1B000/0x1000; coredump 0x1C000/0x10000
factory 0x30000/0x300000; ota_0 0x330000/0x300000; ota_1 0x630000/0x300000
backfill (data, undefined) 0x930000/0x500000     -> ends 0xE30000, 1.8 MB spare in 16 MB
```
Measured app image 545 KB (17% of a 3 MB slot) with the spike feature set. 3 MB x 3 apps is more than needed; 2 MB slots
would still leave about 3x headroom and free about 3 MB. Decide after a real image exists.

## Second run (2026-10-12/13): steps 1, 2, 4 still NOT RUN: board resets only into ROM download mode

What was done: rewrote step 4 (UART0 TX on spare GPIO4; GPIO4's pad input fed to UART1/UART2 RXD via
`esp_rom_gpio_connect_in_signal`, signal indices from `gpio_sig_map.h`: U1RXD_IN=15, U2RXD_IN=18; the old code used
the wrong index 14 for U0TXD_OUT, the real one is 12). It adds a threshold sweep, split/merge matrix, 8/205-byte frames,
zero-gap back-to-back frames and a jitter measurement. Added `CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y`.
Set up (and later removed) a throwaway ECDSA CA + server cert (SAN = Mac LAN IP) and a native mosquitto 2.1.2 TLS
listener on 8883 with `allow_anonymous false`; it started and listened. Built with Wi-Fi/MQTT credentials via env vars
(never echoed or written; the build output was filtered). Build **passed** on v6.0.3 (38 s incremental after clean),
app image **1,236,528 B (39.3% of a 3 MB slot)** with Wi-Fi, MQTT-TLS, HTTPS server, certgen and UART all linked
(the earlier 545 KB figure was without credentials, so net.rs was dead-code eliminated; use 1.24 MB as the real baseline).
Flash with `espflash flash --partition-table partitions.csv --flash-size 16mb` succeeded ("Flashing has completed").

**Blocker (not a firmware panic): the chip never ran the app after flashing.** Every reset I could trigger from the Mac
(espflash `flash --monitor`, `monitor`+CTRL+R, `reset`, `reset --after watchdog-reset`, and a manual DTR/RTS pulse with
RTS-only reset, DTR low) landed in the ROM and printed:
```
ESP-ROM:esp32s3-20210327
rst:0x15 (USB_UART_CHIP_RESET),boot:0x0 (DOWNLOAD(USB/UART0))
waiting for download
```
No application log line, no panic text, and no halt message were ever seen, so there is **no panic text to report**.
After `espflash erase-flash` (blank flash) the same banner appears, so the app image is not the cause: the strapping
read at reset is "download" regardless of flash content. Per the brief I stopped retrying. The board still answers espflash
(connect, flash and erase worked). **Needs manual action: unplug the USB cable and plug it back in (power-on reset, no BOOT
button), then retry; if it still lands in download mode, hold B while plugging in, flash, and unplug/replug without B.**
The same symptom probably explains the previous agent's "board stopped responding" (it was likely sitting in ROM download mode
rather than crashed, and the UART0/GPIO1 panic may have been a red herring).
Open question for the re-run: whether macOS asserting DTR on port open keeps GPIO0 low through the USB-Serial/JTAG reset
logic; a monitor that opens the port with DTR/RTS cleared (or `--before no-reset`) after a replug should be tried first.

Cleanup done: `espflash erase-flash` (success, flash only), `cargo clean` (808 MiB removed), scratchpad CA/keys/mosquitto
config deleted, mosquitto killed (no mosquitto process left). No espefuse command run. Final generated sdkconfig:
`CONFIG_ESP_CONSOLE_UART_NUM=-1` (console is USB-Serial/JTAG, so UART0 is free), `ESP_SYSTEM_PANIC_PRINT_HALT=y`,
`MBEDTLS_EXTERNAL_MEM_ALLOC=y`, `MBEDTLS_DYNAMIC_BUFFER=y`; the only `SECURE_BOOT*` matches are the four capability constants
listed under step 0; no `FLASH_ENCRYPTION`, `NVS_ENCRYPTION` or `EFUSE_VIRTUAL` entries.

## Recommendation
**Provisional: v6.0.3, with a hardware re-run required before the plan commits.** Steps 1, 2 and 4 remain unverified at runtime
(no hardware result in two attempts), but nothing found so far is specific to v6.0.3 and failing: the full feature set
(Wi-Fi, SNTP, `espressif/mqtt` over TLS, mbedTLS 4 x509write + PSA, HTTPS server, three UART drivers, raw TOUT register
access) builds and links on v6.0.3, the image fits easily, PSRAM octal + ECC and PSA PBKDF2 are proven on hardware, and the
board failure is a host/strapping reset problem independent of the IDF version (it occurs with a blank flash).
Cost of being wrong is small: if the re-run shows MQTT-TLS or the HTTPS server failing on mbedTLS 4, fall back to v5.5.5 with
a board-crate-only change. Not a clean "v6 is proven" call; treat the UART TOUT unit (bits vs symbols; IDF's
`uart_set_rx_timeout` is symbol-scaled while the register is bit-scaled per the TRM) and the 8/205-byte frame splitting as
open risks to be closed by `src/uart_test.rs`, which is ready to run. PBKDF2 default iteration count should be 10k-20k.

## Third run (2026-10-12/13): step 4 PASS; steps 1 and 2 BLOCKED by Wi-Fi auth (AUTH_EXPIRE); reset quirk solved

### Flashing / reset recipe (use this as the project's flashing recipe on macOS)
1. Flash without any reset or DTR: `espflash flash --after no-reset --partition-table partitions.csv --flash-size 16mb --port /dev/cu.usbmodemXXXX <elf>`.
   Never use `espflash monitor`, `flash --monitor`, or anything that asserts DTR (it lands the S3 in ROM download mode, `boot:0x0`).
2. Run the app with an RTS-only pulse while DTR stays low, via pyserial (`uvx --with pyserial python -I ...`): set `dtr=False, rts=False`
   BEFORE `open()`, then `rts=True; sleep(0.1); rts=False`. The USB device disappears and returns on chip reset, so the monitor
   must reopen in a loop (always with dtr/rts low set before open). This worked first time on every run (7 resets, 0 download-mode landings).
3. `espflash erase-flash --after no-reset` also works.
Python 3.14 `python3` shim must be first on PATH for the build (friction 1); `source ~/export-esp.sh` and rustup on PATH.

### Step 4: UART RX-only + TOUT, two UARTs at once: PASS
Loopback: UART0 TX on GPIO4 (UART0 driver needs an RX pin and an RX buffer in v6/hal: `UartTxDriver` fails with "uart rx buffer length error",
use `UartDriver` with a spare RX pin, GPIO5), pad input routed to UART1 and UART2 RXD. 9600 8N1, char = 1042 us.
- **TOUT unit: the register is in BITS.** `uart_set_rx_timeout(n)` writes reg = 10*n (n = symbols of 10 bits). Measured idle-detect delay after TX done:
  reg 10 -> ~990 us, 35 -> ~3590 us, 100 -> ~10340 us (104 us/bit). API 4 -> reg 40 -> 4165 us. Raw reg 35 = 3.5 chars exactly (3646 us nominal).
- Sweep (two 10-byte frames, gap in us; split = 2): API 1 splits at >=1000 us; API 2 at >=2000; API 3 at >=3000; API 4 at >=4500 (merged at 3600);
  API 6 only at 10000; API 10 never. So API 4 (3.5 char) splits gaps of >=4.5 ms and merges <=3.6 ms; API 3 splits at 3.0 ms.
  A 3.5-char Modbus gap is raw 35, i.e. API 3.5 is not expressible: use API 4 (4.0 chars) or write the register directly (raw 35); the
  register write works (readback matches).
- Both UARTs simultaneously, 8 / 205 / zero-gap back-to-back (20+37+9 in one write) / 64 + 12 at 400 us gap: each UART delivered exactly 4 frames,
  lengths 8, 205, 66 (back-to-back merged, as expected) and 76 (the 400 us gap does not split). UART1 vs UART2 timestamp difference 16-130 us (first frame 123-130 us, later 16-44 us).
- Timestamp jitter (esp_timer us at idle-detect, 30 frames): latency after TX-done min 4014, max 4069, mean 4023 us; spread ~43-55 us. esp_timer step 1 us.
- Extras: RX_FILT register reachable; `uart_detect_bitrate_start` works with all three UARTs in use.
- Heap after UART: internal free 299,595 B (min ever 267,432), PSRAM free 7,850,612 B. Boot: internal 316,651, PSRAM 7,860,492. PBKDF2 10k = 927 ms (re-confirmed).
- Task watchdog fires during the 50k PBKDF2 busy loop (main task starves IDLE0): benign, spike-only. No panics.

### Steps 1 and 2: NOT RUN (Wi-Fi never associated)
Broker side was ready (mosquitto 2.1.2 TLS on 8883, `allow_anonymous false`, throwaway P-256 CA, SAN = Mac LAN IP); firmware built with credentials from the
Keychain via env only. Scan shows the SSID on 3 BSSIDs (ch 6 at -28..-34 dBm, ch 1 at -60..-70, ch 6 at -75..-80), authmode WPA2WPA3Personal (WPA2Personal when SAE is compiled out).
Attempts, all failing before the 4-way handshake:
1. Default config (SAE on, sae_pwe_h2e=0): `init->auth`, `auth->init` after ~4 s, disconnect reason=2 (AUTH_EXPIRE), alternating ch 6/1.
2. SAE compiled out (`CONFIG_ESP_WIFI_ENABLE_WPA3_SAE=n`, plain WPA2-PSK): AP answered auth and moved to assoc once, then `assoc->init`, again reason=2.
3. SAE on with `sae_pwe_h2e = BOTH` (readback 3), via raw `esp_wifi_set_config`: auth timeout, reason=2.
4. Explicit `AuthMethod::WPA2WPA3Personal`, PMF capable (not required), all-channel scan: same, reason=2.
No password-related failure code (no 4-way handshake). Per instruction, stopped there. **User action: check AP controller for MAC filtering (board STA MAC <MAC>),
WPA3-only/PMF-required, minimum data rate (try disabling/lowering), band steering, client limit; or give a plain WPA2 SSID/guest network.**
Evidence not collected: SNTP, MQTT publish/subscribe round trip, cert generation time, `curl -k`, `openssl s_client` curve, heap with both running.
The code for them is unchanged and linked (net.rs; image 1.246 MB, 39.6% of the slot). Diagnostics added to net.rs: scan of matching APs, disconnect reason log, sae_pwe_h2e/PMF raw config.

Checks: serial logs were grepped for the Wi-Fi password and SSID (via Keychain values): not present. No eFuse commands.
Cleanup: `espflash erase-flash` done (flash blank, board will loop `invalid header`), `cargo clean`, scratchpad CA/keys/config deleted, mosquitto killed.

### Final recommendation: **v6.0.3 (provisional)**
Step 4 and 3 pass on hardware on v6.0.3 and there is nothing v6-specific failing. The Wi-Fi failure is an AP/network symptom (auth never completes even with plain WPA2),
not an IDF-version finding, but it means MQTT-TLS and HTTPS on mbedTLS 4 have still not run. Keep v6.0.3, with a 30-minute re-run of steps 1 and 2 once the network issue is fixed
before the plan commits; fall back to v5.5.5 (board-crate-only change) if either fails.

## IoT Wi-Fi join check (2026-10-12, association + DHCP only)
Change: new `spikes/esp-idf-v6/src/wifi_check.rs`, enabled by build env `SPIKE_WIFI_ONLY=1` (main returns after it; also `SPIKE_WIFI_AUTH=wpa2wpa3`,
`SPIKE_WIFI_PMF=off`). `net.rs` still needs `SPIKE_CA_PEM` to point at any file (used `Cargo.toml`). Credentials from Keychain inline only.
- Scan: SSID matched on 3 BSSIDs, authmode **WPA2Personal** (ch 6 -30, ch 1 -55, ch 6 -76 dBm).
- Variant 1 (WPA2Personal, PMF capable, not required): never associated; ch 1/6 home-channel hops, then `StaDisconnected reason=2` (AUTH_EXPIRE) at ~9 s. No IP.
- Variant 2 (PMF capable=false): flashed, but the console showed no output afterwards (monitor lost the USB re-enumeration, later runs returned 0 bytes); result not observed.
- After that the board stopped answering `espflash` ("Failed to connect"), so `erase-flash` FAILED: the Wi-Fi-only image (with SSID/password baked in) is still in flash.
  Needs a manual BOOT-button erase. Serial logs grepped for the password: absent. No eFuse commands. `cargo clean` done.

## New board A/B (2026-10-12, new XIAO ESP32S3 Plus MAC <MAC>, fresh antenna)
- Flash with `--after no-reset` worked first time (board-info, factory firmware no obstacle). RTS-only reset with a pre-started reopen-loop monitor worked.
- Variant 1 (WPA2Personal, PMF capable, not required): scan matched 3 BSSIDs (WPA2Personal, ch 6 -28/-29, ch 1 -54..-59, ch 6 -73..-77 dBm). Never associated:
  ch 1/6 home-channel hops, `StaDisconnected reason=2` (AUTH_EXPIRE) at ~9 s, `ESP_ERR_TIMEOUT` at ~24 s. No IP. Same symptom as the old board, so the antenna/TX hypothesis is not supported.
- Variant 2 (PMF capable=false): scan OK, then the console went silent after the second boot banner and stayed silent over two more RTS resets (device node present); outcome not observed.
- Cleanup: `espflash erase-flash` FAILED twice ("Failed to connect"): the image with SSID/password baked in is STILL IN FLASH. Needs manual BOOT-button erase. `cargo clean` done.
  Logs grepped for the password: absent. No eFuse commands.

## Hotspot A/B (2026-10-12): v6 Wi-Fi works; <IoT SSID> failure is on the network side

Same `SPIKE_WIFI_ONLY` image (v6.0.3 app, PMF capable/not required, WPA2 threshold), new XIAO (MAC new-board), joining an
Phone hotspot (2.4 GHz "Maximize Compatibility", WPA2, ch1): scan rssi -13, `init -> auth -> assoc -> run` in ~15 ms,
associated in 2605 ms, GOT IP 172.20.10.2 at 6.8 s, stayed connected 30 s (rssi -11..-21). So ESP-IDF v6 + esp-idf-svc
Wi-Fi and both boards' radios are fine; the AUTH_EXPIRE (reason 2) on <IoT SSID>/<home SSID> is AP controller-side (AP never answers the
auth frame). Next: AP controller AP event log for the MAC, check 802.11r/fast roaming, MAC filter, per-AP blocklist.
- Note: the 2nd-stage bootloader banner reads `ESP-IDF v6.1-beta1` because espflash flashes its bundled bootloader;
  the app is v6.0.3. The firmware plan should flash the project's own `bootloader.bin` (`--bootloader`).
- Recovery from B-button download mode: after flashing, an RTS pulse lands in `boot:0x0` again; a USB power-cycle boots
  the app (`boot:0x2b`).
- Full `espflash erase-flash` timed out on EraseFlash after connecting (16 MB chip erase exceeds its timeout).
- Workaround that works: `espflash erase-region` of nvs (`0x9000 0x10000`) and the app (`0x30000 0x300000`) takes ~5 s;
  the new board is now clean. The old board still holds the old <IoT SSID> image; erase it the same way.

## <IoT SSID> isolation tests (2026-10-12 evening)
- Live controller (read-only, via the network-config repo): neither XIAO MAC has ever been recorded; nothing blocked; <IoT SSID> has
  WPA2/PMF off/no MAC filter/no 11r/no RADIUS; another Espressif client (OUI <Espressif>) is joined and healthy.
- v6 pinned to the outdoor AP (ch 1, BSSID <MAC>, rssi -52..-62): same `init -> auth`, no reply, reason 2.
  So not specific to the U7 Pro XGS / ch 6.
- **MicroPython v1.29.0 (ESP-IDF v5.5.2) on the same board: also fails** (status 202 AUTH_FAIL roughly every 6 s, 4 tries).
  So it is NOT an ESP-IDF v6 regression; the v6 choice stands on this point. Remaining: AP-side logs (`ssh -J truenas`, read-only)
  or a monitor-mode capture to see whether the AP receives the Authentication frame.

## ROOT CAUSE FOUND (2026-10-12 ~22:40 local): TX power at max
- AP-side logs (U7 Pro XGS 13:47, `logread`, run by the user over `ssh -J truenas`): the AP DOES receive every auth frame
  from <MAC> (rssi ~-33) and hostapd logs "IEEE 802.11: authenticated" each time, i.e. it sends the auth
  response; STA-TRACKER logs `auth_failures` with assoc_status 0, i.e. the XIAO never follows with an assoc request.
  So the XIAO is not receiving/decoding the AP's auth response.
- TX power sweep (MicroPython v1.29 / IDF v5.5.2, `w.config(txpower=N)`, <IoT SSID>): 8.5, 11, 13, 15, 17, 18, 18.5, 19 dBm all
  join (GOT IP in 1.2-2.2 s); **19.5 dBm fails**, and the default (max, ~20 dBm) fails. Repeats at 17 and 15 also join.
- Consistent with widely reported small-module ESP32-S3/C3 behaviour where lowering TX power fixes AUTH_EXPIRE
  (e.g. arduino-esp32 #6767, Home Assistant community thread, Arduino forum ESP32-C3 thread).
- Firmware plan impact: `wifi.tx_power_dbm` must be a runtime config value (No-static-values rule), with a default
  below the threshold (proposed 17 dBm), applied via `esp_wifi_set_max_tx_power` (units of 0.25 dBm) after `esp_wifi_start`.
  Re-verify on v6 and when powered from the carrier's buck (USB power from the Mac may contribute) before the plan.
- Board new-board currently holds MicroPython; erase it (nvs + all) on the next B-button visit, along with old-board.

## Fourth run (2026-10-12 late): steps 1 and 2 PASS on v6.0.3 from <IoT SSID> (the new board, <reserved LAN IP>)
Firmware changes vs the third run (`spikes/esp-idf-v6/src/net.rs`):
- `esp_wifi_set_max_tx_power(68)` (17 dBm) after `wifi.start()`. Reads back `actual=68`, rc=0.
- The auth threshold is `AuthMethod::WPA2Personal`. A `WPA2WPA3Personal` threshold rejects WPA2-only APs with reason 211.
- The MQTT wait was raised to 600 s, so Wi-Fi stays up long enough to observe.

Results:
- **Wi-Fi:** joined in 3.67 s and got the DHCP reservation <reserved LAN IP>. The AP controller reservation was moved from old-board to new-board.
- **SNTP:** synced in 4.4 s through the permanent IoT→NTP rule.
- **Step 1 (MQTT over TLS):**
  - Connected to mosquitto at <broker LAN IP>:8883 with a throwaway P-256 CA, username and password, and `allow_anonymous false`. The TLS connect took 2.1 s.
  - The broker logged `New client connected from <reserved LAN IP> as solark-spike (p4, c1, k120, u'spike')`, then a SUBSCRIBE, then a QoS 1 PUBLISH to `solark/spike/hello`.
  - Inbound works: a publish from the Mac to `solark/spike/cmd` arrived (`mqtt rx topic=solark/spike/cmd len=13`).
- **Step 2 (HTTPS with an on-device certificate):**
  - A P-256 certificate was generated in 307 ms. The server listened on :443.
  - From the Mac: HTTP 200, TLSv1.2 `ECDHE-ECDSA-AES256-GCM-SHA384`, `CN=solark-spike`. Verify result 18 is expected for a self-signed certificate.
  - Note: the server negotiated **TLS 1.2, not 1.3**. Decide in the plan whether to enable `CONFIG_MBEDTLS_SSL_PROTO_TLS1_3` for the server.

**Final recommendation: ESP-IDF v6.0.3, confirmed.** Steps 0 to 4 are all verified on hardware.

Items for the plan:
- `wifi.tx_power_dbm`, default 17.
- WPA2Personal as the auth threshold.
- A configurable DHCP hostname, default `solark-xiao`. AP controller showed `espressif` and `mpy-esp32s3` flapping.
- Flash our own `bootloader.bin`. espflash's bundled one is v6.1-beta1.
- An erase-region recovery recipe.
- TLS 1.3 on the server.
- Re-verify TX power when powered from the carrier's buck.
