# Hardware and electrical feasibility: XIAO ESP32S3 Plus tap inside the Sol-Ark dongle

Status: research, 2026-10-12. Input for the schematic and BOM.
Related: [`../serial-link-findings.md`](../serial-link-findings.md),
[`../plans/2026-10-11-xiao-firmware-design.md`](../plans/2026-10-11-xiao-firmware-design.md) section 1.

Every claim is labelled. **[V]** means verified from a primary source, which is
cited. **[I]** means inferred, with the reasoning given. **[M]** means it must be
measured before connecting anything (see the checklist in section 9).

## 0. Decisions at a glance

| Item | Decision |
|---|---|
| Tap "resp" (pad 9, R1OUT, inverter→dongle) | XIAO **D0 = GPIO1**, UART1 RX |
| Tap "req" (pad 10, T1IN, dongle→inverter) | XIAO **D1 = GPIO2**, UART2 RX |
| Series resistor per tap | **10 kΩ**, mounted **at the dongle pad end** |
| Pull-up | Internal pull-up **off**. Optional external 100 kΩ to XIAO 3V3, at the XIAO end |
| Glitch filter (optional) | 100 pF C0G from GPIO to GND at the XIAO end (do not fit by default) |
| If pad 7 measures 5 V | Add a 22 kΩ resistor to GND at the XIAO end (divider with the 10 k), **or** fit an SN74LVC2G17 powered from XIAO 3V3 (preferred) |
| Status LED | On-board USER_LED, GPIO21, active-low. No external part needed |
| Button | On-board BOOT, GPIO0, read after boot (for example, long-press for a config reset). No external part |
| 12 V→5 V regulator | **Pololu D24V10F5** (#2831, 5 V 1 A, 5.1–36 V in). Fallback: D45V5F5 (#5433) |
| 12 V input protection | PTC fuse (~0.3 A hold) → Schottky (SS14) → SMAJ18A TVS → 33 µF/50 V electrolytic + 100 nF |
| 5 V into XIAO | Regulator VOUT → **low-Vf Schottky (SS34/PMEG3020) or LM66100** → XIAO **5V pad**, with 100 µF low-ESR + 10 µF at the pad |
| Antenna | XIAO Plus has **U.FL only**. Use an adhesive 2.4 GHz FPC antenna inside the dongle housing, away from the dongle's antenna and from metal |
| Firmware requirements from hardware | `CONFIG_SPIRAM_ECC_ENABLE=y` (thermal), internal pull-ups off on the RX pins, UART0 and BOOT left free, configurable Wi-Fi TX power cap, publish the die temperature in health |

**Show-stoppers: none found.** The open risks are thermal margin (65 °C limit
without PSRAM ECC), the DB9 12 V current budget (no published rating), and the
unmeasured pad 7.

---

## 1. XIAO ESP32S3 Plus

Primary sources:
- Seeed wiki: <https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/>
- Plus schematic v1.1 (KiCad, dated 2026-01-15, 4 sheets):
  <https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_V1.1_SCH_260115.pdf>
- ESP32-S3 datasheet v2.2: <https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf>

### 1.1 Memory

- **[V, measured on the user's own board]** On 2026-10-12, read-only
  esptool/espefuse on the user's XIAO ESP32S3 Plus reported: **ESP32-S3
  (QFN56) rev v0.2; 16 MB quad flash at 3.3 V; 8 MB embedded PSRAM, vendor
  AP_3v3; USB mode USB-Serial/JTAG.** Embedded 8 MB AP 3.3 V PSRAM makes
  the part an **ESP32-S3R8**, which is inferred from Espressif's ordering
  info (datasheet Table 1-1: S3R8 = 8 MB octal, 3.3 V VDD_SPI). The
  schematic evidence below agrees.
- **[V] Flash: 16 MB.** The wiki says "On-chip 8MB PSRAM & 16MB Flash" and
  "8MB FLASH (16MB in Plus version)". The schematic (sheet 4, U5) shows an
  external **PY25Q128HA-DFH-IR**, a 128 Mbit quad-SPI NOR, on VDD_SPI (pins
  SPICS0/SPICLK/SPID/SPIQ/SPIWP/SPIHD).
- **[V] PSRAM: 8 MB**, according to the wiki.
- **[I] PSRAM type: octal, in-package, so the chip is an ESP32-S3R8.** The
  schematic's block diagram (sheet 3) labels the PSRAM "Internal". On sheet 4,
  GPIO33–37 on the MCU symbol are no-connect (X), and so is SPICS1. Datasheet
  Table 1-1 lists the ESP32-S3R8 as "8 MB (Octal SPI)" with VDD_SPI at 3.3 V.
  The datasheet's pin-restriction notes say GPIO33–37 are "the higher 4 bits
  data line interface and DQS … in 8-line SPI mode", and "Do not use the pins
  connected to in-package flash/PSRAM for any other purposes." This agrees
  with the esptool readout above. A visual check of the chip marking is
  optional.
- **Consequence:** octal PSRAM uses GPIO33–37 plus the SPI0/1 pins (GPIO26–32).
  **None of these are brought out on the Plus**, so no exposed pad is tied to
  PSRAM or flash.

### 1.2 Exposed pads and GPIO map [V]

Schematic U2 "XIAO-HALF-HOLE-23P" (castellated) and the wiki pin table:

| XIAO pad | GPIO | Notes / hazards |
|---|---|---|
| D0 | GPIO1 | free. **Recommended: tap "resp" (pad 9)** |
| D1 | GPIO2 | free. **Recommended: tap "req" (pad 10)** |
| D2 | GPIO3 | **strapping** (JTAG signal source). Floating by default. Avoid |
| D3 | GPIO4 | free (spare) |
| D4 | GPIO5 | free (I2C SDA by convention) |
| D5 | GPIO6 | free (I2C SCL by convention) |
| D6 | GPIO43 | **U0TXD**, the ROM/IDF console. Leave free |
| D7 | GPIO44 | **U0RXD**, the console. Leave free |
| D8 | GPIO7 | free (SPI SCK by convention) |
| D9 | GPIO8 | free |
| D10 | GPIO9 | free |
| 5V | VBUS | see 1.4: **this is the USB VBUS net itself** |
| GND | GND | |
| 3V3 | VCC_3V3 | output of the on-board buck (Seeed says "you can draw 700mA"; the schematic notes Imax=600 mA) |
| D11 (pad 15) | GPIO38 | free |
| D12 (pad 16) | GPIO39 | MTCK (JTAG). Usable, but avoid |
| D13 (pad 17) | GPIO40 | MTDO (JTAG). Avoid |
| D14 (pad 18) | GPIO41 | MTDI (JTAG). Avoid |
| D15 (pad 19) | GPIO42 | MTMS (JTAG). Avoid |
| D16 (pad 20) | GPIO10 | **ADC_BAT** on the Plus (battery sense). Avoid |
| D17 (pad 23) | GPIO13 | free |
| D18 (pad 22) | GPIO12 | free |
| D19 (pad 21) | GPIO11 | free |

The extra pads 15–23 are the second castellated row on the Plus. Seeed
publishes two base footprints, with and without the "bottom pad lead out".

Other connections [V] (schematic sheet 4):
- **BOOT button K2 → GPIO0** (10 kΩ R7 pull-up to 3V3, 10 pF). GPIO0 is a strapping pin (boot mode).
- **RESET button K1 → EN/CHIP_PU** (10 kΩ R8, 1 µF).
- **USER_LED D3 (yellow): 3V3 → 1.5 kΩ R15 → LED → GPIO21.** It is active-low.
- **USB D−/D+ = GPIO19/GPIO20** (22 Ω series), wired only to the USB-C port and test pads TP7/TP8. They are not on the castellated pads.
- **GPIO45, GPIO46 (strapping):** no-connect on the MCU symbol.
- **B2B connector J3** (34-pin): carries GPIO11–18, 38–42, 47, 48, 21, 10, D2/D8/D9/D10, 3V3, and "VIN 3.7–5V". It is not used here.
- **Strapping pins [V]** (datasheet section 3, Table 3-1): GPIO0 (weak pull-up), GPIO3 (floating), GPIO45 (weak pull-down), GPIO46 (weak pull-down). Of these, only GPIO0 (BOOT) and GPIO3 (D2) can be reached on the Plus.

### 1.3 Antenna [V]

The schematic shows LNA_IN → L2 3.3 nH / C17 1.2 pF / C18 1.8 pF matching →
**ANT1 "U.FL-R-SMT-1", "RF U-FL Female"**. There is no populated PCB or chip
antenna (the alternative footprints are crossed out as not fitted). The wiki
says: "In order to get better WiFi/Bluetooth signal, you need to take out the
antenna inside the package". **An antenna must be attached**: without one the
range is minimal, and transmitting into an open connector is poor practice.

### 1.4 Power path of the 5V pad [V], with a backfeed hazard

From schematic sheet 4:

```
USB-C VBUS ──┬───────────── U2 pin 14 "5V/VBUS" (castellated pad)    ← same net, no diode
             ├─ C10 1 µF, R9 100 k, Q1 gate (PMOS battery switch: off when VBUS present)
             ├─ U4 SGM40567 Li-ion charger VIN
             └─ D2 LMBR4010BST5G (Schottky) ──► VIN ──► U3 SGM6029 buck ──► VCC_3V3 (Imax 600 mA)
VBAT ── Q1 PMOS ──────────────────────────────► VIN
```

- **The 5V pad is the USB VBUS net directly.** The only diode (D2) sits *after*
  the pad, between VBUS and the buck input. Seeed's wiki says the same thing:
  "You can also use this as a voltage input but you must have some sort of
  diode (schottky, signal, power) between your external power source and this
  pin with anode to battery, cathode to 5V pin."
- **Backfeed risk:** if the regulator feeds the 5V pad directly and a USB cable
  is plugged in, the computer's VBUS and the regulator output are shorted
  together. Neither Pololu board has reverse-current protection on VOUT. The
  external regulator would also power the charger IC.
- **Fix (adopted):** put a Schottky diode (SS14 class, 1 A 40 V) from regulator
  VOUT (anode) to the XIAO 5V pad (cathode). Use a low-Vf part (SS34 /
  PMEG3020-class, or an LM66100 ideal diode; see 4.4). After the two drops
  about **4.2–4.4 V reaches the SGM6029** (~4.0–4.1 V at the 390 mA peak with
  an SS14). That is
  fine: its input range is 1.95–5.5 V and it supports 100 % duty cycle
  ([SG Micro SGM6029](https://www.sg-micro.com/product/SGM6029) [V]), so it
  needs only ~0.5 V headroom at 400 mA [I].
- **Do not feed 3.3 V into the 3V3 pad [I].** That node is the synchronous
  buck's output. Back-driving it while VIN is unpowered (or while USB is
  plugged in) is unspecified behaviour that could reverse-bias the buck's
  high-side FET or fight its regulation loop. It also bypasses the board's
  power sequencing. Rejected.
- The BAT pads are not used. Seeed: "When you use battery power, there will be no voltage on the 5V pin."

### 1.5 Recommended GPIO use

| Function | Pin | Reason |
|---|---|---|
| UART1 RX "resp" ← pad 9 | **D0 / GPIO1** | Standard row, not strapping, not JTAG, not UART0, no on-board load |
| UART2 RX "req" ← pad 10 | **D1 / GPIO2** | same |
| Status LED | **GPIO21** (on-board, active-low) | Already fitted. The dongle case is opaque [I], so an external LED is optional. If one is wanted, use D3/GPIO4 → 1 kΩ → LED → GND |
| User button | **GPIO0** (on-board BOOT) | Read only after boot. Holding it at power-up enters download mode, which is acceptable for a service action |
| Spare | D3/GPIO4, D4/GPIO5, D5/GPIO6 | e.g., a future temperature sensor (I2C) |
| Keep free | D6/D7 (UART0 console), D2/GPIO3 (strapping), GPIO10 (ADC_BAT), GPIO39–42 (JTAG) | |
| Never use | **GPIO33–37** (octal PSRAM, not brought out), GPIO26–32 (flash/PSRAM SPI), GPIO19/20 (USB-Serial/JTAG, the active USB mode) | |

Pin choice must stay configurable (standing rule 2). These are defaults.

---

## 2. ESP32-S3 UART

Primary source: ESP32-S3 Technical Reference Manual v1.8,
<https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf>,
chapter 26 "UART Controller (UART)" and chapter 6 "IO MUX and GPIO Matrix".

- **[V] Three UART controllers** (UART0/1/2), §26.1: "ESP32-S3 has three UART
  controllers". The RX/TX FIFOs share 1024 × 8-bit RAM (§26.2), with 128 bytes
  RX by default (UART_MEM_CONF_REG.UART_RX_SIZE). The longest reply is 205
  bytes (100 registers), so the driver must drain by interrupt or use a larger
  RX size. ESP-IDF's driver handles this with its ring buffer.
- **[V] UART0 is the ROM/IDF console** on GPIO43/44 (datasheet "GPIO43,
  GPIO44: UART0 interface"). USB-Serial-JTAG is a **separate** peripheral on
  GPIO19/20. It is not a UART controller. **[I]** So the two taps use UART1
  and UART2, and UART0 stays free for the console whether the IDF console is
  set to UART0 or to USB-Serial-JTAG. All three UARTs are then in use if UART0
  is a console. That is fine because nothing else needs a UART.
- **[V] Any GPIO can be UART RX via the GPIO matrix.** §6 overview: "175 digital
  peripheral input signals can be sourced from the input of any GPIO pins."
  GPIO1 and GPIO2 are therefore valid. The matrix adds a couple of APB cycles
  of latency, which is irrelevant at 9600 baud.
- **[V] RX timeout (TOUT) is measured in bit times.** §26.4.3: "The
  UART_RXFIFO_TOUT_INT interrupt will be triggered when the bus is in the idle
  state for more than UART_RX_TOUT_THRHD bit time on current baud rate after
  the receiver has received at least one byte." Register 26.2
  (UART_MEM_CONF_REG, 0x0060): **UART_RX_TOUT_THRHD is bits [26:17] (10 bits,
  max 1023), reset 0xA**, enabled by UART_RX_TOUT_EN.
  - Modbus t3.5 at 8N1 is 3.5 × 10 = **35 bit times** (38.5 if counted with
    11-bit characters, as Modbus specifies for no parity). Set ≥ 35, and keep
    it configurable.
  - **[I]** ESP-IDF's public `uart_set_rx_timeout(port, tout_thresh)` takes
    whole *symbols* (characters) and multiplies by the bits per symbol, so
    3.5 cannot be expressed. Use 4 symbols (40 bit times) through the public
    API. For exact bit-time values, use `uart_ll_set_rx_tout` /
    `hal/uart_ll.h`. Verify this against the IDF version you pin. At 10
    bits/symbol the 1023 ceiling is about 102 symbols, which is ample.
- **[V] RX glitch filter exists.** Register 26.8 UART_RX_FILT_REG (0x0018):
  "UART_GLITCH_FILT When input pulse width is lower than this value, the pulse
  is ignored", 8 bits, reset 0x8; "UART_GLITCH_FILT_EN Set this bit to enable
  RX signal filter." **Caveat:** the prose in §26.4.3.2 ties this filter to
  the Baudrate_Detect block ("The Baudrate_Detect module … filters any noise
  whose pulse width is shorter than UART_GLITCH_FILT"). **[I]** The time unit
  is presumably the UART core clock (APB 80 MHz → max 255 × 12.5 ns ≈ 3.2 µs).
  The TRM does not say explicitly. Verify on the bench by injecting <0.5 µs
  pulses, or rely on the optional 100 pF RC (section 3).
- **[V] Autobaud: yes, but it is a measurement, not automatic.** §26.4.3.2
  "Baud Rate Detection": "Automatic baud rate detection (Autobaud) on UARTs is
  enabled by setting UART_AUTOBAUD_EN." The hardware latches
  UART_LOWPULSE_MIN_CNT, UART_HIGHPULSE_MIN_CNT, UART_POSEDGE_MIN_CNT and
  UART_NEGEDGE_MIN_CNT. Then "These four fields are read by software to
  determine the transmitter's baud rate", using for example
  `B = f_clk / ((LOWPULSE_MIN_CNT + HIGHPULSE_MIN_CNT + 2) / 2)`.
  **So firmware must read the counters, compute the rate and re-program the
  divider itself.** The UART does not lock on by itself. The design's "switch
  RX UARTs to automatic baud detection" is feasible as a software routine on
  top of these registers. **[I]** ESP-IDF exposes this only through the
  low-level HAL (`uart_ll_set_autobaud_en`, `uart_ll_get_low_pulse_cnt`, etc.),
  not through the public driver API, so verify this against the pinned IDF
  version. **[I] Rust:** the `uart_ll_*` helpers are `static inline` in
  `hal/uart_ll.h`, and esp-idf-sys bindgen generally does not emit static
  inline functions. From esp-idf-svc, autobaud and bit-exact TOUT will
  probably need direct register access (UART_AUTOBAUD_REG,
  UART_MEM_CONF_REG) or a small C shim. The firmware plan must budget for
  this. Also, a minimum-pulse measurement needs at least one isolated
  single-bit pulse in the traffic, which Modbus data provides quickly.

---

## 3. Logic levels and input protection

### 3.1 What drives the tapped lines

- **[V] UT3232 receiver output (R1OUT, pad 9)**: VOH ≥ VCC − 0.6 V at
  IOH = −1 mA (typ. VCC − 0.1 V). VOL ≤ 0.4 V at IOL = 1.6 mA. VCC is
  3.0–5.5 V. "Accepts 5.0V Logic Input With 3.3V Supply" (driver inputs).
  Source: UTC UT3232 datasheet (preliminary),
  <https://atta.szlcsc.com/upload/public/pdf/source/20161105/1478330903034.pdf>
  (the LCSC-hosted copy; the ordering table lists UT3232G-S16-R / -P16-R).
- **[V] Pad 10 (T1IN)** is a UT3232 driver *input*. It is driven by the
  dongle's ESP32 UART TX (a strong CMOS output), so it is only ever a
  receive-tap for us.
- **[V] ESP32-S3 inputs** (datasheet Table 5-4, 3.3 V, 25 °C): VIH ≥ 0.75 × VDD
  (2.475 V), VIL ≤ 0.25 × VDD (0.825 V), max input VDD + 0.3 = 3.6 V,
  IIH/IIL ≤ 50 nA, **CIN = 2 pF**, internal pull-up/down 45 kΩ typ. Inputs
  are **not 5 V tolerant**.

### 3.2 Pad 7 (UT3232G VCC): probably 3.3 V **[I], must be measured [M]**

Reasoning:
- The photo (`dongle_serial.jpg`) shows an **Espressif ESP32-SOLO-1** module on
  the PIEX-0025-00 carrier. That module runs from 3.0–3.6 V only and its GPIOs
  are not 5 V tolerant. The boot log confirms an ESP32 (ESP-IDF v3.3 bootloader)
  and a LAN8720 PHY, a 3.3 V part.
- R1OUT swings to the UT3232's VCC. If VCC were 5 V, R1OUT would drive about
  5 V into the ESP32's RX pin, which a competent design would avoid. The
  UT3232's 5 V-tolerant *driver* inputs allow 3.3 V logic with a 5 V supply,
  but the *receiver* output would still be 5 V.
- So 3.3 V is very likely. 5 V cannot be ruled out without a meter: a cheap
  design could rely on the ESP32's clamp diodes, or put a divider on the RX
  line that we haven't seen.

### 3.3 Baseline protection (pad 7 = 3.3 V)

Per channel:

```
dongle pad 9 (or 10) ──[R1 10 kΩ, at the pad]──────── 30 AWG, twisted with GND ──────┬── XIAO GPIO1 (or GPIO2)
                                                                                      ├── C1 100 pF C0G → GND   (optional, do not fit by default)
                                                                                      └── R2 100 kΩ → XIAO 3V3   (optional)
```

- **XIAO-side fault protection (optional):** R1 sits at the pad, so a wire
  fault at the XIAO end (for example a tap wire touching the 12 V lead) would
  hit GPIO1/2 directly. Either add **1 kΩ in series at the XIAO end** (this has
  no effect on timing or levels), or route the 12 V pair physically apart
  from the signal twist. Doing both is best.

- **R1 = 10 kΩ, placed at the dongle pad end.** It protects the *bus* from
  anything that happens on the wire or the XIAO: a pinched wire, a short to 5 V
  or 12 V, or a GPIO misconfigured as an output. A 1/8 W axial resistor can be
  dead-bugged straight onto the pad with heat-shrink over it.
- **Passive-only guarantee, quantified [I from V data]:** in the worst case a
  misconfigured XIAO output fights the line through 10 kΩ, so it can inject
  at most 3.3 V / 10 kΩ = **0.33 mA**. The UT3232 spec (VOH ≥ VCC−0.6 at 1 mA)
  bounds R1OUT's output resistance at ≲ 600 Ω, so the dongle's RX line moves by
  **≤ ~0.2 V**: still a valid high (and a valid low the other way). Pad 10 is
  driven by an ESP32 GPIO (tens of mA), so its shift is smaller still. **No XIAO
  configuration can corrupt the dongle↔inverter link.** If one-way isolation is
  wanted in hardware rather than by arithmetic, use the buffer in 3.4.
- **RC timing [I]:** C = 2 pF (pin) + about 5–10 pF (30 AWG run of ≤ 15 cm plus
  the pad) ≈ 12 pF, so τ = 10 kΩ × 12 pF = **0.12 µs**, against a **104 µs**
  bit. The edge delay is under 0.5 % of a bit and irrelevant.
- **Optional C1 = 100 pF C0G** gives τ = 1 µs. That rejects the < 0.5 µs glitches
  seen in the Saleae captures (which may be a probe/ground-clip artifact),
  costs about 1 % of a bit, and does not depend on the UART glitch-filter
  semantics. Leave the footprint/pad space but do not fit it unless the decode
  shows framing errors.
- **Do NOT enable the ESP32-S3 internal pull-up with a 10 kΩ series resistor
  [I from V data].** The pull-up is 45 kΩ typical, and process spread could
  bring it near 30 kΩ. When R1OUT is low (~0.05 V at this light load) the pin
  would sit at about 0.05 + 3.3 × 10/(10+30…45) ≈ **0.65–0.88 V**, at or above
  VIL max (0.825 V). Use **R2 = 100 kΩ external** instead (low level ≈ 0.35 V),
  only if you want a defined idle-high when a wire comes off. Firmware should
  configure the RX pins with no internal pulls.
- **Bus loading [I from V data]:** with the XIAO input at ≤ 50 nA leakage, the
  only DC load added to R1OUT is the optional R2 path (≤ 30 µA through
  110 kΩ). That is negligible against the UT3232's 1–1.6 mA rated drive. The
  existing load is the dongle's ESP32 RX input, also high-impedance.
- **Clamp diodes:** none are needed. The ESP32-S3's internal ESD structures,
  behind 10 kΩ, see at most (5.5 − 3.6)/10 kΩ ≈ 0.19 mA even with a 5 V
  source. Espressif does not publish an injection-current limit, so **do not
  rely on this as a design mode**. It is only a fault margin. If pad 7 is 5 V,
  use 3.4.
- **Unpowered XIAO / powered dongle [I]:** the line high (3.3 V) feeds the
  XIAO's 3V3 rail through R1 and the input clamp: ≤ 0.3 mA, harmless, and too
  small to bring the XIAO up. Both are normally powered from the same 12 V, so
  this occurs only transiently.

### 3.4 If pad 7 measures 5 V (or for hard one-way isolation)

**Preferred: SN74LVC2G17** (dual Schmitt-trigger buffer, SOT-23-6/SC70-6),
powered from the **XIAO 3V3** pad, with a 100 nF decoupler.
[TI SN74LVC2G17](https://www.ti.com/product/SN74LVC2G17) [V]: VCC 1.65–5.5 V,
"Inputs Accept Voltages to 5.5 V", "Ioff Supports … Partial-Power-Down Mode
Operation and Back-Drive Protection", Schmitt inputs, −40…125 °C.

```
pad 9  ──[10 kΩ at pad]── A1 ┐ SN74LVC2G17 (VCC = XIAO 3V3) ┌ Y1 ──[100 Ω]── GPIO1
pad 10 ──[10 kΩ at pad]── A2 ┘                              └ Y2 ──[100 Ω]── GPIO2
```

- One package covers both taps. The buffer outputs can only drive the XIAO
  side, so even a misconfigured GPIO can never reach pads 9/10. Ioff keeps an
  unpowered XIAO from loading the bus.
- Its Schmitt input plus the optional 100 pF on the A side also deals with the
  glitches.

**Fallback: resistor divider** at the XIAO end. Keep R1 = 10 kΩ at the pad and
add **R3 = 22 kΩ from GPIO to GND**. With R1OUT high between VCC−0.6 = 4.4 V and
5.0 V, the pin sees 3.03–3.44 V: above VIH (2.475 V) and below the 3.6 V
maximum. Thevenin source ≈ 6.9 kΩ, so the timing is still negligible. Do not
fit R2 with this option.

---

## 4. Power: 12 V → 5 V

### 4.1 Load budget [V data → I totals]

| Rail | Typical | Peak | Basis |
|---|---|---|---|
| ESP32-S3 3.3 V | ~80–100 mA (STA connected, modem idle between bursts) | **340 mA** (802.11b 1 Mbps @ 21 dBm, 100 % duty) | Datasheet Table 5-7 [V]. Seeed lists Plus "Wi-Fi active 81 mA" [V] |
| + octal PSRAM, flash, LED, margin | | ~+60–110 mA | [I] |
| **3V3 budget** | | **≈ 450 mA** | under the board's 600 mA buck limit |
| At the XIAO 5V pad (SGM6029 η ≈ 90 %, VIN ≈ 4.3 V after D2) | ~100 mA | **≈ 390 mA** | [I] |
| At 12 V (5 V regulator η ≈ 85 %, plus the series Schottky loss) | ~50 mA (~0.6 W) | **≈ 190 mA (~2.3 W)** | [I] |

Wi-Fi TX bursts last milliseconds. Bulk capacitance carries the peak, so the
DB9 12 V sees closer to the average. A **configurable TX-power cap** (for
example 15 dBm) reduces the peak current (to roughly 250 mA at 3.3 V [I]) and
also coupling into the dongle's radio.

### 4.2 "Pololu D45V5F5" exists [V]

[Pololu #5433, D45V5F5](https://www.pololu.com/product/5433): 5 V, input
5.2–65 V, "Typical max output current 500 mA", up to 700 mA depending on
input/output (graph), Iq < 0.2 mA, 1.1 MHz, 7.6 × 11.4 × 2.8 mm, 0.4 g,
VIN/GND/VOUT only. No reverse-voltage protection. Pololu warns that LC spikes
above 65 V will destroy it and suggests a 33 µF electrolytic at VIN.

The ≈ 390 mA 5 V peak is ~78 % of its typical rating, which is workable but
thin at elevated temperature.

### 4.3 Recommendation: **Pololu D24V10F5** [V]

[Pololu #2831, D24V10F5](https://www.pololu.com/product/2831): 5 V ±4 %, input
**5.1–36 V**, **1 A** typical max continuous, Iq ≈ 200 µA, 500 kHz, efficiency
80–93 %, **18 × 13 × 3.5 mm**, 0.1" pins **PG, SHDN, VIN, GND, VOUT**.
SHDN has an internal 100 kΩ pull-up to VIN, so it can be left open. PG is open
drain and low during the 2 ms soft-start. No reverse protection. For inputs
above 20 V or long leads, Pololu recommends ≥ 33 µF/≥ 50 V electrolytic at
VIN.

Why this part: it has 2.5× margin on the peak, the soft start limits inrush on
the inverter's 12 V, and it fits easily in the dongle case (the comparable
4G dongle housing is 78.5 × 153 × 34.5 mm). Its 36 V ceiling is 3× nominal.
With the TVS below clamping well under 36 V, transient headroom is adequate
for an inverter-internal 12 V rail, which is a regulated SMPS output rather
than an automotive bus [I]. PG is optional (it could go to a spare GPIO, D3,
through a 10 kΩ pull-up to 3V3, as a "supply OK" health bit).

If space is critical, use the D45V5F5 (65 V input, half the area) with the
same protection and the 100 µF output bulk below.

### 4.4 Protection and bulk capacitance (12 V side, in order from the DB9)

| Ref | Part (example) | Purpose |
|---|---|---|
| F1 | PTC, **Ihold ≈ 0.3 A, Itrip ≈ 0.6 A, Vmax ≥ 30 V**, 1206/1812 (e.g., Bourns MF-MSMF030 class; check the datasheet's derating at 60 °C) — or a 0.5 A 63 V 1206 fast fuse (Littelfuse 466-series) | Protects the inverter's 12 V rail and the 30 AWG tap wire from a short. **Fit it at the DB9 tap end** |
| D1 | **SS14** (1 A, 40 V Schottky), SMA | Reverse polarity. ~0.3 V drop at 0.2 A |
| TVS1 | **SMAJ18A** (18 V standoff, ~20 V breakdown, 29.2 V clamp at Ipp) | Clamps spikes below the D24V10F5's 36 V |
| C1 | 33 µF, ≥ 50 V aluminium electrolytic (6.3 × 5.4 mm SMD, 105 °C rated) | Pololu's own recommendation; damps LC ringing |
| C2 | 100 nF / 50 V X7R | HF bypass at VIN |

5 V side:

| Ref | Part | Purpose |
|---|---|---|
| D2 | **Low-Vf Schottky: SS34 or PMEG3020-class (≈0.3 V at 0.4 A)**, or a TI **LM66100** ideal diode | Blocks backfeed between USB VBUS and the regulator (section 1.4). Low Vf matters: at the 390 mA peak an SS14 (~0.45 V) plus the on-board LMBR4010 (~0.4 V) leaves only ~4.0–4.1 V at the SGM6029 |
| C3 | 100 µF, 6.3–10 V low-ESR polymer/tantalum, **at the XIAO 5V pad** | Carries the Wi-Fi TX bursts |
| C4 | 10 µF X5R, at the 5V pad | HF |

Mount the regulator next to the XIAO so the 5 V link is 1–3 cm long. Only the
12 V pair runs from the DB9.

### 4.5 Rule for bench work

Never plug in USB while the XIAO is installed and inverter-powered, unless you
go through a **USB isolator** (ADuM3160/ADuM4160 class). D2 removes the
backfeed path, but the ground-reference issue remains (section 5.3). Use OTA
in service.

---

## 5. Inverter-side power (DB9)

### 5.1 What is published

- **[V]** Sol-Ark's own 4G dongle datasheet (SA-DGL-4G, PS-00043 Rev 1,
  2026-05-19,
  <https://sol-ark.com/wp-content/uploads/2026/05/4G_Dongle_Datasheet_Rev1.0_PS-00043_19-May-2026.pdf>)
  says: "Supply Voltage 12 V DC, powered directly from the inverter's DB9
  communication port", "Power Consumption < 2 W typical", "Main Connector DB9
  connector (Power & RS-232)", and operating temperature −20 °C to +55 °C. It
  lists compatibility with 12K-2P-LL, **15K-2P-LV**, 18K-2P-LV, 30K-3P, 60K-3P.
- **[V]** The 15K-2P-N manual
  (<https://www.sol-ark.com/wp-content/uploads/2024/06/SK140-0001-002-15K-2P-N-EN-Manual.pdf>)
  says the dongle plugs into "the Sol-Ark DB-9 port" with two M4 screws. **It
  publishes no DB9 current rating.** The "12Vdc (−3%) … 100mA max, 12VDC,
  1.2W" figure in the same manual is for **terminal pins 15/16 (the RSD
  transmitter supply), not the DB9**. Do not conflate them. The model names
  also differ (15K-2P-N in the manual, 15K-2P-LV on the 4G sheet). **[M]**
  Confirm your model from the nameplate.
- **[I]** The DB9 pinout is from a **third-party** Sunsynk/Deye guide
  (<https://kellerza.github.io/sunsynk/guide/wiring>): pin 2 TX, pin 3 RX,
  pin 5 GND, pin 9 Vdc (typically 12 V). It is not a Sol-Ark document.
  `dongle_serial.jpg` appears to show only four populated DB9 pins, which
  fits 2/3/5/9. **[M]** Confirm on the bench.
- Aside **[V]**: the 15K manual itself publishes the dongle's fixed default
  hotspot password (section "STEP 3 (alternate method)"). This confirms the
  findings doc's suspicion that the always-on AP is guessable. The value is
  not repeated here.

### 5.2 Headroom [I]

Sol-Ark's port must at least supply its own 4G dongle at < 2 W typical (and
LTE Cat-1 transmit peaks above that). The Wi-Fi/Ethernet dongle (ESP32 + LAN8720
+ RS-232) likely draws ~1 W [I, **M**]. Adding the XIAO's ~0.6 W average and
~2.3 W peak (buffered by C3) makes ≈ 1.6 W average, which is within what the
4G dongle implies the port can source. But **the port's rating is unknown**.
This is the main residual risk. Measure it (checklist): the 12 V no-load
voltage, the sag with a 100 Ω (120 mA, 1.44 W) dummy load, and the sag with the
dongle plus XIAO running a TX-heavy test.

### 5.3 Grounds [I, M]

- **In service there is no ground loop.** The XIAO's only connections are to
  the dongle: 12 V/GND from the DB9 solder joints, and the signals plus GND
  from the header. All of these sit on the dongle PCB's single ground. Run
  the power GND from DB9 pin 5 (per the third-party pinout) to the regulator.
  Run a signal GND from **pad 6** twisted with the two tap wires. Those two
  grounds meet on the dongle board and on the XIAO, inside a loop of a few
  cm², which is acceptable. **[M]** Confirm DB9 GND ↔ pad 6 continuity
  (< 1 Ω).
- **On the bench (USB connected) there is a loop:** laptop ground → XIAO →
  dongle → inverter comms ground. Whether the inverter's comms ground is
  isolated from battery negative or PE is **unknown**. Use a USB isolator or
  a battery-only laptop that is not on a charger.

---

## 6. Environment

### 6.1 Temperature [V]

| Item | Range | Source |
|---|---|---|
| ESP32-S3R8 (octal PSRAM) ambient | **−40 … 65 °C**; **85 °C if PSRAM ECC is enabled** (usable PSRAM −1/16) | Datasheet Table 1-1 and footnote 3 |
| XIAO ESP32S3 (board) | −20 … 65 °C | Seeed wiki spec table |
| Sol-Ark 15K ambient | −25 … 55 °C, derating above 45 °C | 15K manual, General Data |
| Sol-Ark 4G dongle operating | −20 … 55 °C | SA-DGL-4G datasheet |
| SN74LVC2G17 | −40 … 125 °C | TI |

- Datasheet footnote 3: "Ambient temperature specifies the recommended
  temperature range of the environment immediately outside an Espressif chip."
  Inside a closed plastic dongle housing, with the dongle's ESP32, PHY and
  regulator dissipating ~1 W, mounted on an inverter in sun, the local air can
  plausibly run 10–15 °C above the inverter's 55 °C ambient [I]. **That is at
  or above the 65 °C limit.**
- **Requirement:** enable PSRAM ECC (`CONFIG_SPIRAM_ECC_ENABLE=y`, ESP32-S3
  octal only, reserves 1/16 of PSRAM). It is off by default and must be set
  manually in sdkconfig
  ([esp32.com thread](https://esp32.com/viewtopic.php?p=127039),
  [ESPHome psram docs](https://esphome.io/components/psram/)) [I: these are
  secondary sources; check the Kconfig of the pinned IDF]. This raises the
  chip limit to 85 °C. The board-level 65 °C rating from Seeed stays as a
  residual risk [I]: it is probably driven by the PSRAM and the charger, not by
  passives.
- Publish the ESP32-S3 die temperature (internal sensor) in
  `solark/<id>/health`. Cap the Wi-Fi TX power (configurable). **[M]** Log the
  in-housing temperature on a hot afternoon before final install.
- Cold: −20 °C (XIAO) versus −25 °C (inverter). This is only marginal in very
  cold climates.
- Electrolytics: use 105 °C-rated parts. The TVS, Schottkys and PTC are all
  fine at 85 °C, but **the PTC's hold current derates about 20–30 % at 60 °C**
  (check its datasheet), which is why the hold rating is 0.3 A.

### 6.2 RF [I]

- The dongle's housing is plastic (Sol-Ark's 4G dongle uses polycarbonate; the
  Wi-Fi dongle is presumably similar), and the dongle's own PCB antenna works
  from inside it. So an antenna **inside the same housing** should see similar
  propagation. The inverter's metal chassis is behind the dongle and shadows
  one hemisphere.
- Use an **adhesive 2.4 GHz FPC antenna on a U.FL pigtail** (the one shipped
  with the XIAO, or an equivalent ~50 mm FPC). Stick it to the inside of the
  housing at the end **farthest from the DB9 shell and the inverter chassis**.
  Keep it **≥ 3 cm from the ESP32-SOLO-1's antenna** (the left end in the
  photo). Avoid running it parallel to the ESP32-SOLO-1 antenna.
- Fit an external RP-SMA bulkhead only if RSSI is poor (worse than about
  −75 dBm). It breaches the housing's weather sealing.
- **Coexistence:** both radios will normally join the same AP and channel, so
  802.11 CSMA arbitrates. The XIAO publishes roughly every 10 s, so contention
  is negligible. Near-field coupling at a few cm can desensitise the other
  receiver during TX. Mitigations: separation, a TX-power cap, **BLE
  disabled**, and **no SoftAP on the XIAO** after provisioning (all
  configurable).

### 6.3 EMI from the inverter [I]

- The tap wiring lives entirely inside the dongle (≤ 10–15 cm), not in the
  inverter's power compartment. Twist each signal with a ground wire (or twist
  resp, req and GND together), keep runs short, and route them away from the
  dongle's DC-DC inductor and the RJ45/Ethernet magnetics.
- The 10 kΩ at the pad, plus the optional 100 pF and the Schmitt buffer, give
  a 1 µs low-pass and hysteresis. The UART samples mid-bit (≈ 52 µs into a
  104 µs bit), so nanosecond-scale switching spikes do not corrupt bytes, and
  CRC catches the rest.

---

## 7. Wire: Jonard Kynar 30 AWG

- **[V]** (Jonard/OK Industries KSW spec sheet and Jonard product listings):
  solid, **silver-plated OFHC copper**, Kynar (PVDF) insulation rated **105 °C**,
  UL 1423 (0.004" wall) at 30 AWG, about 0.52 mm OD. The spec sheet says
  wire-wrap wire is "**not voltage rated**". Data sheet (as found by web search; it returned
  403 to a scripted fetch, so open it in a browser):
  <https://jonard.com/sites/default/files/product_files/Data%20Sheet%20-%20Kynar%C2%AE%20Wire_54.pdf>.
- **[I] Resistance:** 30 AWG copper ≈ 0.34 Ω/m (standard AWG table). For a
  round trip of 2 × 10 cm at a 0.4 A peak, the drop is ≈ 27 mV, so it is
  electrically fine even for power. For the 12 V run at ≤ 0.2 A, the drop is
  negligible. Commonly quoted chassis-wiring ampacity for 30 AWG is ~0.5–0.8 A.
  F1 (0.3 A hold) protects it.
- **Recommendation:**
  - Signals (pads 9 and 10, pad 6 GND): 30 AWG Kynar, twisted.
  - 12 V and GND from the DB9 to the regulator: 30 AWG is acceptable with F1
    at the tap end. **Use two strands in parallel**, or 26–28 AWG stranded
    silicone if available, for mechanical robustness rather than for current.
  - 5 V regulator → XIAO: as short as possible (1–3 cm). Two strands or a
    thicker wire.
- **Soldering:** PVDF softens around 170 °C, but it tolerates brief iron
  contact much better than PVC. Strip with a wire-wrap stripper (no nicks:
  solid 30 AWG breaks at a nick). Use 320–350 °C with brief contact, and
  pre-tin both the wire and the pad. Do **not** solder to the ESP32-SOLO-1
  module's castellations. Use the carrier's header pads and the DB9 solder
  joints.
- **Strain relief (essential with solid wire):** anchor every wire within
  ~5 mm of its joint with Kapton tape plus a dab of hot glue or UV-cure
  adhesive. If silicone is used, it must be **neutral-cure RTV, never
  acetoxy**, which releases acetic acid and corrodes copper. Secure the XIAO
  and the regulator to the housing or PCB with double-sided foam tape so that
  the joints carry no load. Insulate the dead-bugged 10 kΩ resistors with
  heat-shrink.

---

## 8. Block schematic (for the schematic/BOM agent)

```
DB9 pin 9 (+12 V) [M] ──F1 PTC 0.3 A──D1 SS14──┬──────────┬──────────┬── VIN  Pololu D24V10F5
                                               TVS1       C1 33µ/50V  C2 100n       │ SHDN: n.c.   PG: n.c. (or → D3/GPIO4 + 10k to 3V3)
DB9 pin 5 (GND)   [M] ─────────────────────────┴──────────┴──────────┴── GND ───────┤
                                                                         VOUT ─D2 SS34─┬── C3 100µ ── C4 10µ ── XIAO 5V pad
                                                                                       └─────────────────────── XIAO GND
Header pad 9  (R1OUT) ──R1 10k (at pad)── twisted ── XIAO D0/GPIO1   [opt C 100p→GND, opt R 100k→3V3]
Header pad 10 (T1IN)  ──R1' 10k (at pad)─ twisted ── XIAO D1/GPIO2   [opt C 100p→GND, opt R 100k→3V3]
Header pad 6  (GND)   ─────────────────── twisted ── XIAO GND
(If pad 7 = 5 V: insert an SN74LVC2G17 at the XIAO end, VCC = XIAO 3V3, 100 nF, 100 Ω series to the GPIOs; or 22k GPIO→GND dividers.)
U.FL ── FPC 2.4 GHz antenna (inside the housing, far end)
```

BOM summary: XIAO ESP32S3 Plus ×1; Pololu D24V10F5 ×1; PTC 0.3 A/≥30 V ×1;
SS14 ×1 (D1); SS34/PMEG3020 or LM66100 ×1 (D2); SMAJ18A ×1; 33 µF/50 V electrolytic ×1; 100 nF/50 V ×1; 100 µF/10 V
polymer ×1; 10 µF/10 V X5R ×1; 10 kΩ 1/8 W axial ×2. Optional: 100 pF C0G ×2,
100 kΩ ×2, 1 kΩ ×2 (XIAO-end series), SN74LVC2G17 + 100 nF + 100 Ω ×2 (or 22 kΩ ×2), FPC U.FL antenna,
foam tape, Kapton, heat-shrink.

---

## 9. Measure before connecting

Do all of these with the dongle powered from the inverter, and with nothing
connected to pads 9/10 yet.

1. **Pad 7 (UT3232G VCC) to pad 6:** 3.3 V → baseline (3.3). About 5 V → fit
   the 3.4 buffer or divider. Anything else → stop.
2. **Pads 9 and 10 idle voltage** (expect ≈ pad 7). Scope the levels (VOH and
   VOL) during traffic.
3. **DB9 pin identification:** which pins are populated, and which pin carries
   12 V relative to which ground (expected 9 and 5, from a third-party
   source). Check polarity.
4. **DB9 12 V:** no-load voltage; with a 100 Ω / 2 W dummy load in parallel
   (sag); and the ripple on a scope. Record the min and max.
5. **Continuity:** DB9 GND ↔ header pad 6 (< 1 Ω). Also DB9 GND ↔ RJ45 shield
   and ↔ the inverter chassis, for information about the comms ground.
6. **Dongle input path:** does the dongle have its own fuse, diode or
   regulator after the DB9 12 V pin? Decide the tap point (before its fuse is
   preferable, so a fault in our circuit doesn't kill the dongle; F1 protects
   ours).
7. **Dongle current draw** at 12 V (ammeter in series in a DB9 breakout, if
   you have one). This is the baseline for the budget.
8. **XIAO bench checks:** continuity from the 5V pad to the USB-C VBUS pin
   (expect a short, confirming section 1.4). The chip variant is already
   established by esptool (S3, 8 MB AP 3.3 V PSRAM → S3R8). Confirm the U.FL antenna is attached.
9. **Regulator bench test** before install: from a 12 V bench supply through
   F1/D1/TVS, check 5 V at the XIAO pad (~4.6–4.7 V after D2), and the 3V3 pad
   under a Wi-Fi TX test (≥ 3.2 V, no brown-out resets).
10. **Space:** measure the free volume inside the dongle housing (XIAO
    21 × 17.8 mm, D24V10F5 18 × 13 × 3.5 mm) and the clearance to the
    ESP32-SOLO-1 antenna.
11. **Thermal:** temperature inside the closed housing on the inverter on a
    hot day (a thermocouple or a logging sensor), before you rely on the
    65 °C (or 85 °C with ECC) limit.

## 10. Verified vs inferred summary

**Verified (primary source or esptool on the user's board):** chip ESP32-S3
QFN56 rev v0.2, 16 MB quad flash at 3.3 V (PY25Q128HA), 8 MB embedded AP 3.3 V
PSRAM, USB-Serial/JTAG mode;
the pad→GPIO map; the 5V pad = USB VBUS with Schottky D2 after it; buck
SGM6029 at 600 mA; U.FL-only antenna; USER_LED GPIO21 active-low; BOOT = GPIO0;
strapping pins; three UARTs; any-GPIO input routing; RX TOUT in bit times
(10-bit field, reset 10); RX glitch-filter register; autobaud is pulse-width
measurement with software computing the rate; ESP32-S3 VIH/VIL/CIN/abs max;
340 mA Wi-Fi TX peak; S3R8 65 °C / 85 °C with ECC; UT3232 receiver drive and
3.0–5.5 V supply; D45V5F5 and D24V10F5 specs; SN74LVC2G17 5.5 V-tolerant
inputs and Ioff; Sol-Ark dongle 12 V from the DB9, < 2 W; the 100 mA figure is
for the RSD terminal, not the DB9; Kynar wire at 105 °C, not voltage rated.

**Inferred:** the ESP32-S3R8 variant (octal PSRAM, so GPIO33–37 are
reserved), deduced from the esptool readout and the ordering info; pad 7 = 3.3 V; the DB9 pinout
(2/3/5/9); the DB9 current capacity; DB9 GND = pad 6; the load-budget totals;
the in-housing temperature rise; RF placement and coexistence; the
glitch-filter time unit and scope; ESP-IDF API exposure of autobaud and
bit-time TOUT; 30 AWG resistance and ampacity figures.
