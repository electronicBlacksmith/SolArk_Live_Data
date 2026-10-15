# Rev B-diy changes (2026-10-13)

This is the lowest-cash, hand-soldered, minimum-fix variant of the Rev A carrier.

Item numbers refer to `review-synthesis.md`. Every claim is marked:
- **[V]**: read today (2026-10-13) at the URL given.
- **[I]**: inferred. Open [I] items are listed in `OPEN-ITEMS.md`.

Verification run:
- `sh scripts/build.sh` exits 0 with ERC 0, DRC 0, 0 unconnected items and 0 parity issues (all severities).
- `pytest tests` reports 25 passed (after the 2026-10-14 small fixes below).

## Outline

**29.0 x 30.0 mm** (Rev A was 27 x 27). Both axes grew.

| Axis | Rev A | Rev B | Why it grew |
|---|---|---|---|
| x, along the J1 edge, perpendicular to the USB-C edge | 27 | 29 | The left strip widened from 4.4 to 6.4 mm to hold two columns of 0603 parts plus the SOT-23-6 buffer. |
| y, along the USB-C edge, perpendicular to the J1 edge | 27 | 30 | The 8 mm band between the XIAO courtyard and J1 cannot hold TVS1, D1 and the Bourns 1812 fuse land stacked (8.9 mm). |

- The USB-C receptacle is still flush with the right edge.
- Nothing on the board extends beyond the outline. The exception is the J1 harness wires, which leave the bottom edge (see item 2).
- Test: `test_outline_within_the_user_limit`.

## Fixes

| # | Fix | What changed | Verified by |
|---|---|---|---|
| 1 | Socket holes | **Mill-Max receptacles dropped.** The XIAO is soldered on Sullins PRPC040SAAN-RC header pins (0.64 mm square [V]). Drill 1.10 mm gives a finished hole of 1.02-1.23 mm at JLC's PTH tolerance of +0.13/-0.08 mm. The pin diagonal is 0.905 mm nominal and 0.933 mm at 0.66 mm, so clearance is 0.09 mm at the worst case. Sullins recommends a 1.00 mm hole [V], so ours is about 0.02-0.23 mm larger. Rings: top 1.45 mm (0.175 mm designed, 0.11 mm worst case); bottom solder ring 1.8 mm. OSH Park's hole tolerance is ±0.064 mm, inside JLC's. | `test_xiao_hole_fits_a_0p64_square_header_pin_at_every_tolerance` |
| 2 | J1 plug overhang | The JST GH is gone. J1 is now 6 plated wire pads on 2.54 mm pitch (1.0 mm drill, 1.8 mm pad) along the bottom edge. The harness carries the in-line disconnect: a Sullins PPTC061LFBN-RC female housing mating with a 6-pin section of PRPC040 header (plastic kept), soldered to the J1 wires. Nothing on the board overhangs. **Flag:** the wires leave across the J1 edge, so the wire bend extends beyond the outline (OPEN-ITEMS O2). | `test_harness_pinout`; render_bottom.png |
| 3 | Stack height | Model: 1.0 mm trimmed tail + 1.6 mm board + 0.3 mm gap + 4.9 mm XIAO ≈ **7.8 mm**, against the 9.0 mm limit. The header plastic (2.50 mm [V]) is removed after soldering; leaving it on gives about 10.0 mm. All four numbers except the board thickness are [I]. What to measure is in OPEN-ITEMS O1. | `gen_lib.py` constants; render_side_*.png |
| 4 | Castellation short | The castellation (SMD) pads are gone from the XIAO footprint; only THT pins remain. The 1.45 mm top ring clears Seeed's Plus pads 15-23 by **0.174 mm** when the XIAO sits flush. | `test_top_pad_clears_the_plus_castellations_when_flush`, `test_xiao_footprint_has_no_castellation_pads` |
| 5 | Laptop backfeed | "J1 OFF FOR USB / unplug harness before USB-C" is on the bottom silk and in the README. (The laptop test step in `docs/hardware/README.md` is outside this directory and is not edited here.) | render_bottom.png |
| 6 | RX-only buffer | **U3 SN74LVC2G17DBVR** sits between the taps and the GPIOs. The chain is: J1 → R3/R4 1k → U3 inputs (R5/R6 100k bias to 3V3) → U3 outputs → R7/R8 1k → GPIO1/GPIO2. No populated path exists from any GPIO to J1: the GPIO side sees only U3 outputs. R7/R8 limit a boot glitch on GPIO1/2 to 3.3 mA of contention. C5/C6 (DNP) are deleted; U3's Schmitt inputs plus 11 k of series resistance cover item 11. | `test_buffer_is_the_only_path_from_tap_to_gpio`, `test_tap_nets_touch_only_the_harness_and_the_series_resistors`, `test_buffer_*` |
| 7 | VBUS window | The divider is now **20.5k / 3.83k, 0.1 %, 25 ppm/°C** (Panasonic ERA-3AEB). See the arithmetic below. | `test_vbus_window_at_the_xiao_pin_after_d2`, `test_fb_divider_top_is_in_the_ti_recommended_range` |
| 12 | Build safeguards | `build.sh` exits with gen_pcb's status. ERC and DRC run with `--severity-all --exit-code-violations`. The JLC04161H-7628 stackup is in the board, so the `.gbrjob` lists copper 35/15.2/15.2/35 µm and dielectrics 0.2104/1.065/0.2104 mm. The rules are the stricter of JLC and OSH Park for every minimum (2026-10-14 values below): edge 0.4, hole-to-copper 0.3, drill 0.26, ring 0.15, clearance 0.15, track 0.127, hole-to-hole 0.5, via 0.46. | `test_build_fails_on_errors`, `test_job_file_declares_the_jlc_7628_stackup`, `test_drc_rules_are_at_least_as_strict_as_both_fabs`, `test_reports_are_clean` |
| 13 | JLC assembly | R12 has the DNP attribute in the PCB. Parts excluded from position files: JP1, TP1, J1 and U1. For route (a), the JLC BOM and CPL list only JLC-placed Basic parts. CPL rotations are taken from KiCad; check them in JLC's preview (OPEN-ITEMS O6). Silk text is 1.0 mm minimum. | `test_jlc_bom_and_cpl_list_exactly_the_jlc_placed_parts` |

**Out of scope** (unchanged from Rev A): item 8 (the buck hot loop), item 9 (C3 sizing) and item 10 (test points). The board works without them.

### Item 7 arithmetic

The tolerance combines resistor tolerance and drift: 0.1 % + 25 ppm/°C × 60 °C = **0.25 %** per resistor. VFB is 0.788 / 0.800 / 0.812 V [V, TI].

| | Calculation | Result |
|---|---|---|
| Vout min | 0.788 × (1 + 20.5 × 0.9975 / (3.83 × 1.0025)) | **4.985 V** |
| Vout nominal | 0.800 × (1 + 20.5 / 3.83) | 5.082 V |
| Vout max | 0.812 × (1 + 20.5 × 1.0025 / (3.83 × 0.9975)) | **5.180 V** |
| Pin min (after D2) | Vout min − VF(0.5 A, cold) = 4.985 − 0.50 | **4.485 V**, ≥ 4.40 V (USB 2.0 low-power port minimum [I]) |
| Pin max | Vout max − 0, no diode credit taken | **5.180 V**, ≤ 5.25 V USB maximum |

About the VF(0.5 A, cold) = 0.50 V figure:
- It is a bound [I]. The PMEG4030ER table gives 0.44 V max at 1 A and 25 °C [V].
- The datasheet curve gives 0.43 V typical at 0.5 A and −40 °C [I].

The 0.1 % parts are hand-fit in both routes: JLC has no 0.1 % resistor in Basic or Preferred-Extended [V].

## Parts (all [V] 2026-10-13 unless marked)

Sources:
- Digi-Key data: the `https://www.digikey.com/en/products/result?keywords=<DK PN>` page. Stock and price are cut tape at qty 1 (qty 10 where marked).
- JLC data: the JLC parts API, matching `https://jlcpcb.com/partdetail/<C#>`.

| Ref | Part | MPN | Digi-Key PN | DK stock | DK $ | LCSC | JLC class | Datasheet | Land pattern |
|---|---|---|---|---|---|---|---|---|---|
| U2 | 4-65 V 1 A buck | TI LMR51610YDBVR | 296-LMR51610YDBVRCT-ND | 4,188 | 1.71 | C22427220 | Extended, not Preferred [V] (hand) | ti.com/lit/ds/symlink/lmr51610.pdf | TI DBV0006A: 1.1 x 0.6 pads, 2.6 mm rows [V] |
| U3 | Dual Schmitt buffer | TI SN74LVC2G17DBVR | 296-SN74LVC2G17DBVRCT-ND | 384,274 | 0.20 | C10429 | Extended, not Preferred [V] (hand) | ti.com/lit/ds/symlink/sn74lvc2g17.pdf | DBV0006A [V]. Pinout 1A, GND, 2A, 2Y, VCC, 1Y [V]. |
| L1 | 10 µH, Isat 2.3 A, Irms 1.8 A | Bourns SRP4020TA-100M | SRP4020TA-100MCT-ND | 41,663 | 1.07 | C189929 | Extended, not Preferred [V] (hand) | bourns.com SRP4020TA | 5.2 overall / 2.2 gap / 2.4 tall [V]. Pad length 1.5 = (5.2 − 2.2)/2. |
| F1 | PPTC 0.5 A hold, 60 V | Bourns MF-MSMF050/60X-2 | 118-MF-MSMF050/60X-2CT-ND | 943 | 0.91 | – | – | bourns.com/docs/Product-Datasheets/mfmsmf.pdf | 1.68 x 2.95 pads, 3.1 gap [V] |
| TVS1 | TVS 18 V VRWM, 29.2 V VC @ 6.8 A, 200 W | Littelfuse SMF18A | F5820CT-ND | 21,298 | 0.57 | C409420 | Extended, not Preferred [V] (hand) | Littelfuse SMF datasheet (rev 12/06/17), LCSC mirror: datasheet.lcsc.com/datasheet/pdf/6d382c654924c5ddbeb5b90893b39699.pdf | Littelfuse mounting pad layout: 1.3 x 1.4 pads, 1.6 gap [V]. Cathode bar on silk. Ratings from Littelfuse's SMF18A row: VR 18 V, VBR 20.0-22.1 V, VC 29.2 V @ 6.8 A [V]. |
| D1 | Schottky 40 V 1 A, 0.60 V @ 1 A | MCC B5819W-TP | B5819W-TPMSCT-ND | 39,242 | 0.28 | C8598 (CJ) | **Basic** | mccsemi.com/pdf/Products/B5817W-B5819W(SOD-123).pdf | MCC: 0.91 x 1.22, 2.36 gap [V] |
| D2 | Schottky 40 V 3 A | Nexperia PMEG4030ER,115 | 1727-5313-1-ND | 195,583 | 0.59 | C389355 | Extended, not Preferred [V] (hand) | assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf | CFP3 1.2 x 1.2 land [V], 2.8 pitch (KiCad Nexperia_CFP3_SOD-123W) |
| R13 | 20.5k 0.1 % 25 ppm | Panasonic ERA-3AEB2052V | P20.5KDBCT-ND | 8,443 | 0.11 | – | none at JLC | Panasonic ERA-3AE | 0603 |
| R14 | 3.83k 0.1 % 25 ppm | Panasonic ERA-3AEB3831V | P3.83KDBCT-ND | 25,291 | 0.11 | – | none at JLC | Panasonic ERA-3AE | 0603 |
| C1 | 10 µF 50 V X5R 1206 | Yageo CC1206KKX5R9BB106 | 13-CC1206KKX5R9BB106CT-ND | 22,608 | 0.75 | C13585 | **Basic** | – | 1206 |
| C3 | 100 µF 6.3 V X5R 1206 | TDK C3216X5R0J107M160AB (Active; replaced Taiyo Yuden JMK316BJ107ML-T, NFND, on 2026-10-14) | 445-6008-1-ND | 22,959 [V 10-14] | 1.11 | C15008 | **Basic** | TDK characterization sheet (see below) | KiCad C_1206_3216Metric; differs from TDK's recommended land (see below) |
| C7 | 22 µF 25 V X5R 1206 | Taiyo Yuden TMK316BBJ226ML-T | 587-3246-1-ND | 414,245 | 0.45 | – | (hand) | – | 1206. No 0805 22 µF 25 V is in stock at Digi-Key. |
| C2, C4, C8, C9 | 100 nF 50 V X7R 0603 | Yageo CC0603KRX7R9BB104 | 311-1344-1-ND | 4,771,083 | 0.080 @10 | C14663 | **Basic** | – | 0603 |
| R3, R4, R7, R8 | 1k 1 % 0603 | Yageo RC0603FR-071KL | 311-1.00KHRCT-ND | 2,586,238 | 0.025 @10 | C21190 | **Basic** | – | 0603 |
| R5, R6 | 100k 1 % 0603 | Yageo RC0603FR-07100KL | 311-100KHRCT-ND | 7,036 | 0.025 @10 | C25803 | **Basic** | – | 0603 |
| (U1 mount) | 40-pin header, 0.64 mm square pin | Sullins PRPC040SAAN-RC | S1011EC-40-ND | 45,650 | 1.23 | – | – | Sullins drawing 11635 rev B | 1.10 drill (item 1) |
| (harness) | 6-pin female, 2.54 mm | Sullins PPTC061LFBN-RC | S7004-ND | 26,627 | 0.47 | – | – | Sullins | – |
| (harness, **required**) | 2 x 10 k series, 1/8 W 5 % axial | Stackpole CF18JT10K0 | CF18JT10K0CT-ND | 261,497 [V 10-14] | 0.10 (0.023 @10) | – | – | – | in-line on the tap wires at the dongle pads |
| R12, JP1, TP1 | Proxy reservation | DNP / bare copper | – | – | – | – | – | – | unchanged |

For the Basic parts, JLC places a different MPN under the same LCSC number: C1 and C3 are Samsung CL31A106KBHNNNE and CL31A107MQHNNNE, the resistors are Uniroyal 0603WAF, and D1 is CJ B5819W. The Digi-Key column is the hand-route part.

Removed from Rev A:
- JST GH J1
- 14 Mill-Max 7305 receptacles
- FNR4030S inductor
- C5/C6 (DNP)
- The 0402 passives (all passives are now 0603 or 1206)

Ratings check:
- **Input path:** F1 60 V, D1 40 V, C1 50 V, U2 65 V operating. TVS1 clamps at 29.2 V.
- **L1:** Isat 2.3 A is above the LMR51610 peak current limit of 1.95 A max [V], so L1 does not saturate in a short circuit.
- **L1 ripple:** about 0.27 A p-p at 12 V and 1.1 MHz, so the peak is about 0.63 A at a 0.5 A load.
- **U3:** inputs are rated to 5.5 V with Ioff, so the taps cannot back-power the XIAO through it. Its thresholds at VCC 3 V are VT+ 1.3-2.0 V and VT− 0.8-1.3 V [V].
- **U3 bias:** with the pad low, the 100k/11k divider puts BUF_IN at 0.33 V, below VT− min. A 3.3 V high puts it at about 3.3 V, above VT+ max. A 5 V high would put it at 4.83 V, below 5.5 V.

## Small fixes (2026-10-14)

Approved fixes from `../VERIFY-revB.md` (Board B items 1, 4, 8). Verification: `sh scripts/build.sh` exits 0; ERC 0 errors, 0 warnings; DRC 0 violations, 0 unconnected; `pytest -q tests` 25 passed.

**1. DRC minimums are now the stricter of both fabs.** Source: `write_rules()` in `scripts/gen_pcb.py` (it writes `carrier.kicad_pro`). Published 4-layer values read 2026-10-14 [V]: JLC https://jlcpcb.com/capabilities/pcb-capabilities, OSH Park https://docs.oshpark.com/services/four-layer/.

| Rule (mm) | JLC | OSH Park | Was | Now |
|---|---|---|---|---|
| Clearance | 0.09 trace, 0.15 SMD pad to pad | 0.127 | 0.127 | **0.15** |
| Track width | 0.09 | 0.127 | 0.127 | 0.127 |
| Annular ring (vias and PTH) | 0.15 PTH min (0.20 recommended); via dia − hole ≥ 0.1 | 0.1016 | 0.11 | **0.15** |
| Via diameter | 0.25 | 0.457 (10 mil + 2 x 4 mil) | 0.45 | **0.46** |
| Hole size | 0.15 | 0.254 | 0.26 | 0.26 |
| Hole to copper | 0.30 inner-layer PTH (0.28 PTH to track, 0.2 via) | 0.254 | 0.26 | **0.30** |
| Hole to hole | 0.45 pad (0.2 via) | 0.127 recommended | 0.5 | 0.5 |
| Copper to edge | 0.20 routed | 0.381 | 0.4 | 0.4 |

- A probe run at ring 0.18 flagged every XIAO PTH pad as well as the vias, so KiCad 10's annular rule covers PTH pads, not only vias [V, tool output].
- No layout change was needed. The vias (0.6/0.3) sit exactly at 0.15. The XIAO top ring is 0.175 nominal: it passes JLC's 0.15 minimum but not its 0.20 recommendation, so JLC may raise a DFM warning [I].
- Test: `test_drc_rules_are_at_least_as_strict_as_both_fabs` holds both fabs' published values separately and asserts each `.kicad_pro` minimum is at least the larger.

**2. C3 is now TDK C3216X5R0J107M160AB (445-6008-1-ND).** The JLC route keeps Samsung CL31A107MQHNNNE (C15008).
- Digi-Key [V 2026-10-14, https://www.digikey.com/en/products/result?keywords=C3216X5R0J107M160AB]: Active, 22,959 in stock, $1.11 at 1, $0.708 at 10. 100 µF ±20 %, 6.3 V, X5R, 1206 (3216), 1.80 mm max height. The old part shows "Not For New Designs" there (https://www.digikey.com/en/products/result?keywords=JMK316BJ107ML-T).
- Height: TDK's characterization sheet gives T = 1.60 +0.3/−0.1, so 1.9 mm max [V]. C3 is at (127.6, 125.3), outside the XIAO courtyard (y ≤ 118.35), so it does not affect the 7.8 mm stack.
- **Effective capacitance at 5 V: slightly worse, so this check fails narrowly.** TDK: −71.3 % at 5.0 V, 25 °C, so about **28.7 µF** [V]. Source: TDK characterization sheet https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/charasheet/c3216x5r0j107m160ab.pdf (403 to scripted fetch; read from the archive copy http://web.archive.org/web/20251006181201/ of that URL). The old part's own curve is no longer published. Its renamed successor reads −69.8 %, about **30.2 µF** [I] (https://ds.yuden.co.jp/TYCOMPAS/ut/detail?pn=MLASJ31LAB5107MTNA01&u=M). That makes TDK about 1.5 µF (5 %) lower, against an inferred comparator. It matches the Samsung JLC part (about 29 µF). C3 is bulk storage after D2, and the docs already treat it as about 30 µF, so the circuit margin does not change [I].
- The closest equivalent would be the Taiyo Yuden successor (MBASJ31LBB5107MTNA01 or MLASJ31LAB5107MTNA01). It was not taken, because neither its Digi-Key stock and status nor its mapping to JMK316**BJ**107ML-T (the rename page maps JMK316**ABJ**107ML-T) could be verified today: Digi-Key returned 403. See OPEN-ITEMS O8.
- Land pattern: TDK's recommended C3216 reflow land is a 2.0-2.4 gap, 1.0-1.2 pad length and 1.1-1.6 pad width [V] (TDK spec GC11010023, p. 18, archived at http://web.archive.org/web/20250909200311/https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/specification/mlccspec_commercial_general_midvoltage_en.pdf). KiCad's C_1206_3216Metric has a 1.8 gap, 1.15 length and 1.8 width. That is **not** TDK's recommended land; the old part used the same footprint. The terminals (B ≥ 0.20, gap G ≥ 1.00 [V]) still land on both pads, so it is fine for hand soldering [I]. The footprint is unchanged.
- Test: `test_c3_is_the_active_tdk_part` pins the MPN, DK part number and footprint; `test_digikey_bom_lists_every_fitted_part` checks the BOM row.

**3. The harness 10 k resistors are in the kit and marked required.** Stackpole CF18JT10K0, CF18JT10K0CT-ND: Active, 261,497 in stock, 10 kΩ 5 % 1/8 W axial, 1.7 x 3.3 mm body, $0.10 at 1, $0.023 at 10 [V 2026-10-14, https://www.digikey.com/en/products/result?keywords=CF18JT10K0]. This is the part `docs/hardware/README.md` specifies. It is 2 per board, so the order is 10 for two boards (cheaper than 4). Board B has no D3/D4, which is acceptable only with these fitted (`../VERIFY-revB.md` §2a). It is now in `KIT` (`scripts/design.py`), the Digi-Key BOM (row `kit`), the README harness steps and PRICING.
- Test: `test_kit_includes_the_harness_10k_series_resistors`.
