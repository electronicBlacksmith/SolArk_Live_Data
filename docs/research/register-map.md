# Sol-Ark 15K Modbus register map: research (2026-10-12)

Scope: the holding registers the Sol-Ark dongle reads over the passive tap
(fc03 blocks 0-29, 15, 20-24, 25-58, 59-124, 150-199, 200-299, 300-315,
312-319, 320-419 and 433-487), plus the fc16 clock write and the cloud's
non-periodic items 42x2 and 44x4. See `docs/serial-link-findings.md` and
section 4 of `docs/plans/2026-10-11-xiao-firmware-design.md`.

Provenance tags are used throughout and kept strictly separate:

| Tag | Meaning |
|---|---|
| **[SA14 p.N]** | **Official Sol-Ark document**: "Modbus RTU Protocol, Sol-Ark Hybrid Inverters: 5k, 8k, 12k, 15k", V1.4, page N |
| **[SAB p.N]** | Official Sol-Ark battery integration guide (not a register map) |
| [DY118 p.N] | Deye "Modbus RTU Protocol" V118 (Deye, not Sol-Ark) |
| [KZ] | kellerza/sunsynk (community) |
| [HAS] | davidrapan/ha-solarman `deye_hybrid.yaml` (community) |
| *observed* | Our scrubbed captures (`solark-telemetry-data/captures/20261011-191812`, 900 s, and `...-193820-unplug-replug` for the boot-only read) |
| *inferred* | Our reasoning and not verified against the MySolArk app |

Nothing here is verified against the MySolArk app yet. Every map entry stays
`verified: false` until that comparison is made.

## 1. Sources

### Official Sol-Ark

| Document | Revision / date | Where | Models | Notes |
|---|---|---|---|---|
| Modbus RTU Protocol, Sol-Ark Hybrid Inverters (PDF title "Modbus for Sol-Ark Inverters V1.4 (Public Release)") | **V1.4, 2023-10-13** ("Added registers for total energy data, misc. clarifications"). PDF created 2023-10-23, modified 2024-04-04. 10 pages. sha256 `48a27a55942fa4f1a5bf56122baf1b3958c93b6c9380b5375789e74429c82076` | Mirror: https://github.com/chuyskywalker/solark-esphome/blob/main/Modbus%20Sol-Ark%20V1.4%20(Public%20Release).pdf | 5K, 8K, 12K, **15K** (one shared map with "15K only" notes) | The repo README says Sol-Ark support emailed it on 2025-01-15 and **said it was the latest**. Not copied into this repo. |
| Same document, revision history (SA14 p.1) | V1.0 2021-03-31 (initial); V1.1 2021-04-15 (disclaimer and notes); V1.2 2021-07-28 (cleanup); **V1.3 2022-06-29 / 2022-09-15 ("Added Sol-Ark 15K")**; V1.4 2023-10-13 | — | — | Only V1.4 was obtained. |
| "Sol-Ark ModBus V1.1" | V1.1 (by title) | https://www.scribd.com/document/899282857/Sol-Ark-ModBus-V1-1 | unknown | **Not read** (Scribd preview only). A search snippet called it "confidential under NDA"; the fetched page showed no such marking. Unverified. |
| "Modbus Sol-Ark V1.1 (Public Release).pdf" attachment | V1.1 | DIY Solar Power forum thread https://diysolarforum.com/threads/sol-ark-inverter-monitoring.23717/ | unknown | **Not read** (HTTP 403). Known from a search snippet only. |
| Battery Integration Guide, Low Voltage 48V (SK140-0026-001), "solark_inverter_battery_communications_installation_guide_v3.1.pdf" | 2024 | https://www.sol-ark.com/wp-content/uploads/2024/06/solark_inverter_battery_communications_installation_guide_v3.1.pdf | 12K/15K and others | Not a register map. It names the firmware format: "**Comm v143F** or greater", "latest primary and follower MCU versions" (SAB pp. 3, 8, 17, 18, 20, 21). |
| 15K / 12K installation manuals | various | e.g. https://sol-ark.com/wp-content/uploads/2024/06/SK140-0003-002-12K-2P-N-EN-Manual-1-1.pdf | — | Per search results (not opened): the Modbus map is "available upon request for READ operations only". |
| Sol-Ark software-update page | — | https://www.sol-ark.com/software-updates/ | — | A search snippet said the 15K-2P's current versions are **MCU 7228 / COMM 1452**. The fetched page did not show this, so it is **unverified**. |

**What V1.4 covers:** the serial (3-7), 60-114 (energy, temperatures,
faults, PV V/I), 150-196 (real-time power) and the fault table. It does
**not** cover 0-2, 8-58, 115-124, 197-487, writes, or the clock.

V1.4 disclaimers (SA14 p.2, p.5): the map is for the third-party RS-485 port.
"The inverter only supports read operations" (fc03 only). Slave ID is fixed
at 0x01. "Reserved... and unsupported registers are all filled with 0x00."
The fc16 clock write we observed on the *dongle* link is outside that
document's scope. It does not contradict it.

### Deye and community (not Sol-Ark)

| Source | Revision | URL | Use |
|---|---|---|---|
| Deye "Modbus RTU Protocol" (Chinese/English) | **V118** (history to V117, 2021-04-08). PDF created 2022-01-23, 43 pp. sha256 `7444d2ef...6b3717` | https://github.com/user-attachments/files/16597960/Deye.Modbus.protocol.V118.pdf (the reference cited by ha-solarman `deye_hybrid.yaml`) | The only source for 0-58 and 197-437. Page map: 0-24 p.5-6, 25-58 p.7-9, 59-124 p.9-15, hybrid 150-196 p.18-21, 200-330 p.21-28, 331-391 p.29-30, 392-437 p.30-32. |
| kellerza/sunsynk `definitions/single_phase.py`, `single_phase_16kw.py`, `identity.py`, `sensors.py`, `rwsensors.py` | main @ `8c7997e` (2026-08-28) | https://github.com/kellerza/sunsynk/tree/main/src/sunsynk/definitions | Sunsynk/Deye single-phase sensors, the SystemTime codec, and the device-type table. A negative factor in kellerza means "signed", not "inverted". |
| davidrapan/ha-solarman `inverter_definitions/deye_hybrid.yaml` | main (fetched 2026-10-12) | https://github.com/davidrapan/ha-solarman/blob/main/custom_components/solarman/inverter_definitions/deye_hybrid.yaml | Identity and firmware-version register groupings, settings 200-326. |
| chuyskywalker/solark-esphome `doc.md` | 2025-2026 | https://github.com/chuyskywalker/solark-esphome | A markdown transcription of SA14. Same register set (checked). |
| aneisch/home-assistant-config `extras/esphome/sol-ark.yaml` | master | https://github.com/aneisch/home-assistant-config/blob/master/extras/esphome/sol-ark.yaml | Sol-Ark ESPHome user config. 32-bit totals are `U_DWORD_R` (low word first), which agrees with our finding. |
| pbix/HA-solark-PV, aaronmelton/solark_monitor | — | GitHub | Listed only. Not mined. |
| StephanJoubert/home_assistant_solarman, Solar Assistant, generic ESPHome Deye configs | — | — | **Not consulted.** Solar Assistant is closed source. StephanJoubert's `deye_hybrid.yaml` is the predecessor of the ha-solarman file above. |
| Forum lineage threads | — | https://diysolarforum.com/threads/are-eg4-and-sol-ark-inverters-rebranded-deye-inverters.98697/ , https://diysolarforum.com/threads/sol-ark-vs-deye-everyone-claims-they-are-the-same.85095/ | Claims only (search snippets). |

No community source defines registers 438-487. Deye V118 defines 433-437,
but those definitions do not fit our values (section 3).

## 2. Lineage of the 15K

- **Official:** Sol-Ark publishes **one** register map for the 5K, 8K, 12K
  and 15K. The 15K was added in V1.3, and only PV3 (113/114/188) and "90
  not used in 15K" are marked 15K-specific (SA14 p.1, p.7, p.9). The
  register-map lineage question is therefore answered by Sol-Ark itself:
  the 15K uses the same map.
- **Observed and inferred:** the wire matches Deye V118 closely outside
  SA14's coverage too:
  - device type `0x0003` (kellerza: "single-phase hybrid")
  - protocol `0x0201`
  - rated power 16/17 = 15000.0 W
  - 18 = `0x0301` (3 MPPT, 1 phase)
  - the clock at 22-24
  - Deye's settings block layout (285 = 60 Hz, 286 = 120/240 split-phase,
    289/290 = 62.00/57.00 Hz)
  - Deye's California ride-through block (331-365), which holds
    grid-code style trip points for 240 V / 60 Hz, similar to IEEE
    1547-2018: 288/264/211.2 V; 62.00/61.50/58.50/57.00 Hz; clearing
    times at 0.01 s of 0.16, 13, 21 and 2 s, and 299 s

  So the 15K firmware is Deye-protocol-derived. The few misfits (20, 26,
  28-30, 34, 117/118, 185, 433+) are Sol-Ark or newer-firmware deviations.
- **Manufacturing claims** ("Deye makes Sol-Ark inverters", "Sol-Ark has
  exclusive US distribution of white-labelled Deye") come from forums and
  resellers only. They are not used as evidence here.
- **Scale differs from the Deye 16 kW:** kellerza's `single_phase_16kw`
  scales 169/172 by x10, and ha-solarman uses `scale: [1,10,10]` by model.
  **On our 15K the grid/load powers are x1** (observed: 178 − 175 == 169
  exactly, in every snapshot). Do not import x10.

## 3. Resolved questions

### (a) Firmware and protocol versions in 0-29 (for the change recorder)

The wire reads 0-18 every 30 s (block `0x00 x19`), and 0-29 once at boot.
So versions are visible continuously, not only at boot.

| Reg | Observed | Meaning | Evidence |
|---|---|---|---|
| 0 | `0x0003` | Device type, single-phase hybrid | KZ identity table. DY118 p.5 writes `0x0300`, so the byte order differs. |
| 2 | `0x0201` | Modbus protocol version 2.1 (hi.lo) | DY118 p.5 ("0x0102 = V1.2"); KZ |
| 11 | `0x1725` | Control-board **auxiliary** program version (probably Sol-Ark's "follower MCU") | DY118 p.5; HAS groups [13,12,11] as control-board FW. "Follower" is *inferred* from SAB p.3's "primary and follower MCU versions". |
| 13 | `0x7222` | Control-board (**MCU**) firmware | DY118 p.6; HAS. The format matches Sol-Ark's "MCU 72xx" (unverified snippet: current 7228). |
| 14 | `0x143F` | **COMM** board firmware | DY118 p.6; HAS. **Strong match:** Sol-Ark's own guide says "Comm v143F" (SAB p.3 and others). |
| 10, 12 | 0, 0 | Extra version fields (comm field 2, control field 2) | DY118 p.5 |
| 9 | `0x8000` | Chip type (low nibble 0) | DY118 p.5; HAS. The meaning of the high bit is unknown. |
| 16/17 | 18928 / 2 | Rated power, 0.1 W, lo/hi: (2·65536 + 18928)·0.1 = **15000 W** | DY118 p.6; KZ. *Observed*: this proves low-word-first. |
| 18 | `0x0301` | MPPTs = 3 (high byte), phases = 1 (low byte) | DY118 p.6; HAS |
| 3-7 | — | Serial (ASCII). **Never record.** | SA14 p.6 |

**Recorder recommendation:** watch {2, 11, 13, 14} as versions (also store
10 and 12) and {0, 9, 16, 17, 18} as identity. Display versions as 4-digit
hex (`7222`, `143F`). The inverter appears to be on an older firmware
(COMM 143F) than the unverified "current" 1452, so an update is likely at
some point. That is a good test of the recorder.

### (b) Registers 42-47

They are not in SA14. Per DY118 p.8:

| Reg | Meaning | Observed |
|---|---|---|
| 42 | Apparent-power regulation, 0.1 % | 0 |
| 43 | Switch on/off: 1 = on (HAS: on=1, off=2; KZ "Inverter enabled") | 1 |
| 44 | Factory-reset enable | 0 |
| 45 | Self-check time | 1 |
| 46 | Island-protection enable | 0 |
| 47 | Soft-start / MPPT-number (MI) | 0 |

All six are already read every 30 s inside the 25x34 block.

The cloud's non-periodic items are `op:3` = 42x2 (covers **on/off**) and
`op:2` = 44x4 (covers **factory reset**). *Inferred:* op 2/3 are probably
remote-command templates (remote power on/off and similar) rather than
reads. Treat any write to 42-47 as a high-alert event.

### (c) Register 90

**Resolved by the official doc:** "DC/DC Transformer temperature... **Not
used in 15K**" (SA14 p.7). Its raw value of 655 (−34.5 °C) is meaningless.
Use **91 (IGBT heat-sink)**, (raw − 1000) × 0.1 °C: *observed* 44.5-50.1 °C.

Two kellerza labels are also wrong for this unit:

- 92 is not "SD status". It is 0, the Deye V117 generator energy (low word).
  SD status is **94** (= 2000, "OK").
- 95 is not "environment temperature". It is 0, the generator energy (high
  word). As a temperature it would read −100 °C.

### (d) Clock at 22-24

The format is confirmed as `YY MM / DD hh / mm ss`, one byte each, with the
year offset from 2000:

- DY118 p.6: system time bytes 01-06, "based on the year 2000".
- kellerza `SystemTimeRWSensor`: same encoding, read and write.
- *Observed*: the fc16 write and the read-back.

The values are local wall time (findings doc).

*Observed, not explained:* in the unplug-replug capture, measured against
the folder timestamp, the read-back clock went:

- about **−13 s** at t = 15 s (before the unplug)
- already **−4.7 s** at the boot read (t = 76.7 s), **before any write**
- about **−5 s** after the fc16 write at t ≈ 87.6 s, which carried the
  exact wall time

The 900 s capture also showed about −13.6 s. So the offset changed by
about 8 s while the dongle was unplugged, with no write on the wire, and
the exact-time write did not remove the remaining ~5 s. 22-24 may
therefore not be a simple live clock: it could be a cached copy, or the
inverter may ignore small corrections. Capture-start uncertainty of a few
seconds (section 7) also contributes. None of this affects the format.

### (e) `inverter_protocol: 1D`

**Not resolved.** No official or community source mentions it. 0x1D (29)
does not equal any value in 0-29 (device type 0x0003, protocol 0x0201).
*Inferred:* it is most likely the dongle firmware's own profile ID for
"Deye/Sol-Ark single-phase hybrid", which selects the boot read and the
cloud poll template. It could also be the last register index of the
0-29 boot read, but that is a coincidence-level guess.

### (f) 32-bit values

**Low word first** everywhere. This is proven by 16/17 (rated power) and
agrees with SA14's "low word / high word" labels and aneisch's `U_DWORD_R`.
All are unsigned except 63/64, which SA14 labels "Signed int". *Observed*
totals:

| Lo / Hi | Meaning (SA14) | Decoded |
|---|---|---|
| 16 / 17 | Rated power (DY118), 0.1 W | 15000 W |
| 63 / 64 | Total active (grid-port) energy, signed, 0.1 kWh | 67 483.0 kWh |
| 72 / 73 | Total battery charge | 33 440.0 kWh |
| 74 / 75 | Total battery discharge | 32 161.1 kWh (unsigned; the raw low word 59467 is > 32767) |
| **78 / 80** | Total grid buy. **Not contiguous:** 79 is grid Hz. | 33 544.5 kWh |
| 81 / 82 | Total grid sell | 68.6 kWh |
| 85 / 86 | Total load energy | 100 971.9 kWh |
| 96 / 97 | Total PV energy | 76 499.5 kWh |

The totals are mutually plausible: charge > discharge, and PV + grid-buy
≈ load + losses.

**Schema correction:** the design's `words: 1|2` cannot express 78/80.
Use `registers: [lo, hi]` (an explicit list, low word first).

### (g) Split-phase, generator, and sign conventions

- **Official sign conventions (SA14 p.8-9):**
  - 169 grid total: **> 0 = BUY (import), < 0 = SELL**.
  - 166 gen/AC-coupled port: **+ = output as a load, − = AC input**
    (micro-inverter or generator feeding in).
  - 190/191 battery: "battery output power/current", signed, so
    **+ = discharge**. *Observed:* +3.9 kW at night with PV ≈ 0 and
    183 × 191 = 190 within 1 W.
- **L1/L2 (SA14 p.8):**

  | Quantity | L1 | L2 | Total |
  |---|---|---|---|
  | Grid V | 150 | 151 | 152 (L1-L2) |
  | Inverter V | 154 | 155 | 156 (L1-L2) |
  | Load V | 157 | 158 | — |
  | Grid I | 160 | 161 | — |
  | CT I | 162 | 163 | — |
  | Inverter I | 164 | 165 | — |
  | Load I | 179 | 180 | — |
  | Grid P | 167 | 168 | 169 |
  | CT P | 170 | 171 | 172 |
  | Inverter P | 173 | 174 | 175 |
  | Load P | 176 | 177 | 178 |

  *Observed:* 173 + 174 == 175 and 176 + 177 == 178 exactly.
- **Grid on this install (*observed*):** in every snapshot,
  **169 == 172 == 170 + 171**, and **178 − 175 == 169**. The internal
  grid-side 167/168 (about −10..−18 W and 0 W) do **not** sum to 169. This
  fits 244 = 2 (Deye p.23: limit control = zero export to the external CT
  / "limiter sensor"). In this configuration 169 reports CT power.
  Use 169 for `grid_w` (the official definition). Keep 167/168 and 172 as
  diagnostics.
- **Generator port:**
  - 166 power
  - 181 gen voltage L1-L2, 0.1 V (*observed* 7.8 V: no generator)
  - 195 gen relay (low nibble: 0 open, 1 closed, 2 no connection, 3 closed
    with gen on)
  - 196 gen frequency
  - 235 port mode (Deye/KZ: 0 gen input, 1 smart load, 2 micro-inverter
    input; *observed* 0)
  - 62, 92/95 gen energy (Deye V117)
  - Smart-load thresholds 236-239.

### (h) Writable settings the cloud might write (`writes` decoder labels)

From DY118, KZ and HAS. None are in SA14. Labels:

| Registers | Label | Alert |
|---|---|---|
| 22-24 | clock sync (verified pattern) | normal |
| 43 | inverter on/off | **high** |
| 44 | factory reset | **high** |
| 54 | EEPROM init (1 = control, 2 = comm board) | **high** |
| 55 | factory test commands | **high** |
| 20 | remote lock | high |
| 21, 25-53, 56-58 | grid / protection / regulation parameters | medium |
| 200-249 | battery and system: charge mode, voltages, Ah, currents 210/211/230, SOC thresholds 217-219, gen/grid charge 225-232, aux port 235, smart load 236-239, energy pattern 243, limit control 244, max sell 245, solar sell 247, TOU enable 248 | medium |
| 250-279 | time-of-use programs 1-6 (time, power, voltage, SOC, charge/mode/sell bits) | low (routine app edits) |
| 280-295 | peak shaving, grid mode/frequency/type, grid V/Hz limits, PF | medium |
| 320-330 | BMS limits, battery protocol (325), meter/CT (326, 327 CT ratio) | medium |
| 331-370 | grid-code ride-through, volt-var, freq-watt, volt-watt | medium |
| 416/417 | off-grid force / parallel config | high |
| anything else | unknown write | trigger recorder |

## 4. Corrections to the initial map (design section 4)

1. **Add PV3.** The 15K has three MPPTs (18 = `0x0301`; SA14: 188 PV3 W,
   113/114 PV3 V/A "15K only"). `pv_w` = 186 + 187 + 188 (189 is PV4 and
   always 0).
2. **Drop 90** on the 15K (SA14 p.7). Use 91 for the inverter temperature.
3. **Temperature formula:** (raw − 1000) × 0.1 °C. In our schema that is
   `scale 0.1, offset −100` (applies to 182, 91, and 319 if a BMS is ever
   present).
4. **32-bit registers need an explicit `[lo, hi]` list** (78/80 is
   non-contiguous). Word order is low-first.
5. **Grid power is x1 on the 15K**, not the x10 of Deye/Sunsynk 16 kW
   profiles.
6. **SD status is 94, not 92. 95 is not a temperature.**
7. **The 312-319 (10 s poll) BMS block is all zero.** 200 = 0 (lead-acid /
   voltage mode) and 325 = 0, so there is no BMS link on this install. SOC
   (184) is the inverter's own estimate. The design's map is unaffected.
8. Confirmations: 59 run state, 79 grid Hz, 150 grid V, 167, 169, 172, 175,
   178, 182, 183, 184, 186, 187, 190, 191, 192 and 193 all match the
   official definitions (SA14), with the stated scales and signs.

## 5. Proposed default register map (firmware config)

`value = raw × scale + offset`. `registers` is low-word-first.
Confidence levels:

- **H:** official SA14 definition and physically consistent in our data.
- **M:** official, or Deye with a clear physical check, but only seen at
  night or in a narrow range.
- **L:** Deye/community only, or conflicting.

| name | registers | signed | scale | offset | unit | conf. | source |
|---|---|---|---|---|---|---|---|
| soc | [184] | n | 1 | 0 | % | H | SA14 p.8 |
| battery_v | [183] | n | 0.01 | 0 | V | H | SA14 p.8 |
| battery_a | [191] | y | 0.01 | 0 | A (+discharge) | H | SA14 p.9 |
| battery_w | [190] | y | 1 | 0 | W (+discharge) | H | SA14 p.9 |
| battery_temp | [182] | n | 0.1 | −100 | °C | H | SA14 p.8 |
| pv1_w | [186] | n | 1 | 0 | W | M | SA14 p.9 |
| pv2_w | [187] | n | 1 | 0 | W | M | SA14 p.9 |
| pv3_w | [188] | n | 1 | 0 | W | M | SA14 p.9 (15K only) |
| pv_w | derived 186+187+188 | — | — | — | W | M | — |
| pv1_v / pv1_a | [109] / [110] | n | 0.1 | 0 | V / A | M | SA14 p.7 |
| pv2_v / pv2_a | [111] / [112] | n | 0.1 | 0 | V / A | M | SA14 p.7 |
| pv3_v / pv3_a | [113] / [114] | n | 0.1 | 0 | V / A | M | SA14 p.7 |
| grid_w | [169] | y | 1 | 0 | W (+import) | H | SA14 p.8 |
| grid_ct_w | [172] | y | 1 | 0 | W | H | SA14 p.8 |
| grid_l1_w / grid_l2_w | [167] / [168] | y | 1 | 0 | W | L (see 3g) | SA14 p.8 |
| grid_v_l1 / grid_v_l2 / grid_v | [150] / [151] / [152] | n | 0.1 | 0 | V | H | SA14 p.8 |
| grid_hz | [79] | n | 0.01 | 0 | Hz | H | SA14 p.6 |
| load_w | [178] | y | 1 | 0 | W | H | SA14 p.8 |
| load_l1_w / load_l2_w | [176] / [177] | y | 1 | 0 | W | H | SA14 p.8 |
| load_hz | [192] | n | 0.01 | 0 | Hz | H | SA14 p.9 |
| inverter_w | [175] | y | 1 | 0 | W | H | SA14 p.8 |
| inverter_l1_w / inverter_l2_w | [173] / [174] | y | 1 | 0 | W | H | SA14 p.8 |
| inverter_hz | [193] | n | 0.01 | 0 | Hz | H | SA14 p.9 |
| inverter_temp | [91] | n | 0.1 | −100 | °C | H | SA14 p.7 |
| gen_w | [166] | y | 1 | 0 | W (+out, −in) | M | SA14 p.8 |
| gen_v | [181] | n | 0.1 | 0 | V | M | SA14 p.8 |
| gen_hz | [196] | n | 0.01 | 0 | Hz | M | SA14 p.9 |
| grid_relay | [194] | n | 1 | 0 | enum | L (conflict) | SA14 p.9 vs DY118 |
| gen_relay | [195] & 0x0F | n | 1 | 0 | enum | M | SA14 p.9 |
| run_state | [59] | n | 1 | 0 | enum 0-5 | M | DY118 p.9 |
| faults | [103,104,105,106] | n | — | — | 64-bit bitfield | H | SA14 p.7, p.9-10 |
| warnings | [101,102] | n | — | — | bitfield | L | DY118 p.14 |
| day_pv_kwh | [108] | n | 0.1 | 0 | kWh | H | SA14 p.7 |
| day_load_kwh | [84] | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| day_batt_charge_kwh / day_batt_discharge_kwh | [70] / [71] | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| day_grid_buy_kwh / day_grid_sell_kwh | [76] / [77] | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| total_pv_kwh | [96,97] | n | 0.1 | 0 | kWh | H | SA14 p.7 |
| total_load_kwh | [85,86] | n | 0.1 | 0 | kWh | H | SA14 p.6-7 |
| total_batt_charge_kwh / total_batt_discharge_kwh | [72,73] / [74,75] | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| total_grid_buy_kwh | **[78,80]** | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| total_grid_sell_kwh | [81,82] | n | 0.1 | 0 | kWh | H | SA14 p.6 |
| total_active_kwh | [63,64] | y | 0.1 | 0 | kWh | M | SA14 p.6 |
| rated_power | [16,17] | n | 0.1 | 0 | W | H (obs.) | DY118 p.6 |
| version_protocol / version_mcu_aux / version_mcu / version_comm | [2] / [11] / [13] / [14] | n | hex | — | — | M-H | DY118; SAB |
| clock | [22,23,24] | — | bytes | — | YY MM DD hh mm ss | H | DY118 p.6; observed write |

## 6. Open questions

1. **194 grid relay:** SA14 says 1 = Open (disconnect) and 2 = Closed.
   Deye says 0 = not closed. kellerza treats non-zero as "grid connected".
   *Observed* 1 with grid voltage present, 8-10 A on 160/161, and CT import
   about 11 W. Check against the app and during a grid outage.
2. **Grid internals:** 160/161 show 8-10 A while 167/168 show about 0 W.
   Is the grid relay actually open (consistent with SA14's "1 = open")
   while the CT measures the house? Compare the app's grid figure with
   169/172.
3. **117/118 and 185** track inverter output power (W) closely. Deye calls
   them alarm/status words. Their Sol-Ark meaning is unknown.
4. **120-124** (Deye "debug") hold live values (121 signed −14..−5, 123
   about 7990). Unknown.
5. **0-58 misfits versus Deye:** 9 high bit `0x8000`, 20 = `0x00FF`,
   26 = 12000, 27 = 1300, 28-30 = 0, 34 = 8000, 57 = 1. Sol-Ark has
   different semantics or units here.
6. **297-310** (Deye arc-fault factory parameters): 304/306/308 changed
   during capture. These may be live arc-fault readings rather than
   parameters.
7. **433-487** are undocumented anywhere we found. Deye's 433-437 (meter
   energy totals) do not fit: 433/434 as a 32-bit total would be absurd.
   *Observed* values look like grid-code tables:
   - 433-436 = 2638, 2114, 6148, 5852, which reads as 263.8 V / 211.4 V /
     61.48 Hz / 58.52 Hz, just inside the trip points in 333/334/344/345
   - 441-448 = (110.00 %, 100.00 %), (111 %, 50 %), (112 %, 0 %)…, which
     looks like a volt-watt curve
   - 450-458 ≈ 59.50 / 60.50 Hz, 40.00
   - 464-487 = paired 2000/10000/8000 values

   Not asserted. Ask Sol-Ark for a newer map or correlate with app settings
   screens.
8. **`inverter_protocol: 1D`**: unknown (see 3e).
9. **What do cloud op 2/3 (42x2, 44x4) do?** Capture a session where the
   app toggles remote power on/off (only if the user approves; it is a
   passive capture, but it changes the inverter's state).
10. **Daytime check of PV registers:** all PV values so far are from
    night. Confirm 186-188 and 109-114 scales in daylight against the app.
11. **Is there a newer Sol-Ark map** (V1.5+ or an 18K/"Limitless" map)?
    Support said V1.4 was current as of 2025-01-15. Firmware has since
    moved (the dongle protocol change of Oct 2025).
12. **Clock read-back offset** (3d).

## 7. Side finding: `meta.json` `started` is the end time

`tools/capture.py` writes `"started": datetime.now()` **after** the capture
completes and is saved (line 92). So `meta.json`'s `started` is roughly the
capture end. For example, `20261011-191812` has `started: 19:33:18` = the
folder time plus 900 s. The folder name (directory-creation time) is the
better start estimate, but it still precedes the Saleae start by an
unknown few seconds. This matters for clock comparisons like 3d. The fix
belongs in the tools: record the time just before `start_capture` and
again after. Not changed here.

## Appendix A: cross-reference table (all polled registers)

The table is generated by a script from the scrubbed `registers.csv`
files: `20261011-191812` (900 s) for everything, and `...-193820-unplug-replug`
for register 19, which is only in the boot read. "Observed" shows the last
value decoded with the stated scale, with the range if it changed during
capture. Runs of identical undocumented registers are collapsed. The
serial (3-7) is never shown. "—" in the official column means V1.4 does
not list the register.

| Reg | Official Sol-Ark V1.4 | Deye / community | Observed (decoded) | Consistent? |
|---|---|---|---|---|
| 0 | — | Device type; 0x0003 = single-phase hybrid [KZ identity.py]; DY118 lists 0x0300 [DY118 p.5] | 0x0003 | yes (byte order differs from DY118 text) |
| 1 | — | Modbus address [DY118 p.5] | 1 | yes (=1) |
| 2 | — | Communication protocol version, hi.lo [DY118 p.5; KZ] | 0x0201 | yes: 2.1 |
| 3-7 | SN bytes 1-10, ASCII [SA14 p.6] | Serial [DY118 p.5] | (scrubbed; never recorded) | n/a |
| 8 | — | Rated phase / MI flag; 0-2 = single-phase [DY118 p.5; HAS] | 0 | yes |
| 9 | — | Chip type, low nibble [DY118 p.5; HAS] | 0x8000 | partial: high bit 0x8000 unexplained |
| 10 | — | Comm-board firmware field 2 [DY118 p.5; HAS] | 0x0000 | yes (0) |
| 11 | — | Control-board auxiliary program version [DY118 p.5]; part of control-board FW [13,12,11] [HAS] | 0x1725 | plausible (follower/aux MCU) |
| 12 | — | Control-board firmware field 2 [DY118 p.5] | 0x0000 | yes (0) |
| 13 | — | Control-board (MCU) firmware version [DY118 p.6; HAS] | 0x7222 | yes: MCU 7222 (Sol-Ark-style version) |
| 14 | — | Comm-board firmware version [DY118 p.6; HAS] | 0x143F | YES: 143F = 'Comm v143F' in [SAB p.3] |
| 15 | — | Safety type (Deye: <3 = 48 V battery) [DY118 p.6] | 0 | unknown |
| 16 | — | Rated power low word, 0.1 W [DY118 p.6; KZ (16,17)] | 15000 W (lo=16, hi=17) | YES: 15000 W proves lo-first |
| 17 | — | Rated power high word [DY118 p.6] | high word of 16 [raw 2] | yes |
| 18 | — | MPPT count (hi byte) and phases (lo byte) [DY118 p.6; HAS] | 0x0301 | YES: 3 MPPT, 1 phase |
| 19 | — | Rated grid voltage class 0-3 [DY118 p.6] | 0 | unknown |
| 20 | — | Remote lock (0x0002 off / 0x0000 on) [DY118 p.6] | 0x00FF | NO: 0x00FF not a Deye value |
| 21 | — | Power-on self-check time, s [DY118 p.6; HAS] | 10 s [raw 10] | yes |
| 22 | — | System time: year-2000 (hi), month (lo) [DY118 p.6; KZ SystemTimeRWSensor] | 0x1A0A = year-2000 26, month 10 | YES (verified by fc16 write) |
| 23 | — | System time: day (hi), hour (lo) [DY118 p.6] | 0x0B13 = day 11, hour 19 | YES |
| 24 | — | System time: minute (hi), second (lo) [DY118 p.6] | 0x2034 = min 32, sec 52 | YES |
| 25 | — | External-CT flag / min insulation impedance [DY118 p.7] | 1 | unknown |
| 26 | — | DC voltage upper limit, 0.1 V, range 2000-10000 [DY118 p.7] | 12000 | NO: 12000 out of Deye range |
| 27 | — | Grid voltage upper limit, 0.1 V [DY118 p.7] | 1300 | unclear (1300) |
| 28 | — | Grid voltage lower limit [DY118 p.7] | 0 | NO: 0 |
| 29 | — | Grid frequency upper limit, 0.01 Hz [DY118 p.7] | 0 | NO: 0 |
| 30 | — | Grid frequency lower limit [DY118 p.7] | 0 | NO: 0 |
| 31 | — | Grid current upper limit [DY118 p.7] | 0 | unclear |
| 32 | — | Start voltage upper limit, 0.1 V [DY118 p.7] | 10000 | unclear |
| 33 | — | Start voltage lower limit [DY118 p.7] | 3000 | unclear |
| 34 | — | Over-frequency derate point, 0.01 Hz [DY118 p.7] | 8000 | NO: 8000 out of range |
| 35 | — | Over-frequency derate % [DY118 p.7] | 2000 | unclear |
| 36 | — | Internal temperature upper limit, 0.1 C [DY118 p.7] | 85 C [raw 850] | plausible (85.0 C) |
| 37 | — | Communication address [DY118 p.7] | 0 | - |
| 38 | — | Comm baud / MI Zigbee-PLC [DY118 p.7] | 0 | - |
| 39 | — | Power factor setting, (x-1000)*0.001 [DY118 p.7] | 1000 | yes (1000 = PF 1.000) |
| 40 | — | Active power regulation 0.1 % [DY118 p.8] | 0 | unclear (0) |
| 41 | — | Reactive power regulation [DY118 p.8] | 0 | - |
| 42 | — | Apparent power regulation [DY118 p.8]; cloud op:3 reads/writes 42x2 | 0 | - |
| 43 | — | Switch on/off: 1 = on [DY118 p.8]; KZ 'Inverter enabled'; HAS on=1 off=2 | 1 | yes (1 = on) |
| 44 | — | Factory reset enable [DY118 p.8]; cloud op:2 covers 44x4 | 0 | yes (0) |
| 45 | — | Self-checking time [DY118 p.8] | 1 | - |
| 46 | — | Island protection enable [DY118 p.8] | 0 | - |
| 47 | — | Soft-start enable (MI) / MPPT number [DY118 p.8] | 0 | - |
| 48 | — | GFDI (old) / meter enable (new) [DY118 p.8] | 0 | - |
| 49 | — | Over-freq derate enable / RCD enable [DY118 p.8] | 0 | - |
| 50 | — | RISO enable [DY118 p.8] | 0 | - |
| 51 | — | Grid standard [DY118 p.8] | 0 | - |
| 52 | — | PV curve enable / CT ratio [DY118 p.8] | 0 | - |
| 53 | — | Max solar power W (old) / hardware matching (new) [DY118 p.8]; KZ 'Max Solar power' | 18000 W [raw 18000] | plausible (18000 W) |
| 54 | — | EEPROM init (1 = control, 2 = comm board) [DY118 p.9] | 0 | - |
| 55 | — | Factory test command bits [DY118 p.9] | 0 | - |
| 56 | — | Limiter function enable [DY118 p.9] | 0 | - |
| 57 | — | PowerWH correction factor, 0.01 [DY118 p.9] | 1 | unclear (1) |
| 58 | — | General settings bits [DY118 p.9] | 1 | - |
| 59 | — | Run state: 0 standby, 1 self-check, 2 normal, 3 alarm, 4 fault [DY118 p.9; KZ] | 2 | yes (2 = normal) |
| 60 | Day active energy, signed, 0.1 kWh, inverter grid-port energy [SA14 p.6] | same [DY118 p.10] | 59.7 kWh (range 58.7..59.7) [raw 597] | yes |
| 61 | — | Day reactive energy, 0.1 kVarh [DY118 p.10] | 0 | - |
| 62 | — | Day generator energy, 0.1 kWh (V117) [DY118 p.2,10] | 0 kWh [raw 0] | yes (no gen) |
| 63 | Total active energy low word, 0.1 kWh [SA14 p.6] | same [DY118 p.10] | 67483 kWh (lo=63, hi=64) | yes |
| 64 | Total active energy high word [SA14 p.6] | same | high word of 63 [raw 10] | yes |
| 65 | — | Month PV energy, 1 kWh [DY118 p.10; KZ] | 0 | unsupported? (0) |
| 66 | — | Month load energy [DY118 p.10] | 0 | unsupported? (0) |
| 67 | — | Month grid energy [DY118 p.10] | 0 | unsupported? (0) |
| 68 | — | Year PV energy lo [DY118 p.10] | 0 | unsupported? (0) |
| 69 | — | Year PV energy hi [DY118 p.10] | 0 | unsupported? (0) |
| 70 | Day battery charge, 0.1 kWh [SA14 p.6] | same [DY118 p.10] | 28.5 kWh [raw 285] | yes |
| 71 | Day battery discharge, 0.1 kWh [SA14 p.6] | same | 19.8 kWh (range 18.8..19.8) [raw 198] | yes |
| 72 | Total battery charge low word [SA14 p.6] | same [DY118 p.11] | 33440 kWh (lo=72, hi=73) | yes |
| 73 | Total battery charge high word [SA14 p.6] | same | high word of 72 [raw 5] | yes |
| 74 | Total battery discharge low word [SA14 p.6] | same | 32161.1 kWh (lo=74, hi=75) | yes (unsigned!) |
| 75 | Total battery discharge high word [SA14 p.6] | same | high word of 74 [raw 4] | yes |
| 76 | Day grid buy, 0.1 kWh [SA14 p.6] | same | 5.8 kWh [raw 58] | yes |
| 77 | Day grid sell, 0.1 kWh [SA14 p.6] | same | 0 kWh [raw 0] | yes |
| 78 | Total grid buy LOW word [SA14 p.6] (high word is 80) | same [DY118 p.11] | 33544.5 kWh (lo=78, hi=80) | yes (non-contiguous) |
| 79 | Grid frequency, 0.01 Hz [SA14 p.6] | same [DY118 p.11; KZ] | 60 Hz (range 59.95..60) [raw 6000] | yes |
| 80 | Total grid buy HIGH word [SA14 p.6] | same | high word of 78 [raw 5] | yes |
| 81 | Total grid sell low word [SA14 p.6] | same | 68.6 kWh (lo=81, hi=82) | yes |
| 82 | Total grid sell high word [SA14 p.6] | same | high word of 81 [raw 0] | yes |
| 83 | — | Generator daily run time, 0.1 h [DY118 p.12] | 0 | yes (0) |
| 84 | Day load energy, 0.1 kWh [SA14 p.6] | same | 65.5 kWh (range 64.6..65.5) [raw 655] | yes |
| 85 | Total load energy low word [SA14 p.6] | same | 100971.9 kWh (lo=85, hi=86) | yes |
| 86 | Total load energy high word [SA14 p.7] | same | high word of 85 [raw 15] | yes |
| 87 | — | Year load energy lo [DY118 p.12] | 0 | unsupported? (0) |
| 88 | — | Year load energy hi [DY118 p.12] | 0 | unsupported? (0) |
| 89 | — | (string inv: output reactive power hi) [DY118 p.13] | 0 | - |
| 90 | DC/DC transformer temp, (x-1000)*0.1 C, **Not used in 15K** [SA14 p.7] | DC transformer / radiator temp [DY118 p.13; KZ] | -34.5 C (range -35..-34.5) [raw 655] | garbage on 15K, as documented |
| 91 | IGBT heat-sink temp, (x-1000)*0.1 C [SA14 p.7] | Radiator / IGBT temp [DY118 p.13; KZ] | 49.7 C (range 44.5..50.1) [raw 1497] | yes |
| 92 | — | Total generator energy lo (V117) [DY118 p.2,13]; KZ: SD status (wrong here) | 0 | Deye V117 fits (0) |
| 93 | — | Power factor / phase-error bits [DY118 p.13] | 0 | - |
| 94 | — | SD card status: 1000 fault, 2000 OK [DY118 p.13] | 2000 | yes (2000 = OK) |
| 95 | — | Total generator energy hi (V117) [DY118 p.2,13]; KZ: environment temp (wrong here: would be -100 C) | 0 | Deye V117 fits (0) |
| 96 | Total PV energy low word [SA14 p.7] | same [DY118 p.13] | 76499.5 kWh (lo=96, hi=97) | yes |
| 97 | Total PV energy high word [SA14 p.7] | same | high word of 96 [raw 11] | yes |
| 98 | — | Year grid sell lo [DY118 p.13] | 0 | unsupported? (0) |
| 99 | — | Year grid sell hi [DY118 p.13] | 0 | unsupported? (0) |
| 100 | — | Other test flag bits [DY118 p.13] | 0x0001 (1) | - |
| 101 | — | Warning word 1 [DY118 p.14; HAS] | 0x0000 (0) | yes (0) |
| 102 | — | Warning word 2 [DY118 p.14] | 0x0000 (0) | yes (0) |
| 103 | Fault word 1 (bit flags, F01-F16) [SA14 p.7, table p.9-10] | same [DY118 p.14] | 0x0000 (0) | yes (0) |
| 104 | Fault word 2 (F17-F32) [SA14 p.7] | same | 0x0000 (0) | yes (0) |
| 105 | Fault word 3 (F33-F48) [SA14 p.7] | same | 0x0000 (0) | yes (0) |
| 106 | Fault word 4 (F49-F64) [SA14 p.7] | same | 0x0000 (0) | yes (0) |
| 107 | Corrected battery capacity, 1 Ah [SA14 p.7] | same [DY118 p.14] | 618 Ah [raw 618] | yes (cf. 204 = 600 Ah) |
| 108 | Daily PV energy, 0.1 kWh [SA14 p.7] | same | 74.5 kWh [raw 745] | yes |
| 109 | PV1 voltage, 0.1 V [SA14 p.7] | same [DY118 p.14; KZ] | 8.4 V (range 8.4..131.8) [raw 84] | yes (night) |
| 110 | PV1 current, 0.1 A [SA14 p.7] | same | 0.1 A (range 0.1..0.2) [raw 1] | yes |
| 111 | PV2 voltage, 0.1 V [SA14 p.7] | same | 8.5 V (range 8.5..114.5) [raw 85] | yes |
| 112 | PV2 current, 0.1 A [SA14 p.7] | same | 0.2 A (range 0.1..0.2) [raw 2] | yes |
| 113 | PV3 voltage, 0.1 V [SA14 p.7] | same | 12.7 V (range 12.7..152.6) [raw 127] | yes |
| 114 | PV3 current, 0.1 A, 15K only [SA14 p.7] | same | 0.2 A (range 0.1..0.2) [raw 2] | yes |
| 115 | — | PV4 voltage [DY118 p.14] | 0 | yes (no PV4) |
| 116 | — | PV4 current [DY118 p.14] | 0 | yes (no PV4) |
| 117 | — | Alarm status 1 [DY118 p.14] | 3765 (range 3737..3892) | NO: tracks inverter power (~W) |
| 118 | — | Alarm status 2 [DY118 p.14] | 3742 (range 3715..3864) | NO: tracks inverter power (~W) |
| 119 | — | PV string damage flags [DY118 p.14] | 0x0000 (0) | yes (0) |
| 120 | — | Debug data [DY118 p.14-15] | 0 | unknown (live values) |
| 121 | — | Debug data [DY118 p.14-15] | 65526 (range 65522..65531) | unknown (live values) |
| 122 | — | Debug data [DY118 p.14-15] | 36702 | unknown (live values) |
| 123 | — | Debug data [DY118 p.14-15] | 7991 (range 7987..8001) | unknown (live values) |
| 124 | — | Debug data [DY118 p.14-15] | 44 | unknown (live values) |
| 150 | Grid side voltage L1-N, 0.1 V [SA14 p.8] | same [DY118 p.18] | 124.1 V (range 124..125.8) [raw 1241] | yes |
| 151 | Grid side voltage L2-N, 0.1 V [SA14 p.8] | same | 124 V (range 123.8..125.6) [raw 1240] | yes |
| 152 | Grid side voltage L1-L2, 0.1 V [SA14 p.8] | same | 248.8 V (range 248.7..252.3) [raw 2488] | yes |
| 153 | Voltage at middle side of relay L1-L2, 0.1 V [SA14 p.8] | same | 247.4 V (range 245.6..251.6) [raw 2474] | yes |
| 154 | Inverter output voltage L1-N [SA14 p.8] | same | 124.1 V (range 124..125.8) [raw 1241] | yes |
| 155 | Inverter output voltage L2-N [SA14 p.8] | same | 124 V (range 123.8..125.6) [raw 1240] | yes |
| 156 | Inverter output voltage L1-L2 [SA14 p.8] | same | 248.1 V (range 247.8..251.4) [raw 2481] | yes |
| 157 | Load voltage L1, 0.1 V [SA14 p.8] | same | 124.1 V (range 124..125.8) [raw 1241] | yes |
| 158 | Load voltage L2, 0.1 V [SA14 p.8] | same | 124 V (range 123.8..125.6) [raw 1240] | yes |
| 159 | — | Reserved [DY118 p.18] | 0 | yes (0) |
| 160 | Grid side current L1, signed, 0.01 A [SA14 p.8] | same [DY118 p.19] | 8.02 A (range 7.9..8.04) [raw 802] | ? (8 A with ~0 W internal grid power) |
| 161 | Grid side current L2, signed, 0.01 A [SA14 p.8] | same | 9.95 A (range 9.81..10.13) [raw 995] | ? (as 160) |
| 162 | Grid external limiter (CT) current L1, signed, 0.01 A [SA14 p.8] | same | 6.89 A (range 6.41..7.34) [raw 689] | plausible |
| 163 | Grid external limiter (CT) current L2, signed, 0.01 A [SA14 p.8] | same | 8.4 A (range 7.86..9.04) [raw 840] | plausible |
| 164 | Inverter output current L1, signed, 0.01 A [SA14 p.8] | same; KZ 'Inverter current' | 11.2 A (range 10.8..11.3) [raw 1120] | yes |
| 165 | Inverter output current L2, signed, 0.01 A [SA14 p.8] | same | 17.7 A (range 17.2..18.4) [raw 1770] | yes |
| 166 | Gen or AC-coupled power, 1 W: +ve as load output, -ve as AC input [SA14 p.8] | Gen port power [DY118 p.19; KZ 'Gen power'] | 0 W [raw 0] | yes (0, no gen) |
| 167 | Grid side L1 power, signed, 1 W [SA14 p.8] | same; KZ 'Grid LD power' | -11 W (range -18..0) [raw 65525] | see note: != part of 169 here |
| 168 | Grid side L2 power, signed, 1 W [SA14 p.8] | same | 0 W (range -11..0) [raw 0] | see note |
| 169 | Total grid side power L1-L2, signed, 1 W, >0 BUY, <0 SELL [SA14 p.8] | same [DY118 p.19]; KZ x1 (x10 on 16 kW); HAS scale [1,10,10] | 11 W (range 0..22) [raw 11] | yes, x1: 178-175 == 169 exactly |
| 170 | Grid external limiter 1 power (CT1), signed, 1 W [SA14 p.8] | same | 11 W (range 0..17) [raw 11] | yes |
| 171 | Grid external limiter 2 power (CT2), signed, 1 W [SA14 p.8] | same | 0 W (range 0..14) [raw 0] | yes |
| 172 | Grid external total power, signed, 1 W [SA14 p.8] | same; KZ 'Grid CT power' | 11 W (range 0..22) [raw 11] | yes (== 169 == 170+171 here) |
| 173 | Inverter output L1 power, signed, 1 W [SA14 p.8] | same | 1487 W (range 1465..1503) [raw 1487] | yes |
| 174 | Inverter output L2 power, signed, 1 W [SA14 p.8] | same | 2296 W (range 2283..2396) [raw 2296] | yes |
| 175 | Inverter output total power, signed, 1 W [SA14 p.8] | same; KZ 'Inverter power' | 3783 W (range 3756..3895) [raw 3783] | yes (== 173+174) |
| 176 | Load side L1 power, signed, 1 W [SA14 p.8] | same | 1498 W (range 1480..1517) [raw 1498] | yes |
| 177 | Load side L2 power, signed, 1 W [SA14 p.8] | same | 2296 W (range 2283..2396) [raw 2296] | yes |
| 178 | Load side total power, signed, 1 W [SA14 p.8] | same; KZ 'Load power' | 3794 W (range 3767..3911) [raw 3794] | yes (== 176+177 == 175+169) |
| 179 | Load current L1, signed, 0.01 A [SA14 p.8] | same | 14.76 A (range 14.63..15.03) [raw 1476] | yes |
| 180 | Load current L2, signed, 0.01 A [SA14 p.8] | same | 22.96 A (range 22.83..23.96) [raw 2296] | yes |
| 181 | Gen port voltage L1-L2, 0.1 V [SA14 p.8] | Gen port voltage (V116) [DY118 p.2,20] | 7.8 V (range 7.7..8) [raw 78] | yes (no gen) |
| 182 | Battery temperature, (x-1000)*0.1 C [SA14 p.8] | same [DY118 p.20; KZ TempSensor] | 25 C [raw 1250] | yes |
| 183 | Battery voltage, 0.01 V [SA14 p.8] | same | 52.07 V (range 52.06..52.08) [raw 5207] | yes |
| 184 | Battery SOC, 1 % [SA14 p.8] | same | 72 % (range 72..75) [raw 72] | yes (inverter-estimated: no BMS) |
| 185 | — | Battery status [DY118 p.20] | 3772 (range 3746..3895) | NO: tracks 175 (W) |
| 186 | PV1 input power, 1 W [SA14 p.9] | same [DY118 p.20] | 1 W (range 1..22) [raw 1] | yes (night) |
| 187 | PV2 input power, 1 W [SA14 p.9] | same | 1 W (range 1..23) [raw 1] | yes |
| 188 | PV3 input power, 1 W, 15K only [SA14 p.9] | same | 2 W (range 2..31) [raw 2] | yes |
| 189 | PV4 input power, 1 W [SA14 p.9] | same | 0 W [raw 0] | yes (0) |
| 190 | Battery output power, signed, 1 W [SA14 p.9] | same (+ = discharge) [DY118 p.20; KZ] | 3909 W (range 3879..4039) [raw 3909] | YES: = 183*191, +ve while discharging at night |
| 191 | Battery output current, signed, 0.01 A [SA14 p.9] | same; HAS scale varies by model | 75.08 A (range 74.51..77.58) [raw 7508] | YES: x0.01 |
| 192 | Load frequency, 0.01 Hz [SA14 p.9] | same | 59.95 Hz (range 59.95..60) [raw 5995] | yes |
| 193 | Inverter output frequency, 0.01 Hz [SA14 p.9] | same | 59.95 Hz (range 59.95..60) [raw 5995] | yes |
| 194 | Grid side relay status: 1 = Open (disconnect), 2 = Closed [SA14 p.9] | Deye: 0 = not closed, else closed [DY118 p.20]; KZ binary 'Grid connected' | 1 | CONFLICT (see open questions) |
| 195 | Gen relay status, low nibble: 0 open, 1 closed, 2 no connection, 3 closed when gen on [SA14 p.9] | Deye adds bits 4-7 = on/off signal [DY118 p.20] | 0x0010 (16) | yes (lo nibble 0 = open) |
| 196 | Generator relay frequency, 0.01 Hz [SA14 p.9] | Gen port frequency [DY118 p.21] | 0 Hz [raw 0] | yes (no gen) |
| 197-199 | — | (197 undocumented) [DY118 p.21] | all 0 | - |
| 200 | — | Battery control mode: 0 lead-acid/voltage, 1 lithium [DY118 p.21; HAS] | 0 | yes (0, matches no BMS) |
| 201 | — | Equalization voltage, 0.01 V [DY118 p.21] | 55 V [raw 5500] | yes |
| 202 | — | Absorption voltage, 0.01 V | 55.5 V [raw 5550] | yes |
| 203 | — | Float voltage, 0.01 V | 54 V [raw 5400] | yes |
| 204 | — | Battery capacity, 1 Ah | 600 Ah [raw 600] | yes |
| 205 | — | Empty voltage, 0.01 V | 48 V [raw 4800] | yes |
| 206 | — | Zero-export power, W [HAS]; KZ 'Grid trickle feed' | 20 W [raw 20] | yes |
| 207 | — | Equalization cycle, days | 30 | yes |
| 208 | — | Equalization time, 0.5 h | 2 | yes |
| 209 | — | Temperature compensation, mV/C | 0 | yes |
| 210 | — | Max charge current, 1 A [KZ; HAS] | 275 A [raw 275] | YES: 275 A = 15K rating |
| 211 | — | Max discharge current, 1 A | 275 A [raw 275] | YES: 275 A |
| 212 | — | undefined | 0 | - |
| 213 | — | Battery operation: 0 by voltage, 1 by capacity, 2 no battery | 0 | yes |
| 214 | — | Lithium wake-up | 1 | - |
| 215 | — | Battery resistance, mOhm | 5 | - |
| 216 | — | Charging efficiency, 0.1 % | 990 | yes (99.0 %) |
| 217 | — | Shutdown SOC % [KZ] | 20 % [raw 20] | yes |
| 218 | — | Restart SOC % | 50 % [raw 50] | yes |
| 219 | — | Low SOC % | 35 % [raw 35] | yes |
| 220 | — | Shutdown voltage, 0.01 V | 48.5 V [raw 4850] | yes |
| 221 | — | Restart voltage, 0.01 V | 52.5 V [raw 5250] | yes |
| 222 | — | Low voltage, 0.01 V | 52 V [raw 5200] | yes |
| 223 | — | Generator max run time, 0.1 h | 10242 | unclear (10242) |
| 224 | — | Generator cool-down time, 0.1 h | 0 | - |
| 225 | — | Gen charge start voltage, 0.01 V | 49 V [raw 4900] | yes |
| 226 | — | Gen charge start SOC % | 50 | yes |
| 227 | — | Gen charge current, A | 40 | yes |
| 228 | — | Grid charge start voltage, 0.01 V | 49 V [raw 4900] | yes |
| 229 | — | Grid charge start SOC % | 50 | yes |
| 230 | — | Grid charge current, A [KZ] | 150 | yes |
| 231 | — | Gen charge enable | 0 | - |
| 232 | — | Grid charge enable [KZ] | 0 | - |
| 233 | — | Solar as PSU | 0 | - |
| 234 | — | Force generator as load | 0 | - |
| 235 | — | Gen/AUX port use: 0 gen input, 1 smart load, 2 micro-inverter input [DY118 p.23; KZ] | 0 | yes |
| 236 | — | Smart-load OFF voltage, 0.01 V | 51 V [raw 5100] | yes |
| 237 | — | Smart-load OFF SOC % | 80 | yes |
| 238 | — | Smart-load ON voltage, 0.01 V | 54 V [raw 5400] | yes |
| 239 | — | Smart-load ON SOC % | 90 | yes |
| 240 | — | PWM test | 0 | - |
| 241 | — | Min solar power to start gen, W | 500 | plausible |
| 242 | — | Gen/grid signal | 3 | - |
| 243 | — | Energy pattern: 0 battery first, 1 load first [KZ 'Priority Load'] | 0 | - |
| 244 | — | Limit control: 0 allow export, 1 essentials/built-in CT, 2 zero export to external CT [DY118 p.23; KZ] | 2 | yes (2; consistent with 169 == CT power) |
| 245 | — | Max sell power, W [KZ] | 3000 W [raw 3000] | yes |
| 246 | — | External CT clamp phase | 22 | - |
| 247 | — | Solar sell enable [KZ] | 0 | - |
| 248 | — | Time-of-use: bit0 enable, bits1-7 Mon..Sun [DY118 p.24; HAS] | 0x00FF (255) | yes (0xFF) |
| 249 | — | undefined | 1 | - |
| 250 | — | Program 1 time, HHMM [DY118 p.24; KZ] | 100 = 01:00 | yes |
| 251 | — | Program 2 time, HHMM [DY118 p.24; KZ] | 500 = 05:00 | yes |
| 252 | — | Program 3 time, HHMM [DY118 p.24; KZ] | 900 = 09:00 | yes |
| 253 | — | Program 4 time, HHMM [DY118 p.24; KZ] | 1300 = 13:00 | yes |
| 254 | — | Program 5 time, HHMM [DY118 p.24; KZ] | 1700 = 17:00 | yes |
| 255 | — | Program 6 time, HHMM [DY118 p.24; KZ] | 2100 = 21:00 | yes |
| 256 | — | Program 1 power, W [KZ] | 2000 W [raw 2000] | yes |
| 257 | — | Program 2 power, W [KZ] | 2000 W [raw 2000] | yes |
| 258 | — | Program 3 power, W [KZ] | 2000 W [raw 2000] | yes |
| 259 | — | Program 4 power, W [KZ] | 4500 W [raw 4500] | yes |
| 260 | — | Program 5 power, W [KZ] | 4500 W [raw 4500] | yes |
| 261 | — | Program 6 power, W [KZ] | 4500 W [raw 4500] | yes |
| 262 | — | Program 1 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 263 | — | Program 2 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 264 | — | Program 3 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 265 | — | Program 4 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 266 | — | Program 5 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 267 | — | Program 6 voltage, 0.01 V [KZ] | 49 V [raw 4900] | yes |
| 268 | — | Program 1 SOC % [KZ] | 50 % [raw 50] | yes |
| 269 | — | Program 2 SOC % [KZ] | 50 % [raw 50] | yes |
| 270 | — | Program 3 SOC % [KZ] | 50 % [raw 50] | yes |
| 271 | — | Program 4 SOC % [KZ] | 100 % [raw 100] | yes |
| 272 | — | Program 5 SOC % [KZ] | 50 % [raw 50] | yes |
| 273 | — | Program 6 SOC % [KZ] | 50 % [raw 50] | yes |
| 274 | — | Program 1 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 275 | — | Program 2 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 276 | — | Program 3 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 277 | — | Program 4 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 278 | — | Program 5 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 279 | — | Program 6 charge bits (b0 grid, b1 gen; b2-4 mode; 0x40 sell) [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 280 | — | Peak-shaving / grid-always-on bit fields [DY118 p.25; KZ] | 0x0000 (0) | yes |
| 281 | — | (text precedes 282 in DY118) | 0 | - |
| 282 | — | Grid reconnect time, s [DY118 p.25; HAS] | 60 s [raw 60] | yes (60 s) |
| 283 | — | Solar arc-fault mode [DY118 p.25] | 0 | - |
| 284 | — | Grid mode: 0 general, 1 UL1741&IEEE1547, 2 CPUC Rule 21, 3 SRD-UL1741 [DY118 p.26] | 3 | plausible (3) |
| 285 | — | Grid frequency: 0 50 Hz, 1 60 Hz [DY118 p.26] | 1 | YES (1 = 60 Hz) |
| 286 | — | Grid type: 0 240/230 1-ph, 1 120/240 split, 2 208 3-ph, 3 120 1-ph [DY118 p.26] | 1 | YES (1 = 120/240 split-phase) |
| 287 | — | Grid voltage high, 0.1 V [DY118 p.26] | 288 V [raw 2880] | yes |
| 288 | — | Grid voltage low, 0.1 V | 120 V [raw 1200] | yes |
| 289 | — | Grid Hz high, 0.01 Hz | 62 Hz [raw 6200] | YES (62.00) |
| 290 | — | Grid Hz low, 0.01 Hz | 57 Hz [raw 5700] | YES (57.00) |
| 291 | — | Gen peak-shaving enable? | 0 | - |
| 292 | — | Gen peak-shaving power, W [KZ; HAS] | 8000 W [raw 8000] | yes |
| 293 | — | Grid peak-shaving power, W [KZ; HAS] | 8000 W [raw 8000] | yes |
| 294 | — | Smart-load open delay, min | 100 | plausible |
| 295 | — | PF / power % (800 = 80 %, 1200 = 120 %) | 1000 | plausible (1000) |
| 296 | — | External relay bits [DY118 p.26] | 0xFFFF (65535) | - |
| 297 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 298 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 30000 | ? (some vary: 304/306/308) |
| 299 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 300 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 45000 | ? (some vary: 304/306/308) |
| 301 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 302 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 800 | ? (some vary: 304/306/308) |
| 303 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 304 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 50 (range 35..50) | ? (some vary: 304/306/308) |
| 305 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 306 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 540 (range 540..600) | ? (some vary: 304/306/308) |
| 307 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 0 | ? (some vary: 304/306/308) |
| 308 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 100 (range 55..100) | ? (some vary: 304/306/308) |
| 309 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 3 | ? (some vary: 304/306/308) |
| 310 | — | Arc-fault factory parameters B/I/F/D/T/C/Frz, hi/lo pairs [DY118 p.26-27] | 41486 | ? (some vary: 304/306/308) |
| 311 | — | UPS time, s [DY118 p.27] | 0 | - |
| 312 | — | BMS charging voltage, 0.01 V [DY118 p.27; HAS] | 0 | yes (0: no BMS) |
| 313 | — | BMS discharge voltage, 0.01 V | 0 | yes (0) |
| 314 | — | BMS charge current limit, A [KZ] | 0 | yes (0) |
| 315 | — | BMS discharge current limit, A [KZ] | 0 | yes (0) |
| 316 | — | BMS SOC % | 0 | yes (0) |
| 317 | — | BMS voltage, 0.01 V | 0 | yes (0) |
| 318 | — | BMS current, A | 0 | yes (0) |
| 319 | — | BMS temperature, (x-1000)*0.1 C | 0 | yes (0) |
| 320 | — | BMS max charge current limit [DY118 p.27] | 0 | yes (0) |
| 321 | — | BMS max discharge current limit | 0 | yes (0) |
| 322 | — | Lithium alarm bits | 0x0000 (0) | yes (0) |
| 323 | — | Lithium fault bits | 0x0000 (0) | yes (0) |
| 324 | — | Lithium symbol bits | 0x0000 (0) | - |
| 325 | — | Lithium battery/BMS protocol [DY118 p.28; KZ 'BMS Protocol'] | 0 | yes (0; Sol-Ark 'BMS Lithium Batt 00') |
| 326 | — | External meter/CT bits [DY118 p.28] | 0x0000 (0) | - |
| 327 | — | CT ratio, 200-8000 [DY118 p.28] | 2000 | YES (2000) |
| 328 | — | (stop?) [DY118 p.28] | 0 | - |
| 329 | — | AC-couple frequency upper limit, 0.01 Hz [DY118 p.28] | 62 Hz [raw 6200] | yes (62.00) |
| 330 | — | LCD bits: beep, AM/PM, auto-dim [DY118 p.28] | 0x00C3 (195) | plausible |
| 331 | — | CA_LHVRT (voltage ride-through) enable [DY118 p.29] | 1 | yes |
| 332 | — | CA_HV2 trip voltage, 0.1 V [DY118 p.29] | 288 V [raw 2880] | yes (1.2/1.1/0.88/0.7/0.5 pu of 240 V; 1547-like) |
| 333 | — | CA_HV1 trip voltage, 0.1 V [DY118 p.29] | 264 V [raw 2640] | yes (1.2/1.1/0.88/0.7/0.5 pu of 240 V; 1547-like) |
| 334 | — | CA_LV1 trip voltage, 0.1 V [DY118 p.29] | 211.2 V [raw 2112] | yes (1.2/1.1/0.88/0.7/0.5 pu of 240 V; 1547-like) |
| 335 | — | CA_LV2 trip voltage, 0.1 V [DY118 p.29] | 168 V [raw 1680] | yes (1.2/1.1/0.88/0.7/0.5 pu of 240 V; 1547-like) |
| 336 | — | CA_LV3 trip voltage, 0.1 V [DY118 p.29] | 120 V [raw 1200] | yes (1.2/1.1/0.88/0.7/0.5 pu of 240 V; 1547-like) |
| 337 | — | CA_HV2 trip time, 0.01 s [DY118 p.29] | 0.16 s [raw 16] | yes (1547-like clearing time) |
| 338 | — | CA_HV1 trip time, 0.01 s [DY118 p.29] | 13 s [raw 1300] | yes (1547-like clearing time) |
| 339 | — | CA_LV1 trip time, 0.01 s [DY118 p.29] | 21 s [raw 2100] | yes (1547-like clearing time) |
| 340 | — | CA_LV2 trip time, 0.01 s [DY118 p.29] | 2 s [raw 200] | yes (1547-like clearing time) |
| 341 | — | CA_LV3 trip time, 0.01 s [DY118 p.29] | 0.01 s [raw 1] | unclear (implausibly short) |
| 342 | — | CA_LHFRT (frequency ride-through) enable | 1 | yes |
| 343 | — | CA_HF2 trip frequency, 0.01 Hz [DY118 p.29] | 62 Hz [raw 6200] | yes (grid-code-like; 1547-2018 defaults would be 61.2/56.5 for HF1/LF2) |
| 344 | — | CA_HF1 trip frequency, 0.01 Hz [DY118 p.29] | 61.5 Hz [raw 6150] | yes (grid-code-like; 1547-2018 defaults would be 61.2/56.5 for HF1/LF2) |
| 345 | — | CA_LF1 trip frequency, 0.01 Hz [DY118 p.29] | 58.5 Hz [raw 5850] | yes (grid-code-like; 1547-2018 defaults would be 61.2/56.5 for HF1/LF2) |
| 346 | — | CA_LF2 trip frequency, 0.01 Hz [DY118 p.29] | 57 Hz [raw 5700] | yes (grid-code-like; 1547-2018 defaults would be 61.2/56.5 for HF1/LF2) |
| 347 | — | CA_HF2 trip time, 0.01 s [DY118 p.29] | 0.16 s [raw 16] | yes (1547-like clearing time) |
| 348 | — | CA_HF1 trip time, 0.01 s [DY118 p.29] | 299 s [raw 29900] | yes (1547-like clearing time) |
| 349 | — | CA_LF1 trip time, 0.01 s [DY118 p.29] | 299 s [raw 29900] | yes (1547-like clearing time) |
| 350 | — | CA_LF2 trip time, 0.01 s [DY118 p.29] | 0.16 s [raw 16] | yes (1547-like clearing time) |
| 351 | — | CA volt-var (QV) enable | 0 | - |
| 352 | — | CA_QV_V1, 0.01 % of nominal? [DY118 p.29] | 9000 | plausible (90/94/106/110 %) |
| 353 | — | CA_QV_V2, 0.01 % of nominal? [DY118 p.29] | 9400 | plausible (90/94/106/110 %) |
| 354 | — | CA_QV_V3, 0.01 % of nominal? [DY118 p.29] | 10600 | plausible (90/94/106/110 %) |
| 355 | — | CA_QV_V4, 0.01 % of nominal? [DY118 p.29] | 11000 | plausible (90/94/106/110 %) |
| 356 | — | CA_QV_Q1, signed, 0.01 % [DY118 p.29] | 43.6 % [raw 4360] | plausible (+/-43.6 %) |
| 357 | — | CA_QV_Q2, signed, 0.01 % [DY118 p.29] | 0 % [raw 0] | plausible (+/-43.6 %) |
| 358 | — | CA_QV_Q3, signed, 0.01 % [DY118 p.29] | 0 % [raw 0] | plausible (+/-43.6 %) |
| 359 | — | CA_QV_Q4, signed, 0.01 % [DY118 p.29] | -43.6 % [raw 61176] | plausible (+/-43.6 %) |
| 360 | — | CA freq-watt (FW) enable | 1 | - |
| 361 | — | CA_Fstart, 0.01 Hz | 60.5 Hz [raw 6050] | plausible |
| 362 | — | CA_Fstop, 0.01 Hz | 62 Hz [raw 6200] | plausible |
| 363 | — | CA volt-watt (VW) enable | 0 | - |
| 364 | — | CA_Vstart, 0.1 V | 264 V [raw 2640] | plausible |
| 365 | — | CA_Vstop, 0.1 V | 266.4 V [raw 2664] | plausible |
| 366 | — | Normal ramp rate % [DY118 p.30] | 600 | - |
| 367 | — | Soft-start ramp rate % | 600 | - |
| 368 | — | QV response time, s | 100 | - |
| 369 | — | VW response time, s | 50 | - |
| 370 | — | FW response time, s | 4000 | - |
| 371-375 | — | reserved [DY118 p.30] | all 1000 | ? (1000 = looks like x0.001 factor) |
| 376 | — | Calibration Grid1_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 377 | — | Calibration Grid2_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 378 | — | Calibration Grid_V_L1 (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 379 | — | Calibration Grid_V_L2 (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 380 | — | Calibration Limit1_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 381 | — | Calibration Limit2_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 382 | — | Calibration PV1_V (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 383 | — | Calibration PV1_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 384 | — | Calibration PV2_V (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 385 | — | Calibration PV2_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 386 | — | Calibration INV_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 387 | — | Calibration INV_V (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 388 | — | Calibration BAT_I (x0.001?) [DY118 p.30] | 1000 | plausible (~1000) |
| 389 | — | Calibration BAT_V (x0.001?) [DY118 p.30] | 993 | plausible (~1000) |
| 390 | — | Solar1 as wind input enable | 0 | - |
| 391 | — | Solar2 as wind input enable | 0 | - |
| 392-403 | — | Wind curve voltages 1-12, 0.1 V [DY118 p.30] | all 0 | yes (0) |
| 404-415 | — | Wind curve currents 1-12, 0.1 A [DY118 p.30-31] | all 0 | yes (0) |
| 416 | — | Force off-grid operation bit [DY118 p.31] | 0 | - |
| 417 | — | Parallel: b0 enable, b1 master, b8-9 phase, b10-15 Modbus SN [DY118 p.31] | 0x0400 (1024) | yes (0x0400: SN 1, not parallel) |
| 418 | — | Per-phase inverter counts (parallel) [DY118 p.31] | 0 | yes (0) |
| 419 | — | Lithium battery version low [DY118 p.31] | 0 | yes (0) |
| 433 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2638 | unknown (looks like grid-code settings) |
| 434 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2114 | unknown (looks like grid-code settings) |
| 435 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 6148 | unknown (looks like grid-code settings) |
| 436 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 5852 | unknown (looks like grid-code settings) |
| 437 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2760 | unknown (looks like grid-code settings) |
| 438 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 1000 | unknown (looks like grid-code settings) |
| 439 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 50 | unknown (looks like grid-code settings) |
| 440 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 441 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 11000 | unknown (looks like grid-code settings) |
| 442 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 443 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 11100 | unknown (looks like grid-code settings) |
| 444 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 5000 | unknown (looks like grid-code settings) |
| 445 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 11200 | unknown (looks like grid-code settings) |
| 446 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 447 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 11200 | unknown (looks like grid-code settings) |
| 448 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 449 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 1 | unknown (looks like grid-code settings) |
| 450-451 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 5950 | unknown (looks like grid-code settings) |
| 452 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 4000 | unknown (looks like grid-code settings) |
| 453-454 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 0 | unknown (looks like grid-code settings) |
| 455 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 65535 | unknown (looks like grid-code settings) |
| 456-457 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 6050 | unknown (looks like grid-code settings) |
| 458 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 4000 | unknown (looks like grid-code settings) |
| 459-460 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 0 | unknown (looks like grid-code settings) |
| 461-462 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 65535 | unknown (looks like grid-code settings) |
| 463 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 464-465 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 2000 | unknown (looks like grid-code settings) |
| 466 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 467 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2000 | unknown (looks like grid-code settings) |
| 468 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 469 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2000 | unknown (looks like grid-code settings) |
| 470 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 471 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2000 | unknown (looks like grid-code settings) |
| 472 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 473 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 5000 | unknown (looks like grid-code settings) |
| 474-475 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | all 10000 | unknown (looks like grid-code settings) |
| 476 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 8000 | unknown (looks like grid-code settings) |
| 477 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 478 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 8000 | unknown (looks like grid-code settings) |
| 479 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 480 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 8000 | unknown (looks like grid-code settings) |
| 481 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 2000 | unknown (looks like grid-code settings) |
| 482 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 500 | unknown (looks like grid-code settings) |
| 483 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 5000 | unknown (looks like grid-code settings) |
| 484 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 10000 | unknown (looks like grid-code settings) |
| 485 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 0 | unknown (looks like grid-code settings) |
| 486 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 11500 | unknown (looks like grid-code settings) |
| 487 | — | DY118: 433-437 meter energy totals (does NOT fit); 438+ undocumented in DY118; no community map found | 5000 | unknown (looks like grid-code settings) |
