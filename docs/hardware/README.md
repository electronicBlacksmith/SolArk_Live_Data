# Hardware build guide: passive Modbus tap (XIAO ESP32S3 Plus in the Sol-Ark dongle)

> Custom JLCPCB carrier board (replaces the protoboard): [`../../hardware/carrier/README.md`](../../hardware/carrier/README.md)

Status: Rev A, 2026-10-12. Build package for the hardware in
[`../plans/2026-10-11-xiao-firmware-design.md`](../plans/2026-10-11-xiao-firmware-design.md) §1.
Primary input: [`../research/hardware-electrical.md`](../research/hardware-electrical.md) (cited as "EL §n").
Link facts: [`../serial-link-findings.md`](../serial-link-findings.md).

- Schematic: [`schematic.svg`](schematic.svg). Its reference designators match the BOM below.
- Quick wiring view: [`wiring.mmd`](wiring.mmd) (Mermaid).

Labels used here, as in the electrical doc. **[V]** means verified against a cited primary
source. **[I]** means inferred, with the reasoning given. **[M]** means it must be measured
before you connect anything (see the gates, §5).

---

## 1. Overview

A Seeed XIAO ESP32S3 Plus and a 12 V→5 V buck sit on a small perfboard **carrier** inside
the Sol-Ark Wi-Fi/Ethernet dongle housing. A removable **harness** connects the carrier to
the dongle:

- **Power:** the inverter's 12 V on DB9 pin 9 and pin 5 [M] runs through F1 (PTC, at the DB9
  joint) → D1 (reverse polarity) → TVS1 + C1/C2 → U2 Pololu D24V10F5 → D2 (backfeed
  blocker) → C3/C4 → XIAO **5V pad**.
- **Taps, receive only:** module header H1 pad 9 (R1OUT, inverter→dongle "resp") and pad 10
  (T1IN, dongle→inverter "req"). Each goes through a **10 kΩ resistor soldered at the pad**
  (R1/R2), then a 30 AWG twisted run, the connector, a 1 kΩ (R3/R4) at the XIAO end, and
  on to GPIO1 / GPIO2 (UART1 / UART2 RX). Pad 6 is the signal ground.
- **Disconnect:** a keyed 1×6 2.54 mm socket/header (P1/J1). Unplug it to remove the
  whole carrier without touching the dongle's pads.

**Passive by construction.** The only conductive path from any XIAO pin to pads 9/10 goes
through R1/R2 at the pad. A GPIO that is misconfigured as an output injects at most
3.3 V / 11 kΩ ≈ 0.3 mA, which moves the line ≲ 0.2 V (EL §3.3). No TX pin is wired. The
proxy-mode TX path exists only as a **DNP** reservation (R12/JP1) on the carrier. It has no
connection to the harness.

### Final topology decisions (what changed versus EL §8)

| Topic | EL doc | This build | Why |
|---|---|---|---|
| Backfeed blocker D2 | "SS34/PMEG3020 or LM66100" | **Vishay 1N5822** (3 A, 40 V Schottky, through-hole). LM66100 is an optional upgrade | ≈0.33 V at 0.4 A [V, Vishay Fig. 3]. Leaves ≥0.4 V of headroom in the worst case (§8.5). Through-hole suits perfboard |
| F1 | PTC 0.3 A hold | **Bourns MF-R050** (0.5 A hold / 1.0 A trip, 60 V) | MF-R030 derates to **0.19 A hold at 60 °C** [V, Bourns table]. That is at the 12 V peak (~0.19 A), so it risks nuisance trips. MF-R050 at 60 °C ≈ 0.32 A [I, same derating ratio] |
| TVS1 | SMAJ18A (SMD) | **P6KE22A** (through-hole, VR 18.8 V, Vc 30.6 V) | Same clamp class, below the D24V10F5's 36 V. Through-hole |
| D1 | SS14 | **1N5819** (through-hole equivalent) | Through-hole |
| 12 V wire | 30 AWG Kynar, doubled | **26 AWG stranded silicone** | Mechanical reasons (solid wire fatigues; Kynar has no voltage rating). Also, with the 1.0 A trip it is no longer comfortable for 30 AWG (§8.6) |
| XIAO-end 1 kΩ R3/R4 | optional | **fitted** | 12 V is in the same connector. This bounds the GPIO fault current |
| Mounting | foam tape | **perfboard carrier**, foam-taped. XIAO on sockets if height allows (G10) | Serviceable, and keeps load off the joints |

---

## 2. Netlist and wiring table

Lengths are estimates scaled from `dongle_serial.jpg`, assuming the carrier sits in the free
board area between the black jack and the DB9 [I]. Measure them at G10 and cut to fit, plus
about 15 mm of slack. Wire colours are suggestions. If your Kynar is a single colour, mark
each end with a band of heat-shrink.

| # | From (dongle) | Inline part | Connector | To (carrier / XIAO) | Wire | Colour | Length |
|---|---|---|---|---|---|---|---|
| W1 | J2 DB9 **pin 9** solder joint (+12 V) [M: G3] | **F1** MF-R050, inline at the joint, in adhesive heat-shrink | P1.1 → J1.1 | D1 anode → +12V_P → U2 VIN | 26 AWG stranded silicone | red | ~8–10 cm |
| W2 | J2 DB9 **pin 5** solder joint (GND) [M: G3] | — | P1.2 → J1.2 | carrier GND rail (U2 GND, C1/C2/TVS1, U1 GND pad 13) | 26 AWG stranded silicone | black | ~8–10 cm, twisted with W1 |
| — | — | — | P1.3 / J1.3 | **key**: J1 pin 3 pulled out, P1 hole 3 plugged with a snipped pin | — | — | — |
| W5 | H1 **pad 6** (GND, UT3232G pin 15) | — | P1.4 → J1.4 | carrier GND → U1 GND pad 13 | 30 AWG Kynar | black/white | ~10–14 cm, 3-wire twist with W3/W4 |
| W3 | H1 **pad 9** (R1OUT, "resp") | **R1** 10 kΩ, *soldered into/onto the pad*, heat-shrunk | P1.5 → J1.5 | **R3** 1 kΩ → U1 **D0 / GPIO1** (UART1 RX) [opt C5 to GND, R5 to 3V3] | 30 AWG Kynar | yellow | ~10–14 cm |
| W4 | H1 **pad 10** (T1IN, "req") | **R2** 10 kΩ, at the pad, heat-shrunk | P1.6 → J1.6 | **R4** 1 kΩ → U1 **D1 / GPIO2** (UART2 RX) [opt C6, R6] | 30 AWG Kynar | green | ~10–14 cm |
| — | H1 **pad 7** (UT3232G VCC) | **not wired.** Measure only (G1) | — | — | — | — | — |
| C-1 | — | U2 VOUT → **D2** anode; D2 cathode → +5V_X | on carrier | U1 **5V pad 14** (with C3 100 µF + C4 10 µF *at the pad*) | 26 AWG or component lead | red | ≤ 2 cm |
| C-2 | — | U2 PG (open drain) → **R11** 10 kΩ pull-up to 3V3 *(optional)* | on carrier | U1 **D3 / GPIO4** ("supply OK") | 30 AWG | any | ≤ 3 cm |
| C-3 | — | — | U.FL | **ANT1** FPC antenna on the inside of the housing lid (§6.4) | 100 mm coax (part of ANT1) | — | 100 mm |
| DNP | — | **R12** 1 kΩ + **JP1** pad, *not fitted* | — | U1 D9 / GPIO8 reservation only | **none** | — | — |

Keep apart: route the W1/W2 pair along one side of the housing and the W3/W4/W5 twist along
the other. Keep both away from the dongle's DC-DC inductor and the Ethernet magnetics
(EL §6.3).

---

## 3. Bill of materials

Prices are Digi-Key (DK) qty-1 USD unless noted. Stock was checked on **2026-10-12** from the
distributor pages. "not shown" means the page had no stock figure, so it was **not verified**.

### 3.1 Required (fitted)

| Ref | Qty | Part | Manufacturer P/N | Primary source | Distributor | Purpose | ≈ $ | Stock 2026-10-12 |
|---|---|---|---|---|---|---|---|---|
| U1 | 1 | Seeed XIAO ESP32S3 Plus | 102010671 (SKU) | [Seeed wiki](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/), [Plus schematic v1.1](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_V1.1_SCH_260115.pdf) | [Seeed](https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32S3-Plus-p-6361.html) | MCU, Wi-Fi | **owned** (7.90) | in stock (no qty shown) |
| U2 | 1 | 5 V 1 A step-down regulator | Pololu D24V10F5, item #2831 | [Pololu product page](https://www.pololu.com/product/2831) | [Pololu](https://www.pololu.com/product/2831); DK 2183-2831-ND | 12 V → 5 V | 12.95 | Pololu: "Active and Preferred", qty not shown; DK marketplace 374 |
| F1 | 1 | PTC resettable fuse, radial, 0.5 A hold / 1.0 A trip, 60 V | Bourns **MF-R050** | [MF-R datasheet](https://www.bourns.com/docs/product-datasheets/mf-r.pdf) | [DK](https://www.digikey.com/en/products/detail/bourns-inc/MF-R050/259965) | protects the inverter's 12 V and the harness | 0.47 | 10,865 (Ih 500 mA, It 1 A, 60 V, active) |
| D1 | 1 | Schottky 40 V 1 A, DO-41 | Vishay **1N5819-E3/54** | [Vishay 88525](https://www.vishay.com/docs/88525/1n5817.pdf) | [DK search](https://www.digikey.com/en/products/result?keywords=1N5819-E3%2F54) (DK 1N5819-E3/54GICT-ND) | reverse polarity | 0.71 | 18,013 |
| TVS1 | 1 | TVS 600 W unidirectional, VR 18.8 V, Vc 30.6 V | **P6KE22A**: Vishay P6KE22A-E3/54 (in stock) or Littelfuse P6KE22A | [Vishay P6KE datasheet](https://www.vishay.com/docs/88369/p6ke.pdf); [Littelfuse P6KE datasheet](https://www.littelfuse.com/assetdocs/littelfuse_tvs_diode_p6ke_datasheet.pdf?assetguid=620a3cb5-3282-4670-8b03-66f21bc75523) | [DK (Littelfuse)](https://www.digikey.com/en/products/detail/littelfuse-inc/P6KE22A/688079); [DK search for the Vishay part](https://www.digikey.com/en/products/result?keywords=P6KE22A-E3%2F54) | clamps spikes below U2's 36 V | 0.96 (Vishay, cut tape) | Vishay 2,441; Littelfuse 14-wk lead |
| C1 | 1 | 33 µF 50 V aluminium electrolytic, 105 °C, 6.3×11.2 mm | Panasonic **EEU-FC1H330** | [Panasonic](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFC1H330) | [DK](https://www.digikey.com/en/products/detail/panasonic-industry/EEU-FC1H330/266329) | input bulk; damps LC ringing (Pololu's recommendation) | 0.46 | 1,344 |
| C2 | 1 | 100 nF 50 V X7R radial MLCC | KEMET **C320C104K5R5TA** | [KEMET C1050](https://www.yageogroup.com/content/datasheet/asset/file/KEM_C1050_GOLDMAX_X7R) | [DK](https://www.digikey.com/en/products/detail/kemet/C320C104K5R5TA/818040) | HF bypass at U2 VIN | 1.49 | 109,659 |
| D2 | 1 | Schottky 40 V 3 A, DO-201AD | Vishay **1N5822-E3/54** | [Vishay 88526](https://www.vishay.com/docs/88526/1n5820.pdf) | [DK search](https://www.digikey.com/en/products/result?keywords=1N5822-E3%2F54) (DK 1N5822-E3/54GICT-ND) | **backfeed blocker** between U2 and USB VBUS | 0.91 | 9,997 |
| C3 | 1 | 100 µF 16 V conductive polymer, 18 mΩ, 6.3×9 mm, 105 °C | KEMET **EA750EK107M1CAA** | [KEMET A750](https://www.yageogroup.com/content/datasheet/asset/file/KEM_A4067_A750) | [DK](https://www.digikey.com/en/products/detail/kemet/EA750EK107M1CAA/6196443) | carries Wi-Fi TX bursts **at the 5V pad** | 0.55 | 5,490 |
| C4 | 1 | 10 µF 25 V X7R radial MLCC | TDK **FG16X7R1E106KRT06** | [TDK product search](https://product.tdk.com/en/search/capacitor/ceramic/lead-mlcc/info?part_no=FG16X7R1E106KRT06) (403 to scripted fetch; datasheet not opened) | [DK](https://www.digikey.com/en/products/detail/tdk/FG16X7R1E106KRT06/5802770) | HF bypass at the 5V pad | 0.81 | 10,173 |
| R1, R2 | 2 | 10 kΩ 1/8 W carbon film, axial (small body for dead-bugging) | Stackpole **CF18JT10K0** | [Stackpole CF/CFM datasheet](https://www.seielect.com/catalog/sei-cf_cfm.pdf) (403 to scripted fetch; open in a browser) | [DK search](https://www.digikey.com/en/products/result?keywords=CF18JT10K0) | **passive guarantee**, at the pads | 0.20 | 262,272 |
| R3, R4 | 2 | 1 kΩ 1/8 W axial | Stackpole **CF18JT1K00** | [Stackpole CF/CFM datasheet](https://www.seielect.com/catalog/sei-cf_cfm.pdf) (403 to scripted fetch; open in a browser) | [DK search](https://www.digikey.com/en/products/result?keywords=CF18JT1K00) | GPIO fault limiting at the XIAO end | 0.20 | 70,327 |
| J1 (+ U1 pins) | 1 | 2.54 mm male break-away header, 1×40 | Sullins **PRPC040SAAN-RC** | Sullins (manufacturer page not fetched; DK page lists the datasheet) | [DK](https://www.digikey.com/en/products/detail/sullins-connector-solutions/PRPC040SAAN-RC/2775214) | J1 (6 pins, pin 3 pulled), XIAO pins, U2 pins if needed | 1.23 | 45,559 |
| P1 | 1 | 2.54 mm female socket 1×6 | Sullins **PPTC061LFBN-RC** | [Sullins female header datasheet (DK-hosted)](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/937/Female_Headers.100_DS.pdf) | [DK search](https://www.digikey.com/en/products/result?keywords=PPTC061LFBN-RC) | harness-side plug (solder wires to tails) | 0.47 | 26,643 (DK: contact type "Female Socket", 6 pos, 2.54 mm) |
| PCB1 | 1 | perfboard, plated-through, both sides, 2.54 mm, 50.8×48.3 mm (cut to ~40×30) | DigiKey Standard **DKS-SOLDERBREAD-01** | DK house brand (DK listing is the primary source) | [DK search](https://www.digikey.com/en/products/result?keywords=DKS-SOLDERBREAD-01) | carrier | 2.49 | 3,271 |
| ANT1 | 1 | 2.4/5 GHz flexible adhesive antenna, U.FL (MHF1), 100 mm cable | Molex **146153-0100** | [Molex PS-146153-100](https://www.molex.com/pdm_docs/ps/PS-146153-100.pdf) | [DK](https://www.digikey.com/en/products/detail/molex/1461530100/5455886) | Wi-Fi antenna inside the housing | 2.59 | 46,067 (146153-0050, 50 mm: 16,347) |
| W1/W2 | 1+1 | 26 AWG stranded silicone wire, red + black, 25 ft | Adafruit **2513** (red), **2517** (black) | [Adafruit 2513](https://www.adafruit.com/product/2513) (26 AWG stranded, silicone, 200 °C, 600 V), [Adafruit 2517](https://www.adafruit.com/product/2517) | [DK 2513](https://www.digikey.com/en/products/detail/adafruit-industries-llc/2513/5975011), [DK 2517](https://www.digikey.com/en/products/detail/adafruit-industries-llc/2517/5975015) | 12 V pair; 5 V link | 9.90 | 179 / 185 |
| W3–W5 | — | 30 AWG Kynar wire-wrap wire (solid, silver-plated) | Jonard (KSW series) | [Jonard data sheet](https://jonard.com/sites/default/files/product_files/Data%20Sheet%20-%20Kynar%C2%AE%20Wire_54.pdf) | — | signal taps | **owned** | — |
| — | 1 | 3:1 adhesive-lined heat-shrink, 3 mm→1 mm, 4 ft | TE Raychem **ATUM-3/1-0-MS-STK** | [TE product page](https://www.te.com/en/product-ATUM-3-1-0-MS-STK.html) (403 to scripted fetch) | [DK](https://www.digikey.com/en/products/detail/te-connectivity-raychem-cable-protection/ATUM-3-1-0-MS-STK/12140881) | F1, R1/R2, P1 back-shell, joints | 9.35 | 2,186 (adhesive lining inferred from "dual-wall", check) |
| — | 4 | double-sided urethane foam tape, 1×1 in squares | 3M **4026** (DK 4026-1-X1) | 3M (manufacturer page not fetched) | [DK](https://www.digikey.com/en/products/detail/3m/4026-1-X1/1818867) | carrier mount | 2.00 | 107,520 |
| — | 1 | polyimide (Kapton) tape, 1/2 in | 3M **5413**, 1/2 in × 5 yd (3M-TC 5413-0.5-5) | 3M (manufacturer page not fetched) | [DK search](https://www.digikey.com/en/products/result?keywords=5413-0.5-5) | insulate under the carrier and over the joints | 33.04 | 24 (skip it if you already own Kapton) |
| — | — | hot-melt glue or UV-cure adhesive; neutral-cure RTV only (never acetoxy) | — | — | — | strain relief | owned | — |

**Required subtotal: ≈ $28 for electronics + ≈ $54 for consumables = ≈ $82** (about $49 if you
already own Kapton). The XIAO and the Kynar wire are excluded (owned). Shipping is extra.

### 3.2 Optional (dashed on the schematic; not fitted by default)

| Ref | Qty | Part | Manufacturer P/N | Distributor | Fit when | ≈ $ | Stock |
|---|---|---|---|---|---|---|---|
| C5, C6 | 2 | 100 pF C0G 50 V radial | KEMET **C315C101J5G5TA** ([C1049](https://www.yageogroup.com/content/datasheet/asset/file/KEM_C1049_GOLDMAX_C0G)) | [DK](https://www.digikey.com/en/products/detail/kemet/C315C101J5G5TA/6562399) | decode shows framing errors from glitches (τ ≈ 1 µs) | 1.34 | 1,900 |
| R5, R6 | 2 | 100 kΩ 1/8 W | Stackpole **CF18JT100K** ([Stackpole CF/CFM datasheet](https://www.seielect.com/catalog/sei-cf_cfm.pdf) (403 to scripted fetch; open in a browser)) | [DK search](https://www.digikey.com/en/products/result?keywords=CF18JT100K) | you want a defined idle-high when a wire comes off. **Never** the internal pull-up | 0.20 | 206,926 |
| R11 | 1 | 10 kΩ 1/8 W | CF18JT10K0 (the R1 part) | above | PG → GPIO4 "supply OK" health bit | 0.10 | above |
| XIAO sockets | 2 | 2.54 mm female 1×7 | Sullins PPTC071LFBN-RC | [DK search](https://www.digikey.com/en/products/result?keywords=PPTC071LFBN-RC) | G10 shows ≥ ~18 mm of height above the dongle PCB (makes the XIAO itself removable) | ~1.10 | **not checked** |
| ANT1 alt | 1 | the antenna shipped with the XIAO Plus | (Seeed accessory) | — | only if it fits; an FPC is preferred | 0 | — |
| D2 alt | 1 | TI **LM66100** ideal diode (SC-70-6, 0.65 mm pitch) + an SC-70-6 (0.65 mm) to DIP adapter. **Not** the PA0085, which is 0.95 mm SOT-23-6. Adapter part not identified | LM66100DCKR ([TI](https://www.ti.com/product/LM66100)) | TI "Order now" (active); **distributor stock not checked** | G9 measures VIN headroom < 0.3 V (not expected) | ~1 + adapter | not checked |

**Alternate A, only if G1 measures pad 7 at about 5 V** (boxed on the schematic). Fit U3 and
R7/R8 *instead of* R3/R4, and omit R5/R6:

| Ref | Qty | Part | P/N | Distributor | ≈ $ | Stock |
|---|---|---|---|---|---|---|
| U3 | 1 | dual Schmitt buffer, 5.5 V-tolerant inputs, Ioff | TI **SN74LVC2G17DBVR** ([TI](https://www.ti.com/product/SN74LVC2G17)) | [DK](https://www.digikey.com/en/products/detail/texas-instruments/SN74LVC2G17DBVR/479735) | 0.20 | in stock (the page qty 398,914 may be a Nexperia equivalent) |
| — | 1 | SOT-23-6 → DIP-6 adapter | Chip Quik **PA0085** ([datasheet](https://www.chipquik.com/datasheets/PA0085.pdf)) | [DK](https://www.digikey.com/en/products/detail/chip-quik-inc/PA0085/5014712) | 2.69 | 345 |
| C7 | 1 | 100 nF 50 V X7R | C320C104K5R5TA | as C2 | 1.49 | as C2 |
| R7, R8 | 2 | 100 Ω 1/8 W | Stackpole **CF18JT100R** ([Stackpole CF/CFM datasheet](https://www.seielect.com/catalog/sei-cf_cfm.pdf) (403 to scripted fetch; open in a browser)) | [DK search](https://www.digikey.com/en/products/result?keywords=CF18JT100R) | 0.20 | 91,582 |
| R9, R10 | 2 | *fallback instead of U3:* 22 kΩ GPIO→GND dividers | Stackpole **CF18JT22K0** ([Stackpole CF/CFM datasheet](https://www.seielect.com/catalog/sei-cf_cfm.pdf) (403 to scripted fetch; open in a browser)) | [DK search](https://www.digikey.com/en/products/result?keywords=CF18JT22K0) | 0.20 | 66,602 |

**DNP (do not populate): R12 (1 kΩ) + JP1.** This is a proxy-mode TX reservation from
D9/GPIO8. It is not in any order, not fitted and not wired. Fitting it needs a separately
approved proxy-mode design (CLAUDE.md rule 6). Pad 10 is driven by the dongle ESP32's TX, so
a proxy would also mean cutting a dongle trace. That is a new design, not a population
option.

Optional parts subtotal: ≈ $6 (Alternate A ≈ $4.60 more).

### 3.3 Bench and test gear (recommended, cheap)

| Item | P/N | Distributor | ≈ $ | Stock | Why |
|---|---|---|---|---|---|
| USB isolator, low/full speed (12 Mbps), isolated side 100 mA @ 5 V | Adafruit **2107** (ADuM4160 + ADuM5000), [Adafruit page](https://www.adafruit.com/product/2107) | [DK](https://www.digikey.com/en/products/detail/adafruit-industries-llc/2107/6238004) | 34.95 | DK 166 | USB debugging **while installed**. Use it with a data-only cable (§6.6) |
| 12 V 1 A wall adapter, 5.5×2.1 mm | Bel Power **SWI12-12-N-P5** ([datasheet](https://www.belfuse.com/media/datasheets/products/power-supplies/SWI12-N.pdf)) | [DK](https://www.digikey.com/en/products/detail/bel-power-solutions/SWI12-12-N-P5/5287239) | 18.77 | 1,441 | bench-power the carrier (and, after G3, the dongle) away from the inverter |
| barrel jack → screw terminal | Adafruit **368** ([Adafruit page](https://www.adafruit.com/product/368)) | [DK](https://www.digikey.com/en/products/detail/adafruit-industries-llc/368/5629434) | 2.00 | 5,422 | adapter to the harness 12 V pair |
| 100 Ω 2 W resistor (dummy load, 120 mA at 12 V) | Vishay **PR02000201000JR500** (Vishay PR02 datasheet not fetched) | [DK search](https://www.digikey.com/en/products/result?keywords=PR02000201000JR500) | 0.41 | 5,969 | G4: DB9 12 V sag under load |
| USB-C inline V/A meter | Plugable **USBC-VAMETER3** | Amazon/CDW; **not stocked by DK, Mouser, Pololu or Seeed; stock not verified** | ~30 | — | optional. A DMM in series on the 12 V side does the same job for the bench test |
| bench supply with current limit | any 0–30 V / 3 A unit | — | — | — | optional. Nicer than the wall adapter for G9 (you can set a 0.3 A limit) |

Bench subtotal: ≈ $56 (≈ $86 with the USB meter).

### 3.4 Shopping list by vendor

- **Digi-Key** (one order): MF-R050 ×1, 1N5819-E3/54 ×1, P6KE22A-E3/54 ×1,
  EEU-FC1H330 ×1, C320C104K5R5TA ×1 (×2 if Alternate A), 1N5822-E3/54 ×1,
  EA750EK107M1CAA ×1, FG16X7R1E106KRT06 ×1, CF18JT10K0 ×5, CF18JT1K00 ×4,
  PRPC040SAAN-RC ×1, PPTC061LFBN-RC ×2, DKS-SOLDERBREAD-01 ×1, Molex 1461530100 ×1,
  Adafruit 2513 + 2517, ATUM-3/1-0-MS-STK ×1, 3M 4026-1-X1 ×4, 3M 5413-0.5-5 (if needed).
  Optional: C315C101J5G5TA ×2, CF18JT100K ×2, PPTC071LFBN-RC ×2. If pad 7 = 5 V:
  SN74LVC2G17DBVR ×2, PA0085 ×1, CF18JT100R ×2, CF18JT22K0 ×2.
  Bench: Adafruit 2107, SWI12-12-N-P5, Adafruit 368, PR02000201000JR500 ×2.
  Spares are included where parts are pennies (resistors ×4–5, a second socket).
- **Pololu:** D24V10F5 #2831 ×1 (×2 for a spare is sensible). Digi-Key marketplace also lists it.
- **Seeed:** nothing. The XIAO is owned.
- **Elsewhere (optional):** Plugable USBC-VAMETER3.

---

## 4. Re-verification of the electrical doc (2026-10-12)

| # | Claim (EL doc) | Primary source checked | Result |
|---|---|---|---|
| 1 | The XIAO Plus 5V pad is the USB VBUS net with no diode | Seeed Plus schematic v1.1, sheet 4: U2 "XIAO-HALF-HOLE-23P" pin 14 = **VBUS**. USB0 (UBF31-0171) A4/B9 and B4/A9 = **VBUS** with no series element. D2 **LMBR4010BST5G** goes from VBUS to VIN of U3 **SGM6029CYG/TR** buck (L4 470 nH, "Imax=600mA" on VCC_3V3). Q1 PMOS gate on VBUS. U4 SGM40567 charger VIN on VBUS. CC1/CC2 have 5.1 kΩ to GND (sink only) | **Agree [V].** No fuse or diode between the USB-C VBUS and the 5V pad |
| 2 | D0 = GPIO1, D1 = GPIO2, safe | Schematic U2 pins 1/2 = GPIO1_D0, GPIO2_D1. ESP32-S3 datasheet v2.2: strapping pins are **GPIO0, 3, 45, 46** only. Pin table: GPIO1/2 are "IE" at reset (no pull). Flash/PSRAM pins are GPIO26–37, not exposed | **Agree [V]**, with one addition the EL doc lacks: datasheet **Table 2-2: GPIO1–14 output a ~60 µs low-level glitch at power-up**. Through R1/R2 that is the same ≤ 0.33 mA bound, harmless. It is the strongest reason the at-pad resistor is mandatory |
| 3 | D24V10F5 specs and fit | [Pololu #2831](https://www.pololu.com/product/2831): 5.1–36 V in, 5 V ±4 %, 1 A, Iq ≈ 200 µA, **18×13×3.5 mm**, PG/SHDN/VIN/GND/VOUT, no reverse protection, 33 µF/50 V recommended. Seeed's KiCad footprint (`OPL_Kicad_Library/XIAO-ESP32-S3-DIP.kicad_mod`): pin rows at ±7.62 mm, so **15.24 mm row spacing, 2.54 mm pitch** (perfboard-compatible) | **Specs agree [V].** Fit is **[I]**: scaled from the photo using the DB9 shell (standard 30.8 mm flange, 25 mm screw pitch), the free board area between the black jack and the DB9 is roughly 30–35 × 35–40 mm. Side by side, the XIAO (21×17.8) and the regulator (18×13) need about 38×28 mm. It is tight but plausible. **Housing height is unknown** (G10). The EL doc's 78.5×153×34.5 mm figure is for the *4G* dongle, a different product, so it is not used here |
| 4 | 10 kΩ series + internal pull-up math | Datasheet Table 5-4: RPU **45 kΩ typ, no min/max given**. VIL max 0.25×VDD = 0.825 V. VIH min 2.475 V. CIN 2 pF. IIH/IIL ≤ 50 nA | **Agree [V data, I math].** Low level with the internal PU: 3.3×10/(10+45) ≈ 0.60 V typical, rising to ~0.76 V at 33 kΩ. That eats most of the 0.825 V margin, and the PU spread is unpublished. **Internal pulls OFF.** External 100 kΩ (R5/R6) → ≈0.30 V (0.33 V with R3/R4). The RC τ ≈ 11 kΩ × 12 pF ≈ 0.13 µs ≪ 104 µs bit |
| 5 | Backfeed-diode drop keeps 3V3 in regulation at the peak | SGM6029 datasheet: VIN 1.95–5.5 V (6 V abs max), **100 % duty mode**, high-side RDSON 185 mΩ typ / **310 mΩ max**, U3 is the **C variant with output discharge** (RDSCH_SW 4–11 Ω). LMBR4010 (Leshan): Vf ≈ 0.39 V @ 0.1 A, ≈ 0.5 V @ 0.5 A. 1N5822 Fig. 3: ≈ 0.33 V @ 0.4 A, 25 °C | **Agree, with numbers (see §8.5).** It is a *buck*, not an LDO. Worst-case VIN ≈ 3.95 V against ≈ 3.55 V needed, so a ≥ 0.4 V margin. A Schottky is enough **only if it is a low-Vf 3 A-class part** (an SS14 at ~0.5 V would cut the margin to ~0.25 V) |

Related: Sol-Ark DB9 12 V current rating is still **unpublished** (EL §5.1), so G4 matters.

---

## 5. Measure-before-connecting gates

Reconciled with EL §9. G1–G11 are EL items 1–11 (re-ordered). G12–G14 are new. **Do every
gate in order. A failed gate stops the build.** Unless a gate says otherwise, the dongle is
powered from the inverter and **nothing is connected to pads 9/10**. Use a DMM, plus a scope
or the Saleae (listen-only).

| Gate | Measure | Pass | If not |
|---|---|---|---|
| **G1** | H1 **pad 7 → pad 6** DC voltage | 3.3 V ±0.2 → baseline build | ≈ 5 V → **Alternate A** (U3, or the R9/R10 dividers). Anything else → stop |
| **G2** | **Pads 9 and 10 idle** voltage (expect ≈ pad 7). Scope VOH/VOL during traffic | idle ≈ pad 7, VOL < 0.4 V, VOH > pad 7 − 0.6 V | investigate before tapping |
| **G3** | **DB9 pin identification:** which pins are populated, and which carries +12 V relative to which GND. Expected 9 (+) and 5 (−) from a third-party source | polarity and pins confirmed | re-assign W1/W2. D1 protects against reversal, but don't rely on it |
| **G4** | **DB9 12 V:** no-load voltage; with the **100 Ω / 2 W dummy** in parallel (sag); ripple on a scope. Record min and max | 11.4–13 V, sag < 0.5 V, ripple < 200 mV p-p [I thresholds] | sag > 1 V → the port is weak: cap Wi-Fi TX power and re-measure with the dongle and XIAO running |
| **G5** | **Continuity: DB9 GND (pin 5) ↔ H1 pad 6** (< 1 Ω). Also, for information, DB9 GND ↔ RJ45 shield and ↔ inverter chassis | < 1 Ω | if not continuous, the signal-ground plan is wrong: stop |
| **G6** | **Dongle input path:** fuse, diode or regulator after DB9 pin 9? Pick the tap point (before the dongle's own fuse is preferable) | tap point chosen | — |
| **G7** | **Dongle current draw** at 12 V (meter in series, via a DB9 breakout, if available) | baseline recorded | optional |
| **G8** | **XIAO bench:** continuity 5V pad ↔ USB-C VBUS pin (expect a **short**, confirming §4 row 1). U.FL antenna attached before any RF test | short | if not a short, re-check the board revision |
| **G9** | **Carrier bench test** (no dongle; §7 steps 4–6): 12 V adapter → harness pins 1/2 → carrier. Measure +12V_P, **+5V_X at the 5V pad: expect ≈ 4.6–4.7 V idle**, and the **3V3 pad under a Wi-Fi TX test: ≥ 3.2 V, no brown-out resets**. 12 V current: ~50 mA average, < 250 mA peak | all pass | low 5V pad → check the D2 part. 3V3 sag → add the LM66100 option |
| **G10** | **Space and height:** free area and height inside the closed housing, and the clearance to the ESP32-SOLO-1 antenna | carrier ≈ 40×30 mm fits. Height ≥ ~18 mm → XIAO on sockets, else solder the XIAO pins directly (~9 mm) | mount the carrier on the inside of the lid instead |
| **G11** | **Thermal:** in-housing temperature on the inverter on a hot afternoon (logging sensor), before relying on the 65 °C (85 °C with ECC) rating | < 60 °C | see §6.5 |
| **G12** *(new)* | **Data-only USB cable** (§6.6): VBUS at the C plug with the cable plugged into a powered host | 0 V. With the XIAO powered from 12 V, the host still enumerates it [I] | re-tape the plug |
| **G13** *(new)* | **Passive check:** a Saleae listen-only capture on pads 9/10 for 15 min, **before and after** the taps are connected (XIAO powered and running, and also with the XIAO unpowered) | 100 % CRC, the same 10 s / 30 s schedule, reply latency 24–26 ms, the same edge levels (compare with the 510/510 baseline) | disconnect and investigate |
| **G14** *(new, optional, **needs your approval**)* | **Fault injection:** dongle on the bench 12 V adapter (after G3), **no inverter connected** (pad 9 then idles high from the UT3232). A test firmware deliberately drives GPIO1 low. Scope pad 9 | shift ≤ 0.2 V, as predicted | this deliberately drives a pin, so it is bounded but not "listen-only". Do it only with an explicit OK |

---

## 6. Build notes (robustness)

### 6.1 Wire gauge

- **Power, 12 V pair (W1/W2): 26 AWG stranded silicone.** Electrically, 30 AWG would be fine:
  0.34 Ω/m [I] × ~0.2 m round trip × 0.2 A peak ≈ 14 mV. But solid 30 AWG fatigues where it
  flexes at the disconnect, and Kynar wire-wrap wire is "not voltage rated" [V, Jonard]. With
  F1 at 0.5 A hold / 1.0 A trip, a fault can push ~1 A through the wire until F1 trips. That
  is above the commonly quoted ~0.86 A chassis ampacity for 30 AWG [I, secondary table],
  and well within 26 AWG's (~2.2 A [I]). **This disagrees with EL §7's "30 AWG doubled is
  acceptable".**
- **5 V link (U2 → D2 → 5V pad):** on the carrier, ≤ 2 cm, component leads or 26 AWG.
- **Signals (W3/W4/W5):** 30 AWG Kynar, 3-wire twist (about 1 twist per cm). Kynar is fine
  here: µA currents, 105 °C insulation [V].

### 6.2 Strain relief

- Anchor every wire within 5 mm of its joint. Put Kapton tape under it, then a dab of
  hot-melt or UV-cure adhesive over the tape (so the glue never touches the pad directly and
  can be peeled for service). If you use RTV, it must be neutral-cure, never acetoxy.
- **R1/R2 at the pads:** cut the pad-side lead to ~3 mm and solder it into the header hole or
  pad. Slide a 3 mm adhesive heat-shrink over the resistor and the Kynar joint. Then tack the
  heat-shrink to the board with a dab of hot-melt. The resistor body must not lever the pad.
- **F1 at DB9 pin 9:** same treatment. Heat-shrink over the PTC and both joints, tacked
  down. Do not solder to the ESP32-SOLO-1 castellations (EL §7).
- **P1 (harness plug):** solder W1–W5 to the socket tails, then cover all the tails with one
  piece of 6 mm adhesive heat-shrink to make a moulded back-shell. Pull J1 pin 3 out with
  pliers, and plug P1 hole 3 with a snipped header pin. Now the plug cannot be inserted
  offset or reversed in a way that puts 12 V on a signal pin.

### 6.3 Mounting

- Layout on the carrier: XIAO and U2 side by side, J1 along the edge facing the harness,
  and the XIAO's **USB-C at a carrier edge** so it stays reachable. U2 is a module on its
  own 0.1" pins. D1/TVS1/C1/C2 sit by J1. D2/C3/C4 sit by the XIAO 5V pad.
- Height (G10): if there is room, solder male pins to the XIAO and plug it into 2× 1×7
  sockets, so the XIAO itself is removable. Otherwise solder the XIAO's pins straight into
  the perfboard. The carrier is still removable at P1/J1.
- Fixing: a layer of Kapton on the dongle PCB area, then 2–4 squares of **3M 4026** foam
  tape under the carrier. Put it in the free area between the black jack and the DB9 [I],
  **not** over the dongle's DC-DC converter. If the PCB area is too small, put the carrier on
  the inside of the lid. Either way the harness must have slack, so no joint carries load
  when the lid closes.

### 6.4 Antenna (ANT1)

The ESP32-SOLO-1 and its PCB antenna are at the **opposite end from the DB9** (the left end
in `dongle_serial.jpg`). The carrier sits near the DB9. So stick the Molex FPC on the
**inside of the housing lid over the middle/DB9 half of the board**, **≥ 3 cm** (in practice
~6–8 cm) from the SOLO-1 antenna, **oriented perpendicular to it**, and not directly over
the DB9 metal shell or the black jack [I]. Route the 100 mm coax without sharp bends (radius
≥ 5 mm). Snap the U.FL on once and hold it with a strip of Kapton (U.FL connectors are rated
for few mating cycles). Never transmit with the antenna unplugged. Check RSSI in health
telemetry. If RSSI is worse than about −75 dBm, consider an RP-SMA bulkhead (it breaches the
housing seal). The XIAO's own shipped antenna is an alternative only if it fits.

### 6.5 Heat

- ESP32-S3R8: ambient **65 °C** max, **85 °C with PSRAM ECC** [V, datasheet Table 1-1 note 3].
  The XIAO board is rated −20…65 °C [V, Seeed]. The inverter is rated to 55 °C ambient, and
  the inside of the housing can run 10–15 °C hotter [I]. So **`CONFIG_SPIRAM_ECC_ENABLE=y` is
  mandatory**. The board-level 65 °C is a residual risk.
- U2 dissipates ~0.1 W average (85 % efficiency at ~0.6 W) [I]. Keep the XIAO's RF shield
  away from the dongle's own regulator. Cap Wi-Fi TX power (configurable). Publish the die
  temperature. G11 decides.
- Electrolytic C1 has a 1000 h rating at 105 °C. The 10 °C rule of thumb gives ≈ 20 k h at
  ~60 °C [I]. It only damps ringing, and it wears out by losing capacitance, not by shorting.
  Replace it at the 2-year service, or substitute a longer-life series if one is in stock.

### 6.6 USB while installed (backfeed and ground hazard)

- D2 stops the regulator and the host's VBUS from fighting. **Still, never plug a laptop
  straight into the installed XIAO.** The inverter's comms ground and the laptop ground form
  a loop (EL §5.3).
- Use the **Adafruit 2107 isolator** with a **data-only cable**. Its isolated 5 V is only
  100 mA [V, Adafruit] and would try to feed Wi-Fi bursts through the 5V pad. Cover the VBUS
  pin (pin 1) of the USB-A plug of an A-to-C cable with a sliver of Kapton, and label the
  cable "DATA ONLY". The XIAO stays powered from the inverter. ESP32-S3 USB-Serial/JTAG needs
  no VBUS to enumerate [I]: confirm at G12 on the bench. Prefer OTA in service.
- With USB attached and no 12 V, D2 also stops the laptop from back-powering U2 (reverse
  leakage ≈ 10 µA at 5 V, 25 °C, [V] Vishay Fig. 4).
- **[I]** With 4.6–4.9 V on VBUS and no battery, the on-board SGM40567 charger is powered,
  and its CHG LED may blink or glow. This is harmless (a few mA).

### 6.7 Conformal coating

**Do not coat the XIAO** (U.FL, USB-C, buttons, RF matching network, sockets). The housing is
closed and the board sits indoors or under the inverter's own protection. If the site is
humid or coastal, an acrylic coating (removable for rework) on the **carrier's solder side
only**, masking J1, is acceptable [I]. It is not in the BOM.

---

## 7. Assembly and bench-test sequence

1. **Gates G1–G8** with the dongle on the inverter. Stop on any failure.
2. **Prepare the XIAO (bench):** antenna on. Flash the test firmware over plain USB (not
   installed yet, so no isolator is needed). Confirm G8.
3. **Build the carrier:** fit J1 (6 pins, pull pin 3), D1, TVS1 (band toward +12V_P),
   C1 (observe polarity), C2, U2 (on its pins, label side up for the pinout), D2 (band toward
   the 5V pad), C3 (polarity) and C4 at the 5V pad, R3/R4, and the XIAO (sockets or direct).
   Optional: R11, C5/C6, R5/R6 only if needed. **Leave R12/JP1 empty (DNP).** Check for
   shorts: +12V_P–GND, +5V_X–GND, 3V3–GND, and J1.1–J1.5/J1.6.
4. **Power test without the XIAO firmware load:** 12 V adapter → Adafruit 368 → J1.1 (+) /
   J1.2 (−), with a DMM in series on the + lead (or a bench supply limited to 0.3 A). Check
   +12V_P ≈ 11.7 V (after D1), U2 VOUT ≈ 5.0 V, 5V pad ≈ 4.6–4.7 V.
5. **Current and stability:** run a Wi-Fi TX-heavy test (iperf or MQTT flood). Record 12 V
   average and peak current (expect ~50 mA average). Scope the 5V pad and 3V3 during
   bursts (G9: 3V3 ≥ 3.2 V, no brown-out resets in 10 min). Reverse-polarity test: briefly
   swap the leads. Nothing should conduct (D1).
6. **USB with 12 V present:** connect via the isolator and the data-only cable. Check G12
   (enumerates, 0 V on the cable VBUS). Optionally, with a *plain* cable to a battery-powered
   laptop (no charger), confirm that the 5V pad follows the higher of the two sources and
   nothing gets warm (proves D2).
7. **Build the harness:** solder R1/R2 at pads 9/10 and F1 at DB9 pin 9 with the **dongle
   unplugged from the inverter**. Then the W1–W5 runs, twisting and anchoring, and P1 with
   its back-shell and key. Check: pad 9 ↔ P1.5 = 10 kΩ, pad 10 ↔ P1.6 = 10 kΩ,
   pad 6 ↔ P1.4 < 1 Ω, DB9 pin 9 ↔ P1.1 ≈ 1 Ω (F1), and no continuity between P1.1 and
   P1.4–6.
8. **Passive link check (G13), part 1:** plug the dongle into the inverter with P1
   **unplugged**. Saleae listen-only capture for 15 min (baseline).
9. **Part 2:** mate P1/J1 (the XIAO is now powered from the inverter). Capture again for 15 min
   with the XIAO running the RX-only firmware. Compare CRC, schedule, latency and levels.
   Also capture with the XIAO held in reset (RST button) or unpowered. Pass = identical link
   behaviour.
10. **Optional G14** fault injection, only with your explicit approval.
11. **Mount:** foam-tape the carrier, place ANT1, dress the harness, close the housing
    (G10/G11). Check RSSI and die temperature over a hot afternoon.

---

## 8. Facts to carry into the firmware config

These are defaults. Every one is configurable (standing rule 2).

| Item | Value | Source |
|---|---|---|
| resp RX (pad 9) | **GPIO1 (D0)**, UART1 RX, 9600 8N1 | [V] schematic / findings |
| req RX (pad 10) | **GPIO2 (D1)**, UART2 RX, 9600 8N1 | [V] |
| Pulls on GPIO1/2 | **internal pull-up and pull-down OFF** | §4 row 4 |
| TX pins | **none configured** for UART1/2 (set TX to "no pin") | passive rule |
| RX idle timeout | ≥ 35 bit times (4 symbols via the public API) | EL §2 |
| Status LED | GPIO21, active-low (on board) | [V] |
| Button | GPIO0 BOOT, read only after boot | [V] |
| Supply-OK input (optional R11) | GPIO4 (D3), PG open-drain: low = 5 V out of window | [V] Pololu |
| Reserved/avoid | GPIO3 (strap), GPIO43/44 (UART0 console), GPIO10 (ADC_BAT), GPIO39–42 (JTAG), GPIO19/20 (USB), GPIO26–37 (flash/PSRAM) | [V] |
| DNP TX reservation | GPIO8 (D9): **never** configured as an output in v1 | this doc |
| sdkconfig | **`CONFIG_SPIRAM_ECC_ENABLE=y`** (85 °C rating; loses 1/16 of PSRAM) | [V] datasheet, Kconfig to be confirmed on the pinned IDF |
| Radio | Wi-Fi TX power cap (configurable, e.g. 15 dBm), **BLE off**, **no SoftAP after provisioning** | EL §6.2 |
| Health | die temperature, RSSI, PG state, brown-out/reset reason | §6.5 |
| Startup | expect a ~60 µs low glitch on GPIO1/2 at power-up (datasheet Table 2-2). It is absorbed by R1/R2. Ignore the first partial frame | [V] |

## 8.5 Headroom calculation (backfeed solution)

Load: ≈ 450 mA at 3V3 peak (EL §4.1). The SGM6029 is in 100 % duty near dropout.

- **VIN needed** ≈ 3.3 V + I × (RDSON_HS + DCR_L4) ≈ 3.3 + 0.45 × (0.31 max × ~1.3 hot
  + ~0.05) ≈ **3.5–3.55 V** [V RDSON; I temperature factor and DCR].
- **VIN available, worst case** = U2 min 4.80 V (5 V −4 %) − D2 1N5822 ≈ 0.35 V − LMBR4010
  ≈ 0.47 V (≈0.4 A) − wiring ≈ 0.02 V ≈ **3.96 V**. Typical: 5.0 − 0.33 − 0.45 ≈ **4.2 V**.
- **Margin ≥ 0.4 V.** The Schottky solution holds. C3 (18 mΩ polymer) covers the
  millisecond bursts.
- Alternatives considered:
  - **LM66100 ideal diode**: 79 mΩ, so +0.3 V of margin. But it is a 5.5 V-max SC-70 part,
    so on perfboard it needs a breakout. Kept as an option, not needed.
  - **Raise the regulator output**: rejected. The D24V10F5 is fixed at 5 V. A 6 V module
    puts ~5.7 V on VBUS, above the SGM6029's 5.5 V operating maximum (6 V abs), and onto the
    charger IC.
  - **3.3 V buck into the 3V3 pad**: rejected. On the XIAO, U3 is the SGM6029 **C**
    variant, which has an output-discharge switch (4–11 Ω, VOS→GND when disabled), and its
    EN is tied to VIN. If an external 3.3 V is present while the XIAO's VIN is absent or
    dipping, that switch can sit across the external supply. The high-side body diode also
    back-charges VIN through L4 and wakes the IC into a regulator fight. It also bypasses
    the board's sequencing. [V datasheet features, I consequence]

## 8.6 Wire check numbers

30 AWG ≈ 0.34 Ω/m; 26 AWG ≈ 0.13 Ω/m [I, standard AWG table]. Peak 12 V current ≈ 0.19 A
(EL §4.1). F1 MF-R050 trips at 1.0 A (23 °C) [V].

---

## 9. Verified vs inferred

**Verified [V] (primary source named):**
- 5V pad = USB-C VBUS with no diode. LMBR4010 → SGM6029C buck. Imax 600 mA note. CC 5.1 kΩ
  sink (Seeed Plus schematic v1.1, sheet 4).
- D0 = GPIO1, D1 = GPIO2. Footprint rows 15.24 mm apart at 2.54 mm pitch (Seeed schematic
  and Seeed KiCad library).
- Strapping pins 0/3/45/46. The GPIO1–14 60 µs power-up low glitch. RPU 45 kΩ typ. VIL/VIH.
  CIN 2 pF. S3R8 65/85 °C with ECC (ESP32-S3 datasheet v2.2).
- SGM6029: 1.95–5.5 V, 100 % duty, RDSON HS 185/310 mΩ, discharge switch (SG Micro datasheet).
- D24V10F5 specs and dimensions (Pololu). MF-R030/MF-R050 ratings and derating table
  (Bourns). P6KE22A VR/VBR/Vc (Littelfuse via DK). 1N5822 Vf and leakage curves (Vishay).
  LM66100 (TI). Adafruit 2107 speed and 100 mA (Adafruit). Stock figures as listed (DK pages,
  2026-10-12).

**Inferred [I]:**
- Fit inside the housing (photo scaling). Wire lengths.
- Housing temperature rise. C1 life at 60 °C. MF-R050 hold at 60 °C (by derating ratio).
- 12 V port capacity (unpublished). G4 thresholds. 30/26 AWG ampacity and resistance.
- Antenna placement and RSSI.
- USB enumeration without VBUS. Charger LED behaviour.
- LMBR4010 Vf: read from a third-party-hosted copy of the Leshan sheet, with an unclear
  column layout.
- 1N5819 Vf at 0.2 A (graph not read; only the 0.60 V @ 1 A max is verified).

**Not checked:** PPTC071LFBN-RC (optional XIAO sockets); LM66100 distributor stock and an
SC-70 adapter; the TDK FG16, Sullins male-header, 3M, TE and Vishay PR02 manufacturer pages
(several returned 403 to scripted fetches); the USB-C meter's stock; the exact antenna in the
XIAO Plus box; the exact Digi-Key detail URLs for the 1N5819/1N5822/CF18 parts (search links
are given instead).

## 10. Open questions

1. Pad 7 voltage (G1) decides baseline versus Alternate A.
2. DB9 pin assignment and 12 V capacity (G3/G4). Sol-Ark publishes no rating for the port.
3. Internal housing height and free area (G10) decide XIAO on sockets versus soldered, and
   carrier on the PCB versus on the lid.
4. In-housing temperature on a hot day (G11). Is the board-level 65 °C acceptable with ECC on?
5. Does the dongle have its own input fuse or diode? Where exactly should we tap (G6)?
6. Confirm on the bench that the ESP32-S3 enumerates over a VBUS-less cable (G12).
7. Whether to run G14 (deliberate bounded drive): needs your approval.
