# Carrier Rev B (JLC-assembled variant): changes from Rev A

Date: 2026-10-13. Route: JLCPCB 4-layer, Economic PCBA, top-side SMD only, fab 5 and assemble 2.
JLC places every SMD part. The user hand-solders only the XIAO header pins, the harness wires and the two harness 10 k resistors (hand-fit kit, README).

**Board: 27.0 x 27.0 mm, unchanged.** No axis grew, so nothing was added along the USB-C edge or the
J1 edge. Nothing extends past the outline: the harness wires enter the plated holes vertically.

Tags: [V] means I read the primary source today (2026-10-13) and the URL is given. [I] means inferred.

## Fixes (review items)

| # | Fix | Verification |
|---|---|---|
| 1, 4 | Mill-Max sockets and castellation pads removed. The XIAO sits on 2.54 mm male headers with 0.64 mm square posts (Sullins PRPC040SAAN-RC). Holes are 1.10 mm drill on 1.70 mm pads. | The finished hole is 1.02-1.23 mm after JLC's +0.13/-0.08 mm, which is at least Sullins' recommended 1.00 mm hole (drawing 11635 rev B) [V]. The post diagonal is 0.905 mm, leaving at least 0.115 mm clearance. The worst-case ring is 0.235 mm, against JLC's 0.20 mm recommended (0.15 mm absolute minimum) multilayer ring. The gap between pads is 0.84 mm, so one 0.2 mm track fits between pins. `test_xiao_header_holes_fit_square_pins_with_jlc_tolerance` reads the generated footprint. |
| 2 | J1 (GH connector, 3-6 mm plug overhang) replaced by 5 plated wire holes: 2.54 mm pitch, 1.0 mm drill, 1.7 mm pad. They sit 0.55 mm inside the J1 edge and the wire exits vertically. Pin order: 1 +12V, 2 GND (power), 3 GND (signal), 4 TAP pad 9, 5 TAP pad 10. The NC spare was dropped. | DRC passes, including copper-to-edge 0.3 mm. `test_harness_pinout` and `test_harness_pads_are_through_hole` pass. This also removes J1's Extended fee. **Trade-off: there is no on-board disconnect any more. See OPEN-ITEMS 1.** |
| 3 | Stack height recomputed for the header mount (below). | Arithmetic is below. The XIAO height is unmeasured; see OPEN-ITEMS. |
| 5 | The silk rule is now "12V OFF FOR USB (or USB isolator)" on the bottom, and the README has the same rule. | Visible in `fab/render_bottom.png`. |
| 6 | RX buffer U3 (74LVC2G17GW) added. The chain is TAP -> D3/D4 ESD -> R3/R4 1k -> U3 (R5/R6 100k pull-ups to 3V3) -> R7/R8 1k -> XIAO D0/D1. The DNP proxy path (R12, JP1, TP1, GPIO8) and the DNP C5/C6 were removed, so there is no TX path at all. | `test_buffer_is_the_only_path_from_tap_to_gpio` and `test_no_gpio_can_reach_a_tap` treat every footprint as fitted, U3 as one-way and power nets as terminals. `test_no_tx_or_proxy_provision` and `test_no_dnp_parts_left` also pass. |
| 7 | The divider is now R13 33k / R14 6.19k, both 0.1 % 25 ppm thin film. | `test_feedback_divider_worst_case_window`. The arithmetic is below. |
| 12 | `build.sh` fails if gen_pcb fails (exit status kept, with no pipefail needed). ERC and DRC use `--exit-code-violations`. The JLC04161H-7628 stackup is written into the board and so into the job file. | During development, real DRC violations made the build exit 5. `test_job_file_declares_the_jlc_4_layer_stackup` checks copper 0.035/0.0152/0.0152/0.035 and dielectrics 0.2104/1.065/0.2104 in `fab/gerbers/carrier-job.gbrjob`, against https://jlcpcb.com/impedance [V]. |
| 13 | DNP parts are excluded from the CPL (`dnp or not in_bom`); none remain. Rotation offsets are data-driven (`design.CPL_ROTATION`): SOT-23* -90 and SOT363-2 180, from JLCKicadTools `cpl_rotations_db.csv` [I]. Silk text is at least 1.0 mm, which is the DRC min_text_height. | `test_cpl_lists_exactly_the_assembled_parts_with_jlc_rotation_offsets`. Rotations still need confirming in JLC's preview: see OPEN-ITEMS. |

Out of scope, unchanged: hot-loop polish, test points and C3 rework. The board works without them.

## Small fixes after verification (2026-10-14, VERIFY-revB.md)

Tags in this section: [V] read today, 2026-10-14. No layout change; nothing moved.

| Fix | Change | Verification |
|---|---|---|
| DRC rules vs JLC | The rules moved from literals in `gen_pcb.write_rules()` to `design.DRC_RULES`, checked against `design.JLC_MIN` (JLC multilayer 1 oz minimums, https://jlcpcb.com/capabilities/pcb-capabilities [V]). Three were looser than JLC and were raised: annular ring 0.10 -> **0.15** (PTH absolute minimum; KiCad applies it to vias and PTH pads), clearance 0.127 -> **0.15** (SMD pad to pad, different nets), hole to copper 0.25 -> **0.30** (inner-layer PTH hole to copper; outer PTH to track is 0.28). Already stricter and kept: track 0.127 (JLC 0.09), via 0.45 (0.25), hole 0.2 (0.15), hole to hole 0.5 (0.45), copper to edge 0.3 (0.2), text 1.0/0.15 (1.0/0.15). | `test_drc_rules_are_at_least_as_strict_as_jlc_4_layer_minimums`, `test_project_rules_come_from_design`. DRC: 0 violations, 0 unconnected. Enforcement checked on a scratch copy: at ring 0.36 / hole clearance 0.40, DRC flagged 26 vias (ring 0.15), 14 XIAO pads (0.30), 5 J1 pads (0.35) and hole clearances down to 0.337 mm, so the real minimums are ring 0.15 (vias, exactly at JLC's minimum) and hole to copper 0.337. |
| Kapton shim | The spacer-off mount now states the shim as required (0.049 mm ring-to-pad clearance), with a range of 0.06-0.2 mm (`design.SHIM`), and the spacer-on mount as allowed only if the measured XIAO is 4.1 mm or less. Kapton tape added to the hand-fit kit (`design.KIT`): Bertech PPTA-1/2, Digi-Key 4393-PPTA-1/2-ND, 0.064 mm, 660 in stock, $13.95 [V]. | `test_kit_has_kapton_within_the_shim_range` (tape inside the range; spacer-off stack at 0.2 mm within 9.0; spacer-on over 9.0). |
| Harness 10 k | Added to the hand-fit kit: Stackpole CF14JT10K0, Digi-Key CF14JT10K0CT-ND, 571,559 in stock, $0.027 each at 10 [V]. README harness and bring-up steps say where they go. | `test_kit_has_one_harness_10k_per_tap_wire`, `test_kit_parts_are_priced_and_documented`. |
| C3 note | OPEN-ITEMS 16: NRND, about 29 uF at 5 V; no other Basic/Preferred 100 uF 1206 at JLC [V]. No change. | JLC parts API search. |

## JLC tooling holes and silkscreen (2026-10-14)

Tags: [V] read today. No part moved; no copper changed (except the pours, which now clear the holes).

| Fix | Change | Verification |
|---|---|---|
| Tooling holes | Two customer-placed tooling holes, TH1 (top-left) and TH2 (top-right): 1.152 mm round NPTH, 0.148 mm solder mask expansion, centres 2.0 mm from the top and side edges (`design.TOOLING`, `design.tooling_holes()`; board-only footprint from `gen_lib.gen_tooling_hole()`). JLC: "Two or three tooling holes ... in opposite corners ... as far apart from one another as practical", "1.152mm(45.4mil) round non-plated holes with 0.148mm solder mask expansion", "keep them away from traces" (https://jlcpcb.com/help/article/how-to-add-tooling-holes-for-pcb-assembly-order [V]). The page gives no edge distance; hole edge to board edge is 1.42 mm, against a 1.0 mm floor taken from JLC's castellated-hole rule [I]. Copper clearance floor 0.5 mm (JLC NPTH to track is 0.2 [V]); actual nearest copper is U1 pad 1 at about 1.0 mm. The bottom corners cannot take a hole without moving a part (J1 pad 1 bottom-left; C3 pad 2 and L1 bottom-right). The drill export now writes separate `carrier-PTH.drl` and `carrier-NPTH.drl` (`--excellon-separate-th`). TH2 sits under the XIAO, inside U1's courtyard, so `npth_inside_courtyard` is set to ignore in the project file (`design.DRC_SEVERITY`). | `test_tooling_holes_match_jlc_spec`, `test_tooling_holes_keep_clear_of_copper`, `test_pours_clear_the_tooling_holes`, `test_tooling_holes_are_in_the_drill_file`, `test_only_the_tooling_courtyard_check_is_downgraded` (only the listed checks are downgraded, every NPTH is a tooling hole). F.Mask and B.Mask have a 1.448 mm opening at each hole. |
| Silkscreen (JLC DFM: silk to pad 49, silk to hole 31, line width 64) | JLC legend rules (https://jlcpcb.com/capabilities/pcb-capabilities [V]): line 0.15 mm, text 1.0 mm, pad to silk 0.15 mm (`design.SILK`). New `scripts/silk.py`: gen_pcb widens every silk stroke to 0.15 mm (stock footprints used 0.12) and cuts footprint and board silk lines back to 0.15 mm from pads, via and pad holes, NPTH mask openings and the board edge; pieces under 0.3 mm are dropped. Texts moved by hand: the bottom-silk "SolArk carrier rev B / 12V OFF FOR USB / (or USB isolator)" block to (119.3, 121.95-124.95) clear of vias, line pitch 1.5 mm; FOAM TAPE +0.15 mm; bottom 12V label +0.2 mm down; pad-3 G label 0.45 mm left; U1 "USB" 0.35 mm toward the board centre. `silk_over_copper`, `silk_overlap`, `silk_edge_clearance`, `text_height`, `text_thickness` are DRC errors and `min_silk_clearance` = 0.15. `lib_footprint_mismatch` is ignored because the board copies of stock footprints now differ from the library by design. | `test_silk_rules_are_drc_errors`, `test_silk_strokes_and_text_meet_jlc_minimums`, `test_silk_check_report_is_clean` (`fab/silk.rpt`: 0 violations; pin-1 / cathode silk kept next to pad 1 of U2, U3, D1, D2, TVS1), `test_xiao_pin_1_is_marked_by_a_square_pad`. |
| Mask opening exposing a trace (JLC DFM, 1) | Not changed. No mask opening exposes non-pad copper in KiCad's geometry (pad mask margin is 0, vias are tented). Three same-net traces run along or through a pad's opening and are the likely hit: +12V_P across C2 pad 1, BUF_OUT_REQ along R8 pad 1, GND along C7 pad 2. Same net, so there is no short risk. | Scratch geometry check (track minus pad copper inside mask openings = 0). |

## VBUS window (item 7)

Inputs:
- LMR51610 datasheet (SLUSEW3): Vfb is 0.788 / 0.800 / 0.812 V. PFM Vout regulation is -1.5 % / +2.5 %, over TJ -40 to 150 C with "typical components", and is not production tested [V] (https://www.ti.com/lit/ds/symlink/lmr51610.pdf).
- Resistor TC excursion: assumed 100 K [I].

Ratio of the new divider: k = 33/6.19 = 5.3312, so Vout is 5.065 V nominal.
- k max = 5.3312 x (1 + 0.001 + 0.0025) / (1 - 0.001 - 0.0025) = 5.3686
- k min = 5.2940

| Case | Arithmetic | Result | Limit |
|---|---|---|---|
| Max, before D2 (conservative: the brief allows it after D2) | 0.800 x 1.025 x (1 + 5.3686) | 5.222 V | <= 5.25 V |
| Min, at the XIAO 5V pin after D2 | 0.788 x (1 + 5.2940) - 0.44 | 4.520 V | >= 4.40 V |

- D2 is the PMEG4030ER: VF is at most 440 mV at 1 A and 25 C [V] (Nexperia datasheet, LCSC C389355 link below).
- VF rises at cold [I], and the margin is 0.12 V. The XIAO peak is about 0.5 A [I], well below the 1 A rating.
- Stacked reading: if the +2.5 % excludes the reference tolerance, the pre-D2 maximum is 0.812 x 1.025 x 6.3686 = 5.30 V. At the pin it is still at most 5.30 V minus D2's drop at load [I]. The XIAO's 3V3 regulator (SGM6029) is rated to 5.5 V operating and 6 V absolute maximum [I, from Seeed's schematic].

Basic-part alternative, under the same assumptions: 27k / 5.1k at 1 % and 100 ppm.
- Max: 0.82 x (1 + 5.510) = 5.338 V, which fails.
- Min: 0.788 x (1 + 5.087) - 0.44 = 4.356 V, which also fails.
- So the two Extended precision resistors ($6.14 in fees) are kept, as the brief requires (VBUS margin is never traded).

## Stack height (item 3)

Heights are from the carrier bottom to the XIAO top. The XIAO Plus is 4.9 mm overall including the
PCB [I, unmeasured]. The carrier is 1.6 mm. The header tail is trimmed to 0.8 mm, about the
thickness of the foam tape.

| Mount | Stack | Total |
|---|---|---|
| Header plastic spacer left on (2.50 mm, Sullins [V]) | 0.8 + 1.6 + 2.5 + 4.9 | 9.8 mm: over the 9.0 mm design limit, inside 10 mm |
| Spacer slid off; XIAO on a Kapton shim, 0.06-0.2 mm (required: 0.049 mm ring-to-pad clearance) | 0.8 + 1.6 + 0.06-0.2 + 4.9 | 7.4-7.5 mm |

- No carrier part sits under the XIAO outline (only THT pads and tented vias), so the low-profile mount works. The renders model the spacer-on case (`design.MOUNT`).
- The post above the XIAO (5.84 mm mating side) must be trimmed to the XIAO's tallest part.

## Parts (all top side, JLC parts API read 2026-10-13 [V])

Stock and unit price at quantity 1-9 come from the JLC parts API. Basic/Extended status is JLC's
library type; "Preferred" is Extended but exempt from the feeder fee
(https://jlcpcb.com/help/article/PCB-assembly-faqs [V]).

| Ref | Part | MPN | LCSC | Status | Stock | Unit $ | Datasheet | Land pattern |
|---|---|---|---|---|---|---|---|---|
| U3 (new) | Dual Schmitt buffer, 1.65-5.5 V, inputs 5.5 V-tolerant, Ioff +-2 uA at VCC = 0 | Nexperia 74LVC2G17GW,125 | C80500 | Extended | 8,570 | 0.0884 | https://assets.nexperia.com/documents/data-sheet/74LVC2G17.pdf | Custom footprint from Nexperia sot363-2_fr: lands 0.75 x 0.40 at +-0.975 mm, 0.65 mm pitch, pad ring counter-clockwise (pin 1 top-left, test `test_sot363_pad_ring_is_counter_clockwise_like_kicad_stock`). Pinout per Table 3: 1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y [V] (https://assets.nexperia.com/documents/outline-drawing/SOT363-2.pdf) |
| D3, D4 (new) | Bidirectional ESD: VRWM 5 V, VBR 5.6-8 V, IR 0.1 uA, Cj 15 pF typ, +-25 kV contact | Hongjiacheng H5VL10B | C7420372 | Preferred | 10,117,041 | 0.0064 | https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2306301553_hongjiacheng-H5VL10B_C7420372.pdf | Custom footprint: pads 0.55 x 0.60, gap 0.30, inside the datasheet's suggested J/K/M ranges [V] |
| R5, R6 (now fitted) | 100k 1 % 0402 | UNI-ROYAL 0402WGF1003TCE | C25741 | Basic | 9,746,849 | 0.0021 | https://www.lcsc.com/datasheet/lcsc_datasheet_2206010100_UNI-ROYAL-Uniroyal-Elec-0402WGF1003TCE_C25741.pdf | Stock R_0402 |
| R7, R8 (new), R3, R4 | 1k 1 % 0402 | UNI-ROYAL 0402WGF1001TCE | C11702 | Basic | 7,875,625 | 0.0031 | https://www.lcsc.com/datasheet/lcsc_datasheet_2206010216_UNI-ROYAL-Uniroyal-Elec-0402WGF1001TCE_C11702.pdf | Stock R_0402 |
| C9 (new), C2, C4, C8 | 100nF 50V X7R 0402 | Samsung CL05B104KB54PNC | C307331 | Basic | 15,026,932 | 0.0104 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL05B104KB54PNC_C307331.pdf | Stock C_0402 |
| R13 (changed) | 33k 0.1 % 25 ppm thin film | YAGEO RT0402BRD0733KL | C728559 | Extended | 12,364 | 0.0279 | https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_YAGEO-RT0402BRD0733KL_C728559.pdf | Stock R_0402 |
| R14 (changed) | 6.19k 0.1 % 25 ppm thin film | YAGEO RT0402BRD076K19L | C705638 | Extended | 6,968 | 0.0283 | https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2009282238_YAGEO-RT0402BRD076K19L_C705638.pdf | Stock R_0402 |
| TVS1 (changed source) | SMF18A: VRWM 18 V, VBR 20-22.1 V, VC 29.2 V at 6.8 A, 200 W | Hongjiacheng SMF18A | C19077512 | Preferred | 70,450 | 0.0301 | https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312280940_hongjiacheng-SMF18A_C19077512.pdf | Stock D_SOD-123F: pads 1.1 x 1.1 span 0.85-1.95 mm from centre, covering leads that end at 1.95 mm (D max 3.9) with length 0.4-0.9 mm and width 1.0-1.2 mm [V]. Cathode band = pin 1 = +12V_P. |
| U2 | 4-65 V 1 A buck, 1.1 MHz PFM | TI LMR51610YDBVR | C22427220 | Extended | 3,160 | 1.1173 | https://www.ti.com/lit/ds/symlink/lmr51610.pdf | Stock SOT-23-6 [I, kept from Rev A] |
| L1 | 10 uH 1.6 A, 2.4 A sat | cjiang FNR4030S100MT | C167879 | Extended | 105,910 | 0.0467 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_cjiang--Changjiang-Microelectronics-Tech-FNR4030S100MT_C167879.pdf | Stock L_Changjiang_FNR4030S [I, kept] |
| F1 | PPTC 0.5 A 60 V 1812 | PTTC SMD1812P050TF/60 | C462518 | Extended | 3,885 | 0.3008 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_PTTC-Polytronics-Tech-SMD1812P050TF-60_C462518.pdf | Stock Fuse_1812 [I, kept] |
| D2 | Schottky 40 V 3 A, VF <= 440 mV at 1 A | Nexperia PMEG4030ER,115 | C389355 | Extended | 11,286 | 0.2727 | https://www.lcsc.com/datasheet/lcsc_datasheet_2407241028_Nexperia-PMEG4030ER-115_C389355.pdf | Stock Nexperia_CFP3_SOD-123W [I, kept] |
| D1 | Schottky 40 V 1 A | CJ B5819W SL | C8598 | Basic | 383,586 | 0.0283 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Jiangsu-Changjing-Electronics-Technology-Co---Ltd--B5819W-SL_C8598.pdf | Stock D_SOD-123 [I, kept] |
| C1 | 10uF 50V X5R 1206 | Samsung CL31A106KBHNNNE | C13585 | Basic | 2,156,107 | 0.1584 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL31A106KBHNNNE_C13585.pdf | Stock C_1206 |
| C3 | 100uF 6.3V X5R 1206 | Samsung CL31A107MQHNNNE | C15008 | Basic | 1,699,904 | 0.1307 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL31A107MQHNNNE_C15008.pdf | Stock C_1206 |
| C7 | 22uF 25V X5R 0805 | Samsung CL21A226MAQNNNE | C45783 | Basic | 3,451,121 | 0.2372 | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL21A226MAQNNNE_C45783.pdf | Stock C_0805 |
| XIAO header (hand) | 2.54 mm 1x40 male header, 0.64 mm square posts | Sullins PRPC040SAAN-RC | Digi-Key S1011EC-40-ND | n/a | 45,650 | 1.23 | https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/386/xRxCzzzSxxN-RC_ST_11635-B.pdf | Hole sized above [V] |

Removed parts:
- J1 (GH connector, C51940119, Extended).
- C5, C6, R12, JP1 and TP1 (DNP).
- The Mill-Max receptacles.
- TVS1's old source C123787, replaced by C19077512 (same SMF18A rating, Preferred).

**Feeder-fee parts: 7 Extended (U2, L1, F1, D2, U3, R13, R14) x $3.07 = $21.49.** No Basic or
Preferred part was found equivalent for these. TVS1, D3 and D4 are Preferred (no fee). Rev A had 6
fee parts (J1, U2, L1, F1, D2 and TVS1 C123787). Rev B swaps J1 and TVS1 out and U3, R13 and R14 in.

The kept parts' land patterns are the stock KiCad footprints named for each package. They were
reviewed in Rev A for polarity, but not re-checked against the datasheets today: see OPEN-ITEMS 10.
